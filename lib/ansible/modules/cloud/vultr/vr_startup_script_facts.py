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
module: vr_startup_script_facts
short_description: Gather facts about the Vultr startup scripts available.
description:
  - Gather facts about vr_startup_scripts available.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr startup scripts facts
  local_action:
    module: vr_startup_script_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_startup_script_facts
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
vultr_startup_script_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    "vultr_startup_script_facts": [
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


class AnsibleVultrStartupScriptFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrStartupScriptFacts, self).__init__(module, "vultr_startup_script_facts")

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
    return [startupscript for id, startupscript in startupscipts_list.items()]


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    startupscript_facts = AnsibleVultrStartupScriptFacts(module)
    result = startupscript_facts.get_result(parse_startupscript_list(startupscript_facts.get_startupscripts()))
    ansible_facts = {
        'vultr_startup_script_facts': result['vultr_startup_script_facts']
    }
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
