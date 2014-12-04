# -*- coding: utf-8 -*-
import re, os, sys
from pylibs.utils import UtilsException
from pymorphy import get_morph


class UtilsTexts(UtilsException):
    pass


def toUnicode(keyword):
    if type(keyword).__name__ != 'unicode':
        keyword = unicode(keyword, 'utf-8')
    return keyword


def prepareKeyword(keyword):
    keyword = toUnicode(keyword).lower().strip().replace('\t', ' ')
    keyword = re.sub('[\?!,:\.-]+(?is)', ' ', keyword)
    keyword = re.sub('[\s\xa0]+(?is)', ' ', keyword).strip()
    return keyword


def strip_tags(value):
    return re.sub('<[^>]*?>(?is)', '', value)


def delete_stop_words(s):
    sw = unicode('a|about|all|an|and|any|are|as|at|be|but|by|can|do|for|from|have|i|if|in|is|it|my|no|not|of|on|one|or|'
                 'so|that|the|there|they|this|to|was|we|what|which|will|with|would|you|а|або|авжеж|аж|але|атож|б|без|би'
                 '|бо|був|буде|будем|будемо|будет|будете|будеш|будешь|буду|будут|будуть|будь|будьмо|будьте|була|були|'
                 'було|бути|бы|был|была|были|было|быть|в|вам|вами|вас|ваш|ваша|ваше|вашим|вашими|ваших|вашого|вашому|'
                 'вашою|вашої|вашу|ваші|вашій|вашім|ввесь|весь|вже|ви|во|воно|вот|все|всего|всей|всем|всеми|всему|всех'
                 '|всею|всього|всьому|всю|вся|всё|всі|всій|всім|всіма|всіх|всією|всієї|вы|від|він|да|де|для|до|дуже|еге'
                 '|его|ее|ей|ему|если|есть|еще|ещё|ею|её|ж|же|з|за|зі|и|из|или|им|ими|их|й|його|йому|к|как|кем|кимось|'
                 'ко|когда|кого|когось|ком|кому|комусь|которая|которого|которое|которой|котором|которому|которою|'
                 'которую|которые|который|которым|которыми|которых|кто|кім|ледве|лиш|лише|майже|мене|меня|мені|мне|'
                 'мной|мною|мовби|мог|моги|могите|могла|могли|могло|мого|могу|могут|мое|моего|моей|моем|моему|моею|'
                 'можем|может|можете|можешь|мои|моим|моими|моих|мой|мочь|мою|моя|моё|моём|моє|моєму|моєю|моєї|мої|'
                 'моїй|моїм|моїми|моїх|мы|між|мій|на|навіть|над|нам|нами|нас|наче|начебто|наш|наша|наше|нашего|нашей|'
                 'нашем|нашему|нашею|наши|нашим|нашими|наших|нашого|нашому|нашою|нашої|нашу|наші|нашій|нашім|не|невже|'
                 'него|нее|ней|нем|немов|нему|неначе|нет|нехай|нею|неё|неї|ним|ними|них|но|ну|нього|ньому|нём|ні|ніби|'
                 'нібито|ній|ніким|нікого|нікому|нікім|нім|ніхто|нічим|нічого|нічому|ніщо|ніяка|ніяке|ніякий|ніяким|'
                 'ніяких|ніякого|ніякому|ніякою|ніякої|ніякі|ніякій|о|об|од|один|одна|одни|одним|одними|одних|одно|'
                 'одного|одной|одном|одному|одною|одну|он|она|они|оно|от|отак|ото|оце|оцей|оцеє|оцим|оцими|оцих|оцього|'
                 'оцьому|оцю|оцюю|оця|оцяя|оці|оцій|оцім|оцією|оцієї|оції|по|поки|при|про|під|с|сам|сама|саме|самий|'
                 'самим|самими|самих|само|самого|самому|самою|самої|саму|самі|самій|самім|свого|свое|своего|своей|'
                 'своем|своему|своею|свои|своим|своими|своих|свой|свою|своя|своё|своём|своє|своєму|своєю|своєї|свої|'
                 'своїй|своїм|своїми|своїх|свій|се|себе|себя|сей|сими|сих|собой|собою|собі|сього|сьому|сю|ся|сі|сій|'
                 'сім|сією|сієї|та|так|така|такая|таке|таки|такие|такий|таким|такими|таких|такого|такое|такой|таком|'
                 'такому|такою|такої|таку|такую|такі|такій|такім|тая|твого|твою|твоя|твоє|твоєму|твоєю|твоєї|твої|'
                 'твоїй|твоїм|твоїми|твоїх|твій|те|тебе|тебя|тем|теми|тех|теє|ти|тим|тими|тих|то|тобой|тобою|тобі|'
                 'того|той|только|том|тому|тот|тою|тої|ту|тую|ты|ті|тій|тільки|тім|тією|тієї|тії|у|увесь|уже|усе|'
                 'усього|усьому|усю|уся|усі|усій|усім|усіма|усіх|усією|усієї|хай|хоч|хто|хтось|хіба|це|цей|цеє|цим|'
                 'цими|цих|цього|цьому|цю|цюю|ця|цяя|ці|цій|цім|цією|цієї|ції|чего|чем|чему|чи|чий|чийого|чийому|чим|'
                 'чимось|чимсь|чию|чия|чиє|чиєму|чиєю|чиєї|чиї|чиїй|чиїм|чиїми|чиїх|чого|чогось|чому|чомусь|что|чтобы|'
                 'чём|чім|чімсь|ще|що|щоб|щось|эта|эти|этим|этими|этих|это|этого|этой|этом|этому|этот|эту|я|як|яка|'
                 'якась|яке|якесь|який|якийсь|яким|якими|якимись|якимось|якимсь|яких|якихось|якого|якогось|якому|'
                 'якомусь|якою|якоюсь|якої|якоїсь|якраз|яку|якусь|якщо|які|якій|якійсь|якім|якімось|якімсь|якісь|є|'
                 'і|із|іякими|їй|їм|їх|їхнього|їхньому|їхньою|їхньої|їхню|їхня|їхнє|їхні|їхній|їхнім|їхніми|їхніх|її|'
                 'http|www', 'utf-8')
    s = s.replace(' ', '  ')
    s = re.sub('\s('+sw+')\s', ' ', ' '+s+' ')
    s = re.sub('\s+(?is)', ' ', s)
    return s.strip()


