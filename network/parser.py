# -*- coding: utf-8 -*-
from pylibs.network import NetworkException
from pylibs.network.urls import delete_http, get_domain, get_host, BadDomainNetworkException
from lxml.cssselect import CSSSelector
from lxml import etree, html
import lxml, re
from string import *


class ParserException(NetworkException):
    pass


def print_element(element):
    pe = etree.tostring(element, pretty_print=True, method="html")
    lxml.html.etree.clear_error_log()
    print(pe)


def css(tree, selectorSpec):
    sel = CSSSelector(selectorSpec)
    lxml.html.etree.clear_error_log()
    return sel(tree)


def at_css(tree, selectorSpec):
    r = css(tree, selectorSpec)
    lxml.html.etree.clear_error_log()
    if r:
        return r[0]
    else:
        return None


def at_xpath(e, path):
    r = e.xpath(path)
    lxml.html.etree.clear_error_log()
    if r:
        return r[0]
    else:
        return None


def xpath(e, path):
    r = e.xpath(path)
    lxml.html.etree.clear_error_log()
    return r


def element_text(e, method='text'):
    et = strip(etree.tostring(e, method=method, encoding="UTF-8"))
    lxml.html.etree.clear_error_log()
    return et


def parse_html(htmldata):
    htmldata = htmldata.replace('<![CDATA[', '').replace(']]><', '<')
    ph = lxml.html.fromstring(htmldata)
    lxml.html.etree.clear_error_log()
    return ph


def parse_xml(xml):
    ph = etree.fromstring(xml)
    etree.clear_error_log()
    return ph


def get_page_links(url, html_string, link_type='ext', is_noindex=False, is_nofollow=False):
    
    all_links = []

    html_string = re.sub('<!--\s*([/]?)noindex\s*-->(?is)', '<\\1noindex>', html_string)
    html_string = re.sub('<!--.*?-->(?isu)', '', html_string)
    html_string = re.sub('<style[^>]*>.*?</style>(?isu)', '', html_string)
    html_string = re.sub('<script[^>]*>.*?</script>(?isu)', '', html_string)
    
    stop_domains = ['depositfiles.com', 'facebook.com', 'feedburner.com', 'google.com', 'letitbit.net',
                    'liveinternet.ru', 'mail.ru', 'okis.ru', 'rambler.ru', 'twitter.com', 'ucoz.ru', 'w3.org',
                    'vk.com', 'vkontakte.ru', 'wordpress.org', 'yandex.ru', 'youtube.com']
    if html_string != '':
        try:
            html_string = parse_html(html_string)
        except Exception as e:
            return all_links
    else:
        return all_links
    
    # create manual base href
    base_href = delete_http(url).split('/')
    if len(base_href) > 1:
        base_href.pop()
    base_href = 'http://'+"/".join(base_href)+"/"

    # try parse base href from html
    base_href_tmp = at_xpath(html_string, './/head/base/@href')
    if base_href_tmp is not None:
        tmp = str(base_href_tmp)
        try:
            if get_domain(tmp) == get_domain(url):
                base_href = tmp.strip()
        except:
            pass
    
    # this domain
    this_domain = get_domain(base_href)
    this_host = get_host(base_href)
    
    r_filter = re.compile(u"[^/]+/\.\.(?is)")
    
    links = xpath(html_string, './/a[@href]')
    for link in links:
        href = at_xpath(link, '@href')
        
        if 'javascript' in href.lower() or 'mailto' in href.lower():
            continue
        
        anchor = element_text(link).strip()
        if anchor == '':
            anchor = None

        # detect noindex
        noindex = at_xpath(link, 'ancestor::noindex')
        noindex = not noindex is None

        if not is_noindex and noindex:
            continue

        # detect nofollow
        rel = at_xpath(link, '@rel')
        nofollow = True if rel is not None and ' nofollow ' in ' %s ' % rel else False
        m = re.search('(http[s]?):\/\/(?is)', href)
        if m:
            this_protocol = m.group(1).strip()
            this_host_local = get_host(href)
            href = href.replace(this_host_local, this_host_local.lower())
            href = href.replace(this_protocol, this_protocol.lower())

        href = href.strip(" \"'\n\r")

        if href == '':
            href = '/'

        m1 = re.search('^http[s]?://(?is)', href)
        m2 = re.search('^http[s]?://([^/\?:]+\.|)'+this_domain+'(?is)', href)

        l_type = 'int' if m1 is None or m2 else 'ext'

        if link_type != l_type:
            continue

        if l_type == 'int':
            if m1 is None:
                if href[0:2] == './':
                    href = href[2:].strip()
                    if href == '':
                        href = '/'

                if href[0] != '/':
                    href = base_href+href
                else:
                    href = 'http://%s/%s' % (this_host, href)

                # replace double "/"
                href = re.sub('/+(?is)', '/', delete_http(href))                        

                while re.search(r_filter, href):
                    href = re.sub(r_filter, '/', href)

                href = 'http://%s' % href
                href = href.replace('../', '')
            href = re.sub('#.*$(?is)', '', href)    
        else:
            # считаем что ссылки со стоп ресурсов - в ноуфоллоу
            try:
                lnk_domain = get_domain(href)
            except BadDomainNetworkException:
                continue

            lnk_domain_2 = ".".join(lnk_domain.split('.')[-2:])
            if lnk_domain in stop_domains or lnk_domain_2 in stop_domains:
                nofollow = True
            
        if not is_nofollow and nofollow:
            continue
        
        all_links.append({'href': str(href), 'anchor': str(anchor), 'noindex': noindex,
                          'nofollow': nofollow, 'type': l_type})

    return all_links



