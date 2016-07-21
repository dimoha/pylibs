# -*- coding: utf-8 -*-
from pylibs.phones import PhonesException
import urllib
import requests
import json
import logging


class InfoTelException(PhonesException):
    pass


class InfoTelApiException(InfoTelException):
    pass


class InfoTelApiBadHttpException(InfoTelApiException):
    pass


class InfoTelApi(object):
    api_url = 'http://tell-info.com/Kokos_tone_extension_dial_API/'

    def __init__(self, api_key):
        self.api_key = api_key

    def __request(self, data):

        if data is None:
            data = {}
        data['key'] = self.api_key
        logging.info("Request POST to {0}: {1}".format(self.api_url, data))
        r = requests.post(self.api_url, data={'data': json.dumps(data)})
        logging.info("response: {0}".format(r.text))

        if r.status_code != 200:
            raise InfoTelApiBadHttpException(r.status_code)

        try:
            response = json.loads(r.text)
        except ValueError:
            raise InfoTelApiException("bad response: {0}".format(r.text))

        if response['status'] != u'ok':
            if 'message' in response and response['message']:
                raise InfoTelApiException(response['message'])
            else:
                raise InfoTelApiException(r.text)

        return response

    def send_lead(self, data):
        self.__request(data)
        return True
