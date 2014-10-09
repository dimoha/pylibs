# -*- coding: utf-8 -*-
import re

def toUnicode(keyword):
    if type(keyword).__name__!='unicode':
        keyword = unicode(keyword, 'utf-8')
    return keyword

def prepareKeyword(keyword):
    keyword = toUnicode(keyword).lower().strip().replace('\t', ' ')
    keyword = re.sub('[\?!,:\.-]+(?is)', ' ', keyword)
    keyword = re.sub('[\s\xa0]+(?is)', ' ', keyword).strip()
    return keyword

