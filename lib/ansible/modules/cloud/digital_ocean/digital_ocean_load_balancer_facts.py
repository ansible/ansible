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
module: digital_ocean_load_balancer_facts
short_description: Gather facts about DigitalOcean load balancers
description:
    - This module can be used to gather facts about DigitalOcean provided load balancers.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
options:
  load_balancer_id:
    description:
     - Load balancer ID that can be used to identify and reference a load_balancer.
    required: false
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather facts about all load balancers
  digital_ocean_load_balancer_facts:
    oauth_token: "{{ oauth_token }}"

- name: Gather facts about load balancer with given id
  digital_ocean_load_balancer_facts:
    oauth_token: "{{ oauth_token }}"
    load_balancer_id: "4de7ac8b-495b-4884-9a69-1050c6793cd6"

- name: Get name from load balancer id
  digital_ocean_load_balancer_facts:
  register: resp_out
- set_fact:
    load_balancer_name: "{{ item.name }}"
  loop: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?id=='4de7ac8b-495b-4884-9a69-1050c6793cd6']"
- debug: var=load_balancer_name
'''


RETURN = '''
data:
    description: DigitalOcean Load balancer facts
    returned: success
    type: list
    sample: [
        {
          "id": "4de7ac8b-495b-4884-9a69-1050c6793cd6",
          "name": "example-lb-01",
          "ip": "104.131.186.241",
          "algorithm": "round_robin",
          "status": "new",
          "created_at": "2017-02-01T22:22:58Z",
          ...
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    load_balancer_id = module.params.get('load_balancer_id', None)
    rest = DigitalOceanHelper(module)

    base_url = 'load_balancers?'
    if load_balancer_id is not None:
        response = rest.get("%s/%s" % (base_url, load_balancer_id))
        status_code = response.status_code

        if status_code != 200:
            module.fail_json(msg="Failed to retrieve load balancers for DigitalOcean")

        resp_json = response.json
        load_balancer = resp_json['load_balancer']
    else:
        load_balancer = rest.get_paginated_data(base_url=base_url, data_key_name='load_balancers')

    module.exit_json(changed=False, data=load_balancer)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        load_balancer_id=dict(type='str', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
