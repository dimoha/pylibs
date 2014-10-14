# -*- coding: utf-8 -*-
from pylibs.seo.yandex import YandexException, Yandex
from pylibs.network.parser import *
from pylibs.network.urls import *
from pylibs.network.browser import BrowserException
from pylibs.utils.text import toUnicode
from logging import info, debug, warning
import re, json, urllib, math

class YandexMarketException(YandexException):
    pass

class YandexMarketWebException(YandexMarketException):
    pass

class YandexMarket404Exception(YandexMarketWebException):
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

        
        for j in range(try_cnt):
            try:
                _tmp = self.get(uri, params)
                break
            except BrowserException as e:
                if j == (try_cnt-1):
                    raise
                else:
                    warning("Get %s error %s: %s" % (posesname, j, e))
                    continue


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
        super(YandexMarketWeb, self).__init__(*args, **kwargs)


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

    def get_popular_list(self, hid, limit = 200):
        url = '%s/catalog.xml?hid=%s&track=pieces' % (self.host, hid)
        html = self.request(url)
        self.check_region()

        popular_link = at_xpath(self.html, u'//a[@class="top-3-models__title-link" and contains(text(), "Популярные")]').attrib['href']
        popular_link = '%s%s'  % (self.host, popular_link)
        info("popular_link: %s" % popular_link) 
        return self.get_products_list(popular_link, limit)


    def get_shop_offers(self, shop_id, limit = None):
        url = '%s/search.xml?fesh=%s' % (self.host, shop_id)
        try_cnt = 6
        products = []
        while True:
            
            for i in range(try_cnt):
                try:
                    html = self.request(url)
                    break
                except Exception as e:
                    if i == (try_cnt-1):
                        raise
                    else:
                        warning("get_shop_offers error %s: %s" % (i, e))
                        continue
            
            self.check_region()

            
            positions = css(html, 'div.b-serp__item')
            if len(positions) > 0:
                m = re.search(u'mvc\.map\("search-results",([^;]+)\);(?isu)', self.transport.unicode())
                search_json = json.loads(m.group(1).strip())
                glen = len(search_json[0])
                search_json = search_json[1]
                info("Found %s positions on page" % len(positions))
                for n,position in enumerate(positions):
                    product_link = at_css(position, 'a.b-offers__name')
                    product_name = toUnicode(element_text(product_link))
                    model_id = int(search_json[n*(1+glen) + glen])
                    price = element_text(at_xpath(position, './/span[@class="b-old-prices__num"]'))
                    price = float(re.sub("[^\d\.]+(?is)", "", price.replace(",", ".")))
                    debug("%s | %s | %s" % (product_name, model_id, price))
                    product = {'product_name':product_name, "model_id":model_id, "price":price}
                    products.append(product)
            else:
                break

            next_url = at_xpath(html, '//a[@class="b-pager__next"]')
            if next_url is None:
                break
            else:
                url = '%s%s' % (self.host, next_url.attrib['href'])
                debug("next url: %s" % url)

            if limit is not None and len(products) >= limit:
                products = products[0:limit]
                break

        debug("parsed: %s positions" % len(products))
        return products

    def get_products_list(self, url, limit=200):
        
        try_cnt = 6
        products = []
        while True:
            
            for i in range(try_cnt):
                try:
                    html = self.request(url)
                    break
                except Exception as e:
                    if i == (try_cnt-1):
                        raise
                    else:
                        warning("get_products_list error %s: %s" % (i, e))
                        continue
            
            self.check_region()

            positions = css(html, 'div.b-offers_type_guru')
            for position in positions:
                if 'id' in position.attrib:

                    product_link = at_xpath(position, './/a[contains(@id, "item-href-")]')

                    model_id = int(product_link.attrib['id'].replace("item-href-", ""))
                    debug("model_id: %s" % model_id)
                    product_name = toUnicode(element_text(product_link))
                    debug("product_name: %s" % product_name)
                    product_href = '%s%s' % (self.host, product_link.attrib['href'])
                    debug("product_href: %s" % product_href)

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
        return products

    def parse_model_offers_page(self, model_id, hid = None):
        params = {'modelid':model_id}
        if hid is not None:
            params['hid'] = hid
        params = urllib.urlencode(params)
        page_url = '%s/offers.xml?%s' % (self.host, params)
        debug(page_url)

        html = self.request(page_url)

        title = element_text(at_xpath(html, '//title'))
        info("title: %s" % title)
        if title == '404':
            raise YandexMarket404Exception("Model %s not found" % model_id)


        self.check_region()
        
        model_name = element_text(at_css(html, 'h1.b-page-title__title'))

        breadcrumbs = []
        breadcrumbs_a = xpath(html, '//a[@class="b-breadcrumbs__link"]')
        for a in breadcrumbs_a:
            breadcrumbs.append({'url':a.attrib['href'].decode('utf-8'), 'title':element_text(a).decode('utf-8')})
        
        if len(breadcrumbs) == 0:
            raise YandexMarketWebException("Not found breadcrumbs in %s" % page_url)

        info("breadcrumbs: %s" % repr(breadcrumbs).decode("unicode-escape"))

        offers = []
        offers_info_list = css(html, 'div.b-offers__offers')
        for offer in offers_info_list:
            
            rating = at_css(offer, 'span.b-aura-rating')
            rating = int(rating.attrib['data-rate']) if rating is not None else 0

            rating_link = at_css(offer, 'a.b-rating__link')
            if rating_link is None:
                rating_link = at_css(offer, 'a.b-offers__price__grade')
            shop_id = int(rating_link.attrib['href'].split("/")[2])

            price = element_text(at_xpath(offer, './/span[@class="b-old-prices__num"]'))
            price = float(re.sub("[^\d\.]+(?is)", "", price.replace(",", ".")))
            shop_name = toUnicode(element_text(at_css(offer, 'div.b-offers__feats a.shop-link')))
            product_name = toUnicode(element_text(at_css(offer, 'a.b-offers__name')))
            delivery_info = toUnicode(element_text(at_css(offer, 'div.b-offers__delivery span.b-offers__delivery-text')))
            delivery_cost = None
            m = re.search(u'Доставка\s+(\d+)\s+руб(?isu)', delivery_info)
            if m:
                delivery_cost = m.group(1).strip().replace(",", ".")
                try:
                    delivery_cost = float(re.sub("[^\d\.]+(?is)", "", delivery_cost))
                except Exception as e:
                    warning("Can't get delivery_cost from string: %s" % delivery_cost)
                    delivery_cost = None

            offer_dict = {'price':price, 'shop_id':shop_id, 'rating':rating, 'shop_name':shop_name, 'product_name':product_name, "delivery_cost":delivery_cost, "delivery_info":delivery_info}
            offers.append(offer_dict)

        info("Found %s offers" % len(offers))
        return {'breadcrumbs':breadcrumbs, "model_name":model_name, "offers":offers}



        
