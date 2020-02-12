#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: awplus_vrf
version_added: "2.10"
author:
    - Jeremy Toth (@jtsource)
    - Isaac Daly (@dalyIsaac)
short_description: Manage the collection of VRF definitions on AlliedWare Plus devices
description:
    - This module provides declarative management of VRF definitions on
        Awplus devices. It allows playbooks to manage individual or
        the entire VRF collection. It also supports purging VRF definitions from
        the configuration that are not explicitly defined.
options:
    vrfs:
        description:
            - The set of VRF definition objects to be configured on the remote
                Awplus device. Ths list entries can either be the VRF name or a hash
                of VRF definitions and attributes. This argument is mutually
                exclusive with the C(name) argument.
    name:
        description:
            - The name of the VRF definition to be managed on the remote Awplus
                device. The VRF definition name is an ASCII string name used
                to uniquely identify the VRF. This argument is mutually exclusive
                with the C(vrfs) argument
    description:
        description:
            - Provides a short description of the VRF definition in the
                current active configuration. The VRF definition value accepts
                alphanumeric characters used to provide additional information
                about the VRF.
    rd:
        description:
            - The router-distinguisher value uniquely identifies the VRF to
                routing processes on the remote Awplus system. The RD value takes
                the form of C(A:B) where C(A) and C(B) are both numeric values.
    interfaces:
        description:
            - Identifies the set of interfaces that
                should be configured in the VRF. Interfaces must be routed
                interfaces in order to be placed into a VRF.
    associated_interfaces:
        description:
            - This is a intent option and checks the operational state of the for given vrf C(name)
                for associated interfaces. If the value in the C(associated_interfaces) does not match with
                the operational state of vrf interfaces on device it will result in failure.
    delay:
        description:
            - Time in seconds to wait before checking for the operational state on remote
                device.
        default: 10
    purge:
        description:
            - Instructs the module to consider the VRF definition absolute. It will remove any previously
                configured VRFs on the device.
        default: false
        type: bool
    state:
        description:
            - Configures the state of the VRF definition
                as it relates to the device operational configuration. When set
                to I(present), the VRF should be configured in the device active
                configuration and when set to I(absent) the VRF should not be
                in the device active configuration
        default: present
        choices: ['present', 'absent']
    route_both:
        description:
            - Adds an export and import list of extended route target communities to the VRF.
    route_export:
        description:
            - Adds an export list of extended route target communities to the VRF.
    route_import:
        description:
            - Adds an import list of extended route target communities to the VRF.
    route_both_ipv4:
        description:
            - Adds an export and import list of extended route target communities in address-family configuration submode to the VRF.
    route_export_ipv4:
        description:
            - Adds an export list of extended route target communities in address-family configuration submode to the VRF.
    route_import_ipv4:
        description:
            - Adds an import list of extended route target communities in address-family configuration submode to the VRF.
    route_both_ipv6:
        description:
            - Adds an export and import list of extended route target communities in address-family configuration submode to the VRF.
    route_export_ipv6:
        description:
            - Adds an export list of extended route target communities in address-family configuration submode to the VRF.
    route_import_ipv6:
        description:
            - Adds an import list of extended route target communities in address-family configuration submode to the VRF.
notes:
    - Check mode is supported.
"""

EXAMPLES = """
- name: configure a vrf named management
    awplus_vrf:
        name: management
        description: oob mgmt vrf
        interfaces:
            - Management1
- name: remove a vrf named test
    awplus_vrf:
        name: test
        state: absent
- name: configure set of VRFs and purge any others
    awplus_vrf:
        vrfs:
            - red
            - blue
            - green
        purge: yes
- name: Creates a list of import RTs for the VRF with the same parameters
    awplus_vrf:
        name: test_import
        rd: 1:100
        route_import:
            - 1:100
            - 3:100
- name: Creates a list of import RTs in address-family configuration submode for the VRF with the same parameters
    awplus_vrf:
        name: test_import_ipv4
        rd: 1:100
        route_import_ipv4:
            - 1:100
            - 3:100
- name: Creates a list of import RTs in address-family configuration submode for the VRF with the same parameters
    awplus_vrf:
        name: test_import_ipv6
        rd: 1:100
        route_import_ipv6:
            - 1:100
            - 3:100
- name: Creates a list of export RTs for the VRF with the same parameters
    awplus_vrf:
        name: test_export
        rd: 1:100
        route_export:
            - 1:100
            - 3:100
- name: Creates a list of export RTs in address-family configuration submode for the VRF with the same parameters
    awplus_vrf:
        name: test_export_ipv4
        rd: 1:100
        route_export_ipv4:
            - 1:100
            - 3:100
- name: Creates a list of export RTs in address-family configuration submode for the VRF with the same parameters
    awplus_vrf:
        name: test_export_ipv6
        rd: 1:100
        route_export_ipv6:
            - 1:100
            - 3:100
