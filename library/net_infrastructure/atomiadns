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
  command:
    choices: ['AddDnsRecords', 'AddNameserver', 'AddZone', 'DeleteNameserver', 'DeleteZone', 'EditZone', 'GetAllZones', 'GetDnsRecords', 'GetLabels', 'GetNameserver', 'GetZone', 'ReloadAllZones']
    description: The name of the action you wish to execute. Allowed commands are AddDnsRecords, AddNameserver, AddZone, DeleteNameserver, DeleteZone, EditZone, GetAllZones, GetDnsRecords, GetLabels, GetNameserver, GetZone, ReloadAllZones
    required: true
  expire:
    description: the SOA expire field
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
"""
EXAMPLES = """
# get all zones:
action: atomiadns command=GetAllZones user=jochen@sejo-it.be password=test
# get labels for zone sejo-it.be
action: atomiadns command=GetLabels user=jochen@sejo-it.be password=test zone=sejo-it.be
"""


def main():
    command_required_param_map = dict(
        AddDnsRecords=('zone', 'records'),
        AddNameserver=('nameserver', 'nameservergroup'),
        AddZone=('zonename', 'zonettl', 'mname', 'rname', 'refresh', 'retry', 'expire', 'minimum', 'nameservers',
                 'nameservergroup'),
        DeleteNameserver=('nameserver',),
        DeleteZone=('zone',),
        EditZone=('zonename', 'zonettl', 'mname', 'rname', 'refresh', 'retry', 'expire', 'minimum', 'nameservers',
                  'nameservergroup'),
        GetAllZones=(),
        GetDnsRecords=('zone', 'label'),
        GetLabels=('zone',),
        GetNameserver=('nameserver'),
        GetZone=('zone',),
        ReloadAllZones=())

    module = AnsibleModule(
        argument_spec=dict(
            command=dict(default=None, required=True, choices=command_required_param_map.keys()),
            user=dict(default=None, required=True),
            password=dict(default=None, required=True),
            url=dict(default=None, required=True),
            expire=dict(default=None, required=False),
            label=dict(default=None, required=False),
            minimum=dict(default=None, required=False),
            mname=dict(default=None, required=False),
            nameservergroup=dict(default=None, required=False),
            nameservers=dict(default=None, required=False),
            records=dict(default=None, required=False),
            rname=dict(default=None, required=False),
            refresh=dict(default=None, required=False),
            retry=dict(default=None, required=False),
            zone=dict(default=None, required=False),
            zonename=dict(default=None, required=False),
            zonettl=dict(default=None, required=False),
        )
    )

    #fetch all required params first
    command = module.params['command']
    user = module.params['user']
    password = module.params['password']
    url = module.params['url']

    # create the atomiaclient
    client = AtomiaClient(url, user, password)

    args = dict()
    # Here we will run over all the required arguments for the command given.
    for param in command_required_param_map.get(command):
        # if the argument is not found, error.
        if not module.params[param]:
            module.fail_json(msg='%s param is required for command=%s' % (param, command))
        else:
            # a bit specific, for nameservers we need to provide a list, but I choose to provide a comma separated
            # string. This would make it much easier to do from commandline
            if param == 'nameservers':
                args[param] = module.params[param].split(',')
            # for records we need a json string that has all the needed params (see docs)
            elif param == 'records':
                args[param] = json.loads(module.params[param])
            else:
                args[param] = module.params[param]
    changed = False
    # getattr is a function that allows me to get the attribute or method of an object.
    # thus getattr(client, command), means give me the method that has the same name of the value of command
    # for the client object.
    # the (**args) behind it mean that the method should be invoked at once with the keyword argument list
    # that is constructed in args.
    # the reason why we use getattr is to avoid long if clauses that run client.<command>, this could
    # possibly lead to more bugs as more code is needed.
    retval = getattr(client, command)(**args)
    ret = json.loads(retval)
    if 'error_message' in ret:
        module.fail_json(changed=changed, msg=ret, cmd=command)
    else:
        changed = True
        module.exit_json(changed=changed, out=ret, cmd=command)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
