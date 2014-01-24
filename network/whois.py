# -*- coding: utf-8 -*-

#####################################################################
# Whois Class, Based on PyWhois (patched by dimoha 31.08.2011)
#####################################################################

import sys, time, re, socket, optparse
from pylibs.network import NetworkException

class WhoIsException(NetworkException):
	pass

class WhoIsUndefinedDateFormatError(WhoIsException):
    pass

class DomainDateError(WhoIsException):
	pass


def domain_expiration_date(domain):
	return domain_date(domain, 'expiration_date')

def domain_reg_date(domain):
	return domain_date(domain, 'creation_date')
	
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







###############################
############ MAIN METHODS
###############################


def whois(url):
   
    # clean domain to expose netloc
    domain, pydomain = extract_domain(url)
   
    # call whois command with domain
    nic_client = NICClient()
    text = nic_client.whois_lookup(None, pydomain, 0)
    try:
    	try:
		print text
	except UnicodeDecodeError:
		print unicode(text, 'windows-1251')	
	except:
		raise

    except Exception as e:
	print e
    	pass
    return WhoisEntry.load(domain, text)

def extract_domain(url):
    """Extract the domain from the given URL

    >>> extract_domain('http://www.google.com.au/tos.html')
    'google.com.au'
    """
   
    suffixes = 'ac', 'ad', 'ae', 'aero', 'af', 'ag', 'ai', 'al', 'am', 'an', 'ao', 'aq', 'ar', 'arpa', 'as', 'asia', 'at', 'au', 'aw', 'ax', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'biz', 'bj', 'bm', 'bn', 'bo', 'br', 'bs', 'bt', 'bv', 'bw', 'by', 'bz', 'ca', 'cat', 'cc', 'cd', 'cf', 'cg', 'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'com', 'coop', 'cr', 'cu', 'cv', 'cx', 'cy', 'cz', 'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'edu', 'ee', 'eg', 'er', 'es', 'et', 'eu', 'fi', 'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf', 'gg', 'gh', 'gi', 'gl', 'gm', 'gn', 'gov', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn', 'hr', 'ht', 'hu', 'id', 'ie', 'il', 'im', 'in', 'info', 'int', 'io', 'iq', 'ir', 'is', 'it', 'je', 'jm', 'jo', 'jobs', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me', 'mg', 'mh', 'mil', 'mk', 'ml', 'mm', 'mn', 'mo', 'mobi', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu', 'mv', 'mw', 'mx', 'my', 'mz', 'na', 'name', 'nc', 'ne', 'net', 'nf', 'ng', 'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om', 'org', 'pa', 'pe', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr', 'pro', 'ps', 'pt', 'pw', 'py', 'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd', 'se', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'st', 'su', 'sv', 'sy', 'sz', 'tc', 'td', 'tel', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to', 'tp', 'tr', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'uk', 'us', 'uy', 'uz', 'va', 'vc', 've', 'vg', 'vi', 'vn', 'vu', 'wf', 'ws', 'xn', 'ye', 'yt', 'za', 'zm', 'zw', 'рф', 'dominic', 'donetsk', 'kiev', 'chernovtsy', 'cv', 'ivano-frankivsk', 'km', 'ks', 'rv', 'uzhgorod', 'zhitomir', 'zt', 'dnepropetrovsk', 'kirovograd', 'dp', 'kherson', 'kr', 'kh', 'kharkiv', 'kharkov', 'lg', 'lugansk', 'sumy', 'zaporizhzhe', 'zp', 'dn', 'pl', 'poltava'
    url = re.sub('^.*://', '', url).split('/')[0].lower()
    domain = []
    for section in url.split('.'):
        if section in suffixes:
            domain.append(section)
        else:
            domain = [section]
    domain = '.'.join(domain).strip()

    if type(domain).__name__!='unicode':
        pydomain = unicode(domain, 'utf-8')
    else:
	pydomain = domain

    pydomain = str(pydomain.encode("idna")) # convert to punicode

    return domain, pydomain



##############################
#### PARSING PART
###############################



# added by dimoha 31.08.2011
class PywhoisUndefinedDomainError(WhoIsException):
    def __init__(self, domain=None):
	if domain is not None:
		self.message = 'No entries found for '+domain
	else:
		self.message = 'No entries found for the selected domain'
    def __str__(self):
	return self.message

