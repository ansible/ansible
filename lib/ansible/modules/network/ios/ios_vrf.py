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


DOCUMENTATION = """
---
module: ios_vrf
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Manage the collection of VRF definitions on Cisco IOS devices
description:
  - This module provides declarative management of VRF definitions on
    Cisco IOS devices.  It allows playbooks to manage individual or
    the entire VRF collection.  It also supports purging VRF definitions from
    the configuration that are not explicitly defined.
extends_documentation_fragment: ios
notes:
  - Tested against IOS 15.6
options:
  vrfs:
    description:
      - The set of VRF definition objects to be configured on the remote
        IOS device.  Ths list entries can either be the VRF name or a hash
        of VRF definitions and attributes.  This argument is mutually
        exclusive with the C(name) argument.
  name:
    description:
      - The name of the VRF definition to be managed on the remote IOS
        device.  The VRF definition name is an ASCII string name used
        to uniquely identify the VRF.  This argument is mutually exclusive
        with the C(vrfs) argument
  description:
    description:
      - Provides a short description of the VRF definition in the
        current active configuration.  The VRF definition value accepts
        alphanumeric characters used to provide additional information
        about the VRF.
  rd:
    description:
      - The router-distinguisher value uniquely identifies the VRF to
        routing processes on the remote IOS system.  The RD value takes
        the form of C(A:B) where C(A) and C(B) are both numeric values.
  interfaces:
    description:
      - Identifies the set of interfaces that
        should be configured in the VRF.  Interfaces must be routed
        interfaces in order to be placed into a VRF.
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for given vrf C(name)
        for associated interfaces. If the value in the C(associated_interfaces) does not match with
        the operational state of vrf interfaces on device it will result in failure.
    version_added: "2.5"
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device.
    version_added: "2.4"
    default: 10
  purge:
    description:
      - Instructs the module to consider the
        VRF definition absolute.  It will remove any previously configured
        VRFs on the device.
    default: false
  state:
    description:
      - Configures the state of the VRF definition
        as it relates to the device operational configuration.  When set
        to I(present), the VRF should be configured in the device active
        configuration and when set to I(absent) the VRF should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
  route_both:
    description:
      - Adds an export and import list of extended route target communities to the VRF.
    version_added: "2.5"
  route_export:
    description:
      - Adds an export list of extended route target communities to the VRF.
    version_added: "2.5"
  route_import:
    description:
      - Adds an import list of extended route target communities to the VRF.
    version_added: "2.5"
  route_both_ipv4:
    description:
      - Adds an export and import list of extended route target communities in address-family configuration submode to the VRF.
    version_added: "2.7"
  route_export_ipv4:
    description:
      - Adds an export list of extended route target communities in address-family configuration submode to the VRF.
    version_added: "2.7"
  route_import_ipv4:
    description:
      - Adds an import list of extended route target communities in address-family configuration submode to the VRF.
    version_added: "2.7"
  route_both_ipv6:
    description:
      - Adds an export and import list of extended route target communities in address-family configuration submode to the VRF.
    version_added: "2.7"
  route_export_ipv6:
    description:
      - Adds an export list of extended route target communities in address-family configuration submode to the VRF.
    version_added: "2.7"
  route_import_ipv6:
    description:
      - Adds an import list of extended route target communities in address-family configuration submode to the VRF.
    version_added: "2.7"

"""
EXAMPLES = """
- name: configure a vrf named management
  ios_vrf:
    name: management
    description: oob mgmt vrf
    interfaces:
      - Management1

- name: remove a vrf named test
  ios_vrf:
    name: test
    state: absent

- name: configure set of VRFs and purge any others
  ios_vrf:
    vrfs:
      - red
      - blue
      - green
    purge: yes

- name: Creates a list of import RTs for the VRF with the same parameters
  ios_vrf:
    name: test_import
    rd: 1:100
    route_import:
      - 1:100
      - 3:100

- name: Creates a list of import RTs in address-family configuration submode for the VRF with the same parameters
  ios_vrf:
    name: test_import_ipv4
    rd: 1:100
    route_import_ipv4:
      - 1:100
      - 3:100

- name: Creates a list of import RTs in address-family configuration submode for the VRF with the same parameters
  ios_vrf:
    name: test_import_ipv6
    rd: 1:100
    route_import_ipv6:
      - 1:100
      - 3:100

- name: Creates a list of export RTs for the VRF with the same parameters
  ios_vrf:
    name: test_export
    rd: 1:100
    route_export:
      - 1:100
      - 3:100

- name: Creates a list of export RTs in address-family configuration submode for the VRF with the same parameters
  ios_vrf:
    name: test_export_ipv4
    rd: 1:100
    route_export_ipv4:
      - 1:100
      - 3:100

- name: Creates a list of export RTs in address-family configuration submode for the VRF with the same parameters
  ios_vrf:
    name: test_export_ipv6
    rd: 1:100
    route_export_ipv6:
      - 1:100
      - 3:100

- name: Creates a list of import and export route targets for the VRF with the same parameters
  ios_vrf:
    name: test_both
    rd: 1:100
    route_both:
      - 1:100
      - 3:100

- name: Creates a list of import and export route targets in address-family configuration submode for the VRF with the same parameters
  ios_vrf:
    name: test_both_ipv4
    rd: 1:100
    route_both_ipv4:
      - 1:100
      - 3:100

- name: Creates a list of import and export route targets in address-family configuration submode for the VRF with the same parameters
  ios_vrf:
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
  sample: "2016-11-16 10:38:15.126146"
end:
  description: The time the job ended
  returned: always
  type: str
  sample: "2016-11-16 10:38:25.595612"
delta:
  description: The time elapsed to perform all operations
  returned: always
  type: str
  sample: "0:00:10.469466"
"""
import re
import time
from functools import partial

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.ios.ios import load_config, get_config
from ansible.module_utils.network.ios.ios import ios_argument_spec, check_args
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.six import iteritems


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
    if 'vrf definition %s' % name not in commands:
        commands.extend([
            'vrf definition %s' % name,
            'address-family ipv4', 'exit',
            'address-family ipv6', 'exit',
        ])
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
            commands.append('no vrf definition %s' % want['name'])
            continue

        if not have.get('state'):
            commands.extend([
                'vrf definition %s' % want['name'],
                'address-family ipv4', 'exit',
                'address-family ipv6', 'exit',
            ])

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

        if needs_update(want, have, 'route_import_ipv4'):
                cmd = 'address-family ipv4'
                add_command_to_vrf(want['name'], cmd, commands)
                for route in want['route_import_ipv4']:
                    cmd = 'route-target import %s' % route
                    add_command_to_vrf(want['name'], cmd, commands)
                cmd = 'exit-address-family'
                add_command_to_vrf(want['name'], cmd, commands)

        if needs_update(want, have, 'route_export_ipv4'):
                cmd = 'address-family ipv4'
                add_command_to_vrf(want['name'], cmd, commands)
                for route in want['route_export_ipv4']:
                    cmd = 'route-target export %s' % route
                    add_command_to_vrf(want['name'], cmd, commands)
                cmd = 'exit-address-family'
                add_command_to_vrf(want['name'], cmd, commands)

        if needs_update(want, have, 'route_import_ipv6'):
                cmd = 'address-family ipv6'
                add_command_to_vrf(want['name'], cmd, commands)
                for route in want['route_import_ipv6']:
                    cmd = 'route-target import %s' % route
                    add_command_to_vrf(want['name'], cmd, commands)
                cmd = 'exit-address-family'
                add_command_to_vrf(want['name'], cmd, commands)

        if needs_update(want, have, 'route_export_ipv6'):
                cmd = 'address-family ipv6'
                add_command_to_vrf(want['name'], cmd, commands)
                for route in want['route_export_ipv6']:
                    cmd = 'route-target export %s' % route
                    add_command_to_vrf(want['name'], cmd, commands)
                cmd = 'exit-address-family'
                add_command_to_vrf(want['name'], cmd, commands)

        if want['interfaces'] is not None:
            # handle the deletes
            for intf in set(have.get('interfaces', [])).difference(want['interfaces']):
                commands.extend(['interface %s' % intf,
                                 'no vrf forwarding %s' % want['name']])

            # handle the adds
            for intf in set(want['interfaces']).difference(have.get('interfaces', [])):
                cfg = get_config(module)
                configobj = NetworkConfig(indent=1, contents=cfg)
                children = configobj['interface %s' % intf].children
                intf_config = '\n'.join(children)

                commands.extend(['interface %s' % intf,
                                 'vrf forwarding %s' % want['name']])

                match = re.search('ip address .+', intf_config, re.M)
                if match:
                    commands.append(match.group())

    return commands


