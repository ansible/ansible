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
module: asa_og
version_added: "2.8"
author:
    - "Federico Olivieri (@Federico87)"
short_description: Manage object groups on a Cisco ASA
description:
    - This module allows you to create and update object-group network/service on Cisco ASA device.
options:
    name:
        description:
            - Name of the object group.
        required: true
    group_type:
        description:
            - The object group type.
        choices: ['network-object', 'service-object', 'port-object']
        required: true
    protocol:
        description:
            - The protocol for object-group service with port-object.
        choices: ['udp', 'tcp', 'tcp-udp']
    host_ip:
        description:
            - The host IP address for object-group network.
        type: list
    description:
        description:
            - The description for the object-group.
    group_object:
        description:
            - The group-object for network object-group.
        type: list
    ip_mask:
        description:
            - The IP address and mask for network object-group.
        type: list
    port_range:
        description:
            - The port range for port-object.
    port_eq:
        description:
            - The single port for port-object.
    service_cfg:
        description:
            - The service-object configuration protocol, direction, range or port.
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present', 'absent', 'replace']
"""

EXAMPLES = """
---
- name: configure network object-group
  asa_og:
    name: ansible_test_0
    group_type: network-object
    state: present
    description: ansible_test object-group description
    host_ip:
      - 8.8.8.8
      - 8.8.4.4
    ip_mask:
      - 10.0.0.0 255.255.255.0
      - 192.168.0.0 255.255.0.0
    group_object:
      - awx_lon
      - awx_ams

- name: configure port-object object-group
  asa_og:
    name: ansible_test_1
    group_type: port-object
    state: replace
    description: ansible_test object-group description
    protocol: tcp-udp
    port_eq:
      - 1025
      - kerberos
    port_range:
      - 1025 5201
      - 0 1024

- name: configure service-object object-group
  asa_og:
    name: ansible_test_2
    group_type: service-object
    state: absent
    description: ansible_test object-group description
    service_cfg:
      - tcp destination eq 8080
      - tcp destination eq www
"""

RETURN = """
commands:
  description: command sent to the device
  returned: always
  type: list
  sample: [
    "object-group network ansible_test_0",
    "description ansible_test object-group description",
    "network-object host 8.8.8.8",
    "network-object host 8.8.4.4",
    "network-object 10.0.0.0 255.255.255.0",
    "network-object 192.168.0.0 255.255.0.0",
    "network-object 192.168.0.0 255.255.0.0",
    "group-object awx_lon",
    "group-object awx_ams",
    ]
