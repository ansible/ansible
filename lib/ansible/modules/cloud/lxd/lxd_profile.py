#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Hiroaki Nakamura <hnakamur@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: lxd_profile
short_description: Manage LXD profiles
version_added: "2.2"
description:
  - Management of LXD profiles
author: "Hiroaki Nakamura (@hnakamur)"
options:
    name:
        description:
          - Name of a profile.
        required: true
    config:
        description:
          - 'The config for the container (e.g. {"limits.memory": "4GB"}).
            See U(https://github.com/lxc/lxd/blob/master/doc/rest-api.md#patch-3)'
          - If the profile already exists and its "config" value in metadata
            obtained from
            GET /1.0/profiles/<name>
            U(https://github.com/lxc/lxd/blob/master/doc/rest-api.md#get-19)
            are different, they this module tries to apply the configurations.
          - Not all config values are supported to apply the existing profile.
            Maybe you need to delete and recreate a profile.
        required: false
    devices:
        description:
          - 'The devices for the profile
            (e.g. {"rootfs": {"path": "/dev/kvm", "type": "unix-char"}).
            See U(https://github.com/lxc/lxd/blob/master/doc/rest-api.md#patch-3)'
        required: false
    new_name:
        description:
          - A new name of a profile.
          - If this parameter is specified a profile will be renamed to this name.
            See U(https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-11)
        required: false
    state:
        choices:
          - present
          - absent
        description:
          - Define the state of a profile.
        required: false
        default: present
    url:
        description:
          - The unix domain socket path or the https URL for the LXD server.
        required: false
        default: unix:/var/lib/lxd/unix.socket
    key_file:
        description:
          - The client certificate key file path.
        required: false
        default: '"{}/.config/lxc/client.key" .format(os.environ["HOME"])'
    cert_file:
        description:
          - The client certificate file path.
        required: false
        default: '"{}/.config/lxc/client.crt" .format(os.environ["HOME"])'
    trust_password:
        description:
          - The client trusted password.
          - You need to set this password on the LXD server before
            running this module using the following command.
            lxc config set core.trust_password <some random password>
            See U(https://www.stgraber.org/2016/04/18/lxd-api-direct-interaction/)
          - If trust_password is set, this module send a request for
            authentication before sending any requests.
        required: false
notes:
  - Profiles must have a unique name. If you attempt to create a profile
    with a name that already existed in the users namespace the module will
    simply return as "unchanged".
'''

EXAMPLES = '''
# An example for creating a profile
- hosts: localhost
  connection: local
  tasks:
    - name: Create a profile
      lxd_profile:
        name: macvlan
        state: present
        config: {}
        description: my macvlan profile
        devices:
          eth0:
            nictype: macvlan
            parent: br0
            type: nic

# An example for creating a profile via http connection
- hosts: localhost
  connection: local
  tasks:
  - name: create macvlan profile
    lxd_profile:
      url: https://127.0.0.1:8443
      # These cert_file and key_file values are equal to the default values.
      #cert_file: "{{ lookup('env', 'HOME') }}/.config/lxc/client.crt"
      #key_file: "{{ lookup('env', 'HOME') }}/.config/lxc/client.key"
      trust_password: mypassword
      name: macvlan
      state: present
      config: {}
      description: my macvlan profile
      devices:
        eth0:
          nictype: macvlan
          parent: br0
          type: nic

# An example for deleting a profile
- hosts: localhost
  connection: local
  tasks:
    - name: Delete a profile
      lxd_profile:
        name: macvlan
        state: absent

# An example for renaming a profile
- hosts: localhost
  connection: local
  tasks:
    - name: Rename a profile
      lxd_profile:
        name: macvlan
        new_name: macvlan2
        state: present
'''

RETURN='''
old_state:
  description: The old state of the profile
  returned: success
  type: string
  sample: "absent"
logs:
  description: The logs of requests and responses.
  returned: when ansible-playbook is invoked with -vvvv.
  type: list
  sample: "(too long to be placed here)"
actions:
  description: List of actions performed for the profile.
  returned: success
  type: list
  sample: '["create"]'
'''

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.lxd import LXDClient, LXDClientException


# PROFILE_STATES is a list for states supported
PROFILES_STATES = [
    'present', 'absent'
]

# CONFIG_PARAMS is a list of config attribute names.
CONFIG_PARAMS = [
    'config', 'description', 'devices'
]


class LXDProfileManagement(object):
    def __init__(self, module):
        """Management of LXC containers via Ansible.

        :param module: Processed Ansible Module.
        :type module: ``object``
        """
        self.module = module
        self.name = self.module.params['name']
        self._build_config()
        self.state = self.module.params['state']
        self.new_name = self.module.params.get('new_name', None)

        self.url = self.module.params['url']
        self.key_file = self.module.params.get('key_file', None)
        self.cert_file = self.module.params.get('cert_file', None)
        self.debug = self.module._verbosity >= 4
        try:
            self.client = LXDClient(
                self.url, key_file=self.key_file, cert_file=self.cert_file,
                debug=self.debug
            )
        except LXDClientException as e:
            self.module.fail_json(msg=e.msg)
        self.trust_password = self.module.params.get('trust_password', None)
        self.actions = []

    def _build_config(self):
        self.config = {}
        for attr in CONFIG_PARAMS:
            param_val = self.module.params.get(attr, None)
            if param_val is not None:
                self.config[attr] = param_val

    def _get_profile_json(self):
        return self.client.do(
            'GET', '/1.0/profiles/{0}'.format(self.name),
            ok_error_codes=[404]
        )

    @staticmethod
    def _profile_json_to_module_state(resp_json):
        if resp_json['type'] == 'error':
            return 'absent'
        return 'present'

    def _update_profile(self):
        if self.state == 'present':
            if self.old_state == 'absent':
                if self.new_name is None:
                    self._create_profile()
                else:
                    self.module.fail_json(
                        msg='new_name must not be set when the profile does not exist and the specified state is present',
                        changed=False)
            else:
                if self.new_name is not None and self.new_name != self.name:
                    self._rename_profile()
                if self._needs_to_apply_profile_configs():
                    self._apply_profile_configs()
        elif self.state == 'absent':
            if self.old_state == 'present':
                if self.new_name is None:
                    self._delete_profile()
                else:
                    self.module.fail_json(
                        msg='new_name must not be set when the profile exists and the specified state is absent',
                        changed=False)

    def _create_profile(self):
        config = self.config.copy()
        config['name'] = self.name
        self.client.do('POST', '/1.0/profiles', config)
        self.actions.append('create')

    def _rename_profile(self):
        config = {'name': self.new_name}
        self.client.do('POST', '/1.0/profiles/{}'.format(self.name), config)
        self.actions.append('rename')
        self.name = self.new_name

    def _needs_to_change_profile_config(self, key):
        if key not in self.config:
            return False
        old_configs = self.old_profile_json['metadata'].get(key, None)
        return self.config[key] != old_configs

    def _needs_to_apply_profile_configs(self):
        return (
            self._needs_to_change_profile_config('config') or
            self._needs_to_change_profile_config('description') or
            self._needs_to_change_profile_config('devices')
        )

    def _apply_profile_configs(self):
        config = self.old_profile_json.copy()
        for k, v in self.config.items():
            config[k] = v
        self.client.do('PUT', '/1.0/profiles/{}'.format(self.name), config)
        self.actions.append('apply_profile_configs')

    def _delete_profile(self):
        self.client.do('DELETE', '/1.0/profiles/{}'.format(self.name))
        self.actions.append('delete')

    def run(self):
        """Run the main method."""

        try:
            if self.trust_password is not None:
                self.client.authenticate(self.trust_password)

            self.old_profile_json = self._get_profile_json()
            self.old_state = self._profile_json_to_module_state(self.old_profile_json)
            self._update_profile()

            state_changed = len(self.actions) > 0
            result_json = {
                'changed': state_changed,
                'old_state': self.old_state,
                'actions': self.actions
            }
            if self.client.debug:
                result_json['logs'] = self.client.logs
            self.module.exit_json(**result_json)
        except LXDClientException as e:
            state_changed = len(self.actions) > 0
            fail_params = {
                'msg': e.msg,
                'changed': state_changed,
                'actions': self.actions
            }
            if self.client.debug:
                fail_params['logs'] = e.kwargs['logs']
            self.module.fail_json(**fail_params)


def main():
    """Ansible Main module."""

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(
                type='str',
                required=True
            ),
            new_name=dict(
                type='str',
            ),
            config=dict(
                type='dict',
            ),
            description=dict(
                type='str',
            ),
            devices=dict(
                type='dict',
            ),
            state=dict(
                choices=PROFILES_STATES,
                default='present'
            ),
            url=dict(
                type='str',
                default='unix:/var/lib/lxd/unix.socket'
            ),
            key_file=dict(
                type='str',
                default='{}/.config/lxc/client.key'.format(os.environ['HOME'])
            ),
            cert_file=dict(
                type='str',
                default='{}/.config/lxc/client.crt'.format(os.environ['HOME'])
            ),
            trust_password=dict( type='str', no_log=True)
        ),
        supports_check_mode=False,
    )

    lxd_manage = LXDProfileManagement(module=module)
    lxd_manage.run()


if __name__ == '__main__':
    main()
