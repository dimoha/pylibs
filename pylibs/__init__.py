# -*- coding: utf-8 -*-


class PyLibsException(Exception):
    u'''
    Базовый класс для всех ошибок
    '''
    def __init__(self, msg = False, errno = None):
        Exception.__init__(self, msg)
        
        if not msg:
            if self.args:
                msg = self.args
            else:
                msg = ""
            msg = self.args
        else:
            msg = unicode(msg).encode('utf-8')
        self.message = msg
        self.errno = errno
        if self.errno is not None:
            self.message = '%s - %s' % (self.errno, self.message)

    def __str__(self):
        s = self.__class__.__name__
        if self.message:
            s = s + ": " + str(self.message)

        return s