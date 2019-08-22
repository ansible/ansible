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
---
module: onyx_wjh
version_added: "2.9"
author: "Anas Shami (@anass)"
short_description: Configure what-just-happend module
description:
  - This module provides declarative management of wjh
    on Mellanox ONYX network devices.
notes:
options:
    group:
        description:
         - Name of wjh group.
        choices: ['all', 'forwarding', 'acl']
        type: str
    enabled:
        description:
          - wjh group status
        type: bool
    auto_export:
        description:
          - wjh group auto export pcap file status
        type: bool
    export_group:
        description:
          - wjh group auto export group
        choices: ['all', 'forwarding', 'acl']
        type: str
    clear_group:
        description:
          - clear pcap file by group
        choices: ['all', 'user', 'auto-export']
        type: str
"""

EXAMPLES = """
- name: enable wjh
  onyx_wjh:
      group: forwarding
      enabled: True

- name: disable wjh
  onyx_wjh:
      group: forwarding
      enabled: False

- name: enable auto-export
  onyx_wjh:
        auto_export: True
        export_group: forwarding
- name: disable auto-export
  onyx_wjh:
        auto_export: False
        export_group: forwarding
- name: clear pcap file
  onyx_wjh:
        clear_group: auto-export
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - what-just-happend forwarding enable
    - what-just-happend auto-export forwarding enable
    - clear what-just-happend pcap-file user
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule, show_cmd


class OnyxWJHModule(BaseOnyxModule):
    WJH_DISABLED_REGX = re.compile(r'^no what-just-happened ([a-z]+) enable.*')
    WJH_DISABLED_AUTO_EXPORT_REGX = re.compile(r'^no what-just-happened auto-export ([a-z]+) enable.*')

    WJH_CMD_FMT = '{0}what-just-happened {1} enable'
    WJH_EXPORT_CMD_FMT = '{0}what-just-happened auto-export {1} enable'
    WJH_CLEAR_CMD_FMT = 'clear what-just-happened pcap-files {0}'

    WJH_GROUPS = ['all', 'forwarding', 'acl']
    CLEAR_GROUPS = ['all', 'user', 'auto-export']

    def init_module(self):
        """
        module initialization
        """
        element_spec = dict(group=dict(choices=self.WJH_GROUPS),
                            enabled=dict(type='bool'),
                            auto_export=dict(type='bool'),
                            export_group=dict(choices=self.WJH_GROUPS),
                            clear_group=dict(choices=self.CLEAR_GROUPS))

        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_together=[
                ['group', 'enabled'],
                ['auto_export', 'export_group']
            ])

    def get_required_config(self):
        self._required_config = dict()
        module_params = self._module.params
        group = module_params.get('group')
        export_group = module_params.get('export_group')
        clear_group = module_params.get('clear_group')

        params = dict()
        if group:
            enabled = module_params.get('enabled')
            params.update({
                'group': group,
                'enabled': enabled
            })

        if export_group:
            auto_export = module_params.get('auto_export')
            params.update({
                'export_group': export_group,
                'auto_export': auto_export
            })

        if clear_group:
            params.update({
                'clear_group': clear_group
            })

        self.validate_param_values(params)
        self._required_config = params

    def _get_wjh_config(self):
        return show_cmd(self._module, "show running-config | include .*what-just-happened.*", json_fmt=False, fail_on_error=False)

    def _set_current_config(self, config):
        if not config:
            return
        current_config = self._current_config
        lines = config.split('\n')
        for line in lines:
            if line.startswith('#'):
                continue
            match = self.WJH_DISABLED_REGX.match(line)
            if match:
                # wjh is disabled
                group = match.group(1)
                current_config[group] = False

            match = self.WJH_DISABLED_AUTO_EXPORT_REGX.match(line)
            if match:
                # wjh auto export is disabled
                export_group = match.group(1) + '_export'
                current_config[export_group] = False

    '''
        show running config will contains [no wjh * group enable] if disabled - default config is enabled
    '''
    def load_current_config(self):
        self._current_config = dict()
        config_lines = self._get_wjh_config()
        if config_lines:
            self._set_current_config(config_lines)

    def wjh_group_status(self, current_config, group_value, suffix=''):
        current_enabled = False
        if group_value == 'all':
            # no disabled group so all would be false
            current_enabled = not all([
                                      (group + suffix) in current_config for group in self.WJH_GROUPS])
        else:
            # if no current-value its enabled
            current_enabled = current_config[group_value + suffix] if((group_value + suffix) in current_config) else True
        return current_enabled

    '''
        wjh is enabled "by default"
        when wjh disable we  will find no wjh commands in running config
    '''
    def generate_commands(self):
        current_config, required_config = self._current_config, self._required_config
        group = required_config.get('group')
        export_group = required_config.get('export_group')
        clear_group = required_config.get('clear_group')
        if group:
            current_enabled = self.wjh_group_status(current_config, group)
            if(required_config['enabled'] != current_enabled):
                self._commands.append(self.WJH_CMD_FMT
                                      .format(('' if required_config['enabled'] else 'no '), group))
        if export_group:
            current_enabled = self.wjh_group_status(current_config, required_config['export_group'], '_export')
            if(required_config['auto_export'] != current_enabled):
                self._commands.append(self.WJH_EXPORT_CMD_FMT
                                      .format(('' if required_config['auto_export'] else 'no '), export_group))
        if clear_group:
            # clear pcap files
            self._commands.append(self.WJH_CLEAR_CMD_FMT.format(clear_group))


def main():
    """ main entry point for module execution
    """
    OnyxWJHModule.main()


if __name__ == '__main__':
    main()
