#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ted Elhourani <ted@bigswitch.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: bcf_switch
author: "Ted (@tedelhourani)"
short_description: Create and remove a bcf switch.
description:
    - Create and remove a Big Cloud Fabric switch.
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
    type: bool
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


RETURN = ''' # '''

import os
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.bigswitch.bigswitch import Rest
from ansible.module_utils._text import to_native


def switch(module, check_mode):
    try:
        access_token = module.params['access_token'] or os.environ['BIGSWITCH_ACCESS_TOKEN']
    except KeyError as e:
        module.fail_json(msg='Unable to load %s' % e.message, exception=traceback.format_exc())

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

    if check_mode:
        module.exit_json(changed=True)

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
        ),
        supports_check_mode=True,
    )

    try:
        switch(module, check_mode=module.check_mode)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
