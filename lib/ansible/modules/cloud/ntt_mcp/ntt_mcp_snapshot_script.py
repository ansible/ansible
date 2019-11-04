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
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def enable_scripts(module, client, network_domain_id, server_id):
    return None


def update_scripts(module, client, network_domain_id, server):
    return None


def disable_scripts(module, client, network_domain_id, server_id):
    return None


def compare_scripts(module, snapshot_config):
    """
    Compare the existing Snapshot config to the provided arguments

    :arg module: The Ansible module instance
    :arg snapshot_config: The dict containing the existing Snapshot config to compare to
    :returns: Any differences between the the Snapshot configs
    """

    old_config = {
        'preSnapshotScript': snapshot_config.get('preSnapshotScript'),
        'postSnapshotScript': snapshot_config.get('postSnapshotScript')
    }

    new_config = {
        'preSnapshotScript': {
            'path': module.params.get('pre_path'),
            'description': module.params.get('pre_description'),
            'timeoutSeconds': module.params.get('pre_timeout'),
            'failureHandling': module.params.get('on_failure')
        },
        'postSnapshotScript': {
            "path": module.params.get('post_path'),
            "description": module.params.get('post_description')
        }
    }

    compare_result = compare_json(new_config, old_config, None)
    # Implement Check Mode
    if module.check_mode:
        module.exit_json(msg='Check mode', data=compare_result)
    return compare_result['changes']


def main():
    """
    Main function
    :returns: Snapshot Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, default=None, type='str'),
            server=dict(required=True, default=None, type='str'),
            pre_path=dict(required=False, default=None, type='str'),
            pre_description=dict(required=False, default=None, type='str'),
            pre_timeout=dict(required=False, default=300, type='int'),
            on_failure=dict(required=False, default='CONTINUE', choices=['CONTINUE', 'ABORT']),
            post_path=dict(required=False, default=None, type='str'),
            post_description=dict(required=False, default=None, type='str'),
            username=dict(required=False, default=None, type='str'),
            password=dict(required=False, default=None, type='str'),
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
    return_data = return_object('snapshot_info')
    network_domain_name = module.params.get('network_domain')
    server_name = module.params.get('server')
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
        if not server.get('guest', {}).get('vmTools', {}).get('runningStatus') == 'RUNNING':
            raise NTTMCPAPIException('VMWare Tools is required to be running on server {0}'.format(server_name))
        server_id = server.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not locate any existing server - {0}'.format(e))

    if state == 'present':
        if not server.get('snapshotService'):
            module.fail_json(msg='This server does not currently have the Snapshot Service enabled')
        elif not server.get('snapshotService').get('preSnapshotScript') or not server.get('snapshotService').get('postSnapshotScript'):
            
        else:
            if compare_scripts(module, server.get('snapshotService')):
                update_scripts(module, client, network_domain_id, server)
            module.exit_json(result=server)
    elif state == 'absent':
        if not server.get('snapshotService'):
            module.exit_json(msg='Snapshots are not currently configured for this server')
        if module.check_mode:
            module.exit_json(msg='The Snapshot service and all associated snapshots will be removed from this server')
        disable_scripts(module, client, network_domain_id, server_id)


if __name__ == '__main__':
    main()