def parse_description(configobj, name):
    cfg = configobj['vrf definition %s' % name]
    cfg = '\n'.join(cfg.children)
    match = re.search(r'description (.+)$', cfg, re.M)
    if match:
        return match.group(1)


def parse_rd(configobj, name):
    cfg = configobj['vrf definition %s' % name]
    cfg = '\n'.join(cfg.children)
    match = re.search(r'rd (.+)$', cfg, re.M)
    if match:
        return match.group(1)


def parse_interfaces(configobj, name):
    vrf_cfg = 'vrf forwarding %s' % name
    interfaces = list()
    for intf in re.findall('^interface .+', str(configobj), re.M):
        if vrf_cfg in '\n'.join(configobj[intf].children):
            interfaces.append(intf.split(' ')[1])
    return interfaces


def parse_import(configobj, name):
    cfg = configobj['vrf definition %s' % name]
    cfg = '\n'.join(cfg.children)
    matches = re.findall(r'route-target\s+import\s+(.+)', cfg, re.M)
    return matches


def parse_export(configobj, name):
    cfg = configobj['vrf definition %s' % name]
    cfg = '\n'.join(cfg.children)
    matches = re.findall(r'route-target\s+export\s+(.+)', cfg, re.M)
    return matches


def parse_both(configobj, name, address_family='global'):
    rd_pattern = re.compile('(?P<rd>.+:.+)')
    matches = list()
    export_match = None
    import_match = None
    if address_family == "global":
        export_match = parse_export(configobj, name)
        import_match = parse_import(configobj, name)
    elif address_family == "ipv4":
        export_match = parse_export_ipv4(configobj, name)
        import_match = parse_import_ipv4(configobj, name)
    elif address_family == "ipv6":
        export_match = parse_export_ipv6(configobj, name)
        import_match = parse_import_ipv6(configobj, name)
    if import_match and export_match:
        for ex in export_match:
            exrd = rd_pattern.search(ex)
            exrd = exrd.groupdict().get('rd')
            for im in import_match:
                imrd = rd_pattern.search(im)
                imrd = imrd.groupdict().get('rd')
                if exrd == imrd:
                    matches.extend([exrd]) if exrd not in matches else None
                    matches.extend([imrd]) if imrd not in matches else None
    return matches


