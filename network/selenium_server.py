# -*- coding: utf-8 -*-
from datetime import date, timedelta, datetime
from multiprocessing.connection import Client
from multiprocessing.connection import Listener
from multiprocessing import Process
from logging import debug, info, warning, error, critical
import json, SocketServer, sys, time, zlib, socket, urlparse, threading, urllib, base64, StringIO, traceback
from PIL import Image
from getopt import getopt, GetoptError

from setproctitle import setproctitle
from copy import deepcopy

from pylibs.utils.text import toUnicode
from pylibs.utils.decorators import lock, cached_property
from pylibs.utils.botmanager import MultiThreadsTasksManager
from pylibs.network.urls import get_domain
from pylibs.utils.tools import processecControl, kill_process
from pylibs.seo.yandex import Yandex
from pylibs.network.anticaptcha import AntigateNotAvailable, solveImgUrl
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import selenium.webdriver.support.ui as ui

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime, create_engine
Base = declarative_base()
sql_engine = None

class SeleniumException(Exception):
    pass

class SeleniumServerException(SeleniumException):
    pass

class NoBrowsers(SeleniumServerException):
    pass

class NeedRebootServerException(SeleniumServerException):
    pass

class CaptchaException(SeleniumServerException):
    pass

class DigitalOceanException(SeleniumServerException):
    pass

class SeleniumBrowserException(SeleniumException):
    pass

class SeleniumBrowser(object):
    """
    Имитирует интерфейс класса pylibs.network.browser.Browser
    """
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port

    def get(self, url):
        response = ''

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(60)
        debug('try connect...')
        s.connect((self.server_host, self.server_port))
        debug('try send..')
        s.sendall(url)
        debug('sended. wait response...')

        block_len = 1448
        while True:
            data = s.recv(block_len)
            response += data
            if data is None or len(data)==0:
                break
        s.close()

        debug("response zip length: %s" % len(response))

        response = response.decode("zlib")
        self.response = json.loads(response)
        if 'errnum' in response:
            raise SeleniumBrowserException(self.response['message'])

    def unicode(self):
        return self.response['result']['html']

    def body(self):
        return self.unicode().encode('utf-8')

    @property
    def effective_url(self):
        return self.response['result']['effective_url']


class SeleniumSession(Base):
   __tablename__ = 'obj_selenium_sessions'
   id = Column(Integer, primary_key=True)
   server = Column(String(100))
   session_id = Column(String(100))
   create_date = Column(DateTime)
   cnt_requests = Column(Integer)
   cnt_captcha = Column(Integer)
   last_request_date = Column(DateTime)

class PersistentWebdriver(webdriver.Remote):

    def __init__(self, *args, **kwargs):
        self.existed_session_id = None
        if 'session_id' in kwargs:
            self.existed_session_id = deepcopy(kwargs['session_id'])
            del kwargs['session_id']
        super(PersistentWebdriver, self).__init__(*args, **kwargs)

    def start_session(self, *args, **kwargs):
        if self.existed_session_id is None:
            super(PersistentWebdriver, self).start_session(*args, **kwargs)
        else:
            self.connect_to_existed_session(*args, **kwargs)

    def connect_to_existed_session(self, *args, **kwargs):
        info("try connect_to_existed_session...")
        if 'getSession' not in self.command_executor._commands:
            self.command_executor._commands['getSession'] = ('GET', '/session/$sessionId')
        try:
            response = self.execute('getSession', {
                'desiredCapabilities':args[0],
                'sessionId': self.existed_session_id
            })
            self.session_id = response['sessionId']
            self.capabilities = response['value']
            page_source = self.page_source
            info("CONNECTED TO EXISTS")
        except WebDriverException as e:
            info("Existed session not found.. create new session")
            self.existed_session_id = None
            return self.start_session(*args, **kwargs)
        except Exception as e:
            if 'timed out' in str(e):
                info("Existed session not found.. create new session")
                self.existed_session_id = None
                return self.start_session(*args, **kwargs)
            else:
                raise

        


