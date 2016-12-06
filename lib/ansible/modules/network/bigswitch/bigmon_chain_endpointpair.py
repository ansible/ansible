#!/usr/bin/python
# -*- coding: utf-8 -*-

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
DOCUMENTATION = '''
---
module: bigmon_chain_endpointpair
short_description: add/delete bigmon inline service chain endpoints (interfaces)
description:
    - add/delete bigmon inline service chain endpoints (interfaces).
version_added: "2.3"
options:
  name:
    description:
     - The name of the chain.
    required: true
  switch:
    description:
     - The datapath id the switch.
    required: true
  endpoint1:
    description:
     - The first interface of the chain.
    required: true
  endpoint2:
    description:
     - The second interface of the chain.
    required: true
  state:
    description:
     - Whether the service chain endpointpair should be present or absent.
    default: present
    choices: ['present', 'absent']
  access_token:
    description:
     - Bigmon access token.

notes:
  - An environment variable can be used, BIGSWITCH_ACCESS_TOKEN.

requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
    - name: bigmon inline service chain endpointpair
      bigmon_chain_endpointpair:
        name: MyChain
        endpoint1: ethernet1
        endpoint2: ethernet2
        switch: 00:00:00:00:00:00:00:0b
        controller: '{{ inventory_hostname }}'
        state: present
'''


RETURN = '''
{
    "changed": true,
    "invocation": {
        "module_args": {
            "access_token": null,
            "controller": "192.168.86.221",
            "endpoint1": "ethernet1",
            "endpoint2": "ethernet2",
            "name": "MyChain",
            "state": "present",
            "switch": "00:00:00:00:00:00:00:0b",
            "validate_certs": false
        },
        "module_name": "bigmon_chain_endpointpair"
    }
}
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.bigswitch_utils import Rest, Response
from ansible.module_utils.pycompat24 import get_exception

def endpointpair(module):
    try:
        access_token = module.params['access_token'] or os.environ['BIGSWITCH_ACCESS_TOKEN']
    except KeyError:
        e = get_exception()
        module.fail_json(msg='Unable to load %s' % e.message )

    name = module.params['name']
    switch = module.params['switch']
    endpoint1 = module.params['endpoint1']
    endpoint2 = module.params['endpoint2']
    state = module.params['state']
    controller = module.params['controller']

    rest = Rest(module,
                {'content-type': 'application/json', 'Cookie': 'session_cookie='+access_token},
                'https://'+controller+':8443/api/v1/data/controller/applications/bigchain')

    if None in (name, switch, endpoint1, endpoint2):
        module.fail_json(msg='parameter `name` is missing')

    response = rest.get('chain?config=true', data={})
    if response.status_code != 200:
        module.fail_json(msg="failed to obtain existing chain config: {}".format(response.json['description']))

    target = {"endpoint1":endpoint1, "endpoint2":endpoint2, "switch":switch}
    config_present = False
    for chain in response.json:
        if chain['name'] == name and 'endpoint-pair' in chain:
            if all(item in chain['endpoint-pair'].items() for item in target.items()):
                config_present = True
                break
    
    if state in ('present') and config_present:
        module.exit_json(changed=False)

    if state in ('absent') and not config_present:
        module.exit_json(changed=False)
        
    if state in ('present'):
        response = rest.put('chain[name="%s"]/endpoint-pair' % name, data=target)
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="error creating endpoint-pair '{}': {}".format(name, response.json['description']))

    if state in ('absent'):
        response = rest.delete('chain[name="%s"]/endpoint-pair' % name, data={})
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="error deleting endpoint-pair '{}': {}".format(name, response.json['description']))

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            switch=dict(type='str', required=True),
            endpoint1=dict(type='str', required=True),
            endpoint2=dict(type='str', required=True),
            controller=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present'),
            validate_certs=dict(type='bool', default='False'),
            access_token=dict(aliases=['BIGSWITCH_ACCESS_TOKEN'], no_log=True)
        )
    )

    try:
        endpointpair(module)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
