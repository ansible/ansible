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
#
from ansible.module_utils.basic import *
from ansible.module_utils.dimensiondata import *
try:
    from libcloud.common.dimensiondata import DimensionDataAPIException
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    import libcloud.security
    HAS_LIBCLOUD = True
except:
    HAS_LIBCLOUD = False

# Get regions early to use in docs etc.
dd_regions = get_dd_regions()

DOCUMENTATION = '''
---
module: dimensiondata_vlan
short_description: Create, Read, Update or Delete VLANs.
description:
  - Create, Read, Update, Delete or Expand VLANs.
version_added: "2.2"
author: 'Aimon Bustardo (@aimonb)'
options:
  region:
    description:
      - The target region.
    choices:
      - Regions choices are defined in Apache libcloud project [libcloud/common/dimensiondata.py]
      - Regions choices are also listed in https://libcloud.readthedocs.io/en/latest/compute/drivers/dimensiondata.html
      - Note that the region values are available as list from dd_regions().
      - Note that the default value "na" stands for "North America".  The code prepends 'dd-' to the region choice.
    default: na
  location:
    description:
      - The target datacenter.
    required: true
  name:
    description:
      - The name of the VLAN, required for 'create' action
    required: false
  description:
    description:
      - Additional description of the VLAN.
    required: false
    default: null
  network_domain:
    description:
      - The network domain name of the target network.
    required: true
  private_ipv4_base_address:
    description:
        - The base IPv4 address e.g. 192.168.1.0.
    required: false
  private_ipv4_prefix_size:
    description:
        - The size of the IPv4 address space, e.g 24.
    required: false
  vlan_id:
    description:
      - The VLAN ID, required for 'update' and 'expand' action.
    required: false
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
      - Only applicable if wait is true.
        This is the amount of time in seconds to wait
    required: false
    default: 600
  wait_poll_interval:
    description:
      - The amount to time inbetween polling for task completion
    required: false
    default: 2
  action:
    description:
      - create, read(get), update, delete or expand.
    choices: [create, read, get, update, delete, expand]
    default: create
'''

EXAMPLES = '''
# Add VLAN
- dimensiondata_vlan:
    region: na
    location: NA5
    network_domain: test_network
    name: my_vlan1
    description: A test VLAN'd Network.
    private_ipv4_base_address: 192.168.23.0
    private_ipv4_prefix_size: 24
    action: create
    wait: yes
# Read/Get a VLAN details
- dimensiondata_vlan:
    region: na
    location: NA5
    network_domain: test_network
    name: my_vlan1
    action: read
    wait: yes
# Update a VLAN
# VLAN ID is required to modify a VLAN.
- dimensiondata_vlan:
    region: na
    location: NA5
    network_domain: test_network
    vlan_id: a2c6cccc-bbbb-aaaa-0000-000028bcc47c
    name: my_vlan_1
    description: A test VLAN network, renamed.
    state: present
    wait: yes
# Delete a VLAN by name
- dimensiondata_vlan:
    region: na
    location: NA5
    network_domain: test_network
    name: my_vlan_1
    action: delete
    wait: no
# Delete a VLAN by ID
- dimensiondata_vlan:
    region: na
    location: NA5
    network_domain: test_network
    vlan_id: a2c6cccc-bbbb-aaaa-0000-000028bcc47c
    action: delete
    wait: no
'''

RETURN = '''
vlan:
    description: Dictionary describing the VLAN.
    returned: On success when I(state) is 'present'
    type: dictionary
    contains:
        id:
            description: VLAN ID.
            type: string
            sample: "aaaaa000-a000-4050-a215-2808934ccccc"
        name:
            description: VLAN name.
            type: string
            sample: "My VLAN"
        description:
            description: VLAN description.
            type: string
            sample: "My VLAN description"
        location:
            description: Datacenter location.
            type: string
            sample: NA3
        status:
            description: VLAN status.
            type: string
            sample: NORMAL
'''


