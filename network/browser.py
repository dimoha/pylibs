# -*- coding: utf-8 -*-
from pylibs.network import NetworkException
from pylibs.network.parser import *
from pylibs.network.urls import *
from pylibs.utils.text import strip_tags
import pycurl, re, os, cookielib, time, urllib,  json
from cStringIO import StringIO
from urllib2 import Request
from logging import debug, info, warning, error

class BrowserException(NetworkException):
    pass

class BadHttpStatus(BrowserException):
    def __init__(self, msg = False):
        BrowserException.__init__(self, msg)
        statuses = {'100': 'Continue', '101': 'Switching Protocols', '201': 'Created', '202': 'Accepted', '203': 'Non-Authoritative Information', '204': 'No Content', '205': 'Reset Content', '206': 'Partial Content', '300': 'Multiple Choices', '301': 'Moved Permanently', '302': 'Found', '303': 'See Other', '304': 'Not Modified', '305': 'Use Proxy', '307': 'Temporary Redirect', '400': 'Bad Request', '401': 'Unauthorized', '402': 'Payment Required', '403': 'Forbidden', '404': 'Not Found', '405': 'Method Not Allowed', '406': 'Not Acceptable', '407': 'Proxy Authentication Required', '408': 'Request Timeout', '409': 'Conflict', '410': 'Gone', '411': 'Length Required', '412': 'Precondition Failed', '413': 'Request Entity Too Large', '414': 'Request-URI Too Long', '415': 'Unsupported Media Type', '416': 'Requested Range Not Satisfiable', '417': 'Expectation Failed', '500': 'Internal Server Error', '501': 'Not Implemented', '502': 'Bad Gateway', '503': 'Service Unavailable', '504': 'Gateway Timeout', '505': 'HTTP Version Not Supported'}
        self.code = int(self.message)
        if str(self.message) in statuses:
            self.message = str(self.message)+" "+statuses[str(self.message)]

class CannotResolve(BrowserException):
    pass

class ConnectionTimeOut(BrowserException):
    pass

class CurlError(BrowserException):
    pass

