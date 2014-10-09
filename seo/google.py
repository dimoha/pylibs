# -*- coding: utf-8 -*-
from pylibs.network.browser import Browser
from pylibs.network.parser import *
from pylibs.network.urls import *
from logging import info, debug, warning
from pylibs.network.anticaptcha import solveImgUrl, AntiCaptchaException
from pylibs.seo import SeoException
import re,json, urllib, datetime 
from urlparse import urlparse
import time, hashlib, math
from copy import deepcopy 


class GoogleException(SeoException):
	pass


####################################################################################################################
####################################		GOOGLE SEARCH CLASS		####################################
####################################################################################################################


class GoogleException(NetworkException):
	pass

class GoogleQueryException(GoogleException):
	pass

class GoogleBase(object):
	cookie_file = None

class GoogleQuery(GoogleBase):
	AJAX_QUERY=0
	HTML_QUERY=1

	def __init__(self, qtext, region = {'id':-1, 'name':'Любой', 'google_data':None}, query_type = 1, anticaptcha_key=None, anticaptcha_host = None):
		self.q = qtext
		self.results = []
		self.region = region
		self.reask_phrase = None
		self.anticaptcha_key = anticaptcha_key
		self.anticaptcha_host = anticaptcha_host
		self.executeQuery = {
			self.__class__.AJAX_QUERY: self.executeAjaxQuery,
			self.__class__.HTML_QUERY: self.executeHtmlQuery
		}[query_type]

	def executeAjaxQuery(self, start=0, count=10, oldSession=False):
		self.results = []
		textq = self.q
		url = 'http://ajax.googleapis.com/ajax/services/search/web?v=2.0&'+urllib.urlencode({'q':textq, 'start':str(start), 'num': str(count)})
		
		br = Browser(self.cookie_file)


		jsondata = br.get(url)

		data = json.loads(jsondata)

		self.urlnotfound = False
		self.textnotfound = False
		
		
		# check responseStatus
		if 'responseStatus' in data:
			if data['responseStatus']!=200:
				errMsg = 'responseStatus of executeAjaxQuery: '+str(data['responseStatus'])+'.'
				if 'responseDetails' in data:
					if data['responseDetails'].find("Terms of Service Abuse") > 0:
						self.executeHtmlQuery()
						return
					errMsg = errMsg+' '+data['responseDetails']+'.'
				raise GoogleQueryException(errMsg)
		else:
			raise GoogleQueryException('No responseStatus in executeAjaxQuery')

		# check cursor
		if 'cursor' not in data['responseData']:
			raise GoogleQueryException('No cursor in responseData of executeAjaxQuery')
		
		# check exists of results
		if 'responseData' in data:
			if 'results' in data['responseData']:
				if len(data['responseData']['results'])==0:
					self.urlnotfound = True
					self.textnotfound = True
			else:
				raise GoogleQueryException('No results in responseData of executeAjaxQuery')
		else:
			raise GoogleQueryException('No responseData in executeAjaxQuery')
	
		if 'estimatedResultCount' in data['responseData']['cursor']:
			self.totalResults = int(data['responseData']['cursor']['estimatedResultCount'])
		else:
			self.totalResults = len(data['responseData']['results'])

		results = data['responseData']['results']
		i=1
		for result in results:
			r = {}
			r['title'] = result['titleNoFormatting']
			r['url'] = url_from_pynicode(result['url'])
			r['domain'] = get_domain(result['url'])

			if '.' not in result['domain']:
				raise GoogleQueryException('Undefined domain in serp by XML. ('+str(up.netloc)+')')

			r['host'] = r['domain']
			if 'www.'==delete_http(r['url'])[0:4]:
				r['host'] = 'www.'+r['host']
			r['position'] = i
			self.results.append(r)
			i = i +1


	def get_serp(self, deep=100, on_page=100):
		results = []
		cntSerps = int(math.ceil(float(deep)/float(on_page)))
		for p in range(cntSerps):
			self.executeHtmlQuery(p*on_page, on_page, cnt_prev=len(results))
			for pos in self.results:
				results.append(pos)
		self.results = results

	
	def executeHtmlQuery(self, start=0, count=100, cnt_prev=None):
		
		br = Browser(self.cookie_file)
		if hasattr(self, 'proxy'):
			br.proxy = self.proxy
		if hasattr(self, 'proxy_port'):
			br.proxy_port = self.proxy_port

		
		self.results = []
		
		textq = str(self.q)
		
		google_domain = "google.ru"
		google_hl = 'ru'
		
		# блокируем один куки файл на время проведения двух запросов к гуглу
		br.block_cookie = False
		
		location_cookie = None
		if 'google_data' in self.region.keys() and self.region['google_data'] is not None:

			google_domain = self.region['google_data']['domain']
			if 'hl' in self.region['google_data']['get'].keys():
				google_hl = self.region['google_data']['get']['hl']
			if 'manual_hl' in self.region['google_data']:
				google_hl = self.region['google_data']['manual_hl']
				debug('Set manual_hl=%s for request' % google_hl)

			if 'location_cookie' in self.region['google_data']:
				now = int(time.time())
				uid = hashlib.md5(str(now)).hexdigest()
				location_cookie = 'ID=%s:TM=%s:LM=%s:L=%s:S=%s' % (uid[0:16], now, now, self.region['google_data']['location_cookie'], uid[16:32])
				location_cookie = location_cookie.encode('utf-8')
			else:
				prerequest = self.region['google_data']['prerequest']
				prerequest = prerequest.replace('maps.google.ru', google_domain)
				debug('prerequest is %s' % prerequest)
				br.get(prerequest)
			
				cookie_domain = '.'+google_domain
				if google_domain in ['google.by', 'google.kz', 'google.kg', 'google.ge', 'google.tm', 'google.com.tr', 'google.com.cy', 'google.az', 'google.am', 'google.co.uz', 'google.com.tj']:
					cookie_domain = '.google.com'
			
				if cookie_domain in br.current_cookies and '/' in br.current_cookies[cookie_domain] and 'PREF' in br.current_cookies[cookie_domain]['/']:
					location_cookie = br.current_cookies[cookie_domain]['/']['PREF'].value
			
				if location_cookie is None:
					raise GoogleQueryException('Not finded %s cookie. Region id is %s' % (google_domain, self.region['id']))
			
		url = 'https://www.'+google_domain+'/search?as_qdr=all&as_dt=e&hl='+google_hl+'&q='+urllib.quote(textq, '')+'&num='+str(count)+'&start='+str(start)#&filter=0
		debug('Request: %s ' % (url,))
		
		debug('location_cookie is %s' % location_cookie)
		if location_cookie is not None:
			location_cookie = [{'name':'PREF', 'value':location_cookie}]
			debug(location_cookie)

		try:
			debug("Start br.get")
			br.get(url, cookies=location_cookie)
			debug("End br.get")
		except:
			if br.effective_url is not None and urlparse(br.effective_url).path.startswith('/sorry/'):
				html = br.html()
				img = at_xpath(html, "//img[contains(@src, 'sorry')]")
				if img is None:
					raise GoogleQueryException, "captcha not finded on sorry-page for "+str(br.ip_address)
				form = at_xpath(html, "//form[@action = 'Captcha']")
				img_url = br.relative_url(img.attrib['src'])
				action_abs = br.relative_url(form.action)
				debug( 'Request to antigate.com ...')
				code = solveImgUrl(self.anticaptcha_key, captcha_url=img_url, br=br, host=self.anticaptcha_host)
				
				form.fields['captcha'] = code
				debug('Google send captcha '+str(code)+'...')
					
				try:
					br.postForm(form)
					br.get(url, cookies=location_cookie)
				except:
					if urlparse(br.effective_url).path.startswith('/sorry/'):
						raise GoogleQueryException, "captcha twice for "+str(br.ip_address)
					else:
						raise GoogleQueryException, "some other exception"
			else:
				raise
				
		
		html = br.html()


		#### new ####
		need_reask_a = at_xpath(html, u'.//a[@class="spell"]')
		need_reask_span = at_xpath(html, u'.//span[@class="spell"]')
		if need_reask_a is not None and need_reask_span is not None:
			self.reask_phrase = element_text(need_reask_a)

		self.urlnotfound = not at_xpath(html, u'.//*[contains(text(),"Извините, у нас нет информации об адресе")]') is None
		
		self.textnotfound_1 = not at_xpath(html, u'.//*[contains(text(),"Не найдено ни одного документа, соответствующего запросу")]') is None	
		#self.textnotfound_2 = not at_xpath(html, u'.//div[@id="topstuff"]/div[@class="med"]/p') is None	
		self.textnotfound_2 = not at_xpath(html, u'.//div[@id="topstuff"]//div[@class="med"]') is None	
		self.textnotfound_3 = not at_xpath(html, u'.//span[@class="spell_orig"]') is None	
		topstuff = not at_xpath(html, u'.//div[@id="topstuff"]') is None	
	

		
		if self.textnotfound_1 or self.textnotfound_2 or self.textnotfound_3:
			self.textnotfound = True
		else:
			self.textnotfound = False
		
		xtotal = at_css(html, 'div#resultStats')
		if xtotal is not None:	 
			xtotal = element_text(xtotal).strip()
		if xtotal is not None and xtotal!='':		
			ttotal = re.sub("[^\d\(\)]+(?is)", '', xtotal).strip()
			dtotal = re.search('^(\d+)', ttotal).group()
			total = int(dtotal)
			self.totalResults = total
		else:
			if self.urlnotfound or self.textnotfound:
				self.totalResults = 0
			else:
				if not topstuff:
					raise GoogleQueryException('No notfound texts executeHtmlQuery. Request is: '+url)
				else:
					# bad requests... serp exists but its from another query!))
					self.totalResults = 0
		
		
		
		xresults = html.xpath('//li[(@class="g" or @class="g videobox") and not(@id)]')
		
		

		i=1+start
		if cnt_prev is not None and cnt_prev>start:
			i=1+cnt_prev
		
		for xresult in xresults:
			
			intrlu = at_css(xresult, "table.intrlu")
			#if intrlu is not None: # пропускаем адреса
			#	continue

			a = at_xpath(xresult, './/h3[@class="r"]//a[@class="l"]')
			if a is None:
				a = at_css(xresult, "h3.r a")
				

			#a = at_xpath(xresult, '//h3[@class="r"]/a[@class="l"]')
			if a is not None:
				href = a.attrib['href']
				#print href
				
				title = element_text(a)
				result = {}
								
				need_part = False
				
				#print href
				
				if href.startswith('/images?'):
					continue

				if href.startswith('/search?q='):
					continue
				
				is_infected = False
				if href.startswith('/infected?url='):
					is_infected = True
					href = href[14:]
					need_part = True

				if href.startswith('/interstitial?url='):
					href = href[18:]
					need_part = True

				if href.startswith('/url?url='):
					href = href[9:]
					need_part = True

				if href.startswith('/url?q='):
					href = href[7:]
					need_part = True
				
				if need_part:
					href = href.partition('&')
					href = urllib.unquote(href[0])

				if href=='#':
					continue
				#print href
				result['title'] = title
				result['is_infected'] = is_infected


				snippet = at_xpath(xresult, './/span[@class="st"]')
				if snippet is not None:
					snippet = element_text(snippet).strip()
				result['snippet'] = snippet
				
				try:
					result['url'] = url_from_pynicode(href)
					result['domain'] = get_domain(result['url'])	
				except (PynicodeConvertException, BadDomainNetworkException) as e:
					warning(e)
					result['url'] = 'http://google.error/'
					result['domain'] = 'google.error'
				except:
					if intrlu:
						warning('Finded bad domain in addresses block %s... Ny i pohyi.' % href)
						continue
					else:
						raise
				
				if is_infected:
					seo.application.warning('===== INFECTED: %s' % result['domain'])
				
				
				if '.' not in result['domain']:
					raise GoogleQueryException('Undefined domain in serp. ('+str(result['url'])+')')
				
				#<span class="b w xsm">[DOC]</span>

				mimeType = at_xpath(xresult, './/span[@class="b w xsm"]')
				if mimeType is not None:
					result['mimeType'] = element_text(mimeType).replace('[', '').replace(']', '').lower()
				else:
					result['mimeType'] = 'html'
				
				result['host'] = result['domain']
				if 'www.'==delete_http(result['url'])[0:4]:
					result['host'] = 'www.'+result['host']
			
								
				result['position'] = i
				self.results.append(result)
				i = i+1
		debug(len(self.results))
		if len(self.results)==0 and self.totalResults>0:
			if not self.urlnotfound and not self.textnotfound:
				warning('Google Serp have no positions and have no "urlnotfound string". xresults='+str(len(xresults))+', May be parser is broken. url: '+str(url))
				raise GoogleQueryException('Google Serp have no positions and have no "urlnotfound string". May be parser is broken. xresults='+str(len(xresults))+', url: '+str(url))
			


