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
module: digital_ocean_tag_facts
short_description: Gather facts about DigitalOcean tags
description:
    - This module can be used to gather facts about DigitalOcean provided tags.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
options:
  tag_name:
    description:
     - Tag name that can be used to identify and reference a tag.
    required: false
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather facts about all tags
  digital_ocean_tag_facts:
    oauth_token: "{{ oauth_token }}"

- name: Gather facts about tag with given name
  digital_ocean_tag_facts:
    oauth_token: "{{ oauth_token }}"
    tag_name: "extra_awesome_tag"

- name: Get resources from tag name
  digital_ocean_tag_facts:
  register: resp_out
- set_fact:
    resources: "{{ item.resources }}"
  loop: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?name=='extra_awesome_tag']"
- debug: var=resources
'''


RETURN = '''
data:
    description: DigitalOcean tag facts
    returned: success
    type: list
    sample: [
        {
            "name": "extra-awesome",
            "resources": {
            "droplets": {
                "count": 1,
                ...
                }
            }
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    tag_name = module.params.get('tag_name', None)
    rest = DigitalOceanHelper(module)

    base_url = 'tags?'
    if tag_name is not None:
        response = rest.get("%s/%s" % (base_url, tag_name))
        status_code = response.status_code

        if status_code != 200:
            module.fail_json(msg="Failed to retrieve tags for DigitalOcean")

        resp_json = response.json
        tag = resp_json['tag']
    else:
        tag = rest.get_paginated_data(base_url=base_url, data_key_name='tags')

    module.exit_json(changed=False, data=tag)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        tag_name=dict(type='str', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
