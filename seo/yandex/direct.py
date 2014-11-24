# -*- coding: utf-8 -*-
from pylibs.seo.yandex import YandexException, Yandex
from pylibs.network.parser import *
from pylibs.network.urls import *
from pylibs.utils.text import prepareKeyword, toUnicode
from logging import info, warning, error, debug
from pylibs.network.anticaptcha import AntiCaptchaException
import re, time

class YandexDirectException(YandexException):
    pass

class YandexDirectCaptchaException(YandexDirectException):
    pass

class YandexDirect(Yandex):
    
    limit_symbols = 4096
    freq_types = ['yandex_exact', 'yandex_total', 'yandex_in_quotes']

    def is_captcha(self, *args, **kwargs):
        captcha_found = super(YandexDirect, self).is_captcha(*args, **kwargs)
        if at_xpath(self.html, '//input[@name="captcha_id"]') is not None:
            captcha_found = True

        return captcha_found

    def _get_captcha_form(self):
        return at_xpath(self.html, '//form[contains(@action,"direct.yandex.ru")]')

    def _get_captcha_img(self, form):
        return at_xpath(self.html, '//img[contains(@src,"captcha.yandex")]')

    def _fill_captcha_form(self, form, captcha_value):
        form.fields['captcha_code'] = captcha_value
        return form

    def get_freqs_looped(self, keywords, region_id = 0, freq_type='yandex_exact'):


            if freq_type not in self.freq_types:
                raise YandexDirectException('Unsupported freq type (%s). Use one of: %s' % (freq_type, self.freq_types))

            freq_res = {}
            for kwd in keywords:
                freq_res[kwd] = None

            while True:
                if len(keywords)>0:
                    info("Send %s for freq" % len(keywords))
                    freqs = self.__get_freqs(keywords, region_id, freq_type)
                    if len(freqs) == 0:
                        raise YandexDirectException('Freqs not calculated for %s phrases' % len(keywords))
                    for kwd, val in freqs.iteritems():
                        if val is not None:
                            freq_res[kwd] = val
                            keywords.remove(kwd)
                else:
                    break
            return freq_res

    def __get_freqs(self, keywords, region_id = 0, freq_type='yandex_exact'):

        self.result = {}
        for keyword in keywords:
            self.result[keyword] = None
        
        to_check = {}
        for keyword in self.result:
            kwd = prepareKeyword(keyword)
            kwdToFreq = self.prepareToFreq(kwd, freq_type)      
            kwdToFreqClear = self.prepareToFreq(kwd, 'yandex_total')
            
            if kwdToFreqClear=='' or kwdToFreq=='' or kwd=='':
                self.result[keyword] = -1
                continue

            if len(kwdToFreq.split(' '))>7: 
                self.result[keyword] = 0
                continue

            if self.notForFreq(kwdToFreqClear):
                self.result[keyword] = -1
                continue
            
            to_check[kwdToFreq] = keyword



        info('to send %s phrases' % len(to_check))

        requests = []
        onereq = ''
        for q in to_check:

            if len(onereq+"\n"+q)<self.limit_symbols:
                onereq = onereq+q+"\n"
            else:
                requests.append(onereq)
                onereq = ''
        if onereq!='':
            requests.append(onereq)

        c = 0
        for req in requests:
            try:
                freqs = self.__get_freqs_one(req, region_id)
                for phraseTpl, freq in freqs.iteritems():
                    if freq_type == 'yandex_total' and phraseTpl.startswith('"'):
                        phraseTpl = phraseTpl.strip('" ')
                    if phraseTpl in to_check:
                        thisID = to_check[phraseTpl]
                        self.result[thisID] = freq
                    else:
                        info(phraseTpl+' - undefined keyword :(')
            except AntiCaptchaException:
                time.sleep(30)
            except YandexDirectException as e:
                info("try found stops, because: %s" % e)
                stops = self.get_stops(toUnicode(str(e)))    

                if len(stops)>0:
                    info('finded %s stops' % len(stops))
                    for stop in stops:
                        thisID = None
                        stop_prep = self.prepareToFreq(stop, freq_type) 
                        if stop_prep in to_check:
                            thisID = to_check[stop_prep]
                        elif stop in to_check:
                            thisID = to_check[stop]

                        if thisID is not None:
                            info("Set %s to -1" % stop.encode('utf-8'))
                            self.result[thisID] = -1
                
        return self.result


    def __get_freqs_one(self, request, region_id = 0):
    
        freqs = {}
    
        freqUrl = 'http://direct.yandex.ru/registered/main.pl?cmd=ForecastByWords'
        self.request(freqUrl)
        freq_form = at_xpath(self.html, '//form[contains(@name,"ad")]')

        if freq_form is not None:
            freq_form.fields['geo'] = str(region_id)
            freq_form.fields['new_phrases'] = request
            self.request(post_form = freq_form, post = {'timestamp':time.time()})
            


        m = re.findall('phrase:\s+\'([^\']+)\'.+?,\s+shows:\s+([\d]+)\s(?isu)', self.transport.body())
        if m:
            for v in m:
                word = unicode(v[0], 'utf-8').replace('\\"', '"')
                freq = int(v[1])
                if word!='':
                    freqs[word] = freq
                    debug(word.encode('utf-8')+' => '+str(freq))

        if len(freqs)==0:
            htm = self.transport.unicode()
            m = re.search('<td width="58%" class="body">[^<]+<p>(.+)</p>[^<]*</td>[^<]*<td[^>]+width="17%"[^>]*>(?isu)', htm)
            if not m:
                m = re.search('<p[^>]+class="p-common-error__message">(.+)</p>(?isu)', htm)
            if m:
                htm = m.group(1).strip()
                raise YandexDirectException('WordStat return: %s' % htm)
            else:
                
                raise YandexDirectException('No Results in HTML')
        
        return freqs


    def get_stops(self, message):
        
        stops = []
        m = re.findall(u'только из минус-слов \(([^\)]+)\)(?isu)', message)
        if m is not None:
            for v in m:
                phrase = v.replace('&quot;', '').strip().split(' ')
                for k,word in enumerate(phrase):
                    phrase[k] = re.sub('^!(?i)', '', word.strip())
                phrase = ' '.join(phrase)
                stops.append(phrase.strip())
        
        m = re.findall(u'Ошибка в ключевой фразе &quot;(.+)&quot;(?isu)', message.strip())
        if m is not None:
            for v in m:
                phrase = v.replace('&quot;', '"').strip().split(' ')
                for k,word in enumerate(phrase):
                    phrase[k] = re.sub('^!(?i)', '', word.strip())
                phrase = ' '.join(phrase)
                stops.append(phrase.strip())
        
        m = re.findall(u'союзов,\s+предлогов,\s+частиц\s+\(([^\)]+)\)(?isu)', message)
        if m is not None:
            for v in m:
                phrase = v.replace('&quot;', '').strip().split(' ')
                for k,word in enumerate(phrase):
                    phrase[k] = re.sub('^!(?i)', '', word.strip())
                phrase = ' '.join(phrase)
                stops.append(phrase.strip())
        return stops

    def prepareToFreq(self, keyword, freq_type):
        keyword = re.sub(u'[^\w\s\$\^ ](?isu)', ' ', toUnicode(keyword))
        keyword = re.sub('[\s\xa0]+(?is)', ' ', keyword).strip()
        if freq_type in ['yandex_exact', 'yandex_in_quotes']:
            if freq_type=='yandex_exact':
                keyword = keyword.split(' ')
                keyword = '"!'+' !'.join(keyword).strip()+'"'
            else:
                keyword = '"'+keyword.strip()+'"'
        return keyword

    def notForFreq(self, keyword):
        keyword = re.sub(u'['+unicode('а-яА-ЯёЁЄЇІієї', 'utf-8')+'a-zA-Z0-9-+!\s ](?isu)', '', toUnicode(keyword)).strip()
        if keyword=='':
            return False
        else:
            return True
