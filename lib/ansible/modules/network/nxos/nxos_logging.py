#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: nxos_logging
version_added: "2.4"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage logging on network devices
description:
  - This module provides declarative management of logging
    on Cisco NX-OS devices.
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['console', 'logfile', 'module', 'monitor', 'server']
  remote_server:
    description:
      - Hostname or IP Address for remote logging (when dest is 'server').
    version_added: '2.7'
  use_vrf:
    description:
      - VRF to be used while configuring remote logging (when dest is 'server').
    version_added: '2.7'
  interface:
    description:
      - Interface to be used while configuring source-interface for logging (e.g., 'Ethernet1/2', 'mgmt0')
    version_added: '2.7'
  name:
    description:
      - If value of C(dest) is I(logfile) it indicates file-name.
  facility:
    description:
      - Facility name for logging.
  dest_level:
    description:
      - Set logging severity levels.
    aliases: ['level']
  facility_level:
    description:
      - Set logging severity levels for facility based log messages.
  aggregate:
    description: List of logging definitions.
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
  event:
    description:
      - Link/trunk enable/default interface configuration logging
    choices: ['link-enable', 'link-default', 'trunk-enable', 'trunk-default']
    version_added: '2.8'
  interface_message:
    description:
      - Add interface description to interface syslogs.
        Does not work with version 6.0 images using nxapi as a transport.
    choices: ['add-interface-description']
    version_added: '2.8'
  file_size:
    description:
      - Set logfile size
    version_added: '2.8'
  facility_link_status:
    description:
      - Set logging facility ethpm link status.
        Not idempotent with version 6.0 images.
    choices: ['link-down-notif', 'link-down-error', 'link-up-notif', 'link-up-error']
    version_added: '2.8'
  timestamp:
    description:
      - Set logging timestamp format
    choices: ['microseconds', 'milliseconds', 'seconds']
    version_added: '2.8'
  purge:
    description:
      - Remove any switch logging configuration that does not match what has been configured
        Not supported for ansible_connection local.
        All nxos_logging tasks must use the same ansible_connection type.

    type: bool
    default: no
    version_added: '2.8'
extends_documentation_fragment: nxos
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
- name: Configure logging logfile with size
  nxos_logging:
    dest: logfile
    name: testfile
    dest_level: 3
    file_size: 16384
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
- name: Configure Remote Logging
  nxos_logging:
    dest: server
    remote_server: test-syslogserver.com
    facility: auth
    facility_level: 1
    use_vrf: management
    state: present
- name: Configure Source Interface for Logging
  nxos_logging:
    interface: mgmt0
    state: present
- name: Purge nxos_logging configuration not managed by this playbook
  nxos_logging:
    purge: true
- name: Configure logging timestamp
  nxos_logging:
    timestamp: milliseconds
    state: present
- name: Configure logging facility ethpm link status
  nxos_logging:
    facility: ethpm
    facility_link_status: link-up-notif
    state: present
- name: Configure logging message ethernet description
  nxos_logging:
    interface_message: add-interface-description
    state: present
- name: Configure logging event link enable
  nxos_logging:
    event: link-enable
    state: present
- name: Configure logging using aggregate
  nxos_logging:
    aggregate:
      - { dest: console, dest_level: 2 }
      - { dest: logfile, dest_level: 2, name: testfile }
      - { facility: daemon, facility_level: 0 }
    state: present
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
import copy

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands, save_module_context, read_module_context
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args, normalize_interface
from ansible.module_utils.basic import AnsibleModule


STATIC_CLI = {'link-enable': 'logging event link-status enable',
              'link-default': 'logging event link-status default',
              'trunk-enable': 'logging event trunk-status enable',
              'trunk-default': 'logging event trunk-status default',
              'microseconds': 'logging timestamp microseconds',
              'milliseconds': 'logging timestamp milliseconds',
              'seconds': 'logging timestamp seconds',
              'link-up-error': 'link-up error',
              'link-up-notif': 'link-up notif',
              'link-down-error': 'link-down error',
              'link-down-notif': 'link-down notif',
              'add-interface-description': 'logging message interface type ethernet description'}

