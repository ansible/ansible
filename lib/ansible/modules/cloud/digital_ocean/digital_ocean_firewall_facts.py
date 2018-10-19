#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Anthony Bond <ajbond2005@gmail.com>
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
module: digital_ocean_firewall_facts
short_description: Gather facts about DigitalOcean firewalls
description:
    - This module can be used to gather facts about DigitalOcean firewalls.
author: "Anthony Bond (@BondAnthony)"
version_added: "2.8"
options:
  name:
    description:
     - Firewall rule name that can be used to identify and reference a specific firewall rule.
    required: false
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather facts about all firewalls
  digital_ocean_firewall_facts:
    oauth_token: "{{ oauth_token }}"

- name: Gather facts about a specific firewall by name
  digital_ocean_firewall_facts:
    oauth_token: "{{ oauth_token }}"
    name: "firewall_name"

- name: Gather information from a firewall rule
  digital_ocean_firewall_facts:
    name: SSH
  register: resp_out

- set_fact:
    firewall_id: "{{ resp_out.data.id }}"

- debug:
    msg: "{{ firewall_id }}"
'''


RETURN = '''
data:
    description: DigitalOcean firewall facts
    returned: success
    type: list
    sample: [
        {
            "id": "435tbg678-1db53-32b6-t543-28322569t252",
            "name": "metrics",
            "status": "succeeded",
            "inbound_rules": [
                {
                    "protocol": "tcp",
                    "ports": "9100",
                    "sources": {
                        "addresses": [
                            "1.1.1.1"
                        ]
                    }
                }
            ],
            "outbound_rules": [],
            "created_at": "2018-01-15T07:04:25Z",
            "droplet_ids": [
                87426985
            ],
            "tags": [],
            "pending_changes": []
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    firewall_name = module.params.get('name', None)
    rest = DigitalOceanHelper(module)
    base_url = 'firewalls?'

    response = rest.get("%s" % base_url)
    status_code = response.status_code
    if status_code != 200:
        module.fail_json(msg="Failed to retrieve firewalls from Digital Ocean")
    firewalls = rest.get_paginated_data(base_url=base_url, data_key_name='firewalls')

    if firewall_name is not None:
        rule = {}
        for firewall in firewalls:
            if firewall['name'] == firewall_name:
                rule.update(firewall)
        module.exit_json(changed=False, data=rule)
    else:
        module.exit_json(changed=False, data=firewalls)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
