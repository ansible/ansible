#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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
module: ios_logging
version_added: "2.4"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on Cisco Ios devices.
notes:
  - Tested against IOS 15.6
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['on', 'host', 'console', 'monitor', 'buffered']
  name:
    description:
      - If value of C(dest) is I(file) it indicates file-name,
        for I(user) it indicates username and for I(host) indicates
        the host name to be notified.
  size:
    description:
      - Size of buffer. The acceptable value is in range from 4096 to
        4294967295 bytes.
    default: 4096
  facility:
    description:
      - Set logging facility.
  level:
    description:
      - Set logging severity levels.
  aggregate:
    description: List of logging definitions.
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: ios
"""

EXAMPLES = """
- name: configure host logging
  ios_logging:
    dest: host
    name: 172.16.0.1
    state: present

- name: remove host logging configuration
  ios_logging:
    dest: host
    name: 172.16.0.1
    state: absent

- name: configure console logging level and facility
  ios_logging:
    dest: console
    facility: local7
    level: debugging
    state: present

- name: enable logging to all
  ios_logging:
    dest : on

- name: configure buffer size
  ios_logging:
    dest: buffered
    size: 5000

- name: Configure logging using aggregate
  ios_logging:
    aggregate:
      - { dest: console, level: notifications }
      - { dest: buffered, size: 9000 }

- name: remove logging using aggregate
  ios_logging:
    aggregate:
      - { dest: console, level: notifications }
      - { dest: buffered, size: 9000 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - logging facility local7
    - logging host 172.16.0.1
"""

import re

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec, validate_ip_address
from ansible.module_utils.network.ios.ios import get_config, load_config
from ansible.module_utils.network.ios.ios import get_capabilities
from ansible.module_utils.network.ios.ios import ios_argument_spec, check_args


def validate_size(value, module):
    if value:
        if not int(4096) <= int(value) <= int(4294967295):
            module.fail_json(msg='size must be between 4096 and 4294967295')
        else:
            return value


def map_obj_to_commands(updates, module, os_version):
    dest_group = ('console', 'monitor', 'buffered', 'on')
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

        if facility:
            w['dest'] = 'facility'

        if state == 'absent' and w in have:
            if dest:
                if dest == 'host':
                    if '12.' in os_version:
                        commands.append('no logging {0}'.format(name))
                    else:
                        commands.append('no logging host {0}'.format(name))

                elif dest in dest_group:
                    commands.append('no logging {0}'.format(dest))

                else:
                    module.fail_json(msg='dest must be among console, monitor, buffered, host, on')

            if facility:
                commands.append('no logging facility {0}'.format(facility))

        if state == 'present' and w not in have:
            if facility:
                present = False

                for entry in have:
                    if entry['dest'] == 'facility' and entry['facility'] == facility:
                        present = True

                if not present:
                    commands.append('logging facility {0}'.format(facility))

            if dest == 'host':
                if '12.' in os_version:
                    commands.append('logging {0}'.format(name))
                else:
                    commands.append('logging host {0}'.format(name))

            elif dest == 'on':
                commands.append('logging on')

            elif dest == 'buffered' and size:
                present = False

                for entry in have:
                    if entry['dest'] == 'buffered' and entry['size'] == size and entry['level'] == level:
                        present = True

                if not present:
                    if level and level != 'debugging':
                        commands.append('logging buffered {0} {1}'.format(size, level))
                    else:
                        commands.append('logging buffered {0}'.format(size))

            else:
                if dest:
                    dest_cmd = 'logging {0}'.format(dest)
                    if level:
                        dest_cmd += ' {0}'.format(level)
                    commands.append(dest_cmd)
    return commands


def parse_facility(line, dest):
    facility = None
    if dest == 'facility':
        match = re.search(r'logging facility (\S+)', line, re.M)
        if match:
            facility = match.group(1)

    return facility


def parse_size(line, dest):
    size = None

    if dest == 'buffered':
        match = re.search(r'logging buffered(?: (\d+))?(?: [a-z]+)?', line, re.M)
        if match:
            if match.group(1) is not None:
                size = match.group(1)
            else:
                size = "4096"

    return size


def parse_name(line, dest):
    if dest == 'host':
        match = re.search(r'logging host (\S+)', line, re.M)
        if match:
            name = match.group(1)
    else:
        name = None

    return name


def parse_level(line, dest):
    level_group = ('emergencies', 'alerts', 'critical', 'errors', 'warnings',
                   'notifications', 'informational', 'debugging')

    if dest == 'host':
        level = 'debugging'

    else:
        if dest == 'buffered':
            match = re.search(r'logging buffered(?: \d+)?(?: ([a-z]+))?', line, re.M)
        else:
            match = re.search(r'logging {0} (\S+)'.format(dest), line, re.M)

        if match and match.group(1) in level_group:
            level = match.group(1)
        else:
            level = 'debugging'

    return level


def map_config_to_obj(module):
    obj = []
    dest_group = ('console', 'host', 'monitor', 'buffered', 'on', 'facility')

    data = get_config(module, flags=['| include logging'])

    for line in data.split('\n'):
        match = re.search(r'^logging (\S+)', line, re.M)
        if match:
            if match.group(1) in dest_group:
                dest = match.group(1)

                obj.append({
                    'dest': dest,
                    'name': parse_name(line, dest),
                    'size': parse_size(line, dest),
                    'facility': parse_facility(line, dest),
                    'level': parse_level(line, dest)
                })
            elif validate_ip_address(match.group(1)):
                dest = 'host'
                obj.append({
                    'dest': dest,
                    'name': match.group(1),
                    'size': parse_size(line, dest),
                    'facility': parse_facility(line, dest),
                    'level': parse_level(line, dest)
                })
            else:
                ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', match.group(1), re.M)
                if ip_match:
                    dest = 'host'
                    obj.append({
                        'dest': dest,
                        'name': match.group(1),
                        'size': parse_size(line, dest),
                        'facility': parse_facility(line, dest),
                        'level': parse_level(line, dest)
                    })
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
            if d['dest'] != 'host':
                d['name'] = None

            if d['dest'] == 'buffered':
                if 'size' in d:
                    d['size'] = str(validate_size(d['size'], module))
                elif 'size' not in d:
                    d['size'] = str(4096)
                else:
                    pass

            if d['dest'] != 'buffered':
                d['size'] = None

            obj.append(d)

    else:
        if module.params['dest'] != 'host':
            module.params['name'] = None

        if module.params['dest'] == 'buffered':
            if not module.params['size']:
                module.params['size'] = str(4096)
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
        dest=dict(type='str', choices=['on', 'host', 'console', 'monitor', 'buffered']),
        name=dict(type='str'),
        size=dict(type='int'),
        facility=dict(type='str'),
        level=dict(type='str', default='debugging'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(ios_argument_spec)

    required_if = [('dest', 'host', ['name'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    device_info = get_capabilities(module)
    os_version = device_info['device_info']['network_os_version']

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module, required_if=required_if)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module, os_version)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
