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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = """
---
module: vyos_logging
version_added: "2.4"
author: "Trishna Guha (@trishnag)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on Vyatta Vyos devices.
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['console', 'file', 'global', 'host', 'user']
  name:
    description:
      - If value of C(dest) is I(file) it indicates file-name,
        for I(user) it indicates username and for I(host) indicates
        the host name to be notified.
  facility:
    description:
      - Set logging facility.
  level:
    description:
      - Set logging severity levels.
  aggregate:
    description: List of logging definitions.
  purge:
    description:
      - Purge logging not defined in the aggregate parameter.
    default: no
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure console logging
  vyos_logging:
    dest: console
    facility: all
    level: crit
- name: remove console logging configuration
  vyos_logging:
    dest: console
    state: absent
- name: configure file logging
  vyos_logging:
    dest: file
    name: test
    facility: local3
    level: err
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - set system syslog global facility all level notice
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vyos import get_config, load_config
from ansible.module_utils.vyos import vyos_argument_spec, check_args


def spec_to_commands(updates, module):
    commands = list()
    want, have = updates

    for w in want:
        dest = w['dest']
        name = w['name']
        facility = w['facility']
        level = w['level']
        state = w['state']
        del w['state']

        if state == 'absent' and w in have:
            if w['name']:
                commands.append('delete system syslog {0} {1} facility {2} level {3}'.format(
                    dest, name, facility, level))
            else:
                commands.append('delete system syslog {0} facility {1} level {2}'.format(
                    dest, facility, level))
        elif state == 'present' and w not in have:
            if w['name']:
                commands.append('set system syslog {0} {1} facility {2} level {3}'.format(
                    dest, name, facility, level))
            else:
                commands.append('set system syslog {0} facility {1} level {2}'.format(
                    dest, facility, level))

    return commands


def config_to_dict(module):
    data = get_config(module)
    obj = []

    for line in data.split('\n'):
        if line.startswith('set system syslog'):
            match = re.search(r'set system syslog (\S+)', line, re.M)
            dest = match.group(1)
            if dest == 'host':
                match = re.search(r'host (\S+)', line, re.M)
                name = match.group(1)
            elif dest == 'file':
                match = re.search(r'file (\S+)', line, re.M)
                name = match.group(1)
            elif dest == 'user':
                match = re.search(r'user (\S+)', line, re.M)
                name = match.group(1)
            else:
                name = None

            if 'facility' in line:
                match = re.search(r'facility (\S+)', line, re.M)
                facility = match.group(1)
            if 'level' in line:
                match = re.search(r'level (\S+)', line, re.M)
                level = match.group(1).strip("'")

                obj.append({'dest': dest,
                            'name': name,
                            'facility': facility,
                            'level': level})

    return obj


def map_params_to_obj(module):
    obj = []

    if 'aggregate' in module.params and module.params['aggregate']:
        for c in module.params['aggregate']:
            d = c.copy()
            if d['dest'] not in ('host', 'file', 'user'):
                d['name'] = None
            else:
                pass

            if 'state' not in d:
                d['state'] = module.params['state']

            obj.append(d)

    else:
        if module.params['dest'] not in ('host', 'file', 'user'):
            module.params['name'] = None

        obj.append({
            'dest': module.params['dest'],
            'name': module.params['name'],
            'facility': module.params['facility'],
            'level': module.params['level'],
            'state': module.params['state']
        })

    return obj


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        dest=dict(type='str', choices=['console', 'file', 'global', 'host', 'user']),
        name=dict(type='str'),
        facility=dict(type='str'),
        level=dict(type='str'),
        state=dict(default='present', choices=['present', 'absent']),
        aggregate=dict(type='list'),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(vyos_argument_spec)
    required_if = [('dest', 'host', ['name', 'facility', 'level']),
                   ('dest', 'file', ['name', 'facility', 'level']),
                   ('dest', 'user', ['name', 'facility', 'level']),
                   ('dest', 'console', ['facility', 'level']),
                   ('dest', 'global', ['facility', 'level'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    want = map_params_to_obj(module)
    have = config_to_dict(module)

    commands = spec_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        load_config(module, commands, commit=commit)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
