#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communications Cloud Infrastructure Services
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_vlan
short_description: List, Create, Update, Delete VLANs
description:
    - Get, Create, Delete VLANs
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
            - Valid values can be found in nttmcp.common.config.py under APIENDPOINTS
        required: false
        default: na
        type: str
    datacenter:
        description:
            - The datacenter name
        required: true
        type: str
    network_domain:
        description:
            - The name of the Cloud Network Domain
        required: true
        type: str
    name:
        description:
            - The name of the VLAN
        required: true
        type: str
    description:
        description:
            - The description of the VLAN
        required: false
        type: str
    ipv4_network_address:
        description:
            - The IPv4 network address for the VLAN
        required: false
        type: str
    ipv4_prefix_size:
        description:
            - The prefix size for the VLAN (e.g. /24)
        required: false
        type: int
    ipv6_network_address:
        description:
            - The IPv6 network address for the VLAN (used for searching only)
        required: false
        type: str
    vlan_type:
        description:
            - The type of VLAN
        required: true
        default: attachedVlan
        choices:
          - attachedVlan
          - detachedVlan
        type: str
    attached_vlan_gw:
        description:
            - Required if vlan_type == attachedVlan. HIGH == .254, LOW == .1
        required: false
        default: LOW
        choices:
            - LOW
            - HIGH
        type: str
    detached_vlan_gw:
        description:
            - Required if vlan_type == detachedVlan. IPv4 address of the gw
            - Cannot be the first or last address in the range
        required: false
        type: str
    detached_vlan_gw_ipv6:
        description:
            - Required if vlan_type == detachedVlan. IPv6 address of the gw
            - Cannot be any of the first 32 addresses in the range
        required: false
        type: str
    new_name:
        description:
            - The new name of the Cloud Network Domain, used when updating
        required: true
        type: str
    state:
        description:
            - The action to be performed
        required: true
        default: present
        choices:
            - present
            - absent
        type: str
    wait:
        description:
            - Should Ansible wait for the task to complete before continuing
        required: false
        default: true
        type: bool
    wait_time:
        description: The maximum time the Ansible should wait for the task
                     to complete in seconds
        required: false
        default: 600
        type: int
    wait_poll_interval:
        description:
            - The time in between checking the status of the task in seconds
        required: false
        default: 10
        type: int
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
    - configparser>=3.7.4
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Create an Attached VLAN
    ntt_mcp_vlan:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myVLAN2
      ipv4_network_address: "10.1.78.0"
      ipv4_prefix_size: 24
      attached_vlan_gw: HIGH
      state: present

  - name: Create a Detached VLAN
    ntt_mcp_vlan:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myVLAN3
      ipv4_network_address: "10.1.79.0"
      ipv4_prefix_size: 24
      vlan_type: detachedVlan
      detached_vlan_gw: "10.1.79.1"
      state: present

  - name: Update a VLAN - Change the name and the detached VLAN gateway
    ntt_mcp_vlan:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myVLAN3
      ipv4_network_address: "10.1.79.0"
      ipv4_prefix_size: 24
      vlan_type: detachedVlan
      detached_vlan_gw: "10.1.79.2"
      new_name: myVLAN4
      state: present

  - name: Delete a VLAN
    ntt_mcp_vlan:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myVLAN4
      state: absent
'''

RETURN = '''
data:
    description: Dictionary of the vlan
    returned: success
    type: complex
    contains:
        id:
            description: VLAN ID
            type: str
            returned: when state == present
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        name:
            description: VLAN name
            type: str
            returned: when state == present and wait is True
            sample: "My network"
        description:
            description: VLAN description
            type: str
            returned: when state == present and wait is True
            sample: "My network description"
        datacenterId:
            description: Datacenter id/location
            type: str
            returned: when state == present and wait is True
            sample: NA9
        state:
            description: Status of the VLAN
            type: str
            returned: when state == present and wait is True
            sample: NORMAL
        attached:
            description: Whether or not the VLAN is a dettached VLAN
            type: bool
            returned: when state == present and wait is True
        createTime:
            description: The creation date of the image
            type: str
            returned: when state == present and wait is True
            sample: "2019-01-14T11:12:31.000Z"
        gatewayAddressing:
            description: Use low (.1) or high (.254) addressing for the default gateway
            type: str
            returned: when state == present and wait is True
            sample: LOW
        ipv4GatewayAddress:
            description: The IPv4 default gateway for this VLAN
            type: str
            returned: when state == present and wait is True
            sample: "10.0.0.1"
        ipv6GatewayAddress:
            description: The IPv6 default gateway for this VLAN
            type: str
            returned: when state == present and wait is True
            sample: "1111:1111:1111:1111:0:0:0:1"
        ipv6Range:
            description: The IPv6 address range
            type: complex
            returned: when state == present and wait is True
            contains:
                address:
                    description: The base IPv6 network address
                    type: str
                    sample: "1111:1111:1111:1111:0:0:0:0"
                prefixSize:
                    description: The IPv6 network prefix size
                    type: int
                    sample: 64
        networkDomain:
            description: The Cloud Network Domain
            type: complex
            returned: when state == present and wait is True
            contains:
                id:
                    description: The UUID of the Cloud Network Domain of the VLAN
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                name:
                    description: The name of the Cloud Network Domain
                    type: str
                    sample: "my_network_domain"
        privateIpv4Range:
            description: The IPv4 address range
            type: complex
            returned: when state == present and wait is True
            contains:
                address:
                    description: The base IPv46 network address
                    type: str
                    sample: "10.0.0.0"
                prefixSize:
                    description: The IPv6 network prefix size
                    type: int
                    sample: 24
        small:
            description: Internal use
            type: bool
            returned: when state == present and wait is True
