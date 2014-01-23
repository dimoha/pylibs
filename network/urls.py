# -*- coding: utf-8 -*-
import re,  time, urllib, urlparse
from network import NetworkException

class UrlsException(NetworkException):
	pass

class PynicodeConvertException(UrlsException):
	pass

class BadDomainNetworkException(UrlsException):
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


def url_to_pynicode(url, is_iri_to_uri=False):
	h = delete_www(get_host(url))
	
	if type(h).__name__!='unicode':
		h = unicode(h, 'utf-8')
	
	hp = str(h.encode("idna")) 
	prepared = url.replace(h, hp, 1)
	if is_iri_to_uri:
		prepared = iri_to_uri(prepared)

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
		raise UrlsException('Unknown URL-format: "'+str(url)+'".')
	return domain_url.lower().strip(), (page_url[0]+page_url[2]).strip()

def is_social_site(url):
	MOZ_TOP = ['facebook.com', 'twitter.com', 'google.com', 'youtube.com', 'wordpress.org', 'adobe.com', 'blogspot.com', 'wikipedia.org', 'wordpress.com', 'linkedin.com', 'yahoo.com', 'amazon.com', 'flickr.com', 'w3.org', 'pinterest.com', 'apple.com', 'tumblr.com', 'myspace.com', 'microsoft.com', 'vimeo.com', 'digg.com', 'qq.com', 'stumbleupon.com', 'baidu.com', 'addthis.com', 'miibeian.gov.cn', 'statcounter.com', 'bit.ly', 'feedburner.com', 'nytimes.com', 'reddit.com', 'delicious.com', 'msn.com', 'macromedia.com', 'bbc.co.uk', 'weebly.com', 'blogger.com', 'icio.us', 'goo.gl', 'gov.uk', 'cnn.com', 'yandex.ru', 'webs.com', 'google.de', 'mail.ru', 'livejournal.com', 'sourceforge.net', 'go.com', 'imdb.com', 'jimdo.com', 'instagram.com', 'free.fr', 'tinyurl.com', 'fc2.com', 'google.co.jp', 'typepad.com', 'joomla.org', 'technorati.com', 't.co', 'networkadvertising.org', 'sina.com.cn', 'creativecommons.org', 'about.com', 'vk.com', 'yahoo.co.jp', 'guardian.co.uk', 'aol.com', 'google.co.uk', 'nih.gov', 'tripod.com', 'hugedomains.com', 'mozilla.org', 'wsj.com', 'ameblo.jp', 'ebay.com', 'huffingtonpost.com', 'europa.eu', 'rambler.ru', '51.la', 'gnu.org', 'theguardian.com', 'bing.com', 'geocities.com', 'taobao.com', 'godaddy.com', 'mapquest.com', 'issuu.com', 'washingtonpost.com', 'photobucket.com', 'slideshare.net', 'reuters.com', 'wix.com', 'clickbank.net', '163.com', 'homestead.com', 'posterous.com', 'forbes.com', 'soundcloud.com', 'cnet.com', 'amazon.co.uk', 'etsy.com', 'usatoday.com', 'intoidc.net', 'dailymotion.com', 'weibo.com', 'archive.org', 'phpbb.com', 'yelp.com', 'telegraph.co.uk', 'constantcontact.com', 'phoca.cz', 'latimes.com', 'php.net', 'rakuten.co.jp', 'amazon.de', 'google.fr', 'ning.com', 'opera.com', 'live.com', 'scribd.com', 'squidoo.com', 'sakura.ne.jp', 'altervista.org', 'sohu.com', 'cdc.gov', 'dailymail.co.uk', 'mit.edu', 'deviantart.com', 'wikimedia.org', 'e-recht24.de', 'google.it', 'parallels.com', 'time.com', 'stanford.edu', 'harvard.edu', 'addtoany.com', 'bbb.org', 'alibaba.com', 'nasa.gov', 'imageshack.us', 'miitbeian.gov.cn', 'npr.org', 'ca.gov', 'gravatar.com', 'wired.com', 'narod.ru', 'blogspot.co.uk', 'hatena.ne.jp', 'histats.com', 'angelfire.com', 'amazon.co.jp', 'nifty.com', 'blog.com', 'over-blog.com', 'bloomberg.com', 'eventbrite.com', 'google.es', 'ocn.ne.jp', 'blinklist.com', 'dedecms.com', 'amazonaws.com', 'google.ca', 'ibm.com', 'prweb.com', 'pbs.org', 'xrea.com', 'nbcnews.com', 'mozilla.com', 'weather.com', 'a8.net', 'noaa.gov', 'foxnews.com', 'cbsnews.com', 'newsvine.com', 'cpanel.net', 'goo.ne.jp', 'businessweek.com', 'comsenz.com', 'berkeley.edu', 'geocities.jp', 'loc.gov', 'discuz.net', 'sfgate.com', 'bluehost.com', 'apache.org', 'bandcamp.com', 'whitehouse.gov', 'seesaa.net', 'usda.gov', 'vkontakte.ru', 'biglobe.ne.jp', 'freewebs.com', 'nationalgeographic.com', 'mashable.com', 'epa.gov', 'icq.com', 'oracle.com', 'boston.com', 'mysql.com', 'ted.com', 'eepurl.com', 'ezinearticles.com', 'examiner.com', 'cornell.edu', 'tripadvisor.com', 'hp.com', 'nps.gov', 'kickstarter.com', 'house.gov', 'techcrunch.com', 'alexa.com', 'mediafire.com', 'ucoz.ru', 'sphinn.com', 'google.nl', 'un.org', 'xinhuanet.com', 'people.com.cn', 'independent.co.uk', 'reverbnation.com', 'irs.gov', 'wunderground.com', 'webnode.com', 'ustream.tv', 'who.int', 'squarespace.com', 'opensource.org', 'last.fm', 'senate.gov', 'oaic.gov.au', 'drupal.org', 'bizjournals.com', 'webstarts.com', 'topsy.com', 'privacy.gov.au', 'gmpg.org', 'spiegel.de', 'mac.com', 'disqus.com', 'skype.com', 'redcross.org', 'moonfruit.com', 'cbslocal.com', 'cbc.ca', 'jugem.jp', 'umich.edu', '1688.com', 'discovery.com', 'nature.com', 'ycombinator.com', 'wikia.com', 'ifeng.com', 'dropbox.com', 'fda.gov', 'google.com.br', 'surveymonkey.com', 'youku.com', 'exblog.jp', 'businessinsider.com', 'webmd.com', 'blogspot.com.es', 'shinystat.com', 'auda.org.au', 'xanga.com', 'github.com', 'paypal.com', 'sitemeter.com', 'ft.com', 'state.gov', 'marketwatch.com', 'netvibes.com', 'netscape.com', 'uol.com.br', 'wiley.com', 'prnewswire.com', 'networksolutions.com', 'cloudflare.com', 'liveinternet.ru', 'ed.gov', 'zdnet.com', 'cafepress.com', 'diigo.com', 'about.me', 'goodreads.com', 'chicagotribune.com', 'ftc.gov', 'soup.io', 'quantcast.com', 'google.pl', 'economist.com', 'google.cn', 'census.gov', 'ehow.com', 'com.com', 'blogspot.de', 'intuit.com', 'pagesperso-orange.fr', 'nydailynews.com', 'blogspot.fr', 'skyrock.com', 'upenn.edu', 'ow.ly', 'google.com.au', 'desdev.cn', 'meetup.com', 'hubpages.com', 'utexas.edu', 'slashdot.org', 'doubleclick.net', 'washington.edu', 'engadget.com', 'cdbaby.com', 'blinkweb.com', 'jigsy.com', 'patch.com', 'ucla.edu', 'theatlantic.com', 'thetimes.co.uk', 'imgur.com', 'abc.net.au', 'columbia.edu', 'bloglines.com', 'devhub.com', 'usgs.gov', 'infoseek.co.jp', 'marriott.com', 'behance.net', 'yale.edu', 'hc360.com', 'hilton.com', 'so-net.ne.jp', 'plala.or.jp', 'umn.edu', 'flavors.me', 'list-manage.com', 'jiathis.com', 'dion.ne.jp', 'howstuffworks.com', 'hexun.com', 'wikispaces.com', 'is.gd', 'slate.com', 'naver.com', 'g.co', 'elegantthemes.com', 'usa.gov', 'edublogs.org', 'bigcartel.com', 'lycos.com', 'usnews.com', 'psu.edu', 'wisc.edu', 'sun.com', 'yellowbook.com', 'ucoz.com', 'webeden.co.uk', 'state.tx.us', 'nhs.uk', 'cargocollective.com', 'timesonline.co.uk', 'unicef.org', 'salon.com', 'shareasale.com', 'samsung.com', 'theglobeandmail.com', 'xing.com', 'smh.com.au', 'gizmodo.com', 'me.com', 'businesswire.com', 'intel.com', 'purevolume.com', 'paginegialle.it', 'cocolog-nifty.com', 'example.com', 'artisteer.com', 'biblegateway.com', 'answers.com', 'cmu.edu', 'ask.com', 'unesco.org', 'blogspot.in', 'reference.com', 'booking.com', 'altavista.com', 'prlog.org', 'de.vu', 'sciencedaily.com', 'i2i.jp', 'google.ru', 'multiply.com', 'dmoz.org', 'dagondesign.com', 'blogs.com', 'smugmug.com', 'canalblog.com', 'deliciousdays.com', 'blogspot.com.br', 'craigslist.org', 'istockphoto.com', 'google.com.hk', 'domainmarket.com', 't-online.de', 'jalbum.net', 'cnbc.com', 'mtv.com', 'si.edu', 'zimbio.com', 'twitpic.com', '1und1.de', 'wufoo.com', 'ebay.co.uk', 'furl.net', 'netlog.com', 'symantec.com', 'indiatimes.com', 'nypost.com', 'hhs.gov', 'uiuc.edu', 'princeton.edu', 'comcast.net', 'newyorker.com', 'livedoor.com', 'cisco.com', 'nba.com', 'chron.com', 'admin.ch', 'thedailybeast.com', 'java.com', 'springer.com', '4shared.com', 'vistaprint.com', 'hud.gov', 'storify.com', 'shutterfly.com', 'chronoengine.com', 'mlb.com', 'simplemachines.org', 'dyndns.org', 'sciencedirect.com', 'dell.com', 'wallinside.com', 'virginia.edu', 'bravesites.com', 'tinypic.com', 'csmonitor.com', 'msu.edu', 'dot.gov', 'tuttocitta.it', 'ovh.net', 'fotki.com', 'japanpost.jp', 'tamu.edu', 'aboutads.info', 'accuweather.com', 'earthlink.net', 'printfriendly.com', 'nyu.edu', 'army.mil', 'tripod.co.uk', 'mayoclinic.com', 'omniture.com', 'arizona.edu', 'lulu.com', 'ucsd.edu', 'rediff.com', 'odnoklassniki.ru', 'china.com.cn', 'elpais.com', 'hostmonster.com', 'unblog.fr', 'real.com', 'toplist.cz', 'fastcompany.com', 'studiopress.com', 'ox.ac.uk', 'vinaora.com', 'unc.edu', 'jevents.net', 'cyberchimps.com', 'purdue.edu', 'suntimes.com', 'mapy.cz', 'shop-pro.jp', 'yellowpages.com', 'webnode.fr', 'seattletimes.com', 'blogtalkradio.com', 'cba.pl', 'beep.com', 'nsw.gov.au', 'scientificamerican.com', 'va.gov', 'arstechnica.com', 'mixx.com', 'cam.ac.uk', 'fema.gov', 'oakley.com', 'chinadaily.com.cn', 'uchicago.edu']
	domain = get_domain(url)
	return domain in MOZ_TOP
	

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









