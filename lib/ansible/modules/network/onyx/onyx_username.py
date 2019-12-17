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
module: onyx_username
version_added: "2.10"
author: "Anas Shami (@anass)"
short_description: Configure username module
description:
  - This module provides declarative management of users/roles
    on Mellanox ONYX network devices.
notes:
options:
    username:
        description:
            - Create/Edit user using username
        type: str
        required: True
    full_name:
        description:
            - Set the full name of this user
        type: str
    nopassword:
        description:
            - Clear password for such user
        type: bool
        default: False
    password:
        description:
            - Set password fot such user
        type: str
    encrypted_password:
        description:
            - Decide the type of setted password (plain text or encrypted)
        type: bool
        default: False
    capability:
        description:
            - Grant capability to this user account
        type: str
        choices: ['monitor', 'unpriv', 'v_admin', 'admin']
    reset_capability:
        description:
            - Reset capability to this user account
        type: bool
        default: False
    disconnected:
        description:
            - Disconnect all sessions of this user
        type: bool
        default: False
    disabled:
        description:
            - Disable means of logging into this account
        type: str
        choices: ['none', 'login', 'password', 'all']
    state:
        description:
            - Set state of the given account
        default: present
        type: str
        choices: ['present', 'absent']
"""

EXAMPLES = """
- name: create new user
  onyx_username:
      username: anass

- name: set the user full-name
  onyx_username:
      username: anass
      full_name: anasshami

- name: set the user encrypted password
  onyx_username:
      username: anass
      password: 12345
      encrypted_password: True

- name: set the user capability
  onyx_username:
      username: anass
      capability: monitor

- name: reset the user capability
  onyx_username:
      username: anass
      reset_capability: True

- name: remove the user configuration
  onyx_username:
      username: anass
      state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - username *
    - username * password *
    - username * nopassword
    - username * disable login
    - username * capability admin
    - no username *
    - no username * disable

"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule, show_cmd


class OnyxUsernameModule(BaseOnyxModule):
    ACCOUNT_STATE = {
        'Account locked out': dict(disabled='all'),
        'No password required for login': dict(nopassword=True),
        'Local password login disabled': dict(disabled='password'),
        'Account disabled': dict(disabled='all')
    }
    ENCRYPTED_ID = 7

    def init_module(self):
        """
        module initialization
        """
        element_spec = dict()

        argument_spec = dict(state=dict(choices=['absent', 'present'], default='present'),
                             username=dict(type='str', required=True),
                             disabled=dict(choices=['none', 'login', 'password', 'all']),
                             capability=dict(choices=['monitor', 'unpriv', 'v_admin', 'admin']),
                             nopassword=dict(type='bool', default=False),
                             password=dict(type='str', no_log=True),
                             encrypted_password=dict(type='bool', default=False),
                             reset_capability=dict(type="bool", default=False),
                             disconnected=dict(type='bool', default=False),
                             full_name=dict(type='str'))
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
            mutually_exclusive=[['password', 'nopassword']])

    def get_required_config(self):
        self._required_config = dict()
        module_params = self._module.params
        params = {}
        ''' Requred/Default fields '''
        params['username'] = module_params.get('username')
        params['state'] = module_params.get('state')
        params['encrypted_password'] = module_params.get('encrypted_password')
        params['reset_capability'] = module_params.get('reset_capability')
        ''' Other fields '''
        for key, value in module_params.items():
            if value is not None:
                params[key] = value
        self.validate_param_values(params)
        self._required_config = params

    def _get_username_config(self):
        return show_cmd(self._module, "show usernames", json_fmt=True, fail_on_error=False)

    def _set_current_config(self, users_config):
        '''
        users_config ex:
        {
            admin": [
                    {
                        "CAPABILITY": "admin",
                        "ACCOUNT STATUS": "No password required for login",
                        "FULL NAME": "System Administrator"
                    }
            ],
        }
        '''
        if not users_config:
            return
        current_config = self._current_config
        for username, config in users_config.items():
            config_json = config[0]
            current_config[username] = current_config.get(username, {})
            account_status = config_json.get('ACCOUNT STATUS')
            status_value = self.ACCOUNT_STATE.get(account_status)

            if status_value is not None:
                #  None for enabled account with password account "Password set (SHA512 | MD5)" so we won't change any attribute here.
                current_config[username].update(status_value)
            current_config[username].update({
                'capability': config_json.get('CAPABILITY'),
                'full_name': config_json.get('FULL NAME')
            })

    def load_current_config(self):
        self._current_config = dict()
        users_config = self._get_username_config()
        self._set_current_config(users_config)

    def generate_commands(self):
        current_config, required_config = self._current_config, self._required_config
        username = required_config.get('username')
        current_user = current_config.get(username)
        if current_user is not None:
            '''created account we just need to edit his attributes'''
            full_name = required_config.get('full_name')
            if full_name is not None and current_user.get('full_name') != full_name:
                self._commands.append("username {0} full-name {1}".format(username, full_name))

            disabled = required_config.get('disabled')
            if disabled is not None and current_user.get('disabled') != disabled:
                if disabled == 'none':
                    self._commands.append("no username {0} disable".format(username))
                elif disabled == 'all':
                    self._commands.append("username {0} disable".format(username))
                else:
                    self._commands.append("username {0} disable {1}".format(username, disabled))

            state = required_config.get('state')
            if state == 'absent':  # this will remove the user
                self._commands.append("no username {0}".format(username))

            capability = required_config.get('capability')
            if capability is not None and current_user.get('capability') != capability:
                self._commands.append("username {0} capability {1}".format(username, capability))

            reset_capability = required_config.get('reset_capability')
            if reset_capability:
                self._commands.append("no username {0} capability".format(username))

            password = required_config.get('password')
            if password is not None:
                encrypted = required_config.get('encrypted_password')
                if encrypted:
                    self._commands.append("username {0} password {1} {2}".format(username, self.ENCRYPTED_ID, password))
                else:
                    self._commands.append("username {0} password {1}".format(username, password))

            nopassword = required_config.get('nopassword')
            if nopassword and nopassword != current_user.get('nopassword', False):
                self._commands.append("username {0} nopassword".format(username))

            disconnected = required_config.get('disconnected')
            if disconnected:
                self._commands.append("username {0} disconnect".format(username))
        else:
            '''create new account if we have valid inforamtion, just check for username, capability, full_name, password'''

            capability = required_config.get('capability')
            password = required_config.get('password')
            full_name = required_config.get('full_name')
            if capability is not None or password is not None or full_name is not None:
                if capability is not None:
                    self._commands.append("username {0} capability {1}".format(username, capability))

                if password is not None:
                    encrypted = required_config.get('encrypted_password')
                    if encrypted:
                        self._commands.append("username {0} password {1} {2} ".format(username, self.ENCRYPTED_ID, password))
                    else:
                        self._commands.append("username {0} password {1}".format(username, password))

                if full_name is not None:
                    self._commands.append("username {0} full-name {1}".format(username, full_name))

            else:
                self._commands.append("username {0}".format(username))


def main():
    """ main entry point for module execution
    """
    OnyxUsernameModule.main()


if __name__ == '__main__':
    main()
