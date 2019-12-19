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
module: ntt_mcp_snapshot_migrate
short_description: Migrate a server currently in preview mode to a production server
description:
    - Migrate a server currently in preview mode to a production server
    - Refer to the Snapshot service documentation at https://docs.mcp-services.net/x/DoBk
version_added: "2.10"
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
            - The name of the Cloud Network Domain
        required: false
        type: str
    name:
        description:
            - The name of the server to migrate
        required: true
        type: str
    wait:
        description:
            - Should Ansible wait for the task to complete before continuing
        required: false
        type: bool
        default: true
    wait_time:
        description:
            - The maximum time the Ansible should wait for the task to complete in seconds
        required: false
        type: int
        default: 1800
    wait_poll_interval:
        description:
            - The time in between checking the status of the task in seconds
        required: false
        type: int
        default: 30
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Migrate (but don't wait for) a server in preview mode
    ntt_mcp_snapshot_preview:
      region: na
      datacenter: NA9
      server: My_Preview_Server

  - name: Migrate a server in preview mode and wait for the completion of the migration
    ntt_mcp_snapshot_preview:
      region: na
      datacenter: NA9
      server: My_Preview_Server
      wait: True

'''
RETURN = '''
msg:
    description: Message on completion
    returned: when wait is True
    type: str
    sample: "The Snapshot Preview server migration has successfully been deployed"
'''
from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException

CORE = {
    'region': None,
    'datacenter': None,
    'network_domain_id': None,
    'name': None}


def wait_for_migration(module, client, server_id):
    """
    Wait for the preview server.

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server_id: The UUID of the server

    :returns: The server dict
    """
    state = 'NORMAL'
    set_state = wait_required = False
    actual_state = ''
    time = 0
    wait_time = module.params.get('wait_time')
    wait_poll_interval = module.params.get('wait_poll_interval')
    server = None
    while not set_state and time < wait_time:
        try:
            server = client.get_server_by_id(server_id=server_id)
        except NTTMCPAPIException as e:
            module.fail_json(msg='Failed to get a list of servers - {0}'.format(e))
        try:
            actual_state = server.get('state')
        except (KeyError, IndexError):
            module.fail_json(msg='Failed to get the current state for the server with ID - {0}'.format(server_id))

        if actual_state != state:
            wait_required = True
        else:
            wait_required = False

        if wait_required:
            sleep(wait_poll_interval)
            time = time + wait_poll_interval
        else:
            set_state = True

    if server and time >= wait_time:
        return None

    return server


def main():
    """
    Main function
    :returns: A message
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=False, default=None, type='str'),
            name=dict(required=True, type='str'),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=1800, type='int'),
            wait_poll_interval=dict(required=False, default=30, type='int'),
        ),
        supports_check_mode=True
    )
    result = None
    CORE['name'] = module.params.get('name')
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

    try:
        client = NTTMCPClient(credentials, module.params.get('region'))
    except NTTMCPAPIException as e:
        module.fail_json(msg=e.msg)

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=module.params.get('network_domain'),
                                                    datacenter=module.params.get('datacenter'))
        CORE['network_domain_id'] = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(module.params.get('network_domain')))

    try:
        server = client.get_server_by_name(datacenter=module.params.get('datacenter'),
                                           network_domain_id=network.get('id'),
                                           name=CORE.get('name'))
        if not server:
            module.fail_json(msg='Could not find the server - {0} in {1}'.format(module.params.get('name'),
                                                                                 module.params.get('datacenter')))
    except (KeyError, IndexError, AttributeError):
        module.fail_json(msg='Could not find the server - {0} in {1}'.format(module.params.get('name'),
                                                                             module.params.get('datacenter')))

    try:
        if module.check_mode:
            module.exit_json('Server with ID {0} will be migrated from preview mode'.format(server.get('id')))
        result = client.migrate_snapshot_preview(server.get('id'))
        if result.get('responseCode') != 'IN_PROGRESS':
            module.fail_json(msg='The Snapshot server migration failed with reason - {0}'.format(result.get('responseCode')))
        wait_for_migration(module, client, server.get('id'))
        module.exit_json(msg='The Snapshot Preview server migration was successful')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not retrieve the Snapshot - {0}'.format(e))


if __name__ == '__main__':
    main()
