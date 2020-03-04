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
module: vultr_os_info
short_description: Get information about the Vultr OSes available.
description:
  - Get infos about OSes available to boot servers.
version_added: "2.9"
author:
  - "Yanis Guenane (@Spredzy)"
  - "René Moser (@resmo)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Get Vultr OSes infos
  vultr_os_info:
  register: results

- name: Print the gathered infos
  debug:
    var: results.vultr_os_info
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
vultr_os_info:
  description: Response from Vultr API as list
  returned: available
  type: complex
  contains:
    arch:
      description: OS Architecture
      returned: success
      type: str
      sample: x64
    family:
      description: OS family
      returned: success
      type: str
      sample: openbsd
    name:
      description: OS name
      returned: success
      type: str
      sample: OpenBSD 6 x64
    windows:
      description: OS is a MS Windows
      returned: success
      type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrOSInfo(Vultr):

    def __init__(self, module):
        super(AnsibleVultrOSInfo, self).__init__(module, "vultr_os_info")

        self.returns = {
            "OSID": dict(key='id', convert_to='int'),
            "arch": dict(),
            "family": dict(),
            "name": dict(),
            "windows": dict(convert_to='bool')
        }

    def get_oses(self):
        return self.api_query(path="/v1/os/list")


def parse_oses_list(oses_list):
    return [os for id, os in oses_list.items()]


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    os_info = AnsibleVultrOSInfo(module)
    result = os_info.get_result(parse_oses_list(os_info.get_oses()))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
