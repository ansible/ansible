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
module: ntt_mcp_snapshot
short_description: Initiate, update or delete a manual snapshot on a server
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
    id:
        description:
            - The UUID of the snapshot to delete
        required: false
        type: str
    description:
        description:
            - Optional description for the manual snapshot
        required: false
        type: str
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

  - name: Initiate a manual snapshot
    ntt_mcp_snapshot_info:
      region: na
      datacenter: NA9
      server: myServer
      description: A random snapshot

  - name: Update the metadata on a manual snapshot
    ntt_mcp_snapshot_info:
      region: na
      id: 112b7faa-ffff-ffff-ffff-dc273085cbe4
      description: A random snapshot description

  - name: Delete a manual snapshot
    ntt_mcp_snapshot_info:
      region: na
      id: 112b7faa-ffff-ffff-ffff-dc273085cbe4
      state: absent
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def main():
    """
    Main function
    :returns: Initiate a Snapshot
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=False, type='str'),
            network_domain=dict(required=False, default=None, type='str'),
            server=dict(required=False, default=None, type='str'),
            description=dict(required=False, default=None, type='str'),
            id=dict(required=False, default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )
    state = module.params.get('state')
    result = None
    server = {}
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    server_name = module.params.get('server')

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
        if state == 'present':
            if module.params.get('id') and module.params.get('description'):
                if module.check_mode:
                    module.exit_json(msg='The snapshot {0} will be updated with the descriprition: {1}'.format(
                        module.params.get('id'),
                        module.params.get('description')
                    ))
                # If there is an ID and a description assume an update to the snapshot metadata
                if client.update_snapshot(module.params.get('id'), module.params.get('description')):
                    result = module.params.get('id')
            else:
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
                    if not server.get('id'):
                        raise NTTMCPAPIException('No server found for {0}'.format(server_name))
                except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
                    module.fail_json(msg='Could not locate any existing server - {0}'.format(e))

                if module.check_mode:
                    if server.get('snapshotService'):
                        module.exit_json(msg='A Snapshot will be taken for server ID: {0}'.format(server.get('id')))
                    else:
                        module.warn(warning='Snapshots are not enabled for server ID: {0}'.format(server.get('id')))
                        module.exit_json(msg='No Snapshot can be taken')

                # Take the snapshot
                result = client.manual_snapshot(server.get('id'), module.params.get('description'))

            if result:
                module.exit_json(changed=True, data=result)
            module.fail_json(msg='Could not ascertain the status of the manual snapshot. Check manually')
        elif state == 'absent':
            if module.params.get('id') is None:
                module.fail_json(msg='Argument "id" is required when deleting a manual snapshot')
            if module.check_mode:
                module.exit_json(msg='Snapshot with ID {0} will be deleted'.format(module.params.get('id')))
            if client.delete_snapshot(module.params.get('id')):
                module.exit_json(changed=True, msg='The manual snapshot was successfully deleted')
            module.fail_json(msg='Could not ascertain the status of the snapshot deletion. Check manually')

    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not initiate a manual Snapshot: {0}'.format(e))


if __name__ == '__main__':
    main()