class ThreadedTCPServer(SocketServer.ForkingMixIn, SocketServer.TCPServer): #ThreadingMixIn
    def serve_forever(self, address, *args, **kwargs):
        self.address = address
        return SocketServer.TCPServer.serve_forever(self, *args, **kwargs)


class SeleniumDefaultTCPHandler(SocketServer.BaseRequestHandler):
    
    def __get_browser(self):
        conn = Client(self.server.address)
        conn.send(["get_browser"])
        br = conn.recv()
        info('Get browser %s' % br)
        return br

    def __release_browser(self, br, need_reboot, need_reboot_server):
        conn = Client(self.server.address)
        conn.send(["release_browser", [br, need_reboot, need_reboot_server]])

    def _get_url(self, br, url):
        br.get(url)
        return br.driver.page_source

    def __prepare_response(self, response, effective_url):
        response = {'result':{'html':response, 'effective_url':effective_url}}
        return response

    def __send_response(self, response):
        if "errnum" in response:
            error(response['message'])
        response = zlib.compress(json.dumps(response), 9)
        self.request.sendall(response)

    def is_no_connect(self, response):
        no_connect = False
        bad_responces = ['Unable to connect to host', 'It may have died', 'Unable to bind', 'object has no attribute', "Message: ''", 'Session not found', 'refused']
        for r in bad_responces:
            if r in response:
                no_connect = True
                break
        return no_connect

    def handle(self):
        st = time.time()
        url = self.request.recv(4096).strip()
        debug("Catched request from client: %s" % url)


        br = self.__get_browser()

        if br is not None:

            need_reboot = False
            need_reboot_server = False

            try:
                socket.setdefaulttimeout(60)
                info("%s: Send request: %s" % (br, url))

                page_source = self._get_url(br, url)
                info("_get_url fiinished at %s sec" % (time.time()-st, ))

                effective_url = br.driver.current_url
                info("effective url fiinished at %s sec (%s)" % (time.time()-st, effective_url))

                response = self.__prepare_response(page_source, effective_url)
                info("__prepare_response finished at %s sec" % (time.time()-st, ))
            except Exception as e:
                response = str(e)
                
                etype, evalue, etrace = sys.exc_info()
                trace = str(traceback.format_exception(etype, evalue, etrace))

                if self.is_no_connect(response):
                    response = "Selenium can't connect to browser."
                    warning("Send server %s to reboot, because %s, TRACE: %s" % (br.server.server_name, e, trace))
                    need_reboot_server = True
                else:
                    warning(trace)

                response = {"errnum":1, "message":response} 
            except KeyboardInterrupt:
                response = {"errnum":2, "message":"KeyboardInterrupt"} 
            finally:
                self.__send_response(response)
                info("data sended in %s sec" % (time.time()-st, ))
                socket.setdefaulttimeout(None)
                self.__release_browser(br, need_reboot, need_reboot_server)
        else:
            self.__send_response({"errnum":2, "message":"All browsers is busy."} )


