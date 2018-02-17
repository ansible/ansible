#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (C) 2017-18, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: digital_ocean_floating_ip_facts
short_description: DigitalOcean Floating IPs facts
description:
     - This module can be used to fetch DigitalOcean Floating IPs facts.
version_added: "2.5"
author: "Patrick Marques (@pmarques)"
extends_documentation_fragment: digital_ocean.documentation
notes:
  - Version 2 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: "Gather facts about all Floating IPs"
  digital_ocean_floating_ip_facts:
  register: result

- name: "List of current floating ips"
  debug: var=result.floating_ips
'''


RETURN = '''
# Digital Ocean API info https://developers.digitalocean.com/documentation/v2/#floating-ips
floating_ips:
    description: a DigitalOcean Floating IP resource
    returned: success and no resource constraint
    type: list
    sample: [
      {
        "ip": "45.55.96.47",
        "droplet": null,
        "region": {
          "name": "New York 3",
          "slug": "nyc3",
          "sizes": [
            "512mb",
            "1gb",
            "2gb",
            "4gb",
            "8gb",
            "16gb",
            "32gb",
            "48gb",
            "64gb"
          ],
          "features": [
            "private_networking",
            "backups",
            "ipv6",
            "metadata"
          ],
          "available": true
        },
        "locked": false
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    rest = DigitalOceanHelper(module)

    page = 1
    has_next = True
    floating_ips = []
    status_code = None
    while has_next or status_code != 200:
        response = rest.get("floating_ips?page={0}&per_page=20".format(page))
        status_code = response.status_code
        # stop if any error during pagination
        if status_code != 200:
            break
        page += 1
        floating_ips.extend(response.json["floating_ips"])
        has_next = "pages" in response.json["links"] and "next" in response.json["links"]["pages"]

    if status_code == 200:
        module.exit_json(changed=False, floating_ips=floating_ips)
    else:
        module.fail_json(msg="Error fetching facts [{0}: {1}]".format(
            status_code, response.json["message"]))


def main():
    module = AnsibleModule(
        argument_spec=DigitalOceanHelper.digital_ocean_argument_spec()
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
