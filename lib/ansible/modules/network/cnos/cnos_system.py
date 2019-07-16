#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2019 Lenovo.
# (c) 2017, Ansible by Red Hat, inc
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
# Module to work on System Configuration with Lenovo Switches
# Lenovo Networking
#
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cnos_system
version_added: "2.8"
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage the system attributes on Lenovo CNOS devices
description:
  - This module provides declarative management of node system attributes
    on Lenovo CNOS devices.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an
        ASCII string value or keyword 'default'
  domain_name:
    description:
      - Configures the default domain
        name suffix to be used when referencing this node by its
        FQDN.  This argument accepts either a list of domain names or
        a list of dicts that configure the domain name and VRF name or
        keyword 'default'. See examples.
  lookup_enabled:
    description:
      - Administrative control for enabling or disabling DNS lookups.
        When this argument is set to True, lookups are performed and
        when it is set to False, lookups are not performed.
    type: bool
  domain_search:
    description:
      - Configures a list of domain
        name suffixes to search when performing DNS name resolution.
        This argument accepts either a list of domain names or
        a list of dicts that configure the domain name and VRF name or
        keyword 'default'. See examples.
  name_servers:
    description:
      - List of DNS name servers by IP address to use to perform name resolution
        lookups.  This argument accepts either a list of DNS servers or
        a list of hashes that configure the name server and VRF name or
        keyword 'default'. See examples.
  lookup_source:
    description:
      - Provides one or more source interfaces to use for performing DNS
        lookups. The interface must be a valid interface configured.
        on the device.
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure hostname and domain-name
  cnos_system:
    hostname: cnos01
    domain_name: test.example.com

- name: remove configuration
  cnos_system:
    state: absent

- name: configure name servers
  cnos_system:
    name_servers:
      - 8.8.8.8
      - 8.8.4.4

- name: configure DNS Lookup sources
  cnos_system:
    lookup_source: MgmtEth0/0/CPU0/0
    lookup_enabled: yes

- name: configure name servers with VRF support
  nxos_system:
    name_servers:
      - { server: 8.8.8.8, vrf: mgmt }
      - { server: 8.8.4.4, vrf: mgmt }
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - hostname cnos01
    - ip domain-name test.example.com vrf default
