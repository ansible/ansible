#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: onyx_syslog_remote
version_added: "2.10"
author: "Anas Shami (@anass)"
short_description: Configure remote syslog module
description:
  - This module provides declarative management of syslog
    on Mellanox ONYX network devices.
notes:
options:
    enabled:
        description:
          - Disable/Enable logging to given remote host
        default: true
        type: bool
    host:
        description:
          - <IP4/IP6 Hostname> Send event logs to this server using the syslog protocol
        required: true
        type: str
    port:
        description:
          - Set remote server destination port for log messages
        type: int
    trap:
        description:
          - Minimum severity level for messages to this syslog server
        choices: ['none', 'debug', 'info', 'notice', 'alert', 'warning', 'err', 'emerg', 'crit']
        type: str
    trap_override:
        description:
          - Override log levels for this sink on a per-class basis
        type: list
        suboptions:
            override_class:
                description:
                  - Specify a class whose log level to override
                choices: ['mgmt-front', 'mgmt-back', 'mgmt-core', 'events', 'debug-module', 'sx-sdk', 'mlx-daemons', 'protocol-stack']
                required: True
                type: str
            override_priority:
                description:
                  -Specify a priority whose log level to override
                choices: ['none', 'debug', 'info', 'notice', 'alert', 'warning', 'err', 'emerg', 'crit']
                type: str
            override_enabled:
                description:
                  - disable override priorities for specific class.
                default: True
                type: bool

    filter:
        description:
          - Specify a filter type
        choices: ['include', 'exclude']
        type: str
    filter_str:
        description:
          - Specify a regex filter string
        type: str
"""

EXAMPLES = """
- name: remote logging port 8080
- onyx_syslog_remote:
    host: 10.10.10.10
    port: 8080

- name: remote logging trap override
- onyx_syslog_remote:
    host: 10.10.10.10
    trap_override:
        - override_class: events
          override_priority: emerg

- name: remote logging trap emerg
- onyx_syslog_remote:
    host: 10.10.10.10
    trap: emerg

- name: remote logging filter include 'ERR'
- onyx_syslog_remote:
    host: 10.10.10.10
    filter: include
    filter_str: /ERR/

- name: disable remote logging with class events
- onyx_syslog_remote:
    enabled: False
    host: 10.10.10.10
    class: events
- name : disable remote logging
- onyx_syslog_remote:
    enabled: False
    host: 10.10.10.10

- name : enable/disable override class
- onyx_syslog_remote:
    host: 10.7.144.71
    trap_override:
        - override_class: events
          override_priority: emerg
          override_enabled: False
        - override_class: mgmt-front
          override_priority: alert
"""

RETURN = """
commands:
    description: The list of configuration mode commands to send to the device.
    returned: always
    type: list
    sample:
        - logging x port 8080
        - logging 10.10.10.10 trap override class events priority emerg
        - no logging 10.10.10.10 trap override class events
        - logging 10.10.10.10 trap emerg
        - logging 10.10.10.10 filter [include | exclude] ERR
