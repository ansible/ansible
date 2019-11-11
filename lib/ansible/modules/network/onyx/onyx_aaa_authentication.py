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
module: onyx_aaa_authentication
version_added: "2.10"
author: "Sara Touqan (@sarato)"
short_description: Configures AAA authentication parameters
description:
  - This module provides declarative management of AAA authentication protocol params
    on Mellanox ONYX network devices.
options:
  auth_login_method1:
    description:
      - Configures first auth method to be used in login authentication
    type: str
    choices: ['local', 'ldap', 'radius', 'tacacs+']
  auth_login_method2:
    description:
      - Configures second auth method to be used in login authentication
    type: str
    choices: ['local', 'ldap', 'radius', 'tacacs+']
  auth_login_method3:
    description:
      - Configures third auth method to be used in login authentication
    type: str
    choices: ['local', 'ldap', 'radius', 'tacacs+']
  auth_login_method4:
    description:
      - Configures forth auth method to be used in login authentication
    type: str
    choices: ['local', 'ldap', 'radius', 'tacacs+']
  auth_fail_delay_time:
    description:
      -  Delay for a fixed period of time after every auth failure.
    type: int
  auth_track_enabled:
    description:
      -  Enables/Disables tracking of failed auth attempts.
    type: bool
  track_downcase_enabled:
    description:
      -  Enables/Disables Converting all usernames to lowercase (for authentication failure tracking purposes only).
    type: bool
  reset_for:
    description:
      -  Clears auth history and/or unlock accounts for all users or for a specific user.
    type: str
    choices: ['all', 'user']
  user_name:
    description:
      -  Specifys the username for whom you want to clear the auth history
    type: str
  reset_type:
    description:
      -  Here we have 2 reset types:
         first : no-clear-history which means to unlock <all or specific user> accounts, but do not clear auth history
         second: no-unlock which means to clear auth history for <all or specific user> accounts, but do not unlock them
    type: str
    choices: ['no-clear-history', 'no-unlock']
  admin_no_lockout_enabled:
    description:
      -  when it is enabled it means to never lock the 'admin' account based on auth failures.
    type: bool
  unknown_account_hash_username_enabled:
    description:
      - Enables/Disables protecting unknown usernames by hashing them.
    type: bool
  unknown_account_no_track_enabled:
    description:
      - when it is enabled it means do not track auth failures for unknown usernames.
    type: bool
  lockout_enabled:
    description:
      - Enables/Disables lockout of accounts based on failed auth attempts.
    type: bool
  lock_time:
    description:
      - Temporarily locks account after every auth failure for a fixed period of time.
    type: int
  unlock_time:
    description:
      - Allows auth retry on locked account after a period of time.
    type: int
  max_failure_account:
    description:
      - Sets maximum permitted consecutive auth failures before lockout.
    type: int

"""

EXAMPLES = """
- name: configures aaa authentication login
  onyx_aaa_authentication:
    auth_login_method1: local
    auth_login_method2: ldap
    auth_login_method3: tacacs+
    auth_login_method4: radius
- name: configures aaa authentication fail delay time
  onyx_aaa_authentication:
    auth_fail_delay_time: 55
- name: configures aaa authentication track cmds
  onyx_aaa_authentication:
    auth_track_enabled: True
    track_downcase_enabled: False
- name: reset for all
  onyx_aaa_authentication:
    reset_for: all
    reset_type: no-unlock
- name: reset for user x
  onyx_aaa_authentication:
    reset_for: user
    user_name: x
    reset_type: no-unlock
- name: configures account settings configs.
  onyx_aaa_authentication:
    admin_no_lockout_enabled: yes
    unknown_account_hash_username_enabled: false
    unknown_account_no_track_enabled: true
- name: configures lockout settings
  onyx_aaa_authentication:
    lockout_enabled: yes
    lock_time: 66
    unlock_time: 66
    max_failure_account: 55
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - aaa authentication login default <first_method> <second_method> <third_method> <forth_method>
    - aaa authentication attempts fail-delay <time>
    - aaa authentication attempts track enable
    - no aaa authentication attempts track enable
    - aaa authentication attempts track downcase
    - no aaa authentication attempts track downcase
    - aaa authentication attempts reset user <user_name> <reset_type>
    - aaa authentication attempts reset user <user_name>
    - aaa authentication attempts reset all
    - aaa authentication attempts reset all <reset_type>
    - aaa authentication attempts class-override admin no-lockout
    - no aaa authentication attempts class-override admin no-lockout
    - aaa authentication attempts class-override unknown hash-username
    - no aaa authentication attempts class-override unknown hash-username
    - aaa authentication attempts class-override unknown no-track
    - no aaa authentication attempts class-override unknown no-track
    - aaa authentication attempts lockout enable
    - no aaa authentication attempts lockout enable
    - aaa authentication attempts lockout lock-time <lock_time>
    - aaa authentication attempts lockout unlock-time <unlock_time>
    - aaa authentication attempts lockout max-fail <max_failure_account>