####################################################################################################################
####################################		GOOGLE FUNCTIONS		####################################
####################################################################################################################



def cacheDate(url):
	url = url_to_pynicode(url) # convert to punicode
	curl1 = 'http://webcache.googleusercontent.com/search?hl=en&q='+urllib.quote('cache:'+seo.network.delete_http(url))
	curl2 = 'http://webcache.googleusercontent.com/search?hl=en&q='+urllib.quote('cache:'+seo.network.fix_www(seo.network.delete_http(url)))
	br = Browser()
	for url in [curl1, curl2]:
		br.get(url)
		html = br.unicode()
		m = re.search('It is a snapshot of the page as it appeared on (\d+\s+[a-zA-Z]+\s+\d+)\s+(?is)', html)
		if m:
			cdate = m.group(1).strip()
			debug('google cache date: '+str(cdate))
			time_tuple = time.strptime(cdate, "%d %b %Y")
			timestamp = int(time.mktime(time_tuple))
	return None



def getSavedCopyHTML(url):
	url = url_to_pynicode(url) # convert to punicode
	curl1 = 'http://webcache.googleusercontent.com/search?hl=en&q='+urllib.quote('cache:'+seo.network.delete_http(url))
	curl2 = 'http://webcache.googleusercontent.com/search?hl=en&q='+urllib.quote('cache:'+seo.network.fix_www(seo.network.delete_http(url)))
	debug(curl1)
	debug(curl2)
	br = resourceBrowser()
	for url in [curl1, curl2]:
		
		try:
			br.get(url)
		except BadHttpStatus as httpresponce:
			if httpresponce.code==503:
				warning(br.body())
			
			if httpresponce.code==404:
				continue
			
			raise
		
		html = br.unicode()
		if 'It is a snapshot of the page as it appeared on' in html:
			return html
	raise GoogleException('Cant get SavedCopy from Google')
	