def vlan_obj_to_dict(vlan):
    vlan_d = dict(id=vlan.id,
                  name=vlan.name,
                  description=vlan.description,
                  location=vlan.location.id,
                  private_ipv4_range_address=vlan.private_ipv4_range_address,
                  private_ipv4_range_size=vlan.private_ipv4_range_size,
                  status=vlan.status,
                  )
    return vlan_d


def wait_for_vlan_state(module, driver, vlan_id, state_to_wait_for):
    try:
        return driver.connection.wait_for_state(
            state_to_wait_for, driver.ex_get_vlan,
            module.params['wait_poll_interval'],
            module.params['wait_time'], vlan_id
        )
    except DimensionDataAPIException as e:
        module.fail_json(msg='VLAN did not reach % state in time: %s'
                         % (state, e.msg))


def create_vlan(module, driver, location, network_domain, name, description,
                base_address, prefix_size):
    try:
        vlan = driver.ex_create_vlan(network_domain, name, base_address,
                                     description, prefix_size)
    except DimensionDataAPIException as e:
        if e.code == 'NAME_NOT_UNIQUE':
            vlan = get_vlan(module, driver, location, network_domain, 'False',
                            name)
            return {'vlan': vlan, 'changed': False}
        module.fail_json(msg="Failed to create VLAN: %s" % e)
    # Wait for it to become ready
    if module.params['wait']:
        vlan = wait_for_vlan_state(module, driver, vlan.id, 'NORMAL')
    return {'vlan': vlan, 'changed': True}


def get_vlan(module, driver, location, network_domain, vlan_id, name):
    if vlan_id is not 'False':
        try:
            vlan = driver.ex_get_vlan(vlan_id)
            return vlan
        except DimensionDataAPIException as e:
            if e.code == "NOT_FOUND":
                return {'id': False}
            else:
                module.fail_json(msg="Unexpected error: %s" % e)
    elif name is not False:
        try:
            # Find vlan by name
            vlans = driver.ex_list_vlans(location, network_domain, name)
            # VLAN not found
            if len(vlans) < 1:
                return {'id': False}
            return driver.ex_get_vlan(vlans[0].id)
        except DimensionDataAPIException as e:
            module.fail_json(msg="Unexpected API error: %s" % e)
    else:
        module.fail_json(msg="Unexpected Error: One of vlan_id or name " +
                             "must be provided.")


def delete_vlan(module, driver, location, network_domain, vlan_id, name):
    vlan = get_vlan(module, driver, location, network_domain,
                    vlan_id, name)
    if type(vlan) is dict:
        return False
    try:
        return driver.ex_delete_vlan(vlan)
    except DimensionDataAPIException as e:
        module.fail_json(msg="Unexpected API error: %s" % e)


def update_vlan(module, driver, location, network_domain, vlan_id,
                name, description):
    vlan_obj = get_vlan(module, driver, location, network_domain,
                        vlan_id, name)
    if vlan_obj is False:
        changed = False
        vlan = False
    elif vlan_obj.name != name or vlan_obj.description != description:
        vlan_obj.name = name
        vlan_obj.description = description
        try:
            vlan = driver.ex_update_vlan(vlan_obj)
        except DimensionDataAPIException as e:
            module.fail_json(msg="Failed to update VLAN: %s" % e)
        changed = True
    else:
        changed = False
        vlan = False
    return {'changed': changed, 'vlan': vlan}


