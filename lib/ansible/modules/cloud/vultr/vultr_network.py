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

DOCUMENTATION = '''
---
module: vultr_network
short_description: Manages networks on Vultr.
description:
  - Manage networks on Vultr. A network cannot be updated. It needs to be deleted and re-created.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
options:
  name:
    description:
      - Name of the network.
    required: true
    aliases: [ description, label ]
  cidr:
    description:
      - The CIDR IPv4 network block to be used when attaching servers to this network. Required if I(state=present).
  region:
    description:
      - Region the network is deployed into. Required if I(state=present).
  state:
    description:
      - State of the network.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = '''
- name: Ensure a network is present
  local_action:
    module: vultr_network
    name: mynet
    cidr: 192.168.42.0/24
    region: Amsterdam

- name: Ensure a network is absent
  local_action:
    module: vultr_network
    name: mynet
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
      type: str
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
      type: str
      sample: "https://api.vultr.com"
vultr_network:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    id:
      description: ID of the network
      returned: success
      type: str
      sample: "net5b62c6dc63ef5"
    name:
      description: Name (label) of the network
      returned: success
      type: str
      sample: "mynetwork"
    date_created:
      description: Date when the network was created
      returned: success
      type: str
      sample: "2018-08-02 08:54:52"
    region:
      description: Region the network was deployed into
      returned: success
      type: str
      sample: "Amsterdam"
    v4_subnet:
      description: IPv4 Network address
      returned: success
      type: str
      sample: "192.168.42.0"
    v4_subnet_mask:
      description: Ipv4 Network mask
      returned: success
      type: int
      sample: 24
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrNetwork(Vultr):

    def __init__(self, module):
        super(AnsibleVultrNetwork, self).__init__(module, "vultr_network")

        self.returns = {
            'NETWORKID': dict(key='id'),
            'DCID': dict(key='region', transform=self._get_region_name),
            'date_created': dict(),
            'description': dict(key='name'),
            'v4_subnet': dict(),
            'v4_subnet_mask': dict(convert_to='int'),
        }

    def _get_region_name(self, region_id=None):
        return self.get_region().get('name')

    def get_network(self):
        networks = self.api_query(path="/v1/network/list")
        if networks:
            for id, network in networks.items():
                if network.get('description') == self.module.params.get('name'):
                    return network
        return {}

    def present_network(self):
        network = self.get_network()
        if not network:
            network = self._create_network(network)
        return network

    def _create_network(self, network):
        self.result['changed'] = True
        data = {
            'description': self.module.params.get('name'),
            'DCID': self.get_region()['DCID'],
            'v4_subnet': self.module.params.get('cidr').split('/')[0],
            'v4_subnet_mask': self.module.params.get('cidr').split('/')[1]
        }
        self.result['diff']['before'] = {}
        self.result['diff']['after'] = data

        if not self.module.check_mode:
            self.api_query(
                path="/v1/network/create",
                method="POST",
                data=data
            )
            network = self.get_network()
        return network

    def absent_network(self):
        network = self.get_network()
        if network:
            self.result['changed'] = True

            data = {
                'NETWORKID': network['NETWORKID'],
            }

            self.result['diff']['before'] = network
            self.result['diff']['after'] = {}

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/network/destroy",
                    method="POST",
                    data=data
                )
        return network


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['description', 'label']),
        cidr=dict(),
        region=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['cidr', 'region']]]
    )

    vultr_network = AnsibleVultrNetwork(module)
    if module.params.get('state') == "absent":
        network = vultr_network.absent_network()
    else:
        network = vultr_network.present_network()

    result = vultr_network.get_result(network)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
