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
author:
    - "Trishna Guha (@trishnaguha)"
    - "Kedar Kekan (@kedarX)"
short_description: Configuration management of system logging services on network devices
description:
  - This module provides declarative management configuration of system logging (syslog)
    on Cisco IOS XR devices.
requirements:
    - ncclient >= 0.5.3 when using netconf
    - lxml >= 4.1.1 when using netconf
notes:
  - This module works with connection C(network_cli) and C(netconf). See L(the IOS-XR Platform Options,../network/user_guide/platform_iosxr.html).
  - Tested against IOS XRv 6.1.3
options:
  dest:
    description:
      - Destination for system logging (syslog) messages.
    choices: ['host', 'console', 'monitor', 'buffered', 'file']
  name:
    description:
      - When C(dest) = I(file) name indicates file-name
      - When C(dest) = I(host) name indicates the host-name or ip-address of syslog server.
  vrf:
    description:
      - vrf name when syslog server is configured, C(dest) = C(host)
    default: default
    version_added: 2.5
  size:
    description:
      - Size of buffer when C(dest) = C(buffered). The acceptable value is in the range I(307200 to 125000000 bytes). Default 307200
      - Size of file when C(dest) = C(file). The acceptable value is in the range I(1 to 2097152)KB. Default 2 GB
  facility:
    description:
      - To configure the type of syslog facility in which system logging (syslog) messages are sent to syslog servers
        Optional config for C(dest) = C(host)
    default: local7
  hostnameprefix:
    description:
      - To append a hostname prefix to system logging (syslog) messages logged to syslog servers.
        Optional config for C(dest) = C(host)
    version_added: 2.5
  level:
    description:
      - Specifies the severity level for the logging.
    default: debugging
    aliases: ['severity']
  aggregate:
    description: List of syslog logging configuration definitions.
  state:
    description:
      - Existential state of the logging configuration on the node.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: iosxr
"""

EXAMPLES = """
- name: configure logging for syslog server host
  iosxr_logging:
    dest: host
    name: 10.10.10.1
    level: critical
    state: present

- name: add hostnameprefix configuration
  iosxr_logging:
    hostnameprefix: host1
    state: absent

- name: add facility configuration
  iosxr_logging:
    facility: local1
    state: present

- name: configure console logging level
  iosxr_logging:
    dest: console
    level: debugging
    state: present

- name: configure monitor logging level
  iosxr_logging:
    dest: monitor
    level: errors
    state: present

- name: configure syslog to a file
  iosxr_logging:
    dest: file
    name: file_name
    size: 2048
    level: errors
    state: present

- name: configure buffered logging with size
  iosxr_logging:
    dest: buffered
    size: 5100000

- name: Configure logging using aggregate
  iosxr_logging:
    aggregate:
      - { dest: console, level: warning }
      - { dest: buffered, size: 4800000 }
      - { dest: file, name: file3, size: 2048}
      - { dest: host, name: host3, level: critical}

- name: Delete logging using aggregate
  iosxr_logging:
    aggregate:
      - { dest: console, level: warning }
      - { dest: buffered, size: 4800000 }
      - { dest: file, name: file3, size: 2048}
      - { dest: host, name: host3, level: critical}
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always (empty list when no commands to send)
  type: list
  sample:
    - logging 10.10.10.1 vrf default severity debugging
    - logging facility local7
    - logging hostnameprefix host1
    - logging console critical
    - logging buffered 2097153
    - logging buffered warnings
    - logging monitor errors
    - logging file log_file maxfilesize 1024 severity info
xml:
  description: NetConf rpc xml sent to device with transport C(netconf)
  returned: always (empty list when no xml rpc to send)
  type: list
  version_added: 2.5
  sample:
    - '<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <syslog xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-syslog-cfg">
    <files>
    <file xc:operation="delete">
    <file-name>file1</file-name>
    <file-log-attributes>
    <max-file-size>2097152</max-file-size>
    <severity>2</severity>
    </file-log-attributes>
    </file>
    </files>
    </syslog>
    </config>'
