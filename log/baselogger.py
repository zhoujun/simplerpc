#!/usr/bin/env python
# *_* encoding=utf-8 *_*

from twisted.python.failure import Failure
import codecs
import datetime
import os
import sys
import time
import traceback

DEFAULT_LOG_ENCODING = 'utf-8'
DEFAULT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class BaseLogger(object):
    def __init__(self):
        self._print_to_console = False
        self._file = None
        self._time_format = DEFAULT_TIME_FORMAT
        
    def enable_console(self, enable):
        self._print_to_console = enable
        
    def _format(self, format, *args):
        try:
            msg = format % args
        except Exception, e:
            self.error('LogError\n' + ''.join(traceback.format_stack()))
            temp = [format] + list(args)
            for i, _ in enumerate(temp):
                if type(temp[i] is str):
                    temp[i] = temp[i].decode(DEFAULT_LOG_ENCODING)
                else:
                    try:
                        temp[i] = unicode(temp[i])
                    except:
                        temp[i] = unicode(repr(temp[i]))
                        
            msg = u''.join(temp)
        msg = u'[%s]%s\n' % (time.strftime(self._time_format, time.localtime()), msg)
        return msg
    
    def log(self, format, *args, **kwargs):
        msg = self._format(format, *args)
        if self._print_to_console:
            print msg
        self._file.write(msg)
        self._file.flush()
        
    def error(self, format, *args, **kwargs):
        self.log(format, *args, **kwargs)
        e = kwargs.pop('exc_info', None)
        if e:
            if issubclass(type(e), Exception):
                s = traceback.format_exception(type(e), e, sys.exc_info()[2])
                msg = u''.join([i.decode(DEFAULT_LOG_ENCODING) for i in s])
                self._file.write(msg)
                self._file.write(u'\n')
                if self._print_to_console:
                    print msg
                elif isinstance(e, Failure):
                    errmsg = e.getErrorMessage()
                    self._file.write(errmsg)
                    e.printTraceback(self._file)
                    
        self._file.flush()
                
class FileLogger(BaseLogger):
    def __init__(self, path, log_name):
        BaseLogger.__init__(self)
        logpath = os.path.join(path, '%s.log' % (log_name))
        self._file = codecs.open(logpath, 'ab', DEFAULT_LOG_ENCODING)
        
    def get_file(self):
        return self._file
    
class DiaryRollingFileLogger(BaseLogger):
    def __init__(self, path, log_name):
        BaseLogger.__init__(self)
        self._time_format = u'%H:%M:%S'
        self._path = path
        self._name = log_name
        self._rorate_time = 0
        self._file = None
        
        self._open_file()
        
    def _open_file(self):
        path = os.path.join(self._path, '%s.log' % self._name)
        today = datetime.date.today()
        if os.path.exists(path):
            last_modify = os.stat(path)[-2]
            last_date = datetime.datetime.fromtimestamp(last_modify).date()
            if last_date != today:
                os.rename(path, '%s.%s' % (path, last_date.strftime('%Y%m%d')))
            
        self._open(path, today)
        
    def _open(self, path, today):
        self._file = codecs.open(path, 'ab', DEFAULT_LOG_ENCODING)
        tomorrow = today + datetime.timedelta(1)
        self._rorate_time = time.mktime(tomorrow.timetuple())
        
    def _rotate(self):
        today = datetime.date.today()
        
        if self._file:
            self._file.close()
            
        path = os.path.join(self._path, '%s.log' % self._name)
        yesterday = today - datetime.timedelta(1)
        os.rename(path, '%s.%s' % (path, yesterday.str('%y%m%d')))
        
        self._open(path, today)
        
    def log(self, *args, **kwargs):
        now = time.time()
        if now >= self._rorate_time:
            self._rotate()
            
        BaseLogger.log(self, *args, **kwargs)
        
if __name__ == '__main__':
    daily = DiaryRollingFileLogger('D:\\', 'testlog')
    daily.log("haha中文")
        
        
        
        
    
    
        
        