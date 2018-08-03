#!/usr/bin/python
#
# Scaleway servers facts module
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
module: scaleway_servers_facts
short_description: Scaleway servers facts module
version_added: "2.7"
author: Remy Leone (@sieben)
description:
    - "This module gather facts about servers on Scaleway."
extends_documentation_fragment: scaleway
options:
  region:
    description:
    - Scaleway compute zone
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1
'''

EXAMPLES = '''
- name: Get servers information
  scaleway_servers_facts:
    region: par1
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "scaleway_servers": [
            {
                "arch": "x86_64",
                "boot_type": "local",
                "bootscript": {
                    "architecture": "x86_64",
                    "bootcmdargs": "LINUX_COMMON scaleway boot=local nbd.max_part=16",
                    "default": true,
                    "dtb": "",
                    "id": "b1e68c26-a19c-4eac-9222-498b22bd7ad9",
                    "initrd": "http://169.254.42.24/initrd/initrd-Linux-x86_64-v3.14.5.gz",
                    "kernel": "http://169.254.42.24/kernel/x86_64-mainline-lts-4.4-4.4.127-rev1/vmlinuz-4.4.127",
                    "organization": "11111111-1111-4111-8111-111111111111",
                    "public": true,
                    "title": "x86_64 mainline 4.4.127 rev1"
                },
                "commercial_type": "START1-S",
                "creation_date": "2018-07-31T13:37:59.326366+00:00",
                "dynamic_ip_required": false,
                "enable_ipv6": false,
                "extra_networks": [],
                "hostname": "scw-a7cdb5",
                "id": "4f4d2b9e-32b5-4486-9621-67e1adf3f24d",
                "image": {
                    "arch": "x86_64",
                    "creation_date": "2018-07-03T13:35:45.953478+00:00",
                    "default_bootscript": {
                        "architecture": "x86_64",
                        "bootcmdargs": "LINUX_COMMON scaleway boot=local nbd.max_part=16",
                        "default": true,
                        "dtb": "",
                        "id": "b1e68c26-a19c-4eac-9222-498b22bd7ad9",
                        "initrd": "http://169.254.42.24/initrd/initrd-Linux-x86_64-v3.14.5.gz",
                        "kernel": "http://169.254.42.24/kernel/x86_64-mainline-lts-4.4-4.4.127-rev1/vmlinuz-4.4.127",
                        "organization": "11111111-1111-4111-8111-111111111111",
                        "public": true,
                        "title": "x86_64 mainline 4.4.127 rev1"
                    },
                    "extra_volumes": [],
                    "from_server": null,
                    "id": "b338f25c-ba76-4fb5-bb3d-9b9b36d8f11d",
                    "modification_date": "2018-07-03T16:07:03.945061+00:00",
                    "name": "Ubuntu Xenial",
                    "organization": "51b656e3-4865-41e8-adbc-0c45bdd780db",
                    "public": true,
                    "root_volume": {
                        "id": "d499f9e0-7437-4458-80e7-37f8509de87b",
                        "name": "snapshot-84e78b32-9aa2-4662-9954-262805b8f72d-2018-07-03_13:35",
                        "size": 50000000000,
                        "volume_type": "l_ssd"
                    },
                    "state": "available"
                },
                "ipv6": null,
                "location": {
                    "cluster_id": "10",
                    "hypervisor_id": "613",
                    "node_id": "3",
                    "platform_id": "13",
                    "zone_id": "par1"
                },
                "maintenances": [],
                "modification_date": "2018-07-31T13:38:35.149407+00:00",
                "name": "scw-a7cdb5",
                "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
                "private_ip": "10.16.90.5",
                "public_ip": {
                    "address": "212.47.228.83",
                    "dynamic": false,
                    "id": "6747b98e-d5e5-49e0-85b9-a46a7e2c9552"
                },
                "security_group": {
                    "id": "54e2d5f6-d79c-44cc-b19f-613699b9cc7e",
                    "name": "Default security group"
                },
                "state": "running",
                "state_detail": "booting kernel",
                "tags": [],
                "volumes": {
                    "0": {
                        "creation_date": "2018-07-31T13:37:59.326366+00:00",
                        "export_uri": "device://dev/vda",
                        "id": "21dc2613-fcc7-49f6-8aef-f97f03bf82fd",
                        "modification_date": "2018-07-31T13:37:59.326366+00:00",
                        "name": "snapshot-84e78b32-9aa2-4662-9954-262805b8f72d-2018-07-03_13:35",
                        "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
                        "server": {
                            "id": "4f4d2b9e-32b5-4486-9621-67e1adf3f24d",
                            "name": "scw-a7cdb5"
                        },
                        "size": 50000000000,
                        "state": "available",
                        "volume_type": "l_ssd"
                    }
                }
            }
        ]
    }
'''

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.scaleway import ScalewayAPI, SCALEWAY_LOCATION


def core(module):
    api_token = module.params['oauth_token']
    region = module.params["region"]

    compute_api = ScalewayAPI(module=module,
                              headers={'X-Auth-Token': api_token},
                              base_url=SCALEWAY_LOCATION[region]["api_endpoint"])

    response = compute_api.get("servers")
    status_code = response.status_code

    if not response.ok:
        module.fail_json(msg='Error fetching facts [{0}: {1}]'.format(
            status_code, response.json['message']))

    servers = response.json["servers"]
    module.exit_json(changed=False, scaleway_servers=servers)


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
            region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
            timeout=dict(type="int", default=30),
            validate_certs=dict(default=True, type='bool'),
        ),
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