class Browser():


    def tab(self):
        br = Browser(self.cookie_file)
        br.ip_address = self.ip_address
        br.user_agent = self.user_agent
        br.referer = None
        br.connect_timeout = self.connect_timeout
        br.timeout = self.timeout
        br.maxredirs = self.maxredirs
        br.proxy_port = self.proxy_port
        br.proxy_type = self.proxy_type
        br.proxy = self.proxy
        return br
        
    def __init__(self, cookie_file = None):
        self.cookie_file = cookie_file
        self.closed = False
        self._body = StringIO()
        self._header = StringIO()
        self.ip_address = None
        self.user_agent = 'Mozilla/5.0 (Windows NT 5.1; rv:19.0) Gecko/20100101 Firefox/19.0' 
        self.referer = None
        self.connect_timeout = None
        self.perform_url = None
        self.effective_url = None
        self.http_status = None
        self._html = None
        self._json = None
        self._text = None
        self.timeout = 15
        self.name = str(id(self))
        self.page_handler = None
        self.maxredirs = 10
        self.pages_headers = []
        self.block_cookie = True
        self.current_cookies = {}
        self.curl = None
        self.user_pwd = None
        self.ssl_cert = None
        self.ssl_key = None
        
        self.proxy = None
        self.proxy_port = None
        self.proxy_type = None

    def __str__(self):
        return self.name
    
    def save_cookie_file(self,permanent_cookie_file = None):
        if permanent_cookie_file and permanent_cookie_file != self.cookie_file:
            os.remove(permanent_cookie_file)
            os.rename(self.cookie_file, permanent_cookie_file)
            self.cookie_file = permanent_cookie_file
        
    

        
    
    def printCookies(self, jar = None):
        for cookie in jar or self.getCookieJar():
            debug(cookie.name + "=" + str(cookie.value))
    
    
    ###################### special class for extract_cookies
    class headerInfo():
        def __init__(self, s):
            self.headers = {}
            for one in s.replace("\r", "\n").split("\n"):
                oneList = one.strip().split(":")
                tc = oneList[0].strip()
                if tc!='':
                    if tc not in self.headers:
                        self.headers[tc] = []
                    self.headers[tc].append(":".join(one.split(':')[1:]).strip())
    
        def info(self):
            return self
        
        def getheaders(self, name):
            if name in self.headers:
                return self.headers[name]
            return []

        def getallmatchingheaders(self, name):
            res = []
            if name in self.headers:
                for val in self.headers[name]:
                    res.append('%s: %s\r\n' % (name, val))
            return res

    
    def saveCookies(self):
        ho = self.headerInfo(self._header.getvalue())
        req = Request(self.perform_url)
        jar = self.getCookieJar(True)
        jar.extract_cookies(ho, req)
        # костыль под беларусский регион в гугле и под казахстанский. до лучших времен пока гугл багу не поправит
        if 'google.' in self.perform_url:
            jar.extract_cookies(ho, Request('google.com'))
        self.current_cookies = jar._cookies
    
    ###########################################################
    def _process_cookies(self, work_type, ck):
        if work_type=='read':
            try:
                ck.load()
            except:
                pass
        else:
            jar = self.getCookieJar(True);
            jar.set_cookie(ck)
            jar.save(ignore_discard=True, ignore_expires=True)

    def _work_with_cookies(self, work_type='read', ck=None, withLock=False):
        self._process_cookies(work_type, ck)

        return ck

    def getCookieJar(self, withLock=True):
        cookie_jar = cookielib.MozillaCookieJar(self.cookie_file)
        self._work_with_cookies('read', cookie_jar, withLock)
        return cookie_jar
    
    def setCookie(self, cname, cvalue, cdomain = None, cpath = None, cexpires = int(time.time()) + 3600):
        ck = cookielib.Cookie(version=0, name=cname, value=cvalue, port=None, port_specified=False, domain=(cdomain or "www.example.com"), domain_specified=(not cdomain is None), domain_initial_dot=False, path=(cpath or "/"), path_specified=(not cpath is None), secure=False, expires=cexpires, discard=False, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        self._work_with_cookies('write', ck, True)

    def getCookie(self, name, domain = None):
        for cookie in self.getCookieJar():
            if cookie.name == name:
                if not domain or domain == cookie.domain:
                    return cookie.value
        return None

    def removeDuplicatesCookies(self, cookies):
        names = []
        for ck in cookies:
            names.append(ck['name'])
        need_save = False
        jar = self.getCookieJar()
        for cookie in jar:
            if cookie.name in names:
                jar.clear(cookie.domain, cookie.path, cookie.name)
                need_save = True
        jar.save(ignore_discard=True, ignore_expires=True)


    def set_useragent(self):
        lastNum = int(self.ip_address[-2:].replace('.', ''))
        agents = [
                'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/18.6.872.0 Safari/535.2 UNTRUSTED/1.0', 
                'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3', 
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6', 
                'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6', 
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', 
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/28.0.1469.0 Safari/537.36', 
                'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/28.0.1469.0 Safari/537.36', 
                'Mozilla/5.0 (Windows NT 6.1; rv:12.0) Gecko/20120403211507 Firefox/12.0', 
                'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1',
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20120427 Firefox/15.0a1', 
                'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0) Gecko/16.0 Firefox/16.0', 
                'Mozilla/5.0 (Windows NT 6.2; rv:19.0) Gecko/20121129 Firefox/19.0', 
                'Mozilla/5.0 (Windows NT 6.2; rv:20.0) Gecko/20121202 Firefox/20.0', 
                'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Maxthon 2.0)', 
                'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.1 (KHTML, like Gecko) Maxthon/3.0.8.2 Safari/533.1', 
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML like Gecko) Maxthon/4.0.0.2000 Chrome/22.0.1229.79 Safari/537.1', 
                'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)', 
                'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)', 
                'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/4.0)', 
                'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)', 
                'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/5.0)', 
                'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)', 
                'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.2; Trident/5.0)', 
                'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.2; WOW64; Trident/5.0)', 
                'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)', 
                'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/6.0)', 
                'Opera/9.25 (Windows NT 6.0; U; en)', 
                'Opera/9.80 (Windows NT 5.2; U; en) Presto/2.2.15 Version/10.10', 
                'Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.7.39 Version/11.00', 
                'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.7.62 Version/11.01', 
                'Opera/9.80 (Windows NT 5.1; U; zh-tw) Presto/2.8.131 Version/11.10', 
                'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00', 
                'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10', 
                'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/533.17.8 (KHTML, like Gecko) Version/5.0.1 Safari/533.17.8', 
                'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5', 
                'Mozilla/5.0 (Windows; U; Windows NT 6.2; es-US ) AppleWebKit/540.0 (KHTML like Gecko) Version/6.0 Safari/8900.00', 
                'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.1.17) Gecko/20110123 (like Firefox/3.x) SeaMonkey/2.0.12', 
                'Mozilla/5.0 (Windows NT 5.2; rv:10.0.1) Gecko/20100101 Firefox/10.0.1 SeaMonkey/2.7.1', 
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20120422 Firefox/12.0 SeaMonkey/2.9', 
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:15.0) Gecko/20100101 Firefox/15.0.1'
            ]
        lastNum %= len(agents)
        self.user_agent = agents[lastNum]
        #self.user_agent = 'YB/5.1.1'
        

    def _curl_init(self, curl, cookies=None):
        self._body.truncate(0)
        self._header.truncate(0)
        self._html = None
        self._text = None
        curl.setopt(curl.HEADERFUNCTION, self._header.write)
    
        if cookies is not None:
            self.removeDuplicatesCookies(cookies)
            cookie_to_send = []
            for cookie in cookies:
                cookie_to_send.append('%s=%s' % (cookie['name'], cookie['value']))
            curl.setopt(pycurl.COOKIE, "; ".join(cookie_to_send))
        if self.cookie_file:
            curl.setopt(pycurl.COOKIEFILE, self.cookie_file)
            curl.setopt(pycurl.COOKIEJAR, self.cookie_file)

        curl.setopt(pycurl.FOLLOWLOCATION, 1)
        curl.setopt(pycurl.MAXREDIRS, self.maxredirs)
        curl.setopt(pycurl.USERAGENT, self.user_agent)
        curl.setopt(pycurl.ENCODING, "gzip")
        curl.setopt(pycurl.NOSIGNAL, 1)
        curl.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)
        if self.ssl_cert:
            curl.setopt(pycurl.SSLCERT, self.ssl_cert)
        if self.ssl_key:
            curl.setopt(pycurl.SSLKEY, self.ssl_key)

        if self.timeout:
            curl.setopt(pycurl.TIMEOUT, self.timeout)
        if self.ip_address:
            self.set_useragent()
            curl.setopt(pycurl.INTERFACE, self.ip_address)
        if self.effective_url and not self.referer:
            self.referer = self.effective_url
        
        if self.referer:
            curl.setopt(pycurl.REFERER, self.referer)
        if self.connect_timeout:
            curl.setopt(pycurl.CONNECTTIMEOUT, self.connect_timeout);
        
        if self.proxy:
            curl.setopt(pycurl.PROXY, self.proxy)
            curl.setopt(pycurl.PROXYPORT, self.proxy_port)
            if self.proxy_type == 'socks5':
                curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)

        if self.pages_headers:
            curl.setopt(pycurl.HTTPHEADER, self.pages_headers)

        if self.user_pwd is not None:
            curl.setopt(pycurl.USERPWD, self.user_pwd)
        
        self.curl = curl

    def curlException(self,e):
        message = e[1]
        code = e[0]
        known = {
            6:CannotResolve(get_domain(self.perform_url)),
            28:ConnectionTimeOut(message+' ('+self.perform_url+')')
        }
        
        if code in known.keys():
            return known[code]
        else:
            return CurlError("%s, error code = %s" % (message,code))


    def _curl_info(self, curl):
        self.effective_url = curl.getinfo(pycurl.EFFECTIVE_URL)
        self.http_status = curl.getinfo(pycurl.HTTP_CODE)
        self.saveCookies()

    def get(self, url, headers = {}, cookies = None):
        curl = pycurl.Curl()
        self.perform_url = url
                
        if len(headers)>0:
            self.headers = headers
    
        self._curl_init(curl, cookies=cookies)
        
        url = url_to_pynicode(url) 


        curl.setopt(pycurl.URL, str(url))
        curl.setopt(curl.WRITEFUNCTION, self._body.write)
        try:
            curl.perform()
        except pycurl.error as e:
            raise self.curlException(e)
        self._curl_info(curl)
        curl.close()
        if self.http_status != 200:
            raise BadHttpStatus, self.http_status
        
        if self.page_handler is not None:
            self.page_handler(self)

        return self._body.getvalue()
        
    def post(self, url, fields = None, postdata = None, content_type = None, cookies = None, files = None):
        self.perform_url = url
                
        if fields is not None:
            postdata = urllib.urlencode(fields)
        
        curl = pycurl.Curl()
        self._curl_init(curl, cookies=cookies)
        
        url = url_to_pynicode(url) 
        curl.setopt(pycurl.URL, str(url))
        curl.setopt(curl.WRITEFUNCTION, self._body.write)
        curl.setopt(pycurl.POST, 1)
        
        if postdata is not None:
            curl.setopt(pycurl.POSTFIELDS,postdata)
        if content_type is not None:
            curl.setopt(pycurl.HTTPHEADER, ["Content-type: %s" % content_type])
        
        if files is not None:
            to_send = []
            if postdata is not None and postdata!='':
                to_send = map(lambda x: tuple(x.split('=')) if '=' in x else (x, '') , postdata.split('&'))
            for filename in files:
                to_send.append((os.path.basename(filename), (curl.FORM_FILE, filename)))                
            debug(to_send)
            curl.setopt(curl.HTTPPOST, to_send)
    
        
        try:
            curl.perform()
        except pycurl.error as e:
            raise self.curlException(e)
        
        self._curl_info(curl)
        curl.close()
        
        if self.http_status != 200:
            raise BadHttpStatus, self.http_status

        if self.page_handler is not None:
            self.page_handler(self)
        return self._body.getvalue()
    
    def relative_url(self, url):
        return self._action_url(url)
    
    def _action_url(self,action):
        return urljoin(self.effective_url, action if action is not None else '')
    
    def postForm(self, form, addparams = {}):
        utf8data = {}
        utf8data.update(form.fields)
        utf8data.update(addparams)
        for field, value in utf8data.iteritems():
            if isinstance(value,unicode):
                utf8data[field] = value.encode("utf-8")
        if not self.perform_url:
            raise AppException('effective_url is not set')
        if form.method.lower() == 'post':
            return self.post(self._action_url(form.action), utf8data)
        else:
            return self.get(self._action_url(form.action) + "?" + urllib.urlencode(utf8data))        
    
    def download(self, filename, url):
        self.perform_url = url
        curl = pycurl.Curl()
        self._curl_init(curl)
        self.perform_url = url
        f = open(filename, "wb")
        curl.setopt(pycurl.URL, str(url))
        curl.setopt(curl.WRITEDATA, f)
        curl.perform()
        self._curl_info(curl)
        curl.close()
        f.close
        return self._body.getvalue()
        
    def close(self):
        self.closed = True
    
    def body(self):
        return self._body.getvalue()    
    
    @property
    def headers(self):
        allheaders =  self._header.getvalue()
        headers = allheaders.split("\r\n\r\nH")
        headers_dict = {}
        for v in  headers[-1].strip().split("\r\n"):
            v = v.split(": ") if ": " in v else [v]
            if len(v) == 2:
                headers_dict[v[0]] = v[1]
        return headers_dict

    def html(self):
        if self._html is None:
            self._html = parse_html(self.unicode())
        return self._html
    
    def unicode(self):
        if self._text is None:
            self._text = self.__convert_page_encoding()
        return self._text
    
    def json(self):
        if self._json is None:
            self._json = json.loads(self.body())
        return self._json
    

    def __convert_page_encoding(self):
        
        enclist = {'win-1251':'windows-1251', 'windows-1251':'windows-1251', 'cp-1251':'windows-1251', 'cp1251':'windows-1251', 'utf8':'utf-8', 'utf-8':'utf-8', 'koi8':'koi8-r', 'koi-8':'koi8-r', 'koi8-r':'koi8-r'}
        enc = ''
    

        #s = re.sub('<!--\s*([/]?)noindex\s*-->(?is)', '<\\1noindex>', self.body())
        #s = re.sub('<!--.*?-->(?is)', ' ', s);
        s = self.body().replace("\r\n", "\n")
        
        h = self._header.getvalue()

    
        # detecting encoding by header
        if enc=='':
            m = re.search("content-type:[^\n]+charset=([^\n\s]+)(?is)", h)
            if m:
                h = m.group(1).strip('"\'<> ').lower()
                if enclist.has_key(h):
                    enc = enclist[h]
        
        
        # detecting encoding by meta
        if enc=='':
            m = re.search("<meta[^>]+http-equiv=[\"']?Content-type[\"']?[ \t\n]+content=[\"']?([^;>\"']+);[ \t\n]*charset=([^\"'>]+)[\"']?[ \t\n]*/?>(?is)", s)
            if m:
                h = m.group(2).strip('"\'<> ').lower()
                if enclist.has_key(h):
                    enc = enclist[h]    

        
        if enc=='':
            m = re.search("<meta[^>]+content=[\"']?([^;]+);[^>]*charset=([^\"']+)[\"']?[^>]+http-equiv=[\"']?Content-type[\"']?[^>]*>(?is)", s)
            if m:
                h = m.group(2).strip('"\'<> ').lower()
                if enclist.has_key(h):
                    enc = enclist[h]        
        
        
        # detecting encoding by xml prolog
        if enc=='':
            m = re.search("<\?xml[^>]+encoding=[\"']?([^\s>'\"]+)[\"']?[^>]*>(?is)", s)
            if m:
                h = m.group(1).strip('"\'<> ').lower()
                if enclist.has_key(h):
                    enc = enclist[h]    
        
        # autodetecting
        if enc=='':
            enc = self.__charset_auto_detect(s)        
        
            
        # converting
        if enc=='':
            enc = 'utf-8'
            try:
                tmp = s.decode(enc)
                s = tmp
            except:
                enc = 'windows-1251'
                try:
                    tmp = s.decode(enc)
                    s = tmp
                except:
                    enc = 'koi8-r'
                    try:
                        tmp = s.decode(enc)
                        s = tmp

                    except:
                        pass
        else:
            s = s.decode(enc, 'replace')

        # УДАЛЯЕМ мета теги указывающие на кодировку. LXML глючить может из за них
        # Similarly, you will get errors when you try the same with HTML data in a unicode string that specifies a charset in a meta tag of the header. 
        # You should generally avoid converting XML/HTML data to unicode before passing it into the parsers. 
        # It is both slower and error prone.(http://lxml.de/parsing.html)
        s = re.sub("<meta[^>]+charset[^>]+>(?is)", '', s)
        s = re.sub("<\?xml[^>]+encoding=[\"']?([^\s>'\"]+)[\"']?[^>]*>(?is)", '', s)
        
        return s


    def __charset_auto_detect(self, s):
        counters = {'windows-1251':0, 'koi8-r':0}
        patterns = {193:'koi8-r', 201:'koi8-r', 207:'koi8-r', 212:'koi8-r', 225:'koi8-r', 233:'koi8-r', 239:'koi8-r', 244:'koi8-r', 192:'windows-1251', 200:'windows-1251', 206:'windows-1251', 210:'windows-1251', 224:'windows-1251', 232:'windows-1251', 238:'windows-1251', 242:'windows-1251'}
        try:
            s = s.decode('utf-8')
            enc = 'utf-8'
        except:
            s = strip_tags(s)
            for x in s:
                char = ord(x)
                if (char<128) or (char>256): continue;
                if patterns.has_key(char):
                    counters[patterns[char]] = counters[patterns[char]] + 1
            counters = dict(map(lambda item: (item[1],item[0]),counters.items()))        
            enc = counters[max(counters.keys())];
        return enc