"""
import re
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.asa.asa import check_args
from ansible.module_utils.network.asa.asa import get_config, load_config, run_commands
from ansible.module_utils.network.common.config import NetworkConfig, dumps


class Parser():
    '''Regex class for outputs parsing'''

    def __init__(self, config, protocol):
        '''Parser __init__ method'''
        self.config = config
        self.protocol = protocol

    def parse_obj_grp_name(self):
        list_return = list()
        match = re.search(r'(?:object-group\s)(network\s|service\s)(\w+)\s?(tcp-udp|tcp|udp)?', self.config, re.M)

        if match:
            if match.group(3):
                list_return.append(str(match.group(3)))
            else:
                list_return.append(False)

            if match.group(2):
                list_return.append(str(match.group(2)))

            if match.group(1):
                list_return.append(str(match.group(1)))

        return list_return

    def parse_description(self):
        match = re.search(r'(description\s)(.*)', self.config, re.M)
        if match:
            description = match.group(2)

            return description

    def parse_host(self):
        list_return = list()
        match = re.findall(r'(host\s)(\d+\.\d+\.\d+\.\d+)', self.config, re.M)

        if match:
            for i in match:
                if i[1]:
                    list_return.append(str(i[1]))

        return list_return

    def parse_group_object(self):
        list_return = list()
        match = re.findall(r'(group-object\s)(.*)', self.config, re.M)

        if match:
            for i in match:
                if i[1]:
                    list_return.append(str(i[1]))

        return list_return

    def parse_address(self):
        list_return = list()
        match = re.findall(r'(network-object\s)(\d+\.\d+\.\d+\.\d+\s\d+\.\d+\.\d+\.\d+)', self.config, re.M)

        if match:
            for i in match:
                if i[1]:
                    list_return.append(str(i[1]))

        return list_return

    def parse_port_range(self):
        list_return = list()
        match = re.findall(r'(range\s)(.*)', self.config, re.M)

        if match:
            for i in match:
                if i[1]:
                    list_return.append(str(i[1]))

        return list_return

    def parse_port_eq(self):
        list_return = list()
        match = re.findall(r'(eq\s)(.*)', self.config, re.M)

        if match:
            for i in match:
                if i[1]:
                    list_return.append(str(i[1]))

        return list_return

    def parse_service_cfg(self):
        list_return = list()
        match = re.findall(r'(service-object\s)(.*)', self.config, re.M)

        if match:
            for i in match:
                if i[1]:
                    list_return.append(str(i[1]))

        return list_return


def map_config_to_obj(module):

    obj = list()
    obj_dict = dict()

    group_type = module.params['group_type']
    group_name = module.params['name']
    protocol = module.params['protocol']

    sh_run_group_name = get_config(module, flags=['object-group | include {0}'.format(group_name)])
    run_group_name = Parser(sh_run_group_name, protocol).parse_obj_grp_name()

    obj_dict['have_name'] = run_group_name

    if run_group_name:
        if run_group_name[0] is not False:
            obj_dict['have_group_type'] = "port-object"
            obj_dict['have_protocol'] = run_group_name[0]
        elif 'network' in run_group_name[2]:
            obj_dict['have_group_type'] = "network-object"
        elif 'service' in run_group_name[2] and run_group_name[0] is False:
            obj_dict['have_group_type'] = "service-object"
        else:
            obj_dict['have_group_type'] = None

    sh_run_group_type = get_config(module, flags=['object-group id {0}'.format(group_name)])

    have_description = Parser(sh_run_group_type, protocol).parse_description()
    obj_dict['have_description'] = have_description

    have_host_ip = Parser(sh_run_group_type, protocol).parse_host()
    obj_dict['have_host_ip'] = have_host_ip

    have_group_object = Parser(sh_run_group_type, protocol).parse_group_object()
    obj_dict['have_group_object'] = have_group_object

    have_ip_mask = Parser(sh_run_group_type, protocol).parse_address()
    obj_dict['have_ip_mask'] = have_ip_mask

    have_port_range = Parser(sh_run_group_type, protocol).parse_port_range()
    obj_dict['have_port_range'] = have_port_range

    have_port_eq = Parser(sh_run_group_type, protocol).parse_port_eq()
    obj_dict['have_port_eq'] = have_port_eq

    have_service_cfg = Parser(sh_run_group_type, protocol).parse_service_cfg()

    if have_service_cfg:
        have_lines = list()
        for i in have_service_cfg:
            have_lines.append(i.rstrip(' '))
        obj_dict['have_service_cfg'] = have_lines
    elif have_service_cfg is None:
        obj_dict['have_service_cfg'] = have_service_cfg

    obj.append(obj_dict)

    return obj


def replace(want_dict, have):

    commands = list()
    add_lines = list()
    remove_lines = list()

    have_name = have[0].get('have_name')
    have_group_type = have[0].get('have_group_type')
    have_config = have[0].get('have_lines')
    have_description = have[0].get('have_description')
    have_host_ip = have[0].get('have_host_ip')
    have_group_object = have[0].get('have_group_object')
    have_ip_mask = have[0].get('have_ip_mask')
    have_protocol = have[0].get('have_protocol')
    have_port_range = have[0].get('have_port_range')
    have_port_eq = have[0].get('have_port_eq')
    have_service_cfg = have[0].get('have_service_cfg')

    name = want_dict['name']
    group_type = want_dict['group_type']
    protocol = want_dict['protocol']
    description = want_dict['description']
    host = want_dict['host_ip']
    group_object = want_dict['group_object']
    address = want_dict['ip_mask']
    port_range = want_dict['port_range']
    port_eq = want_dict['port_eq']
    service_cfg = want_dict['service_cfg']

    if 'network-object' in group_type:

        if have_group_type is None:
            commands.append('object-group network {0}'.format(name))

            if host:
                for i in host:
                    commands.append('network-object host ' + i)
            if description:
                if have_description is None:
                    commands.append('description {0}'.format(description))
            if group_object:
                for i in group_object:
                    if i not in have_group_object:
                        commands.append('group-object ' + i)
            if address:
                for i in address:
                    commands.append('network-object ' + i)

        elif 'network' in have_group_type:

            if host:
                if sorted(host) != sorted(have_host_ip):
                    for i in host:
                        if i not in have_host_ip:
                            if 'object-group network {0}'.format(name) not in commands:
                                commands.append('object-group network {0}'.format(name))
                            add_lines.append('network-object host ' + i)
                    for i in have_host_ip:
                        if i not in host:
                            if 'object-group network {0}'.format(name) not in commands:
                                commands.append('object-group network {0}'.format(name))
                            remove_lines.append('no network-object host ' + i)

            if description:
                if description != have_description:
                    if 'object-group network {0}'.format(name) not in commands:
                        commands.append('object-group network {0}'.format(name))
                    add_lines.append('description {0}'.format(description))

            if group_object:
                if sorted(group_object) != sorted(have_group_object):
                    for i in group_object:
                        if i not in have_group_object:
                            if 'object-group network {0}'.format(name) not in commands:
                                commands.append('object-group network {0}'.format(name))
                            add_lines.append('group-object ' + i)
                    for i in have_group_object:
                        if i not in group_object:
                            if 'object-group network {0}'.format(name) not in commands:
                                commands.append('object-group network {0}'.format(name))
                            remove_lines.append('no group-object ' + i)
            if address:
                if sorted(address) != sorted(have_ip_mask):
                    for i in address:
                        if i not in have_ip_mask:
                            if 'object-group network {0}'.format(name) not in commands:
                                commands.append('object-group network {0}'.format(name))
                            add_lines.append('network-object ' + i)
                    for i in have_ip_mask:
                        if i not in address:
                            if 'object-group network {0}'.format(name) not in commands:
                                commands.append('object-group network {0}'.format(name))
                            remove_lines.append('no network-object ' + i)

    elif 'port-object' in group_type:

        if have_group_type is None and have_protocol != protocol:
            commands.append('object-group service {0} {1}'.format(name, protocol))

            if port_range:
                for i in port_range:
                    commands.append('port-object range ' + i)
            if port_eq:
                for i in port_eq:
                    commands.append('port-object eq ' + i)
            if description:
                commands.append('description {0}'.format(description))

        elif 'port' in have_group_type and have_protocol == protocol:

            if port_range:
                if sorted(port_range) != sorted(have_port_range):
                    for i in port_range:
                        if i not in have_port_range:
                            if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                                commands.append('object-group service {0} {1}'.format(name, protocol))
                            add_lines.append('port-object range ' + i)
                    for i in have_port_range:
                        if i not in port_range:
                            if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                                commands.append('object-group service {0} {1}'.format(name, protocol))
                            remove_lines.append('no port-object range ' + i)
            if port_eq:
                if sorted(port_eq) != sorted(have_port_eq):
                    for i in port_eq:
                        if i not in have_port_eq:
                            if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                                commands.append('object-group service {0} {1}'.format(name, protocol))
                            add_lines.append('port-object eq ' + i)
                    for i in have_port_eq:
                        if i not in port_eq:
                            if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                                commands.append('object-group service {0} {1}'.format(name, protocol))
                            remove_lines.append('no port-object eq ' + i)
            if description:
                if description != have_description:
                    if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                        commands.append('object-group service {0} {1}'.format(name, protocol))
                    commands.append('description {0}'.format(description))

    elif 'service-object' in group_type:

        if have_group_type is None:
            commands.append('object-group service {0}'.format(name))

            if description:
                if have_description is None:
                    commands.append('description {0}'.format(description))
            if service_cfg:
                for i in service_cfg:
                    commands.append('service-object ' + i)

        elif 'service' in have_group_type:
            if description:
                if description != have_description:
                    if 'object-group service {0}'.format(name) not in commands:
                        commands.append('object-group service {0}'.format(name))
                    commands.append('description {0}'.format(description))
            if service_cfg:
                for i in service_cfg:
                    if i not in have_service_cfg:
                        if 'object-group service {0}'.format(name) not in commands:
                            commands.append('object-group service {0}'.format(name))
                        add_lines.append('service ' + i)
                for i in have_service_cfg:
                    if i not in service_cfg:
                        if 'object-group service {0}'.format(name) not in commands:
                            commands.append('object-group service {0}'.format(name))
                        remove_lines.append('no service ' + i)

    set_add_lines = set(add_lines)
    set_remove_lines = set(remove_lines)

    for i in list(set_add_lines) + list(set_remove_lines):
        commands.append(i)

    return commands


def present(want_dict, have):

    commands = list()

    have_name = have[0].get('have_name')
    have_group_type = have[0].get('have_group_type')
    have_config = have[0].get('have_lines')
    have_description = have[0].get('have_description')
    have_host_ip = have[0].get('have_host_ip')
    have_group_object = have[0].get('have_group_object')
    have_ip_mask = have[0].get('have_ip_mask')
    have_protocol = have[0].get('have_protocol')
    have_port_range = have[0].get('have_port_range')
    have_port_eq = have[0].get('have_port_eq')
    have_service_cfg = have[0].get('have_service_cfg')

    name = want_dict['name']
    group_type = want_dict['group_type']
    protocol = want_dict['protocol']
    description = want_dict['description']
    host = want_dict['host_ip']
    group_object = want_dict['group_object']
    address = want_dict['ip_mask']
    port_range = want_dict['port_range']
    port_eq = want_dict['port_eq']
    service_cfg = want_dict['service_cfg']

    if 'network-object' in group_type:

        if have_group_type is None:
            commands.append('object-group network {0}'.format(name))

            if host:
                for i in host:
                    commands.append('network-object host ' + i)
            if description:
                if have_description is None:
                    commands.append('description {0}'.format(description))
            if group_object:
                for i in group_object:
                    commands.append('group-object ' + i)
            if address:
                for i in address:
                    commands.append('network-object ' + i)

        elif 'network' in have_group_type:

            if host:
                for i in host:
                    if i not in have_host_ip:
                        if 'object-group network {0}'.format(name) not in commands:
                            commands.append('object-group network {0}'.format(name))
                        commands.append('network-object host ' + i)
            if description:
                if description != have_description:
                    if 'object-group network {0}'.format(name) not in commands:
                        commands.append('object-group network {0}'.format(name))
                    commands.append('description {0}'.format(description))
            if group_object:
                for i in group_object:
                    if i not in have_group_object:
                        if 'object-group network {0}'.format(name) not in commands:
                            commands.append('object-group network {0}'.format(name))
                        commands.append('group-object ' + i)
            if address:
                for i in address:
                    if i not in have_ip_mask:
                        if 'object-group network {0}'.format(name) not in commands:
                            commands.append('object-group network {0}'.format(name))
                        commands.append('network-object ' + i)

    elif 'port-object' in group_type:

        if have_group_type is None and have_protocol != protocol:
            commands.append('object-group service {0} {1}'.format(name, protocol))

            if port_range:
                for i in port_range:
                    commands.append('port-object range ' + i)
            if port_eq:
                for i in port_eq:
                    commands.append('port-object eq ' + i)
            if description:
                commands.append('description {0}'.format(description))

        elif 'port' in have_group_type and have_protocol == protocol:

            if port_range:
                for i in port_range:
                    if i not in have_port_range:
                        if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                            commands.append('object-group service {0} {1}'.format(name, protocol))
                        commands.append('port-object range ' + i)
            if port_eq:
                for i in port_eq:
                    if i not in have_port_eq:
                        if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                            commands.append('object-group service {0} {1}'.format(name, protocol))
                        commands.append('port-object eq ' + i)
            if description:
                if description != have_description:
                    if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                        commands.append('object-group service {0} {1}'.format(name, protocol))
                    commands.append('description {0}'.format(description))

    elif 'service-object' in group_type:

        if have_group_type is None:
            commands.append('object-group service {0}'.format(name))

            if description:
                if have_description is None:
                    commands.append('description {0}'.format(description))
            if service_cfg:
                for i in service_cfg:
                    commands.append('service-object ' + i)

        elif 'service' in have_group_type:

            if description:
                if description != have_description:
                    if 'object-group service {0}'.format(name) not in commands:
                        commands.append('object-group service {0}'.format(name))
                    commands.append('description {0}'.format(description))
            if service_cfg:
                for i in service_cfg:
                    if i not in have_service_cfg:
                        if 'object-group service {0}'.format(name) not in commands:
                            commands.append('object-group service {0}'.format(name))
                        commands.append('service ' + i)

    return commands


def absent(want_dict, have):

    commands = list()

    have_name = have[0].get('have_name')
    have_group_type = have[0].get('have_group_type')
    have_config = have[0].get('have_lines')
    have_description = have[0].get('have_description')
    have_host_ip = have[0].get('have_host_ip')
    have_group_object = have[0].get('have_group_object')
    have_ip_mask = have[0].get('have_ip_mask')
    have_protocol = have[0].get('have_protocol')
    have_port_range = have[0].get('have_port_range')
    have_port_eq = have[0].get('have_port_eq')
    have_service_cfg = have[0].get('have_service_cfg')

    name = want_dict['name']
    group_type = want_dict['group_type']
    protocol = want_dict['protocol']
    description = want_dict['description']
    host = want_dict['host_ip']
    group_object = want_dict['group_object']
    address = want_dict['ip_mask']
    port_range = want_dict['port_range']
    port_eq = want_dict['port_eq']
    service_cfg = want_dict['service_cfg']

    if 'network-object' in group_type:

        if have_group_type is None:
            return commands

        elif 'network' in have_group_type:

            if host:
                for i in host:
                    if i in have_host_ip:
                        if 'object-group network {0}'.format(name) not in commands:
                            commands.append('object-group network {0}'.format(name))
                        commands.append('no network-object host ' + i)
            if description:
                if description == have_description:
                    if 'object-group network {0}'.format(name) not in commands:
                        commands.append('object-group network {0}'.format(name))
                    commands.append('no description {0}'.format(description))
            if group_object:
                for i in group_object:
                    if i in have_group_object:
                        if 'object-group network {0}'.format(name) not in commands:
                            commands.append('object-group network {0}'.format(name))
                        commands.append('no group-object ' + i)
            if address:
                for i in address:
                    if i in have_ip_mask:
                        if 'object-group network {0}'.format(name) not in commands:
                            commands.append('object-group network {0}'.format(name))
                        commands.append('no network-object ' + i)

    elif 'port-object' in group_type:

        if have_group_type is None and have_protocol is None:
            return commands

        elif 'port' in have_group_type and have_protocol == protocol:

            if port_range:
                for i in port_range:
                    if i in have_port_range:
                        if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                            commands.append('object-group service {0} {1}'.format(name, protocol))
                        commands.append('no port-object range ' + i)
            if port_eq:
                for i in port_eq:
                    if i in have_port_eq:
                        if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                            commands.append('object-group service {0} {1}'.format(name, protocol))
                        commands.append('no port-object eq ' + i)
            if description:
                if description == have_description:
                    if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                        commands.append('object-group service {0} {1}'.format(name, protocol))
                    commands.append('no description {0}'.format(description))

    elif 'service-object' in group_type:

        if have_group_type is None:
            return commands

        elif 'service' in have_group_type:
            if description:
                if description == have_description:
                    if 'object-group service {0}'.format(name) not in commands:
                        commands.append('object-group service {0}'.format(name))
                    commands.append('no description {0}'.format(description))
            if service_cfg:
                for i in service_cfg:
                    if i in have_service_cfg:
                        if 'object-group service {0}'.format(name) not in commands:
                            commands.append('object-group service {0}'.format(name))
                        commands.append('no service ' + i)

    return commands


def map_obj_to_commands(want, have, module):

    for w in want:

        want_dict = dict()

        want_dict['name'] = w['name']
        want_dict['group_type'] = w['group_type']
        want_dict['protocol'] = w['protocol']
        want_dict['description'] = w['description']
        want_dict['host_ip'] = w['host_ip']
        want_dict['group_object'] = w['group_object']
        want_dict['ip_mask'] = w['ip_mask']
        want_dict['port_range'] = w['port_range']
        want_dict['port_eq'] = w['port_eq']
        want_dict['service_cfg'] = w['service_cfg']
        state = w['state']

        if state == 'replace':
            return replace(want_dict, have)
        elif state == 'present':
            return present(want_dict, have)
        elif state == 'absent':
            return absent(want_dict, have)


def map_params_to_obj(module):

    obj = list()

    obj.append({
        'name': module.params['name'],
        'group_type': module.params['group_type'],
        'protocol': module.params['protocol'],
        'state': module.params['state'],
        'description': module.params['description'],
        'host_ip': module.params['host_ip'],
        'group_object': module.params['group_object'],
        'port_range': module.params['port_range'],
        'port_eq': module.params['port_eq'],
        'service_cfg': module.params['service_cfg'],
        'ip_mask': module.params['ip_mask']
    })

    return obj


def main():

    argument_spec = dict(
        name=dict(required=True),
        group_type=dict(choices=['network-object', 'service-object', 'port-object'], required=True),
        protocol=dict(choices=['udp', 'tcp', 'tcp-udp']),
        host_ip=dict(type='list'),
        description=dict(),
        group_object=dict(type='list'),
        ip_mask=dict(type='list'),
        port_range=dict(type='list'),
        port_eq=dict(type='list'),
        service_cfg=dict(type='list'),
        state=dict(choices=['present', 'absent', 'replace'], default='present')
    )

    required_if = [('group_type', 'port-object', ['protocol']),
                   ('group_type', 'service-object', ['service_cfg'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    config_commans = map_obj_to_commands(want, have, module)

    result['commands'] = config_commans

    if config_commans:
        if not module.check_mode:
            load_config(module, config_commans)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
