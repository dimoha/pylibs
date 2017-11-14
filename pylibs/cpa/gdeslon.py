# -*- coding: utf-8 -*-
from pylibs.cpa import CpaException
import requests
import json
import logging
import xml.etree.ElementTree as ET


class GdeSlonException(CpaException):
    pass


class GdeSlonApiException(GdeSlonException):
    pass


class GdeSlonApiBadHttpException(GdeSlonApiException):
    pass


class OrderNotExist(GdeSlonApiException):
    pass


class OrderAlreadyPayed(GdeSlonApiException):
    pass


class GdeSlonApi(object):
    api_url = 'https://www.gdeslon.ru/api/'

    def __init__(self, id, api_key):
        self.id = id
        self.api_key = api_key

    def __request(self, api_method=None, params=None):

        request_url = "{0}{1}".format(self.api_url, api_method)
        logging.debug(request_url)

        if params is None:
            params = {}

        r = requests.post(
            request_url,
            auth=(self.id, self.api_key),
            data=json.dumps(params),
            headers={
                'Content-Type': "application/json"
            },
            timeout=30
        )

        logging.info(params)
        logging.info(r.text)

        try:
            response = json.loads(r.text)
        except ValueError:
            response = None

        if response is not None
            if "error" in response and response['result'] == 'error':
                raise GdeSlonApiException(response['error'])

            if "message" in response and response['result'] == 'error':
                raise GdeSlonApiException(response['message'])

        logging.info(response)

        if r.status_code != 200:
            raise GdeSlonApiBadHttpException(r.status_code)

        if response is None:
            raise GdeSlonApiException("bad response: {0}".format(r.text))

        return response

    def get_orders(self, from_dt, period):

        params = {
            "created_at": {
                "date": from_dt,
                "period": period
            }
        }

        return self.__request('orders/', params)

    def postback(self, params):

        json_post = {
            "root": {
                "orders": {
                    "order": [
                        {
                            "order_id": params['id'],
                            "token": params['lead_id'],
                            "status": params['status'],
                        }
                    ]
                }
            }
        }

        logging.info(json_post)
        r = self.__request('operate/postbacks.json', params=json_post)
        logging.info(r)

        return r['result'] == 'success'
