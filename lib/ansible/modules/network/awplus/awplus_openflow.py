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
module: awplus_openflow
short_description: Manages core OpenFlow configuration on AlliedWare Plus device
version_added: "2.10"
description:
    - Manages core OpenFlow configuration on AlliedWare Plus device
author:
    - Cheng Yi Kok (@cyk19)
    - Isaac Daly (@dalyIsaac)
options:
    controllers:
        description:
            - OpenFlow Controller
        type: list
        elements: dict
        suboptions:
            name:
                description:
                    - Name of OpenFlow controller
                type: str
            protocol:
                description:
                    - Protocol type to communicate with the OpenFlow Controller
                type: str
                choices:
                    - ssl
                    - tcp
                required: True
            address:
                description:
                    - The IPv4 address of the Controller
                type: str
                required: True
            ssl_port:
                description:
                    - Port number used to communicate with the OpenFlow controller
                type: int
                required: True
    ports:
        description:
            - Data plane port
        type: list
        elements: dict
        suboptions:
            name:
                description:
                    - Name of port or static aggregator
                type: str
                required: True
            openflow:
                description:
                    - Status of a port/static aggregator as a data plane port
                type: bool
                default: True
    native_vlan:
        description:
            - Native VLAN for data plane ports
        type: int
    fail_mode:
        description:
            - Operation mode for the switch when the Controller connection fails or no Controllers are defined
        type: str
        choices:
            - secure
            - standalone
    state:
        description:
            - Manage state of resource
        default: present
        choices: ['present', 'absent']
notes:
    - Check mode is supported.
"""


EXAMPLES = """
commands:
    - name: Test openflow module
    awplus_openflow:
        address: 192.168.5.1
        state: present
"""


RETURN = """
commands:
    description: The list of commands to send to the device
    returned: always
    type: list
    sample: ['openflow failmode secure non-rule-expired']
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.awplus.awplus import get_config, awplus_argument_spec
from ansible.module_utils.network.awplus.awplus import load_config, run_commands
import re


def map_obj_to_commands(want, have, module):
    commands = []

    have = have[0]
    want = want[0]

    controllers_have = have['controllers']
    ports_have = have['ports']
    native_vlan_have = have['native_vlan']
    fail_mode_have = have['fail_mode']

    remove_all_config = True
    for value in want.values():
        if value is not None and value != 'absent':
            remove_all_config = False
            break

    if remove_all_config:
        for controller in controllers_have:
            commands.append(
                'no openflow controller {0}'.format(controller['name']))
        for port in ports_have:
            commands.append('interface {0}'.format(port['name']))
            commands.append('no openflow')
        if native_vlan_have:
            commands.append('no openflow native vlan')
        if fail_mode_have:
            commands.append('no openflow failmode')
    else:

        controllers = want['controllers']
        ports = want['ports']
        native_vlan = want['native_vlan']
        fail_mode = want['fail_mode']
        state = want['state']

        if state == 'absent':
            if fail_mode and fail_mode == 'standalone' and fail_mode == fail_mode_have:
                commands.append('no openflow failmode')
            if native_vlan and native_vlan != 1 and native_vlan == native_vlan_have:
                commands.append('no openflow native vlan')
            if controllers:
                for controller_w in controllers:
                    for controller_h in controllers_have:
                        if controller_w.get('name') == controller_h.get('name'):
                            commands.append(
                                'no openflow controller {0}'.format(controller_w['name']))
            if ports:
                for port_w in ports:
                    for port_h in ports_have:
                        if port_w.get('name') == port_h.get('name'):
                            commands.append(
                                'interface {0}'.format(port_w['name']))
                            commands.append('no openflow')
        elif state == 'present':
            if native_vlan and native_vlan != native_vlan_have:
                commands.append('openflow native vlan {0}'.format(native_vlan))

            if fail_mode and fail_mode != fail_mode_have:
                if fail_mode == 'secure':
                    commands.append(
                        'openflow failmode secure non-rule-expired')
                else:
                    commands.append('openflow failmode standalone')

            if controllers:
                for controller_w in controllers:
                    new_controller = True
                    cmd = 'openflow controller '
                    for controller_h in controllers_have:

                        if ((controller_w['address'] == controller_h['address'] and controller_w['ssl_port'] == controller_h['ssl_port'])
                                or controller_w['name'] == controller_h['name']):
                            new_controller = False
                            module.fail_json(
                                msg='Controller already exists, please use a different address/ssl port')

                    if new_controller:
                        if controller_w['name']:
                            cmd += controller['name'] + ' '
                            postfix = '{0} {1} {2}'.format(
                                controller_w['protocol'], controller_w['address'], controller_w['ssl_port'])
                            cmd += postfix
                            commands.append(cmd)
                        else:
                            postfix = '{0} {1} {2}'.format(
                                controller_w['protocol'], controller_w['address'], controller_w['ssl_port'])
                            cmd += postfix
                            commands.append(cmd)

            if ports:
                for port_w in ports:
                    new_port = True
                    for port_h in ports_have:

                        if port_w['name'] == port_h['name']:
                            new_port = False
                            if port_w['openflow'] != port_h['openflow']:
                                commands.append(
                                    'interface {0}'.format(port_w['name']))
                                if port_w.get('openflow'):
                                    commands.append('openflow')
                                else:
                                    commands.append('no openflow')

                    if new_port:
                        if not port_w['name'].startswith('po'):
                            module.fail_json(msg='Invalid port name')
                        commands.append('interface {0}'.format(port_w['name']))
                        if port_w.get('openflow'):
                            commands.append('openflow')
                        else:
                            commands.append('no openflow')

    return commands


