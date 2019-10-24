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
module: onyx_ntp
version_added: "2.10"
author: "Sara-Touqan (@sarato)"
short_description: Manage NTP general configurations and ntp keys configurations on Mellanox ONYX network devices
description:
  - This module provides declarative management of NTP & NTP Keys
    on Mellanox ONYX network devices.
options:
  state:
    description:
      - State of the NTP configuration.
    choices: ['enabled', 'disabled']
    type: str
  authenticate_state:
    description:
      - State of the NTP authentication configuration.
    choices: ['enabled', 'disabled']
    type: str
  ntp_authentication_keys:
    type: list
    description:
      - List of ntp authentication keys
    suboptions:
      auth_key_id:
        description:
          - Configures ntp key-id, range 1-65534
        required: true
        type: int
      auth_key_encrypt_type:
        description:
          - encryption type used to configure ntp authentication key.
        required: true
        choices: ['md5', 'sha1']
        type: str
      auth_key_password:
        description:
          - password used for ntp authentication key.
        required: true
        type: str
      auth_key_state:
         description:
             - Used to decide if you want to delete given ntp key or not
         choices: ['present', 'absent']
         type: str
  trusted_keys:
    type: list
    description:
      - List of ntp trusted keys
"""

EXAMPLES = """
- name: configure NTP
  onyx_ntp:
    state: enabled
    authenticate_state: enabled
    ntp_authentication_keys:
            - auth_key_id: 1
              auth_key_encrypt_type: md5
              auth_key_password: 12345
              auth_key_state: absent
    trusted_keys: 1,2,3
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - ntp enable
    - ntp disable
    - ntp authenticate
    - no ntp authenticate
    - ntp authentication-key 1 md5 12345
    - no ntp authentication-key 1
    - ntp trusted-key 1,2,3
"""


from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxNTPModule(BaseOnyxModule):

    def init_module(self):
        """ module initialization
        """
        ntp_authentication_key_spec = dict(auth_key_id=dict(type='int', required=True),
                                           auth_key_encrypt_type=dict(required=True, choices=['md5', 'sha1']),
                                           auth_key_password=dict(required=True),
                                           auth_key_state=dict(choices=['present', 'absent']))
        element_spec = dict(
            state=dict(choices=['enabled', 'disabled']),
            authenticate_state=dict(choices=['enabled', 'disabled']),
            ntp_authentication_keys=dict(type='list', elements='dict', options=ntp_authentication_key_spec),
            trusted_keys=dict(type='list', elements='int')
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def _validate_key_id(self):
        keys_id_list = self._required_config.get("ntp_authentication_keys")
        if keys_id_list:
            for key_item in keys_id_list:
                key_id = key_item.get("auth_key_id")
                if (key_id < 1) or (key_id > 65534):
                    self._module.fail_json(
                        msg='Invalid Key value, value should be in the range 1-65534')

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)
        self._validate_key_id()

    def _show_ntp_config(self):
        show_cmds = []
        cmd = "show ntp"
        show_cmds.append(show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False))
        cmd = "show ntp keys"
        show_cmds.append(show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False))
        return show_cmds

    def _set_ntp_keys_config(self, ntp_config):
        if not ntp_config:
            return
        for req_ntp_auth_key in ntp_config:
            ecryption_type = req_ntp_auth_key.get("Encryption Type")
            self._current_config[req_ntp_auth_key.get("header")] = ecryption_type

    def _set_ntp_config(self, ntp_config):
        ntp_config = ntp_config[0]
        if not ntp_config:
            return
        self._current_config['state'] = ntp_config.get("NTP is administratively")
        self._current_config['authenticate_state'] = ntp_config.get("NTP Authentication administratively")

    def load_current_config(self):
        self._current_config = dict()
        ntp_config = self._show_ntp_config()
        if ntp_config:
            if ntp_config[0]:
                self._set_ntp_config(ntp_config[0])
            if ntp_config[1]:
                self._set_ntp_keys_config(ntp_config[1])

    def generate_commands(self):
        current_state = self._current_config.get("state")
        state = self._required_config.get("state")
        if state is None:
            state = current_state
        if state is not None:
            if current_state != state:
                if state == 'enabled':
                    self._commands.append('ntp enable')
                else:
                    self._commands.append('no ntp enable')
        authenticate_state = self._required_config.get("authenticate_state")
        if authenticate_state:
            current_authenticate_state = self._current_config.get("authenticate_state")
            if authenticate_state is not None:
                if current_authenticate_state != authenticate_state:
                    if authenticate_state == 'enabled':
                        self._commands.append('ntp authenticate')
                    else:
                        self._commands.append('no ntp authenticate')
        req_ntp_auth_keys = self._required_config.get('ntp_authentication_keys')
        if req_ntp_auth_keys:
            if req_ntp_auth_keys is not None:
                for req_ntp_auth_key in req_ntp_auth_keys:
                    req_key_id = req_ntp_auth_key.get('auth_key_id')
                    req_key = 'NTP Key ' + str(req_key_id)
                    current_req_key = self._current_config.get(req_key)
                    auth_key_state = req_ntp_auth_key.get('auth_key_state')
                    req_encrypt_type = req_ntp_auth_key.get('auth_key_encrypt_type')
                    req_password = req_ntp_auth_key.get('auth_key_password')
                    if current_req_key:
                        if req_encrypt_type == current_req_key:
                            if auth_key_state:
                                if auth_key_state == 'absent':
                                    self._commands.append('no ntp authentication-key {0}' .format(req_key_id))
                            else:
                                continue
                        else:
                            if auth_key_state:
                                if auth_key_state == 'present':
                                    self._commands.append('ntp authentication-key {0} {1} {2}'
                                                          .format(req_key_id,
                                                                  req_encrypt_type,
                                                                  req_password))
                            else:
                                self._commands.append('ntp authentication-key {0} {1} {2}'
                                                      .format(req_key_id,
                                                              req_encrypt_type,
                                                              req_password))

                    else:
                        if auth_key_state:
                            if auth_key_state == 'present':
                                self._commands.append('ntp authentication-key {0} {1} {2}'
                                                      .format(req_key_id,
                                                              req_encrypt_type,
                                                              req_password))
                        else:
                            self._commands.append('ntp authentication-key {0} {1} {2}'
                                                  .format(req_key_id,
                                                          req_encrypt_type,
                                                          req_password))

        req_trusted_keys = self._required_config.get('trusted_keys')
        if req_trusted_keys:
            for key in req_trusted_keys:
                self._commands.append('ntp trusted-key {0}' .format(key))


def main():
    """ main entry point for module execution
    """
    OnyxNTPModule.main()


if __name__ == '__main__':
    main()
