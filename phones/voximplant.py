# -*- coding: utf-8 -*-
from pylibs.phones import PhonesException
import urllib
import requests
import json
import logging


class VoxImplantException(PhonesException):
    pass


class VoxImplantApiException(VoxImplantException):
    pass


class VoxImplantApiBadHttpException(VoxImplantApiException):
    pass


class VoxImplantAPI(object):
    api_url = 'https://api.voximplant.com/platform_api/'

    def __init__(self, account_id, api_key):
        self.account_id = account_id
        self.api_key = api_key

    def __request(self, method, data):
        request_url = '{0}{1}/?account_id={2}&api_key={3}&{4}'.format(
            self.api_url,
            method,
            self.account_id,
            self.api_key,
            urllib.urlencode(data)
        )
        logging.info("Request to {0}".format(request_url))
        #r = requests.get(request_url)
        r = None
        logging.info("response: {0}".format(r.text))

        if r.status_code != 200:
            raise VoxImplantApiBadHttpException(r.status_code)

        try:
            response = json.loads(r.text)
        except ValueError:
            raise VoxImplantApiException("bad response: {0}".format(r.text))

        if response['result'] != 1:
            raise VoxImplantApiException(response)

        return response

    def make_call(self, phone_from, phone_to, rule_id):
        data = {
            'rule_id': rule_id,
            'script_custom_data': ":".join(phone_from, phone_to),
        }
        response = self.__request('StartScenarios', data)
        return response
