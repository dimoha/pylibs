# -*- coding: utf-8 -*-
import urllib
import requests
import json
import logging
from pylibs.calltracking import CallTrackingException


class CallTouchAPIException(CallTrackingException):
    pass


class CallTouchAPI(object):

    API_URL = 'http://api.calltouch.ru/calls-service/RestAPI/'

    def __init__(self, project_id, api_key):
        self.project_id = project_id
        self.api_key = api_key

    def __request(self, method, params):
        request_url = "{0}{1}?clientApiId={2}&{3}".format(
            self.API_URL,
            method,
            self.api_key,
            urllib.urlencode(params)
        )
        logging.debug(request_url)
        response = requests.get(request_url)

        try:
            response = json.loads(response.text)
        except ValueError:
            if response.status_code != 200:
                raise CallTouchAPIException("Bad status code: {0}".format(response.status_code))
            elif response.text.strip() == '':
                raise CallTouchAPIException("empty response")
            else:
                raise CallTouchAPIException("bad response body: {0}".format(response.text))

        return response

    def get_calls(self, date_from, date_to, only_unique=False):

        calls = self.__request(
            "{0}/calls-diary/calls".format(self.project_id),
            {
                "dateFrom": date_from.strftime("%d/%m/%Y"),
                "dateTo": date_to.strftime("%d/%m/%Y"),
                'uniqueOnly': only_unique
            }
        )
        logging.info("Found {0} calls".format(len(calls)))
        return calls
