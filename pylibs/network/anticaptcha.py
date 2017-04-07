# -*- coding: utf-8 -*-

from pylibs.network import NetworkException
import time
import httplib, urllib, os
from logging import debug, error, info
from pylibs.network.browser import Browser


class AntiCaptchaException(NetworkException):
    pass

class AntigateNotAvailable(AntiCaptchaException):
    pass


class AntiGate():
    host = 'rucaptha.com'

    def __init__(self, key, url = None, br = None, host = None, img_data = None):
        self.br = Browser() if br is None else br
        self.key = key
        self.url = url
        self.img_data = img_data
        if host is not None:
            self.host = host

    def solve(self):
        
        if self.img_data is None:
            self.br.get(self.url)
            self.captcha_data = self.br.body()
        else:
            self.captcha_data = self.img_data

        debug("file downloaded!")
        fsize = len(self.captcha_data)
        debug('fsize: %s' % fsize)

        if int(fsize) == 0:
            raise AntiCaptchaException("ZeroSize of captcha image")


        try_times = 3
        for i in range(try_times):
            try:
                cap_id = self.send_cap()
                break
            except Exception as e:
                error(e)
                if i == try_times-1:
                    raise

        # get result
        status, text = self.get_cap_text(cap_id)
        
        text = unicode(text, 'utf-8')
        if status == 'ERROR':
            raise AntiCaptchaException(text)
        debug("AntiCaptcha: %s soved = %s" % (cap_id, text))
        return text



    def get_cap_text(self, cap_id):
        ''' Ожидаем и получаем текст капчи '''

        time.sleep(5)

        # получаем результат
        res_url= 'http://%s/res.php' % self.host
        res_url+= "?" + urllib.urlencode({'key': self.key, 'action': 'get', 'id': cap_id})
        while True:
            res = urllib.urlopen(res_url).read()
            if res == 'CAPCHA_NOT_READY':
                debug("AntiCaptcha: %s not ready" % (cap_id,))
                time.sleep(1)
                continue
            break

        res = res.strip().split('|')
        if len(res) == 2:
            return tuple(res)
        else:
            return ('ERROR', res[0])



    def send_cap(self):

        # разделитель для данных
        boundary= '----------OmNaOmNaOmNamo'

        # тело HTTP-запроса
        body = '''--%s
Content-Disposition: form-data; name="method"

post
--%s
Content-Disposition: form-data; name="key"

%s
--%s
Content-Disposition: form-data; name="file"; filename="capcha.jpg"
Content-Type: image/jpeg

%s
--%s--

''' % (boundary, boundary, self.key, boundary, self.captcha_data, boundary)

        # заголовки HTTP-запроса
        headers = {'Content-type' : 'multipart/form-data; boundary=%s' % boundary}

        # подключение к HTTP-серверу
        h = httplib.HTTPConnection(self.host)
            

        # посылка запроса
        try:
            h.request("POST", "/in.php", body, headers)
        except Exception as e:
            raise AntigateNotAvailable(str(e))

        # получение и анализ ответа HTTP-сервера
        resp = h.getresponse()
        data = resp.read()
        h.close()

        if data.startswith('ERROR_'):
            raise AntiCaptchaException('Captcha not send: %s' % data)

        if resp.status == 200:
            cap_id = int(data.split('|')[1])
            debug("AntiCaptcha: got id %s" % (cap_id,))
            return cap_id
        else:
            raise AntiCaptchaException('Captcha not send: %s %s' % (resp.status, resp.reason))



def solveImgUrl(key, captcha_url = None, br = None, host = None, img_data = None):
    a = AntiGate(key, captcha_url, br, host, img_data)
    return a.solve()





