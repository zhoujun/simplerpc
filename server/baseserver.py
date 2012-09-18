#!/usr/bin/env python
# *_* encoding=utf-8 *_*


from finger.rpc.server import BaseAvatar
from twisted.internet import reactor

class BaseServer(object):
    def __init__(self):
        pass
    
    def before(self):
        pass
    
    def run(self):
        pass
    
    def shutdown(self):
        pass
    
    def after(self):
        pass
    
    def stop(self):
        reactor.callLater(0.1, reactor.stop())
        
        
class BaseAdminAvatar(BaseAvatar):
    def __init__(self, name, server):
        BaseAvatar.__init__(self, name)
        self.server = server
        
    def perspective_shutdown(self):
        return self.server.shutdown()
    