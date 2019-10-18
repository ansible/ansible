#!/usr/bin/python
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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_vrf
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manages global VRF configuration.
description:
  - This module provides declarative management of VRFs
    on CISCO NXOS network devices.
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
  - Trishna Guha (@trishnaguha)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - Cisco NX-OS creates the default VRF by itself. Therefore,
    you're not allowed to use default as I(vrf) name in this module.
  - C(vrf) name must be shorter than 32 chars.
  - VRF names are not case sensible in NX-OS. Anyway, the name is stored
    just like it's inserted by the user and it'll not be changed again
    unless the VRF is removed and re-created. i.e. C(vrf=NTC) will create
    a VRF named NTC, but running it again with C(vrf=ntc) will not cause
    a configuration change.
options:
  name:
    description:
      - Name of VRF to be managed.
    required: true
    aliases: [vrf]
  admin_state:
    description:
      - Administrative state of the VRF.
    default: up
    choices: ['up','down']
  vni:
    description:
      - Specify virtual network identifier. Valid values are Integer
        or keyword 'default'.
    version_added: "2.2"
  rd:
    description:
      - VPN Route Distinguisher (RD). Valid values are a string in
        one of the route-distinguisher formats (ASN2:NN, ASN4:NN, or
        IPV4:NN); the keyword 'auto', or the keyword 'default'.
    version_added: "2.2"
  interfaces:
    description:
      - List of interfaces to check the VRF has been
        configured correctly or keyword 'default'.
    version_added: 2.5
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for given vrf C(name)
        for associated interfaces. If the value in the C(associated_interfaces) does not match with
        the operational state of vrf interfaces on device it will result in failure.
    version_added: "2.5"
  aggregate:
    description: List of VRFs definitions.
    version_added: 2.5
  purge:
    description:
      - Purge VRFs not defined in the I(aggregate) parameter.
    type: bool
    default: 'no'
    version_added: 2.5
  state:
    description:
      - Manages desired state of the resource.
    default: present
    choices: ['present','absent']
  description:
    description:
      - Description of the VRF or keyword 'default'.
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state arguments.
    default: 10
'''

EXAMPLES = '''
- name: Ensure ntc VRF exists on switch
  nxos_vrf:
    name: ntc
    description: testing
    state: present

- name: Aggregate definition of VRFs
  nxos_vrf:
    aggregate:
      - { name: test1, description: Testing, admin_state: down }
      - { name: test2, interfaces: Ethernet1/2 }

- name: Aggregate definitions of VRFs with Purge
  nxos_vrf:
    aggregate:
      - { name: ntc1, description: purge test1 }
      - { name: ntc2, description: purge test2 }
    state: present
    purge: yes

- name: Delete VRFs exist on switch
  nxos_vrf:
    aggregate:
      - { name: ntc1 }
      - { name: ntc2 }
    state: absent

- name: Assign interfaces to VRF declaratively
  nxos_vrf:
    name: test1
    interfaces:
      - Ethernet2/3
      - Ethernet2/5

- name: Check interfaces assigned to VRF
  nxos_vrf:
    name: test1
    associated_interfaces:
      - Ethernet2/3
      - Ethernet2/5

- name: Ensure VRF is tagged with interface Ethernet2/5 only (Removes from Ethernet2/3)
  nxos_vrf:
    name: test1
    interfaces:
      - Ethernet2/5

- name: Delete VRF
  nxos_vrf:
    name: ntc
    state: absent
'''

RETURN = '''
commands:
  description: commands sent to the device
  returned: always
  type: list
  sample:
    - vrf context ntc
    - no shutdown
    - interface Ethernet1/2
    - no switchport
    - vrf member test2