def clear_html_general(html, is_strip_tags=True, is_del_links=False):
    html = re.sub('<style[^>]*>.*?</style>(?isu)', '', html)
    html = re.sub('<script[^>]*>.*?</script>(?isu)', '', html)
    html = re.sub('<noindex[^>]*>.*?</noindex>(?isu)', '', html)
    html = re.sub('<!--[\s]*noindex[\s]*-->.*?<!--[\s]*/noindex[\s]*-->(?isu)', '', html)
    html = re.sub('<noscript[^>]*>.*?</noscript>(?isu)', '', html)
    html = re.sub('<!--.*?-->(?isu)', '', html)
    html = re.sub('<select[^>]*>.*?</select>(?isu)', ' ', html)
    html = re.sub('<(option)[^>]*>.*?</\\1>(?isu)', ' ', html)
    html = re.sub('<textarea[^>]*>.*?</textarea>(?isu)', ' ', html)
    html = re.sub('&[^;]{2,10};(?isu)', ' ', html)
    html = re.sub('&#[a-z0-9]{1,10};(?isu)', ' ', html)
    
    if is_del_links:
        html = re.sub('<a[^>]*>.*?</a>(?isu)', '', html)

    if is_strip_tags:
        html = strip_tags(html)

    html = re.sub('\s+(?is)', ' ', html)

    return html


def normalize_string(s):
    s = toUnicode(s)
    m = get_pymorphy_handler()

    nf = []
    s = s.replace('.', ' .')
    for initWord in s.split(' '):
        word = initWord.strip().upper()
        tw = ''

        info = []
        try:
            infos = m.get_graminfo(word, True)
            if len(infos)>0:
                for info in infos:
                    if 'class' in info and (info['class'] == 'S' or info['class'] == 'V' or info['class'] == 'A'):
                        break
                    else:
                        info = []
        except Exception:
            info = []

        if len(info) > 0:
            tw = info['norm'].lower().strip()
        elif word.strip() == '.':
            tw = '.'
        elif len(word.strip(' .')) > 1 and re.search('^[a-zA-Z0-9-]+$(?isu)', word.strip(' .')):
            tw = initWord.strip(' .')

        if tw != '':
            nf.append(tw)

    nf = ' '.join(nf)
    return nf


def normalize_string_simple(s):

    s = toUnicode(s)
    morph = get_pymorphy_handler()

    nf = []
    for kk, ow in enumerate(s.split(' ')):
        word = ow.strip().upper()
        info = morph.get_graminfo(word, True)
        if len(info) > 0 and info[0]['norm'] != '':
            tw = info[0]['norm'].lower().strip()
        else:
            tw = word.lower().strip()
        nf.append(tw)
    nf = ' '.join(nf)
    return nf


def get_pymorphy_handler():
    if 'pymorphy_link' not in globals():
        dicts_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dicts', 'ru')
        globals()['pymorphy_link'] = get_morph(dicts_path, 'cdb')
    return globals()['pymorphy_link']


class SemanticNoContentException(UtilsTexts):
    pass


