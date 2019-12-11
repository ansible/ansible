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
module: ntt_mcp_snapshot_script
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
    pre_path:
        description:
            - The full path to a script on the VM that will be run before a snapshot is taken
        required: false
        type: str
    pre_description:
        description:
            - The description for the pre-script
        required: false
        type: str
    pre_timeout:
        description:
            - The timeout (in seconds) to apply to the pre-script in case of issues
        required: false
        default: 300
        type: int
    on_failure:
        description:
            - What to do in the event of a sript failure
        required: false
        type: str
        default: CONTINUE
        choices:
            - CONTINUE
            - ABORT
    post_path:
        description:
            - The full path to a script on the VM that will be run after a snapshot has been taken
        required: false
        type: str
    post_description:
        description:
            - The description for the post-script
        required: false
        type: str
    username:
        description:
            - The username of an OS level user with sufficient permissions to execute the scripts
            - It is strongly advised not to use root/administrator but a dedicated snapshot script user with
            - only those permissions required to execute the scripts
        required: false
        type: str
    password:
        description:
            - The password of the OS level user
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

  - name: Configure Pre and Post snapshot scripts for a server
    ntt_mcp_snapshot_script:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      server: My_Server
      pre_path: /usr/local/bin/my_pre_script
      pre_description: A pre script
      post_path: /usr/local/bin/my_post_script
      post_description: A post script
      username: myuser
      password: mypassword

  - name: Remove the Pre script from a server
    ntt_mcp_snapshot_script:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      server: My_Server
      pre_path: /usr/local/bin/my_pre_script
      state: absent

  - name: Remove all scripts from a server
    ntt_mcp_snapshot_script:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      server: My_Server
      pre_path: /usr/local/bin/my_pre_script
      post_path: /usr/local/bin/my_post_script
      state: absent
'''
RETURN = '''
msg:
    description: Status of the operation
    returned: always
    sample: "Server snapshot script(s) have been deleted"
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def update_scripts(module, client, server):
    """
    Add/Update scripts for a snapshot enabled server

    :arg module: The Ansible module instance
    :arg client: The CC API provider instance
    :arg server: The server object with snapshots enabled
    :returns: True/False
    """
    try:
        result = client.update_snapshot_scripts(server_id=server.get('id'),
                                                pre_path=module.params.get('pre_path'),
                                                pre_description=module.params.get('pre_description'),
                                                pre_timeout=module.params.get('pre_timeout'),
                                                on_failure=module.params.get('on_failure'),
                                                post_path=module.params.get('post_path'),
                                                post_description=module.params.get('post_description'),
                                                username=module.params.get('username'),
                                                password=module.params.get('password'))
    except NTTMCPAPIException as e:
        module.fail_json(msg=e.msg)
    if result:
        return True
    return False


def delete_scripts(module, client, server):
    """
    Delete scripts from a snapshot enabled server

    :arg module: The Ansible module instance
    :arg client: The CC API provider instance
    :arg server: The server object with snapshots enabled
    :returns: True/False
    """
    delete_pre = delete_post = False
    if module.params.get('pre_path') and server.get('snapshotService').get('preSnapshotScript'):
        delete_pre = True
    if module.params.get('post_path') and server.get('snapshotService').get('postSnapshotScript'):
        delete_post = True
    if client.delete_snapshot_script(server_id=server.get('id'), delete_pre=delete_pre, delete_post=delete_post):
        return True
    return False


def compare_scripts(module, snapshot_config):
    """
    Compare the existing Snapshot config to the provided arguments

    :arg module: The Ansible module instance
    :arg snapshot_config: The dict containing the existing Snapshot config to compare to
    :returns: Any differences between the the Snapshot configs
    """
    new_config = {}
    old_config = {
        'preSnapshotScript': snapshot_config.get('preSnapshotScript') or {},
        'postSnapshotScript': snapshot_config.get('postSnapshotScript') or {}
    }
    if module.params.get('pre_path') is not None:
        new_config['preSnapshotScript'] = {
            'path': module.params.get('pre_path'),
            'description': module.params.get('pre_description'),
            'timeoutSeconds': module.params.get('pre_timeout'),
            'failureHandling': module.params.get('on_failure')
        } or {}

    if module.params.get('post_path') is not None:
        new_config['postSnapshotScript'] = {
            "path": module.params.get('post_path'),
            "description": module.params.get('post_description')
        } or {}

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
            network_domain=dict(required=True, type='str'),
            server=dict(required=True, type='str'),
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
    network_domain_name = module.params.get('network_domain')
    server_name = module.params.get('server')
    network_domain_id = None
    server = None

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
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not locate any existing server - {0}'.format(e))

    if state == 'present':
        if module.params.get('pre_path') is not None or module.params.get('post_path') is not None:
            if None in [module.params.get('username'), module.params.get('password')]:
                module.fail_json(msg='A username and password is required when configuring a snapshot script(s)')
        if not server.get('snapshotService'):
            module.fail_json(msg='This server does not currently have the Snapshot Service enabled')
        else:
            if compare_scripts(module, server.get('snapshotService')):
                update_scripts(module, client, server)
                module.exit_json(changed=True, msg='Snapshot scripts updated for server {0}'.format(server.get('id')))
            module.exit_json(msg='No changes required')
    elif state == 'absent':
        if not server.get('snapshotService'):
            module.exit_json(msg='Snapshots are not currently configured for this server')
        if compare_scripts(module, server.get('snapshotService')):
            delete_scripts(module, client, server)
            module.exit_json(changed=True, msg="Server snapshot script(s) have been deleted")
        module.exit_json(msg='No changes required')


if __name__ == '__main__':
    main()
