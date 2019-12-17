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
module: onyx_snmp_users
version_added: "2.10"
author: "Sara Touqan (@sarato)"
short_description: Configures SNMP User parameters
description:
  - This module provides declarative management of SNMP Users protocol params
    on Mellanox ONYX network devices.
options:
  users:
    type: list
    description:
      - List of snmp users
    suboptions:
      name:
        description:
          - Specifies the name of the user.
        required: true
        type: str
      enabled:
        description:
          - Enables/Disables SNMP v3 access for the user.
        type: bool
      set_access_enabled:
        description:
          - Enables/Disables SNMP SET requests for the user.
        type: bool
      require_privacy:
        description:
             - Enables/Disables the Require privacy (encryption) for requests from this user
        type: bool
      auth_type:
        description:
             -  Configures the hash type used to configure SNMP v3 security parameters.
        choices: ['md5', 'sha', 'sha224', 'sha256', 'sha384', 'sha512']
        type: str
      auth_password:
        description:
             - The password needed to configure the hash type.
        type: str
      capability_level:
        description:
             - Sets capability level for SET requests.
        choices: ['admin','monitor','unpriv','v_admin']
        type: str
"""

EXAMPLES = """
- name: enables snmp user
  onyx_snmp_users:
    users:
       - name: sara
         enabled: true

- name: enables snmp set requests
  onyx_snmp_users:
    users:
       - name: sara
         set_access_enabled: yes

- name: enables user require privacy
  onyx_snmp_users:
    users:
       - name: sara
         require_privacy: true

- name: configures user hash type
  onyx_snmp_users:
    users:
       - auth_type: md5
         auth_password: 1297sara1234sara

- name: configures user capability_level
  onyx_snmp_users:
    users:
        - name: sara
          capability_level: admin
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - snmp-server user <user_name> v3 enable
    - no snmp-server user <user_name> v3 enable
    - snmp-server user <user_name> v3 enable sets
    - no snmp-server user <user_name> v3 enable sets
    - snmp-server user <user_name> v3 require-privacy
    - no snmp-server user <user_name> v3 require-privacy
    - snmp-server user <user_name> v3 capability <capability_level>
    - snmp-server user <user_name> v3 auth <hash_type> <password>
