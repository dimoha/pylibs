# -*- coding: utf-8 -*-
from pylibs.cpa import CpaException
import requests
import json
import logging


class GdeSlonException(CpaException):
    pass


class GdeSlonApiException(GdeSlonException):
    pass


class GdeSlonApiBadHttpException(GdeSlonApiException):
    pass


class GdeSlonApi(object):
    api_url = 'https://www.gdeslon.ru/api/'

    def __init__(self, id, api_key):
        self.id = id
        self.api_key = api_key

    def __request(self, api_method=None, params=None):

        request_url = "{0}{1}/".format(self.api_url, api_method)
        logging.debug(request_url)

        if params is None:
            params = {}

        r = requests.post(
            request_url,
            auth=(self.id, self.api_key),
            data=json.dumps(params),
            headers={
                'Content-Type': "application/json"
            }
        )

        try:
            response = json.loads(r.text)
        except ValueError:
            response = None

        if r.status_code != 200:
            raise GdeSlonApiBadHttpException(r.status_code)

        if response is None:
            raise GdeSlonApiException("bad response: {0}".format(r.text))

        if "error" in response and response['result'] == 'error':
            print response
            raise GdeSlonApiException(response['error'])

        return response

    def get_orders(self, from_dt, period):

        params = {
            "created_at": {
                "date": from_dt,
                "period": period
            }
        }

        return self.__request('orders', params)