DEFAULT_LOGGING_LEVEL = {0: [],
                         1: [],
                         2: ['pktmgr'],
                         3: ['adjmgr', 'arp', 'icmpv6', 'l2rib', 'netstack'],
                         4: [],
                         5: ['mrib'],
                         6: [],
                         7: []}

DEST_GROUP = ['console', 'logfile', 'module', 'monitor', 'server']


def map_obj_to_commands(module, updates):
    commands = list()
    want, have = updates

    for w in want:
        state = w['state']
        del w['state']

        if state == 'absent' and w in have:
            if w['facility'] is not None:
                if not w['dest'] and not w['facility_link_status'] and w['facility'] not in DEFAULT_LOGGING_LEVEL[int(w['facility_level'])]:
                    commands.append('no logging level {0} {1}'.format(w['facility'], w['facility_level']))

                if w['facility_link_status'] and w['facility'] in ('ethpm'):
                    commands.append('no logging level {0} {1}'.format(w['facility'], STATIC_CLI[w['facility_link_status']]))

            if w['name'] is not None:
                commands.append('no logging logfile')

            if w['dest'] in ('console', 'module', 'monitor'):
                commands.append('no logging {0}'.format(w['dest']))

            if w['dest'] == 'server':
                commands.append('no logging server {0}'.format(w['remote_server']))

            if w['interface']:
                commands.append('no logging source-interface')

            if w['event'] and w['event'] in STATIC_CLI:
                commands.append('no ' + STATIC_CLI[w['event']])

            if w['message'] and w['message'] in STATIC_CLI:
                commands.append('no ' + STATIC_CLI[w['message']])

            if w['timestamp'] and w['timestamp'] in STATIC_CLI:
                commands.append('no ' + STATIC_CLI[w['timestamp']])

        if state == 'present' and w not in have:
            if w['facility'] is None:
                if w['dest']:
                    if w['dest'] not in ('logfile', 'server'):
                        commands.append('logging {0} {1}'.format(w['dest'], w['dest_level']))

                    elif w['dest'] == 'logfile':
                        if w['file_size']:
                            commands.append('logging logfile {0} {1} size {2}'.format(
                                w['name'], w['dest_level'], w['file_size']))
                        else:
                            commands.append('logging logfile {0} {1}'.format(
                                w['name'], w['dest_level']))

                    elif w['dest'] == 'server':
                        if w['facility_level']:
                            if w['use_vrf']:
                                commands.append('logging server {0} {1} use-vrf {2}'.format(
                                    w['remote_server'], w['facility_level'], w['use_vrf']))
                            else:
                                commands.append('logging server {0} {1}'.format(
                                    w['remote_server'], w['facility_level']))

                        else:
                            if w['use_vrf']:
                                commands.append('logging server {0} use-vrf {1}'.format(
                                    w['remote_server'], w['use_vrf']))
                            else:
                                commands.append('logging server {0}'.format(w['remote_server']))

            if w['facility']:
                if w['dest'] == 'server':
                    if w['facility_level']:
                        if w['use_vrf']:
                            commands.append('logging server {0} {1} facility {2} use-vrf {3}'.format(
                                w['remote_server'], w['facility_level'], w['facility'], w['use_vrf']))
                        else:
                            commands.append('logging server {0} {1} facility {2}'.format(
                                w['remote_server'], w['facility_level'], w['facility']))
                    else:
                        if w['use_vrf']:
                            commands.append('logging server {0} facility {1} use-vrf {2}'.format(
                                w['remote_server'], w['facility'], w['use_vrf']))
                        else:
                            commands.append('logging server {0} facility {1}'.format(w['remote_server'],
                                                                                     w['facility']))
                else:
                    if w['facility_link_status']:
                        commands.append('logging level {0} {1}'.format(
                            w['facility'], STATIC_CLI[w['facility_link_status']]))
                    else:
                        if not match_facility_default(module, w['facility'], w['facility_level']):
                            commands.append('logging level {0} {1}'.format(w['facility'],
                                                                           w['facility_level']))

            if w['interface']:
                commands.append('logging source-interface {0} {1}'.format(*split_interface(w['interface'])))

            if w['event'] and w['event'] in STATIC_CLI:
                commands.append(STATIC_CLI[w['event']])

            if w['message'] and w['message'] in STATIC_CLI:
                commands.append(STATIC_CLI[w['message']])

            if w['timestamp'] and w['timestamp'] in STATIC_CLI:
                commands.append(STATIC_CLI[w['timestamp']])

    return commands


