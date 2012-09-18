#!/usr/bin/env python
# *_* encoding=utf-8 *_*

from twisted.cred import portal, checkers
from twisted.internet import defer, reactor
from twisted.python import log
from twisted.spread import pb
from zope.interface.declarations import implements
import cPickle as pickle

class RPCServer(object):
    
    def __init__(self, port):
        self.port = port
        self.avatars = []
        
    def add_avatar(self, user, password, avatar_class, args):
        self.avatars.extend([[user, password, avatar_class, args]])
        
    def start(self):
        realm = _Realm(dict([(u,(class_,args))for u,_,class_,args in self.avatars]))
        portal_ = portal.Portal(realm)
        checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
        for u, p, _, _ in self.avatars:
            checker.addUser(u, p)
        portal_.registerChecker(checker)
        print 'RPCServer(%s) start...' % self.port
        reactor.listenTCP(self.port, pb.PBServerFactory(portal_))
        
class _Realm:
    implements(portal.IRealm)
    
    def __init__(self, avatar_dict):
        self.avatar_dict = avatar_dict
        
    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective in interfaces:
            tmp = self.avatar_dict.get(avatarId, None)
            
            if tmp:
                avatar_class, args = tmp
                avatar = avatar_class(avatarId, *args)
            else:
                raise Exception('Unkown avatarID: %s' % avatarId)
                return
            
            avatar.attach(mind)
            return pb.IPerspective, avatar, lambda a=avatar:a.detach(mind)
        else:
            raise NotImplementedError('no interface')
        
class BaseAvatar(pb.Avatar):
    def __init__(self, name):
        self.name = name
        self._addr = None
        self._remote = None
        for name in dir(self):
            if not name.startswith('perspective_'):
                continue
            func = self._wrap_func(getattr(self, name))
            setattr(self, name, func)
            
    def get_addr(self):
        return self._addr
    
    def on_connected(self):
        pass
    
    def call_remote(self, name, *args, **kwargs):
        d = self._remote.callRemote(name, pickle.dumps((args, kwargs)))
        d.addErrback(self._restore_exception_type)
        d.addCallback(lambda result:pickle.loads(result))
        return d
        
    def _wrap_func(self, func):
        def new_func(args):
            args, kwargs = pickle.loads(args)
            d = defer.maybeDeferred(func, *args, **kwargs)
            d.addCallback(pickle.dumps)
            return d
        return new_func
        
    def attach(self, mind):
        try:
            self._remote = mind
            peer = self._remote.borker.transport.getPeer()
            self._addr = peer.host
        except Exception:
            pass
        
        self.on_attached()
        
    def on_attached(self):
        pass
    
    def detach(self, mind):
        self.on_detached()
        self._remote = None
        
    def on_detached(self):
        pass
    
    def _restore_exception_type(self, fail):
        if not isinstance(fail.type, str):
            fail.raiseException()
            return
        module_name, class_name = fail.type.rsplit('.', 1)
        module = __import__(module_name, formlist=[class_name])
        try:
            fail.type = getattr(module, class_name)
        except:
            fail.type = BaseException
        finally:
            fail.raiseException()
            
    def __str__(self):
        return u"""<%s name="%s" addr="%s">""" % (self.__class__.__name__, self.name, self.get_addr())
    
if __name__ == '__main__':
    
    class TestAvatar(BaseAvatar):
        def __init__(self, name, msg):
            BaseAvatar.__init__(self, name)
            
        def perspective_echo(self, msg):
            return msg
        
        def perspective_echo2(self, msg):
            raise Exception, 'test error'
            return 'echo back:' + str(msg) 
        
    server = RPCServer(12000)
    server.add_avatar('user', 'password', TestAvatar, ('',))
    server.start()
    reactor.run()
            