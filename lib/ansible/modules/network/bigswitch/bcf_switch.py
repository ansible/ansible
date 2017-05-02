#!/usr/bin/python
# -*- coding: utf-8 -*-

# Ansible module to manage Big Cloud Fabric switches
# (c) 2017, Ted Elhourani <ted@bigswitch.com>
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata-version': '1.0'}

DOCUMENTATION = '''
---
module: bcf_switch
author: "Ted (@tedelhourani)"
short_description: Create and remove a bcf switch.
description:
    - Create and remove a bcf switch.
version_added: "2.4"
options:
  name:
    description:
     - The name of the switch.
    required: true
  fabric_role:
    description:
     - Fabric role of the switch.
    choices: ['spine', 'leaf']
    required: true
  leaf_group:
    description:
     - The leaf group of the switch if the switch is a leaf.
    required: false
  mac:
    description:
     - The MAC address of the switch.
    required: true
  state:
    description:
     - Whether the switch should be present or absent.
    default: present
    choices: ['present', 'absent']
  controller:
    description:
     - The controller IP address.
    required: true
  validate_certs:
    description:
      - If C(false), SSL certificates will not be validated. This should only be used
        on personally controlled devices using self-signed certificates.
    required: false
    default: true
    choices: [true, false]
  access_token:
    description:
     - Big Cloud Fabric access token. If this isn't set then the environment variable C(BIGSWITCH_ACCESS_TOKEN) is used.
'''


EXAMPLES = '''
- name: bcf leaf switch
  bcf_switch:
    name: Rack1Leaf1
    fabric_role: leaf
    leaf_group: R1
    mac: 00:00:00:02:00:02
    controller: '{{ inventory_hostname }}'
    state: present
    validate_certs: false
'''


RETURN = '''
{
    "changed": true,
    "invocation": {
        "module_args": {
            "access_token": null,
            "controller": "192.168.86.230",
            "fabric_role": "leaf",
            "leaf_group": "R1",
            "mac": "00:00:00:02:00:02",
            "name": "Rack1Leaf1",
            "state": "present",
            "validate_certs": false
        }
    }
}
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.bigswitch_utils import Rest, Response
from ansible.module_utils.pycompat24 import get_exception


def leaf_switch(module):
    try:
        access_token = module.params['access_token'] or os.environ['BIGSWITCH_ACCESS_TOKEN']
    except KeyError:
        e = get_exception()
        module.fail_json(msg='Unable to load %s' % e.message)

    name = module.params['name']
    fabric_role = module.params['fabric_role']
    leaf_group = module.params['leaf_group']
    dpid = '00:00:' + module.params['mac']
    state = module.params['state']
    controller = module.params['controller']

    rest = Rest(module,
                {'content-type': 'application/json', 'Cookie': 'session_cookie=' + access_token},
                'https://' + controller + ':8443/api/v1/data/controller/core')

    response = rest.get('switch-config', data={})
    if response.status_code != 200:
        module.fail_json(msg="failed to obtain existing switch config: {}".format(response.json['description']))

    config_present = False
    for switch in response.json:
        if all((switch['name'] == name,
                switch['fabric-role'] == fabric_role,
                switch['dpid'] == dpid)):
            config_present = switch.get('leaf-group', None) == leaf_group
            if config_present:
                break

    if state in ('present') and config_present:
        module.exit_json(changed=False)

    if state in ('absent') and not config_present:
        module.exit_json(changed=False)

    if state in ('present'):
        data = {'name': name, 'fabric-role': fabric_role, 'leaf-group': leaf_group, 'dpid': dpid}
        response = rest.put('switch-config[name="%s"]' % name, data)
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="error configuring switch '{}': {}".format(name, response.json['description']))

    if state in ('absent'):
        response = rest.delete('switch-config[name="%s"]' % name, data={})
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="error deleting switch '{}': {}".format(name, response.json['description']))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            fabric_role=dict(choices=['spine', 'leaf'], required=True),
            leaf_group=dict(type='str', required=False),
            mac=dict(type='str', required=True),
            controller=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present'),
            validate_certs=dict(type='bool', default='True'),
            access_token=dict(type='str', no_log=True)
        )
    )

    try:
        leaf_switch(module)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
