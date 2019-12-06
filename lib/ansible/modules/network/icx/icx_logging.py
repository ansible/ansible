#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: icx_logging
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description:  Manage logging on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of logging
    on Ruckus ICX 7000 series switches.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  dest:
    description:
      - Destination of the logs.
    choices: ['on', 'host', 'console', 'buffered', 'persistence', 'rfc5424']
    type: str
  name:
    description:
      - ipv4 address/ipv6 address/name of  syslog server.
    type: str
  udp_port:
    description:
      - UDP port of destination host(syslog server).
    type: str
  facility:
    description:
      - Specifies log facility to log messages from the device.
    choices: ['auth','cron','daemon','kern','local0', 'local1', 'local2', 'local3', 'local4', 'local5', 'local6', 'local7', 'user',
              'lpr','mail','news','syslog','sys9','sys10','sys11','sys12','sys13','sys14','user','uucp']
    type: str
  level:
    description:
      - Specifies the message level.
    type: list
    choices: ['alerts', 'critical', 'debugging', 'emergencies', 'errors', 'informational',
                'notifications', 'warnings']
  aggregate:
    description:
      - List of logging definitions.
    type: list
    suboptions:
      dest:
        description:
          - Destination of the logs.
        choices: ['on', 'host', 'console', 'buffered', 'persistence', 'rfc5424']
        type: str
      name:
        description:
          - ipv4 address/ipv6 address/name of  syslog server.
        type: str
      udp_port:
        description:
          - UDP port of destination host(syslog server).
        type: str
      facility:
        description:
          - Specifies log facility to log messages from the device.
        choices: ['auth','cron','daemon','kern','local0', 'local1', 'local2', 'local3', 'local4', 'local5', 'local6', 'local7', 'user',
                  'lpr','mail','news','syslog','sys9','sys10','sys11','sys12','sys13','sys14','user','uucp']
        type: str
      level:
        description:
          - Specifies the message level.
        type: list
        choices: ['alerts', 'critical', 'debugging', 'emergencies', 'errors', 'informational',
                    'notifications', 'warnings']
      state:
        description:
          - State of the logging configuration.
        choices: ['present', 'absent']
        type: str
      check_running_config:
        description:
          - Check running configuration. This can be set as environment variable.
           Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
        type: bool
  state:
    description:
      - State of the logging configuration.
    default: present
    choices: ['present', 'absent']
    type: str
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
       Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
    type: bool
    default: yes
"""

EXAMPLES = """
- name: Configure host logging.
  icx_logging:
    dest: host
    name: 172.16.0.1
    udp_port: 5555
- name: Remove host logging configuration.
  icx_logging:
    dest: host
    name: 172.16.0.1
    udp_port: 5555
    state: absent
- name: Disables the real-time display of syslog messages.
  icx_logging:
    dest: console
    state: absent
- name: Enables local syslog logging.
  icx_logging:
    dest : on
    state: present
- name: configure buffer level.
  icx_logging:
    dest: buffered
    level: critical
- name: Configure logging using aggregate
  icx_logging:
    aggregate:
      - { dest: buffered, level: ['notifications','errors'] }