def parse_import_ipv4(configobj, name):
    cfg = configobj['vrf definition %s' % name]
    try:
        subcfg = cfg['address-family ipv4']
        subcfg = '\n'.join(subcfg.children)
        matches = re.findall(r'route-target\s+import\s+(.+)', subcfg, re.M)
        return matches
    except KeyError:
        pass


def parse_export_ipv4(configobj, name):
    cfg = configobj['vrf definition %s' % name]
    try:
        subcfg = cfg['address-family ipv4']
        subcfg = '\n'.join(subcfg.children)
        matches = re.findall(r'route-target\s+export\s+(.+)', subcfg, re.M)
        return matches
    except KeyError:
        pass


def parse_import_ipv6(configobj, name):
    cfg = configobj['vrf definition %s' % name]
    try:
        subcfg = cfg['address-family ipv6']
        subcfg = '\n'.join(subcfg.children)
        matches = re.findall(r'route-target\s+import\s+(.+)', subcfg, re.M)
        return matches
    except KeyError:
        pass


def parse_export_ipv6(configobj, name):
    cfg = configobj['vrf definition %s' % name]
    try:
        subcfg = cfg['address-family ipv6']
        subcfg = '\n'.join(subcfg.children)
        matches = re.findall(r'route-target\s+export\s+(.+)', subcfg, re.M)
        return matches
    except KeyError:
        pass


