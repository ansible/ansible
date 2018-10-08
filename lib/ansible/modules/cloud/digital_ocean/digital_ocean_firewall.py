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
module: digital_ocean_firewall
short_description: Manage cloud firewalls within Digital Ocean
description:
    - This module can be used to add or remove firewalls on the Digital Ocean cloud platform.
author: "Anthony Bond (@BondAnthony)"
version_added: "2.8"
options:
  name:
    description:
     - Name of the firewall rule to create or manage
    required: true
  state:
    description:
      - Assert the state of the firewall rule. Set to 'present' to create or update and 'absent' to remove.
    default: present
    choices: ['present', 'absent']
  droplet_ids:
    description:
     - List of droplet ids to be assigned to the firewall
    required: false
    type: list
  tags:
    description:
      - List of tags to be assigned to the firewall
    required: false
    type: list
  inbound_rules:
    description:
      - Firewall rules specifically targeting inbound network traffic into Digital Ocean
    required: true
    type: list
    suboptions:
      protocol:
        description:
          - Network protocol to be accepted.
        required: true
        choices: ['udp', 'tcp', 'icmp']
      ports:
        description:
          - The ports on which traffic will be allowed, single, range, or all
        required: true
      sources:
        description:
          - Dictionary of locations from which inbound traffic will be accepted
        required: true
        suboptions:
          addresses:
            description:
              - List of strings containing the IPv4 addresses, IPv6 addresses, IPv4 CIDRs,
                and/or IPv6 CIDRs to which the firewall will allow traffic
            required: false
          droplet_ids:
            description:
              - List of integers containing the IDs of the Droplets to which the firewall will allow traffic
            required: false
          load_balancer_uids:
            description:
              - List of strings containing the IDs of the Load Balancers to which the firewall will allow traffic
            required: false
          tags:
            description:
              - List of strings containing the names of Tags corresponding to groups of Droplets to
                which the Firewall will allow traffic
            required: false
  outbound_rules:
    description:
      - Firewall rules specifically targeting outbound network traffic from Digital Ocean
    required: true
    type: list
    suboptions:
      protocol:
        description:
          - Network protocol to be accepted.
        required: true
        choices: ['udp', 'tcp', 'icmp']
      ports:
        description:
          - The ports on which traffic will be allowed, single, range, or all
        required: true
      destinations:
        description:
          - Dictionary of locations from which outbound traffic will be allowed
        required: true
        suboptions:
          addresses:
            description:
              - List of strings containing the IPv4 addresses, IPv6 addresses, IPv4 CIDRs,
                and/or IPv6 CIDRs to which the firewall will allow traffic
            required: false
          droplet_ids:
            description:
              - List of integers containing the IDs of the Droplets to which the firewall will allow traffic
            required: false
          load_balancer_uids:
            description:
              - List of strings containing the IDs of the Load Balancers to which the firewall will allow traffic
            required: false
          tags:
            description:
              - List of strings containing the names of Tags corresponding to groups of Droplets to
                which the Firewall will allow traffic
            required: false
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''

EXAMPLES = '''
- name: Create Firewall
  digital_ocean_firewall:
    name: nginx
    state: present
    inbound_rules:
      protocol:
      ports:
      sources:
        addresses:
        droplet_ids:
        load_balancer_uids:
        tags:
    outbound_rules:
      protocol:
      ports:
      sources:
        addresses:
        droplet_ids:
        load_balancer_uids:
        tags:
    droplet_ids:
    tags:
'''

RETURN = '''
data:
    description: DigitalOcean firewall resource
    returned: success
    type: dict
    sample: {
        "created_at": "2018-10-14T18:41:30Z",
        "droplet_ids": [],
        "id": "7acd6ee2-257b-434f-8909-709a5816d4f9",
        "inbound_rules": [
            {
                "ports": "443",
                "protocol": "tcp",
                "sources": {
                    "addresses": [
                        "1.1.1.1",
                        "2.2.2.2"
                    ]
                }
            }
        ],
        "name": "web",
        "outbound_rules": [
            {
                "destinations": {
                    "addresses": [
                        "1.1.1.1"
                    ],
                    "tags": [
                        "proxies"
                    ]
                },
                "ports": "443",
                "protocol": "tcp"
            }
        ],
        "pending_changes": [],
        "status": "succeeded",
        "tags": []
    }
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native

address_spec = dict(
    addresses=dict(type='list', required=False),
    droplet_ids=dict(type='list', required=False),
    load_balancer_uids=dict(type='list', required=False),
    tags=dict(type='list', required=False),
)

inbound_spec = dict(
    protocol=dict(type='str', choices=['udp', 'tcp', 'icmp'], default='tcp'),
    ports=dict(type='str', required=True),
    sources=dict(type='dict', required=True, elements='dict', options=address_spec),
)

outbound_spec = dict(
    protocol=dict(type='str', choices=['udp', 'tcp', 'icmp'], default='tcp'),
    ports=dict(type='str', required=True),
    destinations=dict(type='dict', required=True, elements='dict', options=address_spec),
)


class DOFirewall(object):
    def __init__(self, module):
        self.rest = DigitalOceanHelper(module)
        self.module = module
        self.name = self.module.params.get('name')
        self.baseurl = 'firewalls'
        self.firewalls = self.get_firewalls()

    def get_firewalls(self):
        base_url = self.baseurl + "?"
        response = self.rest.get("%s" % base_url)
        status_code = response.status_code
        if status_code != 200:
            self.module.fail_json(msg="Failed to retrieve firewalls from Digital Ocean")
        return self.rest.get_paginated_data(base_url=base_url, data_key_name='firewalls')

    def get_firewall_by_name(self):
        rule = {}
        for firewall in self.firewalls:
            if firewall['name'] == self.name:
                rule.update(firewall)
                return rule
        return None

    def create(self):
        rule = self.get_firewall_by_name()
        data = {
            "name": self.module.params.get('name'),
            "inbound_rules": self.module.params.get('inbound_rules'),
            "outbound_rules": self.module.params.get('outbound_rules'),
            "droplet_ids": self.module.params.get('droplet_ids'),
            "tags": self.module.params.get('tags')
        }
        if rule is None:
            resp = self.rest.post(path=self.baseurl, data=data)
            status_code = resp.status_code
            if status_code != 202:
                self.module.fail_json(msg=resp.json)
            self.module.exit_json(changed=True, data=resp.json['firewall'])
        else:
            # #TODO: Check existing rule against user input
            self.module.exit_json(changed=False, data=rule)

    def destroy(self):
        rule = self.get_firewall_by_name()
        if rule is None:
            self.module.exit_json(changed=False, data="Firewall does not exist")
        else:
            endpoint = self.baseurl + '/' + rule['id']
            resp = self.rest.delete(path=endpoint)
            status_code = resp.status_code
            if status_code != 204:
                self.module.fail_json(msg="Failed to delete firewall")
            self.module.exit_json(changed=True, data="Deleted firewall rule: {0} - {1}".format(rule['name'], rule['id']))


def core(module):
    state = module.params.get('state')
    firewall = DOFirewall(module)

    if state == 'present':
        firewall.create()
    elif state == 'absent':
        firewall.destroy()


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        droplet_ids=dict(type='list', required=False),
        tags=dict(type='list', required=False),
        inbound_rules=dict(type='list', required=True, elements='dict', options=inbound_spec),
        outbound_rules=dict(type='list', required=True, elements='dict', options=outbound_spec),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
