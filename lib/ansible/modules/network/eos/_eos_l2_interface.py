#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: eos_l2_interface
version_added: "2.5"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage L2 interfaces on Arista EOS network devices.
description:
  - This module provides declarative management of L2 interfaces
    on Arista EOS network devices.
deprecated:
  removed_in: "2.13"
  alternative: eos_l2_interfaces
  why: Updated modules released with more functionality
notes:
  - Tested against EOS 4.15
options:
  name:
    description:
      - Name of the interface
    required: true
    aliases: ['interface']
  mode:
    description:
      - Mode in which interface needs to be configured.
    choices: ['access','trunk']
  access_vlan:
    description:
      - Configure given VLAN in access port.
        If C(mode=access), used as the access VLAN ID.
  native_vlan:
    description:
      - Native VLAN to be configured in trunk port.
        If C(mode=trunk), used as the trunk native VLAN ID.
  trunk_allowed_vlans:
    description:
      - List of allowed VLANs in a given trunk port.
        If C(mode=trunk), these are the ONLY VLANs that will be
        configured on the trunk, i.e. C(2-10,15).
    aliases: ['trunk_vlans']
  aggregate:
    description:
      - List of Layer-2 interface definitions.
  state:
    description:
      - Manage the state of the Layer-2 Interface configuration.
    default:  present
    choices: ['present','absent', 'unconfigured']
extends_documentation_fragment: eos
"""

EXAMPLES = """
- name: Ensure Ethernet1 does not have any switchport
  eos_l2_interface:
    name: Ethernet1
    state: absent

- name: Ensure Ethernet1 is configured for access vlan 20
  eos_l2_interface:
    name: Ethernet1
    mode: access
    access_vlan: 20

- name: Ensure Ethernet1 is a trunk port and ensure 2-50 are being tagged (doesn't mean others aren't also being tagged)
  eos_l2_interface:
    name: Ethernet1
    mode: trunk
    native_vlan: 10
    trunk_allowed_vlans: 2-50

- name: Set switchports on aggregate
  eos_l2_interface:
    aggregate:
      - { name: ethernet1, mode: access, access_vlan: 20}
      - { name: ethernet2, mode: trunk, native_vlan: 10}
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - interface ethernet1
    - switchport access vlan 20
