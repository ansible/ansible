#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: scaleway_lb_facts
short_description: Gather facts about the Scaleway load-balancer available.
description:
  - Gather facts about the Scaleway load-balancer available.
version_added: "2.9"
author:
  - "Remy Leone (@remyleone)"
extends_documentation_fragment: scaleway
options:
  region:
    description:
    - Scaleway zone
    required: true
'''

EXAMPLES = r'''
- name: Gather Scaleway organizations facts
  scaleway_lb_facts:
'''

RETURN = r'''
---
scaleway_lb_facts:
  description: Response from Scaleway API
  returned: success
  type: complex
  contains:
     "scaleway_lb_facts": [
                {
                    "backend_count": 0,
                    "description": "Load-balancer used for testing scaleway_lb_facts ansible module",
                    "frontend_count": 0,
                    "id": "00000000-0000-0000-0000-000000000000",
                    "instances": [
                        {
                            "id": "00000000-0000-0000-0000-000000000000",
                            "ip_address": "10.14.229.145",
                            "region": "fr-par",
                            "status": "ready"
                        },
                        {
                            "id": "00000000-0000-0000-0000-000000000000",
                            "ip_address": "10.14.208.171",
                            "region": "fr-par",
                            "status": "ready"
                        }
                    ],
                    "ip": [
                        {
                            "id": "00000000-0000-0000-0000-000000000000",
                            "ip_address": "51.159.26.123",
                            "lb_id": "00000000-0000-0000-0000-000000000000",
                            "organization_id": "00000000-0000-0000-0000-000000000000",
                            "region": "fr-par",
                            "reverse": ""
                        }
                    ],
                    "name": "lb_facts_ansible_test",
                    "organization_id": "00000000-0000-0000-0000-000000000000",
                    "region": "fr-par",
                    "status": "ready",
                    "tags": [
                        "first_tag",
                        "second_tag"
                    ]
                }
            ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import (
    Scaleway,
    ScalewayException,
    scaleway_argument_spec,
    SCALEWAY_ENDPOINT)


class ScalewayLbFacts(Scaleway):

    def __init__(self, module):
        super(ScalewayLbFacts, self).__init__(module)

        region = module.params["region"]
        api_version = module.params["api_version"]
        self.module.params['api_url'] = "/".join([SCALEWAY_ENDPOINT,
                                                  'lb/%s/regions/%s' % (api_version, region)])

        self.name = 'lbs'


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        region=dict(required=True),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(
            ansible_facts={'scaleway_lb_facts': ScalewayLbFacts(module).get_resources()}
        )
    except ScalewayException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()
