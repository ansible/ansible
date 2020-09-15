#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# (c) 2019, René Moser <mail@renemoser.net>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vultr_ssh_key_info
short_description: Get information about the Vultr SSH keys available.
description:
  - Get infos about SSH keys available.
version_added: "2.9"
author:
  - "Yanis Guenane (@Spredzy)"
  - "René Moser (@resmo)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Get Vultr SSH keys infos
  vultr_ssh_key_info:
  register: result

- name: Print the infos
  debug:
    var: result.vultr_ssh_key_info
'''

RETURN = r'''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: str
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
    api_retry_max_delay:
      description: Exponential backoff delay in seconds between retries up to this max delay value.
      returned: success
      type: int
      sample: 12
      version_added: '2.9'
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: str
      sample: "https://api.vultr.com"
vultr_ssh_key_info:
  description: Response from Vultr API as list
  returned: success
  type: complex
  contains:
    id:
      description: ID of the ssh key
      returned: success
      type: str
      sample: 5904bc6ed9234
    name:
      description: Name of the ssh key
      returned: success
      type: str
      sample: my ssh key
    date_created:
      description: Date the ssh key was created
      returned: success
      type: str
      sample: "2017-08-26 12:47:48"
    ssh_key:
      description: SSH public key
      returned: success
      type: str
      sample: "ssh-rsa AA... someother@example.com"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrSSHKeyInfo(Vultr):

    def __init__(self, module):
        super(AnsibleVultrSSHKeyInfo, self).__init__(module, "vultr_ssh_key_info")

        self.returns = {
            'SSHKEYID': dict(key='id'),
            'name': dict(),
            'ssh_key': dict(),
            'date_created': dict(),
        }

    def get_sshkeys(self):
        return self.api_query(path="/v1/sshkey/list")


def parse_keys_list(keys_list):
    if not keys_list:
        return []

    return [key for id, key in keys_list.items()]


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    sshkey_info = AnsibleVultrSSHKeyInfo(module)
    result = sshkey_info.get_result(parse_keys_list(sshkey_info.get_sshkeys()))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