"""

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxSNMPUsersModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        user_spec = dict(name=dict(required=True),
                         enabled=dict(type='bool'),
                         set_access_enabled=dict(type='bool'),
                         require_privacy=dict(type='bool'),
                         auth_type=dict(type='str', choices=['md5', 'sha', 'sha224', 'sha256', 'sha384', 'sha512']),
                         auth_password=dict(type='str'),
                         capability_level=dict(type='str', choices=['admin', 'monitor', 'unpriv', 'v_admin']),
                         )
        element_spec = dict(
            users=dict(type='list', elements='dict', options=user_spec),
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

    def _set_snmp_config(self, users_config):
        if users_config[0]:
            if users_config[0].get('Lines'):
                return
        current_users = []
        count = 0
        enabled = True
        set_access_enabled = True
        require_privacy = True
        auth_type = ''
        capability_level = ''
        name = ''
        all_users_names = []
        for user in users_config:
            user_dict = {}
            entry_dict = {}
            for entry in user:
                name = entry.split()[2]
                if user.get(entry):
                    if user.get(entry)[0]:
                        enabled = user.get(entry)[0].get('Enabled overall')
                        if enabled == 'no':
                            enabled = False
                        else:
                            enabled = True
                        set_access_enabled = user.get(entry)[1].get('SET access')[0].get('Enabled')
                        if set_access_enabled == 'no':
                            set_access_enabled = False
                        else:
                            set_access_enabled = True
                        require_privacy = user.get(entry)[0].get('Require privacy')
                        if require_privacy == 'yes':
                            require_privacy = True
                        else:
                            require_privacy = False
                        capability_level = user.get(entry)[1].get('SET access')[0].get('Capability level')
                        auth_type = user.get(entry)[0].get('Authentication type')
                        user_dict['enabled'] = enabled
                        user_dict['set_access_enabled'] = set_access_enabled
                        user_dict['auth_type'] = auth_type
                        user_dict['capability_level'] = capability_level
                        user_dict['require_privacy'] = require_privacy
                        entry_dict[name] = user_dict
                        all_users_names.append(name)
            current_users.append(entry_dict)
        self._current_config['users'] = current_users
        self._current_config['current_names'] = all_users_names

    def _show_users(self):
        cmd = "show snmp user"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        users_config = self._show_users()
        if users_config:
            self._set_snmp_config(users_config)

    def generate_commands(self):
        req_uers = self._required_config.get("users")
        current_users = self._current_config.get("users")
        current_names = self._current_config.get("current_names")
        if req_uers:
            for user in req_uers:
                user_id = user.get('name')
                if user_id:
                    if current_names and (user_id in current_names):
                        for user_entry in current_users:
                            for user_name in user_entry:
                                if user_name == user_id:
                                    user_state = user.get("enabled")
                                    user_entry_name = user_entry.get(user_name)
                                    if user_state is not None:
                                        if user_state != user_entry_name.get("enabled"):
                                            if user_state is True:
                                                self._commands.append('snmp-server user {0} v3 enable' .format(user_id))
                                            else:
                                                self._commands.append('no snmp-server user {0} v3 enable' .format(user_id))
                                    set_state = user.get("set_access_enabled")
                                    if set_state is not None:
                                        if set_state != user_entry_name.get("set_access_enabled"):
                                            if set_state is True:
                                                self._commands.append('snmp-server user {0} v3 enable sets' .format(user_id))
                                            else:
                                                self._commands.append('no snmp-server user {0} v3 enable sets' .format(user_id))
                                    auth_type = user.get("auth_type")
                                    if auth_type is not None:
                                        if user.get("auth_password") is not None:
                                            if auth_type != user_entry_name.get("auth_type"):
                                                self._commands.append('snmp-server user {0} v3 auth {1} {2}'
                                                                      .format(user_id, user.get('auth_type'), user.get('auth_password')))
                                    cap_level = user.get("capability_level")
                                    if cap_level is not None:
                                        if cap_level != user_entry_name.get("capability_level"):
                                            self._commands.append('snmp-server user {0} v3 capability {1}'
                                                                  .format(user_id, user.get('capability_level')))
                                    req_priv = user.get("require_privacy")
                                    if req_priv is not None:
                                        if req_priv != user_entry_name.get("require_privacy"):
                                            if req_priv is True:
                                                self._commands.append('snmp-server user {0} v3 require-privacy' .format(user_id))
                                            else:
                                                self._commands.append('no snmp-server user {0} v3 require-privacy' .format(user_id))

                    else:
                        user_state = user.get("enabled")
                        if user_state is not None:
                            if user_state is True:
                                self._commands.append('snmp-server user {0} v3 enable' .format(user_id))
                            else:
                                self._commands.append('no snmp-server user {0} v3 enable' .format(user_id))
                        set_state = user.get("set_access_enabled")
                        if set_state is not None:
                            if set_state is True:
                                self._commands.append('snmp-server user {0} v3 enable sets' .format(user_id))
                            else:
                                self._commands.append('no snmp-server user {0} v3 enable sets' .format(user_id))
                        if user.get("capability_level") is not None:
                            self._commands.append('snmp-server user {0} v3 capability {1}' .format(user_id, user.get('capability_level')))
                        req_priv = user.get("require_privacy")
                        if req_priv is not None:
                            if req_priv is True:
                                self._commands.append('snmp-server user {0} v3 require-privacy' .format(user_id))
                            else:
                                self._commands.append('no snmp-server user {0} v3 require-privacy' .format(user_id))


def main():
    """ main entry point for module execution
    """
    OnyxSNMPUsersModule.main()


if __name__ == '__main__':
    main()
