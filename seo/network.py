# -*- coding: utf-8 -*-
import sys, iconv, pycurl, re, os, cookielib, time, urllib, urlparse, json, threading
from cStringIO import StringIO
from lxml import etree, html
from lxml.cssselect import CSSSelector
import lxml, time
from string import *
from urllib2 import Request

from seo import SeoException

class NetworkException(SeoException):
	pass

class BrowserException(NetworkException):
	pass

class BadHttpStatus(BrowserException):
	def __init__(self, msg = False):
		BrowserException.__init__(self, msg)
		statuses = {'100': 'Continue', '101': 'Switching Protocols', '201': 'Created', '202': 'Accepted', '203': 'Non-Authoritative Information', '204': 'No Content', '205': 'Reset Content', '206': 'Partial Content', '300': 'Multiple Choices', '301': 'Moved Permanently', '302': 'Found', '303': 'See Other', '304': 'Not Modified', '305': 'Use Proxy', '307': 'Temporary Redirect', '400': 'Bad Request', '401': 'Unauthorized', '402': 'Payment Required', '403': 'Forbidden', '404': 'Not Found', '405': 'Method Not Allowed', '406': 'Not Acceptable', '407': 'Proxy Authentication Required', '408': 'Request Timeout', '409': 'Conflict', '410': 'Gone', '411': 'Length Required', '412': 'Precondition Failed', '413': 'Request Entity Too Large', '414': 'Request-URI Too Long', '415': 'Unsupported Media Type', '416': 'Requested Range Not Satisfiable', '417': 'Expectation Failed', '500': 'Internal Server Error', '501': 'Not Implemented', '502': 'Bad Gateway', '503': 'Service Unavailable', '504': 'Gateway Timeout', '505': 'HTTP Version Not Supported'}
		self.code = int(self.message)
		if str(self.message) in statuses:
			self.message = str(self.message)+" "+statuses[str(self.message)]

class CannotResolve(BrowserException):
	pass

class ConnectionTimeOut(BrowserException):
	pass

class CurlError(BrowserException):
	pass