"""

import re
import collections
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config, build_xml
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec, etree_findall
from ansible.module_utils.network.iosxr.iosxr import is_netconf, is_cliconf, etree_find
from ansible.module_utils.network.common.utils import remove_default_spec


severity_level = {'emergency': '0',
                  'alert': '1',
                  'critical': '2',
                  'error': '3',
                  'warning': '4',
                  'notice': '5',
                  'info': '6',
                  'debug': '7',
                  'disable': '15'}

severity_transpose = {'emergencies': 'emergency',
                      'alerts': 'alert',
                      'critical': 'critical',
                      'errors': 'error',
                      'warning': 'warning',
                      'notifications': 'notice',
                      'informational': 'info',
                      'debugging': 'debug'}


class ConfigBase(object):
    def __init__(self, module):
        self._flag = None
        self._module = module
        self._result = {'changed': False, 'warnings': []}
        self._want = list()
        self._have = list()

    def validate_size(self, value, type=None):
        if value:
            if type == 'buffer':
                if value and not int(307200) <= value <= int(125000000):
                    self._module.fail_json(msg='buffer size must be between 307200 and 125000000')
            elif type == 'file':
                if value and not int(1) <= value <= int(2097152):
                    self._module.fail_json(msg='file size must be between 1 and 2097152')
        return value

    def map_params_to_obj(self, required_if=None):
        aggregate = self._module.params.get('aggregate')
        if aggregate:
            for item in aggregate:
                for key in item:
                    if item.get(key) is None:
                        item[key] = self._module.params[key]

                d = item.copy()

                if d['dest'] not in ('host', 'file'):
                    d['name'] = None

                if d['dest'] == 'buffered':
                    if d['size'] is not None:
                        d['size'] = str(self.validate_size(d['size'], 'buffer'))
                    else:
                        d['size'] = str(307200)
                elif d['dest'] == 'file':
                    if d['size'] is not None:
                        d['size'] = str(self.validate_size(d['size'], 'file'))
                    else:
                        d['size'] = str(2097152)
                else:
                    d['size'] = None

                if self._flag == 'NC':
                    d['level'] = severity_transpose[d['level']]

                self._want.append(d)

        else:
            params = self._module.params
            if params['dest'] not in ('host', 'file'):
                params['name'] = None

            if params['dest'] == 'buffered':
                if params['size'] is not None:
                    params['size'] = str(self.validate_size(params['size'], 'buffer'))
                else:
                    params['size'] = str(307200)
            elif params['dest'] == 'file':
                if params['size'] is not None:
                    params['size'] = str(self.validate_size(params['size'], 'file'))
                else:
                    params['size'] = str(2097152)
            else:
                params['size'] = None

            if self._flag == 'NC':
                params['level'] = severity_transpose[params['level']]

            self._want.append({
                'dest': params['dest'],
                'name': params['name'],
                'vrf': params['vrf'],
                'size': params['size'],
                'facility': params['facility'],
                'level': params['level'],
                'hostnameprefix': params['hostnameprefix'],
                'state': params['state']
            })


class CliConfiguration(ConfigBase):
    def __init__(self, module):
        super(CliConfiguration, self).__init__(module)
        self._file_list = set()
        self._host_list = set()

    def map_obj_to_commands(self):
        commands = list()
        for want_item in self._want:
            dest = want_item['dest']
            name = want_item['name']
            size = want_item['size']
            facility = want_item['facility']
            level = want_item['level']
            vrf = want_item['vrf']
            hostnameprefix = want_item['hostnameprefix']
            state = want_item['state']
            del want_item['state']

            have_size = None
            have_console_level = None
            have_monitor_level = None
            have_prefix = None
            have_facility = None

            for item in self._have:
                if item['dest'] == 'buffered':
                    have_size = item['size']
                if item['dest'] == 'console':
                    have_console_level = item['level']
                if item['dest'] == 'monitor':
                    have_monitor_level = item['level']
                if item['dest'] is None and item['hostnameprefix'] is not None:
                    have_prefix = item['hostnameprefix']
                if item['dest'] is None and item['hostnameprefix'] is None and item['facility'] is not None:
                    have_facility = item['facility']

            if state == 'absent':
                if dest == 'host' and name in self._host_list:
                    commands.append('no logging {0} vrf {1}'.format(name, vrf))
                elif dest == 'file' and name in self._file_list:
                    commands.append('no logging file {0}'.format(name))
                elif dest == 'console' and have_console_level is not None:
                    commands.append('no logging {0}'.format(dest))
                elif dest == 'monitor' and have_monitor_level:
                    commands.append('no logging {0}'.format(dest))
                elif dest == 'buffered' and have_size:
                    commands.append('no logging {0}'.format(dest))

                if dest is None and hostnameprefix is not None and have_prefix == hostnameprefix:
                    commands.append('no logging hostnameprefix {0}'.format(hostnameprefix))
                if dest is None and facility is not None and have_facility == facility:
                    commands.append('no logging facility {0}'.format(facility))

            if state == 'present':
                if dest == 'host' and name not in self._host_list:
                    if level == 'errors' or level == 'informational':
                        level = severity_transpose[level]
                    commands.append('logging {0} vrf {1} severity {2}'.format(name, vrf, level))
                elif dest == 'file' and name not in self._file_list:
                    if level == 'errors' or level == 'informational':
                        level = severity_transpose[level]
                    commands.append('logging file {0} maxfilesize {1} severity {2}'.format(name, size, level))
                elif dest == 'buffered' and (have_size is None or (have_size is not None and size != have_size)):
                    commands.append('logging buffered {0}'.format(size))
                elif dest == 'console' and (have_console_level is None or
                                            (have_console_level is not None and have_console_level != level)):
                    commands.append('logging console {0}'.format(level))
                elif dest == 'monitor' and (have_monitor_level is None or
                                            (have_monitor_level is not None and have_monitor_level != level)):
                    commands.append('logging monitor {0}'.format(level))

                if dest is None and hostnameprefix is not None and (have_prefix is None or
                                                                    (have_prefix is not None and hostnameprefix != have_prefix)):
                    commands.append('logging hostnameprefix {0}'.format(hostnameprefix))
                if dest is None and hostnameprefix is None and facility != have_facility:
                    commands.append('logging facility {0}'.format(facility))

        self._result['commands'] = commands
        if commands:
            commit = not self._module.check_mode
            diff = load_config(self._module, commands, commit=commit)
            if diff:
                self._result['diff'] = dict(prepared=diff)
            self._result['changed'] = True

    def parse_facility(self, line):
        match = re.search(r'logging facility (\S+)', line, re.M)
        facility = None
        if match:
            facility = match.group(1)

        return facility

    def parse_size(self, line, dest):
        size = None

        if dest == 'buffered':
            match = re.search(r'logging buffered (\S+)', line, re.M)
            if match:
                try:
                    int_size = int(match.group(1))
                except ValueError:
                    int_size = None

                if int_size is not None:
                    if isinstance(int_size, int):
                        size = str(match.group(1))
        return size

    def parse_hostnameprefix(self, line):
        prefix = None
        match = re.search(r'logging hostnameprefix (\S+)', line, re.M)
        if match:
            prefix = match.group(1)
        return prefix

    def parse_name(self, line, dest):
        name = None
        if dest == 'file':
            match = re.search(r'logging file (\S+)', line, re.M)
            if match:
                name = match.group(1)
        elif dest == 'host':
            match = re.search(r'logging (\S+)', line, re.M)
            if match:
                name = match.group(1)

        return name

    def parse_level(self, line, dest):
        level_group = ('emergencies', 'alerts', 'critical', 'errors', 'warning',
                       'notifications', 'informational', 'debugging')

        level = None
        match = re.search(r'logging {0} (\S+)'.format(dest), line, re.M)
        if match:
            if match.group(1) in level_group:
                level = match.group(1)

        return level

    def parse_dest(self, line, group):
        dest_group = ('console', 'monitor', 'buffered', 'file')
        dest = None
        if group in dest_group:
            dest = group
        elif 'vrf' in line:
            dest = 'host'

        return dest

    def parse_vrf(self, line, dest):
        vrf = None
        if dest == 'host':
            match = re.search(r'logging (\S+) vrf (\S+)', line, re.M)
            if match:
                vrf = match.group(2)
        return vrf

    def map_config_to_obj(self):
        data = get_config(self._module, config_filter='logging')
        lines = data.split("\n")

        for line in lines:
            match = re.search(r'logging (\S+)', line, re.M)
            if match:
                dest = self.parse_dest(line, match.group(1))
                name = self.parse_name(line, dest)
                if dest == 'host' and name is not None:
                    self._host_list.add(name)
                if dest == 'file' and name is not None:
                    self._file_list.add(name)

                self._have.append({
                    'dest': dest,
                    'name': name,
                    'size': self.parse_size(line, dest),
                    'facility': self.parse_facility(line),
                    'level': self.parse_level(line, dest),
                    'vrf': self.parse_vrf(line, dest),
                    'hostnameprefix': self.parse_hostnameprefix(line),
                })

    def run(self):
        self.map_params_to_obj()
        self.map_config_to_obj()
        self.map_obj_to_commands()

        return self._result


class NCConfiguration(ConfigBase):
    def __init__(self, module):
        super(NCConfiguration, self).__init__(module)
        self._flag = 'NC'
        self._log_file_meta = collections.OrderedDict()
        self._log_host_meta = collections.OrderedDict()
        self._log_console_meta = collections.OrderedDict()
        self._log_monitor_meta = collections.OrderedDict()
        self._log_buffered_size_meta = collections.OrderedDict()
        self._log_buffered_level_meta = collections.OrderedDict()
        self._log_facility_meta = collections.OrderedDict()
        self._log_prefix_meta = collections.OrderedDict()

    def map_obj_to_xml_rpc(self):
        self._log_file_meta.update([
            ('files', {'xpath': 'syslog/files', 'tag': True, 'operation': 'edit'}),
            ('file', {'xpath': 'syslog/files/file', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:name', {'xpath': 'syslog/files/file/file-name', 'operation': 'edit'}),
            ('file-attrib', {'xpath': 'syslog/files/file/file-log-attributes', 'tag': True, 'operation': 'edit'}),
            ('a:size', {'xpath': 'syslog/files/file/file-log-attributes/max-file-size', 'operation': 'edit'}),
            ('a:level', {'xpath': 'syslog/files/file/file-log-attributes/severity', 'operation': 'edit'}),
        ])
        self._log_host_meta.update([
            ('host-server', {'xpath': 'syslog/host-server', 'tag': True, 'operation': 'edit'}),
            ('vrfs', {'xpath': 'syslog/host-server/vrfs', 'tag': True, 'operation': 'edit'}),
            ('vrf', {'xpath': 'syslog/host-server/vrfs/vrf', 'tag': True, 'operation': 'edit'}),
            ('a:vrf', {'xpath': 'syslog/host-server/vrfs/vrf/vrf-name', 'operation': 'edit'}),
            ('ipv4s', {'xpath': 'syslog/host-server/vrfs/vrf/ipv4s', 'tag': True, 'operation': 'edit'}),
            ('ipv4', {'xpath': 'syslog/host-server/vrfs/vrf/ipv4s/ipv4', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:name', {'xpath': 'syslog/host-server/vrfs/vrf/ipv4s/ipv4/address', 'operation': 'edit'}),
            ('ipv4-sev', {'xpath': 'syslog/host-server/vrfs/vrf/ipv4s/ipv4/ipv4-severity-port', 'tag': True, 'operation': 'edit'}),
            ('a:level', {'xpath': 'syslog/host-server/vrfs/vrf/ipv4s/ipv4/ipv4-severity-port/severity', 'operation': 'edit'}),
        ])
        self._log_console_meta.update([
            ('a:enable-console', {'xpath': 'syslog/enable-console-logging', 'operation': 'edit', 'attrib': "operation"}),
            ('console', {'xpath': 'syslog/console-logging', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:console-level', {'xpath': 'syslog/console-logging/logging-level', 'operation': 'edit'}),
        ])
        self._log_monitor_meta.update([
            ('monitor', {'xpath': 'syslog/monitor-logging', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:monitor-level', {'xpath': 'syslog/monitor-logging/logging-level', 'operation': 'edit'}),
        ])
        self._log_buffered_size_meta.update([
            ('buffered', {'xpath': 'syslog/buffered-logging', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:size', {'xpath': 'syslog/buffered-logging/buffer-size', 'operation': 'edit'}),
        ])
        self._log_buffered_level_meta.update([
            ('buffered', {'xpath': 'syslog/buffered-logging', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:level', {'xpath': 'syslog/buffered-logging/logging-level', 'operation': 'edit'}),
        ])
        self._log_facility_meta.update([
            ('facility', {'xpath': 'syslog/logging-facilities', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:facility', {'xpath': 'syslog/logging-facilities/facility-level', 'operation': 'edit'}),
        ])
        self._log_prefix_meta.update([
            ('a:hostnameprefix', {'xpath': 'syslog/host-name-prefix', 'operation': 'edit', 'attrib': "operation"}),
        ])

        state = self._module.params['state']

        _get_filter = build_xml('syslog', opcode="filter")
        running = get_config(self._module, source='running', config_filter=_get_filter)

        file_ele = etree_findall(running, 'file')
        file_list = list()
        if len(file_ele):
            for file in file_ele:
                file_name = etree_find(file, 'file-name')
                file_list.append(file_name.text if file_name is not None else None)
        vrf_ele = etree_findall(running, 'vrf')
        host_list = list()
        for vrf in vrf_ele:
            host_ele = etree_findall(vrf, 'ipv4')
            for host in host_ele:
                host_name = etree_find(host, 'address')
                host_list.append(host_name.text if host_name is not None else None)

        console_ele = etree_find(running, 'console-logging')
        console_level = etree_find(console_ele, 'logging-level') if console_ele is not None else None
        have_console = console_level.text if console_level is not None else None

        monitor_ele = etree_find(running, 'monitor-logging')
        monitor_level = etree_find(monitor_ele, 'logging-level') if monitor_ele is not None else None
        have_monitor = monitor_level.text if monitor_level is not None else None

        buffered_ele = etree_find(running, 'buffered-logging')
        buffered_size = etree_find(buffered_ele, 'buffer-size') if buffered_ele is not None else None
        have_buffered = buffered_size.text if buffered_size is not None else None

        facility_ele = etree_find(running, 'logging-facilities')
        facility_level = etree_find(facility_ele, 'facility-level') if facility_ele is not None else None
        have_facility = facility_level.text if facility_level is not None else None

        prefix_ele = etree_find(running, 'host-name-prefix')
        have_prefix = prefix_ele.text if prefix_ele is not None else None

        file_params = list()
        host_params = list()
        console_params = dict()
        monitor_params = dict()
        buffered_params = dict()
        facility_params = dict()
        prefix_params = dict()

        opcode = None
        if state == 'absent':
            opcode = "delete"
            for item in self._want:
                if item['dest'] == 'file' and item['name'] in file_list:
                    item['level'] = severity_level[item['level']]
                    file_params.append(item)
                elif item['dest'] == 'host' and item['name'] in host_list:
                    item['level'] = severity_level[item['level']]
                    host_params.append(item)
                elif item['dest'] == 'console' and have_console:
                    console_params.update({'console-level': item['level']})
                elif item['dest'] == 'monitor' and have_monitor:
                    monitor_params.update({'monitor-level': item['level']})
                elif item['dest'] == 'buffered' and have_buffered:
                    buffered_params['size'] = str(item['size']) if item['size'] else None
                    buffered_params['level'] = item['level'] if item['level'] else None
                elif item['dest'] is None and item['hostnameprefix'] is None and \
                        item['facility'] is not None and have_facility:
                    facility_params.update({'facility': item['facility']})
                elif item['dest'] is None and item['hostnameprefix'] is not None and have_prefix:
                    prefix_params.update({'hostnameprefix': item['hostnameprefix']})
        elif state == 'present':
            opcode = 'merge'
            for item in self._want:
                if item['dest'] == 'file':
                    item['level'] = severity_level[item['level']]
                    file_params.append(item)
                elif item['dest'] == 'host':
                    item['level'] = severity_level[item['level']]
                    host_params.append(item)
                elif item['dest'] == 'console':
                    console_params.update({'console-level': item['level']})
                elif item['dest'] == 'monitor':
                    monitor_params.update({'monitor-level': item['level']})
                elif item['dest'] == 'buffered':
                    buffered_params['size'] = str(item['size']) if item['size'] else None
                    buffered_params['level'] = item['level'] if item['level'] else None
                elif item['dest'] is None and item['hostnameprefix'] is None and \
                        item['facility'] is not None:
                    facility_params.update({'facility': item['facility']})
                elif item['dest'] is None and item['hostnameprefix'] is not None:
                    prefix_params.update({'hostnameprefix': item['hostnameprefix']})

        self._result['xml'] = []
        _edit_filter_list = list()
        if opcode:
            if len(file_params):
                _edit_filter_list.append(build_xml('syslog', xmap=self._log_file_meta,
                                                   params=file_params, opcode=opcode))
            if len(host_params):
                _edit_filter_list.append(build_xml('syslog', xmap=self._log_host_meta,
                                                   params=host_params, opcode=opcode))
            if len(console_params):
                _edit_filter_list.append(build_xml('syslog', xmap=self._log_console_meta,
                                                   params=console_params, opcode=opcode))
            if len(monitor_params):
                _edit_filter_list.append(build_xml('syslog', xmap=self._log_monitor_meta,
                                                   params=monitor_params, opcode=opcode))
            if len(buffered_params):
                _edit_filter_list.append(build_xml('syslog', xmap=self._log_buffered_size_meta,
                                                   params=buffered_params, opcode=opcode))
                _edit_filter_list.append(build_xml('syslog', xmap=self._log_buffered_level_meta,
                                                   params=buffered_params, opcode=opcode))
            if len(facility_params):
                _edit_filter_list.append(build_xml('syslog', xmap=self._log_facility_meta,
                                                   params=facility_params, opcode=opcode))
            if len(prefix_params):
                _edit_filter_list.append(build_xml('syslog', xmap=self._log_prefix_meta,
                                                   params=prefix_params, opcode=opcode))

            diff = None
            if len(_edit_filter_list):
                commit = not self._module.check_mode
                diff = load_config(self._module, _edit_filter_list, commit=commit, running=running,
                                   nc_get_filter=_get_filter)

            if diff:
                if self._module._diff:
                    self._result['diff'] = dict(prepared=diff)

                self._result['xml'] = _edit_filter_list
                self._result['changed'] = True

    def run(self):
        self.map_params_to_obj()
        self.map_obj_to_xml_rpc()

        return self._result


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        dest=dict(type='str', choices=['host', 'console', 'monitor', 'buffered', 'file']),
        name=dict(type='str'),
        size=dict(type='int'),
        vrf=dict(type='str', default='default'),
        facility=dict(type='str', default='local7'),
        hostnameprefix=dict(type='str'),
        level=dict(type='str', default='informational', aliases=['severity'],
                   choices=['emergencies', 'alerts', 'critical', 'errors', 'warning',
                            'notifications', 'informational', 'debugging']),
        state=dict(default='present', choices=['present', 'absent']),
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    mutually_exclusive = [('dest', 'facility', 'hostnameprefix')]

    required_if = [('dest', 'host', ['name']),
                   ('dest', 'file', ['name']),
                   ('dest', 'buffered', ['size']),
                   ('dest', 'console', ['level']),
                   ('dest', 'monitor', ['level'])]

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec,
                       mutually_exclusive=mutually_exclusive, required_if=required_if),
    )

    argument_spec.update(element_spec)
    argument_spec.update(iosxr_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    config_object = None
    if is_cliconf(module):
        # Commenting the below cliconf deprecation support call for Ansible 2.9 as it'll be continued to be supported
        # module.deprecate("cli support for 'iosxr_interface' is deprecated. Use transport netconf instead",
        #                  version='2.9')
        config_object = CliConfiguration(module)
    elif is_netconf(module):
        config_object = NCConfiguration(module)

    if config_object:
        result = config_object.run()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
