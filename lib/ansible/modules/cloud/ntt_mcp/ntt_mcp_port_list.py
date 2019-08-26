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
module: ntt_mcp_port_list
short_description: Create, update and delete Firewall Port Lists
description:
    - Create, update and delete Firewall Port Lists
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        default: na
        type: str
    datacenter:
        description:
            - The datacenter name
        required: true
        type: str
    name:
        description:
            - The name of the Port List
        required: true
        type: str
    description:
        description:
            - The description of the Port List
        required: false
        type: str
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        type: str
    ports:
        description:
            - List of port groups with port_begin and optionally port_end
        required: false
        type: list
    ports_nil:
        description:
            - Used on updating to remove all ports
        required: false
        type: bool
        default: false
    child_port_lists:
        description:
            - List of port list names that will be included in this port list
        required: false
        type: list
    child_port_lists_nil:
        description:
            - Used on updating to remove all child port lists
        required: false
        type: bool
        default: false
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

  - name: Create a port list
    ntt_mcp_port_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myPortList
      description: "API Testing"
      ports:
        - port_begin: 80
        - port_begin: 443
          port_end: 444
      state: present

  - name: Create a port list with a child port list
    ntt_mcp_port_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myPortList2
      description: "API Testing2"
      ports:
        - port_begin: 1077
        - port_begin: 1177
          port_end: 1277
      child_port_lists:
        - myPortList
      state: present

  - name: Update a port list
    ntt_mcp_port_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myPortList2
      description: "API Testing2_new"
      ports:
        - port_begin: 1200
        - port_begin: 1177
          port_end: 1500
      child_port_lists_nil: True
      state: present

  - name: Delete a  port list
    ntt_mcp_port_list:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: myPortList2
      state: absent
'''

RETURN = '''
data:
    description: Array of Port List objects
    returned: success
    type: complex
    contains:
        id:
            description: Port List UUID
            type: str
            returned: when state == present
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        description:
            description: Port List description
            type: str
            returned: when state == present
            sample: "My Port List description"
        name:
            description: Port List name
            type: str
            returned: when state == present
            sample: "My Port List"
        createTime:
            description: The creation date of the image
            type: str
            returned: when state == present
            sample: "2019-01-14T11:12:31.000Z"
        state:
            description: Status of the VLAN
            type: str
            returned: when state == present
            sample: NORMAL
        port:
            description: List of ports and/or port ranges
            type: complex
            returned: when state == present
            contains:
                begin:
                    description: The starting port number for this port or range
                    type: int
                    sample: 22
                end:
                    description: The end port number for this range. This is not present for single ports
                    type: int
                    sample: 23
        childPortList:
            description: List of child Port Lists
            type: complex
            returned: when state == present
            contains:
                id:
                    description: The ID of the Port List
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                name:
                    description: The name of the Port List
                    type: str
                    sample: "My Child Port List"
'''

import traceback
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def create_port_list(module, client, network_domain_id):
    """
    Create a port list

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: The created port list object
    """
    return_data = return_object('port_list')
    name = module.params.get('name')
    description = module.params.get('description')
    ports = module.params.get('ports')
    child_port_lists = module.params.get('child_port_lists')
    if name is None:
        module.fail_json(msg='A valid name is required')
    if not ports and not child_port_lists:
        module.fail_json(msg='ports or child_ports_list must have at least one valid entry')
    try:
        client.create_port_list(network_domain_id, name, description, ports, child_port_lists)
        return_data['port_list'] = client.get_port_list_by_name(network_domain_id, name)
    except (KeyError, IndexError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not create the Port List {0}'.format(e))

    module.exit_json(changed=True, data=return_data.get('port_list'))


def update_port_list(module, client, network_domain_id, port_list):
    """
    Update a port list

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg port_list: The dict containing the existing port list to be updated
    :returns: The updated port list dict
    """
    return_data = return_object('port_list')
    name = module.params.get('name')

    try:
        client.update_port_list(network_domain_id,
                                port_list.get('id'),
                                module.params.get('description'),
                                module.params.get('ports'),
                                module.params.get('ports_nil'),
                                module.params.get('child_port_lists'),
                                module.params.get('child_port_lists_nil'))
        return_data['port_list'] = client.get_port_list_by_name(network_domain_id, name)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not update the Port List - {0}'.format(e))

    module.exit_json(changed=True, data=return_data['port_list'])


def compare_port_list(module, client, network_domain_id, port_list, return_all=False):
    """
    Compare two port lists

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of a Cloud Network Domain
    :arg port_list: The dict of the existing port list to be compared to
    :arg return_all: If True returns the full list of changes otherwise just True/False
    :returns: Any differences between the two port lists
    """
    # Handle schema differences between the returned API object and the one required to be sent
    child_port_list_ids = []
    for i in range(len(port_list['childPortList'])):
        child_port_list_ids.append(port_list['childPortList'][i].get('id'))
    port_list.pop('childPortList')
    port_list['childPortListId'] = child_port_list_ids
    port_list.pop('state')
    port_list.pop('createTime')
    new_port_list = client.port_list_args_to_dict(False,
                                                  network_domain_id,
                                                  port_list.get('id'),
                                                  port_list.get('name'),
                                                  module.params.get('description'),
                                                  module.params.get('ports'),
                                                  module.params.get('ports_nil'),
                                                  module.params.get('child_port_lists'),
                                                  module.params.get('child_port_lists_nil'))
    if module.params.get('child_port_lists_nil') or not port_list.get('childPortListId'):
        new_port_list['childPortListId'] = []
    if module.params.get('ports_nil') and not port_list.get('ports'):
        new_port_list['ports'] = []
    compare_result = compare_json(new_port_list, port_list, None)
    # Implement Check Mode
    if module.check_mode:
        module.exit_json(data=compare_result)
    if return_all:
        return compare_result
    return compare_result.get('changes')


def delete_port_list(module, client, port_list):
    """
    Delete a port lists

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg port_list: The dict of the existing port list to be deleted
    :returns: A message
    """
    try:
        client.remove_port_list(port_list.get('id'))
    except (AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not delete the Port List - {0}'.format(e), exception=traceback.format_exc())

    module.exit_json(changed=True)


def main():
    """
    Main function

    :returns: Port list Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            ports=dict(required=False, type='list'),
            ports_nil=dict(required=False, default=False, type='bool'),
            child_port_lists=dict(required=False, type='list'),
            child_port_lists_nil=dict(required=False, default=False, type='bool'),
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

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Get a list of existing port lists
    try:
        port_list = client.get_port_list_by_name(name=name, network_domain_id=network_domain_id)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Failed to get a list of Port Lists - {0}'.format(e), exception=traceback.format_exc())

    if state == 'present':
        if not port_list:
            # Implement check_mode
            if module.check_mode:
                module.exit_json(msg='A new port list will be created with the parameters: {0}'.format(module.params))
            create_port_list(module, client, network_domain_id)
        else:
            if compare_port_list(module, client, network_domain_id, deepcopy(port_list), False):
                update_port_list(module, client, network_domain_id, port_list)
            module.exit_json(data=port_list)
    elif state == 'absent':
        if not port_list:
            module.exit_json(msg='Port List {0} was not found'.format(name))
        # Implement check_mode
        if module.check_mode:
            module.exit_json(msg='This port list will be removed', data=port_list)
        delete_port_list(module, client, port_list)


if __name__ == '__main__':
    main()
