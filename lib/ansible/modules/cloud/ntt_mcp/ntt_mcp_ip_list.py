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
module: ntt_mcp_ip_list
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
        type: str
        default: na
    datacenter:
        description:
            - The datacenter name
        required: true
        type: str
    name:
        description:
            - The name of the IP Address List
        required: false
        type: str
    description:
        description:
            - The description of the IP Address List
        required: false
        type: str
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        type: str
    ip_addresses:
        description:
            - List of IP Addresses with begin, end or prefix
        required: false
        type: list
    ip_addresses_nil:
        description:
            - Used on updating to remove all IP addresses
        required: false
        type: bool
    child_ip_lists:
        description:
            - List of IP adddress UUIDs to be included in this ip address
        required: false
        type: list
    child_ip_lists_nil:
        description:
            - Used on updating to remove all child IP address lists
        required: false
        type: bool
    version:
        description: The IP protocol version for the IP Address List
        required: false
        type: str
        default: IPV4
        choices:
            - IPV4
            - IPV6
    state:
        description:
            - The action to be performed
        required: true
        type: str
        default: present
        choices:
            - present
            - absent
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Create an IPv4 address list
    ntt_mcp_ip_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      version: IPV4
      name: myIpAddressList
      ip_addresses:
        - begin: "10.0.7.10"
        - begin: "10.1.7.0"
          end: "10.1.7.128"
      state: present

  - name: Create an IP address list with a child IP address list
    ntt_mcp_ip_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      version: IPV4
      name: myIpAddressList2
      ip_addresses:
        - begin: "10.0.8.10"
        - begin: "10.1.8.0"
          prefix: 24
      child_ip_lists:
        - myIpAddressList
      state: present

  - name: Create an IPv6 address list
    ntt_mcp_ip_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      version: IPV6
      name: myIpAddressList3
      ip_addresses:
        - begin: "fc00::01"
        - begin: "fc01::00"
          prefix: "64"
        - begin: "fc02::01"
          end: "fc02::10"
      state: present

  - name: Update IP address list - Change IP addresses and remove child IP address lists
    ntt_mcp_ip_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      version: IPV4
      name: myIpAddressList2
      ip_addresses:
        - begin: "10.0.0.177"
          end: "10.0.0.179"
        - begin: "10.1.8.0"
          prefix: 24
      child_ip_lists_nil: True
      state: present

  - name: Delete an IPv4 address list
    ntt_mcp_ip_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myIpAddressList2
      state: absent
'''

RETURN = '''
data:
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
try:
    import ipaddress
    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException

# Python3 workaround for unicode function so the same code can be used with ipaddress later
try:
    unicode('')
except NameError:
    unicode = str


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
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not create the IP Address List {0}'.format(e))

    module.exit_json(changed=True, data=return_data['ip_list'])


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
                              module.params.get('child_ip_lists_nil'))
        return_data['ip_list'] = client.get_ip_list_by_name(network_domain_id, name, ip_list.get('ipVersion'))
    except (KeyError, IndexError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not update the IP Address List - {0}'.format(e))

    module.exit_json(changed=True, data=return_data['ip_list'])


def compare_ip_list(module, client, network_domain_id, ip_list, return_all=False):
    """
    Compare two IP address lists

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg new_fw_rule: The dict containing the specification for the new rule based on the supplied parameters
    :arg ip_list: The existing IP address list object to be compared
    :arg return_all: If True returns the full list of changes otherwise just True/False
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
                                              module.params.get('version'))

    if module.params.get('child_ip_lists_nil') and not ip_list.get('childIpAddressListId'):
        new_ip_list['childIpAddressListId'] = []
    if module.params.get('ip_addresses_nil') and not ip_list.get('ipAddress'):
        new_ip_list['ipAddress'] = []
    # Handle case where no child IP address list is required but the schema still returns an empty list
    if not ip_list.get('childIpAddressListId') and not module.params.get('child_ip_lists'):
        ip_list.pop('childIpAddressListId')
    # Handle differences in IPv6 address formatting between Cloud Control and everything else
    if ip_list.get('ipVersion') == 'IPV6':
        if ip_list.get('ipAddress') and new_ip_list.get('ipAddress'):
            for num, ipv6 in enumerate(ip_list.get('ipAddress'), start=0):
                ip_list.get('ipAddress')[num]['begin'] = str(ipaddress.ip_address(unicode(ipv6.get('begin'))).exploded)
                if ipv6.get('end'):
                    ip_list.get('ipAddress')[num]['end'] = str(ipaddress.ip_address(unicode(ipv6.get('end'))).exploded)
            for num, ipv6 in enumerate(new_ip_list.get('ipAddress'), start=0):
                new_ip_list.get('ipAddress')[num]['begin'] = str(ipaddress.ip_address(unicode(ipv6.get('begin'))).exploded)
                if ipv6.get('end'):
                    new_ip_list.get('ipAddress')[num]['end'] = str(ipaddress.ip_address(unicode(ipv6.get('end'))).exploded)

    compare_result = compare_json(new_ip_list, ip_list, None)
    # Implement Check Mode
    if module.check_mode:
        module.exit_json(data=compare_result)
    if return_all:
        return compare_result
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
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not delete the IP Address List - {0}'.format(e))

    module.exit_json(changed=True)


def main():
    """
    Main function

    :returns: IP address list Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            name=dict(required=False, type='str'),
            description=dict(required=False, type='str'),
            version=dict(required=False, default='IPV4', type='str', choices=['IPV4', 'IPV6']),
            ip_addresses=dict(required=False, type='list'),
            ip_addresses_nil=dict(required=False, default=False, type='bool'),
            child_ip_lists=dict(required=False, type='list'),
            child_ip_lists_nil=dict(required=False, default=False, type='bool'),
            network_domain=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )

    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    name = module.params.get('name')
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    version = module.params.get('version')

    # Check Imports
    if not HAS_IPADDRESS:
        module.fail_json(msg='Missing Python module: ipaddress')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params['region'])

    # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if the new name already exists
    try:
        # If deletion search both IPv4 and IPv6 IP address lists for the name
        if state == 'absent':
            version = None
        ip_list = client.get_ip_list_by_name(name=name, network_domain_id=network_domain_id, version=version)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Failed to get a list of Port Lists - {0}'.format(e), exception=traceback.format_exc())

    if state == 'present':
        if not ip_list:
            # Implement check_mode
            if module.check_mode:
                module.exit_json(msg='This IP address list will be created', data=module.params)
            create_ip_list(module, client, network_domain_id)
        else:
            if compare_ip_list(module, client, network_domain_id, deepcopy(ip_list)):
                update_ip_list(module, client, network_domain_id, ip_list)
            module.exit_json(data=ip_list)
    elif state == 'absent':
        if not ip_list:
            module.exit_json(msg='IP Address List {0} was not found'.format(name))
        # Implement check_mode
        if module.check_mode:
            module.exit_json(msg='This IP address list will be removed', data=ip_list)
        delete_ip_list(module, client, ip_list)


if __name__ == '__main__':
    main()
