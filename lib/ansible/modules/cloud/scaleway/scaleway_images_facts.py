#!/usr/bin/python
#
# Scaleway images facts module
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
module: scaleway_images_facts
short_description: Scaleway image facts module
version_added: "2.7"
author: Remy Leone (@sieben)
description:
    - "This module gather facts about images on Scaleway."
extends_documentation_fragment: scaleway
options:

  name:
    description:
      - Name of the instance
    required: true

  region:
    description:
    - Scaleway compute zone
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1

  commercial_type:
    description:
    - Commercial name of the compute node
    required: true
    choices:
      - ARM64-2GB
      - ARM64-4GB
      - ARM64-8GB
      - ARM64-16GB
      - ARM64-32GB
      - ARM64-64GB
      - ARM64-128GB
      - C1
      - C2S
      - C2M
      - C2L
      - START1-XS
      - START1-S
      - START1-M
      - START1-L
      - X64-15GB
      - X64-30GB
      - X64-60GB
      - X64-120GB
'''

EXAMPLES = '''
- name: Get image information
  scaleway_images_facts:
    name: Ubuntu Bionic
    region: par1
    commercial_type: START1-S
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "scaleway_images": [
            {
                "arch": "x86_64",
                "creation_date": "2018-07-26T13:00:02.726274+00:00",
                "default_bootscript": {
                    "architecture": "x86_64",
                    "bootcmdargs": "LINUX_COMMON scaleway boot=local nbd.max_part=16",
                    "default": false,
                    "dtb": "",
                    "id": "54ee2857-8ffb-4323-abba-964f55fea4a2",
                    "initrd": "http://169.254.42.24/initrd/initrd-Linux-x86_64-v3.14.5.gz",
                    "kernel": "http://169.254.42.24/kernel/x86_64-mainline-lts-4.9-4.9.93-rev1/vmlinuz-4.9.93",
                    "organization": "11111111-1111-4111-8111-111111111111",
                    "public": true,
                    "title": "x86_64 mainline 4.9.93 rev1"
                },
                "extra_volumes": [],
                "from_server": null,
                "id": "67dcb730-fc17-421c-a328-f67438c74bd6",
                "modification_date": "2018-07-26T13:00:02.726274+00:00",
                "name": "Ubuntu Bionic Beaver",
                "organization": "51b656e3-4865-41e8-adbc-0c45bdd780db",
                "public": true,
                "root_volume": {
                    "id": "2fef7fe5-7201-487d-9cc1-058b2e6e9a12",
                    "name": "snapshot-ea04f81d-b0bd-499f-b23a-887d01f14eb6-2018-07-25_21:28",
                    "size": 50000000000,
                    "volume_type": "l_ssd"
                },
                "state": "available"
            }
        ]
    }
'''

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.scaleway import ScalewayAPI, SCALEWAY_LOCATION, SCALEWAY_COMMERCIAL_TYPES_ARCH_MAPPING
from ansible.module_utils.six.moves.urllib.parse import urlencode


def core(module):
    api_token = module.params['oauth_token']
    region = module.params["region"]
    name = module.params["name"]
    arch = SCALEWAY_COMMERCIAL_TYPES_ARCH_MAPPING[module.params["commercial_type"]]

    compute_api = ScalewayAPI(module=module,
                              headers={'X-Auth-Token': api_token},
                              base_url=SCALEWAY_LOCATION[region]["api_endpoint"])

    response = compute_api.get("images?%s" % urlencode({"arch": arch, "name": name}))
    status_code = response.status_code

    if not response.ok:
        module.fail_json(msg='Error fetching facts [{0}: {1}]'.format(
            status_code, response.json['message']))

    images = response.json["images"]
    module.exit_json(changed=False, scaleway_images=images)


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
            name=dict(required=True),
            region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
            commercial_type=dict(required=True, choices=SCALEWAY_COMMERCIAL_TYPES_ARCH_MAPPING.keys()),
            timeout=dict(type="int", default=30),
            validate_certs=dict(default=True, type='bool'),
        ),
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
