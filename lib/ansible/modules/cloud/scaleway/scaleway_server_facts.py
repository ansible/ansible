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
module: scaleway_server_facts
short_description: Gather facts about the Scaleway servers available.
description:
  - Gather facts about the Scaleway servers available.
version_added: "2.7"
author:
  - "Yanis Guenane (@Spredzy)"
  - "Remy Leone (@sieben)"
extends_documentation_fragment: scaleway
options:
  region:
    version_added: "2.8"
    description:
     - Scaleway region to use (for example par1).
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1
'''

EXAMPLES = r'''
- name: Gather Scaleway servers facts
  scaleway_server_facts:
    region: par1
'''

RETURN = r'''
---
scaleway_server_facts:
  description: Response from Scaleway API
  returned: success
  type: complex
  contains:
    "scaleway_server_facts": [
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
            "commercial_type": "START1-XS",
            "creation_date": "2018-08-14T21:36:56.271545+00:00",
            "dynamic_ip_required": false,
            "enable_ipv6": false,
            "extra_networks": [],
            "hostname": "scw-e0d256",
            "id": "12f19bc7-108c-4517-954c-e6b3d0311363",
            "image": {
                "arch": "x86_64",
                "creation_date": "2018-04-26T12:42:21.619844+00:00",
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
                "id": "67375eb1-f14d-4f02-bb42-6119cecbde51",
                "modification_date": "2018-04-26T12:49:07.573004+00:00",
                "name": "Ubuntu Xenial",
                "organization": "51b656e3-4865-41e8-adbc-0c45bdd780db",
                "public": true,
                "root_volume": {
                    "id": "020b8d61-3867-4a0e-84a4-445c5393e05d",
                    "name": "snapshot-87fc282d-f252-4262-adad-86979d9074cf-2018-04-26_12:42",
                    "size": 25000000000,
                    "volume_type": "l_ssd"
                },
                "state": "available"
            },
            "ipv6": null,
            "location": {
                "cluster_id": "5",
                "hypervisor_id": "412",
                "node_id": "2",
                "platform_id": "13",
                "zone_id": "par1"
            },
            "maintenances": [],
            "modification_date": "2018-08-14T21:37:28.630882+00:00",
            "name": "scw-e0d256",
            "organization": "3f709602-5e6c-4619-b80c-e841c89734af",
            "private_ip": "10.14.222.131",
            "protected": false,
            "public_ip": {
                "address": "163.172.170.197",
                "dynamic": false,
                "id": "ea081794-a581-4495-8451-386ddaf0a451"
            },
            "security_group": {
                "id": "a37379d2-d8b0-4668-9cfb-1233fc436f7e",
                "name": "Default security group"
            },
            "state": "running",
            "state_detail": "booted",
            "tags": [],
            "volumes": {
                "0": {
                    "creation_date": "2018-08-14T21:36:56.271545+00:00",
                    "export_uri": "device://dev/vda",
                    "id": "68386fae-4f55-4fbf-aabb-953036a85872",
                    "modification_date": "2018-08-14T21:36:56.271545+00:00",
                    "name": "snapshot-87fc282d-f252-4262-adad-86979d9074cf-2018-04-26_12:42",
                    "organization": "3f709602-5e6c-4619-b80c-e841c89734af",
                    "server": {
                        "id": "12f19bc7-108c-4517-954c-e6b3d0311363",
                        "name": "scw-e0d256"
                    },
                    "size": 25000000000,
                    "state": "available",
                    "volume_type": "l_ssd"
                }
            }
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import (
    Scaleway,
    ScalewayException,
    scaleway_argument_spec,
    SCALEWAY_LOCATION,
)


class ScalewayServerFacts(Scaleway):

    def __init__(self, module):
        super(ScalewayServerFacts, self).__init__(module)
        self.name = 'servers'

        region = module.params["region"]
        self.module.params['api_url'] = SCALEWAY_LOCATION[region]["api_endpoint"]


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(
            ansible_facts={'scaleway_server_facts': ScalewayServerFacts(module).get_resources()}
        )
    except ScalewayException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()
