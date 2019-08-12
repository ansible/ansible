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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nttc_cis_port_list_info
short_description: List/Get Firewall Port Lists
description:
    - List/Get Firewall Port Lists
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
            - The name of the Port List
        required: false
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
notes:
    - N/A
'''

EXAMPLES = '''
# List Port Lists
- nttc_cis_port_list_facts:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
# Get a specific Port List
- nttc_cis_port_list_facts:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      name: "APITEST"
'''

RETURN = '''
data:
    description: dict of returned Objects
    type: complex
    returned: success
    contains:
        count:
            description: The number of objects returned
            returned: success
            type: int
            sample: 1
        port_list:
            description: Array of Port List object
            returned: success
            type: complex
            contains:
                id:
                    description: Port List UUID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                description:
                    description: Port List description
                    type: str
                    sample: "My Port List description"
                name:
                    description: Port List name
                    type: str
                    sample: "My Port List"
                createTime:
                    description: The creation date of the image
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                state:
                    description: Status of the VLAN
                    type: str
                    sample: NORMAL
                port:
                    description: List of ports and/or port ranges
                    type: complex
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def main():
    """
    Main function
    :returns: Port List Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            name=dict(required=False, type='str'),
            network_domain=dict(required=True, type='str')
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    name = module.params.get('name')
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    return_data = return_object('port_list')

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except NTTCCISAPIException as e:
        module.fail_json(msg='Failed to get a list of Cloud Network Domains - {0}'.format(e))

    try:
        if name:
            result = client.get_port_list_by_name(network_domain_id, name)
            if result:
                return_data['port_list'].append(result)
        else:
            return_data['port_list'] = client.list_port_list(network_domain_id)
    except (KeyError, IndexError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not retrieve a list of the Port Lists - {0}'.format(e))

    return_data['count'] = len(return_data.get('port_list'))
    module.exit_json(data=return_data)


if __name__ == '__main__':
    main()