def get_openflow_config(module):
    return run_commands(module, 'show openflow config')


def parse_name(line):
    match = re.search(r'name="(\S+)"', line, re.U)
    if match:
        return match.group(1)


def parse_ports(line):
    port = dict()
    match = re.search(r'Port "(port\S+)"', line)
    if match:
        port['name'] = match.group(1)
        port['openflow'] = True
        return port


def parse_native_vlan(line):
    match = re.search(r'native_vlan="(\d+)"', line, re.U)
    if match:
        return int(match.group(1))


def parse_fail_mode(line):
    match = re.match(r'fail_mode: (\w+)', line)
    if match:
        return match.group(1)


def map_config_to_obj(module):
    obj_dict = dict()
    obj_dict['ports'] = []
    obj_dict['controllers'] = []
    obj = []

    config = get_openflow_config(module)
    lines = config.splitlines()

    for i in range(len(lines)):
        lines[i] = lines[i].strip()
        oc = re.match(r'Controller "(tcp|ssl):(\S+):(\d+)"', lines[i])
        if oc:
            oc_dict = dict()
            oc_dict['protocol'] = oc.group(1)
            oc_dict['address'] = oc.group(2)
            oc_dict['ssl_port'] = oc.group(3)
            oc_dict['name'] = parse_name(lines[i + 1].strip())
            obj_dict['controllers'].append(oc_dict)

        port = parse_ports(lines[i])
        if port:
            obj_dict['ports'].append(port)

        native_vlan = parse_native_vlan(lines[i])
        if native_vlan:
            obj_dict['native_vlan'] = native_vlan

        fail_mode = parse_fail_mode(lines[i])
        if fail_mode:
            obj_dict['fail_mode'] = fail_mode

    obj.append(obj_dict)
    return obj


def map_params_to_obj(module):
    obj = []

    obj.append({
        'native_vlan': module.params['native_vlan'],
        'fail_mode': module.params['fail_mode'],
        'state': module.params['state'],
        'ports': module.params['ports'],
        'controllers': module.params['controllers']
    })
    return obj


def main():
    """ main entry point for module execution
    """
    controller_spec = dict(
        name=dict(type='str'),
        protocol=dict(type='str', choices=['ssl', 'tcp'], required=True),
        address=dict(type='str', required=True),
        ssl_port=dict(type='int', required=True)
    )

    port_spec = dict(
        name=dict(type='str', required=True),
        openflow=dict(type='bool', default=True)
    )
    argument_spec = dict(
        controllers=dict(type='list', elements='dict',
                         options=controller_spec),
        native_vlan=dict(type='int'),
        fail_mode=dict(type='str', choices=['secure', 'standalone']),
        ports=dict(type='list', elements='dict', options=port_spec),
        state=dict(type='str', default='present',
                   choices=['present', 'absent'])
    )

    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