class YandexTCPHandler(SeleniumDefaultTCPHandler):
    
    anticaptcha_key = None
    anticaptcha_service = None

    def _get_url(self, br, url):
        br.get(url)
        if Yandex.is_yandex_captcha(br.driver.current_url):
            self.yandex_solve_captcha(br)
        
        return br.driver.page_source

    def solve_captcha(self, br, page_source):

        img_str = br.driver.get_screenshot_as_base64()
        img_str =  base64.b64decode(img_str)
        buff = StringIO.StringIO()
        buff.write(img_str)
        buff.seek(0)

        i = Image.open(buff)
        frame2 = i.crop(((165, 250, 375, 335)))
        
        buff2 = StringIO.StringIO()
        img_data = frame2.save(buff2, 'gif')
        img_data = buff2.getvalue()
        buff2.close()

        try:
            code = solveImgUrl(self.anticaptcha_key, img_data = img_data, host = self.anticaptcha_service)
        except AntigateNotAvailable as e:
            raise AntigateNotAvailable("No connect with anticaptcha service")

        return code


        

    def yandex_solve_captcha(self, br):
        debug("CAPTCHA Found. Try solve.")

        br.count_captcha += 1
        cnt_attempts = 2

        br.execute_js_with_jquery("""
            $('body').prepend('<input id="infoinput" type="text" value="init info input">');
        """)

        page_source = br.driver.page_source

        br.execute_js_with_jquery("""
            $('#infoinput').attr('value', 'page_source ok');
        """)

        for i in range(cnt_attempts):
            try:
                code = toUnicode(self.solve_captcha(br, page_source))

                br.execute_js_with_jquery("""
                    $('#infoinput').attr('value', 'code %s');
                """ % code);

                debug('code is "%s"' % code)
                br.driver.execute_script("document.getElementById('rep').value = '%s';" % code)
                debug("%s: Keys sended" % br)

                br.execute_js_with_jquery("""
                    $('#infoinput').attr('value', 'Keys sended: %s');
                """ % code);

                br.execute_js_with_jquery("""
                    $('input[class=b-captcha__submit]').click();
                """);

                # wait redirects
                for i in range(10):
                    if 'captcha' not in br.driver.current_url:
                        break
                    else:
                        time.sleep(1)

                if not Yandex.is_yandex_captcha(br.driver.current_url):
                    break
                else:
                    raise CaptchaException("Yandex captcha not solved (sended code: %s)." % code)
            except AntigateNotAvailable as e:
                error("%s => %s" % (br, e))
                raise CaptchaException(str(e))
            except Exception as e:
                error("%s => %s" % (br, e))
                if i == (cnt_attempts-1):
                    raise CaptchaException(str(e))


class BrowserPool():
    def __init__(self, pool_name):
        self._pool = []
        self.next_ip = -1
        self.last_reboot = None
        self.last_reboot_server_num = None
        self.name = pool_name

    def add(self, br):
        br.pool_id = len(self._pool)
        self._pool.append(br)

    def next(self):
        if len(self._pool) == 0:
            raise NoBrowsers
        self.next_ip += 1
        self.next_ip %= len(self._pool)
        return self._pool[self.next_ip]

    def release_server(self, server):
        info("\n=============================\nStart release_server %s\n==============================" % server)
        for br in self._pool:
            if br.host == server.host:
                br.set_busy(server.reboot_exec_sec)
                info("br.existed_session to remove for %s: %s, driver=%s" % (br, br.existed_session, br.driver))
                br.quit()
                #br.driver = None
                #br.existed_session = None
                info("br.existed_session removed2 for %s: %s, driver=%s" % (br, br.existed_session, br.driver))

    def get(self):

        now = int(time.time())

        #if self.last_reboot is not None and self.last_reboot<(now-Server.reboot_exec_sec):
        #    self.last_reboot = None
        #    self.last_reboot_server_num = None

        for i in range(len(self._pool)):
            br = self.next()

            if br.server.reboot:
                warning("Server %s in rebooting" % br.server)
                continue
            

            if br.server.need_reboot and self.last_reboot is None:
                debug("====> NEED REBOOT SERVER %s" % br.server)
                if not br.server.reboot:
                    br.server.reboot = True
                    reboot_thread = threading.Thread(target=reboot_server, args=(br.server, self))
                    self.release_server(br.server)
                    reboot_thread.start()
                    self.last_reboot = now
                    self.last_reboot_server_num = br.server.server_num
                continue
            else:
                if not br.is_busy or (br.is_busy and br.is_busy_time<now):
                    return br
                else:
                    warning("%s is busy = %s, need wait %s sec" % (br, br.is_busy, (br.is_busy_time - now)))
        return None


    def update(self, br):
        real_br = self._pool[br.pool_id]
        for k,v in br.__dict__.iteritems():
            if k!='server' and hasattr(real_br, k): # server это объект, работает через указатели - переписывать нельзя
                setattr(real_br, k, v)
        self._pool[br.pool_id] = real_br

    def size(self):
        return len(self._pool)

    def close(self):
        info("Try to close %s browsers" % len(self._pool))
        for br in self._pool:
            br.quit()
    
    def set_reboot_server(self, server_num):
        for br in self._pool:
            if br.server.server_num == server_num:
                info("REQUESTED REBOOT OF SERVER %s with last_reboot_time=%s" % (server_num, br.server.last_reboot_time))
                br.server.reboot_time = int(time.time()) - 1
                break