- name: Creates a list of import and export route targets for the VRF with the same parameters
    awplus_vrf:
        name: test_both
        rd: 1:100
        route_both:
            - 1:100intf
            - 3:100
- name: Creates a list of import and export route targets in address-family configuration submode for the VRF with the same parameters
    awplus_vrf:
        name: test_both_ipv4
        rd: 1:100
        route_both_ipv4:
            - 1:100
            - 3:100
- name: Creates a list of import and export route targets in address-family configuration submode for the VRF with the same parameters
    awplus_vrf:
        name: test_both_ipv6
        rd: 1:100
        route_both_ipv6:
            - 1:100
            - 3:100
"""

RETURN = """
commands:
    description: The list of configuration mode commands to send to the device
    returned: always
    type: list
    sample:
        - vrf definition ansible
        - description management vrf
        - rd: 1:100
start:
    description: The time the job started
    returned: always
    type: str
    sample: '2016-11-16 10:38:15.126146'
end:
    description: The time the job ended
    returned: always
    type: str
    sample: '2016-11-16 10:38:25.595612'
delta:
    description: The time elapsed to perform all operations
    returned: always
    type: str
    sample: '0:00:10.469466'
"""

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.awplus.awplus import awplus_argument_spec
from ansible.module_utils.network.awplus.awplus import load_config, get_config, get_connection
from ansible.module_utils.connection import exec_command
from ansible.module_utils.basic import AnsibleModule
from functools import partial
import time
import re


def get_interface_type(interface):

    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    elif interface.upper().startswith('NV'):
        return 'nve'
    else:
        return 'unknown'


def add_command_to_vrf(name, cmd, commands):
    if 'ip vrf %s' % name not in commands:
        commands.extend(['ip vrf %s' % name])
    commands.append(cmd)


def map_obj_to_commands(updates, module):
    commands = list()
    for update in updates:
        want, have = update

        def needs_update(want, have, x):
            if isinstance(want.get(x), list) and isinstance(have.get(x), list):
                return want.get(x) and (want.get(x) != have.get(x)) and not all(elem in have.get(x) for elem in want.get(x))
            return want.get(x) and (want.get(x) != have.get(x))

        if want['state'] == 'absent':
            commands.append('no ip vrf %s' % want['name'])
            continue

        if not have.get('state'):
            commands.extend(['ip vrf %s' % want['name']])

        if needs_update(want, have, 'description'):
            cmd = 'description %s' % want['description']
            add_command_to_vrf(want['name'], cmd, commands)

        if needs_update(want, have, 'rd'):
            cmd = 'rd %s' % want['rd']
            add_command_to_vrf(want['name'], cmd, commands)

        if needs_update(want, have, 'route_import'):
            for route in want['route_import']:
                cmd = 'route-target import %s' % route
                add_command_to_vrf(want['name'], cmd, commands)

        if needs_update(want, have, 'route_export'):
            for route in want['route_export']:
                cmd = 'route-target export %s' % route
                add_command_to_vrf(want['name'], cmd, commands)

        if needs_update(want, have, 'route_both'):
            for route in want['route_both']:
                cmd = 'route-target both %s' % route
                add_command_to_vrf(want['name'], cmd, commands)

        if want['interfaces'] is not None:
            # handle the deletes
            for intf in set(have.get('interfaces', [])).difference(want['interfaces']):
                commands.extend(['interface %s' % intf,
                                 'no ip vrf %s' % want['name']])

            # handle the adds
            for intf in set(want['interfaces']).difference(have.get('interfaces', [])):
                commands.extend(['interface %s' % intf,
                                 'ip vrf forwarding %s' % want['name']])

    return commands


def parse_description(item):
    match = re.search(r'description (.+)', item, re.M)
    if match:
        return match.group(1).strip()


def parse_rd(item):
    match = re.search(r'rd (\d+\:\d+)', item, re.M)
    if match:
        return match.group(1).strip()


def parse_interfaces(module, configobj):
    interfaces = dict()
    intf = r'Interface '
    blocks = [block for block in re.split(intf, configobj.strip()) if block]
    for block in blocks:
        intf = ''
        for s in block:
            if s == '\n':
                break
            else:
                intf += s

        if intf:
            vrf = re.search(r'VRF Binding: Associated with (\w+)', block, re.M)
            if vrf:
                vrf = vrf.group(1)
                try:
                    interfaces[vrf.strip()].append(intf.strip())
                except KeyError:
                    interfaces[vrf.strip()] = [intf.strip()]
    return interfaces


def parse_import(item):
    matches = re.findall(r'route-target\s+import\s+(\S+)', item, re.M)
    return matches


def parse_export(item):
    matches = re.findall(r'route-target\s+export\s+(\S+)', item, re.M)
    return matches


def parse_both(item):
    matches = re.findall(r'route-target\s+both\s+(\S+)', item, re.M)
    return matches


def get_intf_info(module):
    connection = get_connection(module)
    return connection.get('show interface')


def map_config_to_obj(module):
    config = get_config(module)
    intfobj = get_intf_info(module)

    blocks = config.split('!')
    vrfs = []
    for block in blocks:
        if re.search(r'ip vrf (\w+) \d', block, re.M):
            vrfs.append(block)

    if len(vrfs) == 0:
        return list()

    instances = list()

    interfaces = parse_interfaces(module, intfobj)

    for item in set(vrfs):
        name = re.search(r'ip vrf (\w+) \d', item, re.M).group(1)
        obj = {
            'name': name,
            'state': 'present',
            'description': parse_description(item),
            'rd': parse_rd(item),
            'interfaces': interfaces.get(name),
            'route_import': parse_import(item),
            'route_export': parse_export(item),
            'route_both': parse_both(item)
        }
        instances.append(obj)
    return instances


def get_param_value(key, item, module):
    # if key doesn't exist in the item, get it from module.params
    if not item.get(key):
        value = module.params[key]

    # if key does exist, do a type check on it to validate it
    else:
        value_type = module.argument_spec[key].get('type', 'str')
        type_checker = module._CHECK_ARGUMENT_TYPES_DISPATCHER[value_type]
        type_checker(item[key])
        value = item[key]

    # validate the param value (if validator func exists)
    validator = globals().get('validate_%s' % key)
    if validator:
        validator(value, module)

    return value


def map_params_to_obj(module):
    vrfs = module.params.get('vrfs')
    if not vrfs:
        if not module.params['name'] and module.params['purge']:
            return list()
        elif not module.params['name']:
            module.fail_json(msg='name is required')
        collection = [{'name': module.params['name']}]
    else:
        collection = list()
        for item in vrfs:
            if not isinstance(item, dict):
                collection.append({'name': item})
            elif 'name' not in item:
                module.fail_json(msg='name is required')
            else:
                collection.append(item)

    objects = list()
    for item in collection:
        get_value = partial(get_param_value, item=item, module=module)
        item['description'] = get_value('description')
        item['rd'] = get_value('rd')
        item['interfaces'] = get_value('interfaces')
        item['state'] = get_value('state')
        item['route_import'] = get_value('route_import')
        item['route_export'] = get_value('route_export')
        item['route_both'] = get_value('route_both')

        item['associated_interfaces'] = get_value('associated_interfaces')
        objects.append(item)

    return objects


def update_objects(want, have):
    # raise ValueError((want, have))
    updates = list()
    for entry in want:
        item = next((i for i in have if i['name'] == entry['name']), None)
        if all((item is None, entry['state'] == 'present')):
            updates.append((entry, {}))
        else:
            for key, value in iteritems(entry):
                if value:
                    try:
                        if isinstance(value, list):
                            if sorted(value) != sorted(item[key]):
                                if (entry, item) not in updates:
                                    updates.append((entry, item))
                        elif value != item[key]:
                            if (entry, item) not in updates:
                                updates.append((entry, item))
                    except TypeError:
                        pass
    return updates


def check_declarative_intent_params(want, module, result):
    if module.params['associated_interfaces']:

        if result['changed']:
            time.sleep(module.params['delay'])

        name = module.params['name']
        rc, out, err = exec_command(
            module, 'show run vrf | include {0}'.format(name))

        if rc == 0:
            data = out.strip().split()
            # data will be empty if the vrf was just added
            if not data:
                return
            vrf = data[0]
            interface = data[-1]

            for w in want:
                if w['name'] == vrf:
                    if w.get('associated_interfaces') is None:
                        continue
                    for i in w['associated_interfaces']:
                        if get_interface_type(i) is not get_interface_type(interface):
                            module.fail_json(
                                msg="Interface %s not configured on vrf %s" % (interface, name))


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        vrfs=dict(type='list'),

        name=dict(),
        description=dict(),
        rd=dict(),
        route_export=dict(type='list'),
        route_import=dict(type='list'),
        route_both=dict(type='list'),

        interfaces=dict(type='list'),
        associated_interfaces=dict(type='list'),

        delay=dict(default=10, type='int'),
        purge=dict(type='bool', default=False),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(awplus_argument_spec)

    mutually_exclusive = [('name', 'vrfs')]
    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands(update_objects(want, have), module)

    if module.params['purge']:
        want_vrfs = [x['name'] for x in want]
        have_vrfs = [x['name'] for x in have]
        for item in set(have_vrfs).difference(want_vrfs):
            cmd = 'no ip vrf %s' % item
            if cmd not in commands:
                commands.append(cmd)

    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    check_declarative_intent_params(want, module, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
