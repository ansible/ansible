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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nttc_cis_ip_list
short_description: Create, update and delete IP Address Lists
description:
    - Create, update and delete IP Address Lists
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        default: na
        choices:
          - Valid values can be found in nttcis.common.config.py under
            APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTTC CIS Cloud Web UI
    name:
        description:
            - The name of the IP Address List
        required: false
    description:
        description:
            - The description of the IP Address List
        required: false
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    ip_addresses:
        description:
            - List of IP Addresses with begin, end or prefix
        required: false
    ip_addresses_nil:
        description:
            - Used on updating to remove all IP addresses
        required: false
        choices: [true, false]
    child_ip_list:
        description:
            - List of IP adddress UUIDs to be included in this ip address
        required: false
    child_ip_list_nil:
        description:
            - Used on updating to remove all child IP address lists
        required: false
        choices: [true, false]
    version:
        description: The IP protocol version for the IP Address List
        required: false
        choices: [IPV4, IPv6]
        default: IPV4
    state:
        description:
            - The action to be performed
        required: true
        default: create
        choices: [list, get, create, update, delete]
notes:
    - N/A
'''

EXAMPLES = '''
# Create a IP Address List
- nttc_cis_ip_list:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      version: IPV4
      name: "APITEST"
      ip_addresses:
        - begin: "10.0.7.10"
      child_ip_list:
        - "My_Child_IP_List"
      state: present
# Update an IP Address List
- nttc_cis_ip_list:
    region: na
    datacenter: NA9
    network_domain: "xxxx"
    version: IPV4
    name: "APITEST"
    ip_addresses:
        - begin: "10.0.7.10"
    child_ip_list_nil: True
    state: present
# Delete a IP Address List
- nttc_cis_ip_list:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      version: IPV4
      name: "APITEST"
      state: absent
'''

RETURN = '''
results:
    description: a list of IP Address List objects or strings
    returned: success
    type: complex
    contains:
        id:
            description: IP Address List UUID
            type: string
            returned: when state == present
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        description:
            description: IP Address List description
            type: string
            returned: when state == present
            sample: "My IP Address List description"
        name:
            description: IP Address List name
            type: string
            returned: when state == present
            sample: "My IP Address List"
        createTime:
            description: The creation date of the image
            type: string
            returned: when state == present
            sample: "2019-01-14T11:12:31.000Z"
        state:
            description: Status of the VLAN
            type: string
            returned: when state == present
            sample: NORMAL
        ipVersion:
            description: The IP version for the IP Address List
            type: string
            returned: when state == present
            sample: "IPV6"
        ipAddress:
            description: List of IP Addresses and/or IP Address Lists
            type: complex
            returned: when state == present
            contains:
                begin:
                    description: The starting IP Address number for this IP Address or range (IPv4 or IPv6)
                    type: int
                    sample: x.x.x.x
                end:
                    description: The end IP Address number for this range. This is not present for single IP Addresses (IPv4 or IPv6)
                    type: int
                    sample: x.x.x.x
                prefixSize:
                    description: The prefix size for a given subnet
                    type: string
                    sample: "24"
        childIpAddressList:
            description: List of child IP Address Lists
            type: complex
            returned: when state == present
            contains:
                id:
                    description: The ID of the IP Address List
                    type: string
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                name:
                    description: The name of the IP Address List
                    type: string
                    sample: "My Child IP Address List"
