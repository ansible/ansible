#!/usr/bin/python

import json
from ipalib import api
api.bootstrap(context='cli')
api.finalize()
api.Backend.xmlclient.connect()    
inventory = {}
hostvars={}
meta={}
result =api.Command.hostgroup_find()['result']
for hostgroup in result:
    inventory[hostgroup['cn'][0]] = { 'hosts': [host for host in  hostgroup['member_host']]}
    for host in  hostgroup['member_host']:
        hostvars[host] = {}
inventory['_meta'] = {'hostvars': hostvars}
inv_string = json.dumps( inventory)
print inv_string

