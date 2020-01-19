#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ios_acl
version_added: "2.9"
author:
    - "Federico Olivieri (@Federico87)"
short_description: Manage ACLs on Cisco IOS device
description:
    - This module allows you to create and delete ACLs on Cisco IOS device.
options:
    parent:
        description:
            - Name of the parent ACL.
        required: true
    type:
        description:
            - Type of ACL (extended, standard, etc.). Only extended is supported in this version.
        default: extended
        choices: ['extended']
    number:
        description:
            - ACL line number.
        required: true
    status:
        description:
            - ACL permit or deny traffic.
        choices: ['permit', 'deny']
        default: permit
    protocol:
        description:
            - ACL protocol.
        choices: ['tcp', 'udp', 'ip']
        required: true
    spurce:
        description:
            - ACL source IP.
        required: true
    destination:
        description:
            - ACL destination IP.
        required: true
    dst_port:
        description:
            - ACL destination port.
    logging:
        description:
            - ACL logging enabled.
        type: bool
        default: False
        choices: [True, False]
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present', 'absent']
"""

EXAMPLES = """
---
- name: add new line to MY_TEST ACL.
  ios_acl:
    paren: MY_TEST
    type: extended
    number: 50
    status: permit
    protocol: tcp
    source: 192.168.90.0 0.0.0.255
    destination: 10.74.254.0 0.0.0.255
    dst_port: gt 1023
    logging: false
    state: present

- name: remove existing line from MY_TEST ACL.
  ios_acl:
    paren: MY_TEST
    type: extended
    number: 10
    status: deny
    protocol: udp
    source: 192.168.90.0 0.0.0.255
    dst_port: dns
    destination: host 8.8.8.8
    logging: false
    state: absent
"""

RETURN = """
commands:
  description: command sent to the device
  returned: always
  type: list
  sample: [
    "ip access-list extended MY_TEST",
    "50 permit tcp 192.168.90.0 0.0.0.255 10.74.254.0 0.0.0.255 gt 1023",
    "ip access-list extended MY_TEST",
    "no 10 deny udp 192.168.90.0 0.0.0.255 host 8.8.8.8 dns",
    ]
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ios.ios import run_commands, load_config
from ansible.module_utils.network.ios.ios import ios_argument_spec


class Parser():
    def __init__(self, sh_acl):
        self.sh_acl = sh_acl


    def parse_acl_name(self):
        have_acl_name = self.sh_acl[0].splitlines()[0].split()[-1]

        return have_acl_name


    def parse_acl_type(self):
        have_acl_type = self.sh_acl[0].splitlines()[0].split()[0]

        return have_acl_type


def map_params_to_obj(module):
    obj = {
        'parent': module.params['parent'],
        'type': module.params['type'],
        'number': module.params['number'],
        'status': module.params['status'],
        'protocol': module.params['protocol'],
        'source': module.params['source'],
        'destination': module.params['destination'],
        'dst_port': module.params['dst_port'],
        'logging': module.params['logging'],
    }

    parent_want = 'ip access-list {type} {parent}'.format(
        type=obj['type'],
        parent=obj['parent'],
    )

    line_want = '{number} {status} {protocol} {source} {destination} {dst_port} {logging}'.format(
        number=obj['number'],
        status=obj['status'],
        protocol=obj['protocol'],
        source=obj['source'],
        destination=obj['destination'],
        dst_port=''.join([obj.get('dst_port') if obj.get('dst_port') else '']).rstrip(),
        logging=''.join(['log' if obj.get('logging') else '']).rstrip(),
    )

    return parent_want, line_want


def map_config_to_obj(module):

    sh_acl = run_commands(module, commands=['show access-list {}'.format(module.params['parent'])])
    parser_have = Parser(sh_acl)
    type_have = parser_have.parse_acl_type()
    parent_have = parser_have.parse_acl_name()

    parent_have = 'ip access-list {type} {parent}'.format(
        type=type_have.lower(),
        parent=parent_have,
    )
    lines_have = [ line.lstrip().rstrip() for line in sh_acl[0].splitlines()[1:] ]

    return parent_have, lines_have


def map_obj_to_commands(module, want, have):

    commands = list()

    state = module.params['state']
    parent_want = want[0]
    parent_have = have[0]
    line_want = want[1]
    lines_have = have[1]

    if state == 'present':
        if parent_have == parent_want:
            if line_want.rstrip() not in lines_have:
                commands.append(parent_want)
                commands.append(line_want)

    if state == 'absent':
        if parent_have == parent_want:
            if line_want.rstrip() in lines_have:
                commands.append(parent_want)
                commands.append('no ' + line_want)

    return commands


def main():

    argument_spec = dict(
        parent=dict(required=True),
        type=dict(choise=['extended'], default='extended'),
        number=dict(required=True),
        status=dict(choise=['permit', 'deny'], default='permit'),
        protocol=dict(required=True, choise=['tcp', 'udp', 'ip']),
        source=dict(required=True),
        destination=dict(required=True),
        dst_port=dict(required=True),
        logging=dict(type='bool', default=False),
        state=dict(choices=['present', 'absent'], default='present')
    )

    argument_spec.update(ios_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands(module, want, have)

    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
