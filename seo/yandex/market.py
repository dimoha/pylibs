# -*- coding: utf-8 -*-
from pylibs.seo.yandex import YandexException, Yandex
from pylibs.network.parser import *
from pylibs.network.urls import *
from pylibs.network.browser import BrowserException
from pylibs.utils.text import toUnicode
from logging import info, debug, warning, error
import re, json, urllib, math
from datetime import datetime

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

    def __get_supcats(self, url, with_models):
        info(url)
        try_cnt = 10
        for i in range(try_cnt):
            try:
                html = self.request(url)
                break
            except Exception as e:
                if i == (try_cnt-1):
                    raise
                else:
                    warning("__get_supcats error %s: %s" % (i, e))
                    continue



        links = []
        if with_models:
            supcats = xpath(html, '//div[@class="supcat guru"]/a')
        else:
            supcats = xpath(html, '//td[@class="categories"]/div[contains(@class, "supcat")]/a')

        for supcat in supcats:
            if "http://" in supcat.attrib['href']:
                continue
            if supcat.attrib['href'].endswith('hid=90764'):
                continue
            cat_href = self.host + supcat.attrib['href']
            cat_name = element_text(supcat)
            info('%s => %s' % (cat_name, cat_href))
            links.append({'name':cat_name, 'href':cat_href})
        return links

    def get_categories(self, url = None, with_models = True):
        if not hasattr(self, 'categories'):
            self.categories = []

        if url is None:
            url = '%s/catalog.xml' % self.host

        cats = self.__get_supcats(url, with_models)
        for cat in cats:
            self.categories.append(cat)
            self.get_categories(cat['href'], with_models)

        return self.categories

    def get_popular_list(self, hid, limit = 200):
        url = '%s/catalog.xml?hid=%s&track=pieces' % (self.host, hid)
        html = self.request(url)
        self.check_region()


        popular_link = at_xpath(self.html, u'//a[@class="top-3-models__title-link" and contains(text(), "Популярные")]')
        if popular_link is not None:
            popular_link = popular_link.attrib['href']
            popular_link = '%s%s'  % (self.host, popular_link)
        else:
            popular_link = url
        info("popular_link: %s" % popular_link) 
        return self.get_products_list(popular_link, limit)


    def get_shop_offers(self, shop_id, limit = None, offers_without_region = False):
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
                if m is None:
                    raise YandexMarketWebException("Not found search-results JSON in %s" % url)

                search_json = json.loads(m.group(1).strip())

                glen = len(search_json[0])
                search_json = search_json[1]
                info("Found %s positions on page" % len(positions))
                for n,position in enumerate(positions):
                    product_link = at_css(position, 'a.b-offers__name')
                    product_name = toUnicode(element_text(product_link))
                    shop_link = product_link.attrib['href']
                    model_id = int(search_json[n*(1+glen) + glen])
                    price = element_text(at_xpath(position, './/span[@class="b-old-prices__num"]'))
                    price = float(re.sub("[^\d\.]+(?is)", "", price.replace(",", ".")))
                    debug("%s | %s | %s" % (product_name, model_id, price))
                    product = {'product_name':product_name, "model_id":model_id, "price":price, 'shop_link':shop_link}
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
            if len(positions) == 0:
                raise YandexMarket404Exception
            #positions = css(html, 'div.b-serp__item')

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
                info("next url: %s" % url)

            if limit is not None and len(products) >= limit:
                products = products[0:limit]
                break

        cat_name = element_text(at_xpath(html, '//span[@itemprop="title"]'))
        debug("category: %s" % cat_name)
        debug("parsed: %s positions" % len(products))
        return products

    def parse_shop_reviews_page(self, shop_id, sort = None, limit = None):
        page_url = '%s/shop/%s/reviews' % (self.host, shop_id)
        if sort is not None:
            page_url = page_url + '?sort_by=%s' % sort
        debug(page_url)


        res = {}
        res['reviews_1_stars_cnt'] = 0
        res['reviews_2_stars_cnt'] = 0
        res['reviews_3_stars_cnt'] = 0
        res['reviews_4_stars_cnt'] = 0
        res['reviews_5_stars_cnt'] = 0
        res['reviews_cnt'] = 0
        res['stars_cnt'] = 0
        res['reviews'] = self.__parse_reviews_from_page(page_url, limit)
        shop_name = at_xpath(self.html, '//span[@itemprop="name"]')
        if shop_name is None:
            raise YandexMarket404Exception

        res['shop_name'] = element_text(shop_name).strip()
        if res['shop_name'] == "":
            raise YandexMarket404Exception

        #<span xmlns:mx="https://market.yandex.ru/xmlns" class="b-aura-rating b-aura-rating_state_5 b-aura-rating_size_m"
        # title="на основе 2560 оценок покупателей и данных службы качества Маркета"
        # data-title="на основе 2560 оценок покупателей и данных службы качества Маркета" data-rate="5">

        rating_title = at_css(self.html, 'span.b-aura-rating_size_m')
        if rating_title is not None:
            reviews_cnt = re.sub('[^\d]+(?is)', '', rating_title.attrib['title']).strip()
            reviews_cnt = int(reviews_cnt) if reviews_cnt<>'' else 0
            res['reviews_cnt'] = reviews_cnt
            res['stars_cnt'] = int(rating_title.attrib['data-rate'])

        rating_items = css(self.html, 'div.b-aura-ratings__item')
        for rating_item in rating_items:
            sc = at_css(rating_item, 'span.b-aura-rating')
            sc = int(sc.attrib['data-rate'])
            ra = element_text(at_css(rating_item, 'a.b-aura-ratings__link'))
            ra = int(re.sub('[^\d]+(?is)', '', ra).strip())
            res['reviews_%s_stars_cnt' % sc] = ra

        return res


    def parse_model_page(self, model_id, hid = None):
        params = {'modelid':model_id, "track":'tabs'}
        if hid is not None:
            params['hid'] = hid
        params = urllib.urlencode(params)
        page_url = '%s/model.xml?%s' % (self.host, params)
        info(page_url)

        try_cnt = 6
        for i in range(try_cnt):
            try:
                html = self.request(page_url)
                break
            except Exception as e:
                if i == (try_cnt-1):
                    raise
                else:
                    warning("parse_model_page error %s: %s" % (i, e))
                    continue        
    
        prices_range = at_xpath(html, '//span[@class="b-prices b-prices__range"]')
        if prices_range is None:
            prices_range = at_xpath(html, '//span[@class="price__int"]')
            if prices_range is None:
                raise YandexMarket404Exception
            prices_range = element_text(prices_range)
            prices_range = [prices_range, prices_range]
        else:
            prices_range = element_text(prices_range).strip().split("…")
    
        prices_range = map(lambda x:re.sub("[^\d']+", "", x.strip()), prices_range)
        
        rating_value = at_xpath(html, '//meta[@itemprop="ratingValue"]')
        if rating_value is not None:
            try:
                rating_value = float(rating_value.attrib['content'])
            except:
                rating_value = None

        rating_cnt = at_xpath(html, '//span[@class="b-rating-text"]')
        if rating_cnt is not None:
            rating_cnt = int(re.sub("[^\d']+", "", element_text(rating_cnt)))

        cnts = {"offers":0, "geo":0, "opinions":0, "overviews":0, "forums":0}
        for k,v in cnts.iteritems():
            c = at_css(html, 'a.product-tabs__tab-%s span.product-tabs__count' % k)
            if c is not None:
                cnts[k] = int(element_text(c))

        return {'name':self.__parse_model_name(html), 'prices_range':prices_range, 
                    'rating_value':rating_value, 'rating_cnt':rating_cnt, "cnts":cnts}


    def __parse_reviews_from_page(self, page_url, limit = None):

        rewiews = []
        while True:

            try_cnt = 6
            for i in range(try_cnt):
                try:
                    html = self.request(page_url)
                    break
                except Exception as e:
                    if i == (try_cnt-1):
                        raise
                    else:
                        warning("parse_model_reviews_page error %s: %s" % (i, e))
                        continue

            self.check_region()

            for rewiew in page_rewiews:
                date_publish = at_xpath(rewiew, './/meta[@itemprop="datePublished"]').attrib['content']
                date_publish = datetime.strptime(date_publish, '%Y-%m-%dT%H:%I:%S')
                review_id = int(rewiew.attrib['id'].replace("review-", ""))
                userid = at_css(rewiew, 'a.b-aura-username')
                userid = userid.attrib['href'].split('/')[2] if userid is not None else None
                rating = self.__parse_rating(rewiew)
                rewiews.append({'userid':userid, 'rating':rating, "id":review_id, 'date_publish':date_publish})

            next_url = at_xpath(html, '//a[@class="b-pager__next"]')
            if next_url is None:
                break
            else:
                page_url = '%s%s' % (self.host, next_url.attrib['href'])
                debug("next url: %s" % page_url)

            if limit is not None and len(rewiews) >= limit:
                rewiews = rewiews[0:limit]
                break

        return rewiews


    def parse_model_reviews_page(self, model_id, hid = None, limit = None):

        page_url = '%s/product/%s/reviews' % (self.host, model_id)
        if hid is not None:
            page_url = page_url + "?hid=" + str(hid)

        debug(page_url)

        rewiews = self.__parse_reviews_from_page(page_url, limit)

        model_name = self.__parse_model_name(self.html)
        breadcrumbs = self.__parse_breadcrumbs(self.html)
        info("Parsed %s reviews from model_id=%s" % (len(rewiews), model_id))

        return {"breadcrumbs":breadcrumbs, "model_name":model_name, "rewiews":rewiews}

    def __parse_breadcrumbs(self, html):
        breadcrumbs = []
        #breadcrumbs_a = xpath(html, '//a[@class="b-breadcrumbs__link"]')
        breadcrumbs_a = xpath(html, '//ul[@class="breadcrumbs2"]//a[@class="link"]')

        for a in breadcrumbs_a:
            breadcrumbs.append({'url':a.attrib['href'].decode('utf-8'), 'title':element_text(a).decode('utf-8')})

        if len(breadcrumbs) == 0:
            raise YandexMarketWebException("Not found breadcrumbs")

        debug("breadcrumbs: %s" % repr(breadcrumbs).decode("unicode-escape"))

        return breadcrumbs

    def __parse_model_name(self, html):
        return element_text(at_css(html, 'h1.title'))#b-page-title__title

    def __parse_rating(self, html):
        rating = at_css(html, 'span.b-aura-rating')
        return int(rating.attrib['data-rate']) if rating is not None else 0

    def parse_model_offers_page(self, model_id, hid = None, limit=20):
        params = {'modelid':model_id, 'grhow':'shop'}
        if hid is not None:
            params['hid'] = hid
        params = urllib.urlencode(params)
        page_url = '%s/offers.xml?%s' % (self.host, params)
        debug(page_url)

        offers = []

        model_name = None
        breadcrumbs = None
        
        while True:
            info(page_url)
            html = self.request(page_url)

            title = element_text(at_xpath(html, '//title'))
            info("title: %s" % title)
            if title == '404':
                raise YandexMarket404Exception("Model %s not found" % model_id)


            self.check_region()
            
            if model_name is None:
                model_name = self.__parse_model_name(html)
            if breadcrumbs is None:
                breadcrumbs = self.__parse_breadcrumbs(html)

            
            offers_info_list = css(html, 'div.b-offers__offers')
            for offer in offers_info_list:

                rating = self.__parse_rating(offer)

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

            
            next_url = at_xpath(html, '//a[@class="b-pager__next"]')
            if next_url is None:
                break
            else:
                page_url = '%s%s' % (self.host, next_url.attrib['href'])
                debug("next url: %s" % page_url)

            if limit is not None and len(offers) >= limit:
                offers = offers[0:limit]
                break


        info("Found %s offers" % len(offers))
        return {'breadcrumbs':breadcrumbs, "model_name":model_name, "offers":offers}



        
