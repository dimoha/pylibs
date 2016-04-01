# -*- coding: utf-8 -*-
from pylibs.senders import SendersException
import requests
import json
import logging
import re


class MailGunException(SendersException):
    pass


class MailGunApiException(MailGunException):
    pass


class MailGunApiBadHttpException(MailGunApiException):
    pass


class MailGunApiSendEmailException(MailGunApiException):
    pass


class MailGunApi(object):
    api_url = 'https://api.mailgun.net/v3/'

    def __init__(self, api_key, domain):
        self.api_key = api_key
        self.domain = domain

    def __request(self, method, post_params):

        r = requests.post("{0}{1}/{2}".format(self.api_url, self.domain, method), auth=("api", self.api_key), data=post_params)
        if r.status_code != 200:
            raise MailGunApiBadHttpException(r.status_code)

        try:
            response = json.loads(r.text)
        except ValueError:
            raise MailGunApiException("bad response: {0}".format(r.text))

        return response

    def send_mail(self, subject, body, recipients, sender):

        mg_recipients = []
        for recipient in recipients:
            if 'name' in recipient:
                mg_recipients.append(u"{0} <{1}>".format(recipient['name'], recipient['email']))
            else:
                mg_recipients.append(u"{0}".format(recipient['email']))

        if 'name' in sender:
            mg_sender = u"{0} <{1}>".format(sender['name'], sender['email'])
        else:
            mg_sender = sender['email']

        data = {
            "from": mg_sender,
            "to": mg_recipients,
            "subject": subject,
            "text": re.sub('<[^<]+?>', '', body),
            "html": body
        }

        response = self.__request('messages', data)

        if 'id' not in response:
            raise MailGunApiSendEmailException(response['message'])

        return response['id']
