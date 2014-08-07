# -*- coding: utf-8 -*-
def toUnicode(keyword):
    if type(keyword).__name__!='unicode':
        keyword = unicode(keyword, 'utf-8')
    return keyword