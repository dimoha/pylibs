# -*- coding: utf-8 -*-
from pylibs.network import NetworkException
from lxml.cssselect import CSSSelector
from lxml import etree, html
import lxml, time, re
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


def getPageLinks(url, html=None, options = {'type':'ext', 'noindex':False, 'nofollow':False}):
	
	allLinks = []

	if html==None:
		br = Browser()
		br.get(url)
		html = br.unicode()
	
	html = re.sub('<!--\s*([/]?)noindex\s*-->(?is)', '<\\1noindex>', html)
	html = re.sub('<!--.*?-->(?isu)', '', html)
	html = re.sub('<style[^>]*>.*?</style>(?isu)', '', html)
	html = re.sub('<script[^>]*>.*?</script>(?isu)', '', html)
	

	stop_domains = ['depositfiles.com', 'facebook.com', 'feedburner.com', 'google.com', 'letitbit.net', 'liveinternet.ru', 'mail.ru', 'okis.ru', 'rambler.ru', 'twitter.com', 'ucoz.ru', 'w3.org', 'vk.com', 'vkontakte.ru', 'wordpress.org', 'yandex.ru', 'youtube.com']

	if html!='':
		try:
			html = parse_html(html)
		except Exception as e:
			return allLinks
	else:
		return allLinks
	
	# create manual base href
	baseHref = delete_http(url).split('/')
	if len(baseHref)>1:
		baseHref.pop()
	baseHref = 'http://'+"/".join(baseHref)+"/"

	
	# try parse base href from html
	baseHref_tmp = at_xpath(html, './/head/base/@href')
	if baseHref_tmp!=None:
		tmp = str(baseHref_tmp)
		try:
			if domain(tmp)==domain(url):
				baseHref = tmp.strip()
		except:
			pass
	
	# this domain
	tDomain = domain(baseHref)
	tHost = get_host(baseHref)
	
	rFilter = re.compile(u"[^/]+/\.\.(?is)")
	
	if 'nofollow' in options and not options['nofollow']:
		no_get_nofollow = True
	else:
		no_get_nofollow = False
  
	links = xpath(html, './/a[@href]')
	for link in links:
		
		href = at_xpath(link, '@href')
		
		if 'javascript' in href.lower() or 'mailto' in href.lower():
			continue
		
		anchor = element_text(link).strip()
		if anchor=='':
			anchor = None

	
		# detect noindex
		noindex = at_xpath(link, 'ancestor::noindex')
		noindex = not noindex is None


		if 'noindex' in options and options['noindex']==False and noindex:
			continue
		
		
		
		# detect nofollow
		rel = at_xpath(link, '@rel')
		if rel!=None and ' nofollow ' in ' '+str(rel)+' ':
			nofollow = True
		else:
			nofollow = False
	
		m = re.search('(http[s]?):\/\/(?is)', href)
		if m:
			protocol = m.group(1).strip()
			tHost = get_host(href)
			href = href.replace(tHost, tHost.lower())
			href = href.replace(protocol, protocol.lower())

		href = href.strip(" \"'\n\r")

		if href=='':
			href = '/'

		m1 = re.search('^http[s]?://(?is)', href)
		m2 = re.search('^http[s]?://([^/\?:]+\.|)'+tDomain+'(?is)', href) 

	
		if m1==None or m2:
			lType = 'int'
		else:
			lType = 'ext'
			
		if 'type' in options and options['type']!=lType:
			continue

					
		if lType=='int':
			if m1==None:
				if href[0:2]=='./':
					href = href[2:].strip()
					if href=='':
						href = '/'

				if href[0]!='/': 
					href = baseHref+href
				else:
					href = 'http://'+tHost+'/'+href

				# replace double "/"
				href = re.sub('/+(?is)', '/', delete_http(href))						

				while re.search(rFilter, href):
					href = re.sub(rFilter, '/', href)	

				href = 'http://'+href;
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
			
		if no_get_nofollow and nofollow:
			continue
		
		allLinks.append({'href':str(href), 'anchor':str(anchor), 'noindex':noindex, 'nofollow':nofollow, 'type':lType})

	return allLinks


def strip_tags(value):
	return re.sub('<[^>]*?>(?is)', '', value)

