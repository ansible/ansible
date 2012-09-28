#!/usr/bin/env python

# (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import ansible.constants as C
import ConfigParser

HAVE_DNS=False
try:
    import dns.resolver
    HAVE_DNS=True
except ImportError:
    pass

HAVE_REDIS=False
try:
    import redis        # https://github.com/andymccurdy/redis-py/
    HAVE_REDIS=True
except ImportError:
    pass

HAVE_LDAP=False
try:
    import ldap, ldapurl
    HAVE_LDAP=True
except:
    pass

# Lookup types in this file are alphabetically ordered (though they
# need not be).

# ==============================================================
# DNSTXT: DNS TXT records
#
#       key=domainname
#
#   eg: key=www.example.com
# TODO: configurable resolver IPs
# --------------------------------------------------------------

def _lookup_dnstxt(params):

    if HAVE_DNS == False:
        return "ENODNSTXT"

    if not 'key' in params:
        return "ENOKEY"

    domain = params['key']

    string = []
    answers = dns.resolver.query(domain, 'TXT')
    for rdata in answers:
        s = rdata.to_text()
        print s
        string.append(s[1:-1])  # Strip outside quotes on TXT rdata

    return ''.join(string)

# ==============================================================
# environment
#
#       key=variablename
#       default=string      returned if $variablename not found
#                           default is ""
#
#   eg: key=HOME
# --------------------------------------------------------------

def _lookup_env(params):
    
    if not 'key' in params:
        return "ENOKEY"

    return os.getenv(params['key'], params.get('default', ''))

# ==============================================================
# inifile

#       section=
#       key=
#       default=            returned if key not found
#
# --------------------------------------------------------------

def _lookup_inifile(params):

    if C.inipath is None:
        return "ENOINIFILE"
    
    if not 'section' in params or not 'key' in params:
        return "ENOKEY"

    section = params['section']
    key     = params['key']
    default = params.get('default', "")

    cp = ConfigParser.ConfigParser()
    try:
        f = open(C.inipath)
        cp.readfp(f)
    except IOError:
        return "ENOINIFILE"

    try:
        if cp.has_section(section) == True:
            value = cp.get(section, key)
            return value
    except:
        return default


# ==============================================================
# LDAP
#       key=domainname
#
#   eg: key=www.example.com
#
# cfg:
#   [lookups]
#   ldapurl=ldap://localhost:389/dc=company,dc=example,dc=net
# --------------------------------------------------------------

def _lookup_ldap(params):

    if HAVE_LDAP == False:
        return "ENOLDAP"

    if not 'key' in params:
        return "ENOKEY"

    if C.ldapurl is None:
        return "ENOLDAPURL"

    ldap_url = ldapurl.LDAPUrl(C.ldapurl)

    uri = "%s://%s" % (ldap_url.urlscheme, ldap_url.hostport)

    try:
        con = ldap.initialize(uri)
    except:
        return None

    filter = "(%s=%s)" % (params['key'], params['value'])  # FIXME ESCAPING
    attr = params['attrib']

    try:
        res = con.search_s(ldap_url.dn, ldap.SCOPE_SUBTREE, filter, [ str(attr)] )
    except:
        return "ENOLDAPSEARCH"

    con.unbind()

    for dn, entry in res:
        for a in entry:
            if a.upper() == attr.upper():
                return ''.join(entry[a])    # DECISION: join attribute values?

    return "ldapnotfound"

# ==============================================================
# Redis: GET key
#
#       key=key
#   eg: key=name
#
# cfg:
#   [lookups]
#   redis=redis://localhost:6379/
#
# TODO:
#   Add support for urlparse to use authentication
# --------------------------------------------------------------


def _lookup_redis(params):

    if HAVE_REDIS == False:
        return "ENOREDIS"

    if not 'key' in params:
        return "ENOKEY"

    url = C.redisurl

    # urlsplit on Python 2.6.1 is broken. Hmm. Probably also the reason
    # Redis' from_url() doesn't work here.

    p = '(?P<scheme>[^:]+)://?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'

    try:
        m = re.search(p, url)
        host = m.group('host') 
        port = int(m.group('port'))
    except AttributeError:
        return "EBADURL"

    try:
        conn = redis.Redis(host=host, port=port)
        res = conn.get(params['key'])
        if res is None:
            res = ""
        return res
    except:
        return "ENOREDIS"


# ==============================================================
# ext_lookup: dispatcher

def ext_lookup(type, params):

    func_name = "_lookup_%s" % type

    print "@@@@@@@@@@@@@@--> ", func_name
    print "@@@@@@@@@@@@@@--> ", params

    try:
        result = globals()[func_name](params)
    except:
        raise
        result = "ENOLOOKUPTYPE"

    return result

