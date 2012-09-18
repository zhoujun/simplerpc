#!/usr/bin/env python
# *_* encoding=utf-8 *_*

from finger.log.baselogger import FileLogger, DiaryRollingFileLogger
import os
import sys
from twisted.python import log as twisted_log

class Logger(object):
    def __init__(self):
        self.init('.', os.path.split(sys.argv[0])[-1], True, True)
#        path, name, debug, print_to_console = '.', os.path.split(sys.argv[0])[-1], True, True
            
    def init(self, path, name, debug=False, print_to_console=False):
        self._debug = debug
        self._print_to_console = print_to_console
        
        self._log = DiaryRollingFileLogger(path, name)
        self._errlog = DiaryRollingFileLogger(path, '%s.error' % name)
        self._debuglog = FileLogger(path, '%s.debug' % name)
        
        if print_to_console:
            self._debuglog.enable_console(True)
            
    def msg(self, format, *args):
        self._log.log(format, *args)
        if self._debug:
            self._debuglog.log(u'[INFO]%s' % format, *args)
            
    def error(self, format, *args, **kwargs):
        self._errlog.error(format, *args, **kwargs)
        if self._debug:
            self._debuglog.error(u'[ERROR]%s' % format, *args, **kwargs)
        
    def debug(self, format, *args, **kwargs):
        if self._debug:
            self._debuglog.error(u'[DEBUG]%s' % format, *args, **kwargs)
            
log = Logger()
def startLogging(path, filename, debug, capture_stdout=True):
    log.init(path, filename, debug, not capture_stdout)
    
    if debug:
        twisted_log.startLoggingWithObserver(twisted_debug_observer, setStdout=capture_stdout)
    else:
        twisted_log.startLoggingWithObserver(twisted_log_observer, setStdout=capture_stdout)
    
    log.msg('LogStart;%s', filename)
    twisted_log.msg('TwistedLogStart')
    return log
            
def twisted_log_observer(evtdict):
    if evtdict['isError']:
        for msg in evtdict['message']:
            log.error(msg)
        failure = evtdict.get('failure', None)
        if failure:
            log.error('', exc_info=failure)
        
def twisted_debug_observer(evtdict):
    try:
        if evtdict['isError']:
            for msg in evtdict['message']:
                log.error(msg)
            failure = evtdict.get('failure', None)
            if failure:
                log.error('', exc_info=failure)
        else:
            for msg in evtdict['message']:
                log.debug(msg)
                
    except Exception, e:
        log.error('twisted_debug_observer', exc_info=e)
        

if __name__ == '__main__':
    log.debug('%s%s', 'a', 'b')
    log.error('haha')
    log.msg('hehe')
            
        
                     
        