def sindex(domain):
	domain = seo.network.delete_www(seo.network.get_host(domain))
	qtext = "(site:%s OR site:www.%s)" % (domain, domain)
	query = GoogleQuery(qtext)
	query.executeQuery()	
	return int(query.totalResults)

def inIndex(url, returnPage=False):
	
	url = delete_http(url).strip()
	needMask = url.strip('/').lower()
	needMaskUnquoted = urllib.unquote(needMask.encode("utf-8"))
	url = url_to_pynicode(url)
	
	cntRes = 0
	qtexts = ["info:%s" % url, "info:%s" % fix_www(url), "site:%s" % seo.network.delete_www(url)]
	for n,qtext in enumerate(qtexts):
		
		if n==2 and cntRes==0:
			break
		
		query = GoogleQuery(qtext)
		query.executeQuery()	
		if len(query.results)>0:
			cntRes += len(query.results)
			for oneRes in query.results:
				fp = oneRes['url'].lower()
				fpUnquoted = urllib.unquote(fp.encode("utf-8"))
				debug('finded page %s' % fp)
				debug('finded page unquote %s' % fpUnquoted)
				debug('needMask is %s' % needMask)
				debug('needMask unquote %s' % needMaskUnquoted)
				if needMask in fp or needMask in fpUnquoted or needMaskUnquoted in fpUnquoted:
					if returnPage==True:
						return True, oneRes['url']
					else:
						return True

	
	if returnPage:
		return False, None
	else:
		return False


