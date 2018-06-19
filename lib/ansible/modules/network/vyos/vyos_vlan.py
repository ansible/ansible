#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: vyos_vlan
version_added: "2.5"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage VLANs on VyOS network devices
description:
  - This module provides declarative management of VLANs
    on VyOS network devices.
notes:
  - Tested against VYOS 1.1.7
options:
  name:
    description:
      - Name of the VLAN.
  address:
    description:
      - Configure Virtual interface address.
  vlan_id:
    description:
      - ID of the VLAN. Range 0-4094.
    required: true
  interfaces:
    description:
      - List of interfaces that should be associated to the VLAN.
    required: true
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for given vlan C(name)
        for associated interfaces. If the value in the C(associated_interfaces) does not match with
        the operational state of vlan on device it will result in failure.
    version_added: "2.5"
  delay:
    description:
      - Delay the play should wait to check for declarative intent params values.
    default: 10
  aggregate:
    description: List of VLANs definitions.
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: vyos
"""

EXAMPLES = """
- name: Create vlan
  vyos_vlan:
    vlan_id: 100
    name: vlan-100
    interfaces: eth1
    state: present

- name: Add interfaces to VLAN
  vyos_vlan:
    vlan_id: 100
    interfaces:
      - eth1
      - eth2

- name: Configure virtual interface address
  vyos_vlan:
    vlan_id: 100
    interfaces: eth1
    address: 172.26.100.37/24

- name: vlan interface config + intent
  vyos_vlan:
    vlan_id: 100
    interfaces: eth0
    associated_interfaces:
    - eth0

- name: vlan intent check
  vyos_vlan:
    vlan_id: 100
    associated_interfaces:
    - eth3
    - eth4

- name: Delete vlan
  vyos_vlan:
    vlan_id: 100
    interfaces: eth1
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - set interfaces ethernet eth1 vif 100 description VLAN 100
    - set interfaces ethernet eth1 vif 100 address 172.26.100.37/24
    - delete interfaces ethernet eth1 vif 100
"""
import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.vyos.vyos import load_config, run_commands
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


def search_obj_in_list(vlan_id, lst):
    obj = list()
    for o in lst:
        if o['vlan_id'] == vlan_id:
            obj.append(o)
    return obj


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:
        vlan_id = w['vlan_id']
        name = w['name']
        address = w['address']
        state = w['state']
        interfaces = w['interfaces']

        obj_in_have = search_obj_in_list(vlan_id, have)

        if state == 'absent':
            if obj_in_have:
                for obj in obj_in_have:
                    for i in obj['interfaces']:
                        commands.append('delete interfaces ethernet {0} vif {1}'.format(i, vlan_id))

        elif state == 'present':
            if not obj_in_have:
                if w['interfaces'] and w['vlan_id']:
                    for i in w['interfaces']:
                        cmd = 'set interfaces ethernet {0} vif {1}'.format(i, vlan_id)
                        if w['name']:
                            commands.append(cmd + ' description {}'.format(name))
                        elif w['address']:
                            commands.append(cmd + ' address {}'.format(address))
                        else:
                            commands.append(cmd)

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['vlan_id'], want)
            if not obj_in_want:
                for i in h['interfaces']:
                    commands.append('delete interfaces ethernet {0} vif {1}'.format(i, h['vlan_id']))

    return commands


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()

            if not d['vlan_id']:
                module.fail_json(msg='vlan_id is required')

            d['vlan_id'] = str(d['vlan_id'])
            module._check_required_one_of(module.required_one_of, item)

            obj.append(d)
    else:
        obj.append({
            'vlan_id': str(module.params['vlan_id']),
            'name': module.params['name'],
            'address': module.params['address'],
            'state': module.params['state'],
            'interfaces': module.params['interfaces'],
            'associated_interfaces': module.params['associated_interfaces']
        })

    return obj


def map_config_to_obj(module):
    objs = []
    interfaces = list()

    output = run_commands(module, 'show interfaces')
    lines = output[0].strip().splitlines()[3:]

    for l in lines:
        splitted_line = re.split(r'\s{2,}', l.strip())
        obj = {}

        eth = splitted_line[0].strip("'")
        if eth.startswith('eth'):
            obj['interfaces'] = []
            if '.' in eth:
                interface = eth.split('.')[0]
                obj['interfaces'].append(interface)
                obj['vlan_id'] = eth.split('.')[-1]
            else:
                obj['interfaces'].append(eth)
                obj['vlan_id'] = None

            if splitted_line[1].strip("'") != '-':
                obj['address'] = splitted_line[1].strip("'")

            if len(splitted_line) > 3:
                obj['name'] = splitted_line[3].strip("'")
            obj['state'] = 'present'
            objs.append(obj)

    return objs


def check_declarative_intent_params(want, module, result):

    have = None
    obj_interface = list()
    is_delay = False

    for w in want:
        if w.get('associated_interfaces') is None:
            continue

        if result['changed'] and not is_delay:
            time.sleep(module.params['delay'])
            is_delay = True

        if have is None:
            have = map_config_to_obj(module)

        obj_in_have = search_obj_in_list(w['vlan_id'], have)
        if obj_in_have:
            for obj in obj_in_have:
                obj_interface.extend(obj['interfaces'])

    for w in want:
        if w.get('associated_interfaces') is None:
            continue
        for i in w['associated_interfaces']:
            if (set(obj_interface) - set(w['associated_interfaces'])) != set([]):
                module.fail_json(msg='Interface {0} not configured on vlan {1}'.format(i, w['vlan_id']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        vlan_id=dict(type='int'),
        name=dict(),
        address=dict(),
        interfaces=dict(type='list'),
        associated_interfaces=dict(type='list'),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(vyos_argument_spec)

    required_one_of = [['vlan_id', 'aggregate'],
                       ['aggregate', 'interfaces', 'associated_interfaces']]

    mutually_exclusive = [['vlan_id', 'aggregate']]
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive)

    warnings = list()
    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        load_config(module, commands, commit=commit)
        result['changed'] = True

    check_declarative_intent_params(want, module, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
