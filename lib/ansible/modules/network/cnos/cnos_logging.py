#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2019 Lenovo, Inc.
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
# Module to work on Link Aggregation with Lenovo Switches
# Lenovo Networking
#
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cnos_logging
version_added: "2.8"
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on Cisco Cnos devices.
notes:
  - Tested against CNOS 10.9.1
options:
  dest:
    description:
      - Destination of the logs. Lenovo uses the term server instead of host in
        its CLI.
    choices: ['server', 'console', 'monitor', 'logfile']
  name:
    description:
      - If value of C(dest) is I(file) it indicates file-name
        and for I(server) indicates the server name to be notified.
  size:
    description:
      - Size of buffer. The acceptable value is in range from 4096 to
        4294967295 bytes.
    default: 10485760
  facility:
    description:
      - Set logging facility. This is applicable only for server logging
  level:
    description:
      - Set logging severity levels. 0-emerg;1-alert;2-crit;3-err;4-warn;
        5-notif;6-inform;7-debug
    default: 5
  aggregate:
    description: List of logging definitions.
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure server logging
  cnos_logging:
    dest: server
    name: 10.241.107.224
    facility: local7
    state: present

- name: remove server logging configuration
  cnos_logging:
    dest: server
    name: 10.241.107.224
    state: absent

- name: configure console logging level and facility
  cnos_logging:
    dest: console
    level: 7
    state: present

- name: configure buffer size
  cnos_logging:
    dest: logfile
    level: 5
    name: testfile
    size: 5000

- name: Configure logging using aggregate
  cnos_logging:
    aggregate:
      - { dest: console, level: 6 }
      - { dest: logfile, size: 9000 }