def __checkHash(hashnum):

	checkByte = 0;
	flag = 0;

	hashStr = str(hashnum)
	length = len(hashStr);

	i = length-1
	while i>=0:
		re = int(hashStr[i])
		if 1 == (flag % 2):
			re = re+re;
			re = int((re / 10) + (re % 10))
		
		checkByte = checkByte+re
		flag = flag+1
		i = i-1
	
	checkByte = checkByte % 10

	if 0!=checkByte: 
		checkByte = 10 - checkByte
		if 1==(flag % 2): 
			if 1 == (checkByte % 2): 
				checkByte = checkByte+9
			checkByte >>= 1
	
	return '7'+str(checkByte)+hashStr

 

def __strtonum(s, check, magic):
	int32Unit = 4294967296;
	length = len(s);
	for i in range(0, length):
		check = check*magic

		if check >= int32Unit: 
			check = (check - int32Unit*int(check/int32Unit))
			if check < -2147483648: check = check + int32Unit	
		check = check+ord(s[i]);
	
	return check;


def __hashUrl(s):
	check1 = __strtonum(s, 0x1505, 0x21);
	check2 = __strtonum(s, 0, 0x1003F);

	check1 >>= 2;
	check1 = ((check1 >> 4) & 0x3FFFFC0 ) | (check1 & 0x3F);
	check1 = ((check1 >> 4) & 0x3FFC00 ) | (check1 & 0x3FF);
	check1 = ((check1 >> 4) & 0x3C000 ) | (check1 & 0x3FFF);

	t1 = ((((check1 & 0x3C0) << 4) | (check1 & 0x3C)) <<2 ) | (check2 & 0xF0F );
	t2 = ((((check1 & 0xFFFFC000) << 4) | (check1 & 0x3C00)) << 0xA) | (check2 & 0xF0F0000 );

	return (t1 | t2);
	
