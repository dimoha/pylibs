# -*- coding: utf-8 -*-
from pylibs.seo import SeoException
from pylibs.network.parser import *
from logging import info, warning, debug
from pylibs.network.browser import Browser
from pylibs.network.anticaptcha import solveImgUrl

class YandexException(SeoException):
    pass

class YandexAuthorizationException(YandexException):
        pass

class Yandex(object):


    def __init__(self, transport=None, cookie_file = None, anticaptcha_key=None, anticaptcha_host = None, account = None):
        self.transport =  Browser(cookie_file=cookie_file) if transport is None else transport
        self.anticaptcha_key = anticaptcha_key
        self.anticaptcha_host = anticaptcha_host
        self.transport.yandex_account = account
        self.transport.page_handler = yandex_authorization

    def request(self, url = None, post_form = None, post = None):
        debug(url)
        
        if post_form is not None:
            self.transport.postForm(post_form, post)
        elif post is not None:
            self.transport.post(url)
        else:
            self.transport.get(url)

        self.html = parse_html(self.transport.unicode())
        if self.is_captcha():
            warning("Need antigate request, because captcha cathed.")
            if self.anticaptcha_key is None:
                raise YandexException("Need antigate key.")
            self.solve_captcha()
        return self.html

    def is_captcha(self):
        return Yandex.is_yandex_captcha(self.transport.effective_url)

    @staticmethod
    def is_yandex_captcha(effective_url):
        if re.search('yandex.[^/]+/showcaptcha', effective_url)\
            or re.search('captcha.yandex.', effective_url):
            return True
        else:
            return False

    def _get_captcha_form(self):
        form = at_css(self.html, "div.b-captcha form")
        if form is None:
            form = at_xpath(self.html, '//form[contains(@action, "checkcaptcha")]')   
        return form

    def _get_captcha_img(self, form):
        img = None
        if form is not None:
            img = at_css(form, "img.b-captcha__image")
            if img is None:
                img = at_css(form, "img.b-captcha__image_exp")
        return img

    def _fill_captcha_form(self, form, captcha_value):
        form.fields['rep'] = captcha_value
        return form

    def solve_captcha(self):

        form = self._get_captcha_form()
        img = self._get_captcha_img(form)

        effective_url_init = self.transport.effective_url
        if form is None or img is None:
            raise YandexException('Not found form or img on captcha page.')

        try:
            captcha_url = img.attrib['src']
        except:
            raise YandexException('Not found src attribute of captcha image element.')

        debug('captcha_url: %s' % captcha_url)
        captcha_value = solveImgUrl(self.anticaptcha_key, captcha_url=captcha_url,\
            br=self.transport, host=self.anticaptcha_host)
        
        debug('captcha_value: %s' % captcha_value)

        form = self._fill_captcha_form(form, captcha_value)

        self.transport.effective_url = effective_url_init
        self.transport.postForm(form)

        return not self.is_captcha()



def yandex_authorization(br):
    
    if hasattr(br, 'yandex_account'):

        user = br.yandex_account['user']
        password = br.yandex_account['password']

        login_input = at_xpath(br.html(),'//input[@id="login"]')
        auth_form = at_xpath(br.html(), '//form[contains(@action,"passport")]')

        if auth_form is None and login_input is not None:
            _auth_form = at_xpath(br.html(),'//form')
            if 'login' in _auth_form.fields:
                info("catched strange auth form")
                auth_form = _auth_form


        if auth_form is not None:
            info('Start auth in Yandex: %s => %s' % (user, password))
            auth_form.fields['login'] = unicode(user)
            auth_form.fields['passwd'] = unicode(password)
            auth_form.fields['twoweeks'] = True


            debug("START POST")
            br.postForm(auth_form,{'timestamp':time.time()})
            debug("END POST")

            auth_form_again = at_xpath(br.html(),'//form[contains(@action,"passport")]')
            login_form_again = at_xpath(br.html(),'//input[@id="login"]')

            if auth_form_again is not None:
                raise YandexAuthorizationException('Authorization Fail. Auth form Twice.')

            if at_xpath(br.html(),'//input[@id="login"]') is not None:
                raise YandexAuthorizationException('Authorization Fail. input login Twice.')

            if 'ваш браузер не поддерживает автоматическое перенаправление' in br.body():
                info('Auto refrsh page detected, perform_url: %s' % br.perform_url)
                br.get(br.perform_url)
                if br.page_handler.__name__=='yandex_authorization':
                    br.page_handler = None
            else:
                debug("Auth success!")