def map_config_to_obj(module):
    config = get_config(module)
    configobj = NetworkConfig(indent=1, contents=config)
    match = re.findall(r'^vrf definition (\S+)', config, re.M)
    if not match:
        return list()

    instances = list()
    for item in set(match):
        obj = {
            'name': item,
            'state': 'present',
            'description': parse_description(configobj, item),
            'rd': parse_rd(configobj, item),
            'interfaces': parse_interfaces(configobj, item),
            'route_import': parse_import(configobj, item),
            'route_export': parse_export(configobj, item),
            'route_both': parse_both(configobj, item),
            'route_import_ipv4': parse_import_ipv4(configobj, item),
            'route_export_ipv4': parse_export_ipv4(configobj, item),
            'route_both_ipv4': parse_both(configobj, item, address_family='ipv4'),
            'route_import_ipv6': parse_import_ipv6(configobj, item),
            'route_export_ipv6': parse_export_ipv6(configobj, item),
            'route_both_ipv6': parse_both(configobj, item, address_family='ipv6'),
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
        item['route_import_ipv4'] = get_value('route_import_ipv4')
        item['route_export_ipv4'] = get_value('route_export_ipv4')
        item['route_both_ipv4'] = get_value('route_both_ipv4')
        item['route_import_ipv6'] = get_value('route_import_ipv6')
        item['route_export_ipv6'] = get_value('route_export_ipv6')
        item['route_both_ipv6'] = get_value('route_both_ipv6')
        both_addresses_family = ["", "_ipv6", "_ipv4"]
        for address_family in both_addresses_family:
            if item["route_both%s" % address_family]:
                if not item["route_export%s" % address_family]:
                    item["route_export%s" % address_family] = list()
                if not item["route_import%s" % address_family]:
                    item["route_import%s" % address_family] = list()
                item["route_export%s" % address_family].extend(get_value("route_both%s" % address_family))
                item["route_import%s" % address_family].extend(get_value("route_both%s" % address_family))
        item['associated_interfaces'] = get_value('associated_interfaces')
        objects.append(item)

    return objects


def update_objects(want, have):
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
        rc, out, err = exec_command(module, 'show vrf | include {0}'.format(name))

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
                            module.fail_json(msg="Interface %s not configured on vrf %s" % (interface, name))


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
        route_export_ipv4=dict(type='list'),
        route_import_ipv4=dict(type='list'),
        route_both_ipv4=dict(type='list'),
        route_export_ipv6=dict(type='list'),
        route_import_ipv6=dict(type='list'),
        route_both_ipv6=dict(type='list'),


        interfaces=dict(type='list'),
        associated_interfaces=dict(type='list'),

        delay=dict(default=10, type='int'),
        purge=dict(type='bool', default=False),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ios_argument_spec)

    mutually_exclusive = [('name', 'vrfs')]
    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
    result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands(update_objects(want, have), module)

    if module.params['purge']:
        want_vrfs = [x['name'] for x in want]
        have_vrfs = [x['name'] for x in have]
        for item in set(have_vrfs).difference(want_vrfs):
            cmd = 'no vrf definition %s' % item
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
