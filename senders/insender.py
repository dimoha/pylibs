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
            params = {}

        params['time'] = unix_now
        params['token'] = self.token
        signature = urllib.urlencode(params)
        signature = "{0}@{1}".format(self.secret_key, signature)
        params['signature'] = hashlib.md5(signature).hexdigest()
        print "{0}  -  {1}".format(request_url, params)
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

    def get_events(self, event_types, from_ut=None):
        raise NotImplementedError

    def send_mail(self, subject, body, recipient, sender=None, category=None):

        #if 'name' in sender:
        #    mg_sender = u"{0} <{1}>".format(sender['name'], sender['email'])
        #else:
        #mg_sender = sender['email'].split("@")[0]

        #if 'name' in recipient:
        #    mg_recipient = u"{0} <{1}>".format(recipient['name'], recipient['email'])
        #else:
        mg_recipient = recipient['email']

        data = {
            "email": mg_recipient,
            "subject": subject,
            "body_html": body,
            "category": category
        }

        if sender is not None:
            data['reply_to_email'] = sender['email']

        response = self.__request('task.add', data)

        try:
            message_id = response['data']['id']
        except KeyError:
            raise InSenderApiSendEmailException("No mail_id in response: {0}".format(response))

        return message_id
