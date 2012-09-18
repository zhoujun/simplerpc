#!/usr/bin/env python
# *_* encoding=utf-8 *_*


from finger.rpc.server import RPCServer
from finger.server.baseserver import BaseServer
from finger.server.dbproxy_admin_avatar import DBProxyAdminAvatar
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import MetaData


class DBProxyServer(BaseServer):
    def __init__(self):
        self.user = 'root'
        self.password = 'root'
        self.host = '127.0.0.1'
        self.db = 'demo'
        self.url = 'mysql://%s:%s@%s/%s' % (self.user, self.password, self.host, self.db)
        self.engine = create_engine(self.url, echo=True, encoding='utf-8', pool_size=100, pool_recycle=3600)
        self.meta = MetaData(self.engine)
        self.meta.reflect()
        
        server = RPCServer(12000)
        server.add_avatar('admin', '123456', DBProxyAdminAvatar, (self,))
        server.start()
        
    def shutdown(self):
        self.stop()
        
if __name__ == '__main__':
    from twisted.internet import reactor
    
    server = DBProxyServer()
    reactor.run()
    