# -*- coding: utf-8 -*-
from pylibs.predict import PredictException
import requests
import logging
import urllib
import json
import time


class SmartRecException(PredictException):
    pass


class SmartRecApiException(SmartRecException):
    pass


class SmartRecApiBadHttpException(SmartRecApiException):
    pass


class SmartRecWebException(SmartRecException):
    pass


class SmartRecWebNoAuthException(SmartRecWebException):
    pass


class SmartRecWebBadHttpException(SmartRecWebException):
    pass


class SmartRecWebTenantAlreadyExistException(SmartRecWebException):
    pass


class SmartRecApi(object):
    url = 'http://smartrec.pro/api/1.1/json/'

    def __init__(self, api_key):
        self.api_key = api_key

    def __request(self, method, params):
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        request_url = '{0}{1}?{2}'.format(self.url, method, urllib.urlencode(params))
        r = requests.get(request_url)
        try:
            response = json.loads(r.text)
        except ValueError:
            response = None

        if r.status_code != 200:
            raise SmartRecApiBadHttpException(r.status_code)

        if response is None:
            raise SmartRecApiException("bad response: {0}".format(r.text))

        return response

    def get_user_recommendations(self, user_id, tenant_id):
        params = {
            'userid': user_id,
            'tenantid': tenant_id,
            'requesteditemtype': 'ITEM'
        }
        result = self.__request('recommendationsforuser', params)
        logging.info(result)
        return result['recommendedItems']

    def get_most_viewed(self, tenant_id, time_range='WEEK'):
        params = {
            'timeRange': time_range,
            'tenantid': tenant_id,
            'requesteditemtype': 'ITEM'
        }
        result = self.__request('mostvieweditems', params)
        logging.info(result)
        return result['recommendedItems']


class SmartRecWeb(object):
    base_url = 'http://smartrec.pro/'

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.__session = requests.Session()

    def __auth(self):
        logging.debug("Start auth in smartrec...")
        auth_url = '{0}operator/signin?operatorId={1}&password={2}&_={3}'.format(
            self.base_url,
            self.login,
            self.password,
            int(time.time())
        )
        self.__session.get(auth_url)

    def __is_authorized(self, response):
        return 'signInOperatorId' not in response

    def __request(self, uri, without_auth=False):
        request_url = '{0}{1}'.format(self.base_url, uri)

        r = self.__session.get(request_url)

        if r.status_code != 200:
            raise SmartRecWebBadHttpException(r.http_code)

        if not self.__is_authorized(r.text) and not without_auth:
            self.__auth()
            return self.__request(uri, without_auth=True)

        if not self.__is_authorized(r.text):
            raise SmartRecWebNoAuthException

        if r.text.startswith("<?xml"):
            if "<error " in r.text:
                if 'code="204"' in r.text:
                    raise SmartRecWebTenantAlreadyExistException("This tenant already exists.")
                else:
                    raise SmartRecWebException(r.text.split('message="')[1].split('"')[0])

            if 'success code="200"' not in r.text:
                raise SmartRecWebException(r.text)

        return r.text

    def add_project(self, tenant_id, domain):
        add_uri = 'tenant/register?operatorId={0}&tenantId={1}&url=http://{2}&description=&_={3}'.format(
            self.login, tenant_id, domain, int(time.time())
        )

        try:
            self.__request(add_uri)
        except SmartRecWebTenantAlreadyExistException:
            pass

        return True
