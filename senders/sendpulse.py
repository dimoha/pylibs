# -*- coding: utf-8 -*-
from pylibs.senders import SendersException
import urllib
import requests
import json
import logging
import re
from M2Crypto import RSA, BIO
from M2Crypto.EVP import Cipher
import hashlib
import time
from base64 import b64decode, b64encode


class SendPulseException(SendersException):
    pass


class SendPulseApiException(SendPulseException):
    pass


class SendPulseApiBadHttpException(SendPulseApiException):
    pass


class SendPulseAPI(object):
    api_url = 'https://login.sendpulse.com/api/smtp/1.0/'

    def __init__(self, public_key):
        self.public_key = public_key.strip().replace("\r\n", "\n")
        self.a_key = self.__md5(self.public_key)

    def __md5(self, s):
        return hashlib.md5(s).hexdigest()

    def __sha1(self, s):
        return hashlib.sha1(s).hexdigest()

    def __openssl_encrypt(self, s):
        bio = BIO.MemoryBuffer(self.public_key)
        rsa = RSA.load_pub_key_bio(bio)
        encrypted = rsa.public_encrypt(s, RSA.pkcs1_padding)
        return encrypted

    def __openssl_decrypt(self, s):
        bio = BIO.MemoryBuffer(self.public_key)
        rsa = RSA.load_pub_key_bio(bio)
        decrypted = rsa.public_decrypt(s, RSA.pkcs1_padding)
        return decrypted

    def __request(self, post_params):

        a_pass = self.__sha1(str(time.time()))
        a_pass_enc = self.__openssl_encrypt(a_pass)
        a_iv = self.__md5(str(time.time()))[0:16]
        a_iv_enc = self.__openssl_encrypt(a_iv)
        cipher = Cipher('aes_128_cbc', a_pass, a_iv, op=1)

        v = cipher.update(json.dumps(post_params))
        v += cipher.final()

        data = {
            'key': self.a_key,
            'pass': a_pass_enc,
            'iv': a_iv_enc,
            'data': v,
        }

        r = requests.post(self.api_url, data=data)

        if r.status_code != 200:
            raise SendPulseApiBadHttpException(r.status_code)

        try:
            response = json.loads(r.text)
            if response['iv'] and response['pass']:
                passw = self.__openssl_decrypt(b64decode(response['pass']))
                iv = self.__openssl_decrypt(b64decode(response['iv']))

                cipher = Cipher('aes_128_cbc', passw, iv, op=0)
                v = cipher.update(b64decode(response['data']))
                v += cipher.final()
                response = json.loads(v)
            else:
                raise SendPulseApiException(b64decode(response['data_unencrypted']))

        except ValueError:
            raise SendPulseApiException("bad response: {0}".format(r.text))

        if 'error' in response and response['error'] != 0:
            error_data = ": {0}".format(response['data']) if 'data' in response else ''
            raise SendPulseApiException("ErrorCode {0}, {1}{2}".format(response['error'], response['text'], error_data))

        return response['data']

    def ping(self):
        return self.__request({
            "action": "ping"
        })

    def send_sms(self):
        raise NotImplementedError

    def send_mail(self, subject, body, recipients, sender):

        data = {
            "action": "send_email",
            "message": {
                "html": body,
                "text": re.sub('<[^<]+?>', '', body),
                "subject": subject,
                "encoding": "utf8",
                "from": sender,
                "to": recipients,
            }
        }

        response = self.__request(data)
        return response == u'Sent OK'
