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
module: scaleway_organization_facts
short_description: Gather facts about the Scaleway organizations available.
description:
  - Gather facts about the Scaleway organizations available.
version_added: "2.7"
author:
  - "Yanis Guenane (@Spredzy)"
  - "Remy Leone (@sieben)"
options:
  api_url:
    description:
      - Scaleway API URL
    default: 'https://account.scaleway.com'
    aliases: ['base_url']
extends_documentation_fragment: scaleway
'''

EXAMPLES = r'''
- name: Gather Scaleway organizations facts
  scaleway_organization_facts:
'''

RETURN = r'''
---
scaleway_organization_facts:
  description: Response from Scaleway API
  returned: success
  type: complex
  sample:
    "scaleway_organization_facts": [
        {
            "address_city_name": "Paris",
            "address_country_code": "FR",
            "address_line1": "42 Rue de l'univers",
            "address_line2": null,
            "address_postal_code": "75042",
            "address_subdivision_code": "FR-75",
            "creation_date": "2018-08-06T13:43:28.508575+00:00",
            "currency": "EUR",
            "customer_class": "individual",
            "id": "3f709602-5e6c-4619-b80c-e8432ferewtr",
            "locale": "fr_FR",
            "modification_date": "2018-08-06T14:56:41.401685+00:00",
            "name": "James Bond",
            "support_id": "694324",
            "support_level": "basic",
            "support_pin": "9324",
            "users": [],
            "vat_number": null,
            "warnings": []
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.scaleway import (
    Scaleway, ScalewayException, scaleway_argument_spec
)


class ScalewayOrganizationFacts(Scaleway):

    def __init__(self, module):
        super(ScalewayOrganizationFacts, self).__init__(module)
        self.name = 'organizations'


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        api_url=dict(fallback=(env_fallback, ['SCW_API_URL']), default='https://account.scaleway.com', aliases=['base_url']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(
            ansible_facts={'scaleway_organization_facts': ScalewayOrganizationFacts(module).get_resources()}
        )
    except ScalewayException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()