class Browser():


	def tab(self):
		br = Browser(self.cookie_file)
		br.ip_address = self.ip_address
		br.user_agent = self.user_agent
		br.referer = None
		br.connect_timeout = self.connect_timeout
		br.timeout = self.timeout
		br.maxredirs = self.maxredirs
		br.proxy_port = self.proxy_port
		br.proxy_type = self.proxy_type
		br.proxy = self.proxy
		return br
		
	def __init__(self, cookie_file = None):
		self.cookie_file = cookie_file
		self.closed = False
		self._body = StringIO()
		self._header = StringIO()
		self.ip_address = None
		self.user_agent = 'Mozilla/5.0 (Windows NT 5.1; rv:19.0) Gecko/20100101 Firefox/19.0' 
		self.referer = None
		self.connect_timeout = None
		self.perform_url = None
		self.effective_url = None
		self.http_status = None
		self._html = None
		self._json = None
		self._text = None
		self.timeout = 15
		self.name = str(id(self))
		self.page_handler = default_page_handler
		self.maxredirs = 10
		self.headers = []
		self.block_cookie = True
		self.current_cookies = {}
		self.curl = None
		self.user_pwd = None
		self.ssl_cert = None
		self.ssl_key = None
		
		self.proxy = None
		self.proxy_port = None
		self.proxy_type = None

	def __str__(self):
		return self.name
	
	def save_cookie_file(self,permanent_cookie_file = None):
		if permanent_cookie_file and permanent_cookie_file != self.cookie_file:
			os.remove(permanent_cookie_file)
			os.rename(self.cookie_file, permanent_cookie_file)
			self.cookie_file = permanent_cookie_file
		
	

		
	
	def printCookies(self, jar = None):
		for cookie in jar or self.getCookieJar():
			print cookie.name + "=" + str(cookie.value)
	
	
	###################### special class for extract_cookies
	class headerInfo():
		def __init__(self, s):
			self.headers = {}
			for one in s.replace("\r", "\n").split("\n"):
				oneList = one.strip().split(":")
				tc = oneList[0].strip()
				if tc!='':
					if tc not in self.headers:
						self.headers[tc] = []
					self.headers[tc].append(":".join(one.split(':')[1:]).strip())
	
		def info(self):
			return self
		
		def getheaders(self, name):
			if name in self.headers:
				return self.headers[name]
			return []

		def getallmatchingheaders(self, name):
			res = []
			if name in self.headers:
				for val in self.headers[name]:
					res.append('%s: %s\r\n' % (name, val))
			return res

	
	def saveCookies(self):
		ho = self.headerInfo(self._header.getvalue())
		req = Request(self.perform_url)
		jar = self.getCookieJar(True)
		jar.extract_cookies(ho, req)
		# костыль под беларусский регион в гугле и под казахстанский. до лучших времен пока гугл багу не поправит
		if 'google.' in self.perform_url:
			jar.extract_cookies(ho, Request('google.com'))
		self.current_cookies = jar._cookies
	
	###########################################################
	def _process_cookies(self, work_type, ck):
		if work_type=='read':
			try:
				ck.load()
			except:
				pass
		else:
			jar = self.getCookieJar(True);
			jar.set_cookie(ck)
			jar.save(ignore_discard=True, ignore_expires=True)

	def _work_with_cookies(self, work_type='read', ck=None, withLock=False):
		self._process_cookies(work_type, ck)

		return ck

	def getCookieJar(self, withLock=True):
		cookie_jar = cookielib.MozillaCookieJar(self.cookie_file)
		self._work_with_cookies('read', cookie_jar, withLock)
		return cookie_jar
	
	def setCookie(self, cname, cvalue, cdomain = None, cpath = None, cexpires = int(time.time()) + 3600):
		ck = cookielib.Cookie(version=0, name=cname, value=cvalue, port=None, port_specified=False, domain=(cdomain or "www.example.com"), domain_specified=(not cdomain is None), domain_initial_dot=False, path=(cpath or "/"), path_specified=(not cpath is None), secure=False, expires=cexpires, discard=False, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
		self._work_with_cookies('write', ck, True)

	def getCookie(self, name, domain = None):
		for cookie in self.getCookieJar():
			if cookie.name == name:
				if not domain or domain == cookie.domain:
					return cookie.value
		return None

	def removeDuplicatesCookies(self, cookies):
		names = []
		for ck in cookies:
			names.append(ck['name'])
		need_save = False
		jar = self.getCookieJar()
		for cookie in jar:
			if cookie.name in names:
				jar.clear(cookie.domain, cookie.path, cookie.name)
				need_save = True
		jar.save(ignore_discard=True, ignore_expires=True)


	def set_useragent(self):
		lastNum = int(self.ip_address[-2:].replace('.', ''))
		agents = [
				'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/18.6.872.0 Safari/535.2 UNTRUSTED/1.0', 
				'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3', 
				'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6', 
				'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6', 
				'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', 
				'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/28.0.1469.0 Safari/537.36', 
				'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/28.0.1469.0 Safari/537.36', 
				'Mozilla/5.0 (Windows NT 6.1; rv:12.0) Gecko/20120403211507 Firefox/12.0', 
				'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1',
				'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20120427 Firefox/15.0a1', 
				'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0) Gecko/16.0 Firefox/16.0', 
				'Mozilla/5.0 (Windows NT 6.2; rv:19.0) Gecko/20121129 Firefox/19.0', 
				'Mozilla/5.0 (Windows NT 6.2; rv:20.0) Gecko/20121202 Firefox/20.0', 
				'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Maxthon 2.0)', 
				'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.1 (KHTML, like Gecko) Maxthon/3.0.8.2 Safari/533.1', 
				'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML like Gecko) Maxthon/4.0.0.2000 Chrome/22.0.1229.79 Safari/537.1', 
				'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)', 
				'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)', 
				'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/4.0)', 
				'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)', 
				'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/5.0)', 
				'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)', 
				'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.2; Trident/5.0)', 
				'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.2; WOW64; Trident/5.0)', 
				'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)', 
				'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/6.0)', 
				'Opera/9.25 (Windows NT 6.0; U; en)', 
				'Opera/9.80 (Windows NT 5.2; U; en) Presto/2.2.15 Version/10.10', 
				'Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.7.39 Version/11.00', 
				'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.7.62 Version/11.01', 
				'Opera/9.80 (Windows NT 5.1; U; zh-tw) Presto/2.8.131 Version/11.10', 
				'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00', 
				'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10', 
				'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/533.17.8 (KHTML, like Gecko) Version/5.0.1 Safari/533.17.8', 
				'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5', 
				'Mozilla/5.0 (Windows; U; Windows NT 6.2; es-US ) AppleWebKit/540.0 (KHTML like Gecko) Version/6.0 Safari/8900.00', 
				'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.1.17) Gecko/20110123 (like Firefox/3.x) SeaMonkey/2.0.12', 
				'Mozilla/5.0 (Windows NT 5.2; rv:10.0.1) Gecko/20100101 Firefox/10.0.1 SeaMonkey/2.7.1', 
				'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20120422 Firefox/12.0 SeaMonkey/2.9', 
				'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:15.0) Gecko/20100101 Firefox/15.0.1'
			]
		lastNum %= len(agents)
		self.user_agent = agents[lastNum]
		#self.user_agent = 'YB/5.1.1'
		

	def _curl_init(self, curl, cookies=None):
		self._body.truncate(0)
		self._header.truncate(0)
		self._html = None
		self._text = None
		curl.setopt(curl.HEADERFUNCTION, self._header.write)
	
		if cookies is not None:
			self.removeDuplicatesCookies(cookies)
			cookie_to_send = []
			for cookie in cookies:
				cookie_to_send.append('%s=%s' % (cookie['name'], cookie['value']))
			curl.setopt(pycurl.COOKIE, "; ".join(cookie_to_send))
		if self.cookie_file:
			curl.setopt(pycurl.COOKIEFILE, self.cookie_file)
			curl.setopt(pycurl.COOKIEJAR, self.cookie_file)

		curl.setopt(pycurl.FOLLOWLOCATION, 1)
		curl.setopt(pycurl.MAXREDIRS, self.maxredirs)
		curl.setopt(pycurl.USERAGENT, self.user_agent)
		curl.setopt(pycurl.ENCODING, "gzip")
		curl.setopt(pycurl.NOSIGNAL, 1)
		curl.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)
		if self.ssl_cert:
			curl.setopt(pycurl.SSLCERT, self.ssl_cert)
		if self.ssl_key:
			curl.setopt(pycurl.SSLKEY, self.ssl_key)

		if self.timeout:
			curl.setopt(pycurl.TIMEOUT, self.timeout)
		if self.ip_address:
			self.set_useragent()
			curl.setopt(pycurl.INTERFACE, self.ip_address)
		if self.effective_url and not self.referer:
			self.referer = self.effective_url
		
		if self.referer:
			curl.setopt(pycurl.REFERER, self.referer)
		if self.connect_timeout:
			curl.setopt(pycurl.CONNECTTIMEOUT, self.connect_timeout);
		
		if self.proxy:
			curl.setopt(pycurl.PROXY, self.proxy)
			curl.setopt(pycurl.PROXYPORT, self.proxy_port)
			if self.proxy_type == 'socks5':
				curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)

		if self.headers:
			curl.setopt(pycurl.HTTPHEADER, self.headers)

		if self.user_pwd is not None:
			curl.setopt(pycurl.USERPWD, self.user_pwd)
		
		self.curl = curl

	def curlException(self,e):
		message = e[1]
		code = e[0]
		known = {
			6:CannotResolve(domain(self.perform_url)),
			28:ConnectionTimeOut(message+' ('+self.perform_url+')')
		}
		
		if code in known.keys():
			return known[code]
		else:
			return CurlError("%s, error code = %s" % (message,code))


	def _curl_info(self, curl):
		self.effective_url = curl.getinfo(pycurl.EFFECTIVE_URL)
		self.http_status = curl.getinfo(pycurl.HTTP_CODE)
		self.saveCookies()

	def get(self, url, headers = {}, cookies = None):
		curl = pycurl.Curl()
		self.perform_url = url
				
		if len(headers)>0:
			self.headers = headers
	
		self._curl_init(curl, cookies=cookies)
		
		url = url_to_pynicode(url) 

		curl.setopt(pycurl.URL, str(url))
		curl.setopt(curl.WRITEFUNCTION, self._body.write)
		try:
			curl.perform()
		except pycurl.error as e:
			raise self.curlException(e)
		self._curl_info(curl)
		curl.close()
		if self.http_status != 200:
			raise BadHttpStatus, self.http_status
		
		self.page_handler(self)
		return self._body.getvalue()
		
	def post(self, url, fields = None, postdata = None, content_type = None, cookies = None, files = None):
		self.perform_url = url
				
		if fields is not None:
			postdata = urllib.urlencode(fields)
		
		curl = pycurl.Curl()
		self._curl_init(curl, cookies=cookies)
		
		url = url_to_pynicode(url) 
		curl.setopt(pycurl.URL, str(url))
		curl.setopt(curl.WRITEFUNCTION, self._body.write)
		curl.setopt(pycurl.POST, 1)
		
		if postdata is not None:
			curl.setopt(pycurl.POSTFIELDS,postdata)
		if content_type is not None:
			curl.setopt(pycurl.HTTPHEADER, ["Content-type: %s" % content_type])
		
		if files is not None:
			to_send = []
			if postdata is not None and postdata!='':
			    to_send = map(lambda x: tuple(x.split('=')) if '=' in x else (x, '') , postdata.split('&'))
			for filename in files:
				to_send.append((os.path.basename(filename), (curl.FORM_FILE, filename)))				
			curl.setopt(curl.HTTPPOST, to_send)
	
		
		try:
			curl.perform()
		except pycurl.error as e:
			raise self.curlException(e)
		
		self._curl_info(curl)
		curl.close()
		
		if self.http_status != 200:
			raise BadHttpStatus, self.http_status

		self.page_handler(self)
		return self._body.getvalue()
	
	def relative_url(self, url):
		return self._action_url(url)
	
	def _action_url(self,action):
		return urljoin(self.effective_url, action)
	
	def postForm(self, form, addparams = {}):
		utf8data = {}
		utf8data.update(form.fields)
		utf8data.update(addparams)
		for field, value in utf8data.iteritems():
			if isinstance(value,unicode):
				utf8data[field] = value.encode("utf-8")
		if not self.perform_url:
			raise AppException('effective_url is not set')
		if form.method.lower() == 'post':
			return self.post(self._action_url(form.action), utf8data)
		else:
			return self.get(self._action_url(form.action) + "?" + urllib.urlencode(utf8data))		
	
	def download(self, filename, url):
		self.perform_url = url
		curl = pycurl.Curl()
		self._curl_init(curl)
		self.perform_url = url
		f = open(filename, "wb")
		curl.setopt(pycurl.URL, str(url))
		curl.setopt(curl.WRITEDATA, f)
		curl.perform()
		self._curl_info(curl)
		curl.close()
		f.close
		return self._body.getvalue()
		
	def close(self):
		self.closed = True
	
	def body(self):
		return self._body.getvalue()	
	
	def header(self):
		allheaders =  self._header.getvalue()
		headers = allheaders.split("\r\n\r\nH")
		return headers[-1].strip()

	def html(self):
		if self._html is None:
			self._html = parse_html(self.unicode())
		return self._html
	
	def unicode(self):
		global __convert_page_encoding
		if self._text is None:
			self._text = convert_page_encoding(self.body(), header = self.header())
		return self._text
	
	def json(self):
		if self._json is None:
			self._json = json.loads(self.body())
		return self._json
	