def match_facility_default(module, facility, want_level):
    ''' Check wanted facility to see if it matches current device default '''

    matches_default = False
    # Sample output from show logging level command
    # Facility        Default Severity        Current Session Severity
    # --------        ----------------        ------------------------
    # bfd                     5                       5
    #
    # 0(emergencies)          1(alerts)       2(critical)
    # 3(errors)               4(warnings)     5(notifications)
    # 6(information)          7(debugging)

    regexl = r'\S+\s+(\d+)\s+(\d+)'
    cmd = {'command': 'show logging level {0}'.format(facility), 'output': 'text'}
    facility_data = run_commands(module, cmd)
    for line in facility_data[0].split('\n'):
        mo = re.search(regexl, line)
        if mo and int(mo.group(1)) == int(want_level) and int(mo.group(2)) == int(want_level):
            matches_default = True

    return matches_default


def split_interface(interface):
    match = re.search(r'(\D+)(\S*)', interface, re.M)
    if match:
        return match.group(1), match.group(2)


def parse_facility_link_status(line, facility, status):
    facility_link_status = None

    if facility is not None:
        match = re.search(r'logging level {0} {1} (\S+)'.format(facility, status), line, re.M)
        if match:
            facility_link_status = status + "-" + match.group(1)

    return facility_link_status


def parse_event_status(line, event):
    status = None

    match = re.search(r'logging event {0} (\S+)'.format(event + '-status'), line, re.M)
    if match:
        state = match.group(1)
        if state:
            status = state

    return status


def parse_event(line):
    event = None

    match = re.search(r'logging event (\S+)', line, re.M)
    if match:
        state = match.group(1)
        if state == 'link-status':
            event = 'link'
        elif state == 'trunk-status':
            event = 'trunk'

    return event


def parse_message(line):
    message = None

    match = re.search(r'logging message interface type ethernet description', line, re.M)
    if match:
        message = 'add-interface-description'

    return message


def parse_file_size(line, name, level):
    file_size = None

    match = re.search(r'logging logfile {0} {1} size (\S+)'.format(name, level), line, re.M)
    if match:
        file_size = match.group(1)
        if file_size == '8192':
            file_size = None

    return file_size


def parse_timestamp(line):
    timestamp = None

    match = re.search(r'logging timestamp (\S+)', line, re.M)
    if match:
        timestamp = match.group(1)

    return timestamp


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


def parse_remote_server(line, dest):
    remote_server = None

    if dest and dest == 'server':
        match = re.search(r'logging server (\S+)', line, re.M)
        if match:
            remote_server = match.group(1)

    return remote_server


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

    if dest and dest != 'server':
        if dest == 'logfile':
            match = re.search(r'logging logfile {0} (\S+)'.format(name), line, re.M)
            if match:
                dest_level = parse_match(match)

        elif dest == 'server':
            match = re.search(r'logging server (?:\S+) (\d+)', line, re.M)
            if match:
                dest_level = parse_match(match)
        else:
            match = re.search(r'logging {0} (\S+)'.format(dest), line, re.M)
            if match:
                dest_level = parse_match(match)

    return dest_level


