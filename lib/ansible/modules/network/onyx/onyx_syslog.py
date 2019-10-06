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
module: onyx_syslog
version_added: "2.10"
author: "Anas Shami (@anass)"
short_description: Configure system logging module
description:
  - This module provides declarative management of syslog
    on Mellanox ONYX network devices.
notes:
options:
    enabled:
        description:
          - Enable/Disable logging properity
        choices: ['enabled', 'disabled']
        type: str
        default: 'enabled'
    local_level:
        description:
          - Set minimum severity of log messages saved on the local disk
        choices: ['alert', 'crit', 'debug', 'emerg', 'err', 'info', 'none', 'notice', 'warning']
        type: str
    local_override:
        description:
          - list of override log levels
        type: list
        suboptions:
            override_class:
                description:
                - Specify a class whose log level to override
                choices: ['mgmt-front', 'mgmt-back', 'mgmt-core', 'events', 'debug-module', 'sx-sdk', 'mlx-daemons', 'protocol-stack']
                type: str
                required: true
            override_priority:
                description:
                - Specify a priority whose log level to override
                choices: ['alert', 'crit', 'debug', 'emerg', 'err', 'info', 'none', 'notice', 'warning']
                type: str
    cli_level:
        description:
          - Set the severity level of certain CLI log messages
        choices: ['alert', 'crit', 'debug', 'emerg', 'err', 'info', 'none', 'notice', 'warning']
        type: str
    audit_level:
        description:
          - Set the severity level of audit messages for configuration changes and actions taken by the user
        choices: ['alert', 'crit', 'debug', 'emerg', 'err', 'info', 'none', 'notice', 'warning']
        type: str
    format:
        description:
          - Set format used for log messages
        choices: ['standard', 'welf']
        type: str
    format_welf_host:
        description:
           - Set firewall name used in WELF log messages
        type: str
    received:
        description:
           - Allow receiving of syslog messages from remote hosts
        type: bool
    trap:
        description:
           - Set minimum severity of log messages sent to syslog servers
        choices: ['alert', 'crit', 'debug', 'emerg', 'err', 'info', 'none', 'notice', 'warning']
        type: str
    trap_enabled:
        description:
           - Enable/Disable minimum severity of log messages sent to syslog servers
        choices: ['enabled', 'disabled']
        type: str
        default: 'enabled'

    seconds_enabled:
        description:
        - Enable/Disable the seconds field
        choices: ['enabled', 'disabled']
        type: str
    fractional_digits:
        description:
        - Specify the number of digits to the right of the decimal point (truncation is from the right)
        choices: [1, 2, 3, 6]
        type: int
    whole_digits:
        description:
        - Specify the number of digits to the left of the decimal point (truncation is from the left)
        choices: ['1', '6', 'all']
        type: str

    monitor:
        description:
          - List of monitor log
        type: list
        suboptions:
            monitor_facility:
                description:
                - Set monitor log facility
                choices: ['mgmt-front', 'mgmt-back', 'mgmt-core', 'events', 'debug-module', 'sx-sdk', 'mlx-daemons', 'protocol-stack']
                type: str
                required: true
            monitor_level:
                description:
                - Set monitor log level
                choices: ['alert', 'crit', 'debug', 'emerg', 'err', 'info', 'none', 'notice', 'warning']
                type: str
"""

EXAMPLES = """
    - name: change the trap level, local level, cli level, audit level and enable received
    - onyx_syslog:
       local_level: emerg
       trap: alert
       cli_level: notice
       audit_level: none
       received: yes

    - name: override log messages for a list of classes
    - onyx_syslog:
       local_override:
        - override_class: mgmt-front
          override_priority: emerg
        - override_class: mgmt-back
          override_priority: alert

    - name: monitor log messages for a list of facilities
    - onyx_syslog:
       monitor:
        - monitor_facility: mgmt-front
          monitor_level: emerg
        - monitor_facility: mgmt-back
          monitor_level: alert

    - name: monitor log messages for a list of facilities
    - onyx_syslog:
        seconds_enabled: enabled
        fractional_digits: 2
        whole_digits: '6'

"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - logging [trap | local |  ] alert
    - logging level [cli | audit mgmt] emerg
    - logging monitor mgmt-front emerg
    - logging receive
    - logging fields seconds fractional-digits 1
    - logging fields seconds enable
    - logging fields seconds whole-digits all
    - logging format welf fw-name hostname
    - logging format standard
    - no logging trap
    - no logging fields seconds enable
    - no logging local override class mgmt-front
    - no logging format welf
    - no logging moitor mgmt-front
    - no logging receive
    - no logging fields seconds enable
