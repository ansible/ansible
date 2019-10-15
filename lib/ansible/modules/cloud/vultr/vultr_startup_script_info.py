#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vultr_startup_script_info
short_description: Gather information about the Vultr startup scripts available.
description:
  - Gather information about vultr_startup_scripts available.
version_added: "2.9"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr startup scripts information
  local_action:
    module: vultr_startup_script_info
  register: result

- name: Print the gathered information
  debug:
    var: result.vultr_startup_script_info
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
vultr_startup_script_info:
  description: Response from Vultr API
  returned: success
  type: complex
  sample:
    "vultr_startup_script_info": [
      {
        "date_created": "2018-07-19 08:38:36",
        "date_modified": "2018-07-19 08:38:36",
        "id": 327133,
        "name": "lolo",
        "script": "#!/bin/bash\necho Hello World > /root/hello",
        "type": "boot"
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrStartupScriptInfo(Vultr):

    def __init__(self, module):
        super(AnsibleVultrStartupScriptInfo, self).__init__(module, "vultr_startup_script_info")

        self.returns = {
            "SCRIPTID": dict(key='id', convert_to='int'),
            "date_created": dict(),
            "date_modified": dict(),
            "name": dict(),
            "script": dict(),
            "type": dict(),
        }

    def get_startupscripts(self):
        return self.api_query(path="/v1/startupscript/list")


def parse_startupscript_list(startupscipts_list):
    if not startupscipts_list:
        return []

    return [startupscript for id, startupscript in startupscipts_list.items()]


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    startupscript_info = AnsibleVultrStartupScriptInfo(module)
    result = startupscript_info.get_result(parse_startupscript_list(startupscript_info.get_startupscripts()))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
