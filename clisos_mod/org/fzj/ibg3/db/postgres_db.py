'''
Created on Jul 11, 2013

@author: sorg
'''

import psycopg2.extras

DSN = "host=%s dbname=%s user=%s password=%s"

def getDsn(host,dbname,user,password):
    return DSN % (host,dbname,user,password)

#postgres wrapper
class PostgresSql:
    def __init__(self, dsn, withColumnAccess=False):
        self._DSN = dsn
        self._connection = self._openDB()
        if withColumnAccess:
            self._cursor = self._connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            self._cursor = self._connection.cursor()

    def _openDB(self):
        return psycopg2.connect(self._DSN)
    
    def executeQueryCursor(self, query, data=()):
        if(data!=()):
            self._cursor.execute(query,data)
        else:
            self._cursor.execute(query)
        return self._cursor
    
    def executeQuery(self, query, data=()):
        self._cursor.execute(query,data)
        return self._cursor.fetchall()
    
    def insertQuery(self,query,data=(),commit=False):
        self._cursor.execute(query,data)
        if commit:
            self.commit()
            
    def deleteQuery(self,deleteStatement,data=(),commit=False):
        self.insertQuery(deleteStatement,data,commit)

    def modifyQuery(self,query,data=(),commit=False):
        self.insertQuery(query, data, commit)
        
    def commit(self):
        self._connection.commit()
    
    def rollback(self):
        self._connection.rollback()
        
    def close(self):
        self._connection.close()
        
    def autocommit(self,trueFalse):
        if hasattr(self._connection,"autocommit"):
            self._connection.autocommit=trueFalse
        else:
            #version less than 2.4.2
            if trueFalse:
                self._connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            else:
                #default
                self._connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
        