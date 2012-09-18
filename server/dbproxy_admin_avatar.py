#!/usr/bin/env python
# *_* encoding=utf-8 *_*

from finger.server.baseserver import BaseAdminAvatar
from sqlalchemy.sql.expression import select


class DBProxyAdminAvatar(BaseAdminAvatar):
    def __init__(self, name, server):
        BaseAdminAvatar.__init__(self, name, server)
        
    def perspective_test(self, message):
        return message
        
    def perspective_get_users(self):
        users = self.server.meta.tables['users']
        conn = select([users])
        result = conn.execute()
        return [dict(row) for row in result]
    
    def perspective_get_address(self):
        pass
    
    def perspective_insert_user(self, name, fullname):
        pass