def cast_date(date_str, output_format=None):
    """Convert any date string found in WHOIS to a time object.
    """
    date_str = str(date_str).strip()
    
    known_formats = [
        '%d-%b-%Y', 				# 02-jan-2000
        '%Y-%m-%d', 				# 2000-01-02
        '%d-%b-%Y %H:%M:%S %Z',		# 24-Jul-2009 13:20:03 UTC
        '%a %b %d %H:%M:%S %Z %Y',  # Tue Jun 21 23:59:59 GMT 2011
        '%Y-%m-%dT%H:%M:%SZ',       # 2007-01-26T19:10:31Z

	# added several formats by dimoha 31.08.2011
	'%Y.%m.%d', 
	'%d-%b-%Y', 
	'%d-%b-%Y %H:%M:%S UTC', 
	'%d-%b-%Y %H:%M:%S',
	"%d.%m.%Y",
	"%Y%m%d%H%M%S",
	'%Y-%m-%d %H:%M:%S.0',
	'%Y-%m-%d %H:%M:%S',
	'%Y.%m.%d %H:%M:%S',
	'%Y-%b-%d', 
	'%d %b %Y %H:%M', 
	'%d %b %Y', 
	'%Y-%m-%dT%H:%M:%S', 
	'%d/%m/%Y', 
	'%Y/%m/%d', 
	'%Y. %m. %d.', 
	'%d.%m.%Y %H:%M:%S'
    ]   

    for format in known_formats:
        try:
            return time.strptime(date_str.strip(), format)
        except ValueError, e:
            pass # Wrong format, keep trying

    raise WhoIsUndefinedDateFormatError(date_str)




class WhoisEntry(object):
    """Base class for parsing a Whois entries.
    """
    # regular expressions to extract domain data from whois profile
    # child classes will override this
    _regex = {
        'domain_name':      'Domain Name:\s?(.+)',
        'registrar':        'Registrar:\s?(.+)',
        'whois_server':     'Whois Server:\s?(.+)',
        'referral_url':     'Referral URL:\s?(.+)', # http url of whois_server
        'updated_date':     'Updated Date:\s?(.+)',
        'creation_date':    'Creation Date:\s?(.+)',
        'expiration_date':  'Expiration Date:\s?(.+)',
        'name_servers':     'Name Server:\s?(.+)', # list of name servers
        'status':           'Status:\s?(.+)', # list of statuses
        'emails':           '[\w.-]+@[\w.-]+\.[\w]{2,4}', # list of email addresses
    }

    def __init__(self, domain, text, regex=None):
        self.domain = domain
        self.text = text
        if regex is not None:
            self._regex = regex


    def __getattr__(self, attr):
        """The first time an attribute is called it will be calculated here.
        The attribute is then set to be accessed directly by subsequent calls.
        """

        whois_regex = self._regex.get(attr)
        if whois_regex:
            setattr(self, attr, re.findall(whois_regex+'(?i)', self.text))
            ret =  getattr(self, attr)

	    # adde by dimoha 31.08.2011 (all date data returning in %d.%m.%Y format)
	    if '_date' in attr and len(ret)>0:
		ret = [ret[0]]
		for k,date in enumerate(ret):
			if date.strip()!='':
				ret[k] = cast_date(date, "%d.%m.%Y")
	    return ret
        else:
            raise KeyError('Unknown attribute: %s' % attr)

    def __str__(self):
        """Print all whois properties of domain
        """
        return '\n'.join('%s: %s' % (attr, str(getattr(self, attr))) for attr in self.attrs())


    def attrs(self):
        """Return list of attributes that can be extracted for this domain
        """
        return sorted(self._regex.keys())


    @staticmethod
    def load(domain, text):
        """Given whois output in ``text``, return an instance of ``WhoisEntry`` that represents its parsed contents.
        """
        if text.strip() == 'No whois server is known for this kind of object.':
            raise WhoIsException(text)

	zone = domain.split('.')[-1]
	if 'com'==zone:
            return WhoisCom(domain, text)
        elif 'net'==zone or 'tv'==zone:
            return WhoisNet(domain, text)
        elif 'org'==zone or 'info'==zone:
            return WhoisOrg(domain, text)
        elif 'ru'==zone or 'su'==zone or 'рф'==zone:
            return WhoisRuSu(domain, text)
        elif 'name'==zone:
        	return WhoisName(domain, text)
        elif 'us'==zone:
        	return WhoisUs(domain, text)
        elif 'me'==zone:
        	return WhoisMe(domain, text)
        elif 'uk'==zone:
        	return WhoisUk(domain, text)
	elif 'biz'==zone:
		return WhoisBiz(domain, text)
		# метка зоны ua
	elif 'ua'==zone:
		subdom_tp2 = 'dnepropetrovsk', 'dp', 'kirovograd', 'kr', 'pl', 'poltava', 'kiev'
		subdom_tp3 = 'donetsk', 'kh', 'kharkiv', 'kharkov', 'lg', 'lugansk', 'sumy', 'zaporizhzhe', 'zp', 'dn'
		subdom_tp_biz = 'biz'
		Subzone = domain.split('.')[-2]
		if Subzone in subdom_tp2:
			return WhoisUa_template2(domain, text)
		elif Subzone in subdom_tp3:
			return WhoisUa_template3(domain, text)
		elif Subzone in subdom_tp_biz:
			return WhoisUa_template_biz(domain, text)
		else:
			return WhoisUa(domain, text)
	elif 'am'==zone:
        	return WhoisAm(domain, text)
	elif 'kz'==zone:
        	return WhoisKz(domain, text)
	elif 'uz'==zone:
        	return WhoisUz(domain, text)
	elif 'ws'==zone:
        	return WhoisWs(domain, text)
	elif 've'==zone:
        	return WhoisVe(domain, text)
	elif 'tw'==zone or 'nu'==zone:
		return WhoisTw(domain, text)
	elif 'tr'==zone:
		return WhoisTr(domain, text)
	elif 'se'==zone or 'gs'==zone or 'fi'==zone or 'cx'==zone:
		return WhoisSe(domain, text)
	elif 'pl'==zone:
		return WhoisPl(domain, text)
	elif 'no'==zone:
		return WhoisNo(domain, text)
	elif 'ms'==zone:
		return WhoisMs(domain, text)
	elif 'lv'==zone:
		return WhoisLv(domain, text)
	elif 'lu'==zone:
		return WhoisLu(domain, text)
	elif 'lt'==zone:
		return WhoisLt(domain, text)
	elif 'kr'==zone:
		return WhoisKr(domain, text)
	elif 'it'==zone:
		return WhoisIt(domain, text)
	elif 'fr'==zone:
		return WhoisFr(domain, text)
	elif 'ee'==zone or 'cz'==zone:
		return WhoisEe(domain, text)
	elif 'edu'==zone:
		return WhoisEdu(domain, text)
	elif 'dk'==zone:
		return WhoisDk(domain, text)
	elif 'cn'==zone:
		return WhoisCn(domain, text)
	elif 'cc'==zone:
		return WhoisCc(domain, text)
	elif 'ca'==zone:
		return WhoisCa(domain, text)
	elif 'md'==zone:
		return WhoisMd(domain, text)
        else:
            return WhoisEntry(domain, text)

