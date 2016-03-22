# -*- coding: utf-8 -*-
from pylibs.senders import SendersException
import urllib
import requests
import json
import logging


class UniSenderException(SendersException):
    pass


class UniSenderApiException(UniSenderException):
    pass


class UniSenderApiBadHttpException(UniSenderApiException):
    pass


class UniSenderAPI(object):
    api_url = 'https://api.unisender.com/ru/api/'

    def __init__(self, api_key):
        self.api_key = api_key

    def __request(self, method=None, data=None, request_url=None):
        if request_url is None:
            request_url = '{0}{1}?format=json&api_key={2}&{3}'.format(
                self.api_url,
                method,
                self.api_key,
                urllib.urlencode(data)
            )

        logging.info("Request to {0}".format(request_url))
        r = requests.get(request_url)
        logging.info(u"response: {0}".format(r.text))

        if r.status_code != 200:
            raise UniSenderApiBadHttpException(r.status_code)

        try:
            response = json.loads(r.text)
        except ValueError:
            raise UniSenderApiException("bad response: {0}".format(r.text))

        if 'error' in response:
            raise UniSenderApiException(response['error'])

        return response

    def ping(self):
        raise NotImplementedError

    def send_sms(self, phones, sender, text):

        data = {
            'phone': ",".join(phones),
            'sender': sender,
            'text': text,
        }

        response = self.__request('sendSms', data)

        return response

    def send_mail(self, subject, body, emails_to, sender_email, sender_name, list_id):

        data = {
            'subject': subject.encode('utf-8'),
            'body': body.encode('utf-8'),
            'sender_email': sender_email,
            'sender_name': sender_name,
            'list_id': list_id
        }

        for n, email in enumerate(emails_to):
            data['email[{0}]'.format(n)] = email

        response = self.__request('sendEmail', data)

        return response