def __get_google_ch(u):
	u = __hashUrl(u)
	u = __checkHash(u)
	return u

def getPR(url):
	u = delete_http(url.strip());
	u = url_to_pynicode(u) # convert to punicode
	ch = __get_google_ch(u);
	u = urllib.quote(u, '')
	
	#u = "http://toolbarqueries.google.com/search?client=navclient-auto&ch="+ch+"&features=Rank&q=info:"+u+"&num=100&filter=0"
	u = "http://toolbarqueries.google.com/tbr?features=Rank&sourceid=navclient-ff&client=navclient-auto-ff&ch="+ch+"&q=info:"+u+""
	
	html = get_page_as_browser(u)

	pr = 0
	if html[0]==True and html[1]!='':
		m = re.search('Rank_(\d+):(\d+):(\d+)(?is)', html[1])
		if m:
			try:
				pr = int(m.group(3))
			except:
				pr = 0

	return pr


def translate(text,to_lang="en",from_lang = "ru"):
	br = Browser()
	
	if isinstance(text, unicode):
		text = text.encode("utf-8")

	url = "http://translate.google.ru/translate_a/t?client=t&text=%s&hl=ru&sl=%s&tl=%s&multires=0&trs=1&prev=btn&ssel=0&tsel=4&notlr=0&sc=1" % (urllib.quote(text, ''), from_lang, to_lang)

	br.get(url)

	data = br.body()
	data = re.sub(',,',',null,',data)
	data = re.sub(',,',',null,',data)
	data = re.sub(',]', ']', data)
	data = json.loads(data)

	translated = data[0][0][0]
	return translated