"""
import re
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.eos.eos import get_config, load_config, run_commands
from ansible.module_utils.network.eos.eos import eos_argument_spec


def parse_config_argument(configobj, name, arg=None):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)
    match = re.search(r'%s (.+)$' % arg, cfg, re.M)
    if match:
        return match.group(1).strip()


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def map_obj_to_commands(want, have, module):
    commands = list()

    for w in want:
        name = w['name']
        state = w['state']
        mode = w['mode']
        access_vlan = w['access_vlan']
        native_vlan = w['native_vlan']
        trunk_allowed_vlans = w['trunk_allowed_vlans']

        interface = 'interface ' + name
        commands.append(interface)

        obj_in_have = search_obj_in_list(name, have)
        if not obj_in_have:
            module.fail_json(msg='invalid interface {0}'.format(name))

        if state == 'absent':
            if obj_in_have['mode'] == 'access':
                commands.append('no switchport access vlan {0}'.format(obj_in_have['access_vlan']))

            if obj_in_have['mode'] == 'trunk':
                commands.append('no switchport mode trunk')

            if obj_in_have['native_vlan']:
                commands.append('no switchport trunk native vlan {0}'.format(obj_in_have['native_vlan']))

            if obj_in_have['trunk_allowed_vlans']:
                commands.append('no switchport trunk allowed vlan {0}'.format(obj_in_have['trunk_allowed_vlans']))

            if obj_in_have['state'] == 'present':
                commands.append('no switchport')
        else:
            if obj_in_have['state'] == 'absent':
                commands.append('switchport')
                commands.append('switchport mode {0}'.format(mode))

                if access_vlan:
                    commands.append('switchport access vlan {0}'.format(access_vlan))

                if native_vlan:
                    commands.append('switchport trunk native vlan {0}'.format(native_vlan))

                if trunk_allowed_vlans:
                    commands.append('switchport trunk allowed vlan {0}'.format(trunk_allowed_vlans))
            else:
                if mode != obj_in_have['mode']:
                    if obj_in_have['mode'] == 'access':
                        commands.append('no switchport access vlan {0}'.format(obj_in_have['access_vlan']))
                        commands.append('switchport mode trunk')
                        if native_vlan:
                            commands.append('switchport trunk native vlan {0}'.format(native_vlan))
                        if trunk_allowed_vlans:
                            commands.append('switchport trunk allowed vlan {0}'.format(trunk_allowed_vlans))
                    else:
                        if obj_in_have['native_vlan']:
                            commands.append('no switchport trunk native vlan {0}'.format(obj_in_have['native_vlan']))
                            commands.append('no switchport mode trunk')
                        if obj_in_have['trunk_allowed_vlans']:
                            commands.append('no switchport trunk allowed vlan {0}'.format(obj_in_have['trunk_allowed_vlans']))
                            commands.append('no switchport mode trunk')
                        commands.append('switchport access vlan {0}'.format(access_vlan))
                else:
                    if mode == 'access':
                        if access_vlan != obj_in_have['access_vlan']:
                            commands.append('switchport access vlan {0}'.format(access_vlan))
                    else:
                        if native_vlan != obj_in_have['native_vlan'] and native_vlan:
                            commands.append('switchport trunk native vlan {0}'.format(native_vlan))
                        if trunk_allowed_vlans != obj_in_have['trunk_allowed_vlans'] and trunk_allowed_vlans:
                            commands.append('switchport trunk allowed vlan {0}'.format(trunk_allowed_vlans))

        if commands[-1] == interface:
            commands.pop(-1)

    return commands


def map_config_to_obj(module, warnings):
    config = get_config(module, flags=['| section interface'])
    configobj = NetworkConfig(indent=3, contents=config)

    match = re.findall(r'^interface (\S+)', config, re.M)
    if not match:
        return list()

    instances = list()

    for item in set(match):
        command = {'command': 'show interfaces {0} switchport | include Switchport'.format(item),
                   'output': 'text'}
        command_result = run_commands(module, command, check_rc=False)
        if "Interface does not exist" in command_result[0]:
            warnings.append("Could not gather switchport information for {0}: {1}".format(item, command_result[0]))
            continue

        if command_result[0]:
            switchport_cfg = command_result[0].split(':')[1].strip()

            if switchport_cfg == 'Enabled':
                state = 'present'
            else:
                state = 'absent'

            obj = {
                'name': item.lower(),
                'state': state,
                'access_vlan': parse_config_argument(configobj, item, 'switchport access vlan'),
                'native_vlan': parse_config_argument(configobj, item, 'switchport trunk native vlan'),
                'trunk_allowed_vlans': parse_config_argument(configobj, item, 'switchport trunk allowed vlan'),
            }
            if obj['access_vlan']:
                obj['mode'] = 'access'
            else:
                obj['mode'] = 'trunk'

            instances.append(obj)

    return instances


def map_params_to_obj(module):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            item['name'] = item['name'].lower()
            obj.append(item.copy())
    else:
        obj.append({
            'name': module.params['name'].lower(),
            'mode': module.params['mode'],
            'access_vlan': module.params['access_vlan'],
            'native_vlan': module.params['native_vlan'],
            'trunk_allowed_vlans': module.params['trunk_allowed_vlans'],
            'state': module.params['state']
        })

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(type='str', aliases=['interface']),
        mode=dict(choices=['access', 'trunk']),
        access_vlan=dict(type='str'),
        native_vlan=dict(type='str'),
        trunk_allowed_vlans=dict(type='str', aliases=['trunk_vlans']),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(eos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['access_vlan', 'native_vlan'],
                                               ['access_vlan', 'trunk_allowed_vlans']],
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module, warnings)
    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