'''

import traceback
from time import sleep
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def create_vlan(module, client, network_domain_id):
    """
    Create a VLAN

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: VLAN Object
    """
    return_data = return_object('vlan')
    if not module.params.get('ipv4_network_address'):
        module.fail_json(msg='An IPv4 network address is required for a new VLAN.')
    if not module.params.get('ipv4_prefix_size'):
        module.fail_json(msg='An IPv4 Prefix Size is required for a new VLAN.')

    datacenter = module.params['datacenter']
    name = module.params['name']
    vlan_type = module.params['vlan_type']
    ipv4_network = module.params['ipv4_network_address']
    ipv4_prefix = module.params['ipv4_prefix_size']
    wait = module.params['wait']

    if vlan_type == 'attachedVlan':
        if not module.params.get('attached_vlan_gw'):
            module.fail_json(msg='An attached_vlan_gw value [LOW/HIGH] is required for a new Attached VLAN.')
    elif vlan_type == 'detachedVlan':
        if not module.params.get('detached_vlan_gw'):
            module.fail_json(msg='A detached_vlan_gw value (e.g. 10.0.0.1) is reuiqred for a new Detached VLAN.')

    try:
        if vlan_type == 'attachedVlan':
            gateway = module.params['attached_vlan_gw']
            result = client.create_vlan(
                networkDomainId=network_domain_id,
                name=name,
                description=module.params['description'],
                privateIpv4NetworkAddress=ipv4_network,
                privateIpv4PrefixSize=ipv4_prefix,
                attachedVlan=True,
                attachedVlan_gatewayAddressing=gateway)
            new_vlan_id = result['info'][0]['value']
        elif vlan_type == 'detachedVlan':
            gateway = module.params['detached_vlan_gw']
            result = client.create_vlan(
                networkDomainId=network_domain_id,
                name=name,
                description=module.params['description'],
                privateIpv4NetworkAddress=ipv4_network,
                privateIpv4PrefixSize=ipv4_prefix,
                detachedVlan=True,
                detachedVlan_ipv4GatewayAddress=gateway)
            new_vlan_id = result['info'][0]['value']
    except (KeyError, IndexError, NTTMCPAPIException) as exc:
        module.fail_json(msg='Could not create the VLAN - {0}'.format(exc), exception=traceback.format_exc())

    if wait:
        wait_result = wait_for_vlan(module, client, name, datacenter, network_domain_id, 'NORMAL')
        if wait_result is None:
            module.fail_json(msg='Could not verify the VLAN creation was successful. Check the UI.')
        return_data['vlan'] = wait_result
    else:
        return_data['vlan'] = {'id': new_vlan_id}

    module.exit_json(changed=True, data=return_data['vlan'])


def update_vlan(module, client, vlan):
    """
    Update a VLAN

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg vlan: The existing VLAN object
    :returns: the comparison result
    """
    return_data = return_object('vlan')
    name = vlan['name']
    new_name = module.params['new_name']
    description = module.params['description']
    datacenter = vlan['datacenterId']
    vlan_id = vlan['id']
    network_domain_id = vlan['networkDomain']['id']
    detached_vlan_gw = module.params['detached_vlan_gw']
    detached_vlan_gw_ipv6 = module.params['detached_vlan_gw_ipv6']
    wait = module.params['wait']

    if new_name:
        name = new_name

    try:
        client.update_vlan(vlan_id, name, description, detached_vlan_gw, detached_vlan_gw_ipv6)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not update the VLAN - {0}'.format(exc), exception=traceback.format_exc())

    if wait:
        wait_result = wait_for_vlan(module, client, name, datacenter, network_domain_id, 'NORMAL')
        if wait_result is None:
            module.fail_json(msg='Could not verify the VLAN update was successful. Check the UI.')
        return_data['vlan'] = wait_result
    else:
        return_data['vlan'] = {'id': vlan['id']}

    module.exit_json(changed=True, data=return_data['vlan'])


def compare_vlan(module, vlan):
    """
    Compare an existing VLAN to one using the supplied arguments

    :arg module: The Ansible module instance
    :arg vlan: The existing VLAN object
    :returns: the comparison result
    """
    new_vlan = deepcopy(vlan)
    if module.params.get('new_name'):
        new_vlan['name'] = module.params.get('new_name')
    if module.params.get('description'):
        new_vlan['description'] = module.params.get('description')
    if module.params.get('detached_vlan_gw'):
        new_vlan['ipv4GatewayAddress'] = module.params.get('detached_vlan_gw')
    if module.params.get('detached_vlan_gw_ipv6'):
        new_vlan['ipv6GatewayAddress'] = module.params.get('detached_vlan_gw_ipv6')

    compare_result = compare_json(new_vlan, vlan, None)
    # Implement Check Mode
    if module.check_mode:
        module.exit_json(data=compare_result)
    return compare_result.get('changes')


def delete_vlan(module, client, datacenter, network_domain_id, vlan_id):
    """
    Wait for the VLAN operation to complete

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg datacenter: The MCP ID
    :arg network_domain_id: The UUID of the network domain
    :arg vlan_id: The UUID of the VLAN to delete
    """
    vlan_exists = True
    time = 0
    wait_time = module.params['wait_time']
    wait_poll_interval = module.params['wait_poll_interval']

    try:
        client.delete_vlan(vlan_id)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not delete the VLAN - {0}'.format(exc), exception=traceback.format_exc())
    if module.params['wait']:
        while vlan_exists and time < wait_time:
            try:
                vlans = client.list_vlans(datacenter=datacenter, network_domain_id=network_domain_id)
                vlan_exists = [x for x in vlans if x['id'] == vlan_id]
            except (KeyError, IndexError, NTTMCPAPIException):
                pass
            sleep(wait_poll_interval)
            time = time + wait_poll_interval

        if vlan_exists and time >= wait_time:
            module.fail_json(msg='Timeout waiting for the VLAN to be deleted')

    module.exit_json(changed=True, msg='The VLAN has been successfully removed')


def wait_for_vlan(module, client, name, datacenter, network_domain_id, state):
    """
    Wait for the VLAN operation to complete

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg name: The VLAN name
    :arg datacenter: The MCP ID
    :arg network_domain_id: The UUID of the network domain
    :arg state: The state to wait for e.g. NORMAL
    :returns: VIP Node object
    """
    actual_state = ''
    vlan = None
    time = 0
    wait_time = module.params['wait_time']
    wait_poll_interval = module.params['wait_poll_interval']

    while actual_state != state and time < wait_time:
        try:
            vlan = client.get_vlan_by_name(name=name, datacenter=datacenter, network_domain_id=network_domain_id)
        except NTTMCPAPIException as exc:
            module.fail_json(msg='Failed to get a list of VLANS - {0}'.format(exc), exception=traceback.format_exc())
        try:
            actual_state = vlan['state']
        except (KeyError, IndexError):
            module.fail_json(msg='Failed to find the VLAN - {0}'.format(name))
        sleep(module.params['wait_poll_interval'])
        time = time + wait_poll_interval

    if vlan and time >= wait_time:
        module.fail_json(msg='Timeout waiting for the VLAN to be created')

    return vlan


def main():
    """
    Main function

    :returns: VLAN Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            ipv4_network_address=dict(required=False, type='str'),
            ipv4_prefix_size=dict(required=False, type='int'),
            ipv6_network_address=dict(required=False, type='str'),
            vlan_type=dict(default='attachedVlan', choices=['attachedVlan', 'detachedVlan']),
            attached_vlan_gw=dict(required=False, default='LOW', choices=['LOW', 'HIGH']),
            detached_vlan_gw=dict(required=False, type='str'),
            detached_vlan_gw_ipv6=dict(required=False, type='str'),
            new_name=dict(required=False, default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=600, type='int'),
            wait_poll_interval=dict(required=False, default=10, type='int')
        ),
        supports_check_mode=True
    )

    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    name = module.params.get('name')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    network_domain_name = module.params.get('network_domain')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Get a list of existing VLANs and check if the new name already exists
    try:
        vlan = client.get_vlan_by_name(name=name, datacenter=datacenter, network_domain_id=network_domain_id)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Failed to get a list of VLANs - {0}'.format(exc))

    # Create the VLAN
    if state == 'present':
        # Handle case where VLAN name already exists
        if not vlan:
            # Implement Check Mode
            if module.check_mode:
                module.exit_json(msg='A new VLAN will be created in the Cloud Network Domain with the UUID {0}'.format(
                    network_domain_id))
            create_vlan(module, client, network_domain_id)
        else:
            try:
                if compare_vlan(module, vlan):
                    update_vlan(module, client, vlan)
                module.exit_json(result=vlan)
            except NTTMCPAPIException as exc:
                module.fail_json(msg='Failed to update the VLAN - {0}'.format(exc))
    # Delete the VLAN
    elif state == 'absent':
        if not vlan:
            module.exit_json(msg='VLAN not found')
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='An existing VLAN was found for {0} and will be removed'.format(
                vlan.get('id')))
        delete_vlan(module, client, datacenter, network_domain_id, vlan.get('id'))


if __name__ == '__main__':
    main()
