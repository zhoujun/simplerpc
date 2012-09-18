#!/usr/bin/env python
# *_* encoding=utf-8 *_*
from twisted.cred import credentials
from twisted.internet import defer, reactor, error
from twisted.python import log
from twisted.spread import pb
import cPickle as pickle

class BaseClient(pb.Referenceable):
    remote = None
    def __init__(self, server_addr, user, password):
        
        self.pb_addr = server_addr
        self.pb_user = user
        self.pb_pass = password
        
        self._remote = None
        self._factory = None
        
        for name in dir(self):
            if not name.startswith('remote_'):
                continue
            func = self._wrap_func(getattr(self.name))
            setattr(self, name, func)
            
    def _wrap_func(self, func):
        def new_func(args):
            args, kwargs = pickle.loads(args)
            d = defer.maybeDeferred(func, *args, **kwargs)
            d.addCallback(pickle.dumps)
            return d
        return new_func
    
    def connect(self):
        log.msg('connecting to: %s', self.pb_addr)
        self.factory = _ReconnectionPBClientFactory(self)
        reactor.connectTCP(self.pb_addr[0], self.pb_addr[1], self.factory)
        return self.factory.deferred
    
    def attach(self, perspective, factory):
        self._remote = perspective
        self._factory = factory
        
    def detach(self):
        self._remote = None
        
    def is_connected(self):
        return self._remote
    
    def call_remote(self, name, *args, **kwargs):
        d = self._remote.callRemote(name, pickle.dumps((args, kwargs)))
        d.addErrback(self._restore_exception_type)
        d.addCallback(lambda result: pickle.loads(result))
        return d
    
    def _restore_exception_type(self, fail):
        if not isinstance(fail.type, str):
            fail.raiseException()
            return
        module_name, class_name = fail.type.rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        try:
            fail.type = getattr(module, class_name)
        except:
            fail.type = BaseException
        finally:
            fail.raiseException()
            
    def on_connected(self):
        pass
    
    def on_disconnected(self, reason):
        return True
    
    def on_connection_failed(self, reason):
        return True
    
    def close(self):
        if self._factory:
            self.factory.disconnect()
    
class _ReconnectionPBClientFactory(pb.PBClientFactory):
    _callId = None
    _retry = True
    
    connector = None
    client = None
    
    def __init__(self, client):
        pb.PBClientFactory.__init__(self)
        self.deferred = defer.Deferred()
        self.client = client
        
    def clientConnectionMade(self, broker):
        pb.PBClientFactory.clientConnectionMade(self, broker)
        d = self.login(credentials.UsernamePassword(self.client.pb_user, self.client.pb_pass),
                       client=self.client)
        d.addCallback(self.on_login)
        
    def on_login(self, perspective):
        self.client.attach(perspective, self)
        self.client.on_connected()
        if not self.deferred.called:
            self.deferred.callback(self.client)
            
    def clientConnectionFailed(self, connector, reason):    
        log.msg('client connection failed.')
        if self.client.on_connection_failed(reason) and self._retry:
            self.connector = connector
            self.retry(connector)
            
    def clientConnectionLost(self, connector, reason):
        log.msg('client connection lost')
        self.client.detach()
        if self.client.on_disconnected(reason) and self._retry:
            self.connector = connector
            self.retry(connector)
            
    def disconnect(self):
        self._retry = False
        pb.PBClientFactory.disconnect(self)
        
    def retry(self, connector):
        delay = 5.0
        log.msg('retry after %s seconds.', delay)
        def reconnector():
            connector.connect()
            
        self._callId = reactor.callLater(delay, reconnector)
        
    def stopTrying(self):
        self._retry = False
        if self._callId:
            self._callId.cancel()
            self._callId = None
        if self.connector:
            try:
                self.connector.stopConnecting()
            except error.NotConnectingError:
                pass
            
if __name__ == '__main__':
    def p(result):
        print 'result:', result
    
    def e(failure):
        print failure
        
    class TestClient(BaseClient):
        def on_connected(self):
            d = self.call_remote('echo', 'hello world!')    
            d.addCallbacks(p, e)
    
    client = TestClient(('localhost', 12000), 'user', 'password')
    client.connect()
    reactor.run()
            