'''

import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, get_interface_type
from ansible.module_utils.network.common.utils import remove_default_spec


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o


def execute_show_command(command, module):
    if 'show run' not in command:
        output = 'json'
    else:
        output = 'text'
    cmds = [{
        'command': command,
        'output': output,
    }]
    body = run_commands(module, cmds)
    return body


def get_existing_vrfs(module):
    objs = list()
    command = "show vrf all"
    try:
        body = execute_show_command(command, module)[0]
    except IndexError:
        return list()
    try:
        vrf_table = body['TABLE_vrf']['ROW_vrf']
    except (TypeError, IndexError, KeyError):
        return list()

    if isinstance(vrf_table, list):
        for vrf in vrf_table:
            obj = {}
            obj['name'] = vrf['vrf_name']
            objs.append(obj)

    elif isinstance(vrf_table, dict):
        obj = {}
        obj['name'] = vrf_table['vrf_name']
        objs.append(obj)

    return objs


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']
    purge = module.params['purge']

    args = ('rd', 'description', 'vni')

    for w in want:
        name = w['name']
        admin_state = w['admin_state']
        vni = w['vni']
        interfaces = w.get('interfaces') or []
        state = w['state']
        del w['state']

        obj_in_have = search_obj_in_list(name, have)

        if state == 'absent' and obj_in_have:
            commands.append('no vrf context {0}'.format(name))

        elif state == 'present':
            if not obj_in_have:
                commands.append('vrf context {0}'.format(name))
                for item in args:
                    candidate = w.get(item)
                    if candidate and candidate != 'default':
                        cmd = item + ' ' + str(candidate)
                        commands.append(cmd)
                if admin_state == 'up':
                    commands.append('no shutdown')
                elif admin_state == 'down':
                    commands.append('shutdown')
                commands.append('exit')

                if interfaces and interfaces[0] != 'default':
                    for i in interfaces:
                        commands.append('interface {0}'.format(i))
                        if get_interface_type(i) in ('ethernet', 'portchannel'):
                            commands.append('no switchport')
                        commands.append('vrf member {0}'.format(name))

            else:
                # If vni is already configured on vrf, unconfigure it first.
                if vni:
                    if obj_in_have.get('vni') and vni != obj_in_have.get('vni'):
                        commands.append('no vni {0}'.format(obj_in_have.get('vni')))

                for item in args:
                    candidate = w.get(item)
                    if candidate == 'default':
                        if obj_in_have.get(item):
                            cmd = 'no ' + item + ' ' + obj_in_have.get(item)
                            commands.append(cmd)
                    elif candidate and candidate != obj_in_have.get(item):
                        cmd = item + ' ' + str(candidate)
                        commands.append(cmd)
                if admin_state and admin_state != obj_in_have.get('admin_state'):
                    if admin_state == 'up':
                        commands.append('no shutdown')
                    elif admin_state == 'down':
                        commands.append('shutdown')

                if commands:
                    commands.insert(0, 'vrf context {0}'.format(name))
                    commands.append('exit')

                if interfaces and interfaces[0] != 'default':
                    if not obj_in_have['interfaces']:
                        for i in interfaces:
                            commands.append('vrf context {0}'.format(name))
                            commands.append('exit')
                            commands.append('interface {0}'.format(i))
                            if get_interface_type(i) in ('ethernet', 'portchannel'):
                                commands.append('no switchport')
                            commands.append('vrf member {0}'.format(name))

                    elif set(interfaces) != set(obj_in_have['interfaces']):
                        missing_interfaces = list(set(interfaces) - set(obj_in_have['interfaces']))
                        for i in missing_interfaces:
                            commands.append('vrf context {0}'.format(name))
                            commands.append('exit')
                            commands.append('interface {0}'.format(i))
                            if get_interface_type(i) in ('ethernet', 'portchannel'):
                                commands.append('no switchport')
                            commands.append('vrf member {0}'.format(name))

                        superfluous_interfaces = list(set(obj_in_have['interfaces']) - set(interfaces))
                        for i in superfluous_interfaces:
                            commands.append('vrf context {0}'.format(name))
                            commands.append('exit')
                            commands.append('interface {0}'.format(i))
                            if get_interface_type(i) in ('ethernet', 'portchannel'):
                                commands.append('no switchport')
                            commands.append('no vrf member {0}'.format(name))
                elif interfaces and interfaces[0] == 'default':
                    if obj_in_have['interfaces']:
                        for i in obj_in_have['interfaces']:
                            commands.append('vrf context {0}'.format(name))
                            commands.append('exit')
                            commands.append('interface {0}'.format(i))
                            if get_interface_type(i) in ('ethernet', 'portchannel'):
                                commands.append('no switchport')
                            commands.append('no vrf member {0}'.format(name))

    if purge:
        existing = get_existing_vrfs(module)
        if existing:
            for h in existing:
                if h['name'] in ('default', 'management'):
                    pass
                else:
                    obj_in_want = search_obj_in_list(h['name'], want)
                    if not obj_in_want:
                        commands.append('no vrf context {0}'.format(h['name']))

    return commands


def validate_vrf(name, module):
    if name == 'default':
        module.fail_json(msg='cannot use default as name of a VRF')
    elif len(name) > 32:
        module.fail_json(msg='VRF name exceeded max length of 32', name=name)
    else:
        return name


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            d['name'] = validate_vrf(d['name'], module)
            obj.append(d)
    else:
        obj.append({
            'name': validate_vrf(module.params['name'], module),
            'description': module.params['description'],
            'vni': module.params['vni'],
            'rd': module.params['rd'],
            'admin_state': module.params['admin_state'],
            'state': module.params['state'],
            'interfaces': module.params['interfaces'],
            'associated_interfaces': module.params['associated_interfaces']
        })
    return obj


def get_value(arg, config, module):
    extra_arg_regex = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(arg), re.M)
    value = ''
    if arg in config:
        value = extra_arg_regex.search(config).group('value')
    return value


def map_config_to_obj(want, element_spec, module):
    objs = list()

    for w in want:
        obj = deepcopy(element_spec)
        del obj['delay']
        del obj['state']

        command = 'show vrf {0}'.format(w['name'])
        try:
            body = execute_show_command(command, module)[0]
            vrf_table = body['TABLE_vrf']['ROW_vrf']
        except (TypeError, IndexError):
            return list()

        name = vrf_table['vrf_name']
        obj['name'] = name
        obj['admin_state'] = vrf_table['vrf_state'].lower()

        command = 'show run all | section vrf.context.{0}'.format(name)
        body = execute_show_command(command, module)[0]
        extra_params = ['vni', 'rd', 'description']
        for param in extra_params:
            obj[param] = get_value(param, body, module)

        obj['interfaces'] = []
        command = 'show vrf {0} interface'.format(name)
        try:
            body = execute_show_command(command, module)[0]
            vrf_int = body['TABLE_if']['ROW_if']
        except (TypeError, IndexError):
            vrf_int = None

        if vrf_int:
            if isinstance(vrf_int, list):
                for i in vrf_int:
                    intf = i['if_name']
                    obj['interfaces'].append(intf)
            elif isinstance(vrf_int, dict):
                intf = vrf_int['if_name']
                obj['interfaces'].append(intf)

        objs.append(obj)
    return objs


def check_declarative_intent_params(want, module, element_spec, result):

    have = None
    is_delay = False

    for w in want:
        if w.get('associated_interfaces') is None:
            continue

        if result['changed'] and not is_delay:
            time.sleep(module.params['delay'])
            is_delay = True

        if have is None:
            have = map_config_to_obj(want, element_spec, module)

        for i in w['associated_interfaces']:
            obj_in_have = search_obj_in_list(w['name'], have)

            if obj_in_have:
                interfaces = obj_in_have.get('interfaces')
                if interfaces is not None and i not in interfaces:
                    module.fail_json(msg="Interface %s not configured on vrf %s" % (i, w['name']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(type='str', aliases=['vrf']),
        description=dict(type='str'),
        vni=dict(type='str'),
        rd=dict(type='str'),
        admin_state=dict(type='str', default='up', choices=['up', 'down']),
        interfaces=dict(type='list'),
        associated_interfaces=dict(type='list'),
        delay=dict(type='int', default=10),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(type='bool', default=False),
    )

    argument_spec.update(element_spec)
    argument_spec.update(nxos_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(want, element_spec, module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands and not module.check_mode:
        load_config(module, commands)
        result['changed'] = True

    check_declarative_intent_params(want, module, element_spec, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
