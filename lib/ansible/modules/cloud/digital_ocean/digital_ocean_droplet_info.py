#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
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
module: digital_ocean_droplet_info
short_description: Gather information about DigitalOcean droplets
description:
    - This module can be used to gather information about droplets
author: "Ken Celenza (@itdependsnetworks)"
version_added: "2.10"

requirements:
  - "python >= 2.6"

options:
  name:
    description:
     - The name of the droplet.
    required: false
    type: str
  id:
    description:
     - The id of the droplet.
    required: false
    type: int
  all:
    description:
     - Whether or not you want to get all droplet information.
    required: false
    type: bool
extends_documentation_fragment: digital_ocean.documentation
'''

EXAMPLES = '''
- name: Gather information about droplet by name
  digital_ocean_droplet_info:
    oauth_token: "{{ oauth_token }}"
    name: "ntc_tower_server"

- name: Gather information about droplet by id
  digital_ocean_droplet_info:
    oauth_token: "{{ oauth_token }}"
    id: "185585000"

- name: Gather information about all droplets
  digital_ocean_droplet_info:
    oauth_token: "{{ oauth_token }}"
    all: "yes"
'''


RETURN = '''
data:
    description: DigitalOcean droplet information
    returned: success
    type: list
    sample:
      - droplet:
          backup_ids: []
          created_at: '2020-03-20T20:10:50Z'
          disk: 320
          features: []
          id: 185580000
          image:
            created_at: '2020-03-10T00:07:26Z'
            distribution: Ubuntu
            id: 60380000
            min_disk_size: 320
            name: ntc-tower-09T23:52:42Z
            public: false
            regions:
            - nyc1
            - nyc3
            size_gigabytes: 7.37
            slug:
            status: available
            tags: []
            type: snapshot
          kernel:
          locked: false
          memory: 16384
          name: ntc-tower
          networks:
            v4:
            - gateway: 167.71.240.1
              ip_address: 167.71.240.2
              netmask: 255.255.240.0
              type: public
            v6: []
          next_backup_window:
          region:
            available: true
            features:
            - private_networking
            - backups
            - ipv6
            - metadata
            - install_agent
            - storage
            - image_transfer
            name: New York 3
            sizes:
            - s-1vcpu-1gb
            - 512mb
            - s-1vcpu-2gb
            - 1gb
            - s-3vcpu-1gb
            - s-2vcpu-2gb
            - s-1vcpu-3gb
            - s-2vcpu-4gb
            - 2gb
            - s-4vcpu-8gb
            - m-1vcpu-8gb
            - c-2
            - 4gb
            - g-2vcpu-8gb
            - gd-2vcpu-8gb
            - m-16gb
            - s-6vcpu-16gb
            - c-4
            - 8gb
            - m-2vcpu-16gb
            - m3-2vcpu-16gb
            - g-4vcpu-16gb
            - gd-4vcpu-16gb
            - m6-2vcpu-16gb
            - m-32gb
            - s-8vcpu-32gb
            - c-8
            - 16gb
            - m-4vcpu-32gb
            - m3-4vcpu-32gb
            - g-8vcpu-32gb
            - s-12vcpu-48gb
            - gd-8vcpu-32gb
            - m6-4vcpu-32gb
            - m-64gb
            - s-16vcpu-64gb
            - c-16
            - 32gb
            - m-8vcpu-64gb
            - m3-8vcpu-64gb
            - g-16vcpu-64gb
            - s-20vcpu-96gb
            - 48gb
            - gd-16vcpu-64gb
            - m6-8vcpu-64gb
            - m-128gb
            - s-24vcpu-128gb
            - 64gb
            - m-16vcpu-128gb
            - m3-16vcpu-128gb
            - g-32vcpu-128gb
            - s-32vcpu-192gb
            - m-24vcpu-192gb
            - m-224gb
            - m6-16vcpu-128gb
            - m3-24vcpu-192gb
            - m6-24vcpu-192gb
            slug: nyc3
          size:
            available: true
            disk: 320
            memory: 16384
            price_hourly: 0.11905
            price_monthly: 80
            regions:
            - ams2
            - ams3
            - blr1
            - fra1
            - lon1
            - nyc1
            - nyc2
            - nyc3
            - sfo1
            - sfo2
            - sgp1
            - tor1
            slug: s-6vcpu-16gb
            transfer: 6
            vcpus: 6
          size_slug: s-6vcpu-16gb
          snapshot_ids: []
          status: active
          tags: []
          vcpus: 6
          volume_ids: []
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native

class DODroplet(object):
    def __init__(self, module):
        self.rest = DigitalOceanHelper(module)
        self.module = module
        # pop the oauth token so we don't include it in the POST data
        self.module.params.pop('oauth_token')

    def get_all(self):
        data = []
        page = 1
        while page is not None:
            response = self.rest.get('droplets?page={0}'.format(page))
            if response.status_code == 200:
                json_data = response.json['droplets']
                data.extend(json_data)
                if 'links' in json_data and 'pages' in json_data['links'] and 'next' in json_data['links']['pages']:
                    page += 1
                else:
                    page = None
        return data

    def get_by_id(self, droplet_id):
        if not droplet_id:
            return None
        response = self.rest.get('droplets/{0}'.format(droplet_id))
        json_data = response.json
        if response.status_code == 200:
            return [json_data]
        return None

    def get_by_name(self, droplet_name):
        if not droplet_name:
            return None
        json_data = self.get_all()
        for droplet in json_data:
            if droplet['name'] == droplet_name:
                return [droplet]
        return None

def core(module):
    droplet = DODroplet(module)
    if module.params.get('id'):
        data = droplet.get_by_id(module.params.get('id'))
    elif module.params.get('name'):
        data = droplet.get_by_name(module.params.get('name'))
    elif module.params.get('all'):
        data = droplet.get_all()
    if not data:
        module.fail_json(msg="Failed to find the droplet")
    module.exit_json(changed=False, data=data)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str'),
            id=dict(aliases=['droplet_id'], type='int'),
            all=dict(type='bool', default=False),
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(['id', 'name', 'all'],),
        mutually_exclusive=[['id', 'name', 'all']],
        supports_check_mode=False,
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())

if __name__ == '__main__':
    main()
