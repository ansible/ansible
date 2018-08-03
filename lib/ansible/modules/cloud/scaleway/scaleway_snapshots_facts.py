#!/usr/bin/python
#
# Scaleway snapshots facts module
#
# Copyright (C) 2018 Online SAS.
# https://www.scaleway.com
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: scaleway_snapshots_facts
short_description: Scaleway snapshots facts module
version_added: "2.7"
author: Remy Leone (@sieben)
description:
    - "This module gathers facts about snapshots on Scaleway."
extends_documentation_fragment: scaleway
'''

EXAMPLES = '''
- name: Get snapshots information
  scaleway_snapshots_facts:
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "scaleway_snapshots": [
            {
              "state": "available",
              "base_volume": null,
              "name": "odoo-snapshot",
              "modification_date": "2018-06-18T11:24:46.272833+00:00",
              "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
              "size": 50000000000,
              "id": "c18dd10e-86c2-443d-81d9-1ecbdc959e3b",
              "volume_type": "l_ssd",
              "creation_date": "2018-06-06T08:40:45.395451+00:00"
            },
            {
              "state": "available",
              "base_volume": null,
              "name": "neo4j-genealogy-snapshot",
              "modification_date": "2018-05-21T10:19:03.868987+00:00",
              "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
              "size": 50000000000,
              "id": "93bf81ec-f778-47ca-a6f3-9c320f646464",
              "volume_type": "l_ssd",
              "creation_date": "2018-05-03T13:58:46.416778+00:00"
            }
        ]
    }
'''

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.scaleway import ScalewayAPI, ROOT_ZONE_ENDPOINT


def core(module):
    api_token = module.params['oauth_token']

    compute_api = ScalewayAPI(module=module,
                              headers={'X-Auth-Token': api_token},
                              base_url=ROOT_ZONE_ENDPOINT)

    response = compute_api.get("snapshots")
    status_code = response.status_code

    if not response.ok:
        module.fail_json(msg='Error fetching facts [{0}: {1}]'.format(
            status_code, response.json['message']))

    snapshots = response.json["snapshots"]
    module.exit_json(changed=False, scaleway_snapshots=snapshots)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            oauth_token=dict(
                no_log=True,
                # Support environment variable for Scaleway OAuth Token
                fallback=(env_fallback, ['SCW_TOKEN', 'SCW_API_KEY', 'SCW_OAUTH_TOKEN']),
                required=True,
                aliases=['api_token'],
            ),
            timeout=dict(type="int", default=30),
            validate_certs=dict(default=True, type='bool'),
        ),
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