def default_page_handler(br):
	pass

def urljoin(host, action):
	if not re.match("https?://.*", host):
		host = "http://" + host 
	if action == "?":
		return urlparse.urljoin(host, "/")
	if re.match("https?://.*", action):
		return action
	else:
		return urlparse.urljoin(host, action)

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

def print_form(form):
	for field, value in form.fields.iteritems():
		print field + "=" + unicode(value)

#browser resources

class UnknownResource(NetworkException):
	pass

def _defaultBeforeUse(name,browser):
	pass

def _defaultAfterUse(name,browser,success,data = None):
	pass

_resources = {}


class ResourceUnavailable(NetworkException):
	def __init__(self, resource):
		NetworkException.__init__(self, resource.name)
		self.resource = resource

class Resource():
	def __init__(self, name, parent_name = None, beforeUse = None, afterUse = None):
		self.name = name
		self.parent_name = parent_name
		if beforeUse is not None:
			self.beforeUse = beforeUse
		
		if afterUse is not None:
			self.afterUse = afterUse
	
	def available(self):
		parent = self.parent()
		if parent is not None:
			return parent.available()
		else:
			return True
	
	def beforeUse(self, name, browser):
		pass
	
	def afterUse(self, name, browser,success,data):
		pass
	
	def getHierarchy(self):
		io = self
		ao = [io]
		while io.parent() is not None:
			io = io.parent()
			ao.append(io)
		return ao
	
	def parent(self):
		if self.parent_name in _resources:
			return _resources[self.parent_name]
		else:
			return None
	
_resources = {
	"default" : Resource("default")
}


def getResource(name):
	if name in _resources.keys():
		return _resources[name] 
	else:
		raise UnknownResource, name

def setResource(name, resource, parent = None):
	resource.name = name
	resource.parent_name = parent
	_resources[name] = resource


