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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'version': '1.0'
}

DOCUMENTATION = '''
---
module: dimensiondata_network
short_description: Create, update, and delete MCP 1.0 & 2.0 networks
description:
  - Create, update, and delete MCP 1.0 & 2.0 networks
version_added: "2.3"
author: 'Aimon Bustardo (@aimonb)'
options:
  region:
    description:
      - The target region.
    choices:
      - Regions are defined in Apache libcloud project [libcloud/common/dimensiondata.py]
      - They are also listed in U(https://libcloud.readthedocs.io/en/latest/compute/drivers/dimensiondata.html)
      - Note that the default value "na" stands for "North America".
      - The module prepends 'dd-' to the region choice.
    default: na
  mcp_user:
    description:
      - The username used to authenticate to the CloudControl API.
      - If not specified, will fall back to C(MCP_USER) from environment variable or C(~/.dimensiondata).
    required: false
  mcp_password:
    description:
      - The password used to authenticate to the CloudControl API.
      - If not specified, will fall back to C(MCP_PASSWORD) from environment variable or C(~/.dimensiondata).
      - Required if I(mcp_user) is specified.
    required: false
  location:
    description:
      - The target datacenter.
    required: true
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
    default: ADVANCED
  verify_ssl_cert:
    description:
      - Check that SSL certificate is valid.
    required: false
    default: true
  wait:
    description:
      - Should we wait for the task to complete before moving onto the next.
    required: false
    default: false
  wait_time:
    description:
      - Only applicable if wait is true. This is the amount of time in seconds to wait
    required: false
    default: 600
  wait_poll_interval:
    description:
      - The length of time between successive polls for completion
    required: false
    default: 2
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
    returned: On success when I(state) is 'present'
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
                argument_spec=dict(
                    region=dict(type='str', default='na'),
                    mcp_user=dict(type='str', required=False),
                    mcp_password=dict(type='str', required=False, no_log=True),
                    location=dict(type='str', required=True),
                    name=dict(type='str', required=True),
                    description=dict(type='str', required=False),
                    service_plan=dict(default='ADVANCED', choices=['ADVANCED', 'ESSENTIALS']),
                    state=dict(default='present', choices=['present', 'absent']),
                    wait=dict(type='bool', required=False, default=False),
                    wait_time=dict(type='int', required=False, default=600),
                    wait_poll_interval=dict(type='int', required=False, default=2),
                    verify_ssl_cert=dict(type='bool', required=False, default=True)
                ),
                required_together=[
                    ['mcp_user', 'mcp_password']
                ]
            )
        )

        self.name = self.module.params['name']
        self.description = self.module.params['description']
        self.location = self.module.params['location']
        self.state = self.module.params['state']

        # Get MCP API Version
        self.mcp_version = self.get_mcp_version(self.location)

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
