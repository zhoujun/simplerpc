#!/usr/bin/env python
# *_* encoding=utf-8 *_*
from finger.rpc.client import BaseClient

class DBProxyClient(BaseClient):
    def on_connected(self):
        d = self.call_remote('get_users')
        d.addCallbacks(p, e)
     
def p(result):
    print 'result:', result
    
def e(failure):
    print failure   
    
    
if __name__ == '__main__':
    from twisted.internet import reactor
    
    client = DBProxyClient(('localhost', 12000), 'admin', '123456')
    client.connect()
    reactor.run()