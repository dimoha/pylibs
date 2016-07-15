# -*- coding: utf-8 -*-
from pylibs.senders import SendersException
import requests
import json
import logging
import re
import time
import hashlib
import urllib
from decimal import Decimal
from django.utils.datastructures import SortedDict


class InSenderException(SendersException):
    pass


class InSenderApiException(InSenderException):
    pass


class InSenderApiBadHttpException(InSenderApiException):
    pass


class InSenderApiSendEmailException(InSenderApiException):
    pass


class InSenderApi(object):
    api_url = 'http://api.insender.ru/1.0/json/'

    def __init__(self, token, secret_key):
        self.token = token
        self.secret_key = secret_key

    def __request(self, api_method=None, params=None):

        request_url = "{0}{1}".format(self.api_url, api_method)
        logging.debug(request_url)

        unix_now = int(time.time())

        if params is None:
            params = SortedDict()

        params['time'] = unix_now
        params['token'] = self.token
        signature = urllib.urlencode(params)
        signature = u"{0}@{1}".format(self.secret_key, signature)
        params['signature'] = hashlib.md5(signature).hexdigest()
        r = requests.post(request_url, data=params)

        try:
            response = json.loads(r.text)
        except ValueError:
            response = None

        if r.status_code != 200:
            raise InSenderApiBadHttpException(r.status_code)

        if response is None:
            raise InSenderApiException("bad response: {0}".format(r.text))

        if "error" in response and response['result'] == 'error':
            print response
            raise InSenderApiException(response['error'])

        return response

    def get_events(self, from_ut=None, category=None):

        year_ago = Decimal(str(time.time() - 86400*365))

        if from_ut is not None:
            from_ut = Decimal(str(from_ut))

        if from_ut is None or from_ut < year_ago:
            from_ut = year_ago

        params = SortedDict()
        params['from'] = int(from_ut)
        params['to'] = int(time.time())

        if category is not None:
            params['category'] = category

        return self.__request('stat.fetchByPeriod', params)['data']

    def send_mail(self, subject, body, recipient, sender=None, category=None):

        #if 'name' in sender:
        #    mg_sender = u"{0} <{1}>".format(sender['name'], sender['email'])
        #else:
        #mg_sender = sender['email'].split("@")[0]

        data = SortedDict()
        data['email'] = recipient['email']
        data['subscriber_title'] = recipient['name']
        data['subject'] = subject
        data['body_html'] = body
        data['category'] = category
        if sender is not None:
            data['reply_to_email'] = sender['email']

        response = self.__request('task.add', data)

        try:
            message_id = response['data']['id']
        except KeyError:
            raise InSenderApiSendEmailException("No mail_id in response: {0}".format(response))

        return message_id
