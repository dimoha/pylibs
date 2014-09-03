# -*- coding: utf-8 -*-
from seo import SeoException
from pylibs.network.browser import Browser
from pylibs.network.parser import *
from pylibs.network.urls import *
import re, json, urllib

class SolomonoException(SeoException):
    pass


class SolomonoQuery():
    
    def __init__(self, qtext):
        self.q = qtext
        
        if isinstance(qtext, unicode):
            self.q = qtext.encode('utf-8')
        else:
            self.q = qtext
        
        self.results = []

    def executeQuery(self, count=10):
        
        self.results = {}
        url = 'http://xml.solomono.ru/?url=%s' % (urllib.quote(self.q),)
        br = Browser()
        br.get(url)
        xmlObj = br.html()
        
        xresults = xmlObj.xpath('//data/*')
        for res in xresults:
            self.results[str(res.tag)] = str(res.text)
        
        if 'index' not in self.results or 'dout' not in self.results or 'hin' not in self.results:
            raise SolomonoException('Bad XML from Solomono: .')
    

class SolomonoSite():

    def __init__(self, url):
        self.domain = get_domain(url)
        query = SolomonoQuery(self.domain)
        query.executeQuery()    
        self.data = query.results

    @property
    def sindex(self):
        return int(self.data['index'])

    @property
    def backlinks(self):
        return int(self.data['hin'])

    @property
    def backlinks_grouped(self):
        return int(self.data['din'])

    # внешние ссылки сайта, сгруппированные по доменам
    @property
    def linkfromdomain(self):
        return int(self.data['dout'])

    # все внешние ссылки сайта
    @property
    def hrefsfromdomain(self):
        return int(self.data['hout'])

    @property
    def linkfromdomain_to_sindex(self):
        lts = 0
        if float(self.data['index'])>0:
            lts = float(self.data['dout'])/float(self.data['index'])
        return lts
    
    @property
    def link_farm_ratio(self):
        lts = 0
        if float(self.data['dout'])>0:
            lts = float(self.data['din'])/float(self.data['dout'])
        return lts

def getDomainData(domain):
    domain = get_domain(domain)
    query = SolomonoQuery(domain)
    query.executeQuery()    
    return query.results

def sindex(domain):
    results = getDomainData(domain)
    return int(results['index'])

def backlinks(domain):
    results = getDomainData(domain)
    return int(results['hin'])

def backlinks_group(domain):
    results = getDomainData(domain)
    return int(results['din'])

def linkfromdomain(domain):
    results = getDomainData(domain)
    return int(results['dout'])

def linkfromdomain_to_sindex(domain):
    lts = 0
    results = getDomainData(domain)
    if float(results['index'])>0:
        lts = float(results['dout'])/float(results['index'])
    return lts

def din_to_dout(domain):
    lts = 0
    results = getDomainData(domain)
    if float(results['dout'])>0:
        lts = float(results['din'])/float(results['dout'])
    return lts