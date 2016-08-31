# -*- coding: utf-8 -*-
from pylibs.predict import PredictException
import requests
import logging
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
    url = 'http://smartrec.pro/'

    def __init__(self, token, secret_key):
        self.token = token
        self.secret_key = secret_key


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


