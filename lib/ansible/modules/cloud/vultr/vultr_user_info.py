#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# Copyright (c) 2019, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vultr_user_info
short_description: Get information about the Vultr user available.
description:
  - Get infos about users available in Vultr.
version_added: "2.9"
author:
  - "Yanis Guenane (@Spredzy)"
  - "René Moser (@resmo)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Get Vultr user infos
  vultr_user_info:
  register: result

- name: Print the infos
  debug:
    var: result.vultr_user_info
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
vultr_user_info:
  description: Response from Vultr API as list
  returned: available
  type: complex
  contains:
    id:
      description: ID of the user.
      returned: success
      type: str
      sample: 5904bc6ed9234
    api_key:
      description: API key of the user.
      returned: only after resource was created
      type: str
      sample: 567E6K567E6K567E6K567E6K567E6K
    name:
      description: Name of the user.
      returned: success
      type: str
      sample: john
    email:
      description: Email of the user.
      returned: success
      type: str
      sample: "john@exmaple.com"
    api_enabled:
      description: Whether the API is enabled or not.
      returned: success
      type: bool
      sample: true
    acls:
      description: List of ACLs of the user.
      returned: success
      type: list
      sample: [ manage_users, support, upgrade ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrUserInfo(Vultr):

    def __init__(self, module):
        super(AnsibleVultrUserInfo, self).__init__(module, "vultr_user_info")

        self.returns = {
            "USERID": dict(key='id'),
            "acls": dict(),
            "api_enabled": dict(),
            "email": dict(),
            "name": dict()
        }

    def get_regions(self):
        return self.api_query(path="/v1/user/list")


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    user_info = AnsibleVultrUserInfo(module)
    result = user_info.get_result(user_info.get_regions())
    module.exit_json(**result)


if __name__ == '__main__':
    main()
