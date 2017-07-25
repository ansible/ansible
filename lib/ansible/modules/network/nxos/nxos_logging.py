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
module: nxos_logging
version_added: "2.4"
author: "Trishna Guha (@trishnag)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on Cisco NX-OS devices.
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['console', 'logfile', 'module', 'monitor']
  name:
    description:
      - If value of C(dest) is I(logfile) it indicates file-name.
  facility:
    description:
      - Facility name for logging.
  dest_level:
    description:
      - Set logging severity levels. C(alias level).
  facility_level:
    description:
      - Set logging serverity levels for facility based log messages.
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
- name: configure console logging with level
  nxos_logging:
    dest: console
    level: 2
    state: present
- name: remove console logging configuration
  nxos_logging:
    dest: console
    level: 2
    state: absent
- name: configure file logging with level
  nxos_logging:
    dest: logfile
    name: testfile
    dest_level: 3
    state: present
- name: configure facility level logging
  nxos_logging:
    facility: daemon
    facility_level: 0
    state: present
- name: remove facility level logging
  nxos_logging:
    facility: daemon
    facility_level: 0
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - logging console 2
    - logging logfile testfile 3
    - logging level daemon 0
"""

import re

from ansible.module_utils.nxos import get_config, load_config
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


DEST_GROUP = ['console', 'logfile', 'module', 'monitor']


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates

    for w in want:
        dest = w['dest']
        name = w['name']
        facility = w['facility']
        dest_level = w['dest_level']
        facility_level = w['facility_level']
        state = w['state']
        del w['state']

        if state == 'absent' and w in have:
            if w['facility'] is not None:
                commands.append('no logging level {}'.format(w['facility']))

            if w['name'] is not None:
                commands.append('no logging logfile')

            if w['dest'] in ('console', 'module', 'monitor'):
                commands.append('no logging {}'.format(w['dest']))

        if state == 'present' and w not in have:
            if w['facility'] is None:
                if w['dest'] is not None:
                    if w['dest'] != 'logfile':
                        commands.append('logging {} {}'.format(w['dest'], w['dest_level']))
                    elif w['dest'] == 'logfile':
                        commands.append('logging logfile {} {}'.format(w['name'], w['dest_level']))
                    else:
                        pass

            if w['facility'] is not None:
                    commands.append('logging level {} {}'.format(w['facility'], w['facility_level']))

    return commands


def parse_name(line, dest):
    name = None

    if dest is not None:
        if dest == 'logfile':
            match = re.search(r'logging logfile (\S+)', line, re.M)
            if match:
                name = match.group(1)
            else:
                pass

    return name


def parse_dest_level(line, dest, name):
    dest_level = None

    def parse_match(match):
        level = None
        if match:
            if int(match.group(1)) in range(0, 8):
                level = match.group(1)
            else:
                pass
        return level

    if dest is not None:
        if dest == 'logfile':
            match = re.search(r'logging logfile {} (\S+)'.format(name), line, re.M)
            if match:
                dest_level = parse_match(match)
        else:
            match = re.search(r'logging {} (\S+)'.format(dest), line, re.M)
            if match:
                dest_level = parse_match(match)

    return dest_level


def parse_facility_level(line, facility):
    facility_level = None

    if facility is not None:
        match = re.search(r'logging level {} (\S+)'.format(facility), line, re.M)
        if match:
            facility_level = match.group(1)

    return facility_level


def map_config_to_obj(module):
    obj = []

    data = get_config(module, flags=['| section logging'])

    for line in data.split('\n'):
        match = re.search(r'logging (\S+)', line, re.M)

        if match:
            if match.group(1) in DEST_GROUP:
                dest = match.group(1)
                facility = None

            elif match.group(1) == 'level':
                match_facility = re.search(r'logging level (\S+)', line, re.M)
                facility = match_facility.group(1)
                dest = None

            else:
                dest = None
                facility = None

            obj.append({'dest': dest,
                        'name': parse_name(line, dest),
                        'facility': facility,
                        'dest_level': parse_dest_level(line, dest, parse_name(line, dest)),
                        'facility_level': parse_facility_level(line, facility)})

    return obj


def map_params_to_obj(module):
    obj = []

    if 'aggregate' in module.params and module.params['aggregate']:
        args = {'dest': '',
                'name': '',
                'facility': '',
                'dest_level': '',
                'facility_level': ''
                }

        for c in module.params['aggregate']:
            d = c.copy()

            for key in args:
                if key not in d:
                    d[key] = None

            if d['dest_level'] is not None:
                d['dest_level'] = str(d['dest_level'])

            if d['facility_level'] is not None:
                d['facility_level'] = str(d['facility_level'])

            if 'state' not in d:
                d['state'] = module.params['state']

            obj.append(d)

    else:
        dest_level = None
        facility_level = None

        if module.params['dest_level'] is not None:
            dest_level = str(module.params['dest_level'])

        if module.params['facility_level'] is not None:
            facility_level = str(module.params['facility_level'])

        obj.append({
            'dest': module.params['dest'],
            'name': module.params['name'],
            'facility': module.params['facility'],
            'dest_level': dest_level,
            'facility_level': facility_level,
            'state': module.params['state']
        })

    return obj


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        dest=dict(choices=DEST_GROUP),
        name=dict(),
        facility=dict(),
        dest_level=dict(type='int', aliases=['level']),
        facility_level=dict(type='int'),
        state=dict(default='present', choices=['present', 'absent']),
        aggregate=dict(type='list'),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(nxos_argument_spec)

    required_if = [('dest', 'logfile', ['name'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           required_together=[['facility', 'facility_level']],
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
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
