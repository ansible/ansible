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
module: scaleway_ip_facts
short_description: Gather facts about the Scaleway ips available.
description:
  - Gather facts about the Scaleway ips available.
version_added: "2.7"
author:
  - "Yanis Guenane (@Spredzy)"
  - "Remy Leone (@sieben)"
extends_documentation_fragment: scaleway
'''

EXAMPLES = r'''
- name: Gather Scaleway ips facts
  scaleway_ip_facts:
'''

RETURN = r'''
---
scaleway_ip_facts:
  description: Response from Scaleway API
  returned: success
  type: complex
  contains:
    "scaleway_ip_facts": [
        {
            "address": "163.172.170.243",
            "id": "ea081794-a581-8899-8451-386ddaf0a451",
            "organization": "3f709602-5e6c-4619-b80c-e324324324af",
            "reverse": null,
            "server": {
                "id": "12f19bc7-109c-4517-954c-e6b3d0311363",
                "name": "scw-e0d158"
            }
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import (
    Scaleway, ScalewayException, scaleway_argument_spec
)


class ScalewayIpFacts(Scaleway):

    def __init__(self, module):
        super(ScalewayIpFacts, self).__init__(module)
        self.name = 'ips'


def main():
    module = AnsibleModule(
        argument_spec=scaleway_argument_spec(),
        supports_check_mode=True,
    )

    try:
        module.exit_json(
            ansible_facts={'scaleway_ip_facts': ScalewayIpFacts(module).get_resources()}
        )
    except ScalewayException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()