"""
import re

from ansible.module_utils.network.cnos.cnos import get_config, load_config
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec
from ansible.module_utils.network.cnos.cnos import check_args, debugOutput
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import ComplexList

_CONFIGURED_VRFS = None


def map_obj_to_commands(want, have, module):
    commands = list()
    state = module.params['state']

    def needs_update(x):
        return want.get(x) and (want.get(x) != have.get(x))

    def difference(x, y, z):
        return [item for item in x[z] if item not in y[z]]

    if state == 'absent':
        if have['hostname']:
            commands.append('no hostname')

        for item in have['domain_name']:
            my_vrf = 'default'
            if item['vrf'] is not None:
                my_vrf = item['vrf']
            cmd = 'no ip domain-name {0} vrf {1}'.format(item['name'], my_vrf)
            commands.append(cmd)

        for item in have['domain_search']:
            my_vrf = 'default'
            if item['vrf'] is not None:
                my_vrf = item['vrf']
            cmd = 'no ip domain-list {0} vrf {1}'.format(item['name'], my_vrf)
            commands.append(cmd)

        for item in have['name_servers']:
            my_vrf = 'default'
            if item['vrf'] is not None:
                my_vrf = item['vrf']
            cmd = 'no ip name-server {0} vrf {1}'.format(item['server'], my_vrf)
            commands.append(cmd)

    if state == 'present':
        if needs_update('hostname'):
            if want['hostname'] == 'default':
                if have['hostname']:
                    commands.append('no hostname')
            else:
                commands.append('hostname %s' % want['hostname'])

        if want.get('lookup_enabled') is not None:
            if have.get('lookup_enabled') != want.get('lookup_enabled'):
                cmd = 'ip domain-lookup'
                if want['lookup_enabled'] is False:
                    cmd = 'no %s' % cmd
                commands.append(cmd)

        if want['domain_name']:
            if want.get('domain_name')[0]['name'] == 'default':
                if have['domain_name']:
                    for item in have['domain_name']:
                        my_vrf = 'default'
                        if item['vrf'] is not None:
                            my_vrf = item['vrf']
                        cmd = 'no ip domain-name {0} vrf {1}'.format(item['name'], my_vrf)
                        commands.append(cmd)
            else:
                for item in difference(have, want, 'domain_name'):
                    my_vrf = 'default'
                    if item['vrf'] is not None:
                        my_vrf = item['vrf']
                    cmd = 'no ip domain-name {0} vrf {1}'.format(item['name'], my_vrf)
                    commands.append(cmd)
                for item in difference(want, have, 'domain_name'):
                    my_vrf = 'default'
                    if item['vrf'] is not None:
                        my_vrf = item['vrf']
                    cmd = 'ip domain-name {0} vrf {1}'.format(item['name'], my_vrf)
                    commands.append(cmd)

        if want['domain_search']:
            if want.get('domain_search')[0]['name'] == 'default':
                if have['domain_search']:
                    for item in have['domain_search']:
                        my_vrf = 'default'
                        if item['vrf'] is not None:
                            my_vrf = item['vrf']
                        cmd = 'no ip domain-list {0} vrf {1}'.format(item['name'], my_vrf)
                        commands.append(cmd)
            else:
                for item in difference(have, want, 'domain_search'):
                    my_vrf = 'default'
                    if item['vrf'] is not None:
                        my_vrf = item['vrf']
                    cmd = 'no ip domain-list {0} vrf {1}'.format(item['name'], my_vrf)
                    commands.append(cmd)
                for item in difference(want, have, 'domain_search'):
                    my_vrf = 'default'
                    if item['vrf'] is not None:
                        my_vrf = item['vrf']
                    cmd = 'ip domain-list {0} vrf {1}'.format(item['name'], my_vrf)
                    commands.append(cmd)

        if want['name_servers']:
            if want.get('name_servers')[0]['server'] == 'default':
                if have['name_servers']:
                    for item in have['name_servers']:
                        my_vrf = 'default'
                        if item['vrf'] is not None:
                            my_vrf = item['vrf']
                        cmd = 'no ip name-server {0} vrf {1}'.format(item['server'], my_vrf)
                        commands.append(cmd)
            else:
                for item in difference(have, want, 'name_servers'):
                    my_vrf = 'default'
                    if item['vrf'] is not None:
                        my_vrf = item['vrf']
                    cmd = 'no ip name-server {0} vrf {1}'.format(item['server'], my_vrf)
                    commands.append(cmd)
                for item in difference(want, have, 'name_servers'):
                    my_vrf = 'default'
                    if item['vrf'] is not None:
                        my_vrf = item['vrf']
                    cmd = 'ip name-server {0} vrf {1}'.format(item['server'], my_vrf)
                    commands.append(cmd)

    return commands


def parse_hostname(config):
    match = re.search(r'^hostname (\S+)', config, re.M)
    if match:
        return match.group(1)


def parse_domain_name(config):
    objects = list()
    myconf = config.splitlines()
    for line in myconf:
        if 'ip domain-name' in line:
            datas = line.split()
            objects.append({'name': datas[2], 'vrf': datas[4]})

    return objects


def parse_domain_search(config):
    objects = list()
    myconf = config.splitlines()
    for line in myconf:
        if 'ip domain-list' in line:
            datas = line.split()
            objects.append({'name': datas[2], 'vrf': datas[4]})

    return objects


def parse_name_servers(config):
    objects = list()
    myconf = config.splitlines()
    for line in myconf:
        if 'ip name-server' in line:
            datas = line.split()
            objects.append({'server': datas[2], 'vrf': datas[4]})

    return objects


def map_config_to_obj(module):
    config = get_config(module)
    configobj = NetworkConfig(indent=2, contents=config)

    return {
        'hostname': parse_hostname(config),
        'lookup_enabled': 'no ip domain-lookup' not in config,
        'domain_name': parse_domain_name(config),
        'domain_search': parse_domain_search(config),
        'name_servers': parse_name_servers(config),
    }


def map_params_to_obj(module):
    obj = {
        'hostname': module.params['hostname'],
        'lookup_enabled': module.params['lookup_enabled'],
    }

    domain_name = ComplexList(dict(
        name=dict(key=True),
        vrf=dict()
    ), module)

    domain_search = ComplexList(dict(
        name=dict(key=True),
        vrf=dict()
    ), module)

    name_servers = ComplexList(dict(
        server=dict(key=True),
        vrf=dict()
    ), module)

    for arg, cast in [('domain_name', domain_name),
                      ('domain_search', domain_search),
                      ('name_servers', name_servers)]:
        if module.params[arg] is not None:
            obj[arg] = cast(module.params[arg])
        else:
            obj[arg] = None

    return obj


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        hostname=dict(),
        lookup_enabled=dict(type='bool'),

        # { name: <str>, vrf: <str> }
        domain_name=dict(type='list'),

        # {name: <str>, vrf: <str> }
        domain_search=dict(type='list'),

        # { server: <str>; vrf: <str> }
        name_servers=dict(type='list'),

        lookup_source=dict(type='str'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

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
