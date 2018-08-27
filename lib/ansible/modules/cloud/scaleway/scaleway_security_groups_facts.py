#!/usr/bin/python
#
# Scaleway security groups facts module
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
module: scaleway_security_groups_facts
short_description: Scaleway security groups facts module
version_added: "2.7"
author: Remy Leone (@sieben)
description:
    - "This module gather facts about security groups on Scaleway."
extends_documentation_fragment: scaleway
'''

EXAMPLES = '''
- name: Get security groups information
  scaleway_security_groups_facts:
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "scaleway_security_groups": [
            {
              "description": "Auto generated security group.",
              "enable_default_security": true,
              "servers": [
                {
                  "id": "3f1568ca-b1a2-4e98-b6f7-31a0588157f1",
                  "name": "ansible_tuto-1"
                },
                {
                  "id": "1cb8a48a-9cd2-4535-a3af-cf6b00a77ee5",
                  "name": "ansible_tuto-2"
                },
                {
                  "id": "495b84c0-58ca-4494-90b3-a55d3d09c83f",
                  "name": "ansible_tuto-0"
                },
                {
                  "id": "4785f73d-4126-4d7c-9865-76d9c39afe99",
                  "name": "scw-e06da7"
                },
                {
                  "id": "7ccdbeeb-9c13-4714-869e-63c5555ceef2",
                  "name": "scw-9d4c6a"
                },
                {
                  "id": "4f4d2b9e-32b5-4486-9621-67e1adf3f24d",
                  "name": "scw-a7cdb5"
                }
              ],
              "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
              "organization_default": true,
              "id": "54e2d5f6-d79c-44cc-b19f-613699b9cc7e",
              "name": "Default security group"
            },
            {
              "description": "allow HTTP and HTTPS traffic",
              "enable_default_security": true,
              "servers": [],
              "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
              "organization_default": false,
              "id": "e00f43d0-15cc-456d-af7b-3c74c1df0022",
              "name": "http"
            },
            {
              "description": "allow HTTP and HTTPS traffic",
              "enable_default_security": true,
              "servers": [],
              "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
              "organization_default": false,
              "id": "48f22a2f-8111-4532-a38d-242ef7fbcaa4",
              "name": "http"
            },
            {
              "description": "red",
              "enable_default_security": true,
              "servers": [],
              "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
              "organization_default": false,
              "id": "a601c662-7d21-4636-9aca-2e096eb8ebef",
              "name": "red"
            },
            {
              "description": "blue",
              "enable_default_security": true,
              "servers": [],
              "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
              "organization_default": false,
              "id": "858d4fe3-86ab-48de-b810-fb60c33ef3e5",
              "name": "blue"
            },
            {
              "description": "allow HTTP and HTTPS traffic",
              "enable_default_security": true,
              "servers": [],
              "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
              "organization_default": false,
              "id": "bb3f38aa-1907-4479-99bd-875743226b83",
              "name": "http"
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

    response = compute_api.get("security_groups")
    status_code = response.status_code

    if not response.ok:
        module.fail_json(msg='Error fetching facts [{0}: {1}]'.format(
            status_code, response.json['message']))

    security_groups = response.json["security_groups"]
    module.exit_json(changed=False, scaleway_security_groups=security_groups)


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