def resourceRegister(name, beforeUse = None, afterUse = None, parent = 'default'):
	_resources[name] = Resource(name, parent, beforeUse, afterUse)
	

def resourceBeforeUse(name, browser):
	getResource(name).beforeUse(name, browser)

def resourceAfterUse(name, browser, success = True, data = None):
	getResource(name).afterUse(name, browser, success, data)

_local = threading.local()


def resourceBrowser():
	if hasattr(_local,'browser'):
		return _local.browser
	else:
		raise SeoException("No local resource browser defined")

class resource_function():
	def __init__(self, resource):
		self.resource_name = resource

	def __call__(self, function):
		def wrapper(*args,**kwargs):
			self.resource = getResource(self.resource_name)
			
			if not self.resource.available():
				raise ResourceUnavailable(self.resource)
			local = threading.local()
			old_br = None
			if hasattr(_local,'browser'):
				old_br = _local.browser
			try:
				_local.browser = Browser()
				hierarchy = self.resource.getHierarchy()
				hierarchy.reverse()
				for resource in hierarchy:
					resourceBeforeUse(resource.name, _local.browser)

				ret = function(*args,**kwargs)
				hierarchy.reverse()
				for resource in hierarchy:
					resourceAfterUse(resource.name, _local.browser, True)
				return ret
			except Exception as e:
				print "Exception in resource_function: %s" % e
				hierarchy = self.resource.getHierarchy()
				for resource in hierarchy:
					resourceAfterUse(resource.name, _local.browser, False,{"exception":e})
				raise
			finally:
				_local.browser = old_br
		wrapper.__doc__  = function.__doc__
		wrapper.__name__ = function.__name__
		return wrapper

resource_method = resource_function

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
	#html = html.replace('</html>', '')+'</html>'
	#html = re.sub('<noscript[^>]*>.*?</noscript>(?isu)', '', html)
	

	stop_domains = ['depositfiles.com', 'facebook.com', 'feedburner.com', 'google.com', 'letitbit.net', 'liveinternet.ru', 'mail.ru', 'okis.ru', 'rambler.ru', 'twitter.com', 'ucoz.ru', 'w3.org', 'vk.com', 'vkontakte.ru', 'wordpress.org', 'yandex.ru', 'youtube.com']
	#print html
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
		#print '%s => %s' % (href, noindex)
		
		if 'javascript' in href.lower() or 'mailto' in href.lower():
			continue
		
		anchor = element_text(link).strip()
		if anchor=='':
			anchor = None

	
		# detect noindex
		noindex = at_xpath(link, 'ancestor::noindex')
		noindex = not noindex is None

		#print '%s => %s' % (href, noindex)

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
		m2 = re.search('^http[s]?://([^/\?:]+\.|)'+tDomain+'(?is)', href) # with subdomains.  

		# Если захотите вернуть как было раньше, надо раскоментить ниже приведенную строку обязательно! иначе с www будут как внешние, так как www тоже по сути субдомен
		#m3 = re.search('^http[s]?://([^/\?:]+\.|)'+fix_www(tDomain)+'(?is)', href) # with subdomains		

	
		if m1==None or m2:  #or m3
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

@resource_method('default')
def get_site_title(url):
	domain = get_domain(url)
	br = resourceBrowser()
	br.get(domain)
	m = re.search('<title[^>]*>(.*?)</title>(?isu)', br.unicode())
	if m:
		return m.group(1).strip()
	else:
		return None
def iri_to_uri(iri):
	"""
	Convert an Internationalized Resource Identifier (IRI) portion to a URI
	portion that is suitable for inclusion in a URL.
 
	This is the algorithm from section 3.1 of RFC 3987.  However, since we are
	assuming input is either UTF-8 or unicode already, we can simplify things a
	little from the full method.
 
	Returns an ASCII string containing the encoded result.
	"""
	# The list of safe characters here is constructed from the "reserved" and
	# "unreserved" characters specified in sections 2.2 and 2.3 of RFC 3986:
	#     reserved    = gen-delims / sub-delims
	#     gen-delims  = ":" / "/" / "?" / "#" / "[" / "]" / "@"
	#     sub-delims  = "!" / "$" / "&" / "'" / "(" / ")"
	#                   / "*" / "+" / "," / ";" / "="
	#     unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
	# Of the unreserved characters, urllib.quote already considers all but
	# the ~ safe.
	# The % character is also added to the list of safe characters here, as the
	# end of section 3.1 of RFC 3987 specifically mentions that % must not be
	# converted.
	if iri is None:
		return iri
	if isinstance(iri, unicode):
		iri = iri.encode('utf-8')
		repr(iri)
	return urllib.quote(iri, safe="/#%[]=:;$&()+,!?*@'~")

class PynicodeConvertException(NetworkException):
	pass

def url_to_pynicode(url, is_iri_to_uri=False):
	h = delete_www(get_host(url))
	
	if type(h).__name__!='unicode':
		h = unicode(h, 'utf-8')
	
	hp = str(h.encode("idna")) 
	prepared = url.replace(h, hp, 1)
	repr(prepared)
	if is_iri_to_uri:
		prepared = iri_to_uri(prepared)
		repr(prepared)
	return prepared

def url_from_pynicode(url):
	h = delete_www(get_host(url, False))
	
	if type(h).__name__!='unicode':
		h = unicode(h, 'utf-8')
	
	try:
		hp = str(h.decode("idna").encode('utf-8')).lower() # convert from punicode
	except Exception as e:
		raise PynicodeConvertException('%s in url %s, domain %s' % (str(e), url, h))
			

	return url.replace(h, hp, 1)

def is_www(s):
	if s.lower().startswith('www.'):
		s = s[4:]
		if '.' in s:
			return True
	return False

def fix_www(s):
	if s.lower().startswith('www.'):
		s = s[4:]
	else:	
		s = 'www.'+s
	return s


