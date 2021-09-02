'''
Created on May 14, 2019

@author: sorg
'''
from clisos_mod.org.fzj.ibg3.db.postgres_db import PostgresSql,getDsn

"""

problem: restrict access to not quality checked data. 

"""

DATA_VALUE_QUERY="""
select data.objectid,sites.code,variables.code,timestampto, datavalue, qualifiers.code, processingstatusid
from 
  observationdata.%s as data,
  observationreferences.qualifiergroups,
  observationreferences.qualifiers,
  cv.variables,
  observationreferences.sites
 where 
  sites.objectid=data.siteid 
  and variables.objectid=data.variableid
  and qualifiergroups.objectid=data.qualifierid
  and qualifiergroups.groupid=qualifiers.objectid  
  and timestampto between %s and %s
  and sites.code in (%s)
  and variables.code in (%s)
"""

def query(username, pw, host, tableName, fromTs, toTs, stations, variables, databaseName="tereno"):
    odmDb=PostgresSql(getDsn(host, databaseName, username, pw))
    crs=odmDb.executeQueryCursor(DATA_VALUE_QUERY, (tableName, fromTs, toTs, stations, variables))
    