"""

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxSyslogRemoteModule(BaseOnyxModule):
    MAX_PORT = 65535
    LEVELS = ['none', 'debug', 'info', 'notice', 'alert', 'warning', 'err', 'emerg', 'crit']
    CLASSES = ['mgmt-front', 'mgmt-back', 'mgmt-core', 'events', 'debug-module', 'sx-sdk', 'mlx-daemons', 'protocol-stack']
    FILTER = ['include', 'exclude']

    LOGGING_HOST = re.compile(r'^logging ([a-z0-9\.]+)$')
    LOGGING_PORT = re.compile(r'^logging ([a-z0-9\.]+) port ([0-9]+)$')
    LOGGING_TRAP = re.compile(r'^logging ([a-z0-9\.]+) trap ([a-z]+)$')
    LOGGING_TRAP_OVERRIDE = re.compile(r'^logging ([a-z0-9\.]+) trap override class ([a-z\-]+) priority ([a-z]+)$')
    LOGGING_FILTER = re.compile(r'^logging ([a-z0-9\.]+) filter (include|exclude) "([\D\d]+)"$')

    def init_module(self):
        """" Ansible module initialization
        """
        override_spec = dict(override_priority=dict(choices=self.LEVELS),
                             override_class=dict(choices=self.CLASSES, required=True),
                             override_enabled=dict(default=True, type="bool"))

        element_spec = dict(enabled=dict(type="bool", default=True),
                            host=dict(type="str", required=True),
                            port=dict(type="int"),
                            trap=dict(choices=self.LEVELS),
                            trap_override=dict(type="list", elements='dict', options=override_spec),
                            filter=dict(choices=self.FILTER),
                            filter_str=dict(type="str"))

        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_together=[
                ['filter', 'filter_str']
            ])

    def validate_port(self, port):
        if port and (port < 1 or port > self.MAX_PORT):
            self._module.fail_json(msg='logging port must be between 1 and {0}'.format(self.MAX_PORT))

    def show_logging(self):
        # we can't use show logging it has lack of information
        return show_cmd(self._module, "show running-config | include .*logging.*", json_fmt=False, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        current_config = self.show_logging().split('\n')
        for line in current_config:
            line = line.strip()
            match = self.LOGGING_HOST.match(line)
            if match:
                host = match.group(1)
                self._current_config[host] = dict()
                continue

            match = self.LOGGING_PORT.match(line)
            if match:
                host = match.group(1)
                port = int(match.group(2))
                if host in self._current_config:
                    self._current_config[host]['port'] = port
                else:
                    self._current_config[host] = dict(port=port)
                continue

            match = self.LOGGING_TRAP.match(line)
            if match:
                host = match.group(1)
                trap = match.group(2)
                host_config = self._current_config.get(host)
                if host_config:
                    self._current_config[host]['trap'] = trap
                else:
                    self._current_config[host] = dict(trap=trap)
                continue

            match = self.LOGGING_TRAP_OVERRIDE.match(line)
            if match:
                host = match.group(1)
                override_class = match.group(2)
                override_priority = match.group(3)
                host_config = self._current_config.get(host)

                if host_config:
                    if 'trap_override' in host_config:
                        self._current_config[host]['trap_override'].append(dict(override_class=override_class, override_priority=override_priority))
                    else:
                        self._current_config[host]['trap_override'] = [dict(override_class=override_class, override_priority=override_priority)]
                else:
                    self._current_config[host] = {'trap_override': [dict(override_class=override_class, override_priority=override_priority)]}
                continue

            match = self.LOGGING_FILTER.match(line)
            if match:
                host = match.group(1)
                filter_type = match.group(2)
                filter_str = match.group(3)
                if host in self._current_config:
                    self._current_config[host].update({'filter': filter_type, 'filter_str': filter_str})
                else:
                    self._current_config[host] = dict(filter=filter_type, filter_str=filter_str)

    def get_required_config(self):
        self._required_config = dict()
        required_config = dict()
        module_params = self._module.params
        port = module_params.get('port')
        trap = module_params.get('trap')
        trap_override = module_params.get('trap_override')
        filtered = module_params.get('filter')

        required_config['host'] = module_params.get('host')
        required_config['enabled'] = module_params.get('enabled')

        if port:
            required_config['port'] = port
        if trap:
            required_config['trap'] = trap
        if trap_override:
            required_config['trap_override'] = trap_override
        if filtered:
            required_config['filter'] = filtered
            required_config['filter_str'] = module_params.get('filter_str', '')

        self.validate_param_values(required_config)
        self._required_config = required_config

    def generate_commands(self):
        required_config = self._required_config
        current_config = self._current_config
        host = required_config.get('host')
        enabled = required_config['enabled']
        '''
        cases:
        if host in current config and current config != required config and its enable
        if host in current config and its disable
        if host in current and it has override_class with disable flag
        '''
        host_config = current_config.get(host, dict())

        if host in current_config and not enabled:
            self._commands.append('no logging {0}'.format(host))
        else:
            if host not in current_config:
                self._commands.append('logging {0}'.format(host))
            if 'port' in required_config:
                if required_config['port'] != host_config.get('port', None) or not host_config:
                    '''Edit/Create new one'''
                    self._commands.append('logging {0} port {1}'.format(host, required_config['port']))

            if 'trap' in required_config or 'trap_override' in required_config:
                trap_commands = self._get_trap_commands(host)
                self._commands += trap_commands

            if 'filter' in required_config:
                is_change = host_config.get('filter', None) != required_config['filter'] or \
                    host_config.get('filter_str', None) != required_config['filter_str']
                if is_change or not host_config:
                    self._commands.append('logging {0} filter {1} {2}'.format(host, required_config['filter'], required_config['filter_str']))

    ''' ********** private methods ********** '''
    def _get_trap_commands(self, host):
        current_config = self._current_config
        required_config = self._required_config
        trap_commands = []
        host_config = current_config.get(host, dict())

        override_list = required_config.get('trap_override')
        if override_list:
            current_override_list = host_config.get('trap_override', [])

            for override_trap in override_list:
                override_class = override_trap.get('override_class')
                override_priority = override_trap.get('override_priority')
                override_enabled = override_trap.get('override_enabled')
                found, found_class = False, False
                for current_override in current_override_list:
                    if current_override.get('override_class') == override_class:
                        found_class = True
                        if not override_enabled:
                            break
                        if override_priority and current_override.get('override_priority') == override_priority:
                            found = True
                            break

                if override_enabled:
                    if not found and override_priority:
                        trap_commands.append('logging {0} trap override class {1} priority {2}'.format(
                            host, override_class, override_priority))
                elif found_class:  # disabled option will use only class
                    trap_commands.append('no logging {0} trap override class {1}'.format(
                        host, override_class))

        else:
            if required_config['enabled']:  # no disabled option for this, just override trap level can be disabled
                trap = required_config.get('trap')
                if trap and (trap != host_config.get('trap', None) or not host_config):
                    trap_commands.append('logging {0} trap {1}'.format(
                        host, trap))
        '''no disable for trap'''

        return trap_commands


def main():
    """ main entry point for module execution
    """
    OnyxSyslogRemoteModule.main()


if __name__ == '__main__':
    main()
