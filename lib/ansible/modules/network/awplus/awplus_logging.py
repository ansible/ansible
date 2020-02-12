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
module: awplus_logging
author: Cheng Yi Kok (@cyk19)
version_added: "2.10"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on AlliedWare Plus devices.
options:
  dest:
    description:
        - Destination of the logs.
    choices: ['console', 'host', 'monitor', 'buffered', 'permanent', 'external', 'facility']
  name:
    description:
        - The hostname or IP address of the destination.
        - Required when I(dest=host).
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
    default: debugging
    choices: ['emergencies', 'alerts', 'critical', 'errors', 'warnings',
              'notices', 'informational', 'debugging', 'any']
  aggregate:
    description: List of logging definitions.
  state:
    description:
        - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
    - name: Configure host logging
      awplus_logging:
        dest: host
        name: 172.16.0.1
        state: present

    - name: Remove host logging configuration
      awplus_logging:
        dest: host
        name: 172.16.0.1
        state: absent

    - name: Configure console logging level and facility
      awplus_logging:
        dest: console
        facility: daemon
        level: notices
        state: present

    - name: Configure buffer size
      awplus_logging:
        dest: buffered
        size: 80

    - name: Configure logging using aggregate
      awplus_logging:
        aggregate:
          - { dest: console, facility: kern}
          - { dest: buffered, size: 100}

    - name: Remove logging using aggregate
      awplus_logging:
        aggregate:from copy import deepcopy
import re
          - { dest: console, facility: kern}
          - { dest: buffered, size: 100}
        state: absent

    - name: Configure global facility
      awplus_logging:
        dest: facility
        facility: kern
notes:
    - Check mode is supported.
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

from copy import deepcopy
import re

from ansible.module_utils.network.awplus.awplus import run_commands, awplus_argument_spec
from ansible.module_utils.network.common.utils import remove_default_spec, validate_ip_address
from ansible.module_utils.basic import AnsibleModule


def validate_size(value, module):
    if value:
        if not int(50) <= int(value) <= int(250):
            module.fail_json(msg='size must be between 50 and 250')
        else:
            return value


def map_obj_to_commands(updates, module):
    dest_group = ('console', 'host', 'monitor', 'buffered',
                  'permanent', 'external', 'facility')
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
        if state == 'absent':
            if dest:
                cmd = ''
                if dest == 'host':
                    for entry in have:
                        if entry['dest'] == 'host' and entry['name'] == name:
                            cmd += 'no log host {0}'.format(name)

                elif dest in dest_group:
                    cmd += 'no log {0}'.format(dest)

                else:
                    module.fail_json(
                        msg='dest must be among console, monitor, buffered, host, on, trap')

            if dest == 'buffered':
                if size:
                    cmd += ' size'

            if facility:
                cmd += ' facility {0}'.format(facility)
                if level:
                    cmd += ' level {0}'.format(level)

            if len(cmd) > 0:
                commands.append(cmd)

        if state == 'present' and w not in have:
            if facility:
                present = False

                for entry in have:
                    if entry['dest'] == dest and entry['facility'] == facility:
                        present = True

                if not present:
                    if dest == 'facility':
                        commands.append('log facility {0}'.format(facility))
                    else:
                        commands.append(
                            'log {0} facility {1}'.format(dest, facility))

            if dest == 'host':
                present = False
                for entry in have:
                    if entry['dest'] == 'host' and entry['name'] == name:
                        present = True

                if not present:
                    commands.append('log host {0}'.format(name))

            elif dest == 'buffered' and size:
                level_present = False
                size_present = False

                for entry in have:
                    if entry['dest'] == 'buffered' and entry['size'] == size:
                        size_present = True
                    elif entry['dest'] == 'buffered' and entry['level'] == level:
                        level_present = True

                if not level_present and level:
                    commands.append('log buffered level {0}'.format(level))
                elif not size_present and size:
                    commands.append('log buffered size {0}'.format(size))

            else:
                if dest:
                    dest_cmd = 'log {0}'.format(dest)
                    if level:
                        dest_cmd += ' level {0}'.format(level)
                        commands.append(dest_cmd)
    return commands


