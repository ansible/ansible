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
module: nttc_cis_os_facts
short_description: Get NTTC CIS Supported Operating System Information
description:
    - Get NTTC CIS Supported Operating System Information
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
    id:
        description:
            - The id of the infrastructure entity, supports wildcard matching with "*" e.g. "*Centos*"
        required: false
    name:
        description:
            - The name of the infrastructure entity, supports wildcard matching with "*" e.g. "*Centos*"
        required: false
    family:
        description:
            - The OS family name of the infrastructure entity
        required: false
        choices:
            - UNIX, WINDOWS
notes:
    - N/A
'''

EXAMPLES = '''
# List all available Centos operating systems
- name: Get a list of Operating Systems
  nttc_cis_os_facts:
    region: na
    name: "*Centos*"
# Get a specific Centos operating system's details
- name: Get the CENTOSX32 operating system detils
  nttc_cis_os_facts:
    region: na
    id: "CENTOSX32"
'''

RETURN = '''
count:
    description: The total count of found/returned objects
    returned: success
    type: int
    sample: 5
os:
    description: A list of operating systems
    returned: success
    type: complex
    contains:
        displayName:
            description: The common name for the OS
            type: str
            sample: "CENTOS7/64"
        family:
            description: OS family
            type: str
            sample: "UNIX"
        id:
            description: OS ID
            type: str
            sample: "CENTOS764"
        networkAdapter:
            description: List of supported network adapters
            type: complex
            contains:
                default:
                    description: Is this the default adapter type for the OS
                    type: bool
                    sample: false
                name:
                    description: The adapter name
                    type: str
                    sample: "VMXNET3"
        osUnitsGroupId:
            description: The OS billing group
            type: str
            sample: "CENTOS"
        scsiAdapterType:
            description: List of supported SCSI adapter types for this OS
            type: complex
            contains:
                adapterType:
                    description: The name of the adapter
                    type: str
                    sample: "LSI_LOGIC_SAS"
                default:
                    description: Is this the default adapter type for the OS
                    type: bool
                    sample: false
        supportsBackup:
            description: Does this OS support NTTC-CIS Backup as a Service
            type: bool
            sample: true
        supportsGuestOsCustomization:
            description:  Does this OS support guest OS cusomtizations
            type: bool
            sample: true
        supportsOvfImport:
            description: Does this OS support OVF importing via NTTC-CIS Cloud Control
            type: bool
            sample: true
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def get_os(module, client):
    """
    List OS Information
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :returns: OS object
    """
    return_data = return_object('os')
    os_id = module.params['id']
    os_name = module.params['name']
    os_family = module.params['family']

    try:
        result = client.get_os(os_id=os_id, os_name=os_name, os_family=os_family)
    except NTTCCISAPIException as exc:
        module.fail_json(msg='Could not get a list of operating systems - {0}'.format(exc.message), exception=traceback.format_exc())
    try:
        return_data['count'] = result['totalCount']
        return_data['os'] = result['operatingSystem']
    except KeyError:
        pass

    module.exit_json(results=return_data)


def main():
    """
    Main function
    :returns: OS Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            id=dict(required=False, type='str'),
            name=dict(required=False, type='str'),
            family=dict(required=False, choices=['UNIX', 'WINDOWS'])
        ),
        supports_check_mode=True
    )

    credentials = get_credentials()

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    # Create the API client
    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    get_os(module=module, client=client)


if __name__ == '__main__':
    main()
