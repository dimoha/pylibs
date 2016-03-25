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

    def __request(self, method=None, data=None, request_url=None):
        post = None
        if request_url is None:
            post = data
            post['account_id'] = self.account_id
            post['api_key'] = self.api_key
            request_url = '{0}{1}'.format(self.api_url, method)

        if post is None:
            logging.info("Request to {0}".format(request_url))
            r = requests.get(request_url)
            logging.info("response: {0}".format(r.text))
        else:
            logging.info("Request POST to {0}: {1}".format(request_url, post))
            r = requests.post(request_url, data=post)
            logging.info("response: {0}".format(r.text))

        if r.status_code != 200:
            raise VoxImplantApiBadHttpException(r.status_code)

        try:
            response = json.loads(r.text)
        except ValueError:
            raise VoxImplantApiException("bad response: {0}".format(r.text))

        if 'error' in response:
            raise VoxImplantApiException(response['error']['msg'])

        return response

    def make_call(self, rule_id, custom_data=None):

        data = {
            'rule_id': rule_id,
            'script_custom_data': custom_data,
        }
        response = self.__request('StartScenarios', data)

        if response['result'] != 1:
            raise VoxImplantApiException(response)

        response['custom_data'] = custom_data

        return response

    def request_media_session_access_url(self, url):
        return self.__request(request_url=url)

    def get_history(self, date_from, date_to, custom_data):
        frmt = "%Y-%m-%d %H:%M:%S"
        data = {
            'from_date': date_from.strftime(frmt),
            'to_date': date_to.strftime(frmt),
            'with_calls': 1,
            'call_session_history_custom_data': custom_data
        }
        response = self.__request('GetCallHistory', data)
        return response