"""

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxAaaAuthenticationModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            auth_login_method1=dict(type='str', choices=['local', 'ldap', 'radius', 'tacacs+']),
            auth_login_method2=dict(type='str', choices=['local', 'ldap', 'radius', 'tacacs+']),
            auth_login_method3=dict(type='str', choices=['local', 'ldap', 'radius', 'tacacs+']),
            auth_login_method4=dict(type='str', choices=['local', 'ldap', 'radius', 'tacacs+']),
            auth_fail_delay_time=dict(type='int'),
            auth_track_enabled=dict(type='bool'),
            track_downcase_enabled=dict(type='bool'),
            reset_for=dict(type='str', choices=['all', 'user']),
            user_name=dict(type='str'),
            reset_type=dict(type='str', choices=['no-clear-history', 'no-unlock']),
            admin_no_lockout_enabled=dict(type='bool'),
            unknown_account_hash_username_enabled=dict(type='bool'),
            unknown_account_no_track_enabled=dict(type='bool'),
            lockout_enabled=dict(type='bool'),
            lock_time=dict(type='int'),
            unlock_time=dict(type='int'),
            max_failure_account=dict(type='int')
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def validate_auth_params(self):
        auth_login_method1 = self._required_config.get("auth_login_method1")
        auth_login_method2 = self._required_config.get("auth_login_method2")
        auth_login_method3 = self._required_config.get("auth_login_method3")
        auth_login_method4 = self._required_config.get("auth_login_method4")
        auth_fail_delay_time = self._required_config.get("auth_fail_delay_time")
        reset_for = self._required_config.get("reset_for")
        user_name = self._required_config.get("user_name")
        if auth_login_method2 is not None:
            if auth_login_method1 is None:
                self._module.fail_json(msg='auth_login_method1 is required when auth_login_method2 is given')
        if auth_login_method3 is not None:
            if ((auth_login_method1 is None) or (auth_login_method2 is None)):
                self._module.fail_json(msg='auth_login_method1 and auth_login_method2 are required when auth_login_method3 is given')
        if auth_login_method4 is not None:
            if ((auth_login_method1 is None) or (auth_login_method2 is None) or (auth_login_method3 is None)):
                self._module.fail_json(msg='auth_login_method1 and auth_login_method2 and auth_login_method3 are required when auth_login_method3 is given')
        if auth_fail_delay_time is not None:
            if (auth_fail_delay_time < 0) or (auth_fail_delay_time > 60):
                self._module.fail_json(msg='auth_fail_delay_time value must be between 0 and 60.')
        if ((reset_for is not None) and (reset_for == 'user')):
            if user_name is None:
                self._module.fail_json(msg='user_name is required when reset_for is entered as a user.')

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)
        self.validate_auth_params()

    def _set_aaa_running_config(self, all_aaa_config):
        curr_config_arr = []
        aaa_config = all_aaa_config.get('Lines')
        if aaa_config is None:
            self._current_config['curr_config_arr'] = curr_config_arr
            return
        for runn_config in aaa_config:
            curr_config_arr.append(runn_config.strip())

        if 'aaa authentication attempts track downcase' in curr_config_arr:
            self._current_config['track_downcase_enabled'] = True
        else:
            self._current_config['track_downcase_enabled'] = False
        self._current_config['curr_config_arr'] = curr_config_arr

    def _set_aaa_config(self, all_aaa_config):
        aaa_config = all_aaa_config[0]
        max_failure_account = all_aaa_config[1].get("Lock account after consecutive auth failures")
        self._current_config['max_failure_account'] = max_failure_account
        if all_aaa_config[1].get("Temp lock after each auth failure (lock time)") != "none":
            lock_time = all_aaa_config[1].get("Temp lock after each auth failure (lock time)").split(" ")[1]
        else:
            lock_time = all_aaa_config[1].get("Temp lock after each auth failure (lock time)")
        self._current_config['lock_time'] = lock_time
        if all_aaa_config[1].get("Allow retry on locked accounts (unlock time)") != "none":
            unlock_time = all_aaa_config[1].get("Allow retry on locked accounts (unlock time)").split(" ")[1]
        else:
            unlock_time = all_aaa_config[1].get("Allow retry on locked accounts (unlock time)")
        self._current_config['unlock_time'] = unlock_time
        if aaa_config.get("Lock accounts based on authentication failures") == "yes":
            self._current_config['lockout_enabled'] = True
        else:
            self._current_config['lockout_enabled'] = False
        unknow_settings = aaa_config.get("Override treatment of unknown usernames").split(',')
        unknow_settings_arr = []
        for item in unknow_settings:
            unknow_settings_arr.append(item.strip())
        if "hash-usernames" in unknow_settings_arr:
            self._current_config['unknown_account_hash_username_enabled'] = True
        else:
            self._current_config['unknown_account_hash_username_enabled'] = False
        if "no-track" in unknow_settings_arr:
            self._current_config['unknown_account_no_track_enabled'] = True
        else:
            self._current_config['unknown_account_no_track_enabled'] = False
        if aaa_config.get("Override treatment of 'admin' user") == 'no-lockout':
            self._current_config['admin_no_lockout_enabled'] = True
        else:
            self._current_config['admin_no_lockout_enabled'] = False
        if aaa_config.get('Delay after each auth failure (fail delay)') !="none":
            self._current_config['auth_fail_delay_time'] = aaa_config.get('Delay after each auth failure (fail delay)').split(' ')[1]
        else:
            self._current_config['auth_fail_delay_time'] = aaa_config.get('Delay after each auth failure (fail delay)')
        if aaa_config.get('Track authentication failures') == 'yes':
            self._current_config['auth_track_enabled'] = True
        else:
            self._current_config['auth_track_enabled'] = False

    def _show_aaa_auth_config(self):
        show_cmds = []
        cmd = "show running-config | include aaa"
        show_cmds.append(show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False))
        cmd = "show aaa authentication attempts configured"
        show_cmds.append(show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False))
        return show_cmds

    def load_current_config(self):
        self._current_config = dict()
        aaa_config = self._show_aaa_auth_config()
        if aaa_config:
            if aaa_config[0] is not None:
                self._set_aaa_running_config(aaa_config[0])
            if aaa_config[1] is not None:
                self._set_aaa_config(aaa_config[1])
        self.validate_auth_params()

    def generate_commands(self):
        curr_config_arr = self._current_config.get("curr_config_arr")
        auth_login_method1 = self._required_config.get("auth_login_method1")
        auth_login_method2 = self._required_config.get("auth_login_method2")
        auth_login_method3 = self._required_config.get("auth_login_method3")
        auth_login_method4 = self._required_config.get("auth_login_method4")
        auth_fail_delay_time = self._required_config.get("auth_fail_delay_time")
        auth_track_enabled = self._required_config.get("auth_track_enabled")
        track_downcase_enabled = self._required_config.get("track_downcase_enabled")
        reset_for = self._required_config.get("reset_for")
        reset_type = self._required_config.get("reset_type")
        user_name = self._required_config.get("user_name")
        curr_track_enabled = self._current_config.get("auth_track_enabled")
        curr_track_downcase = self._current_config.get("track_downcase_enabled")
        admin_no_lockout_enabled = self._required_config.get("admin_no_lockout_enabled")
        curr_admin_no_lockout = self._current_config.get("admin_no_lockout_enabled")
        unknown_account_hash_username_enabled = self._required_config.get("unknown_account_hash_username_enabled")
        curr_unknown_account_hash_username = self._current_config.get("unknown_account_hash_username_enabled")
        unknown_account_no_track_enabled = self._required_config.get("unknown_account_no_track_enabled")
        curr_unknown_account_no_track = self._current_config.get("unknown_account_no_track_enabled")
        lockout_enabled = self._required_config.get("lockout_enabled")
        curr_lockout = self._current_config.get("lockout_enabled")
        lock_time = self._required_config.get("lock_time")
        curr_lock_time = self._current_config.get("lock_time")
        unlock_time = self._required_config.get("unlock_time")
        curr_unlock_time = self._current_config.get("unlock_time")
        max_failure_account = self._required_config.get("max_failure_account")
        curr_max_failure = self._current_config.get("max_failure_account")

        if curr_config_arr is not None:
            if auth_login_method4 is not None:
                if ('aaa authentication login default {0} {1} {2} {3}' .format(auth_login_method1, auth_login_method2,
                                                                               auth_login_method3, auth_login_method4)) not in curr_config_arr:
                    self._commands.append('aaa authentication login default {0} {1} {2} {3}'
                                          .format(auth_login_method1, auth_login_method2, auth_login_method3, auth_login_method4))
            elif auth_login_method3 is not None:
                if ('aaa authentication login default {0} {1} {2}' .format(auth_login_method1, auth_login_method2, auth_login_method3)) not in curr_config_arr:
                    self._commands.append('aaa authentication login default {0} {1} {2}' .format(auth_login_method1, auth_login_method2, auth_login_method3))
            elif auth_login_method2 is not None:
                if ('aaa authentication login default {0} {1}' .format(auth_login_method1, auth_login_method2)) not in curr_config_arr:
                    self._commands.append('aaa authentication login default {0} {1}' .format(auth_login_method1, auth_login_method2))
            elif auth_login_method1 is not None:
                if ('aaa authentication login default {0}' .format(auth_login_method1)) not in curr_config_arr:
                    self._commands.append('aaa authentication login default {0}' .format(auth_login_method1))
        else:
            if auth_login_method4 is not None:
                self._commands.append('aaa authentication login default {0} {1} {2} {3}'
                                      .format(auth_login_method1, auth_login_method2, auth_login_method3, auth_login_method4))
            elif auth_login_method3 is not None:
                self._commands.append('aaa authentication login default {0} {1} {2}' .format(auth_login_method1, auth_login_method2, auth_login_method3))
            elif auth_login_method2 is not None:
                self._commands.append('aaa authentication login default {0} {1}' .format(auth_login_method1, auth_login_method2))
            elif auth_login_method1 is not None:
                self._commands.append('aaa authentication login default {0}' .format(auth_login_method1))

        if auth_fail_delay_time is not None:
            current_delay = self._current_config.get("auth_fail_delay_time")
            if current_delay != "none":
                if auth_fail_delay_time != int(current_delay):
                    self._commands.append('aaa authentication attempts fail-delay {0}' .format(auth_fail_delay_time))
            else:
                self._commands.append('aaa authentication attempts fail-delay {0}' .format(auth_fail_delay_time))

        if auth_track_enabled is not None:
            if auth_track_enabled != curr_track_enabled:
                if auth_track_enabled is True:
                    self._commands.append('aaa authentication attempts track enable')
                else:
                    self._commands.append('no aaa authentication attempts track enable')

        if track_downcase_enabled is not None:
            if curr_track_downcase != track_downcase_enabled:
                if track_downcase_enabled is True:
                    self._commands.append('aaa authentication attempts track downcase')
                else:
                    self._commands.append('no aaa authentication attempts track downcase')

        if reset_for is not None:
            if reset_for == 'user':
                if reset_type is not None:
                    self._commands.append('aaa authentication attempts reset user {0} {1}' .format(user_name, reset_type))
                else:
                    self._commands.append('aaa authentication attempts reset user {0}' .format(user_name))
            else:
                if reset_type is not None:
                    self._commands.append('aaa authentication attempts reset all {0}' .format(reset_type))
                else:
                    self._commands.append('aaa authentication attempts reset all')

        if admin_no_lockout_enabled is not None:
            if admin_no_lockout_enabled != curr_admin_no_lockout:
                if admin_no_lockout_enabled is True:
                    self._commands.append('aaa authentication attempts class-override admin no-lockout')
                else:
                    self._commands.append('no aaa authentication attempts class-override admin no-lockout')

        if unknown_account_hash_username_enabled is not None:
            if unknown_account_hash_username_enabled != curr_unknown_account_hash_username:
                if unknown_account_hash_username_enabled is True:
                    self._commands.append('aaa authentication attempts class-override unknown hash-username')
                else:
                    self._commands.append('no aaa authentication attempts class-override unknown hash-username')

        if unknown_account_no_track_enabled is not None:
            if unknown_account_no_track_enabled != curr_unknown_account_no_track:
                if unknown_account_no_track_enabled is True:
                    self._commands.append('aaa authentication attempts class-override unknown no-track')
                else:
                    self._commands.append('no aaa authentication attempts class-override unknown no-track')

        if lockout_enabled is not None:
            if lockout_enabled != curr_lockout:
                if lockout_enabled is True:
                    self._commands.append('aaa authentication attempts lockout enable')
                else:
                    self._commands.append('no aaa authentication attempts lockout enable')

        if lock_time is not None:
            if curr_lock_time != "none":
                if  lock_time != int(curr_lock_time):
                    self._commands.append('aaa authentication attempts lockout lock-time {0}' .format(lock_time))
            else:
                self._commands.append('aaa authentication attempts lockout lock-time {0}' .format(lock_time))

        if unlock_time is not None:
            if curr_unlock_time != "none":
                if unlock_time != int(curr_unlock_time):
                    self._commands.append('aaa authentication attempts lockout unlock-time {0}' .format(unlock_time))
            else:
                self._commands.append('aaa authentication attempts lockout unlock-time {0}' .format(unlock_time))

        if max_failure_account is not None:
            if curr_max_failure != "none":
                if max_failure_account != int(curr_max_failure):
                    self._commands.append('aaa authentication attempts lockout max-fail {0}' .format(max_failure_account))
            else:
                self._commands.append('aaa authentication attempts lockout max-fail {0}' .format(max_failure_account))


def main():
    """ main entry point for module execution
    """
    OnyxAaaAuthenticationModule.main()


if __name__ == '__main__':
    main()
