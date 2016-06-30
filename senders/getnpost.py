# -*- coding: utf-8 -*-
from pylibs.senders import SendersException
from lxml import etree
import requests
import logging


class GetNPostException(SendersException):
    pass


class GetNPostApiException(GetNPostException):
    pass


class GetNPostApiBadHttpException(GetNPostApiException):
    pass


class GetNPost(object):
    api_url = 'http://api.get-n-post.ru/api/'

    def __init__(self, api_key, id):
        self.api_key = api_key
        self.id = id
        self.xml_parser = etree.XMLParser()

    def __request(self, method=None, data=None):

        request_url = "{0}{1}".format(self.api_url, method)
        params = {
            'key': self.api_key
        }
        params.update(data or {})
        logging.info(u"Request to {0} {1}".format(request_url, params))
        r = requests.get(request_url, params=params)
        logging.info(u"response: {0}".format(r.text))

        if r.status_code != 200:
            raise GetNPostApiBadHttpException(r.status_code)

        try:
            self.xml_parser.feed(r.text)
            response = self.xml_parser.close()
        except ValueError:
            raise GetNPostApiException("bad response: {0}".format(r.text))

        return response

    def check_email(self, email):
        response = self.__request('email_check', {
            'email': email
        })
        status = response.find('status').text
        if status not in ['ok', 'fail']:
            raise GetNPostApiException("Bad check_email status: {0}".format(status))
        return status == 'ok'