- name: remove logging using aggregate
  icx_logging:
    aggregate:
      - { dest: console }
      - { dest: host, name: 172.16.0.1, udp_port: 5555 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - logging host 172.16.0.1
    - logging console
"""

import re
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import Connection, ConnectionError, exec_command
from ansible.module_utils.network.common.utils import remove_default_spec, validate_ip_v6_address
from ansible.module_utils.network.icx.icx import get_config, load_config


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o


def diff_in_list(want, have):
    adds = set()
    removes = set()
    for w in want:
        if w['dest'] == 'buffered':
            for h in have:
                if h['dest'] == 'buffered':
                    adds = w['level'] - h['level']
                    removes = h['level'] - w['level']
                    return adds, removes
    return adds, removes


def map_obj_to_commands(updates):
    dest_group = ('host', 'console', 'persistence', 'enable')
    commands = list()
    want, have = updates

    for w in want:
        dest = w['dest']
        name = w['name']
        level = w['level']
        state = w['state']
        udp_port = w['udp_port']
        facility = w['facility']
        del w['state']
        del w['facility']

        facility_name = ''
        facility_level = ''
        if name is not None and validate_ip_v6_address(name):
            name = 'ipv6 ' + name

        if facility:
            for item in have:
                if item['dest'] == 'facility':
                    facility_name = item['dest']
                    facility_level = item['facility']

        if state == 'absent':
            if have == []:
                if facility:
                    commands.append('no logging facility')

                if dest == 'buffered':
                    for item in have:
                        if item['dest'] == 'buffered':
                            want_level = level
                            have_level = item['level']
                            for item in want_level:
                                commands.append('no logging buffered {0}'.format(item))

                if dest == 'host':
                    if name and udp_port:
                        commands.append('no logging host {0} udp-port {1}'.format(name, udp_port))
                    elif name:
                        commands.append('no logging host {0}'.format(name))
                else:
                    if dest == 'rfc5424':
                        commands.append('no logging enable {0}'.format(dest))
                    else:
                        if dest != 'buffered':
                            commands.append('no logging {0}'.format(dest))

            if facility:
                if facility_name == 'facility' and facility_level != 'user':
                    commands.append('no logging facility')

            if dest == 'buffered':
                for item in have:
                    if item['dest'] == 'buffered':
                        want_level = level
                        have_level = item['level']
                        for item in want_level:
                            if item in have_level:
                                commands.append('no logging buffered {0}'.format(item))

            if w in have:
                if dest == 'host':
                    if name and udp_port:
                        commands.append('no logging host {0} udp-port {1}'.format(name, udp_port))
                    elif name:
                        commands.append('no logging host {0}'.format(name))
                else:
                    if dest == 'rfc5424':
                        commands.append('no logging enable {0}'.format(dest))
                    else:
                        if dest != 'buffered':
                            commands.append('no logging {0}'.format(dest))

        if state == 'present':
            if facility:
                if facility != facility_level:
                    commands.append('logging facility {0}'.format(facility))
            if w not in have:
                if dest == 'host':
                    if name and udp_port:
                        commands.append('logging host {0} udp-port {1}'.format(name, udp_port))
                    elif name:
                        commands.append('logging host {0}'.format(name))
                elif dest == 'buffered':
                    adds, removes = diff_in_list(want, have)
                    for item in adds:
                        commands.append('logging buffered {0}'.format(item))
                    for item in removes:
                        commands.append('no logging buffered {0}'.format(item))
                elif dest == 'rfc5424':
                    commands.append('logging enable {0}'.format(dest))
                else:
                    commands.append('logging {0}'.format(dest))

    return commands


def parse_port(line, dest):
    port = None
    if dest == 'host':
        match = re.search(r'logging host \S+\s+udp-port\s+(\d+)', line, re.M)
        if match:
            port = match.group(1)
        else:
            match_port = re.search(r'logging host ipv6 \S+\s+udp-port\s+(\d+)', line, re.M)
            if match_port:
                port = match_port.group(1)
    return port


def parse_name(line, dest):
    name = None
    if dest == 'host':
        match = re.search(r'logging host (\S+)', line, re.M)
        if match:
            if match.group(1) == 'ipv6':
                ipv6_add = re.search(r'logging host ipv6 (\S+)', line, re.M)
                name = ipv6_add.group(1)
            else:
                name = match.group(1)

    return name


def parse_address(line, dest):
    if dest == 'host':
        match = re.search(r'^logging host ipv6 (\S+)', line.strip(), re.M)
        if match:
            return True
    return False


def map_config_to_obj(module):
    obj = []
    facility = ''
    addr6 = False
    dest_group = ('host', 'console', 'buffered', 'persistence', 'enable')
    dest_level = ('alerts', 'critical', 'debugging', 'emergencies', 'errors', 'informational', 'notifications', 'warnings')
    buff_level = list()
    if module.params['check_running_config'] is False:
        return []
    data = get_config(module, flags=['| include logging'])
    facility_match = re.search(r'^logging facility (\S+)', data, re.M)
    if facility_match:
        facility = facility_match.group(1)
        obj.append({
            'dest': 'facility',
            'facility': facility
        })
    else:
        obj.append({
            'dest': 'facility',
            'facility': 'user'
        })
    for line in data.split('\n'):
        match = re.search(r'^logging (\S+)', line.strip(), re.M)
        if match:

            if match.group(1) in dest_group:
                dest = match.group(1)
                if dest == 'host':
                    obj.append({
                        'dest': dest,
                        'name': parse_name(line.strip(), dest),
                        'udp_port': parse_port(line, dest),
                        'level': None,
                        'addr6': parse_address(line, dest)

                    })
                elif dest == 'buffered':
                    obj.append({
                        'dest': dest,
                        'level': None,
                        'name': None,
                        'udp_port': None,
                        'addr6': False
                    })
                else:
                    if dest == 'enable':
                        dest = 'rfc5424'
                    obj.append({
                        'dest': dest,
                        'level': None,
                        'name': None,
                        'udp_port': None,
                        'addr6': False
                    })
        else:

            ip_match = re.search(r'^no logging buffered (\S+)', line, re.M)
            if ip_match:
                dest = 'buffered'
                buff_level.append(ip_match.group(1))
    if 'no logging on' not in data:
        obj.append({
            'dest': 'on',
            'level': None,
            'name': None,
            'udp_port': None,
            'addr6': False

        })
    levels = set()
    for items in dest_level:
        if items not in buff_level:
            levels.add(items)
    obj.append({
        'dest': 'buffered',
        'level': levels,
        'name': None,
        'udp_port': None,
        'addr6': False

    })
    return obj


def count_terms(check, param=None):
    count = 0
    for term in check:
        if param[term] is not None:
            count += 1
    return count


def check_required_if(module, spec, param):
    for sp in spec:
        missing = []
        max_missing_count = 0
        is_one_of = False
        if len(sp) == 4:
            key, val, requirements, is_one_of = sp
        else:
            key, val, requirements = sp

        if is_one_of:
            max_missing_count = len(requirements)
            term = 'any'
        else:
            term = 'all'

        if key in param and param[key] == val:
            for check in requirements:
                count = count_terms((check,), param)
                if count == 0:
                    missing.append(check)
        if len(missing) and len(missing) >= max_missing_count:
            msg = "%s is %s but %s of the following are missing: %s" % (key, val, term, ', '.join(missing))
            module.fail_json(msg=msg)


def map_params_to_obj(module, required_if=None):
    obj = []
    addr6 = False
    aggregate = module.params.get('aggregate')

    if aggregate:
        for item in aggregate:
            if item['name'] is not None and validate_ip_v6_address(item['name']):
                addr6 = True
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            check_required_if(module, required_if, item)
            item.update({'addr6': addr6})

            d = item.copy()
            d['level'] = set(d['level']) if d['level'] is not None else None
            if d['dest'] != 'host':
                d['name'] = None
                d['udp_port'] = None

            if d['dest'] != 'buffered':
                d['level'] = None
            del d['check_running_config']
            obj.append(d)

    else:
        if module.params['name'] is not None and validate_ip_v6_address(module.params['name']):
            addr6 = True
        if module.params['dest'] != 'host':
            module.params['name'] = None
            module.params['udp_port'] = None

        if module.params['dest'] != 'buffered':
            module.params['level'] = None

        obj.append({
            'dest': module.params['dest'],
            'name': module.params['name'],
            'udp_port': module.params['udp_port'],
            'level': set(module.params['level']) if module.params['level'] else None,
            'facility': module.params['facility'],
            'state': module.params['state'],
            'addr6': addr6
        })
    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        dest=dict(
            type='str',
            choices=[
                'on',
                'host',
                'console',
                'buffered',
                'persistence',
                'rfc5424']),
        name=dict(
            type='str'),
        udp_port=dict(),
        level=dict(
            type='list',
            choices=[
                'alerts',
                'critical',
                'debugging',
                'emergencies',
                'errors',
                'informational',
                'notifications',
                'warnings']),
        facility=dict(
            type='str',
            choices=[
                'auth',
                'cron',
                'daemon',
                'kern',
                'local0',
                'local1',
                'local2',
                'local3',
                'local4',
                'local5',
                'local6',
                'local7',
                'user',
                'lpr',
                'mail',
                'news',
                'syslog',
                'sys9',
                'sys10',
                'sys11',
                'sys12',
                'sys13',
                'sys14',
                'user',
                'uucp']),
        state=dict(
            default='present',
            choices=[
                'present',
                'absent']),
        check_running_config=dict(default=True, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG'])))

    aggregate_spec = deepcopy(element_spec)

    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    required_if = [('dest', 'host', ['name']),
                   ('dest', 'buffered', ['level'])]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    result = {'changed': False}
    warnings = list()

    exec_command(module, 'skip')
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module, required_if=required_if)
    have = map_config_to_obj(module)
    result['want'] = want
    result['have'] = have

    commands = map_obj_to_commands((want, have))
    result['commands'] = commands
    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()
