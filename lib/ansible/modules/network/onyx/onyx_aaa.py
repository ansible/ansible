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
module: onyx_aaa
version_added: "2.10"
author: "Sara Touqan (@sarato)"
short_description: Configures AAA parameters
description:
  - This module provides declarative management of AAA protocol params
    on Mellanox ONYX network devices.
options:
  tacacs_accounting_enabled:
    description:
      - Configures accounting settings.
    type: bool
  auth_default_user:
    description:
      - Sets local user default mapping.
    type: str
    choices: ['admin', 'monitor']
  auth_order:
    description:
      - Sets the order on how to handle remote to local user mappings.
    type: str
    choices: ['local-only', 'remote-first', 'remote-only']
  auth_fallback_enabled:
    description:
      - Enables/Disables fallback server-err option.
    type: bool
"""

EXAMPLES = """
- name: configures aaa
  onyx_aaa:
    tacacs_accounting_enabled: yes
    auth_default_user: monitor
    auth_order: local-only
    auth_fallback_enabled: false
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - aaa accounting changes default stop-only tacacs+
    - no aaa accounting changes default stop-only tacacs+
    - aaa authorization map default-user <user>
    - aaa authorization map order <order>
    - aaa authorization map fallback server-err
    - no aaa authorization map fallback server-err
"""

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxAAAModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            tacacs_accounting_enabled=dict(type='bool'),
            auth_default_user=dict(type='str', choices=['admin', 'monitor']),
            auth_order=dict(type='str', choices=['local-only', 'remote-first', 'remote-only']),
            auth_fallback_enabled=dict(type='bool')
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def _set_aaa_config(self, all_aaa_config):
        aaa_config = all_aaa_config[0]
        self._current_config['auth_default_user'] = aaa_config.get("Default User")
        self._current_config['auth_order'] = aaa_config.get("Map Order")
        auth_fallback_enabled = aaa_config.get("Fallback on server-err")
        if auth_fallback_enabled == "yes":
            self._current_config['auth_fallback_enabled'] = True
        else:
            self._current_config['auth_fallback_enabled'] = False
        aaa_config_2 = all_aaa_config[2]
        accounting_message = aaa_config_2.get("message")
        if accounting_message == "No accounting methods configured.":
            self._current_config['tacacs_accounting_enabled'] = False
        else:
            self._current_config['tacacs_accounting_enabled'] = True

    def _show_aaa_config(self):
        cmd = "show aaa"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        aaa_config = self._show_aaa_config()
        if aaa_config:
            self._set_aaa_config(aaa_config)

    def generate_commands(self):
        tacacs_accounting_enabled = self._required_config.get("tacacs_accounting_enabled")
        if tacacs_accounting_enabled is not None:
            current_accounting_enabled = self._current_config.get("tacacs_accounting_enabled")
            if current_accounting_enabled != tacacs_accounting_enabled:
                if tacacs_accounting_enabled is True:
                    self._commands.append('aaa accounting changes default stop-only tacacs+')
                else:
                    self._commands.append('no aaa accounting changes default stop-only tacacs+')

        auth_default_user = self._required_config.get("auth_default_user")
        if auth_default_user is not None:
            current_user = self._current_config.get("auth_default_user")
            if current_user != auth_default_user:
                self._commands.append('aaa authorization map default-user {0}' .format(auth_default_user))

        auth_order = self._required_config.get("auth_order")
        if auth_order is not None:
            current_order = self._current_config.get("auth_order")
            if current_order != auth_order:
                self._commands.append('aaa authorization map order {0}' .format(auth_order))

        auth_fallback_enabled = self._required_config.get("auth_fallback_enabled")
        if auth_fallback_enabled is not None:
            current_fallback = self._current_config.get("auth_fallback_enabled")
            if current_fallback != auth_fallback_enabled:
                if auth_fallback_enabled is True:
                    self._commands.append('aaa authorization map fallback server-err')
                else:
                    self._commands.append('no aaa authorization map fallback server-err')


def main():
    """ main entry point for module execution
    """
    OnyxAAAModule.main()


if __name__ == '__main__':
    main()
