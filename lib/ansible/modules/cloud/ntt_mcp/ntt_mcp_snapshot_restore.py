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
module: ntt_mcp_snapshot_restore
short_description: Initiate or delete a manual snapshot on a server
description:
    - Initiate a manual snapshot on a server
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
    id:
        description:
            - The UUID of the source snapshot to use
        required: true
        type: str
    src_path:
        description:
            - The full source path to the file/directory to restore
        required: true
        type: str
    dst_path:
        description:
            - The full destination path to the file/directory to restore
        required: true
        type: str
    username:
        description:
            - The OS username with permissions to access the destination file
        required: true
        type: str
    password:
        description:
            - The OS user password
        required: true
        type: str
    wait:
        description:
            - Should Ansible wait for the task to complete before continuing
        required: false
        type: bool
        default: false
    wait_time:
        description:
            - The maximum time the Ansible should wait for the task to complete in seconds
        required: false
        type: int
        default: 3600
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

  - name: Initiate a manual snapshot
    ntt_mcp_snapshot_info:
      region: na
      datacenter: NA9
      server: myServer
      description: A random snapshot

  - name: Delete a manual snapshot
    ntt_mcp_snapshot_info:
      region: na
      id: 112b7faa-ffff-ffff-ffff-dc273085cbe4
      state: A random snapshot
'''
RETURN = '''
data:
    description: Manual snapshot UUID
    returned: success
    type: str
    sample: 112b7faa-ffff-ffff-ffff-dc273085cbe4
msg:
    description: Message
    returned: fail
    type: str
    sample: Could not ascertain the status of the snapshot deletion. Check manually
'''

from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def wait_for_snapshot(module, client, server_id):
    """
    Wait for an operation on a server. Polls based on wait_time and wait_poll_interval values.

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg name: The name of the server
    :arg server_id: The UUID of the server
    :returns: True/False
    """
    state = 'NORMAL'
    set_state = False
    actual_state = None
    time = 0
    wait_time = module.params.get('wait_time')
    wait_required = False
    wait_poll_interval = module.params.get('wait_poll_interval')
    server = []
    while not set_state and time < wait_time:
        try:
            server = client.get_server_by_id(server_id=server_id)
        except NTTMCPAPIException as e:
            module.fail_json(msg='Failed to check the server - {0}'.format(e))
        actual_state = server.get('state')
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
        return False

    return True


def main():
    """
    Main function
    :returns: A message
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            id=dict(required=True, type='str'),
            src_path=dict(required=True, type='str'),
            dst_path=dict(required=True, type='str'),
            username=dict(required=True, type='str'),
            password=dict(required=True, type='str'),
            wait=dict(required=False, default=False, type='bool'),
            wait_time=dict(required=False, default=3600, type='int'),
            wait_poll_interval=dict(required=False, default=30, type='int')
        ),
        supports_check_mode=True
    )

    result = snapshot = None
    snapshot_id = module.params.get('id')

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

    try:
        snapshot = client.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            module.fail_json(msg='Snapshot with ID {0} does not exist'.format(snapshot_id))
        if module.check_mode:
            module.exit_json(msg='A snapshot restore will be performed')
        result = client.snapshot_restore(snapshot_id,
                                         module.params.get('src_path'),
                                         module.params.get('dst_path'),
                                         module.params.get('username'),
                                         module.params.get('password'))
        if module.params.get('wait'):
            server_id = next((item for item in result.get('info') if item["name"] == "serverId"), dict()).get('value')
            if not server_id:
                module.fail_json(msg='Snapshot restore was successful but could not find the server to wait for status updates')
            wait_for_snapshot(module, client, server_id)
            module.exit_json(changed=True, msg='The file/directory have been successfully restored')
        module.exit_json(changed=True, msg='The restoration process is in progress. '
                         'Check the status manually or use ntt_mcp_server_info')

    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Error restoring the file: {0}'.format(e))


if __name__ == '__main__':
    main()