'''
import traceback
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object, compare_json
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def create_ip_list(module, client, network_domain_id):
    """
    Create a IP address list

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: The created IP address list object
    """
    return_data = return_object('ip_list')
    name = module.params.get('name')
    description = module.params.get('description')
    ip_addresses = module.params.get('ip_addresses')
    child_ip_lists = module.params.get('child_ip_lists')
    version = module.params.get('version')
    if name is None:
        module.fail_json(msg='A valid name is required')
    if not ip_addresses and not child_ip_lists:
        module.fail_json(msg='ip_addresses or child_ip_lists must have at least one valid entry')
    try:
        client.create_ip_list(network_domain_id, name, description, ip_addresses, child_ip_lists, version)
        return_data['ip_list'] = client.get_ip_list_by_name(network_domain_id, name, version)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not create the IP Address List {0}'.format(e))

    module.exit_json(changed=True, results=return_data['ip_list'])


def update_ip_list(module, client, network_domain_id, ip_list):
    """
    Update a IP address list

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg ip_list: The existing IP address list to be updated
    :returns: The updated IP address list object
    """
    return_data = return_object('ip_list')
    name = module.params.get('name')

    try:
        client.update_ip_list(network_domain_id,
                              ip_list.get('id'),
                              module.params.get('description'),
                              module.params.get('ip_addresses'),
                              module.params.get('ip_addresses_nil'),
                              module.params.get('child_ip_lists'),
                              module.params.get('child_ip_lists_nil')
                             )
        return_data['ip_list'] = client.get_ip_list_by_name(network_domain_id, name, ip_list.get('ipVersion'))
    except (KeyError, IndexError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not update the IP Address List - {0}'.format(e))

    module.exit_json(changed=True, results=return_data['ip_list'])


def compare_ip_list(module, client, network_domain_id, ip_list):
    """
    Compare two IP address lists

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg new_fw_rule: The dict containing the specification for the new rule based on the supplied parameters
    :arg ip_list: The existing IP address list object to be compared
    :returns: Any differences between the two IP address lists
    """
    # Handle schema differences between the returned API object and the one required to be sent
    child_ip_list_ids = []
    for i in range(len(ip_list['childIpAddressList'])):
        child_ip_list_ids.append(ip_list['childIpAddressList'][i].get('id'))
    ip_list.pop('childIpAddressList')
    ip_list['childIpAddressListId'] = child_ip_list_ids
    ip_list.pop('state')
    ip_list.pop('createTime')

    new_ip_list = client.ip_list_args_to_dict(False,
                                              network_domain_id,
                                              ip_list.get('id'),
                                              ip_list.get('name'),
                                              module.params.get('description'),
                                              module.params.get('ip_addresses'),
                                              module.params.get('ip_addresses_nil'),
                                              module.params.get('child_ip_lists'),
                                              module.params.get('child_ip_lists_nil'),
                                              module.params.get('version')
                                             )

    if module.params.get('child_ip_lists_nil') and not ip_list.get('childIpAddressListId'):
        new_ip_list['childIpAddressListId'] = []
    if module.params.get('ip_addresses_nil') and not ip_list.get('ipAddress'):
        new_ip_list['ipAddress'] = []

    compare_result = compare_json(new_ip_list, ip_list, None)
    return compare_result['changes']


def delete_ip_list(module, client, ip_list):
    """
    Delete a IP address list

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg ip_list: The IP address list object to be removed
    :returns: A message
    """
    try:
        client.remove_ip_list(ip_list.get('id'))
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not delete the IP Address List - {0}'.format(e))

    module.exit_json(changed=True)


def main():
    """
    Main function

    :returns: IP address list Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            name=dict(required=False, type='str'),
            description=dict(required=False, type='str'),
            version=dict(required=False, default=None, type='str', choices=['IPV4', 'IPV6']),
            ip_addresses=dict(required=False, type='list'),
            ip_addresses_nil=dict(required=False, default=False, type='bool'),
            child_ip_lists=dict(required=False, type='list'),
            child_ip_lists_nil=dict(required=False, default=False, type='bool'),
            network_domain=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )

    credentials = get_credentials()
    name = module.params.get('name')
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    version = module.params.get('version')

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

   # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except NTTCCISAPIException as e:
        module.fail_json(msg='Failed to get a list of Cloud Network Domains - {0}'.format(e.message), exception=traceback.format_exc())
    if not network:
        module.fail_json(msg='Failed to find the Cloud Network Domain Check the network_domain value')

    # Get a list of existing VLANs and check if the new name already exists
    try:
        ip_list = client.get_ip_list_by_name(name=name, network_domain_id=network_domain_id, version=version)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Failed to get a list of Port Lists - {0}'.format(e.message), exception=traceback.format_exc())

    if state == 'present':
        if not ip_list:
            create_ip_list(module, client, network_domain_id)
        else:
            if compare_ip_list(module, client, network_domain_id, deepcopy(ip_list)):
                update_ip_list(module, client, network_domain_id, ip_list)
            module.exit_json(result=ip_list)
    elif state == 'absent':
        if not ip_list:
            module.exit_json(msg='IP Address List {0} was not found'.format(name))
        delete_ip_list(module, client, ip_list)


if __name__ == '__main__':
    main()
