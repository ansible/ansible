#!/usr/bin/python
#
# Scaleway IP facts module
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
module: scaleway_ip_facts
short_description: Scaleway IP facts module
version_added: "2.7"
author: Remy Leone (@sieben)
description:
    - "This module gather facts about IP on Scaleway."
extends_documentation_fragment: scaleway
'''

EXAMPLES = '''
- name: Get IP information
  scaleway_ip_facts:
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "scaleway_ips": [
            {
                "address": "212.47.228.83",
                "id": "6747b98e-d5e5-49e0-85b9-a46a7e2c9552",
                "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
                "reverse": null,
                "server": {
                    "id": "4f4d2b9e-32b5-4486-9621-67e1adf3f24d",
                    "name": "scw-a7cdb5"
                }
            },
            {
                "address": "51.15.247.163",
                "id": "42998f26-0523-4c27-9db2-ad290157cf2d",
                "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
                "reverse": null,
                "server": {
                    "id": "4785f73d-4126-4d7c-9865-76d9c39afe99",
                    "name": "scw-e06da7"
                }
            },
            {
                "address": "51.15.224.19",
                "id": "7a53e2d0-1b17-45d2-b9c3-98246c5a13a6",
                "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
                "reverse": null,
                "server": {
                    "id": "7ccdbeeb-9c13-4714-869e-63c5555ceef2",
                    "name": "scw-9d4c6a"
                }
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

    response = compute_api.get("ips")
    status_code = response.status_code

    if not response.ok:
        module.fail_json(msg='Error fetching facts [{0}: {1}]'.format(
            status_code, response.json['message']))

    ips = response.json["ips"]
    module.exit_json(changed=False, scaleway_ips=ips)


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
        supports_check_mode=False,
    )

    core(module)


if __name__ == '__main__':
    main()