def delete_www(s):
	s = s.strip()
	while s.lower().startswith('www.'):
		tmp = s[4:]
		if '.' not in tmp:
			return s
		s = tmp
	return s

def get_domain(url):
	return domain(url)

class BadDomainNetworkException(NetworkException):
	pass

def domain(url):
	domain = delete_www(get_host(url)).strip().lower()
	if domain=='' or '.' not in domain or '(' in domain or "'" in domain:
		raise BadDomainNetworkException('Cant get domain from url: %s' % url)
	return domain

def delete_http(s):
	s = s.strip()
	if s.lower().startswith('http://'):
		s = s[7:]
	elif s.lower().startswith('https://'):
		s = s[8:]
	elif s.lower().startswith('ftp://'):
		s = s[6:]
	return s

def get_host(s, lower=True):
	s = delete_http(s.strip(' /')).split('/');
	s = s[0]
	s = s.strip(' /').split('?')[0]
	if '@' in s:
		try:
			s = s.split('@')[1]
		except IndexError:
			pass
	s = s.strip(' /').split(':')[0]
	host = s.strip(' /')
	if(lower==True):
		host = s.lower()
	return host

def split_url(url):
	domain_url = delete_www(get_host(url, False)).strip()
	if domain_url!='' and '.' in domain_url:
		page_url = delete_www(delete_http(url)).partition(domain_url)
	else:
		raise NetworkException('Unknown URL-format: "'+str(url)+'".')
	return domain_url.lower().strip(), (page_url[0]+page_url[2]).strip()

