# -*- coding: utf-8 -*-
from seo.yandex import YandexException, Yandex
from pylibs.network.parser import *
from pylibs.network.urls import *
from pylibs.network.browser import BrowserException
from logging import info, debug, warning
import re, json, urllib, math

class YandexMarketException(YandexException):
    pass

class YandexMarketWebException(YandexMarketException):
    pass

class YandexMarketApiException(YandexMarketException):
    pass


class YandexMarketApi(Yandex):

    partner_api_url = "https://api.partner.market.yandex.ru/v2/"

    def __init__(self, oauth_token, oauth_client_id, oauth_login):
        super(YandexMarketApi, self).__init__()
        self.transport.pages_headers = [
            'Authorization: OAuth oauth_token=%s, oauth_client_id=%s, oauth_login=%s' 
                % (oauth_token, oauth_client_id, oauth_login)
        ]
        self.transport.timeout = 600



    def __get_elements(self, uri, pp, posesname, limit = None, params = None):
        positions = []
        try_cnt = 5
        default_params = {'pageSize':1, 'page':1}
        if params is None:
            params = {}
        params.update(default_params)

        _tmp = self.get(uri, params)
        count_pages = int(math.ceil(float(_tmp['pager']['total']) / float(pp)))
        info("count pages: %s" % count_pages)
        params['pageSize'] = pp
        for i in range(count_pages):
            page_num = i + 1
            info("Get page %s" % page_num)

            params['page'] = page_num
            for j in range(try_cnt):
                try:
                    res = self.get(uri, params)[posesname]
                    break
                except BrowserException as e:
                    if j == (try_cnt-1):
                        raise
                    else:
                        warning("Get %s error %s: %s" % (posesname, j, e))
                        continue

            for r in res:
                positions.append(r)
            
            if limit is not None and len(positions)>= limit:
                positions = positions[0:limit]
                break

        info("Loaded %s positions" % len(positions))       
        return positions

    def get_categories(self, company_id, limit = None):
        uri = 'campaigns/%s/feeds/categories' % company_id
        return self.__get_elements(uri, 500, 'categories', limit)

    def get_company_offers(self, company_id, limit = None):

        all_offers = {}
        cats = self.get_categories(company_id)
        uri = 'campaigns/%s/offers' % company_id
        for cat in cats:
            info("Get offers of category: %s" % cat['name'])
            for offer in self.__get_elements(uri, 200, 'offers', limit, params = {'shopCategoryId':cat['id']}):
                all_offers[offer['id']] = offer

            if limit is not None and len(all_offers) >= limit:
                all_offers = all_offers.values()[0:limit]
                break

            info("===> all_offers: %s" % len(all_offers))        

        info("all_offers: %s" % len(all_offers))
        return all_offers.values()  


    def request(self, url):
        self.transport.get(url)
        return json.loads(self.transport.unicode())

    def get(self, resource, params = None):
        request_url = "%s%s.json" % (self.partner_api_url, resource)
        if params is not None:
            request_url += '?%s' % urllib.urlencode(params)

        info(request_url)
        res = self.request(request_url)
        return res

    def post(self):
        raise NotImplementedError

    def put(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError


class YandexMarketWeb(Yandex):
    
    host = 'http://market.yandex.ru'


    def __init__(self, *args, **kwargs):
        self.region = kwargs['region']
        del kwargs['region']
        super(YandexMarket, self).__init__(*args, **kwargs)


    def get_region(self):
        #<div class="personal-menu i-bem" onclick="return {'personal-menu':{'regionName':'Москва'}}">
        region_js = at_xpath(self.html, '//div[contains(@class, "personal-menu i-bem")]').attrib['onclick']
        region_js = json.loads(region_js.replace("return ", "").replace("'", '"'))
        region = region_js['personal-menu']['regionName']
        return region

    def check_region(self):
        if hasattr(self, 'region'):
            current_region = self.get_region()
            debug("current_region: %s" % current_region)
            if self.region.lower() != current_region.lower():
                raise YandexMarketWebException("Incorrect region: %s (need %s)" % (current_region, self.region))

    def get_products_list(self, url, limit=200):
        
        products = []
        while True:
            
            html = self.request(url)
            self.check_region()

            positions = css(html, 'div.b-offers_type_guru')
            for position in positions:
                if 'id' in position.attrib:
                    model_id = int(position.attrib['id'])
                    product_link = at_xpath(position, '//a[@id="item-href-%s"]' % model_id)
                    product_name = element_text(product_link)
                    product_href = '%s%s' % (self.host, product_link.attrib['href'])
                    debug("%s | %s | %s" % (model_id, product_name, product_href)) 

                    product = {'model_id':model_id, 'product_name':product_name, 'product_href':product_href}
                    products.append(product)

            next_url = at_xpath(html, '//a[@class="b-pager__next"]')
            if next_url is None:
                break
            else:
                url = '%s%s' % (self.host, next_url.attrib['href'])
                debug("next url: %s" % url)

            if limit is not None and len(products) >= limit:
                products = products[0:limit]
                break

        cat_name = element_text(at_xpath(html, '//span[@itemprop="title"]'))
        debug("category: %s" % cat_name)
        debug("parsed: %s positions" % len(products))

        

        
        