def parse_level(lines, dest, facility):
    level_group = ('emergencies', 'alerts', 'critical', 'errors', 'warnings',
                   'notices', 'informational', 'debugging', 'any')
    level = None
    blocks = re.split('Type .+', lines, re.M)
    for block in blocks:
        facility_match = re.search(r'Facility ... (\w+)', block, re.M)
        if facility_match:
            level_match = re.search(r'Level ...... (\w+)', block, re.M)
            if level_match and level_match.group(1) in level_group:
                level = level_match.group(1)
                return level


def parse_facility(lines, dest):
    facility = []
    if dest in {'console', 'host', 'monitor', 'buffered', 'permanent', 'external'}:
        for line in lines.split('\n'):
            match = re.search(r'Facility ... (\w+)', line, re.M)
            if match:
                facility.append(match.group(1))
    else:
        match = re.search(r'Facility: (\w+)', lines, re.M)
        if match:
            facility.append(match.group(1))

    return facility


def parse_size(line, dest):
    size = None

    if dest == 'buffered':
        match = re.search(r'Maximum size \D+ (\d+)', line, re.M)
        if match:
            if match.group(1) is not None:
                size = match.group(1)
            else:
                size = None
    return size


def parse_name(line, dest):
    if dest == 'host':
        match = re.search(r'Host (\S+) log:', line, re.M)
        if match:
            name = match.group(1)
    else:
        name = None

    return name


def populate_have(line, dest):
    have = []
    facilities = parse_facility(line, dest)
    if len(facilities) == 0:
        have.append({
            'dest': dest,
            'name': parse_name(line, dest),
            'size': parse_size(line, dest),
            'level': None,
            'facility': None
        })
    else:
        for facility in facilities:
            have.append({
                'dest': dest,
                'name': parse_name(line, dest),
                'size': parse_size(line, dest),
                'level': parse_level(line, dest, facility),
                'facility': facility
            })
    return have


def map_config_to_obj(module):
    obj = []
    dest_group = ('console', 'host', 'monitor',
                  'buffered', 'permanent', 'external')

    data = run_commands(module, 'show log config')[0]
    chunks = data.split(
        '                                                                                     ')
    for chunk in chunks:
        blocks = re.split('Statistics .+', chunk, re.M)
        for line in blocks:
            match = re.search(r'(\S+) log:', line, re.M)
            if 'Facility:' in line:
                dest = 'facility'
                haves = populate_have(line, dest)
                for have in haves:
                    obj.append(have)
            if match:
                if match.group(1).lower() in dest_group:
                    dest = match.group(1).lower()
                    haves = populate_have(line, dest)
                    for have in haves:
                        obj.append(have)
                elif validate_ip_address(match.group(1)):
                    dest = 'host'
                    haves = populate_have(line, dest)
                    for have in haves:
                        obj.append(have)
                else:
                    ip_match = re.search(
                        r'\d+\.\d+\.\d+\.\d+', match.group(1), re.M)
                    if ip_match:
                        dest = 'host'
                        haves = populate_have(line, dest)
                        for have in haves:
                            obj.append(have)

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
                    d['size'] = None
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
                module.params['size'] = None
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
    """
    main entry point for module execution
    """
    element_spec = dict(
        dest=dict(type='str', choices=[
                  'console', 'host', 'monitor', 'buffered', 'permanent', 'external', 'facility']),
        name=dict(type='str'),
        size=dict(type='int'),
        facility=dict(type='str'),
        level=dict(type='str', choices=['emergencies', 'alerts', 'critical', 'errors', 'warnings',
                                        'notices', 'informational', 'debugging']),
        state=dict(default='present', choices=['present', 'absent']),
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(awplus_argument_spec)

    required_if = [('dest', 'host', ['name'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module, required_if=required_if)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