# into the thread
def reboot_server(server, pool):
    info("===== Start thread for reboot %s" % server)
    setproctitle("%s Reboot %s" % (pool.name, server.server_name))
    server.perform_reboot(pool)


class Server():
    reboot_minutes = 30
    reboot_exec_sec = 90

    def __init__(self, host, cnt_servers, client_id, api_key, server_num):
        self.host = host
        self.server_num = server_num
        self.client_id = client_id
        self.api_key = api_key
        self.reboot_time = None
        self.reboot = False
        self.create_date = int(time.time())
        self.cnt_servers = cnt_servers
        self.set_reboot_time()
        self.last_reboot_time = None

    @property
    def server_name(self):
        return 'viking%s' % self.server_num

    def __str__(self):
        return '%s' % self.host

    def set_reboot_time(self):
        if self.server_num is not None and self.cnt_servers > 1:
            self.reboot_time = int(time.time())+(self.reboot_minutes*60)
            info("New reboot time for server %s: %s" % (self.server_num, self.reboot_time))
            #if self.reboot_time is None:
            #    self.reboot_time = int(time.time())+(self.reboot_minutes*60*self.server_num)
            #else:
            #    self.reboot_time = self.reboot_time+(self.reboot_minutes*60*self.cnt_servers)
        if self.cnt_servers == 1:
            self.reboot_time = None

    @property
    def need_reboot(self):

        if self.reboot_time is not None and self.reboot_time<int(time.time()):
            info("Need reboot server %s, because reboot_time=%s" % (self.server_num, self.reboot_time))
            return True
        else:
            return False

    def get_server_id(self):
        json_str = urllib.urlopen('https://api.digitalocean.com/droplets/?client_id=%s&api_key=%s' % (self.client_id, self.api_key))
        servers_list = json.loads(json_str.read())
        if servers_list['status']!='OK':
            raise DigitalOceanException(servers_list)

        server_id = None
        for s in servers_list['droplets']:
            if s['ip_address']==unicode(self.host):
                server_id = s['id']
                break

        if server_id is None:
            raise DigitalOceanException('Undefined server with name: %s' % self.server_name)
        info("server_id: %s" % server_id)
        return server_id

    def reboot_dc_server(self, server_id, wait=False):
        info("Send reboot request to server %s." % server_id)
        json_str = urllib.urlopen('https://api.digitalocean.com/droplets/%s/reboot/?client_id=%s&api_key=%s' % (server_id, self.client_id, self.api_key))
        json_str = json_str.read()
        json_str = json.loads(json_str)
        if wait:
            time.sleep(self.reboot_exec_sec)

    def perform_reboot(self, pool):

        self.reboot = True
        info("Start reboot...")

        try:
            server_id = self.get_server_id()
            self.reboot_dc_server(server_id, True)
            self.set_reboot_time()
        except Exception as e:
            error("Error when digitalocean get droplets list: %s" % str(e))
        finally:
            info("\n===========================================\nServer successfully rebooted\n===============================================")
            self.reboot = False
            self.last_reboot_time = int(time.time())
            pool.last_reboot = None
            pool.last_reboot_server_num = None
            for br in pool._pool:
                if br.host == self.host:
                    info("br.existed_session %s is: %s, driver is %s" % (br, br.existed_session, br.driver))
                    br.quit()
                    info("br.existed_session after hardremove %s is: %s, driver is %s" % (br, br.existed_session, br.driver))


