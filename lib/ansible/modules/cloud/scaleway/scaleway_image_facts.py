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
module: scaleway_image_facts
short_description: Gather facts about the Scaleway images available.
description:
  - Gather facts about the Scaleway images available.
version_added: "2.7"
author:
  - "Yanis Guenane (@Spredzy)"
  - "Remy Leone (@sieben)"
extends_documentation_fragment: scaleway

options:

  region:
    version_added: "2.7"
    description:
    - Scaleway compute zone
    required: true
  name:
    version_added: "2.8"
    description: Name of the image
  architecture:
    version_added: "2.8"
    description: Architecture of the instance
    choices:
      - x86_64
      - arm
  most_recent:
    version_added: "2.8"
    description: Return most recent image if multiple exist.
'''

EXAMPLES = r'''
- name: Get the most recent image for an Ubuntu Bionic on architecture x86_64 in Paris (fr-par-1)
  scaleway_image_facts:
    region: fr-par-1
    most_recent: yes
    name: Ubuntu Bionic
    architecture: x86_64
'''

RETURN = r'''
---
scaleway_image_facts:
  description: Response from Scaleway API
  returned: success
  type: complex
  contains:
    "scaleway_image_facts": [
        {
           "arch": "x86_64",
           "creation_date": "2018-07-17T16:18:49.276456+00:00",
           "default_bootscript": {
               "architecture": "x86_64",
               "bootcmdargs": "LINUX_COMMON scaleway boot=local nbd.max_part=16",
               "default": false,
               "dtb": "",
               "id": "15fbd2f7-a0f9-412b-8502-6a44da8d98b8",
               "initrd": "http://169.254.42.24/initrd/initrd-Linux-x86_64-v3.14.5.gz",
               "kernel": "http://169.254.42.24/kernel/x86_64-mainline-lts-4.9-4.9.93-rev1/vmlinuz-4.9.93",
               "organization": "11111111-1111-4111-8111-111111111111",
               "public": true,
               "title": "x86_64 mainline 4.9.93 rev1"
           },
           "extra_volumes": [],
           "from_server": null,
           "id": "00ae4a88-3252-4eda-9feb-5f6b56bf5ef0",
           "modification_date": "2018-07-17T16:42:06.319315+00:00",
           "name": "Debian Stretch",
           "organization": "51b656e3-4865-41e8-adbc-0c45bdd780db",
           "public": true,
           "root_volume": {
               "id": "da32dfbb-c5ff-476d-ae2d-c297dd09b7dd",
               "name": "snapshot-2a7229dc-d431-4dc5-b66e-95db08b773af-2018-07-17_16:18",
               "size": 25000000000,
               "volume_type": "l_ssd"
           },
           "state": "available"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import (
    Scaleway, ScalewayException, scaleway_argument_spec, SCALEWAY_LOCATION)


class ScalewayImageFacts(Scaleway):

    def __init__(self, module):
        super(ScalewayImageFacts, self).__init__(module)
        self.name = 'images'

        region = module.params["region"]
        self.module.params['api_url'] = SCALEWAY_LOCATION[region]["api_endpoint"]


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
        name=dict(),
        architecture=dict(choices=["arm", "x86_64"]),
        most_recent=dict(type="bool", default=False)
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    params = {}
    if module.params["architecture"]:
        params["arch"] = module.params["architecture"]

    if module.params["name"]:
        params["name"] = module.params["name"]

    if module.params["most_recent"]:
        params["only_current"] = 1

    try:
        module.exit_json(
            changed=False,
            ansible_facts={'scaleway_image_facts': ScalewayImageFacts(module).get_resources(params=params)}
        )
    except ScalewayException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()