def is_social_site(url):
	MOZ_TOP = ['facebook.com', 'twitter.com', 'google.com', 'youtube.com', 'wordpress.org', 'adobe.com', 'blogspot.com', 'wikipedia.org', 'wordpress.com', 'linkedin.com', 'yahoo.com', 'amazon.com', 'flickr.com', 'w3.org', 'pinterest.com', 'apple.com', 'tumblr.com', 'myspace.com', 'microsoft.com', 'vimeo.com', 'digg.com', 'qq.com', 'stumbleupon.com', 'baidu.com', 'addthis.com', 'miibeian.gov.cn', 'statcounter.com', 'bit.ly', 'feedburner.com', 'nytimes.com', 'reddit.com', 'delicious.com', 'msn.com', 'macromedia.com', 'bbc.co.uk', 'weebly.com', 'blogger.com', 'icio.us', 'goo.gl', 'gov.uk', 'cnn.com', 'yandex.ru', 'webs.com', 'google.de', 'mail.ru', 'livejournal.com', 'sourceforge.net', 'go.com', 'imdb.com', 'jimdo.com', 'instagram.com', 'free.fr', 'tinyurl.com', 'fc2.com', 'google.co.jp', 'typepad.com', 'joomla.org', 'technorati.com', 't.co', 'networkadvertising.org', 'sina.com.cn', 'creativecommons.org', 'about.com', 'vk.com', 'yahoo.co.jp', 'guardian.co.uk', 'aol.com', 'google.co.uk', 'nih.gov', 'tripod.com', 'hugedomains.com', 'mozilla.org', 'wsj.com', 'ameblo.jp', 'ebay.com', 'huffingtonpost.com', 'europa.eu', 'rambler.ru', '51.la', 'gnu.org', 'theguardian.com', 'bing.com', 'geocities.com', 'taobao.com', 'godaddy.com', 'mapquest.com', 'issuu.com', 'washingtonpost.com', 'photobucket.com', 'slideshare.net', 'reuters.com', 'wix.com', 'clickbank.net', '163.com', 'homestead.com', 'posterous.com', 'forbes.com', 'soundcloud.com', 'cnet.com', 'amazon.co.uk', 'etsy.com', 'usatoday.com', 'intoidc.net', 'dailymotion.com', 'weibo.com', 'archive.org', 'phpbb.com', 'yelp.com', 'telegraph.co.uk', 'constantcontact.com', 'phoca.cz', 'latimes.com', 'php.net', 'rakuten.co.jp', 'amazon.de', 'google.fr', 'ning.com', 'opera.com', 'live.com', 'scribd.com', 'squidoo.com', 'sakura.ne.jp', 'altervista.org', 'sohu.com', 'cdc.gov', 'dailymail.co.uk', 'mit.edu', 'deviantart.com', 'wikimedia.org', 'e-recht24.de', 'google.it', 'parallels.com', 'time.com', 'stanford.edu', 'harvard.edu', 'addtoany.com', 'bbb.org', 'alibaba.com', 'nasa.gov', 'imageshack.us', 'miitbeian.gov.cn', 'npr.org', 'ca.gov', 'gravatar.com', 'wired.com', 'narod.ru', 'blogspot.co.uk', 'hatena.ne.jp', 'histats.com', 'angelfire.com', 'amazon.co.jp', 'nifty.com', 'blog.com', 'over-blog.com', 'bloomberg.com', 'eventbrite.com', 'google.es', 'ocn.ne.jp', 'blinklist.com', 'dedecms.com', 'amazonaws.com', 'google.ca', 'ibm.com', 'prweb.com', 'pbs.org', 'xrea.com', 'nbcnews.com', 'mozilla.com', 'weather.com', 'a8.net', 'noaa.gov', 'foxnews.com', 'cbsnews.com', 'newsvine.com', 'cpanel.net', 'goo.ne.jp', 'businessweek.com', 'comsenz.com', 'berkeley.edu', 'geocities.jp', 'loc.gov', 'discuz.net', 'sfgate.com', 'bluehost.com', 'apache.org', 'bandcamp.com', 'whitehouse.gov', 'seesaa.net', 'usda.gov', 'vkontakte.ru', 'biglobe.ne.jp', 'freewebs.com', 'nationalgeographic.com', 'mashable.com', 'epa.gov', 'icq.com', 'oracle.com', 'boston.com', 'mysql.com', 'ted.com', 'eepurl.com', 'ezinearticles.com', 'examiner.com', 'cornell.edu', 'tripadvisor.com', 'hp.com', 'nps.gov', 'kickstarter.com', 'house.gov', 'techcrunch.com', 'alexa.com', 'mediafire.com', 'ucoz.ru', 'sphinn.com', 'google.nl', 'un.org', 'xinhuanet.com', 'people.com.cn', 'independent.co.uk', 'reverbnation.com', 'irs.gov', 'wunderground.com', 'webnode.com', 'ustream.tv', 'who.int', 'squarespace.com', 'opensource.org', 'last.fm', 'senate.gov', 'oaic.gov.au', 'drupal.org', 'bizjournals.com', 'webstarts.com', 'topsy.com', 'privacy.gov.au', 'gmpg.org', 'spiegel.de', 'mac.com', 'disqus.com', 'skype.com', 'redcross.org', 'moonfruit.com', 'cbslocal.com', 'cbc.ca', 'jugem.jp', 'umich.edu', '1688.com', 'discovery.com', 'nature.com', 'ycombinator.com', 'wikia.com', 'ifeng.com', 'dropbox.com', 'fda.gov', 'google.com.br', 'surveymonkey.com', 'youku.com', 'exblog.jp', 'businessinsider.com', 'webmd.com', 'blogspot.com.es', 'shinystat.com', 'auda.org.au', 'xanga.com', 'github.com', 'paypal.com', 'sitemeter.com', 'ft.com', 'state.gov', 'marketwatch.com', 'netvibes.com', 'netscape.com', 'uol.com.br', 'wiley.com', 'prnewswire.com', 'networksolutions.com', 'cloudflare.com', 'liveinternet.ru', 'ed.gov', 'zdnet.com', 'cafepress.com', 'diigo.com', 'about.me', 'goodreads.com', 'chicagotribune.com', 'ftc.gov', 'soup.io', 'quantcast.com', 'google.pl', 'economist.com', 'google.cn', 'census.gov', 'ehow.com', 'com.com', 'blogspot.de', 'intuit.com', 'pagesperso-orange.fr', 'nydailynews.com', 'blogspot.fr', 'skyrock.com', 'upenn.edu', 'ow.ly', 'google.com.au', 'desdev.cn', 'meetup.com', 'hubpages.com', 'utexas.edu', 'slashdot.org', 'doubleclick.net', 'washington.edu', 'engadget.com', 'cdbaby.com', 'blinkweb.com', 'jigsy.com', 'patch.com', 'ucla.edu', 'theatlantic.com', 'thetimes.co.uk', 'imgur.com', 'abc.net.au', 'columbia.edu', 'bloglines.com', 'devhub.com', 'usgs.gov', 'infoseek.co.jp', 'marriott.com', 'behance.net', 'yale.edu', 'hc360.com', 'hilton.com', 'so-net.ne.jp', 'plala.or.jp', 'umn.edu', 'flavors.me', 'list-manage.com', 'jiathis.com', 'dion.ne.jp', 'howstuffworks.com', 'hexun.com', 'wikispaces.com', 'is.gd', 'slate.com', 'naver.com', 'g.co', 'elegantthemes.com', 'usa.gov', 'edublogs.org', 'bigcartel.com', 'lycos.com', 'usnews.com', 'psu.edu', 'wisc.edu', 'sun.com', 'yellowbook.com', 'ucoz.com', 'webeden.co.uk', 'state.tx.us', 'nhs.uk', 'cargocollective.com', 'timesonline.co.uk', 'unicef.org', 'salon.com', 'shareasale.com', 'samsung.com', 'theglobeandmail.com', 'xing.com', 'smh.com.au', 'gizmodo.com', 'me.com', 'businesswire.com', 'intel.com', 'purevolume.com', 'paginegialle.it', 'cocolog-nifty.com', 'example.com', 'artisteer.com', 'biblegateway.com', 'answers.com', 'cmu.edu', 'ask.com', 'unesco.org', 'blogspot.in', 'reference.com', 'booking.com', 'altavista.com', 'prlog.org', 'de.vu', 'sciencedaily.com', 'i2i.jp', 'google.ru', 'multiply.com', 'dmoz.org', 'dagondesign.com', 'blogs.com', 'smugmug.com', 'canalblog.com', 'deliciousdays.com', 'blogspot.com.br', 'craigslist.org', 'istockphoto.com', 'google.com.hk', 'domainmarket.com', 't-online.de', 'jalbum.net', 'cnbc.com', 'mtv.com', 'si.edu', 'zimbio.com', 'twitpic.com', '1und1.de', 'wufoo.com', 'ebay.co.uk', 'furl.net', 'netlog.com', 'symantec.com', 'indiatimes.com', 'nypost.com', 'hhs.gov', 'uiuc.edu', 'princeton.edu', 'comcast.net', 'newyorker.com', 'livedoor.com', 'cisco.com', 'nba.com', 'chron.com', 'admin.ch', 'thedailybeast.com', 'java.com', 'springer.com', '4shared.com', 'vistaprint.com', 'hud.gov', 'storify.com', 'shutterfly.com', 'chronoengine.com', 'mlb.com', 'simplemachines.org', 'dyndns.org', 'sciencedirect.com', 'dell.com', 'wallinside.com', 'virginia.edu', 'bravesites.com', 'tinypic.com', 'csmonitor.com', 'msu.edu', 'dot.gov', 'tuttocitta.it', 'ovh.net', 'fotki.com', 'japanpost.jp', 'tamu.edu', 'aboutads.info', 'accuweather.com', 'earthlink.net', 'printfriendly.com', 'nyu.edu', 'army.mil', 'tripod.co.uk', 'mayoclinic.com', 'omniture.com', 'arizona.edu', 'lulu.com', 'ucsd.edu', 'rediff.com', 'odnoklassniki.ru', 'china.com.cn', 'elpais.com', 'hostmonster.com', 'unblog.fr', 'real.com', 'toplist.cz', 'fastcompany.com', 'studiopress.com', 'ox.ac.uk', 'vinaora.com', 'unc.edu', 'jevents.net', 'cyberchimps.com', 'purdue.edu', 'suntimes.com', 'mapy.cz', 'shop-pro.jp', 'yellowpages.com', 'webnode.fr', 'seattletimes.com', 'blogtalkradio.com', 'cba.pl', 'beep.com', 'nsw.gov.au', 'scientificamerican.com', 'va.gov', 'arstechnica.com', 'mixx.com', 'cam.ac.uk', 'fema.gov', 'oakley.com', 'chinadaily.com.cn', 'uchicago.edu']
	domain = get_domain(url)
	return domain in MOZ_TOP
	