class WhoisMd(WhoisEntry):
    """Whois parser for .ca domains
    """
    regex = {
	'creation_date':	'Created*\s*:\s*(.+)',
	'updated_date':		'DNS update*\s*:\s*(.+)',
	'expiration_date':	'Expiration date*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No match for' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex)

class WhoisCa(WhoisEntry):
    """Whois parser for .ca domains
    """
    regex = {
	'creation_date':	'Creation date*\s*:\s*(.+)',
	'updated_date':		'Updated date*\s*:\s*(.+)',
	'expiration_date':	'Expiry date*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'available' in text.strip() and 'Creation date' not in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex)
class WhoisCc(WhoisEntry):
    """Whois parser for .cc domains
    """

    def __init__(self, domain, text):
        if 'No match for ' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text)

class WhoisCn(WhoisEntry):
    """Whois parser for .cn domains
    """
    regex = {
	'creation_date':	'Registration Date*\s*:\s*(.+)',
	'expiration_date':	'Expiration Date*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'no matching record' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex)

class WhoisDk(WhoisEntry):
    """Whois parser for .fr domains
    """
    regex = {
	'creation_date':	'Registered*\s*:\s*(.+)',
	'expiration_date':	'Expires*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No entries found' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex)

class WhoisEdu(WhoisEntry):
    """Whois parser for .fr domains
    """
    regex = {
	'creation_date':	'Domain record activated*\s*:\s*(.+)',
	'updated_date':		'Domain record last updated*\s*:\s*(.+)',
	'expiration_date':	'Domain expires*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No Match' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex)

class WhoisEe(WhoisEntry):
    """Whois parser for .fr domains
    """
    regex = {
	'creation_date':	'registered*\s*:\s*(.+)',
	'updated_date':		'changed*\s*:\s*(.+)',
	'expiration_date':	'expire*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No entries found' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisFr(WhoisEntry):
    """Whois parser for .fr domains
    """
    regex = {
	'creation_date':	'created*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No entries found in the' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisIt(WhoisEntry):
    """Whois parser for .lv domains
    """
    regex = {
	'creation_date':	'Created*\s*:\s*(.+)',
	'updated_date':		'Last Update*\s*:\s*(.+)',
	'expiration_date':	'Expire Date*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'AVAILABLE' in text.strip() and 'Created' not in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisKr(WhoisEntry):
    """Whois parser for .lv domains
    """
    regex = {
	'creation_date':	'Registered Date*\s*:\s*(.+)',
	'updated_date':		'Last updated Date*\s*:\s*(.+)',
	'expiration_date':	'Expiration Date*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'Above domain name is not registered' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisLt(WhoisEntry):
    """Whois parser for .lv domains
    """
    regex = {
	'creation_date':	'Registered*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'available' in text.strip() and 'Registered' not in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisLu(WhoisEntry):
    """Whois parser for .lv domains
    """
    regex = {
	'creation_date':	'registered*\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No such domain' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisLv(WhoisEntry):
    """Whois parser for .lv domains
    """
    regex = {
	'creation_date':	'Changed*\s*:\s*(.+)\+.*',
	}
    
    def __init__(self, domain, text):
        if 'Status: free' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisMs(WhoisEntry):
    """Whois parser for .ms domains
    """
    regex = {
	'creation_date':                  'Created*\s*:\s*(.+)\s+AST',
	'expiration_date':                'Expires\s*:\s*(.+)\s+AST',
	}
    
    def __init__(self, domain, text):
        if 'Status: Not Registered' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisNo(WhoisEntry):
    """Whois parser for .no domains
    """
    regex = {
	'creation_date':                  'Created*\s*:\s*(.+)',
	'updated_date':                   'Last updated\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No match' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisPl(WhoisEntry):
    """Whois parser for .pl domains
    """
    regex = {
	'creation_date':                  'created*\s*:\s*(.+)',
	'updated_date':                   'last\s+modified\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No information available about domain name' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisSe(WhoisEntry):
    """Whois parser for .se domains
    """
    regex = {
	'creation_date':                  'created*\s*:\s*(.+)',
	'expiration_date':                'expires\s*:\s*(.+)',
	'updated_date':                   'modified\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if '" not found' in text.strip() or 'Status: Not Registered' in text.strip() or 'Domain not found' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisTr(WhoisEntry):
    """Whois parser for .tr domains
    """
    regex = {
	'creation_date':                  'Created on[\.]*\s*:\s*(.+)\s*\.',
	'expiration_date':                'Expires on[\.]*\s*:\s*(.+)\s*\.',
	}
    
    def __init__(self, domain, text):
        if 'No match found for' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisTw(WhoisEntry):
    """Whois parser for .tw domains
    """
    regex = {
	'creation_date':                  'Record created on\s*(.+)\s*[\(\.]',
	'expiration_date':                'Record expires on\s*(.+)[\(\.]',
	}
    
    def __init__(self, domain, text):
        if 'No Found'==text.strip() or 'NO MATCH for domain "' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisVe(WhoisEntry):
    """Whois parser for .ve domains
    """
    regex = {
	'creation_date':                  'Fecha de Creacion\s*:\s*(.+)',
	'expiration_date':                'Fecha de Vencimiento\s*:\s*(.+)',
	'updated_date':                   'Ultima Actualizacion\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No match for' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisWs(WhoisEntry):
    """Whois parser for .ws domains
    """
    regex = {
        'domain_name':                    'Domain Name[\.]*:\s*(.+)',
	'creation_date':                  'Domain Created\s*:\s*(.+)',
        'updated_date':                   'Domain Last Updated:\s*:\s*(.+)',
	'expiration_date':                'Domain Currently Expires\s*:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No match for' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisUz(WhoisEntry):
    """Whois parser for .uz domains
    """

    def __init__(self, domain, text):
        if '", not found in database' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text) 

class WhoisKz(WhoisEntry):
    """Whois parser for .kz domains
    """
    regex = {
        'domain_name':                    'Domain Name[\.]*:\s*(.+)',
	'creation_date':                  'Domain created\s*:\s*([^\(]+)\s+\(',
        'updated_date':                   'Last modified\s*:\s*([^\(]+)\s+\(',
	'expiration_date':                'Domain Expiration Date:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'Nothing found for this query' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisUa(WhoisEntry):
    """Whois parser for .ua domains
    """
    regex = {
        'domain_name':                    'domain:\s*(.+)',
        'name_servers':                   'nserver:\s*(.+)',  # list of name servers
	'creation_date':                  'created:.*-UANIC\s*(.+)', #.*\s+(\d{8,}) 'created:\s*(.+)'  
        'updated_date':                   'changed:.*-UANIC\s*(.+)', #.*\s+(\d{8,})
	'expiration_date':                'status:.*-UNTIL\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'No entries found' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisUa_template2(WhoisEntry):
    """обработка whois по второму шаблону зоны ua"""
    regex = {
	'creation_date':                  "created:\s*([^\+\n]+)", 
	}

    def __init__(self, domain, text):
	err = ['No such domain', 'No entries found', 'No match record found for']
	for k in err:
		if k in text.strip():
		    raise PywhoisUndefinedDomainError(domain)
		else:
		    WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisUa_template3(WhoisEntry):
    """обработка whois по третьему шаблону зоны ua"""
    regex = {
	'creation_date':                  'Record created:\s*(.+)', 
	}

    def __init__(self, domain, text):
	err = ['No such domain', 'No entries found', 'No match record found for']
	for k in err:
		if k in text.strip():
		    raise PywhoisUndefinedDomainError(domain)
		else:
		    WhoisEntry.__init__(self, domain, text, self.regex)

class WhoisUa_template_biz(WhoisEntry):
    """обработка whois по biz шаблону зоны ua"""
    regex = {
	'creation_date':                  'Created On:\s*(.+)', 
	}

    def __init__(self, domain, text):
	err = ['No such domain', 'No entries found', 'No match record found for']
	for k in err:
		if k in text.strip():
		    raise PywhoisUndefinedDomainError(domain)
		else:
		    WhoisEntry.__init__(self, domain, text, self.regex)

class WhoisBiz(WhoisEntry):
    """Whois parser for .biz domains
    """
    regex = {
        'domain_name':                    'Domain Name:\s*(.+)',
    	'domain__id':                     'Domain ID:\s*(.+)',
        'registrar':                      'Sponsoring Registrar:\s*(.+)',
        'registrar_id':                   'Sponsoring Registrar IANA ID:\s*(.+)',
        'registrar_url':                  'Registrar URL \(registration services\):\s*(.+)',        
        'status':                         'Domain Status:\s*(.+)',  # list of statuses
        'registrant_name':                'Registrant Name:\s*(.+)',
        'name_servers':                   'Name Server:\s*(.+)',  # list of name servers
        'created_by_registrar':           'Created by Registrar:\s*(.+)',
        'last_updated_by_registrar':      'Last Updated by Registrar:\s*(.+)',
        'creation_date':                  'Domain Registration Date:\s*(.+)',
        'expiration_date':                'Domain Expiration Date:\s*(.+)',
        'updated_date':                   'Domain Last Updated Date:\s*(.+)',
	}
    
    def __init__(self, domain, text):
        if 'Not found: ' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisOrg(WhoisEntry):
    """Whois parser for .org domains
    """
    regex = {
        'domain_name': 'Domain Name:\s*(.+)',
        'registrar': 'Registrant Name:\s*(.+)',
        'creation_date': 'Created On:\s*(.+)',
        'expiration_date': 'Expiration Date:\s*(.+)',
        'status': 'Status:\s*(.+)',  # list of statuses
        'emails': '[\w.-]+@[\w.-]+\.[\w]{2,4}',  # list of email addresses
	'name_servers': 'Name Server:\s*(.+)',  # list of name servers
    }
    
    def __init__(self, domain, text):
        if text.strip()=='NOT FOUND':
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisAm(WhoisEntry):
    """Whois parser for .am domains
    """
    regex = {
        'domain_name': 'Domain name:\s*(.+)',
        'registrar': 'Registrar:\s*(.+)',
        'creation_date': 'Registered:\s*(.+)',
        'expiration_date': 'Expires:\s*(.+)',
        'status': 'Status:\s*(.+)',  # list of statuses
        'emails': '[\w.-]+@[\w.-]+\.[\w]{2,4}',  # list of email addresses
    }
    
    def __init__(self, domain, text):
        if 'No match' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisCom(WhoisEntry):
    """Whois parser for .com domains
    """
    def __init__(self, domain, text):
        if 'No match for "' in text:
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text) 

class WhoisNet(WhoisEntry):
    """Whois parser for .net domains
    """
    def __init__(self, domain, text):
        if 'No match for "' in text:
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text) 

class WhoisRuSu(WhoisEntry):
    """Whois parser for .ru domains
    """
    regex = {
        'domain_name': 'domain:\s*(.+)',
        'registrar': 'registrar:\s*(.+)',
        'creation_date': 'created:\s*(.+)',
        'expiration_date': 'paid-till:\s*(.+)',
        'name_servers': 'nserver:\s*(.+)',		# list of name servers
        'status': 'state:\s*(.+)',			# list of statuses
        'emails': '[\w.-]+@[\w.-]+\.[\w]{2,4}',		# list of email addresses
    }

    def __init__(self, domain, text):
       
	if 'No entries found' in text.strip():
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex)

class WhoisName(WhoisEntry):
    """Whois parser for .name domains
    """
    regex = {
    	'domain_name_id':  'Domain Name ID:\s*(.+)',
        'domain_name':     'Domain Name:\s*(.+)',
        'registrar_id':    'Sponsoring Registrar ID:\s*(.+)',
        'registrar':       'Sponsoring Registrar:\s*(.+)',
        'registrant_id':   'Registrant ID:\s*(.+)',
        'admin_id':        'Admin ID:\s*(.+)',
        'technical_id':    'Tech ID:\s*(.+)',
        'billing_id':      'Billing ID:\s*(.+)',
        'creation_date':   'Created On:\s*(.+)',
        'expiration_date': 'Expires On:\s*(.+)',
        'updated_date':    'Updated On:\s*(.+)',
        'name_server_ids': 'Name Server ID:\s*(.+)',  # list of name server ids
        'name_servers':    'Name Server:\s*(.+)',  # list of name servers
        'status':          'Domain Status:\s*(.+)',  # list of statuses
	}
    def __init__(self, domain, text):
        if 'No match.' in text:
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 
            
class WhoisUs(WhoisEntry):
    """Whois parser for .us domains
    """
    regex = {
        'domain_name':                    'Domain Name:\s*(.+)',
    	'domain__id':                     'Domain ID:\s*(.+)',
        'registrar':                      'Sponsoring Registrar:\s*(.+)',
        'registrar_id':                   'Sponsoring Registrar IANA ID:\s*(.+)',
        'registrar_url':                  'Registrar URL \(registration services\):\s*(.+)',        
        'status':                         'Domain Status:\s*(.+)',  # list of statuses
        'registrant_id':                  'Registrant ID:\s*(.+)',
        'registrant_name':                'Registrant Name:\s*(.+)',
        'registrant_address1':            'Registrant Address1:\s*(.+)',
        'registrant_address2':            'Registrant Address2:\s*(.+)',
        'registrant_city':                'Registrant City:\s*(.+)',
        'registrant_state_province':      'Registrant State/Province:\s*(.+)',
        'registrant_postal_code':         'Registrant Postal Code:\s*(.+)',
        'registrant_country':             'Registrant Country:\s*(.+)',
        'registrant_country_code':        'Registrant Country Code:\s*(.+)',
        'registrant_phone_number':        'Registrant Phone Number:\s*(.+)',
        'registrant_email':               'Registrant Email:\s*(.+)',
        'registrant_application_purpose': 'Registrant Application Purpose:\s*(.+)',
        'registrant_nexus_category':      'Registrant Nexus Category:\s*(.+)',
        'admin_id':                       'Administrative Contact ID:\s*(.+)',
        'admin_name':                     'Administrative Contact Name:\s*(.+)',
        'admin_address1':                 'Administrative Contact Address1:\s*(.+)',
        'admin_address2':                 'Administrative Contact Address2:\s*(.+)',
        'admin_city':                     'Administrative Contact City:\s*(.+)',
        'admin_state_province':           'Administrative Contact State/Province:\s*(.+)',
        'admin_postal_code':              'Administrative Contact Postal Code:\s*(.+)',
        'admin_country':                  'Administrative Contact Country:\s*(.+)',
        'admin_country_code':             'Administrative Contact Country Code:\s*(.+)',
        'admin_phone_number':             'Administrative Contact Phone Number:\s*(.+)',
        'admin_email':                    'Administrative Contact Email:\s*(.+)',
        'admin_application_purpose':      'Administrative Application Purpose:\s*(.+)',
        'admin_nexus_category':           'Administrative Nexus Category:\s*(.+)',
        'billing_id':                     'Billing Contact ID:\s*(.+)',
        'billing_name':                   'Billing Contact Name:\s*(.+)',
        'billing_address1':               'Billing Contact Address1:\s*(.+)',
        'billing_address2':               'Billing Contact Address2:\s*(.+)',
        'billing_city':                   'Billing Contact City:\s*(.+)',
        'billing_state_province':         'Billing Contact State/Province:\s*(.+)',
        'billing_postal_code':            'Billing Contact Postal Code:\s*(.+)',
        'billing_country':                'Billing Contact Country:\s*(.+)',
        'billing_country_code':           'Billing Contact Country Code:\s*(.+)',
        'billing_phone_number':           'Billing Contact Phone Number:\s*(.+)',
        'billing_email':                  'Billing Contact Email:\s*(.+)',
        'billing_application_purpose':    'Billing Application Purpose:\s*(.+)',
        'billing_nexus_category':         'Billing Nexus Category:\s*(.+)',
        'tech_id':                        'Technical Contact ID:\s*(.+)',
        'tech_name':                      'Technical Contact Name:\s*(.+)',
        'tech_address1':                  'Technical Contact Address1:\s*(.+)',
        'tech_address2':                  'Technical Contact Address2:\s*(.+)',
        'tech_city':                      'Technical Contact City:\s*(.+)',
        'tech_state_province':            'Technical Contact State/Province:\s*(.+)',
        'tech_postal_code':               'Technical Contact Postal Code:\s*(.+)',
        'tech_country':                   'Technical Contact Country:\s*(.+)',
        'tech_country_code':              'Technical Contact Country Code:\s*(.+)',
        'tech_phone_number':              'Technical Contact Phone Number:\s*(.+)',
        'tech_email':                     'Technical Contact Email:\s*(.+)',
        'tech_application_purpose':       'Technical Application Purpose:\s*(.+)',
        'tech_nexus_category':            'Technical Nexus Category:\s*(.+)',
        'name_servers':                   'Name Server:\s*(.+)',  # list of name servers
        'created_by_registrar':           'Created by Registrar:\s*(.+)',
        'last_updated_by_registrar':      'Last Updated by Registrar:\s*(.+)',
        'creation_date':                  'Domain Registration Date:\s*(.+)',
        'expiration_date':                'Domain Expiration Date:\s*(.+)',
        'updated_date':                   'Domain Last Updated Date:\s*(.+)',
	}
    def __init__(self, domain, text):
        if 'Not found:' in text:
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex)
            
class WhoisMe(WhoisEntry):
    """Whois parser for .me domains
    """
    regex = {
    	'domain_id':                   'Domain ID:(.+)',
        'domain_name':                 'Domain Name:(.+)',
        'creation_date':               'Domain Create Date:(.+)',
        'updated_date':                'Domain Last Updated Date:(.+)',
        'expiration_date':             'Domain Expiration Date:(.+)',
        'transfer_date':               'Last Transferred Date:(.+)',
        'trademark_name':              'Trademark Name:(.+)',
        'trademark_country':           'Trademark Country:(.+)',
        'trademark_number':            'Trademark Number:(.+)',
        'trademark_application_date':  'Date Trademark Applied For:(.+)',
        'trademark_registration_date': 'Date Trademark Registered:(.+)',
        'registrar':                   'Sponsoring Registrar:(.+)',
        'created_by':                  'Created by:(.+)',
        'updated_by':                  'Last Updated by Registrar:(.+)',
        'status':                      'Domain Status:(.+)',  # list of statuses
        'registrant_id':               'Registrant ID:(.+)',
        'registrant_name':             'Registrant Name:(.+)',
        'registrant_org':              'Registrant Organization:(.+)',
        'registrant_address':          'Registrant Address:(.+)',
        'registrant_address2':         'Registrant Address2:(.+)',
        'registrant_address3':         'Registrant Address3:(.+)',
        'registrant_city':             'Registrant City:(.+)',
        'registrant_state_province':   'Registrant State/Province:(.+)',
        'registrant_country':          'Registrant Country/Economy:(.+)',
        'registrant_postal_code':      'Registrant Postal Code:(.+)',
        'registrant_phone':            'Registrant Phone:(.+)',
        'registrant_phone_ext':        'Registrant Phone Ext\.:(.+)',
        'registrant_fax':              'Registrant FAX:(.+)',
        'registrant_fax_ext':          'Registrant FAX Ext\.:(.+)',
        'registrant_email':            'Registrant E-mail:(.+)',
        'admin_id':                    'Admin ID:(.+)',
        'admin_name':                  'Admin Name:(.+)',
        'admin_org':                   'Admin Organization:(.+)',
        'admin_address':               'Admin Address:(.+)',
        'admin_address2':              'Admin Address2:(.+)',
        'admin_address3':              'Admin Address3:(.+)',
        'admin_city':                  'Admin City:(.+)',
        'admin_state_province':        'Admin State/Province:(.+)',
        'admin_country':               'Admin Country/Economy:(.+)',
        'admin_postal_code':           'Admin Postal Code:(.+)',
        'admin_phone':                 'Admin Phone:(.+)',
        'admin_phone_ext':             'Admin Phone Ext\.:(.+)',
        'admin_fax':                   'Admin FAX:(.+)',
        'admin_fax_ext':               'Admin FAX Ext\.:(.+)',
        'admin_email':                 'Admin E-mail:(.+)',
        'tech_id':                     'Tech ID:(.+)',
        'tech_name':                   'Tech Name:(.+)',
        'tech_org':                    'Tech Organization:(.+)',
        'tech_address':                'Tech Address:(.+)',
        'tech_address2':               'Tech Address2:(.+)',
        'tech_address3':               'Tech Address3:(.+)',
        'tech_city':                   'Tech City:(.+)',
        'tech_state_province':         'Tech State/Province:(.+)',
        'tech_country':                'Tech Country/Economy:(.+)',
        'tech_postal_code':            'Tech Postal Code:(.+)',
        'tech_phone':                  'Tech Phone:(.+)',
        'tech_phone_ext':              'Tech Phone Ext\.:(.+)',
        'tech_fax':                    'Tech FAX:(.+)',
        'tech_fax_ext':                'Tech FAX Ext\.:(.+)',
        'tech_email':                  'Tech E-mail:(.+)',
        'name_servers':                'Nameservers:(.+)',  # list of name servers
	}
    def __init__(self, domain, text):
        if 'NOT FOUND' in text:
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex) 

class WhoisUk(WhoisEntry):
    """Whois parser for .uk domains
    """
    regex = {
        'domain_name':                    'Domain name:\n\s*(.+)',
        'registrar':                      'Registrar:\n\s*(.+)',
        'registrar_url':                  'URL:\s*(.+)',
        'status':                         'Registration status:\n\s*(.+)',  # list of statuses
        'registrant_name':                'Registrant:\n\s*(.+)',
        'creation_date':                  'Registered on:\s*(.+)',
        'expiration_date':                'Renewal date:\s*(.+)',
        'updated_date':                   'Last updated:\s*(.+)',
	}
    def __init__(self, domain, text):
        if 'Not found:' in text or 'No match for' in text:
            raise PywhoisUndefinedDomainError(domain)
        else:
            WhoisEntry.__init__(self, domain, text, self.regex)


###############################################
######### GET WHOIS PART
###############################################

class NICClient(object) :

    ABUSEHOST           = "whois.abuse.net"
    NICHOST             = "whois.crsnic.net"
    INICHOST            = "whois.networksolutions.com"
    DNICHOST            = "whois.nic.mil"
    GNICHOST            = "whois.nic.gov"
    ANICHOST            = "whois.arin.net"
    LNICHOST            = "whois.lacnic.net"
    RNICHOST            = "whois.ripe.net"
    PNICHOST            = "whois.apnic.net"
    MNICHOST            = "whois.ra.net"
    QNICHOST_TAIL       = ".whois-servers.net"
    SNICHOST            = "whois.6bone.net"
    BNICHOST            = "whois.registro.br"
    NORIDHOST           = "whois.norid.no"
    IANAHOST            = "whois.iana.org"
    GERMNICHOST         = "de.whois-servers.net"
   
    # added by dimoha 31.08.2011
    MANUAL_HOSTS	= {"kz":"whois.nic.kz", "ve":"whois.nic.ve", "ms":"whois.nic.ms", "by":"whois.ripe.net", "net.ru":"whois.nic.ru","org.ru":"whois.nic.ru", "com.ru":"whois.nic.ru", "ua":'whois.ua'}	
    
    DEFAULT_PORT        = "nicname"
    WHOIS_SERVER_ID     = "Whois Server:"
    WHOIS_ORG_SERVER_ID = "Registrant Street1:Whois Server:"


    WHOIS_RECURSE       = 0x01
    WHOIS_QUICK         = 0x02

    ip_whois = [ LNICHOST, RNICHOST, PNICHOST, BNICHOST ]

    def __init__(self) :
        self.use_qnichost = False
        
    def findwhois_server(self, buf, hostname):
        """Search the initial TLD lookup results for the regional-specifc
        whois server for getting contact details.
        """
        
	nhost = None
        parts_index = 1
        start = buf.find(NICClient.WHOIS_SERVER_ID)
        if (start == -1):
            start = buf.find(NICClient.WHOIS_ORG_SERVER_ID)
            parts_index = 2
        
        if (start > -1):   
            end = buf[start:].find('\n')
            whois_line = buf[start:end+start]
            whois_parts = whois_line.split(':')
            nhost = whois_parts[parts_index].strip()
        elif (hostname == NICClient.ANICHOST):
            for nichost in NICClient.ip_whois:
                if (buf.find(nichost) != -1):
                    nhost = nichost
                    break
        return nhost
        
    def whois(self, query, hostname, flags):
        """Perform initial lookup with TLD whois server
        then, if the quick flag is false, search that result 
        for the region-specifc whois server and do a lookup
        there for contact details
        """
        #pdb.set_trace()
	#print hostname
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((hostname, 43))
        if (hostname == NICClient.GERMNICHOST):
            s.send("-T dn,ace -C US-ASCII " + query + "\r\n")
        elif '.name' in query:			# added by dimoha 31.08.2011
	    s.send("domain=" + query + "\r\n")		
	else:
            s.send(query + "\r\n")
        response = ''
        while True:
            d = s.recv(4096)
            response += d
            if not d:
                break
        s.close()
        #pdb.set_trace()
        nhost = None
        if (flags & NICClient.WHOIS_RECURSE and nhost == None):
            nhost = self.findwhois_server(response, hostname)
        if (nhost != None):
            response += self.whois(query, nhost, 0)
	
        return response
    
    def choose_server(self, domain):
        """Choose initial lookup NIC host"""
        if (domain.endswith("-NORID")):
            return NICClient.NORIDHOST
        pos = domain.rfind('.')
        if (pos == -1):
            return None
        tld = domain[pos+1:]
	
        if (tld[0].isdigit()):
            return NICClient.ANICHOST
	
	try:
		# fucking hack
		ms = ''
		ser = ''
		for z,s in NICClient.MANUAL_HOSTS.iteritems():
			if '.'+z==domain[-(len(z)+1):]:
				if len('.'+z)>len(ms):
					ms = '.'+z
					ser = s
		if ser!='':
			return ser
		else:
			return NICClient.MANUAL_HOSTS[tld]
	except:
		return tld + NICClient.QNICHOST_TAIL
    
    def whois_lookup(self, options, query_arg, flags):
        """Main entry point: Perform initial lookup on TLD whois server, 
        or other server to get region-specific whois server, then if quick 
        flag is false, perform a second lookup on the region-specific 
        server for contact records"""
        nichost = None
        #pdb.set_trace()
        # this would be the case when this function is called by other then main
        if (options == None):                     
            options = {}
     
        if ( (not options.has_key('whoishost') or options['whoishost'] == None)
            and (not options.has_key('country') or options['country'] == None)):
            self.use_qnichost = True
            options['whoishost'] = NICClient.NICHOST
            if ( not (flags & NICClient.WHOIS_QUICK)):
                flags |= NICClient.WHOIS_RECURSE
            
       

	if (options.has_key('country') and options['country'] != None):
            result = self.whois(query_arg, options['country'] + NICClient.QNICHOST_TAIL, flags)
        elif (self.use_qnichost):
            nichost = self.choose_server(query_arg)
	    if (nichost != None):
                result = self.whois(query_arg, nichost, flags)
	    else:
		raise WhoIsException('Cant define WHOIS-server') 
        else:
            result = self.whois(query_arg, options['whoishost'], flags)
        
        return result