def expand_vlan(module, driver, location, network_domain, vlan_id, name,
                private_ipv4_range_size):
    vlan_obj = get_vlan(module, driver, location, network_domain,
                        vlan_id, name)
    if type(vlan_obj) is dict:
        module.exit_json(changed=False, msg="VLAN not found.")
    else:
        if vlan_obj.private_ipv4_range_size == private_ipv4_range_size:
            return False
        else:
            vlan_obj.private_ipv4_range_size = private_ipv4_range_size
            try:
                return driver.ex_expand_vlan(vlan_obj)
            except DimensionDataAPIException as e:
                module.fail_json(msg="Failed to expand VLAN: %s" % e)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=dd_regions),
            location=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            name=dict(default=False, type='str'),
            vlan_id=dict(default=False, type='str'),
            description=dict(default='', type='str'),
            private_ipv4_base_address=dict(default=False, type='str'),
            private_ipv4_prefix_size=dict(default=False, type='str'),
            action=dict(default='create', choices=['create', 'read', 'get',
                                                   'update', 'delete',
                                                   'expand']),
            verify_ssl_cert=dict(required=False, default=True, type='bool'),
            wait=dict(required=False, default=False, type='bool'),
            wait_time=dict(required=False, default=600, type='int'),
            wait_poll_interval=dict(required=False, default=2, type='int')
        )
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud is required for this module.')

    # set short vars for readability
    credentials = get_credentials()
    if credentials is False:
        module.fail_json(msg="User credentials not found")
    user_id = credentials['user_id']
    key = credentials['key']
    region = 'dd-%s' % module.params['region']
    location = module.params['location']
    network_domain_name = module.params['network_domain']
    name = module.params['name']
    vlan_id = module.params['vlan_id']
    description = module.params['description']
    base_address = module.params['private_ipv4_base_address']
    prefix_size = module.params['private_ipv4_prefix_size']
    verify_ssl_cert = module.params['verify_ssl_cert']
    action = module.params['action']

    # Instantiate driver
    libcloud.security.VERIFY_SSL_CERT = verify_ssl_cert
    DimensionData = get_driver(Provider.DIMENSIONDATA)
    driver = DimensionData(user_id, key, region=region)

    # Get Network Domain Object
    network_domain = get_network_domain_by_name(driver, network_domain_name,
                                                location)

    # Process action
    if action == 'create':
        if name is False:
            module.fail_json(msg="'name' is a required argument when action" +
                                 " is 'create'")
        res = create_vlan(module, driver, location, network_domain, name,
                          description, base_address, prefix_size)
        vlan = vlan_obj_to_dict(res['vlan'])
        if res['changed'] is False:
            module.exit_json(changed=False, msg="VLAN with name '%s'" +
                             " already exists." % name, vlan=vlan)
        module.exit_json(changed=True, msg="Successfully created VLAN.",
                         vlan=vlan)
    elif action == 'read' or action == 'get':
        res = get_vlan(module, driver, location, network_domain,
                       vlan_id, name)
        if type(res) is dict:
            vlan = res
        else:
            vlan = vlan_obj_to_dict(res)
        module.exit_json(changed=False, msg="Successfully read VLAN.",
                         vlan=vlan)
    elif action == 'delete':
        res = delete_vlan(module, driver, location, network_domain,
                          vlan_id, name)
        module.exit_json(changed=res, msg="Successfully deleted VLAN or " +
                         "VLAN does not exist")
    elif action == 'update':
        if vlan_id is False:
            module.fail_json(msg="'vlan_id' is a required argument when " +
                             "updating a VLAN")
        res = update_vlan(module, driver, location, network_domain, vlan_id,
                          name, description)
        if res['vlan'] is False and res['changed'] is False:
            module.exit_json(changed=False, msg="VLAN did not need updating.")
        else:
            vlan = vlan_obj_to_dict(res['vlan'])
            module.exit_json(changed=False, msg="Successfully updated VLAN.",
                             vlan=vlan)
    elif action == 'expand':
        if vlan_id is False:
            module.fail_json(msg="'vlan_id' is a required argument when " +
                             "expanding a VLAN")
        res = expand_vlan(module, driver, location, network_domain, vlan_id,
                          name, prefix_size)
        if type(res) is bool:
            module.exit_json(changed=False, msg="VLAN already requested size.")
        else:
            module.exit_json(changes=True, msg="VLAN network size modified.",
                             vlan=vlan_obj_to_dict(res))
    else:
        fail_json(msg="Requested action was " +
                  "'%s'. Action must be one of 'create', 'read', " +
                  "'update', 'expand' or 'delete'" % state)

if __name__ == '__main__':
    main()
