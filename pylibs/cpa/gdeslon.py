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
            },
            timeout=30
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
            raise GdeSlonApiException(response['error'])

        return response

    def __request_xml(self, api_method, params=None):
        request_url = "{0}{1}".format(self.api_url, api_method)
        if params is None:
            params = {}

        params['_gs_at'] = self.api_key

        r = requests.get(
            request_url,
            data=params,
        )

        try:
            response = ET.fromstring(r.text)
        except ET.ParseError:
            response = None
            logging.error(r.text)

        if r.status_code != 200:
            raise GdeSlonApiBadHttpException(r.status_code)

        if response is None:
            raise GdeSlonApiException(u"bad response: {0}".format(r.text))

        if len(response) > 1 and response[1].text == u'failure':
            raise GdeSlonApiException(response[0].text)

        return response

    def get_orders(self, from_dt, period):

        params = {
            "created_at": {
                "date": from_dt,
                "period": period
            }
        }

        return self.__request('orders', params)

    def set_order_status(self, order_id, status):

        try:
            xml_res = self.__request_xml('states.xml', {
                'order_ids[]': order_id,
                'state': status
            })
            if xml_res[0].text != 'success':
                raise GdeSlonApiException(u"set_order_status bad response: {0}".format(xml_res[0].text))
        except GdeSlonApiException as e:
            if u'We found no orders' in str(e):
                raise OrderNotExist(order_id)
            elif u'Unable to change' in str(e):
                raise OrderAlreadyPayed(order_id)
            else:
                raise

    def postback(self, params):
        payload = {
            'codes': params['codes'],
            'order_id': params['id'],
            'merchant_id': params['merchant_id'],
            'token': params['lead_id']
        }
        logging.info(payload)
        r = requests.get('https://www.gdeslon.ru/purchase.js', params=payload)
        logging.info(r.status_code)
        return r.status_code == requests.codes.ok
