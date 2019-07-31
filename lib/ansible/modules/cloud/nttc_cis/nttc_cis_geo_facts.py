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
module: nttc_cis_geo_facts
short_description: Get NTTC CIS Cloud Geo Information
description:
    - Get NTTC CIS Cloud Information
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region API endpoint to
        required: false
        default: na
        choices:
          - Valid values can be found in nttcis.common.config.py under
            APIENDPOINTS
    id:
        description:
            - The id of the infrastructure entity
        required: false
    name:
        description:
            - The name of the infrastructure entity
        required: false
notes:
    - N/A
'''

EXAMPLES = '''
# Get a list of geographic regions
- name: Get a list of geo's
  nttc_cis_geo_facts:
    region: na
# Get a specific geographic region by name
- name: Get a specific geographic region
  nttc_cis_geo_facts:
    region: na
    name: North America
'''

RETURN = '''
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
            type: boolean
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
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def get_geo(module, client):
    """
    List all data geographical regions for a given network domain

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain

    :returns: List of firewall rules
    """
    return_data = return_object('geo')

    geo_id = module.params['id']
    geo_name = module.params['name']
    is_home = module.params['is_home']

    try:
        result = client.get_geo(geo_id=geo_id, geo_name=geo_name, is_home=is_home)
    except NTTCCISAPIException as exc:
        module.fail_json(msg='Could not get a list of Geos - {0}'.format(exc.message))
    try:
        return_data['count'] = result['totalCount']
        return_data['geo'] = result['geographicRegion']
    except KeyError:
        pass

    module.exit_json(results=return_data)


def main():
    """
    Main function

    :returns: GEO Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            id=dict(required=False, type='str'),
            name=dict(required=False, type='str'),
            is_home=dict(default=False, type='bool')
        ),
        supports_check_mode=True
    )

    credentials = get_credentials()

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    # Create the API client
    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    get_geo(module=module, client=client)


if __name__ == '__main__':
    main()
