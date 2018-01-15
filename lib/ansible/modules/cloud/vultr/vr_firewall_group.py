#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vr_firewall_group
short_description: Manages firewall groups on Vultr.
description:
  - Create and remove firewall groups.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the firewall group.
    required: true
    aliases: [ description ]
  state:
    description:
      - State of the firewall group.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = '''
- name: ensure a firewall group is present
  local_action:
    module: vr_firewall_group
    name: my http firewall

- name: ensure a firewall group is absent
  local_action:
    module: vr_firewall_group
    name: my http firewall
    state: absent
'''

RETURN = '''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: string
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: string
      sample: "https://api.vultr.com"
vultr_firewall_group:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    id:
      description: ID of the firewall group
      returned: success
      type: string
      sample: 1234abcd
    name:
      description: Name of the firewall group
      returned: success
      type: string
      sample: my firewall group
    date_created:
      description: Date the firewall group was created
      returned: success
      type: string
      sample: "2017-08-26 12:47:48"
    date_modified:
      description: Date the firewall group was modified
      returned: success
      type: string
      sample: "2017-08-26 12:47:48"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrFirewallGroup(Vultr):

    def __init__(self, module):
        super(AnsibleVultrFirewallGroup, self).__init__(module, "vultr_firewall_group")

        self.returns = {
            'FIREWALLGROUPID': dict(key='id'),
            'description': dict(key='name'),
            'date_created': dict(),
            'date_modified': dict(),
        }

    def get_firewall_group(self):
        firewall_groups = self.api_query(path="/v1/firewall/group_list")
        if firewall_groups:
            for firewall_group_id, firewall_group_data in firewall_groups.items():
                if firewall_group_data.get('description') == self.module.params.get('name'):
                    return firewall_group_data
        return {}

    def present_firewall_group(self):
        firewall_group = self.get_firewall_group()
        if not firewall_group:
            firewall_group = self._create_firewall_group(firewall_group)
        return firewall_group

    def _create_firewall_group(self, firewall_group):
        self.result['changed'] = True
        data = {
            'description': self.module.params.get('name'),
        }
        self.result['diff']['before'] = {}
        self.result['diff']['after'] = data

        if not self.module.check_mode:
            self.api_query(
                path="/v1/firewall/group_create",
                method="POST",
                data=data
            )
            firewall_group = self.get_firewall_group()
        return firewall_group

    def absent_firewall_group(self):
        firewall_group = self.get_firewall_group()
        if firewall_group:
            self.result['changed'] = True

            data = {
                'FIREWALLGROUPID': firewall_group['FIREWALLGROUPID'],
            }

            self.result['diff']['before'] = firewall_group
            self.result['diff']['after'] = {}

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/firewall/group_delete",
                    method="POST",
                    data=data
                )
        return firewall_group


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['description']),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vr_firewall_group = AnsibleVultrFirewallGroup(module)
    if module.params.get('state') == "absent":
        firewall_group = vr_firewall_group.absent_firewall_group()
    else:
        firewall_group = vr_firewall_group.present_firewall_group()

    result = vr_firewall_group.get_result(firewall_group)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
