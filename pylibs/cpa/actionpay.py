# -*- coding: utf-8 -*-
from pylibs.cpa import CpaException
from pylibs.utils.tools import achunk
import requests
import json
import logging
from datetime import timedelta, datetime


class ActionPayException(CpaException):
    pass


class ActionPayApiException(ActionPayException):
    pass


class ActionPayApiBadHttpException(ActionPayApiException):
    pass


class OfferLockedException(ActionPayApiException):
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
            timeout=120,
            verify=False
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

    def get_wm_links(self, source_id, offer_id):
        try:
            return self.__request('apiWmLinks', {'source': source_id, 'offer': offer_id})['result']['links']
        except ActionPayApiException as e:
            err_msg = str(e)
            if u'ссылки по этому офферу заблокированы' in err_msg:
                raise OfferLockedException(err_msg)
            else:
                raise

    def get_offers(self):
        offers = []
        page = 0
        while True:
            page += 1
            logging.info("Load page {0}...".format(page))
            this_offers = self.__request('apiWmOffers', {'page': page})['result']['offers']
            offers += this_offers
            if len(this_offers) == 0:
                break
        return offers

    def get_my_offers(self):
        return self.__request('apiWmMyOffers')['result']['favouriteOffers']

    def get_days_in_period(self, date_from, date_to):
        return [date_from + timedelta(days=i) for i in range((date_to - date_from).days + 1)]

    def get_orders(self, from_date, to_date):

        days = self.get_days_in_period(from_date, to_date)
        pp = 200

        actions = []
        for days_group in achunk(days, 7):
            page = 0
            while True:
                page += 1
                df = str(days_group[0])
                dt = str(days_group[-1])
                logging.info("Load page {0} ({1} - {2}) ...".format(page, df, dt))

                this_actions = self.__request('apiWmStats', {
                    'page': page,
                    'itemsPerPage': pp,
                    'from': df,
                    'till': dt
                })['result']['actions']

                actions += this_actions
                if len(this_actions) < pp:
                    break

        return actions

    def create_conversion(self, target_id, click_id, order_id, price):

        r = requests.get(
            'https://x.actionpay.ru/ok/{0}.png'.format(target_id),
            params={
                'actionpay': click_id,
                'apid': order_id,
                'price': price

            },
            timeout=30
        )

        if r.status_code != 200:
            raise ActionPayApiBadHttpException(r.status_code)

    def postback(self, target_id, click_id, order_id, price, status):

        r = requests.get(
            'https://n.actionpay.ru/status/',
            params={
                'key': self.api_key,
                'aim': target_id,
                'status': status,
                'actionpay': click_id,
                'apid': order_id,
                'price': price
            },
            timeout=30
        )

        if r.status_code != 200:
            raise ActionPayApiBadHttpException(r.status_code)

        if r.text != 'ok':
            raise ActionPayApiException("Bad response in postback: {0}".format(r.text))
