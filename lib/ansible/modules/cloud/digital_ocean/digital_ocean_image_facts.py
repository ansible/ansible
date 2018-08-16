#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: digital_ocean_image_facts
short_description: Gather facts about DigitalOcean images
description:
    - This module can be used to gather facts about DigitalOcean provided images.
    - These images can be either of type C(distribution), C(application) and C(private).
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
options:
  image_type:
    description:
     - Specifies the type of image facts to be retrived.
     - If set to C(application), then facts are gathered related to all application images.
     - If set to C(distribution), then facts are gathered related to all distribution images.
     - If set to C(private), then facts are gathered related to all private images.
     - If not set to any of above, then facts are gathered related to all images.
    default: 'all'
    choices: [ 'all', 'application', 'distribution', 'private' ]
    required: false
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather facts about all images
  digital_ocean_image_facts:
    image_type: all
    oauth_token: "{{ oauth_token }}"

- name: Gather facts about application images
  digital_ocean_image_facts:
    image_type: application
    oauth_token: "{{ oauth_token }}"

- name: Gather facts about distribution images
  digital_ocean_image_facts:
    image_type: distribution
    oauth_token: "{{ oauth_token }}"

- name: Get distribution about image with slug coreos-beta
  digital_ocean_image_facts:
  register: resp_out
- set_fact:
    distribution_name: "{{ item.distribution }}"
  with_items: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?slug=='coreos-beta']"
- debug: var=distribution_name

'''


RETURN = '''
data:
    description: DigitalOcean image facts
    returned: success
    type: list
    sample: [
        {
            "created_at": "2018-02-02T07:11:43Z",
            "distribution": "CoreOS",
            "id": 31434061,
            "min_disk_size": 20,
            "name": "1662.1.0 (beta)",
            "public": true,
            "regions": [
                "nyc1",
                "sfo1",
                "nyc2",
                "ams2",
                "sgp1",
                "lon1",
                "nyc3",
                "ams3",
                "fra1",
                "tor1",
                "sfo2",
                "blr1"
            ],
            "size_gigabytes": 0.42,
            "slug": "coreos-beta",
            "type": "snapshot"
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    image_type = module.params['image_type']

    rest = DigitalOceanHelper(module)

    base_url = 'images?'
    if image_type == 'distribution':
        base_url += "type=distribution&"
    elif image_type == 'application':
        base_url += "type=application&"
    elif image_type == 'private':
        base_url += "private=true&"

    images = rest.get_paginated_data(base_url=base_url, data_key_name='images')

    module.exit_json(changed=False, data=images)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        image_type=dict(type='str',
                        required=False,
                        choices=['all', 'application', 'distribution', 'private'],
                        default='all'
                        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
