# -*- coding: utf-8 -*-
from pylibs.cpa import CpaException
import requests
import json
import logging


class ActionPayException(CpaException):
    pass


class ActionPayApiException(ActionPayException):
    pass


class ActionPayApiBadHttpException(ActionPayApiException):
    pass


class ActionPayApi(object):
    api_url = 'https://api.actionpay.net/ru-ru/{api_method}/'

    def __init__(self, api_key):
        self.api_key = api_key

    def __request(self, api_method, params=None):

        request_url = self.api_url.format(api_method=api_method)

        if params is None:
            params = {}

        params['key'] = self.api_key
        params['format'] = 'json'

        r = requests.get(
            request_url,
            params=params,
            timeout=30
        )

        try:
            response = json.loads(r.text)
        except ValueError:
            response = None

        if response is not None and "error" in response:
            raise ActionPayApiException(u"{0}: {1}".format(response['error']['code'], response['error']['text']))

        if r.status_code != 200:
            raise ActionPayApiBadHttpException(r.status_code)

        if response is None:
            raise ActionPayApiException("bad response: {0}".format(r.text))

        return response

    def get_offers(self):
        return self.__request('apiWmMyOffers')['result']['favouriteOffers']
