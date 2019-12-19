#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Ken Sinfield <ken.sinfield@cis.ntt.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_geo_info
short_description: Get NTT LTD Cloud Geo Information
description:
    - Get NTT LTD Cloud Information
version_added: "2.10"
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region API endpoint to
        required: false
        type: str
        default: na
    id:
        description:
            - The id of the infrastructure entity
        required: false
        type: str
    name:
        description:
            - The name of the infrastructure entity
        required: false
        type: str
    is_home:
        description:
            - Boolean flag to allow a user to just retrieve the home geo for their account if unknown
        required: false
        type: bool
        default: false
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Get a list of datacenters
    ntt_mcp_geo_info:
      region: eu

  - name: Get a specific datacenter
    ntt_mcp_geo_info:
      region: eu
      name: Israel
'''

RETURN = '''
data:
    description: dict of returned Objects
    type: complex
    returned: success
    contains:
        count:
            description: The number of GEO objects returned
            returned: success
            type: int
        geo:
            description: List of GEO objects
            returned: success
            type: complex
            contains:
                id:
                    description: Object ID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                cloudApiHost:
                    description: The API endpoint URL for this geo
                    type: str
                cloudUiUrl:
                    description: The Web UI URL for this geo
                    type: str
                ftpsHost:
                    description: The FTPS server for this geo
                    type: str
                isHome:
                    description: Is this the home geo for the user
                    type: bool
                monitoringUrl:
                    description: The monitoring service URL for this geo
                    type: str
                name:
                    description: The geo common name
                    type: str
                state:
                    description: The state of the geo
                    type: str
                    sample: ENABLED
                timezone:
                    description: The timezone for this geo
                    type: str
                    sample: America/New_York
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def get_geo(module, client):
    """
    List all data geographical regions for a given network domain

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain

    :returns: List of firewall rules
    """
    return_data = return_object('geo')

    geo_id = module.params.get('id')
    geo_name = module.params.get('name')
    is_home = module.params.get('is_home')

    try:
        result = client.get_geo(geo_id=geo_id, geo_name=geo_name, is_home=is_home)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not get a list of Geos - {0}'.format(exc))
    try:
        return_data['count'] = result.get('totalCount')
        return_data['geo'] = result.get('geographicRegion')
    except KeyError:
        pass

    module.exit_json(data=return_data)


def main():
    """
    Main function

    :returns: GEO Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            id=dict(required=False, type='str'),
            name=dict(required=False, type='str'),
            is_home=dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    # Create the API client
    client = NTTMCPClient(credentials, module.params.get('region'))

    get_geo(module=module, client=client)


if __name__ == '__main__':
    main()