class RemoteBrowser():

    reconnect_requests_limit = 20000

    def __init__(self, name, server, port, db_config, session=None):
        self.server = server
        self.db_config = db_config
        self.host = server.host
        self.path = 'http://%s:%s/wd/hub' % (self.host, port)
        self.port = port
        self.name = name
        self.driver = None
        self.created_time = datetime.now()
        self.count_requests = 0
        self.count_captcha = 0
        self.id = None
        self.existed_session = session
        self.is_busy = False
        self.is_busy_time = None
        self.count_requests_for_dump = 0
        self.pool_id = None
        self.last_url_data = None

    def setCookie(self, cname, cvalue, cdomain = None, cpath = None, cexpires = int(time.time()) + 3600):
        cookie = {'name' : cname, 'value' : str(cvalue), "path":(cpath or "/"), "domain":cdomain, "expiry":cexpires}
        self.driver.add_cookie(cookie)

    def __str__(self):
        return '%s at %s' % (self.name, self.host)

    def set_busy(self, seconds=1200):
        self.is_busy = True
        self.is_busy_time = int(time.time()) + seconds

    def unset_busy(self):
        self.is_busy = False
        self.is_busy_time = None



    def _setup_browser(self):
        pass

    def connect(self):

        # close old session if exists
        self.quit() 
        
        info("Start selenium session %s: %s" % (self.name, self.path))
        
        existd_session_id = self.existed_session.session_id if self.existed_session is not None else None
        
        info("existed_session_id is %s" % existd_session_id)

        self.driver = PersistentWebdriver(self.path, webdriver.DesiredCapabilities.FIREFOX, session_id=existd_session_id)
        info("\n========================\nSET DRIVER FOR %s: %s\n=========================" % (self, self.driver))
        self.driver.implicitly_wait(500)
        self.driver.set_page_load_timeout(60)
        self.driver.set_script_timeout(60)
        self.count_requests = 0
        self.count_captcha = 0

        db = get_sql_session(self.db_config)
        if existd_session_id is not None and self.driver.session_id!=existd_session_id:
            info("Was created new session! delete zombi session in database")
            db.delete(self.existed_session)
            db.commit()
            self.existed_session = None

        if self.existed_session is None:
            ses_obj = SeleniumSession(server = self.host, session_id = self.driver.session_id, create_date = self.created_time)
            db.add(ses_obj)
            db.commit()
            self.id = ses_obj.id
        else:
            self.id = self.existed_session.id

        self._setup_browser()

    def execute_js_with_jquery(self, js):
        self.driver.execute_script("""
            function addJQuery(callback) {
                var script = document.createElement('script');
                script.setAttribute('src', '//ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js');
                script.addEventListener('load', function() {
                   var script = document.createElement('script');
                   script.textContent = '(' + callback.toString() + ')();';
                   document.body.appendChild(script)
                }, false);
                document.body.appendChild(script)
            }
            function main() {
                %s
            }
            addJQuery(main)
        """ % js)

    def wait_element_by_xpath(self, xpath, timeout = 10):
        wait = ui.WebDriverWait(self.driver, timeout)
        return wait.until(lambda driver: driver.find_element_by_xpath(xpath))

    def prepare(self):
        if self.driver is None or self.count_requests>self.reconnect_requests_limit:
            info("self.driver is %s" % self.driver)
            self.connect()

    def get_url_data(self, url):
        url_data = urlparse.urlparse(url)
        qs = urlparse.parse_qs(url_data.query)
        return {'data':url_data, 'qs':qs}

    def get(self, url, do_request = True):

        self.prepare()

        url_data = urlparse.urlparse(url)
        qs = urlparse.parse_qs(url_data.query)
        self.last_url_data = self.get_url_data(url)

        if do_request:
            self.driver.get(url)

        self.count_requests += 1

        self.count_requests_for_dump += 1
        info("Captcha stat for %s: %s/%s" % (self.name, self.count_captcha, self.count_requests))
        if self.count_requests_for_dump>0:
            
            db = get_sql_session(self.db_config)
            session = db.query(SeleniumSession).get(self.id)
            session.cnt_requests = self.count_requests
            session.cnt_captcha = self.count_captcha
            session.last_request_date = datetime.now()
            db.commit()

            self.count_requests_for_dump = 0

    def quit(self):
        info("quits from %s ..." % self)
        if self.driver is not None:
        
            # На зависших браузерах не удается выполнить.
            # Если возвращать, то с таймаутом,а то он ждет вечно
            #try:
            #    self.driver.quit()
            #except Exception as e:
            #    error("Error when selenium quit: %s" % e)
            
            self.driver = None
            self.existed_session = None

            info('delete from db: %s' % self.id)

            db = get_sql_session(self.db_config)
            session = db.query(SeleniumSession).get(self.id)
            if session is not None:
                db.delete(session)
                db.commit()


