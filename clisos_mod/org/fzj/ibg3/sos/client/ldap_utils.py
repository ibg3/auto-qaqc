'''
Created on Apr 3, 2018

@author: sorg
'''

import sys, ldap

def getLdapUserAccount(userName):
    # DN = username@example.com, secret = password, un = username
    DN, secret, un = sys.argv[1:4]
    
    DN="gast1"
    secret="ICG-r4user"
    server = "ldap://agro009.ibg.kfa-juelich.de"
    port = 389
    
    base = "dc=example,dc=com"
    scope = ldap.SCOPE_SUBTREE
    filter = "(&(objectClass=user)(sAMAccountName=" + userName + "))"
    attrs = ["*"]
    
    l = ldap.initialize(server)
    l.protocol_version = 3
    l.set_option(ldap.OPT_REFERRALS, 0)
    
    print(l.simple_bind_s(DN, secret))
    
    r = l.search(base, scope, filter, attrs)
    type, user = l.result(r, 60)
    
    name, attrs = user[0]
    
    if hasattr(attrs, 'has_key') and 'displayName' in attrs:
        print(attrs)