"""
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule, show_cmd


class OnyxSyslogModule(BaseOnyxModule):

    FACILITIES = ['mgmt-front', 'mgmt-back', 'mgmt-core', 'events', 'debug-module', 'sx-sdk', 'mlx-daemons', 'protocol-stack']
    LEVELS = ['alert', 'crit', 'debug', 'emerg', 'err', 'info', 'none', 'notice', 'warning']
    FORMAT_WELF_RGX = re.compile('^.*logging format welf fw-name (.*)$')
    FRACTINAL_RGX = re.compile('^.*logging fields seconds fractional-digits ([1-9]).*$')
    WHOLE_RGX = re.compile('^.*logging fields seconds whole-digits (1|6|all).*$')

    def init_module(self):
        """
        module initialization
        """
        override_spec = dict(override_class=dict(type='str', choices=self.FACILITIES, required=True),
                             override_priority=dict(type='str', choices=self.LEVELS))

        monitor_spec = dict(monitor_facility=dict(type='str', choices=self.FACILITIES, required=True),
                            monitor_level=dict(type='str', choices=self.LEVELS))

        element_spec = dict(enabled=dict(type="str", choices=['enabled', 'disabled'], default='enabled'),
                            local_level=dict(type='str', choices=self.LEVELS),
                            trap=dict(type='str', choices=self.LEVELS),
                            trap_enabled=dict(type="str", choices=['enabled', 'disabled'], default='enabled'),
                            cli_level=dict(type='str', choices=self.LEVELS),
                            audit_level=dict(type='str', choices=self.LEVELS),
                            monitor=dict(type='list', options=monitor_spec),
                            local_override=dict(type='list', options=override_spec),
                            format=dict(type='str', choices=['welf', 'standard']),
                            format_welf_host=dict(type='str'),
                            received=dict(type="bool"),
                            seconds_enabled=dict(type="str", choices=['enabled', 'disabled']),
                            fractional_digits=dict(type='int', choices=[1, 2, 3, 6]),
                            whole_digits=dict(type='str', choices=['1', '6', 'all']))
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_if=[
                ['format', 'welf', ['format_welf_host']]
            ],
            required_one_of=[
                ['trap_enabled', 'trap']
            ])

    def get_required_config(self):
        self._required_config = dict()
        module_params = self._module.params
        required_config = dict()

        for key, value in module_params.items():
            if value:
                required_config[key] = value
        self.validate_param_values(required_config)
        self._required_config = required_config

    def _get_syslog_config(self):
        running_config = show_cmd(self._module, 'show running-config | include .*logging.*(fields\\|welf).*', json_fmt=True, fail_on_error=False)
        config = show_cmd(self._module, 'show logging', json_fmt=True, fail_on_error=False)
        if len(config) > 0:
            config[0]['lines'] = running_config['Lines'] if 'Lines' in running_config else []
        else:
            config = [{
                'lines': running_config['Lines'] if 'Lines' in running_config else []
            }]
        return config

    def load_current_config(self):
        syslog_config = self._get_syslog_config()
        self._current_config = dict()
        current_config = dict()

        map_key_value = {
            'Log format': 'format',
            'Allow receiving of messages from remote hosts': 'received',
            'Subsecond timestamp field': 'seconds_enabled',
            'Local logging level': 'local_level',
            'Default remote logging level': 'trap'
        }

        map_key_list = {
            'Levels at which messages are logged': {
                'alias': {
                    'CLI commands': 'cli_level',
                    'Audit messages': 'audit_level'
                }
            },
            'Levels at which messages are echoed to all sessions': {
                'name': 'monitor',
                'keys': ['monitor_facility', 'monitor_level']
            }
        }
        override_prefix = 'Override for class'
        for obj in syslog_config:
            for key, value in obj.items():
                if key in map_key_value:
                    current_key = map_key_value[key]
                    current_config[current_key] = value
                elif key in map_key_list:
                    map_obj = value[0]
                    map_key_element = map_key_list[key]
                    if 'name' in map_key_element:
                        name = map_key_element['name']
                        keys = map_key_element['keys']
                        current_config[name] = [{keys[0]: key, keys[1]: value}
                                                for key, value in map_obj.items()]
                    else:
                        alias = map_key_element['alias']
                        for show_key, current_key in alias.items():
                            current_config[current_key] = map_obj[show_key]
                elif override_prefix in key:
                    override_class = key.replace(override_prefix, '').strip()
                    override_priority = value
                    if 'local_override'in current_config:
                        current_config['local_override'].append({
                            'override_class': override_class,
                            'override_priority': override_priority
                        })
                    else:
                        current_config['local_override'] = [{
                            'override_class': override_class,
                            'override_priority': override_priority
                        }]

        current_config['received'] = True if current_config.get('received') == 'yes' else False
        ''' extract 'format/fields' from running config line (if any ?) its single line - no'''
        if syslog_config and syslog_config[0].get('lines'):
            lines = syslog_config[0].get('lines')
            for line in lines:
                match = self.FORMAT_WELF_RGX.match(line)
                if match:
                    current_config['format_welf_host'] = match.group(1)

                match = self.WHOLE_RGX.match(line)
                if match:
                    current_config['whole_digits'] = match.group(1)

                match = self.FRACTINAL_RGX.match(line)
                if match:
                    current_config['fractional_digits'] = int(match.group(1))

        self._current_config = current_config

    def generate_commands(self):
        required_config = self._required_config
        current_config = self._current_config
        commands = []
        is_disabled = required_config.get('enabled') == 'disabled'

        local_level = required_config.get('local_level')
        if local_level:
            if local_level != current_config.get('local_level'):
                commands.append('logging local {0}'.format(local_level))

        if required_config.get('trap_enabled') == 'disabled' and current_config.get('trap'):  # reset trap if current trap is exist
            commands.append('no logging trap')

        trap = required_config.get('trap')
        if trap:
            if trap != current_config.get('trap'):
                commands.append('logging trap {0}'.format(trap))

        format_str = required_config.get('format')
        if format_str:
            if format_str == 'welf':
                req_format_host = required_config.get('format_welf_host')
                if format_str != current_config.get('format') or req_format_host != current_config.get('format_welf_host'):
                    commands.append('logging format welf fw-name {0}'.format(req_format_host))
            elif format_str != current_config.get('format'):
                commands.append('logging format standard')

        is_received = required_config.get('received')
        if is_received != current_config.get('received'):
            commands.append('{0}logging receive'.format('' if is_received else 'no '))

        cli_level = required_config.get('cli_level')
        if cli_level and cli_level != current_config.get('cli_level'):
            commands.append('logging level cli commands {0}'.format(cli_level))

        audit_level = required_config.get('audit_level')
        if audit_level and audit_level != current_config.get('audit_level'):
            commands.append('logging level audit mgmt {0}'.format(audit_level))

        seconds_enabled = required_config.get('seconds_enabled')
        if seconds_enabled is not None and seconds_enabled != current_config.get('seconds_enabled'):
            commands.append('{0}logging fields seconds enabled'.format('' if seconds_enabled == 'enabled' else 'no '))

        whole_digits = required_config.get('whole_digits')
        if whole_digits and whole_digits != current_config.get('whole_digits'):
            commands.append('logging fields seconds whole-digits {0}'.format(whole_digits))

        fractional_digits = required_config.get('fractional_digits')
        if fractional_digits and fractional_digits != current_config.get('fractional_digits'):
            commands.append('logging fields seconds fractional-digits {0}'.format(fractional_digits))

        ''' list config '''
        monitors = required_config.get('monitor')
        if monitors:
            for monitor in monitors:
                found_facility, found = False, False
                monitor_facility, monitor_level = monitor.get('monitor_facility'), monitor.get('monitor_level')
                for current_monitor in current_config.get('monitor', []):
                    if monitor_facility == current_monitor['monitor_facility']:
                        found_facility = True
                        if is_disabled:
                            break  # no need to iterate more monitors we just need facility to disable
                        if monitor_level == current_monitor['monitor_level']:
                            found = True
                            break
                if monitor_level and not found:
                    commands.append('logging monitor {0} {1}'.format(monitor_facility, monitor_level))
                if found_facility and is_disabled:  # on disable we need just facility to be found
                    commands.append('no logging monitor {0}'.format(monitor_facility))

        override_list = required_config.get('local_override')
        if override_list:
            for override in override_list:
                found_class, found = False, False
                override_class, override_priority = override.get('override_class'), override.get('override_priority')

                for current_override in current_config.get('local_override', []):
                    if override_class == current_override.get('override_class'):
                        found_class = True
                        if is_disabled:
                            break  # no need to iterate more override we just need class to disable
                        if override_priority == current_override.get('override_priority'):
                            found = True
                            break

                if override_priority and not found:
                    commands.append('logging local override class {0} priority {1}'.format(override_class, override_priority))
                if found_class and is_disabled:  # on disable we need just class to be found
                    commands.append('no logging local override class {0}'.format(override_class))

        self._commands = commands


def main():
    """ main entry point for module execution
    """
    OnyxSyslogModule.main()


if __name__ == '__main__':
    main()
