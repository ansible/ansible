#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vr_ssh_key
short_description: Manages ssh keys on Vultr.
description:
  - Create, update and remove ssh keys.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the ssh key.
    required: true
  ssh_key:
    description:
      - SSH public key.
      - Required if C(state=present).
    required: false
  state:
    description:
      - State of the ssh key.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = '''
- name: ensure an SSH key is present
  local_action:
    module: vr_ssh_key
    name: my ssh key
    ssh_key: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"

- name: ensure an SSH key is absent
  local_action:
    module: vr_ssh_key
    name: my ssh key
    state: absent
'''

RETURN = '''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: string
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: string
      sample: "https://api.vultr.com"
vultr_ssh_key:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    id:
      description: ID of the ssh key
      returned: success
      type: string
      sample: 5904bc6ed9234
    name:
      description: Name of the ssh key
      returned: success
      type: string
      sample: my ssh key
    date_created:
      description: Date the ssh key was created
      returned: success
      type: string
      sample: "2017-08-26 12:47:48"
    ssh_key:
      description: SSH public key
      returned: success
      type: string
      sample: "ssh-rsa AA... someother@example.com"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrSshKey(Vultr):

    def __init__(self, module):
        super(AnsibleVultrSshKey, self).__init__(module, "vultr_ssh_key")

        self.returns = {
            'SSHKEYID': dict(key='id'),
            'name': dict(),
            'ssh_key': dict(),
            'date_created': dict(),
        }

    def get_ssh_key(self):
        ssh_keys = self.api_query(path="/v1/sshkey/list")
        if ssh_keys:
            for ssh_key_id, ssh_key_data in ssh_keys.items():
                if ssh_key_data.get('name') == self.module.params.get('name'):
                    return ssh_key_data
        return {}

    def present_ssh_key(self):
        ssh_key = self.get_ssh_key()
        if not ssh_key:
            ssh_key = self._create_ssh_key(ssh_key)
        else:
            ssh_key = self._update_ssh_key(ssh_key)
        return ssh_key

    def _create_ssh_key(self, ssh_key):
        self.result['changed'] = True
        data = {
            'name': self.module.params.get('name'),
            'ssh_key': self.module.params.get('ssh_key'),
        }
        self.result['diff']['before'] = {}
        self.result['diff']['after'] = data

        if not self.module.check_mode:
            self.api_query(
                path="/v1/sshkey/create",
                method="POST",
                data=data
            )
            ssh_key = self.get_ssh_key()
        return ssh_key

    def _update_ssh_key(self, ssh_key):
        param_ssh_key = self.module.params.get('ssh_key')
        if param_ssh_key != ssh_key['ssh_key']:
            self.result['changed'] = True

            data = {
                'SSHKEYID': ssh_key['SSHKEYID'],
                'ssh_key': param_ssh_key,
            }

            self.result['diff']['before'] = ssh_key
            self.result['diff']['after'] = data
            self.result['diff']['after'].update({'date_created': ssh_key['date_created']})

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/sshkey/update",
                    method="POST",
                    data=data
                )
                ssh_key = self.get_ssh_key()
        return ssh_key

    def absent_ssh_key(self):
        ssh_key = self.get_ssh_key()
        if ssh_key:
            self.result['changed'] = True

            data = {
                'SSHKEYID': ssh_key['SSHKEYID'],
            }

            self.result['diff']['before'] = ssh_key
            self.result['diff']['after'] = {}

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/sshkey/destroy",
                    method="POST",
                    data=data
                )
        return ssh_key


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        ssh_key=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['ssh_key']),
        ],
        supports_check_mode=True,
    )

    vr_ssh_key = AnsibleVultrSshKey(module)
    if module.params.get('state') == "absent":
        ssh_key = vr_ssh_key.absent_ssh_key()
    else:
        ssh_key = vr_ssh_key.present_ssh_key()

    result = vr_ssh_key.get_result(ssh_key)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
