# -*- coding: utf-8 -*-
from seo.yandex import YandexException, Yandex
from pylibs.network.parser import *
from pylibs.network.urls import *


class YandexDirectException(YandexException):
    pass

class YandexDirect(Yandex):
    
    def is_captcha(self, *args, **kwargs):
        captcha_found = super(YandexDirect, self).is_captcha(*args, **kwargs)
        
        if at_xpath(self.html, '//input[@name="captcha_id"]') is not None:
            captcha_found = True

        return captcha_found


    def __get_captcha_form(self):
        return at_xpath(self.html, '//form[contains(@action,"direct.yandex.ru")]')

    def __get_captcha_img(self, form):
        return at_xpath(self.html, '//img[contains(@src,"captcha.yandex")]')

    def __fill_captcha_form(self, form, captcha_value):
        form.fields['captcha_code'] = captcha_value
        return form