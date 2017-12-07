#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: iosxr_logging
version_added: "2.4"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on Cisco IOS XR devices.
extends_documentation_fragment: iosxr
notes:
  - Tested against IOS XR 6.1.2
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['on', 'hostnameprefix', console', 'monitor', 'buffered']
  name:
    description:
      - If value of C(dest) is I(file) it indicates file-name,
        for I(user) it indicates username and for I(host) indicates
        the host name to be notified.
  size:
    description:
      - Size of buffer. The acceptable value is in range from 307200 to
        125000000 bytes.
    default: 307200
  facility:
    description:
      - Set logging facility.
    default: local7
  level:
    description:
      - Set logging severity levels.
    default: debugging
  aggregate:
    description: List of logging definitions.
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure hostnameprefix logging
  iosxr_logging:
    dest: hostnameprefix
    name: 172.16.0.1
    state: present

- name: remove hostnameprefix logging configuration
  iosxr_logging:
    dest: hostnameprefix
    name: 172.16.0.1
    state: absent

- name: configure console logging level and facility
  iosxr_logging:
    dest: console
    facility: local7
    level: debugging
    state: present

- name: enable logging to all
  iosxr_logging:
    dest : on

- name: configure buffer size
  iosxr_logging:
    dest: buffered
    size: 5000

- name: Configure logging using aggregate
  iosxr_logging:
    aggregate:
      - { dest: console, level: warning }
      - { dest: buffered, size: 4800000 }

- name: Delete logging using aggregate
  iosxr_logging:
    aggregate:
      - { dest: console, level: warning }
      - { dest: buffered, size: 4800000 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - logging facility local7
    - logging hostnameprefix 172.16.0.1
"""

import re

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec
from ansible.module_utils.network.common.utils import remove_default_spec


def validate_size(value, module):
    if value:
        if value and not int(307200) <= value <= int(125000000):
            module.fail_json(msg='size must be between 307200 and 125000000')
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
            if dest == 'hostnameprefix':
                commands.append('no logging hostnameprefix {}'.format(name))
            elif dest:
                commands.append('no logging {}'.format(dest))
            else:
                module.fail_json(msg='dest must be among console, monitor, buffered, hostnameprefix, on')

            if facility:
                commands.append('no logging facility {}'.format(facility))

        if state == 'present' and w not in have:
            if facility:
                commands.append('logging facility {}'.format(facility))

            if dest == 'hostnameprefix':
                commands.append('logging hostnameprefix {}'.format(name))

            elif dest == 'on':
                commands.append('logging on')

            elif dest == 'buffered' and size:
                commands.append('logging buffered {}'.format(size))

            else:
                dest_cmd = 'logging {}'.format(dest)
                if level:
                    dest_cmd += ' {}'.format(level)

                commands.append(dest_cmd)
    return commands


def parse_facility(line):
    match = re.search(r'logging facility (\S+)', line, re.M)
    if match:
        facility = match.group(1)
    else:
        facility = 'local7'

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
                    size = str(307200)

    return size


def parse_name(line, dest):
    if dest == 'hostnameprefix':
        match = re.search(r'logging hostnameprefix (\S+)', line, re.M)
        if match:
            name = match.group(1)
    else:
        name = None

    return name


def parse_level(line, dest):
    level_group = ('emergencies', 'alerts', 'critical', 'errors', 'warning',
                   'notifications', 'informational', 'debugging')

    if dest == 'hostnameprefix':
        level = 'debugging'

    else:
        match = re.search(r'logging {} (\S+)'.format(dest), line, re.M)
        if match:
            if match.group(1) in level_group:
                level = match.group(1)
            else:
                level = 'debugging'
        else:
            level = 'debugging'

    return level


def map_config_to_obj(module):

    obj = []
    dest_group = ('console', 'hostnameprefix', 'monitor', 'buffered', 'on')

    data = get_config(module, config_filter='logging')
    lines = data.split("\n")

    for line in lines:
        match = re.search(r'logging (\S+)', line, re.M)
        if match:
            if match.group(1) in dest_group:
                dest = match.group(1)
                obj.append({
                    'dest': dest,
                    'name': parse_name(line, dest),
                    'size': parse_size(line, dest),
                    'facility': parse_facility(line),
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

            if d['dest'] != 'hostnameprefix':
                d['name'] = None

            if d['dest'] == 'buffered':
                if 'size' in d:
                    d['size'] = str(validate_size(d['size'], module))
                elif 'size' not in d:
                    d['size'] = str(307200)
                else:
                    pass

            if d['dest'] != 'buffered':
                d['size'] = None

            obj.append(d)

    else:
        if module.params['dest'] != 'hostnameprefix':
            module.params['name'] = None

        if module.params['dest'] == 'buffered':
            if not module.params['size']:
                module.params['size'] = str(307200)
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
        dest=dict(type='str', choices=['on', 'hostnameprefix', 'console', 'monitor', 'buffered']),
        name=dict(type='str'),
        size=dict(type='int'),
        facility=dict(type='str', default='local7'),
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
    argument_spec.update(iosxr_argument_spec)

    required_if = [('dest', 'hostnameprefix', ['name'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}

    want = map_params_to_obj(module, required_if=required_if)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)

    result['commands'] = commands
    result['warnings'] = warnings

    if commands:
        commit = not module.check_mode
        diff = load_config(module, commands, commit=commit)
        if diff:
            result['diff'] = dict(prepared=diff)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