def parse_facility_level(line, facility, dest):
    facility_level = None

    if dest == 'server':
        match = re.search(r'logging server (?:\S+) (\d+)', line, re.M)
        if match:
            facility_level = match.group(1)

    elif facility is not None:
        match = re.search(r'logging level {0} (\S+)'.format(facility), line, re.M)
        if match:
            facility_level = match.group(1)

    return facility_level


def parse_facility(line):
    facility = None

    match = re.search(r'logging server (?:\S+) (?:\d+) (?:\S+) (?:\S+) (?:\S+) (\S+)', line, re.M)
    if match:
        facility = match.group(1)

    return facility


def parse_use_vrf(line, dest):
    use_vrf = None

    if dest and dest == 'server':
        match = re.search(r'logging server (?:\S+) (?:\d+) use-vrf (\S+)', line, re.M)
        if match:
            use_vrf = match.group(1)

    return use_vrf


def parse_interface(line):
    interface = None

    match = re.search(r'logging source-interface (\S*)', line, re.M)
    if match:
        interface = match.group(1)

    return interface


def map_config_to_obj(module):
    obj = []

    data = get_config(module, flags=[' all | section logging'])

    for line in data.split('\n'):
        if re.search(r'no (\S+)', line, re.M):
            state = 'absent'
        else:
            state = 'present'

        match = re.search(r'logging (\S+)', line, re.M)
        if state == 'present' and match:
            event_status = None
            name = None
            dest_level = None
            dest = None
            facility = None
            remote_server = None
            facility_link_status = None
            file_size = None
            facility_level = None

            if match.group(1) in DEST_GROUP:
                dest = match.group(1)

                name = parse_name(line, dest)
                remote_server = parse_remote_server(line, dest)
                dest_level = parse_dest_level(line, dest, name)

                if dest == 'server':
                    facility = parse_facility(line)

                facility_level = parse_facility_level(line, facility, dest)

                if dest == 'logfile':
                    file_size = parse_file_size(line, name, dest_level)

            elif match.group(1) == 'level':
                match_facility = re.search(r'logging level (\S+)', line, re.M)
                facility = match_facility.group(1)

                level = parse_facility_level(line, facility, dest)
                if level.isdigit():
                    facility_level = level
                else:
                    facility_link_status = parse_facility_link_status(line, facility, level)

            elif match.group(1) == 'event' and state == 'present':
                event = parse_event(line)
                if event:
                    status = parse_event_status(line, event)
                    if status:
                        event_status = event + '-' + status
                else:
                    continue

            else:
                pass

            obj.append({'dest': dest,
                        'remote_server': remote_server,
                        'use_vrf': parse_use_vrf(line, dest),
                        'name': name,
                        'facility': facility,
                        'dest_level': dest_level,
                        'facility_level': facility_level,
                        'interface': parse_interface(line),
                        'facility_link_status': facility_link_status,
                        'event': event_status,
                        'file_size': file_size,
                        'message': parse_message(line),
                        'timestamp': parse_timestamp(line)})

    cmd = [{'command': 'show logging | section enabled | section console', 'output': 'text'},
           {'command': 'show logging | section enabled | section monitor', 'output': 'text'}]

    default_data = run_commands(module, cmd)

    for line in default_data:
        flag = False
        match = re.search(r'Logging (\w+):(?:\s+) (?:\w+) (?:\W)Severity: (\w+)', str(line), re.M)
        if match:
            if match.group(1) == 'console' and match.group(2) == 'critical':
                dest_level = '2'
                flag = True
            elif match.group(1) == 'monitor' and match.group(2) == 'notifications':
                dest_level = '5'
                flag = True
        if flag:
            obj.append({'dest': match.group(1),
                        'remote_server': None,
                        'name': None,
                        'facility': None,
                        'dest_level': dest_level,
                        'facility_level': None,
                        'use_vrf': None,
                        'interface': None,
                        'facility_link_status': None,
                        'event': None,
                        'file_size': None,
                        'message': None,
                        'timestamp': None})

    return obj


