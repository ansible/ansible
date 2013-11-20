#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) 2013, Jochen Maes <jochen@sejo-it.be>
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
import json
from pyatomiadns.client import AtomiaClient

DOCUMENTATION = """
---
module: atomiadns
short_description: Manages the atomiadns entries with pyatomiadns
description:
  - Manages your atomiadns servers with help of the pyatomiadns package. You should have pyatomiadns installed.
version_added: "1.0"
author: Jochen Maes
notes:
  - "Requires a functional AtomiaDNS installation"
  - "Requires pyatomiadns to be installed (https://github.com/sejo/pyatomiadns), you can install with pip install pyatomiadns
requirements:
  - pyatomiadns
options:
  activated:
    description: yes or no, whether or not the key is activated (used with dnssec_key)
    required: false
  algorithm:
    description: Algorithm for the key to be added (used with dnssec_key)
    required: false
  command:
    choices: ['dns_records', 'nameserver', 'nameserver_group', 'dnssec_key', 'zone', 'account', 'get_all_zones', 'get_dns_records', 'get_labels', 'get_nameserver', 'get_zone', 'reload_all_zones']
    description: The name of the action you wish to execute. Allowed commands are records, nameserver, nameserver_group, dnssec_key, zone, get_all_zones, get_dns_records, get_labels, get_nameserver, get_zone, reload_all_zones, account
    required: true
  email:
    description: SOAP username to be added/removed (only used with account command)
    required: false
  expire:
    description: the SOA expire field
    required: false
  groupname:
    description: name of the nameserver group
    required: false
  keysize:
    description: The size of the key (ex: KSK 2048, ZSK 1024) (used with dnssec_key)
    required: false
  keytype:
    description: The type of the key (ex: KSK, ZSK) (used with dnssec_key)
    required: false
  label:
    description: string defining the label ('@', 'www', 'ns')
    required: false
  minimum:
    description: integer the SOA minimum field
    required: false
  mname:
    description: string the SOA mname field
    required: false
  nameserver:
    description: related nameserver
    required: false
  nameservergroup:
    description: string stating which nameservergroup the action relates to
    required: false
  nameservers:
    description: a comma separated list the hostnames of the nameservers for the zone ("dns1.example.org,dns2.example.org")
    required: false
  password:
    description: password for the atomiadns soap api
    required: true
  password_soap:
    description: password for the user you want to create (only used with account command)
    required: false
  records:
    description: a dict containing all zones ({ "ttl”: "3600”, "label” : "@”, "class” : "IN”, "type” : "A”, "rdata” : "192.168.0.1” })
    required: false
  refresh:
    description: The SOA refresh field
    required: false
  retry:
    description: The SOA retry field
    required: false
  rname:
    description: The SOA rname field
    required: false
  user:
    description: username for the atomiadns soap api (beware some actions require admin user!)
    required: true
  url:
    description: URL to the soap api
    required: true
  zone:
    description: string defining the zone to use (example.org, sejo-it.be)
    required: false
  zonename:
    description: the name of the related zone
    required: false
  zonettl:
    description: the ttl of the related zone
    required: false
  state:
    description: present or absent
    required: false
"""
EXAMPLES = """
# get all zones:
action: atomiadns command=get_all_zones user=jochen@sejo-it.be password=test
# get labels for zone sejo-it.be
action: atomiadns command=get_labels user=jochen@sejo-it.be password=test zone=sejo-it.be
"""


