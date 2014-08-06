# -*- coding: utf-8 -*-
from seo import SeoException
from pylibs.network.parser import *
from logging import info, warning, debug
from pylibs.network.browser import Browser
from pylibs.network.anticaptcha import solveImgUrl

class YandexException(SeoException):
    pass

class Yandex(object):


    def __init__(self, transport=None, cookie_file = None, anticaptcha_key=None, anticaptcha_host = None):
        self.transport =  Browser(cookie_file=cookie_file) if transport is None else transport
        self.anticaptcha_key = anticaptcha_key
        self.anticaptcha_host = anticaptcha_host

    def request(self, url):
        self.transport.get(url)
        self.html = parse_html(self.transport.unicode())
        if self.is_captcha():
            warning("Need antigate request, because captcha cathed.")
            if self.anticaptcha_key is None:
                raise YandexException("Need antigate key.")
            self.solve_captcha()
        return self.html

    def is_captcha(self):
        if re.search('yandex.[^/]+/showcaptcha', self.transport.effective_url)\
            or re.search('captcha.yandex.', self.transport.effective_url):
            captcha_found = True
        else:
            captcha_found = False

        return captcha_found

    def __get_captcha_form(self):
        form = at_css(self.html, "div.b-captcha form")
        if form is None:
            form = at_xpath(self.html, '//form[contains(@action, "checkcaptcha")]')   
        return form

    def __get_captcha_img(self, form):
        img = None
        if form is not None:
            img = at_css(form, "img.b-captcha__image")
            if img is None:
                img = at_css(form, "img.b-captcha__image_exp")
        return img

    def __fill_captcha_form(self, form, captcha_value):
        form.fields['rep'] = captcha_value
        return form

    def solve_captcha(self):

        form = self.__get_captcha_form()
        img = self.__get_captcha_img(form)
    

        effective_url_init = self.transport.effective_url
        if form is None or img is None:
            raise YandexException('Not found form or img on captcha page.')

        try:
            captcha_url = img.attrib['src']
        except:
            raise YandexException('Not found src attribute of captcha image element.')

        debug('captcha_url: %s' % captcha_url)
        captcha_value = solveImgUrl(captcha_url, self.anticaptcha_key,\
        	self.transport, self.anticaptcha_host)
        
        debug('captcha_value: %s' % captcha_value)

        form = self.__fill_captcha_form(form, captcha_value)

        self.transport.effective_url = effective_url_init
        self.transport.postForm(form)

        return not self.is_captcha()