def map_params_to_obj(module):
    obj = []

    if 'aggregate' in module.params and module.params['aggregate']:
        args = {'dest': '',
                'remote_server': '',
                'use_vrf': '',
                'name': '',
                'facility': '',
                'dest_level': '',
                'facility_level': '',
                'interface': '',
                'facility_link_status': None,
                'event': None,
                'file_size': None,
                'message': None,
                'timestamp': None}

        for c in module.params['aggregate']:
            d = c.copy()

            for key in args:
                if key not in d:
                    d[key] = None

            if d['dest_level'] is not None:
                d['dest_level'] = str(d['dest_level'])

            if d['facility_level'] is not None:
                d['facility_level'] = str(d['facility_level'])

            if d['interface']:
                d['interface'] = normalize_interface(d['interface'])

            if 'state' not in d:
                d['state'] = module.params['state']

            if d['file_size']:
                d['file_size'] = str(d['file_size'])

            obj.append(d)

    else:
        dest_level = None
        facility_level = None
        file_size = None

        if module.params['dest_level'] is not None:
            dest_level = str(module.params['dest_level'])

        if module.params['facility_level'] is not None:
            facility_level = str(module.params['facility_level'])

        if module.params['file_size'] is not None:
            file_size = str(module.params['file_size'])

        obj.append({
            'dest': module.params['dest'],
            'remote_server': module.params['remote_server'],
            'use_vrf': module.params['use_vrf'],
            'name': module.params['name'],
            'facility': module.params['facility'],
            'dest_level': dest_level,
            'facility_level': facility_level,
            'interface': normalize_interface(module.params['interface']),
            'state': module.params['state'],
            'facility_link_status': module.params['facility_link_status'],
            'event': module.params['event'],
            'message': module.params['interface_message'],
            'file_size': file_size,
            'timestamp': module.params['timestamp']
        })
    return obj


def merge_wants(wants, want):
    if not wants:
        wants = list()

    for w in want:
        w = copy.copy(w)
        state = w['state']
        del w['state']

        if state == 'absent':
            if w in wants:
                wants.remove(w)
        elif w not in wants:
            wants.append(w)

    return wants


def absent(h):
    h['state'] = 'absent'
    return h


def outliers(haves, wants):
    wants = list(wants)
    return [absent(h) for h in haves if not (h in wants or wants.append(h))]


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        dest=dict(choices=DEST_GROUP),
        name=dict(),
        facility=dict(),
        remote_server=dict(),
        use_vrf=dict(),
        dest_level=dict(type='int', aliases=['level']),
        facility_level=dict(type='int'),
        interface=dict(),
        facility_link_status=dict(choices=['link-down-notif', 'link-down-error', 'link-up-notif', 'link-up-error']),
        event=dict(choices=['link-enable', 'link-default', 'trunk-enable', 'trunk-default']),
        interface_message=dict(choices=['add-interface-description']),
        file_size=dict(type='int'),
        timestamp=dict(choices=['microseconds', 'milliseconds', 'seconds']),
        state=dict(default='present', choices=['present', 'absent']),
        aggregate=dict(type='list'),
        purge=dict(default=False, type='bool'),
    )

    argument_spec.update(nxos_argument_spec)

    required_if = [('dest', 'logfile', ['name']),
                   ('dest', 'server', ['remote_server'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    merged_wants = merge_wants(read_module_context(module), want)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(module, (want, have))
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    save_module_context(module, merged_wants)

    if module.params.get('purge'):
        pcommands = map_obj_to_commands(module, (outliers(have, merged_wants), have))
        if pcommands:
            if not module.check_mode:
                load_config(module, pcommands)
            result['changed'] = True
        result['commands'] += pcommands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