def get(url):
	br = Browser()
	return br.get(url);
	
def get_page_as_browser(url, options={'convert_utf8':True}):
	buffer = StringIO()

	curl = pycurl.Curl()

	url = url_to_pynicode(url) 
	
	curl.setopt(pycurl.URL, str(url))
	curl.setopt(pycurl.FOLLOWLOCATION, 1)
	curl.setopt(pycurl.MAXREDIRS, 2)
	curl.setopt(pycurl.ENCODING, "gzip")
	curl.setopt(pycurl.RANGE, "0-125000") 
	curl.setopt(pycurl.USERAGENT, "Mozilla")

	if 'referer' in options:
		curl.setopt(pycurl.REFERER, options['referer'])
	
	
	if 'timeout' not in options:
		curl.setopt(pycurl.TIMEOUT, 15)
	else:
		curl.setopt(pycurl.TIMEOUT, options['timeout'])
	
	curl.setopt(pycurl.CONNECTTIMEOUT, 5);
	
	if ('convert_utf8' in options and options['convert_utf8']==True) or ('need_headers' in options and options['need_headers']==True):
		curl.setopt(pycurl.HEADER, 1)
	else:
		curl.setopt(pycurl.HEADER, 0)

	if 'post' in options and options['post']!='':
		curl.setopt(pycurl.POST,1)
		curl.setopt(pycurl.POSTFIELDS, options['post'])
	
	curl.setopt(pycurl.SSL_VERIFYPEER, 0)
	curl.setopt(pycurl.SSL_VERIFYHOST, 0)
	curl.setopt(pycurl.NOSIGNAL, 1)
	curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
	
	effective_url = 'undefined'

	try:
		curl.perform()
		buffer = buffer.getvalue()
		status = True
		effective_url = curl.getinfo(pycurl.EFFECTIVE_URL)
		if delete_www(get_host(url))!=delete_www(get_host(effective_url)): buffer = ''
		if 'convert_utf8' in options and options['convert_utf8']==True:
			buffer = __convert_page_encoding(buffer, ('need_headers' in options and options['need_headers']==True))
	except:
		buffer = 'Error'
		status = False
		pass

	curl.close()
	return [status, buffer, effective_url]

def __convert_page_encoding(s, is_header = False, header = False):
	
	enclist = {'win-1251':'windows-1251', 'windows-1251':'windows-1251', 'cp-1251':'windows-1251', 'cp1251':'windows-1251', 'utf8':'utf-8', 'utf-8':'utf-8', 'koi8':'koi8-r', 'koi-8':'koi8-r', 'koi8-r':'koi8-r'}
	enc = ''

	

	s = re.sub('<!--\s*([/]?)noindex\s*-->(?is)', '<\\1noindex>', s)
	s = re.sub('<!--.*?-->(?is)', ' ', s);
	s = s.replace("\r\n", "\n")
	
	h = header

	if is_header:
		start = s.lower().find('200 ok')
		if start<0:
			start = 0
		s = s[start:]
		h = s.split("\n\n", 1)
	
		if len(h)>1: 
			s = h[1] 
			h = h[0]
		else:
			h = ''
	
	if h:
		# detecting encoding by header
		if enc=='':
			m = re.search("content-type:[^\n]+charset=([^\n\s]+)(?is)", h)
			if m:
				h = m.group(1).strip('"\'<> ').lower()
				if enclist.has_key(h):
					enc = enclist[h]
	
	
	# detecting encoding by meta
	if enc=='':
		m = re.search("<meta[^>]+http-equiv=[\"']?Content-type[\"']?[ \t\n]+content=[\"']?([^;>\"']+);[ \t\n]*charset=([^\"'>]+)[\"']?[ \t\n]*/?>(?is)", s)
		if m:
			h = m.group(2).strip('"\'<> ').lower()
			if enclist.has_key(h):
				enc = enclist[h]	

	
	if enc=='':
		
		m = re.search("<meta[^>]+content=[\"']?([^;]+);[^>]*charset=([^\"']+)[\"']?[^>]+http-equiv=[\"']?Content-type[\"']?[^>]*>(?is)", s)
		if m:
			h = m.group(2).strip('"\'<> ').lower()
			if enclist.has_key(h):
				enc = enclist[h]		
	
	
	# detecting encoding by xml prolog
	if enc=='':
		m = re.search("<\?xml[^>]+encoding=[\"']?([^\s>'\"]+)[\"']?[^>]*>(?is)", s)
		if m:
			h = m.group(1).strip('"\'<> ').lower()
			if enclist.has_key(h):
				enc = enclist[h]	
	
	# autodetecting
	if enc=='':
		enc = __charset_auto_detect(s)		
	
		
	# converting
	if enc=='':
		enc = 'utf-8'
		try:
			tmp = s.decode(enc)
			s = tmp
		except:
			enc = 'windows-1251'
			try:
				tmp = s.decode(enc)
				s = tmp
			except:
				enc = 'koi8-r'
				try:
					tmp = s.decode(enc)
					s = tmp

				except:
					pass
	else:
		s = s.decode(enc, 'replace')

	# УДАЛЯЕМ мета теги указывающие на кодировку. LXML глючить может из за них
	# Similarly, you will get errors when you try the same with HTML data in a unicode string that specifies a charset in a meta tag of the header. 
	# You should generally avoid converting XML/HTML data to unicode before passing it into the parsers. 
	# It is both slower and error prone.(http://lxml.de/parsing.html)
	s = re.sub("<meta[^>]+charset[^>]+>(?is)", '', s)
	s = re.sub("<\?xml[^>]+encoding=[\"']?([^\s>'\"]+)[\"']?[^>]*>(?is)", '', s)
	
	return s