def serve_pool(pool, host, port):
    setproctitle(pool.name)
    listener = Listener((host, port), backlog=300)

    c = 0
    info("Browser pool started")
    while True:
        try:
            debug("serve_pool wait connection")
            conn = listener.accept()
            data = conn.recv()
            comand = data[0]
            args = data[1] if len(data)>1 else []
            info('connection accepted from %s, command %s' % (str(listener.last_accepted), comand))

            if comand=='stop':
                info("Start stop selenium drivers...")
                pool.close()
                conn.send("OK")
                break
            elif comand=='get_browser':
                br = pool.get()
                conn.send(br)
                if br is not None:
                    br.set_busy()
            elif comand=='release_browser':
                br = args[0]
                need_reboot = args[1]
                need_reboot_server = args[2]
                if need_reboot_server:
                    pool.set_reboot_server(br.server.server_num)
                    br.unset_busy()
                elif need_reboot:
                    br.set_busy(3600)
                else:
                    br.unset_busy()
                pool.update(br)
            conn.close()
            debug("serve_pool conn close")
        except Exception as e:
            info('%s exception: %s' % (pool.name, e))
        except KeyboardInterrupt:
            break
    info("Browser pool stopped.")
    listener.close()


def get_sql_engine(DATABASE):
    return create_engine('%s://%s:%s@%s/%s' % (DATABASE['type'], DATABASE['user'],\
        DATABASE['passwd'], DATABASE['host'], DATABASE['db']), echo=False) 

def get_sql_session(DATABASE):
    sql_engine = get_sql_engine(DATABASE)
    return sessionmaker(bind=sql_engine)()

