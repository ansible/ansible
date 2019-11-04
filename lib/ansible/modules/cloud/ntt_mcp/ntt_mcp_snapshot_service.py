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
module: ntt_mcp_snapshot_service
short_description: Enable/Disable and Update the Snapshot Service on a server
description:
    - Enable/Disable and Update the Snapshot Service on a server
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
        required: true
        type: str
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        type: str
    server:
        description:
            - The name of a server to enable Snapshots on
        required: true
        type: str
    service_plan:
        description:
            - The name of a desired Service Plan. Use ntt_mcp_snapshot_info to get a list of valid plans.
        required: true
        type: str
    start_hour:
        description:
            - The starting hour for the snapshot window (24 hour notation). Use ntt_mcp_snapshot_info to find a window.
        required: true
        type: int
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

  - name: Enable Snapshots at 8am
    ntt_mcp_snapshot_service:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      name: My_Server
      service_plan: ONE_MONTH
      start_hour: 8
      state: present

  - name: Update Snapshot config on a server
    ntt_mcp_snapshot_service:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      name: My_Server
      service_plan: TWELVE_MONTH
      start_hour: 10
      state: present

  - name: Disable Snapshots
    ntt_mcp_snapshot_service:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      name: My_Server
      state: absent
'''
RETURN = '''
msg:
    description: Status of the operation
    returned: always
    type: str
'''

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def enable_snapshot(module, client, server_id, service_plan, window_id):
    """
    Enable the Snapshot Service on a server

    :arg module: The Ansible module instance
    :arg client: The CC API provider instance
    :arg server_id: The UUID of the server
    :arg service_plan: The service plan to use (e.g. ONE_MONTH)
    :arg window_id: The UUID of the snapshot Window
    :returns: Message on exit
    """
    try:
        result = client.enable_snapshot_service(False, server_id, service_plan, window_id)
        if result.get('responseCode') == 'OK':
            module.exit_json(changed=True, msg='Snapshots successfully enabled')
        else:
            module.fail_json(msg='Failed to enable Snapshosts: {0}'.format(str(result)))
    except (AttributeError, KeyError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed to enable Snapshosts: {0}'.format(e))


def update_snapshot(module, client, server_id, service_plan, window_id):
    """
    Enable the Snapshot Service on a server

    :arg module: The Ansible module instance
    :arg client: The CC API provider instance
    :arg server_id: The UUID of the server
    :arg service_plan: The service plan to use (e.g. ONE_MONTH)
    :arg window_id: The UUID of the snapshot Window
    :returns: Message on exit
    """
    try:
        result = client.enable_snapshot_service(True, server_id, service_plan, window_id)
        if result.get('responseCode') == 'OK':
            module.exit_json(changed=True, msg='Snapshot Service configuration has been successfully updated')
        else:
            module.fail_json(msg='Failed to update Snapshost Service configuration: {0}'.format(str(result)))
    except (AttributeError, KeyError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed to update Snapshost Service configuration: {0}'.format(e))


def disable_snapshot(module, client, server_id):
    """
    Disable the Snapshot Service on a server

    :arg module: The Ansible module instance
    :arg client: The CC API provider instance
    :arg server_id: The UUID of the server
    :returns: Message on exit
    """
    try:
        result = client.disable_snapshot_service(server_id)
        if result.get('responseCode') == 'OK':
            module.exit_json(changed=True, msg='Snapshots successfully disabled')
        else:
            module.fail_json(msg='Failed to disable Snapshosts: {0}'.format(str(result)))
    except (AttributeError, KeyError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed to disable Snapshosts: {0}'.format(e))


def compare_snapshot(module, snapshot_config):
    """
    Compare the existing Snapshot config to the provided arguments

    :arg module: The Ansible module instance
    :arg snapshot_config: The dict containing the existing Snapshot config to compare to
    :returns: Any differences between the the Snapshot configs
    """
    new_config = deepcopy(snapshot_config)
    new_config['servicePlan'] = module.params.get('service_plan')
    new_config['window'] = {
        'dayOfWeek': '',
        'startHour': module.params.get('start_hour')
    }
    if module.params.get('service_plan') in ['ONE_MONTH', 'THREE_MONTH', 'TWELVE_MONTH']:
        new_config['window']['dayOfWeek'] = 'DAILY'

    compare_result = compare_json(new_config, snapshot_config, None)
    # Implement Check Mode
    if module.check_mode:
        module.exit_json(data=compare_result)
    return compare_result['changes']


def get_window_id(module, client):
    """
    Search for the Snapshot Window and return the UUID

    :arg module: The Ansible module instance
    :arg client: The CC API provider instance
    :returns: The Window UUID
    """
    window_id = None
    try:
        result = client.list_snapshot_windows(module.params.get('datacenter'),
                                              module.params.get('service_plan'),
                                              module.params.get('start_hour'),
                                              module.params.get('slots_available'))
        window_id = result[0].get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not retrieve the required Snapshot Window - {0}'.format(e))
    return window_id


def main():
    """
    Main function
    :returns: Snapshot Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            server=dict(required=True, type='str'),
            service_plan=dict(required=True, type='str'),
            start_hour=dict(required=True, type='int'),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    state = module.params.get('state')
    datacenter = module.params.get('datacenter')
    network_domain_name = module.params.get('network_domain')
    server_name = module.params.get('server')
    service_plan = module.params.get('service_plan')
    window_id = None
    network_domain_id = None
    server_id = None
    server = None

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTMCPClient(credentials, module.params.get('region'))

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
            raise NTTMCPAPIException('No server object found for {0}'.format(server_name))
        server_id = server.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not locate any existing server - {0}'.format(e))

    if state == 'present':
        # Attempt to find the Window for the specified Service Plan
        window_id = get_window_id(module, client)
        if not server.get('snapshotService'):
            if module.check_mode:
                module.exit_json(msg='Input verified, Snapshots can be enabled for the server')
            enable_snapshot(module, client, server_id, service_plan, window_id)
        else:
            if compare_snapshot(module, server.get('snapshotService')):
                update_snapshot(module, client, server_id, service_plan, window_id)
            else:
                module.exit_json(msg='No update required.')
    elif state == 'absent':
        if not server.get('snapshotService'):
            module.exit_json(msg='Snapshots are not currently configured for this server')
        if module.check_mode:
            module.exit_json(msg='The Snapshot service and all associated snapshots will be removed from this server')
        disable_snapshot(module, client, server_id)


if __name__ == '__main__':
    main()
