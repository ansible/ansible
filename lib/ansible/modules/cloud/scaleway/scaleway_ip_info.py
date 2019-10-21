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
module: scaleway_ip_info
short_description: Gather information about the Scaleway ips available.
description:
  - Gather information about the Scaleway ips available.
version_added: "2.9"
author:
  - "Yanis Guenane (@Spredzy)"
  - "Remy Leone (@sieben)"
extends_documentation_fragment: scaleway
options:
  region:
    description:
      - Scaleway region to use (for example C(par1)).
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1
'''

EXAMPLES = r'''
- name: Gather Scaleway ips information
  scaleway_ip_info:
    region: par1
  register: result

- debug:
    msg: "{{ result.scaleway_ip_info }}"
'''

RETURN = r'''
---
scaleway_ip_info:
  description: Response from Scaleway API
  returned: success
  type: complex
  sample:
    "scaleway_ip_info": [
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
    Scaleway,
    ScalewayException,
    scaleway_argument_spec,
    SCALEWAY_LOCATION,
)


class ScalewayIpInfo(Scaleway):

    def __init__(self, module):
        super(ScalewayIpInfo, self).__init__(module)
        self.name = 'ips'

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
            scaleway_ip_info=ScalewayIpInfo(module).get_resources()
        )
    except ScalewayException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()
