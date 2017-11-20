#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ironware_vlan
version_added: "2.5"
author: "Paul Baker (@paulquack)"
short_description: Manage VLANs on Brocade Ironware devices
description:
  - This module provides declarative management of VLANs
    on Brocade Ironware devices.
extends_documentation_fragment: ironware
options:
  name:
    description:
      - Name of the VLAN.
  vlan_id:
    description:
      - ID of the VLAN.
    required: true
  interfaces:
    description:
      - List of interfaces that should be associated to the VLAN.
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
"""

EXAMPLES = """
- name: Create vlan
  ironware_vlan:
    vlan_id: 4000
    name: vlan-4000
    state: present

- name: Add interfaces to vlan
  ironware_vlan:
    vlan_id: 4000
    state: present
    interfaces:
      - 1/1
      - 2/5

- name: Create aggregate of vlans
  ironware_vlan:
    aggregate:
      - vlan_id: 4000
      - {vlan_id: 4001, name: vlan-4001}
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - vlan 20
    - name test-vlan
"""
import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network_common import remove_default_spec
from ansible.module_utils.ironware import load_config, run_commands
from ansible.module_utils.ironware import ironware_argument_spec, check_args


def search_obj_in_list(vlan_id, lst):
    for o in lst:
        if o['vlan_id'] == vlan_id:
            return o


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:

        obj_in_have = search_obj_in_list(w['vlan_id'], have)

        if w['state'] == 'absent':
            if obj_in_have:
                commands.append('no vlan %s' % w['vlan_id'])
        elif w['state'] == 'present':
            if not obj_in_have:
                if w['name']:
                    commands.append('vlan %s name %s' % (w['vlan_id'], w['name']))
                else:
                    commands.append('vlan %s' % w['vlan_id'])

                if w['interfaces']:
                    for i in w['interfaces']:
                        commands.append('untagged ethe %s' % i)
            else:
                if w['name'] and w['name'] != obj_in_have['name']:
                    commands.append('vlan %s name %s' % (w['vlan_id'], w['name']))

                if w['interfaces']:
                    if not obj_in_have['interfaces']:
                        for i in w['interfaces']:
                            commands.append('vlan %s' % w['vlan_id'])
                            commands.append('untagged ethe %s' % i)
                    elif set(w['interfaces']) != obj_in_have['interfaces']:
                        missing_interfaces = list(set(w['interfaces']) - set(obj_in_have['interfaces']))
                        for i in missing_interfaces:
                            commands.append('vlan %s' % w['vlan_id'])
                            commands.append('untagged ethe %s' % i)

                        superfluous_interfaces = list(set(obj_in_have['interfaces']) - set(w['interfaces']))
                        for i in superfluous_interfaces:
                            commands.append('vlan %s' % w['vlan_id'])
                            commands.append('no untagged ethe %s' % i)

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['vlan_id'], want)
            if not obj_in_want and h['vlan_id'] != '1':
                commands.append('no vlan %s' % h['vlan_id'])

    return commands


def map_config_to_obj(module):
    parsed = dict()
    output = run_commands(module, ['show vlan detail'])
    key = None
    for line in output[0].strip().splitlines():
        if not line:
            continue
        match = re.match(r'^PORT-VLAN ([^\s,]+)', line)
        if key and not match:
            parsed[key] += '\n%s' % line
        elif match:
            key = match.group(1)
            parsed[key] = line

    objs = list()
    for key, value in parsed.iteritems():
        value = value.strip().splitlines()
        obj = dict()
        obj['vlan_id'] = key
        match = re.match(r'Name ([^\s,]+)', value[0])
        if match and match.group(1) != '[None]':
            obj['name'] == match.group(1)
        else:
            obj['name'] = None
        obj['state'] = 'active'

        obj['interfaces'] = list()
        for l in value:
            match = re.match(r'^(\d+\/\d+)\s+[A-Z]+\s+(TAGGED|UNTAGGED)\s+', l)
            if match:
                obj['interfaces'].append(match.group(1))

        objs.append(obj)

    return objs


def map_params_to_obj(module):
    obj = list()
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            d['vlan_id'] = str(d['vlan_id'])

            obj.append(d)
    else:
        obj.append({
            'vlan_id': str(module.params['vlan_id']),
            'name': module.params['name'],
            'state': module.params['state'],
            'interfaces': module.params['interfaces']
        })

    return obj


def check_declarative_intent_params(want, module):
    if module.params['interfaces']:
        time.sleep(module.params['delay'])
        have = map_config_to_obj(module)

        for w in want:
            for i in w['interfaces']:
                obj_in_have = search_obj_in_list(w['vlan_id'], have)

                if obj_in_have and 'interfaces' in obj_in_have and i not in obj_in_have['interfaces']:
                    module.fail_json(msg="Interface %s not configured on vlan %s" % (i, w['vlan_id']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        vlan_id=dict(type='int'),
        name=dict(),
        interfaces=dict(type='list'),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['vlan_id'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(ironware_argument_spec)

    required_one_of = [['vlan_id', 'aggregate']]
    mutually_exclusive = [['vlan_id', 'aggregate']]
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive)

    check_args(module)

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        # send the configuration commands to the device and merge
        # them with the current running config
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    if result['changed']:
        if not module.check_mode:
            cmd = {'command': 'write memory'}
            run_commands(module, [cmd])

    if result['changed']:
        check_declarative_intent_params(want, module)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
