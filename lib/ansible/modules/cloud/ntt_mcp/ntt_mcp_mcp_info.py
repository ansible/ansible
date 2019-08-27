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
module: ntt_mcp_mcp_info
short_description: Get NTT LTD MCP datacenter Information
description:
    - Get NTT LTD MCP datacenter Information
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
    id:
        description:
            - The id of an MCP (e.g. NA9)
        required: false
        type: str
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: GET a list of MCPs
    ntt_mcp_mcp_facts:
      region: na

  - name: Get details on a specific MCP
    ntt_mcp_mcp_facts:
      region: na
      name: NA9
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
        mcp:
            description: List of MCP Objects
            returned: success
            type: complex
            contains:
                consoleAccess:
                    description: Object containing information on the virtual console status within an MCP
                    type: complex
                    contains:
                        maintenanceStatus:
                            description: The maintenance status of the console service with in the MCP
                            type: str
                            sample: "NORMAL"
                city:
                    description: The city the MCP is located in
                    type: str
                    sample: "xxxx"
                networking:
                    description: The networking capabilities of the MCP
                    type: complex
                    contains:
                        maintenanceStatus:
                            description: The maintenance status of the network within the MCP
                            type: str
                            sample: "NORMAL"
                        property:
                            description: List of network properties and values for the MCP
                            type: list
                            contains:
                                name:
                                    description: The name of the networking property
                                    type: str
                                    sample: "MAX_POOL_MEMBERS_PER_POOL"
                                value:
                                    description: The value for the networking property
                                    type: str
                                    sample: "100"
                        type:
                            description: Internal Use
                            type: str
                            sample: "2"
                displayName:
                    description: The UI display name for the MCP
                    type: str
                    sample: "US - East 3 - MCP 2.0"
                vpnUrl:
                    description: The VPN URL for client MCP VPN access
                    type: str
                    sample: "xxxx.xxx.xxx"
                country:
                    description: The country the MCP resides in
                    type: str
                    sample: "US"
                state:
                    description: The state the MCP resides in
                    type: str
                    sample: "Virginia"
                snapshot:
                    description: Object containing the snapshot capabilities for the MCP
                    type: complex
                    contains:
                        maintenanceStatus:
                            description: The maintenance status for snapshots within the MCP
                            type: str
                            sample: "NORMAL"
                        property:
                            description: List of the snapshot capabilities in the MCP
                            type: list
                            contains:
                                name:
                                    description: The name of the snapshot property
                                    type: str
                                    sample: "MAX_MANUAL_SNAPSHOTS_PER_SERVER"
                                value:
                                    description: The value of the snapshot property
                                    type: str
                                    sample: "10"
                type:
                    description: The type/version of the MCP
                    type: str
                    sample: "MCP 2.0"
                hypervisor:
                    description: Objecting containing the hypervisor capabilities for the MCP
                    type: complex
                    contains:
                        diskSpeed:
                            description: List of disk speed options within the MCP
                            type: list
                            contains:
                                available:
                                    description: Is the disk speed currently available
                                    type: bool
                                displayName:
                                    description: The UI display name for the disk speed
                                    type: str
                                    sample: "Standard"
                                description:
                                    description: The description for the disk speed
                                    type: str
                                    sample: "Standard Disk Speed"
                                default:
                                    description: Is this the default disk speed option
                                    type: bool
                                variableIops:
                                    description: Does this disk speed support variable IOPs
                                    type: bool
                                abbreviation:
                                    description: Shortcode for the disk speed
                                    type: str
                                    sample: "STD"
                                id:
                                    description: The ID for the disk speed object
                                    type: str
                                    sample: "STANDARD"
                                variableIopLimits:
                                    description: Object containing the information on variable IOPS limits for the disk speed
                                    type: complex
                                    contains:
                                        maxDiskIops:
                                            description: The maximum supported IOPS for the disk
                                            type: int
                                            sample: 1
                                        minIopsPerGb:
                                            description: The minimum supported IOPS per GB of disk space
                                            type: int
                                            sample: 1
                                        minDiskIops:
                                            description: The minimum supported IOPS for the disk
                                            type: int
                                            sample: 1
                                        maxIopsPerGb:
                                            description: The maximum supported IOPS per GB of disk space
                                            type: int
                                            sample: 1
                        maintenanceStatus:
                            description: The maintenance status of the MCP
                            type: str
                            sample: "NORMAL"
                        property:
                            description: List of hypervisor properties and values
                            type: list
                            contains:
                                name:
                                    description: The name of the hypervisor property
                                    type: str
                                    sample: "MIN_DISK_COUNT"
                                value:
                                    description: The value of the hypervisor property
                                    type: str
                                    sample: 0
                        type:
                            description: The hyervisor type
                            type: str
                            sample: "xxxx"
                        cpuSpeed:
                            description: List of hypervisor CPU speeds
                            type: list
                            contains:
                                available:
                                    description: Is the CPU speed available for the hypervisor in this MCP
                                    type: bool
                                default:
                                    description: Is this the default CPU speed
                                    type: bool
                                displayName:
                                    description: The UI display name for the CPU speed
                                    type: str
                                    sample: "Standard"
                                description:
                                    description: The description of the CPU speed
                                    type: str
                                    sample: "Standard CPU Speed"
                                id:
                                    description: The ID of the CPU speed object
                                    type: str
                                    sample: "STANDARD"
                monitoring:
                    description: Object containing monitoring information within the MCP
                    type: complex
                    contains:
                        maintenanceStatus:
                            description: The maintenance status of monitoring within the MCP
                            type: str
                            sample: "NORMAL"
                ftpsHost:
                    description: The FTPS host for copying images to/from the MCP
                    type: str
                    sample: "xxxx.xxxxx.xxx"
                backup:
                    description: Object containing backup information within the MCP
                    type: complex
                    contains:
                        maintenanceStatus:
                            description: The maintenance status of backups within the MCP
                            type: str
                            sample: "NORMAL"
                        type:
                            description: The type of backups available in the MCP
                            type: str
                            sample: "xxxxxx"
                id:
                    description: The ID of the MCP
                    type: str
                    sample: "NA9"
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def get_dc(module, client):
    """
    Gets a the specified DC/MCP

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :returns: MCP Information
    """
    return_data = return_object('mcp')
    dc_id = module.params['id']

    try:
        result = client.get_dc(dc_id=dc_id)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not get a list of MCPs - {0}'.format(exc), exception=traceback.format_exc())
    try:
        return_data['count'] = result.get('totalCount')
        return_data['mcp'] = result.get('datacenter')
    except (KeyError, AttributeError):
        pass

    module.exit_json(data=return_data)


def main():
    """
    Main function

    :returns: MCP Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            id=dict(required=False, type='str')
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
    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    get_dc(module=module, client=client)


if __name__ == '__main__':
    main()