class SemanticAnalyze(object):

    block_elements = ['TITLE', 'ADDRESS', 'BLOCKQUOTE', 'CENTER', 'DIR', 'DIV', 'DL', 'FIELDSET', 'FORM', 'H1', 'H2',
                      'H3', 'H4', 'H5', 'H6', 'ISINDEX', 'MENU', 'NOFRAMES', 'NOSCRIPT', 'OL', 'P', 'PRE', 'TABLE',
                      'UL', 'DD', 'DT', 'FRAMESET', 'LI', 'TBODY', 'TD', 'TFOOT', 'TH', 'THEAD', 'TR', 'APPLET',
                      'BUTTON', 'DEL', 'IFRAME', 'INS', 'MAP', 'OBJECT']

    sentences_delimiters = '\.\?!:,'

    def __init__(self, html, only_normalized_text=False, total_limit=10):
        self.html = toUnicode(html)
        self.only_normalized_text = only_normalized_text
        self.total_limit = total_limit
        self.combinations = {}
        self.singles = {}
        self.reg = "(<"+"[\s\t>]|<".join(self.block_elements)+"[\s\t>])(?isu)"
        self.result_words = []
        self.result_init_words = []

        self.parts_of_page = {
            'title': {'text': '', 'weight': 10},
            'keywords': {'text': '', 'weight': 6},
            'description': {'text': '', 'weight': 6},
            'h1-h6': {'text': '', 'weight': 2},
            'other': {'text': '', 'weight': 1},
        }


    def __get_title(self):
        m = re.search('<title[^>]*>(.*?)</title>(?isu)', self.html)
        if m:
            self.parts_of_page['title']['text'] = m.group(1).strip()

    def __get_kwd_and_desc(self):
        for tag in ['description', 'keywords']:
            m = re.search('(<meta[^>]+name\s*=\s*"\s*'+tag+'\s*"[^>]*>)(?isu)', self.html)
            if m:
                m2 = re.search('content\s*=\s*"([^"]+)"(?isu)', m.group(1))
                if m2:
                    self.parts_of_page[tag]['text'] = m2.group(1).strip()

    def __get_h1h6(self):
        m = re.findall('<h[1-6][^>]*>(.*?)</h[1-6]>(?isu)', self.html)
        if m:
            for v in m:
                self.parts_of_page['h1-h6']['text'] += '. '+v.strip()

    def __get_other_txt(self):
        # remove title
        self.html = re.sub('<title[^>]*>(.*?)</title>(?isu)', '', self.html)

        # remove keywords and descriptions
        self.html = re.sub('<meta[^>]+name\s*=\s*"\s*description\s*"[^>]*>(?isu)', '', self.html)
        self.html = re.sub('<meta[^>]+name\s*=\s*"\s*keywords\s*"[^>]*>(?isu)', '', self.html)

        self.parts_of_page['other']['text'] = self.html
        self.parts_of_page['other']['text'] = self.parts_of_page['other']['text'].replace('#', '')
        self.parts_of_page['other']['text'] = re.sub(self.reg, r'<hr>\1', self.parts_of_page['other']['text'])
        self.parts_of_page['other']['text'] = re.sub('<hr>|<hr/>|<hr />(?is)', ' # ',
                                                                        self.parts_of_page['other']['text'])
        self.parts_of_page['other']['text'] = self.parts_of_page['other']['text'].replace('#?', '#')


    def __prepare_parts_of_pages(self):

        for tag in self.parts_of_page:
            self.parts_of_page[tag]['text'] = re.sub('<[^>]+>(?is)', '', self.parts_of_page[tag]['text'])

            if not self.only_normalized_text:
                self.parts_of_page[tag]['text'] = re.sub('[^\s]*[0-9]+[^\s]+(?i)', ' ', self.parts_of_page[tag]['text'])
                self.parts_of_page[tag]['text'] = re.sub('[^\s]+[0-9]+[^\s]*(?i)', ' ', self.parts_of_page[tag]['text'])


            self.parts_of_page[tag]['text'] = re.sub('[^#\w\d'+self.sentences_delimiters+']+(?isu)', ' ',
                                                                        self.parts_of_page[tag]['text'])
            self.parts_of_page[tag]['text'] = re.sub('\s+(['+self.sentences_delimiters+'])(?i)', ".",
                                                                        self.parts_of_page[tag]['text'])
            self.parts_of_page[tag]['text'] = re.sub('['+self.sentences_delimiters+'](?i)', '.',
                                                                        self.parts_of_page[tag]['text'])
            self.parts_of_page[tag]['text'] = re.sub('[\.]+(?i)', '.', self.parts_of_page[tag]['text'])

        self.parts_of_page['other']['text'] = list(set(self.parts_of_page['other']['text'].split(" # ")))
        self.parts_of_page['other']['text'] = ' # '.join(self.parts_of_page['other']['text']).strip(' #')
        self.parts_of_page['other']['text'] = re.sub('\s*#\s*(?i)', '#', self.parts_of_page['other']['text'])
        self.parts_of_page['other']['text'] = re.sub('\.?#+(?i)', '. ', self.parts_of_page['other']['text'])

    def __filter_by_liveinternet(self, c):
        # NotImplemented
        return c

    def __create_combinations(self):
        for tag in self.parts_of_page:

            if self.parts_of_page[tag]['text'] == "":
                continue

            if not self.only_normalized_text:
                self.parts_of_page[tag]['text'] = re.sub(u'\s[а-яА-ЯёЁa-zA-Z0-9]{1,2}[\s\.](?uis)', ' ',
                                                         ' %s ' % self.parts_of_page[tag]['text']).strip()
                self.parts_of_page[tag]['text'] = re.sub('\s[\s\d]+\s(?uis)', ' ',
                                                         ' %s ' % self.parts_of_page[tag]['text']).strip()
            if not self.only_normalized_text:
                self.parts_of_page[tag]['text'] = normalize_string(self.parts_of_page[tag]['text'])
            else:
                self.parts_of_page[tag]['text'] = normalize_string_simple(self.parts_of_page[tag]['text'])

            self.parts_of_page[tag]['text'] = self.parts_of_page[tag]['text'].split('. ')

            for kk, vv in enumerate(self.parts_of_page[tag]['text']):
                self.parts_of_page[tag]['text'][kk] = vv.strip('. ')

            self.parts_of_page[tag]['text'] = list(set(self.parts_of_page[tag]['text']))

            if not self.only_normalized_text:

                for one in self.parts_of_page[tag]['text']:
                    one = list(set(one.strip().split(' ')))

                    for kk, vv in enumerate(one):
                        one[kk] = vv.strip()

                    if len(one) > 0:
                        for k, word in enumerate(one):
                            self.singles.setdefault(word, [word, 0])
                            self.singles[word][1] += self.parts_of_page[tag]['weight']
                            sub_one = one[k::1]
                            for word2 in sub_one:
                                if word2 != word:
                                    key = word.strip()+' '+word2.strip()
                                    self.combinations.setdefault(key, [key, 0])
                                    self.combinations[key][1] += self.parts_of_page[tag]['weight']

            self.parts_of_page[tag]['text'] = '. '.join(self.parts_of_page[tag]['text'])


    def __get_semantic_of_page(self):
        ss = filter(lambda x: x[1] > 1, self.singles.values())
        sc = filter(lambda x: x[1] > 1, self.combinations.values())
        ss = sorted(ss, key=lambda x: x[1], reverse=True)
        sc = sorted(sc, key=lambda x: x[1], reverse=True)
        ss = ss[0:6]
        sc = sc[0:self.total_limit*1]

        for v in ss:
            if v not in sc:
                sc.append(v)

        return sc

    def __normalize_semantic(self, sc):

        m = get_pymorphy_handler()

        can_forms = ['SS', 'SV', 'VS', 'AS', 'SA', 'S']

        for k, com in enumerate(sc):
            nf = []
            wtype = ''
            for kk, ow in enumerate(com[0].split(' ')):
                word = ow.strip().upper()
                if word != "":
                    info = m.get_graminfo(word, True)

                    if len(info) > 0:
                        wtype += info[0]['class']
                        tw = info[0]['norm'].lower().strip()
                    else:
                        tw = word.lower().strip()

                    if tw.strip() != '' and tw not in nf:
                        nf.append(tw)

            if wtype in can_forms:
                nf = ' '.join(nf)
                if nf.strip() != '' and nf not in self.result_words:
                    self.result_init_words.append(com[0].strip())
                    self.result_words.append(nf.strip())

    def get_semcore(self):

        self.html = clear_html_general(self.html, False, self.only_normalized_text)
        self.html = re.sub('<br[^>]*>(?isu)', ' ', self.html).lower()

        if not self.only_normalized_text:
            self.html = delete_stop_words(self.html)

        self.__get_title()
        self.__get_kwd_and_desc()
        self.__get_h1h6()
        self.__get_other_txt()
        self.__prepare_parts_of_pages()
        self.__create_combinations()

        if self.only_normalized_text:
            return self.parts_of_page

        if len(self.combinations) > 0:
            self.combinations = self.__filter_by_liveinternet(self.combinations)

        sc = self.__get_semantic_of_page()

        if len(sc) == 0:
            raise SemanticNoContentException(u'Not found content on page.')

        self.__normalize_semantic(sc)


def get_semantic(html):
    sa = SemanticAnalyze(html)
    sa.get_semcore()
    return sa.result_words