- name: remove logging using aggregate
  cnos_logging:
    aggregate:
      - { dest: console, level: 6 }
      - { dest: logfile, name: anil, size: 9000 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - logging console 7
    - logging server 10.241.107.224
"""

import re

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import validate_ip_address
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.cnos.cnos import get_config, load_config
from ansible.module_utils.network.cnos.cnos import get_capabilities
from ansible.module_utils.network.cnos.cnos import check_args
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec


def validate_size(value, module):
    if value:
        if not int(4096) <= int(value) <= int(4294967295):
            module.fail_json(msg='size must be between 4096 and 4294967295')
        else:
            return value


def map_obj_to_commands(updates, module):
    dest_group = ('console', 'monitor', 'logfile', 'server')
    commands = list()
    want, have = updates
    for w in want:
        dest = w['dest']
        name = w['name']
        size = w['size']
        facility = w['facility']
        level = w['level']
        state = w['state']
        del w['state']

        if state == 'absent':
            if dest:

                if dest == 'server':
                    commands.append('no logging server {0}'.format(name))

                elif dest in dest_group:
                    commands.append('no logging {0}'.format(dest))

                else:
                    module.fail_json(msg='dest must be among console, monitor, logfile, server')

        if state == 'present' and w not in have:
            if dest == 'server':
                cmd_str = 'logging server {0}'.format(name)
                if level is not None and level > 0 and level < 8:
                    cmd_str = cmd_str + ' ' + level
                    if facility is not None:
                        cmd_str = cmd_str + ' facility ' + facility
                commands.append(cmd_str)

            elif dest == 'logfile' and size:
                present = False

                for entry in have:
                    if entry['dest'] == 'logfile' and entry['size'] == size and entry['level'] == level:
                        present = True

                if not present:
                    cmd_str = 'logging logfile '
                    if name is not None:
                        cmd_str = cmd_str + name
                        if level and level != '7':
                            cmd_str = cmd_str + ' ' + level
                        else:
                            cmd_str = cmd_str + ' 7'
                        if size is not None:
                            cmd_str = cmd_str + ' size ' + size
                        commands.append(cmd_str)
                    else:
                        module.fail_json(msg='Name of the logfile is a mandatory parameter')

            else:
                if dest:
                    dest_cmd = 'logging {0}'.format(dest)
                    if level:
                        dest_cmd += ' {0}'.format(level)
                    commands.append(dest_cmd)
    return commands


def parse_facility(line, dest):
    facility = None
    if dest == 'server':
        result = line.split()
        i = 0
        for x in result:
            if x == 'facility':
                return result[i + 1]
            i = i + 1
    return facility


def parse_size(line, dest):
    size = None
    if dest == 'logfile':
        if 'logging logfile' in line:
            result = line.split()
            i = 0
            for x in result:
                if x == 'size':
                    return result[i + 1]
                i = i + 1
            return '10485760'
    return size


def parse_name(line, dest):
    name = None
    if dest == 'server':
        if 'logging server' in line:
            result = line.split()
            i = 0
            for x in result:
                if x == 'server':
                    name = result[i + 1]
    elif dest == 'logfile':
        if 'logging logfile' in line:
            result = line.split()
            i = 0
            for x in result:
                if x == 'logfile':
                    name = result[i + 1]
    else:
        name = None
    return name


def parse_level(line, dest):
    level_group = ('0', '1', '2', '3', '4', '5', '6', '7')
    level = '7'
    if dest == 'server':
        if 'logging server' in line:
            result = line.split()
            if(len(result) > 3):
                if result[3].isdigit():
                    level = result[3]
    else:
        if dest == 'logfile':
            if 'logging logfile' in line:
                result = line.split()
                if result[3].isdigit():
                    level = result[3]
        else:
            match = re.search(r'logging {0} (\S+)'.format(dest), line, re.M)

    return level


def map_config_to_obj(module):
    obj = []
    dest_group = ('console', 'server', 'monitor', 'logfile')
    data = get_config(module, flags=['| include logging'])
    index = 0
    for line in data.split('\n'):
        logs = line.split()
        index = len(logs)
        if index == 0 or index == 1:
            continue
        if logs[0] != 'logging':
            continue
        if logs[1] == 'monitor' or logs[1] == 'console':
            obj.append({'dest': logs[1], 'level': logs[2]})
        elif logs[1] == 'logfile':
            level = '5'
            if index > 3 and logs[3].isdigit():
                level = logs[3]
            size = '10485760'
            if len(logs) > 4:
                size = logs[5]
            obj.append({'dest': logs[1], 'name': logs[2], 'size': size, 'level': level})
        elif logs[1] == 'server':
            level = '5'
            facility = None

            if index > 3 and logs[3].isdigit():
                level = logs[3]
            if index > 3 and logs[3] == 'facility':
                facility = logs[4]
            if index > 4 and logs[4] == 'facility':
                facility = logs[5]
            obj.append({'dest': logs[1], 'name': logs[2], 'facility': facility, 'level': level})
        else:
            continue
    return obj


def map_params_to_obj(module, required_if=None):
    obj = []
    aggregate = module.params.get('aggregate')

    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            module._check_required_if(required_if, item)

            d = item.copy()
            if d['dest'] != 'server' and d['dest'] != 'logfile':
                d['name'] = None

            if d['dest'] == 'logfile':
                if 'size' in d:
                    d['size'] = str(validate_size(d['size'], module))
                elif 'size' not in d:
                    d['size'] = str(10485760)
                else:
                    pass

            if d['dest'] != 'logfile':
                d['size'] = None

            obj.append(d)

    else:
        if module.params['dest'] != 'server' and module.params['dest'] != 'logfile':
            module.params['name'] = None

        if module.params['dest'] == 'logfile':
            if not module.params['size']:
                module.params['size'] = str(10485760)
        else:
            module.params['size'] = None

        if module.params['size'] is None:
            obj.append({
                'dest': module.params['dest'],
                'name': module.params['name'],
                'size': module.params['size'],
                'facility': module.params['facility'],
                'level': module.params['level'],
                'state': module.params['state']
            })

        else:
            obj.append({
                'dest': module.params['dest'],
                'name': module.params['name'],
                'size': str(validate_size(module.params['size'], module)),
                'facility': module.params['facility'],
                'level': module.params['level'],
                'state': module.params['state']
            })
    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        dest=dict(type='str',
                  choices=['server', 'console', 'monitor', 'logfile']),
        name=dict(type='str'),
        size=dict(type='int', default=10485760),
        facility=dict(type='str'),
        level=dict(type='str', default='5'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)

    required_if = [('dest', 'server', ['name'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)
    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module, required_if=required_if)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