convert_page_encoding = __convert_page_encoding

def strip_tags(value):
	return re.sub('<[^>]*?>(?is)', '', value)

def __charset_auto_detect(s):
	counters = {'windows-1251':0, 'koi8-r':0}
	patterns = {193:'koi8-r', 201:'koi8-r', 207:'koi8-r', 212:'koi8-r', 225:'koi8-r', 233:'koi8-r', 239:'koi8-r', 244:'koi8-r', 192:'windows-1251', 200:'windows-1251', 206:'windows-1251', 210:'windows-1251', 224:'windows-1251', 232:'windows-1251', 238:'windows-1251', 242:'windows-1251'}
	try:
		s = s.decode('utf-8')
		enc = 'utf-8'
	except:
		s = strip_tags(s)
		for x in s:
			char = ord(x)
			if (char<128) or (char>256): continue;
			if patterns.has_key(char):
				counters[patterns[char]] = counters[patterns[char]] + 1
		counters = dict(map(lambda item: (item[1],item[0]),counters.items()))		
		enc = counters[max(counters.keys())];
	return enc

resourceRegister('whois')
@resource_function('whois')
def whois(domain):
	return seo.whois.whois(domain)

def strtotime(s, format = "%Y-%m-%d"):
	return int(time.mktime(time.strptime(str(s), str(format))))

def domain_expiration_date(domain):
	return seo.whois.date_to_unixformat(domain_date(domain, 'expiration_date'))

def domain_reg_date(domain):
	return seo.whois.date_to_unixformat(domain_date(domain, 'creation_date'))

	

class DomainDateError(SeoException):
	pass

def domain_date(domain, typedate):

	wh = whois(domain)
	
	if typedate=='creation_date':
		try:
			rd = wh.creation_date
		except:
			raise DomainDateError("No creation_date for "+str(domain)+'.')
	elif typedate=='expiration_date':
		try:
			rd = wh.expiration_date
		except:
			raise DomainDateError("No expiration_date for "+str(domain)+'.')
	else:
		rd = []
	
	if len(rd)>0: 
		return rd[0]

	raise DomainDateError("Can't define "+str(typedate)+" for "+str(domain)+'. No WHOIS.')	

def domain_level(domain):
	return len(domain.split('.'))

def is_mord(url):
	url = delete_http(delete_www(url)).lower()
	domain = get_host(url)
	
	if domain!='':
		url = url.split(domain)
		if (len(url)==2 and (url[1]=='' or url[1]=='/')) or len(url)==1:
			return True
	return False

def define_need_pagetype(top, self_url):
	"""
	main_page - Надо установить морду
	inner_page - Надо установить внутряк
	None - Все и так ОК
	"""
	cnt_mords = 0
	cnt_inner = 0
	for url in top:
		if is_mord(url):
			cnt_mords += 1
		else:
			cnt_inner += 1

	self_mord = is_mord(self_url)
	bad_cnt = cnt_inner if self_mord else cnt_mords
	bad_prc = round(float(bad_cnt)/float(len(top)), 2) if len(top)>0 else 0
	print "Count of not suit pages: %s" % bad_cnt
	print "Percent of not suit pages: %s" % bad_prc

	if bad_prc>0.9:
		return 'main_page' if not self_mord else 'inner_page'
	return None

def toUnicode(keyword):
	if type(keyword).__name__!='unicode':
		keyword = unicode(keyword, 'utf-8')
	return keyword
def prepareKeyword(keyword):
	keyword = toUnicode(keyword)
	keyword = keyword.lower().strip().replace('\t', ' ')
	#.replace('-', ' ').replace('&quot;', '').replace('!', ' ').replace('?', ' ').replace('+', ' ')
	keyword = re.sub('[\s\xa0]+(?is)', ' ', keyword).strip()
	return keyword
def prepareToFreq(keyword, forExact=True):
	keyword = toUnicode(keyword)
	#keyword = re.sub(u'[^'+unicode('а-яА-ЯёЁЄЇІієї', 'utf-8')+'a-zA-Z0-9-+!\s ](?isu)', ' ', keyword)
	keyword = re.sub(u'[^\w\s\$\^ ](?isu)', ' ', keyword)
	keyword = re.sub('[\s\xa0]+(?is)', ' ', keyword).strip()
	if forExact==True:
		keyword = keyword.split(' ')
		keyword = '"!'+' !'.join(keyword).strip()+'"'
	return keyword

def notForFreq(keyword):
	keyword = toUnicode(keyword)
	keyword = re.sub(u'['+unicode('а-яА-ЯёЁЄЇІієї', 'utf-8')+'a-zA-Z0-9-+!\s ](?isu)', '', keyword).strip()
	if keyword=='':
		return False
	else:
		return True



def check_mirror(domain):
	br = Browser()

	all_effective_hosts = set()
	for url in [domain, 'www.%s' % domain]:
		print "=== Check %s ===" % url
		br.get(url)
		eff_url = url_from_pynicode(br.effective_url)
		print 'effective_url is %s' % eff_url
		host = seo.network.get_host(eff_url)
		print 'effective host is %s' % host
		all_effective_hosts.add(host)
	
	print "all_effective_hosts is %s" % all_effective_hosts
	if len(set(all_effective_hosts))==2:
		main_mirror = 'both'
	else:
		main_mirror = 'with_www' if list(all_effective_hosts)[0].startswith('www.') else 'without_www'	

	return main_mirror