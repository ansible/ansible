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
      - Valid regions are defined in Apache libcloud project [libcloud/common/dimensiondata.py]
      - Regions are also listed in https://libcloud.readthedocs.io/en/latest/compute/drivers/dimensiondata.html
      - Note that the default value "na" stands for "North America".
      - The module prepends 'dd-' to the region.
    default: na
  mcp_user:
    description:
      - The username used to authenticate to the CloudControl API.
      - If not specified, will fall back to MCP_USER from environment variable or  ~/.dimensiondata.
    required: false
  mcp_password:
    description:
      - The password used to authenticate to the CloudControl API.
      - If not specified, will fall back to MCP_PASSWORD from environment variable or  ~/.dimensiondata.
      - Required if mcp_user is specified.
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
      - The amount to time inbetween polling for task completion
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
from ansible.module_utils.dimensiondata import get_credentials, DimensionDataAPIException, LibcloudNotFound
from ansible.module_utils.pycompat24 import get_exception
try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.compute.base import NodeLocation
    import libcloud.security
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False


def network_obj_to_dict(network, version):
    network_dict = dict(id=network.id, name=network.name,
                        description=network.description)
    if isinstance(network.location, NodeLocation):
        network_dict['location'] = network.location.id
    else:
        network_dict['location'] = network.location

    if version == '1.0':
        network_dict['private_net'] = network.private_net
        network_dict['multicast'] = network.multicast
        network_dict['status'] = None
    else:
        network_dict['private_net'] = None
        network_dict['multicast'] = None
        network_dict['status'] = network.status
    return network_dict


def get_mcp_version(driver, location):
    # Get location to determine if MCP 1.0 or 2.0
    location = driver.ex_get_location_by_id(location)
    if 'MCP 2.0' in location.name:
        return '2.0'
    return '1.0'


def create_network(module, driver, mcp_version, location,
                   name, description):

    # Make sure service_plan argument is defined
    if mcp_version == '2.0' and 'service_plan' not in module.params:
        module.fail_json('service_plan required when creating network and ' +
                         'location is MCP 2.0')
    service_plan = module.params['service_plan']

    # Create network
    try:
        if mcp_version == '1.0':
            res = driver.ex_create_network(location, name,
                                           description=description)
        else:
            res = driver.ex_create_network_domain(location, name,
                                                  service_plan,
                                                  description=description)
    except DimensionDataAPIException:
        e = get_exception()

        module.fail_json(msg="Failed to create new network: %s" % str(e))

    if module.params['wait'] is True:
        wait_for_network_state(module, driver, res.id, 'NORMAL')
    msg = "Created network %s in %s" % (name, location)
    network = network_obj_to_dict(res, mcp_version)

    module.exit_json(changed=True, msg=msg, network=network)


def delete_network(module, driver, matched_network, mcp_version):
    try:
        if mcp_version == '1.0':
            res = driver.ex_delete_network(matched_network[0])
        else:
            res = driver.ex_delete_network_domain(matched_network[0])
        if res is True:
            module.exit_json(changed=True,
                             msg="Deleted network with id %s" %
                             matched_network[0].id)

        module.fail_json("Unexpected failure deleting network with " +
                         "id %s", matched_network[0].id)
    except DimensionDataAPIException:
        e = get_exception()

        module.fail_json(msg="Failed to delete network: %s" % str(e))


def wait_for_network_state(module, driver, net_id, state_to_wait_for):
    try:
        return driver.connection.wait_for_state(
            state_to_wait_for, driver.ex_get_network_domain,
            module.params['wait_poll_interval'],
            module.params['wait_time'], net_id
        )
    except DimensionDataAPIException:
        e = get_exception()

        module.fail_json(msg='Network did not reach % state in time: %s'
                         % (state_to_wait_for, e.msg))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na'),
            mcp_user=dict(required=False, type='str'),
            mcp_password=dict(required=False, type='str'),
            location=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            service_plan=dict(default='ADVANCED', choices=['ADVANCED',
                              'ESSENTIALS']),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(required=False, default=False, type='bool'),
            wait_time=dict(required=False, default=600, type='int'),
            wait_poll_interval=dict(required=False, default=2, type='int'),
            verify_ssl_cert=dict(required=False, default=True, type='bool')
        )
    )

    try:
        credentials = get_credentials(module)
    except LibcloudNotFound:
        module.fail_json(msg='libcloud is required for this module.')

    if not credentials:
        module.fail_json(msg="User credentials not found")

    # set short vars for readability
    user_id = credentials['user_id']
    key = credentials['key']
    region = 'dd-%s' % module.params['region']
    location = module.params['location']
    name = module.params['name']
    description = module.params['description']
    verify_ssl_cert = module.params['verify_ssl_cert']
    state = module.params['state']

    # Instantiate driver
    libcloud.security.VERIFY_SSL_CERT = verify_ssl_cert
    DimensionData = get_driver(Provider.DIMENSIONDATA)
    driver = DimensionData(user_id, key, region=region)

    # Get MCP API Version
    mcp_version = get_mcp_version(driver, location)

    # Get network list
    if mcp_version == '1.0':
        networks = driver.list_networks(location=location)
    else:
        networks = driver.ex_list_network_domains(location=location)
    matched_network = [network for network in networks if network.name == name]

    # Ensure network state
    if state == 'present':
        # Network already exists
        if matched_network:
            module.exit_json(
                changed=False,
                msg="Network already exists",
                network=network_obj_to_dict(matched_network[0], mcp_version)
            )
        create_network(module, driver, mcp_version, location, name,
                       description)
    elif state == 'absent':
        # Destroy network
        if matched_network:
            delete_network(module, driver, matched_network, mcp_version)
        else:
            module.exit_json(changed=False, msg="Network does not exist")
    else:
        module.fail_json(msg="Requested state was " +
                             "'%s'. State must be 'absent' or 'present'" % state)

if __name__ == '__main__':
    main()
