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
        description: Name of wjh group
        required: true
        choice: ['all', 'forwarding', 'acl']
    enabled:
        description: wjh group status
        type: bool
    auto_export:
        description: wjh group auto export pcap file status
        type: bool
    export_group:
        description: wjh group auto export group
        choice: ['all', 'forwarding', 'acl']
    clear_group:
        description: clear pcap file by group 
        choice: ['all', 'user', 'auto-export']
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
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import conditional
from ansible.module_utils.network.common.utils import remove_default_spec

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule, show_cmd
from ansible.module_utils.network.onyx.onyx import get_interfaces_config


class OnyxWJHModule(BaseOnyxModule):
    WJH_DISABLED_REGX = re.compile(r'^no what-just-happened ([a-z]+) enable.*')
    WJH_DISABLED_AUTO_EXPORT_REGX = re.compile(r'^no what-just-happened auto-export ([a-z]+) enable.*')


    WJH_CMD_FMT = '{}what-just-happened {} enable'
    WJH_EXPORT_CMD_FMT = '{}what-just-happened auto-export {} enable'
    WJH_CLEAR_CMD_FMT = 'clear what-just-happened pcap-files {}'

    WJH_GROUPS   = ['all', 'forwarding', 'acl']
    CLEAR_GROUPS = ['all', 'user', 'auto-export']
    def init_module(self):
        """ module initialization
        """
        element_spec = dict(
                        group=dict(choices = self.WJH_GROUPS),
                        enabled = dict(type = 'bool'),
                        auto_export = dict(type = 'bool'),
                        export_group = dict(choices = self.WJH_GROUPS),
                        clear_group = dict(choices = self.CLEAR_GROUPS)
                        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        self._required_config = dict()
        module_params = self._module.params
        group = module_params.get('group')
        export_group = module_params.get('export_group')
        clear_group = module_params.get('clear_group')

        auto_export = module_params.get('auto_export', True)
        enabled = module_params.get('enabled', True)

        params = dict()
        if group:
            params.update({
                'group': group,
                'enabled': enabled
            })

        if export_group:
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
        return show_cmd(self._module, "show running-config | include .*what-just-happened.*")
        
    def _set_current_config(self, config):
        if not config:
            return 
        current_config = self._current_config #alias 
        for line in config:
            match = self.WJH_DISABLED_REGX.match(line)
            if match: 
                #wjh is disabled
                group = match.group(1)
                current_config[group] = False 

            match = self.WJH_DISABLED_AUTO_EXPORT_REGX.match(line)
            if match:
                #wjh auto export is disabled
                export_group = match.group(1) + '_export'
                current_config[export_group] = False 
    
    '''
        show running config will contains [no wjh * group enable] if disabled - default config is enabled 
    '''
    def load_current_config(self):
        self._current_config = dict()
        config_lines = self._get_wjh_config().get('Lines', None)
        
        if config_lines:
            self._set_current_config(config_lines)

    '''
        wjh is enabled "by default"
        when wjh disable we  will find no wjh commands in running config 
    ''' 
    def generate_commands(self):
        current_config, required_config = self._current_config, self._required_config
        for key, value in required_config.items():
            if key == 'group': #configration for wjh drop resean group
                if value == 'all':
                    current_enabled = not any([(group in current_config) for group in self.WJH_GROUPS]) # no disabled group
                else:
                    current_enabled = current_config[value] if value in current_config else True # if no current-value its enabled
                
                if(required_config['enabled'] !=  current_enabled):
                    self._commands.append(self.WJH_CMD_FMT.format(
                                                        '' if required_config['enabled'] else 'no ',
                                                        value))

            elif key == 'export_group': #configration for wjh auto-export resean group
                ex_value = value + '_export'

                if value == 'all':
                    current_enabled = not any([(group + '_export') in current_config for group in self.WJH_GROUPS])
                else:
                    current_enabled = current_config[ex_value] if ex_value in current_config else True # if no current its enabled

                if(required_config['auto_export'] !=  current_enabled):
                    self._commands.append(self.WJH_EXPORT_CMD_FMT.format(
                                                        '' if required_config['auto_export'] else 'no ',
                                                        value))

            elif key == 'clear_group':
                #clear pcap files
                self._commands.append(self.WJH_CLEAR_CMD_FMT.format(value))

def main():
    """ main entry point for module execution
    """
    OnyxWJHModule.main()


if __name__ == '__main__':
    main()
