#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Dimension Data
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   - Aimon Bustardo <aimon.bustardo@dimensiondata.com>
#   - Bert Diwa      <Lamberto.Diwa@dimensiondata.com>
#   - Adam Friedman  <tintoy@tintoy.io>
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: dimensiondata_network
short_description: Create, update, and delete MCP 1.0 & 2.0 networks
extends_documentation_fragment:
  - dimensiondata
  - dimensiondata_wait
description:
  - Create, update, and delete MCP 1.0 & 2.0 networks
version_added: "2.3"
author: 'Aimon Bustardo (@aimonb)'
options:
  name:
    description:
      - The name of the network domain to create.
    required: true
  description:
    description:
      - Additional description of the network domain.
    required: false
  service_plan:
    description:
      - The service plan, either “ESSENTIALS” or “ADVANCED”.
      - MCP 2.0 Only.
    choices: [ESSENTIALS, ADVANCED]
    default: ESSENTIALS
  state:
    description:
      - Should the resource be present or absent.
    choices: [present, absent]
    default: present
'''

EXAMPLES = '''
# Create an MCP 1.0 network
- dimensiondata_network:
    region: na
    location: NA5
    name: mynet
# Create an MCP 2.0 network
- dimensiondata_network:
    region: na
    mcp_user: my_user
    mcp_password: my_password
    location: NA9
    name: mynet
    service_plan: ADVANCED
# Delete a network
- dimensiondata_network:
    region: na
    location: NA1
    name: mynet
    state: absent
'''

RETURN = '''
network:
    description: Dictionary describing the network.
    returned: On success when I(state=present).
    type: dictionary
    contains:
        id:
            description: Network ID.
            type: string
            sample: "8c787000-a000-4050-a215-280893411a7d"
        name:
            description: Network name.
            type: string
            sample: "My network"
        description:
            description: Network description.
            type: string
            sample: "My network description"
        location:
            description: Datacenter location.
            type: string
            sample: NA3
        status:
            description: Network status. (MCP 2.0 only)
            type: string
            sample: NORMAL
        private_net:
            description: Private network subnet. (MCP 1.0 only)
            type: string
            sample: "10.2.3.0"
        multicast:
            description: Multicast enabled? (MCP 1.0 only)
            type: boolean
            sample: false
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dimensiondata import DimensionDataModule, DimensionDataAPIException
from ansible.module_utils.pycompat24 import get_exception
try:
    from libcloud.compute.base import NodeLocation

    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False


class DimensionDataNetworkModule(DimensionDataModule):
    """
    The dimensiondata_network module for Ansible.
    """

    def __init__(self):
        """
        Create a new Dimension Data network module.
        """

        super(DimensionDataNetworkModule, self).__init__(
            module=AnsibleModule(
                argument_spec=DimensionDataModule.argument_spec_with_wait(
                    name=dict(type='str', required=True),
                    description=dict(type='str', required=False),
                    service_plan=dict(default='ESSENTIALS', choices=['ADVANCED', 'ESSENTIALS']),
                    state=dict(default='present', choices=['present', 'absent'])
                ),
                required_together=DimensionDataModule.required_together()
            )
        )

        self.name = self.module.params['name']
        self.description = self.module.params['description']
        self.service_plan = self.module.params['service_plan']
        self.state = self.module.params['state']

    def state_present(self):
        network = self._get_network()

        if network:
            self.module.exit_json(
                changed=False,
                msg='Network already exists',
                network=self._network_to_dict(network)
            )

            return

        network = self._create_network()

        self.module.exit_json(
            changed=True,
            msg='Created network "%s" in datacenter "%s".' % (self.name, self.location),
            network=self._network_to_dict(network)
        )

    def state_absent(self):
        network = self._get_network()

        if not network:
            self.module.exit_json(
                changed=False,
                msg='Network "%s" does not exist' % self.name,
                network=self._network_to_dict(network)
            )

            return

        self._delete_network(network)

    def _get_network(self):
        if self.mcp_version == '1.0':
            networks = self.driver.list_networks(location=self.location)
        else:
            networks = self.driver.ex_list_network_domains(location=self.location)

        matched_network = [network for network in networks if network.name == self.name]
        if matched_network:
            return matched_network[0]

        return None

    def _network_to_dict(self, network):
        network_dict = dict(
            id=network.id,
            name=network.name,
            description=network.description
        )

        if isinstance(network.location, NodeLocation):
            network_dict['location'] = network.location.id
        else:
            network_dict['location'] = network.location

        if self.mcp_version == '1.0':
            network_dict['private_net'] = network.private_net
            network_dict['multicast'] = network.multicast
            network_dict['status'] = None
        else:
            network_dict['private_net'] = None
            network_dict['multicast'] = None
            network_dict['status'] = network.status

        return network_dict

    def _create_network(self):

        # Make sure service_plan argument is defined
        if self.mcp_version == '2.0' and 'service_plan' not in self.module.params:
            self.module.fail_json(
                msg='service_plan required when creating network and location is MCP 2.0'
            )

            return None

        # Create network
        try:
            if self.mcp_version == '1.0':
                network = self.driver.ex_create_network(
                    self.location,
                    self.name,
                    description=self.description
                )
            else:
                network = self.driver.ex_create_network_domain(
                    self.location,
                    self.name,
                    self.module.params['service_plan'],
                    description=self.description
                )
        except DimensionDataAPIException:
            api_exception = get_exception()

            self.module.fail_json(
                msg="Failed to create new network: %s" % str(api_exception)
            )

            return None

        if self.module.params['wait'] is True:
            network = self._wait_for_network_state(network.id, 'NORMAL')

        return network

    def _delete_network(self, network):
        try:
            if self.mcp_version == '1.0':
                deleted = self.driver.ex_delete_network(network)
            else:
                deleted = self.driver.ex_delete_network_domain(network)

            if deleted:
                self.module.exit_json(
                    changed=True,
                    msg="Deleted network with id %s" % network.id
                )

            self.module.fail_json(
                "Unexpected failure deleting network with id %s", network.id
            )

        except DimensionDataAPIException:
            api_exception = get_exception()

            self.module.fail_json(
                msg="Failed to delete network: %s" % str(api_exception)
            )

    def _wait_for_network_state(self, net_id, state_to_wait_for):
        try:
            return self.driver.connection.wait_for_state(
                state_to_wait_for,
                self.driver.ex_get_network_domain,
                self.module.params['wait_poll_interval'],
                self.module.params['wait_time'],
                net_id
            )
        except DimensionDataAPIException:
            api_exception = get_exception()

            self.module.fail_json(
                msg='Network did not reach % state in time: %s' % (state_to_wait_for, api_exception.msg)
            )


def main():
    module = DimensionDataNetworkModule()
    if module.state == 'present':
        module.state_present()
    elif module.state == 'absent':
        module.state_absent()

if __name__ == '__main__':
    main()