def start_service(SELENIUM_SERVERS, SELENIUM_SERVER, DATABASE, tcp_handler = None, PORT_2 = None, remote_browser = None,
                  restart = False):

    # create table if not exists
    metadata = SeleniumSession.metadata
    metadata.create_all(get_sql_engine(DATABASE))

    if tcp_handler is None:
        tcp_handler = SeleniumDefaultTCPHandler

    if remote_browser is None:
        remote_browser = RemoteBrowser

    proc_name = 'SocketServer_%s' % DATABASE['db']
    pool_name = 'BrowserPoolManager_%s' % DATABASE['db']

    def get_cnt_prc():
        p1 = processecControl(proc_name, 1, no_exit = True)
        p2 = processecControl(pool_name, 1, no_exit = True)
        return p1 + p2

    def kill_service():
        kill_process(proc_name)
        kill_process(pool_name)

    def restart_service():
        debug("Stop server.")
        for i in range(10):
            kill_service()
            if get_cnt_prc()>0:
                time.sleep(1)
            else:
                break

    def usage():
        print """
    USAGE: %s [options]
        -h --help                display this help
        -s --stop                stop all bots
        -r --reboot                reboot socket server
        -n --reboot_nodes        reboot all nodes
    """ % (sys.argv[0],)

    try:
        opts, args = getopt(sys.argv[1:], "hsrn", ["help", "stop", "reboot", "reboot_nodes"])
    except GetoptError, err:
        usage()
        sys.exit()

    if restart:
        opts.append(('-r', True))
    print opts
    reboot_nodes = False
    for o, value in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-s", "--stop", "-r", "--reload", "-n", "--reboot_nodes"):
            restart_service()
            if o in ("-s", "--stop"):
                sys.exit()
            if o in ("-n", "--reboot_nodes"):
                reboot_nodes = True


    processecControl(proc_name, 1)
    processecControl(pool_name, 1)
    setproctitle(proc_name)
    
    
    HOST = SELENIUM_SERVER['host']
    PORT = SELENIUM_SERVER['port']
    PORT_2 = PORT + 1 if PORT_2 is None else PORT_2
    SocketServer.TCPServer.allow_reuse_address = True
    info("Start serve %s:%s" % (HOST, PORT))
    info("tcp_handler: %s" % tcp_handler)
    
    server = ThreadedTCPServer((HOST, PORT), tcp_handler)


    max_socket_children = 0

    pool = BrowserPool(pool_name)

    try:
        db = get_sql_session(DATABASE)

        num = 0

        cnt_servers = len(SELENIUM_SERVERS)

        sessions_by_servers = {}

        for session in db.query(SeleniumSession).all():
            if session.server not in sessions_by_servers:
                sessions_by_servers[session.server] = []
            sessions_by_servers[session.server].append(session)
        
        server_num = 0
        avg_nodes_cnt = []
        for ip, port, cnt in SELENIUM_SERVERS:
            server_num += 1
            sessions = sessions_by_servers[ip] if ip in sessions_by_servers else []
            srv = Server(ip, cnt_servers, SELENIUM_SERVER['cliend_id'], SELENIUM_SERVER['api_key'], server_num)

            if reboot_nodes:
                sid = srv.get_server_id()
                srv.reboot_dc_server(sid)
                continue

            info('======== %s ========' % srv.server_name)
            max_socket_children += cnt
            avg_nodes_cnt.append(cnt)
            for i in range(cnt):
                num += 1
                name = "Browser %s" % num
                
                existed_session = sessions.pop() if len(sessions)>0 else None
                info('%s at %s, existed session %s' % (name, ip, existed_session.session_id if existed_session is not None else None))
                br = remote_browser(name, srv, port, db_config = DATABASE, session=existed_session)
                pool.add(br)
            if len(sessions)>0:
                warning("Excess %s sessions in %s. Remove it from DataBase" % (len(sessions), ip))
                for session in sessions:
                    db.delete(session)
                    db.commit()
                    warning("Session %s removed" % session.session_id)
        db.close()

        if reboot_nodes:
            info("Reboot finished.")
            sys.exit()

        # serve browser pool
        p = Process(target=serve_pool, args=(pool, HOST, PORT_2))
        p.daemon = True
        p.start()

        info("All selenium sessions created: %s" % pool.size())
        
        avg_nodes_cnt = sum(avg_nodes_cnt)/server_num
        info("avg_nodes_cnt: %s" % avg_nodes_cnt)

        max_socket_children -= avg_nodes_cnt
        max_socket_children -= max_socket_children*0.1
        max_socket_children = max(max_socket_children, avg_nodes_cnt)
        info("max_socket_children is %s" % max_socket_children)

        server.max_children = max_socket_children
        server.serve_forever((HOST, PORT_2))
    except KeyboardInterrupt:

        info("Start stop SocketServer...")
        server.shutdown()
        info("Server stopped.")