def main():
    command_required_param_map = dict(
        account=('email', 'state'),
        dnssec_key=('algorithm', 'keysize', 'keytype', 'activated', 'state'),
        dns_records=('zone', 'records', 'state'),
        get_all_zones=(),
        get_dns_records=('zone', 'label'),
        get_labels=('zone',),
        get_nameserver=('nameserver'),
        get_zone=('zone',),
        nameserver=('nameserver', 'state'),
        nameserver_group=('groupname', 'state'),
        reload_all_zones=(),
        zone=('zonename', 'state'),
    )

    module = AnsibleModule(
        argument_spec=dict(
            activated=dict(default=None, required=False),
            algorithm=dict(default=None, required=False),
            command=dict(default=None, required=True, choices=command_required_param_map.keys()),
            email=dict(default=None, required=False),
            expire=dict(default=None, required=False),
            groupname=dict(default=None, required=False),
            keysize=dict(default=None, required=False),
            keytype=dict(default=None, required=False),
            label=dict(default=None, required=False),
            minimum=dict(default=None, required=False),
            mname=dict(default=None, required=False),
            nameservergroup=dict(default=None, required=False),
            nameservers=dict(default=None, required=False),
            password=dict(default=None, required=True),
            password_soap=dict(default=None, required=False),
            records=dict(default=None, required=False),
            rname=dict(default=None, required=False),
            refresh=dict(default=None, required=False),
            retry=dict(default=None, required=False),
            state=dict(default=None, required=False),
            url=dict(default=None, required=True),
            user=dict(default=None, required=True),
            zone=dict(default=None, required=False),
            zonename=dict(default=None, required=False),
            zonettl=dict(default=None, required=False),
        )
    )
    convert = {
        'account': 'AddAccount',
        'dnssec_key': 'AddDNSSECKey',
        'dns_records': 'AddDnsRecords',
        'get_all_zones': 'GetAllZones',
        'get_dns_records': 'GetDnsRecords',
        'get_labels': 'GetLabels',
        'get_nameserver': 'GetNameserver',
        'get_zone': 'GetZone',
        'nameserver': 'AddNameserver',
        'nameserver_group': 'AddNameserverGroup',
        'reload_all_zones': 'ReloadAllZones',
        'zone': 'AddZone',
    }
    #fetch all required params first
    raw_command = module.params['command']
    command = convert[raw_command]
    user = module.params['user']
    password = module.params['password']
    url = module.params['url']

    # create the atomiaclient
    client = AtomiaClient(url, user, password)

    args = dict()
    # Here we will run over all the required arguments for the command given.
    for param in command_required_param_map[raw_command]:
        # if the argument is not found, error.
        if not module.params[param]:
            module.fail_json(msg='%s param is required for command=%s' % (param, raw_command))
        else:
            if param == 'state':
                #ignore this one
                continue
                # a bit specific, for nameservers we need to provide a list, but I choose to provide a comma separated
            # string. This would make it much easier to do from commandline
            if param == 'nameservers':
                args[param] = module.params[param].split(',')
            # for records we need a json string that has all the needed params (see docs)
            elif param == 'records':
                rlist = list()
                records = module.params[param]
                if isinstance(records, list):
                    for jstr in module.params[param]:
                        rlist.append(json.loads(jstr))
                    args[param] = rlist
                else:
                    args[param] = json.loads(records)
            elif param == 'keysize':
                args[param] = int(module.params[param])
            else:
                args[param] = module.params[param]
    changed = False
    if command == "AddZone":
        if module.params['state'] == 'present':
            # here it might be an edit, so first check if zone exists
            retval = getattr(client, 'GetZone')(module.params['zonename'])
            ret = json.loads(retval)
            if 'error_message' in ret:
                # zone does not exist:
                # add the zone
                command = 'AddZone'
            for param in ('zonettl', 'mname', 'rname', 'refresh', 'retry', 'expire', 'minimum', 'nameservers',
                          'nameservergroup'):
                if param == 'nameservers':
                    args[param] = module.params[param].split(',')
                else:
                    args[param] = module.params[param]
        else:
            command = 'DeleteZone'
    elif command == 'AddNameserver':
        if module.params['state'] == 'absent':
            command = 'DeleteNameserver'
        else:
            args['nameservergroup'] = module.params['nameservergroup']
    elif command == 'AddDnsRecords' and module.params['state'] == 'absent':
        command = 'DeleteDnsRecords'
        rlist = list()
        for rec  in args['records']:
            retval = client.GetDnsRecords(args['zone'], rec['label'])
            ret = json.loads(retval)
            if ret:
                rlist.append(ret[0])
        args['records'] = rlist

    elif command == 'AddDNSSECKey':
        if args['activated'] in ('yes', 'true', 'True', 'YES'):
            args['activated'] = 1
        else:
            args['activated'] = 0
        if module.params['state'] == 'absent':
            command = 'DeleteDNSSecKey'
    elif command == 'AddNameserverGroup' and module.params['state'] == 'absent':
        command = 'DeleteNameserverGroup'
    elif command == 'AddAccount':
        if module.params['state'] == 'absent':
            command = 'DeleteAccount'
        else:
            args['password_soap'] = module.params['password_soap']

    retval = getattr(client, command)(**args)
    # getattr is a function that allows me to get the attribute or method of an object.
    # thus getattr(client, command), means give me the method that has the same name of the value of command
    # for the client object.
    # the (**args) behind it mean that the method should be invoked at once with the keyword argument list
    # that is constructed in args.
    # the reason why we use getattr is to avoid long if clauses that run client.<command>, this could
    # possibly lead to more bugs as more code is needed.
    ret = json.loads(retval)
    if 'error_message' in ret:
        module.fail_json(changed=changed, msg=ret, cmd=command)
    else:
        changed = True
        module.exit_json(changed=changed, out=ret, cmd=command)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
