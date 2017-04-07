# -*- coding: utf-8 -*-
from pylibs.senders import SendersException
import requests
import json
import logging
import re
import time
from decimal import Decimal


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

    def __request(self, api_method=None, params=None, method='POST', url=None):

        if url is None:
            request_url = "{0}{1}/{2}".format(self.api_url, self.domain, api_method)
        else:
            request_url = url
            method = 'GET'
            params = None

        logging.debug(request_url)

        if method == 'POST':
            r = requests.post(request_url, auth=("api", self.api_key), data=params)
        else:
            r = requests.get(request_url,  auth=("api", self.api_key), params=params)

        try:
            response = json.loads(r.text)
        except ValueError:
            response = None

        if r.status_code != 200:
            err_msg = response['message'] if response and 'message' in response else r.status_code
            raise MailGunApiBadHttpException(err_msg)

        if response is None:
            raise MailGunApiException("bad response: {0}".format(r.text))

        return response

    def get_events(self, event_types, from_ut=None):

        year_ago = Decimal(str(time.time() - 86400*365))
        if from_ut is not None:
            from_ut = Decimal(str(from_ut))

        if from_ut is None or from_ut < year_ago:
            from_ut = year_ago

        params = {
            "event": " OR ".join(event_types),
            "begin": from_ut,
            "end": time.time(),
            "limit": 300
        }

        res = self.__request('events', params, method='GET')
        events = res['items']

        while 'paging' in res and 'next' in res['paging']:
            res = self.__request(url=res['paging']['next'])
            events += res['items']
            if len(res['items']) == 0:
                break

        return events

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
