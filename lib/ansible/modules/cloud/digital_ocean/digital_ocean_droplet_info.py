#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: digital_ocean_droplet_info
short_description: Gather information about DigitalOcean droplets
description:
  - This module can be used to gather information about DigitalOcean droplets.
version_added: "2.10"
options:
  droplet_id:
    description:
     - Droplet ID that can be used to identify and reference a droplet.
    required: false
    type: int
  tag_name:
    description:
     - Tag name that can be used to filter droplets by a tag.
    required: false
    type: str
author: "Nicolas Boutet (@boutetnico)"
extends_documentation_fragment: digital_ocean.documentation
notes:
  - Version 2 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: Gather information about all droplets
  digital_ocean_droplet_info:
    oauth_token: "{{ my_do_key }}"

- name: Gather information about a droplet with given id
  digital_ocean_droplet_info:
    oauth_token: "{{ my_do_key }}"
    droplet_id: 3164444

- name: Gather information about droplets having a given tag
  digital_ocean_droplet_info:
    oauth_token: "{{ my_do_key }}"
    tag_name: "staging"
'''


RETURN = '''
# Digital Ocean API info https://developers.digitalocean.com/documentation/v2/#list-all-droplets
data:
    description: List of droplets on DigitalOcean
    returned: success and no resource constraint
    type: dict
    sample: [
      {
        "id": 3164444,
        "name": "example.com",
        "memory": 1024,
        "vcpus": 1,
        "disk": 25,
        "locked": false,
        "status": "active",
        "kernel": {
          "id": 2233,
          "name": "Ubuntu 14.04 x64 vmlinuz-3.13.0-37-generic",
          "version": "3.13.0-37-generic"
        },
        "created_at": "2014-11-14T16:29:21Z",
        "features": [
          "backups",
          "ipv6",
          "virtio"
        ],
        "backup_ids": [
          7938002
        ],
        "snapshot_ids": [

        ],
        "image": {
          "id": 6918990,
          "name": "14.04 x64",
          "distribution": "Ubuntu",
          "slug": "ubuntu-16-04-x64",
          "public": true,
          "regions": [
            "nyc1",
            "ams1",
            "sfo1",
            "nyc2",
            "ams2",
            "sgp1",
            "lon1",
            "nyc3",
            "ams3",
            "nyc3"
          ],
          "created_at": "2014-10-17T20:24:33Z",
          "type": "snapshot",
          "min_disk_size": 20,
          "size_gigabytes": 2.34
        },
        "volume_ids": [

        ],
        "size": {
        },
        "size_slug": "s-1vcpu-1gb",
        "networks": {
          "v4": [
            {
              "ip_address": "104.236.32.182",
              "netmask": "255.255.192.0",
              "gateway": "104.236.0.1",
              "type": "public"
            }
          ],
          "v6": [
            {
              "ip_address": "2604:A880:0800:0010:0000:0000:02DD:4001",
              "netmask": 64,
              "gateway": "2604:A880:0800:0010:0000:0000:0000:0001",
              "type": "public"
            }
          ]
        },
        "region": {
          "name": "New York 3",
          "slug": "nyc3",
          "sizes": [

          ],
          "features": [
            "virtio",
            "private_networking",
            "backups",
            "ipv6",
            "metadata"
          ],
          "available": null
        },
        "tags": [

        ]
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper


def core(module):
    droplet_id = module.params.get('droplet_id', None)
    tag_name = module.params.get('tag_name', None)
    rest = DigitalOceanHelper(module)

    base_url = 'droplets'
    if droplet_id is not None:
        response = rest.get("%s/%s" % (base_url, droplet_id))
        status_code = response.status_code

        if status_code != 200:
            module.fail_json(msg='Error fetching droplet information [{0}: {1}]'.format(
                status_code, response.json['message'])
            )

        resp_json = response.json
        droplets = [resp_json['droplet']]
    elif tag_name is not None:
        base_url = "{0}?tag_name={1}&".format(base_url, tag_name)
        droplets = rest.get_paginated_data(base_url=base_url, data_key_name='droplets')
    else:
        droplets = rest.get_paginated_data(base_url=base_url + '?', data_key_name='droplets')

    module.exit_json(changed=False, data=droplets)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        droplet_id=dict(type='int', required=False),
        tag_name=dict(type='str', required=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(
            ['droplet_id', 'tag_name'],
        ),
    )

    core(module)


if __name__ == '__main__':
    main()
