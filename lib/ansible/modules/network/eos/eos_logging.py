#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: eos_logging
version_added: "2.4"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on Arista Eos devices.
notes:
  - Tested against EOS 4.15
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['on', 'host', 'console', 'monitor', 'buffered']
  name:
    description:
      - The hostname or IP address of the destination.
      - Required when I(dest=host).
  size:
    description:
      - Size of buffer. The acceptable value is in range from 10 to
        2147483647 bytes.
  facility:
    description:
      - Set logging facility.
  level:
    description:
      - Set logging severity levels.
    choices: ['emergencies', 'alerts', 'critical', 'errors',
              'warnings', 'notifications', 'informational', 'debugging']
  aggregate:
    description: List of logging definitions.
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: eos
"""

EXAMPLES = """
- name: configure host logging
  eos_logging:
    dest: host
    name: 172.16.0.1
    state: present

- name: remove host logging configuration
  eos_logging:
    dest: host
    name: 172.16.0.1
    state: absent

- name: configure console logging level and facility
  eos_logging:
    dest: console
    facility: local7
    level: debugging
    state: present

- name: enable logging to all
  eos_logging:
    dest : on

- name: configure buffer size
  eos_logging:
    dest: buffered
    size: 5000

- name: Configure logging using aggregate
  eos_logging:
    aggregate:
      - { dest: console, level: warnings }
      - { dest: buffered, size: 480000 }
    state: present
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
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.eos.eos import get_config, load_config
from ansible.module_utils.network.eos.eos import eos_argument_spec, check_args


DEST_GROUP = ['on', 'host', 'console', 'monitor', 'buffered']
LEVEL_GROUP = ['emergencies', 'alerts', 'critical', 'errors',
               'warnings', 'notifications', 'informational',
               'debugging']


def validate_size(value, module):
    if value:
        if not int(10) <= value <= int(2147483647):
            module.fail_json(msg='size must be between 10 and 2147483647')
        else:
            return value


def map_obj_to_commands(updates, module):
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

        if state == 'absent' and w in have:
            if dest:
                if dest == 'host':
                    commands.append('no logging host {0}'.format(name))

                elif dest in DEST_GROUP:
                    commands.append('no logging {0}'.format(dest))

                else:
                    module.fail_json(msg='dest must be among console, monitor, buffered, host, on')

            if facility:
                commands.append('no logging facility {0}'.format(facility))

        if state == 'present' and w not in have:
            if facility:
                present = False

                # Iterate over every dictionary in the 'have' list to check if
                # similar configuration for facility exists or not

                for entry in have:
                    if not entry['dest'] and entry['facility'] == facility:
                        present = True

                if not present:
                    commands.append('logging facility {0}'.format(facility))

            if dest == 'host':
                commands.append('logging host {0}'.format(name))

            elif dest == 'on':
                commands.append('logging on')

            elif dest == 'buffered' and size:

                present = False

                # Deals with the following two cases:
                # Case 1:       logging buffered <size> <level>
                #               logging buffered <same-size>
                #
                # Case 2:       Same buffered logging configuration
                #               already exists (i.e., both size &
                #               level are same)

                for entry in have:
                    if entry['dest'] == 'buffered' and entry['size'] == size:

                        if not level or entry['level'] == level:
                            present = True

                if not present:
                    if size and level:
                        commands.append('logging buffered {0} {1}'.format(size, level))
                    else:
                        commands.append('logging buffered {0}'.format(size))

            else:
                dest_cmd = 'logging {0}'.format(dest)
                if level:
                    dest_cmd += ' {0}'.format(level)

                commands.append(dest_cmd)

    return commands


def parse_facility(line):
    facility = None
    match = re.search(r'logging facility (\S+)', line, re.M)
    if match:
        facility = match.group(1)

    return facility


def parse_size(line, dest):
    size = None

    if dest == 'buffered':
        match = re.search(r'logging buffered (\S+)', line, re.M)
        if match:
            try:
                int_size = int(match.group(1))
            except ValueError:
                int_size = None

            if int_size:
                if isinstance(int_size, int):
                    size = str(match.group(1))
                else:
                    size = str(10)

    return size


def parse_name(line, dest):
    name = None
    if dest == 'host':
        match = re.search(r'logging host (\S+)', line, re.M)
        if match:
            name = match.group(1)

    return name


def parse_level(line, dest):
    level = None

    if dest != 'host':

        # Line for buffer logging entry in running-config is of the form:
        # logging buffered <size> <level>

        if dest == 'buffered':
            match = re.search(r'logging buffered (?:\d+) (\S+)', line, re.M)

        else:
            match = re.search(r'logging {0} (\S+)'.format(dest), line, re.M)

        if match:
            if match.group(1) in LEVEL_GROUP:
                level = match.group(1)

    return level


def map_config_to_obj(module):
    obj = []

    data = get_config(module, flags=['section logging'])

    for line in data.split('\n'):

        match = re.search(r'logging (\S+)', line, re.M)

        if match:
            if match.group(1) in DEST_GROUP:
                dest = match.group(1)

            else:
                dest = None

            obj.append({'dest': dest,
                        'name': parse_name(line, dest),
                        'size': parse_size(line, dest),
                        'facility': parse_facility(line),
                        'level': parse_level(line, dest)})

    return obj


def parse_obj(obj, module):
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
                    d['size'] = str(10)
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
                module.params['size'] = str(10)
        else:
            module.params['size'] = None

        parse_obj(obj, module)

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        dest=dict(choices=DEST_GROUP),
        name=dict(),
        size=dict(type='int'),
        facility=dict(),
        level=dict(choices=LEVEL_GROUP),
        state=dict(default='present', choices=['present', 'absent']),
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(eos_argument_spec)

    required_if = [('dest', 'host', ['name'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    have = map_config_to_obj(module)
    want = map_params_to_obj(module, required_if=required_if)

    commands = map_obj_to_commands((want, have), module)
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
