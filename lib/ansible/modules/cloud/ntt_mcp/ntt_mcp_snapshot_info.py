#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Ken Sinfield <ken.sinfield@cis.ntt.com>
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
module: ntt_mcp_snapshot_info
short_description: List/Get information about Snapshots
description:
    - List/Get information about Snapshots
version_added: 2.10
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
        required: false
        type: str
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: false
        type: str
    server:
        description:
            - The name of a server to enable Snapshots on
        required: false
        type: str
    service_plan:
        description:
            - The name of a desired Service Plan. Use ntt_mcp_snapshot_info to get a list of valid plans.
        required: false
        type: str
    type:
        description:
            - The type of entity to get/list information about
        required: false
        default: window
        type: str
        choices:
            - window
            - plan
            - snapshot
            - server
    start_hour:
        description:
            - The starting hour for the snapshot window (24 hour notation). Use ntt_mcp_snapshot_info to find a window.
        required: false
        type: int
    slots_available:
        description:
            - Only show windows with slots available
        required: false
        default: True
        type: bool
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: List Snapshot Windows
    ntt_mcp_snapshot_info:
      region: na
      datacenter: NA9
      service_plan: ONE_MONTH

  - name: Get a specific Snapshot Window for 8am
    ntt_mcp_snapshot_info:
      region: na
      datacenter: NA9
      service_plan: ONE_MONTH
      start_hour: 8

  - name: List Snapshot Plans
    ntt_mcp_snapshot_info:
      region: na
      datacenter: NA9
      type: plan

  - name: Get the Snapshot service configuration for a server
    ntt_mcp_snapshot_service:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      name: My_Server
      type: server

'''
RETURN = '''
data:
    description: Snapshot objects
    returned: success
    type: complex
    contains:
        count:
            description: The number of entities returned
            returned: on a list operation
            type: int
            sample: 1
        contains:
            snapshot_info:
                description: List or object instance of the searched for entities
                returned: success
                type: complex
                contains:
                    available:
                        description: When "true" indicates that the plan is available for use
                        returned: type == plan
                        type: bool
                    description:
                        description: More detailed description of what comprises the plan.
                        returned: type == plan
                        type: str
                        sample: "Daily Snapshots retained for 14 Days, Weekly Snapshots retained for 90 Days"
                    displayName:
                        description: Simple text display name. Useful for reference and display in UI integration.
                        returned: type == plan
                        type: str
                        sample: "One Month: 7d-4w"
                    id:
                        description: String UID or UUID identifying the entity
                        returned: success
                        type: str
                        sample: ONE_MONTH or d62596e8-fe2b-44ba-8ad2-a669b9dfcb51
                    snapshotFrequency:
                        description: The frequency of SYSTEM snapshots for the plan. Values are DAILY and WEEKLY
                        returned: type == plan
                        type: str
                        sample: DAILY
                    supportsReplication:
                        description: When True indicates that the plan supports Snapshot Replication
                        returned: type == plan
                        type: str
                    availabilityStatus:
                        description: RESERVED_FOR_MAINTENANCE, AVAILABLE or NOT_CURRENTLY_AVAILABLE
                        returned: type == window
                        type: str
                        sample: OVERLAPS_WITH_MAINTENANCE
                    availableSlotCount:
                        description: The number of available slots in the Snapshot Window
                        returned: type == window
                        type: int
                        sample: 59
                    dayOfWeek:
                        description: Which day it the Snapshot is taken on (this should always be daily)
                        returned: type == window
                        type: str
                        sample: DAILY
                    startHour:
                        description: Snapshot Windows begin on 2 hour periods
                        returned: type == window
                        type: int
                        sample: 8
                    timeZone:
                        description: The timeZone that the Snapshot Window is relative to
                        returned: type == window
                        type: str
                        sample: Etc/UTC
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def get_server_snapshot_info(module, client):
    network_domain_name = module.params.get('network_domain')
    server_name = module.params.get('server')
    datacenter = module.params.get('datacenter')

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(e))

    # Check if the Server exists based on the supplied name
    try:
        server = client.get_server_by_name(datacenter=datacenter,
                                           network_domain_id=network_domain_id,
                                           name=server_name)
        # server = client.get_server_by_name(server_name)
        if not server.get('id'):
            raise NTTMCPAPIException('No server found for {0}'.format(server_name))
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not locate any existing server - {0}'.format(e))

    return server.get('snapshotService', {})


def main():
    """
    Main function
    :returns: Snapshot Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=False, type='str'),
            service_plan=dict(required=False, type='str'),
            start_hour=dict(required=False, default=None, type='int'),
            slots_available=dict(required=False, default=True, type='bool'),
            type=dict(required=False, default='window', choices=['window', 'server', 'plan', 'snapshot']),
            network_domain=dict(required=False, default=None, type='str'),
            server=dict(required=False, default=None, type='str'),
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    snapshot_type = module.params.get('type')
    return_data = return_object('snapshot_info')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTMCPClient(credentials, module.params.get('region'))

    try:
        if snapshot_type == 'window':
            result = client.list_snapshot_windows(module.params.get('datacenter'),
                                                  module.params.get('service_plan'),
                                                  module.params.get('start_hour'),
                                                  module.params.get('slots_available'))
        if snapshot_type == 'plan':
            result = client.list_snapshot_service_plans(module.params.get('service_plan'),
                                                        module.params.get('slots_available'))
        if snapshot_type == 'server':
            result = get_server_snapshot_info(module, client)

        if result:
            return_data['snapshot_info'] = result
            return_data['count'] = len(return_data.get('snapshot_info'))
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not retrieve a list of Snapshot info - {0}'.format(e))

    module.exit_json(data=return_data)


if __name__ == '__main__':
    main()
