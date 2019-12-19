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
module: ntt_mcp_snapshot_preview
short_description: Create and migrate local and remote Snapshot Preview servers
description:
    - Create and migrate local and remote Snapshot Preview servers
    - Refer to the Snapshot service documentation at https://docs.mcp-services.net/x/DoBk
    - Documentation for creating a Preview server via the Cloud Control UI https://docs.mcp-services.net/x/GIBk
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
    cluster:
        description:
            - The name of the cluster when the server is being deployed in a multi-cluster environment
            - This argument can typically be ignored in public MCPs
        required: false
        type: str
    id:
        description:
            - The UUID of the source snapshot to use
        required: true
        type: str
    name:
        description:
            - The name of the server
        required: true
        type: str
    description:
        description:
            - The description of the VLAN
        required: false
        type: str
    start:
        description:
            - Whether to start the Preview server after creation
        required: false
        type: bool
        default: false
    connect_nics:
        description:
            - Should the Preview server NICs be connected
            - To avoid IP address conflicts with the original base server this should be set to False or the original
            - server should be shutdown first
        required: false
        type: bool
        default: false
    preserve_mac:
        description:
            - Whether to keep the same MAC address as the original base server
            - To avoid layer 2 issues with the original base server this should be set to False or the original server
            - should be shutdown first
        required: false
        type: bool
        default: false
    networks:
        description:
            - List of dictionary objects containing network information when creating remote/replicated Preview server
        required: false
        type: list
        suboptions:
            nic:
                description:
                    - Used for NIC identification. NIC ID/number from the original base server
                type: int
                required: true
            vlan:
                description:
                    - The VLAN from the destination datacenter to use for this NIC
                type: str
                required: true
            ipv4_address:
                description:
                    - The new IPv4 address to assign to this NIC
                    - If absent the next available IP address will be assigned from the subnet associated with the VLAN
                type: str
                required: false
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
    wait_for_vmtools:
        description:
            - Should Ansible wait for VMWare Tools to be running before continuing
            - This should only be used for server images that are running VMWare Tools
            - This should not be used for NGOC (Non Guest OS Customization) servers/images
        required: false
        type: bool
        default: false
    migrate:
        description:
            - Initiate an immediate migration of the Preview server to production following the deployment
            - If the Preview server is local to the same datacenter as the source, the source should be shutdown before
            - the migrate or the NICs shoulf be left disconnected (default)
        required: false
        type: bool
        default: false
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Create (but don't migrate) a Preview Server in the same datacenter with NICs disconnected
    ntt_mcp_snapshot_preview:
      region: na
      datacenter: NA9
      id: 112b7faa-ffff-ffff-ffff-dc273085cbe4
      name: My_Preview_Server
      description: A new server from a snapshot
      wait_for_vmtools: True
      migrate: True

  - name: Create and migrate a Replicated Preview Server in a remote datacenter with NICs connected
    ntt_mcp_snapshot_preview:
      region: na
      datacenter: NA12
      network_domain: My_Remote_CND
      id: 222b7faa-ffff-ffff-ffff-dc273085cbe5
      name: My_Replicated_Server
      description: A new server from a replicated snapshot
      connect_network: True
      preserve_mac: True
      migrate: True
      networks:
        - nic: 0
          vlan: my_remote_vlan
          privateIpv4: 10.0.0.100
        - nic: 1
          vlan: my_other_remote_vlan

'''

RETURN = '''
data:
    description: Server objects
    returned: when wait is False
    type: str
    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
msg:
    description: Message on completion
    returned: when wait is True
    type: str
    sample: "The Snapshot Preview Server has successfully been deployed"
'''
from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException

CORE = {
    'region': None,
    'datacenter': None,
    'network_domain_id': None,
    'snapshot': None,
    'vlans': None,
    'start': False}


def create_preview_server(module, client, replica, networks):
    """
    Create a new Preview Server

    :arg module: The Ansible module
    :arg client: The CC API client instance
    :arg replica: Is the new preview server a replicated/remote server
    :arg networks: A list of verified network dicts with details of the network details in the remote datacenter

    :returns: N/A
    """
    try:
        if not replica:
            result = client.create_snapshot_preview(CORE.get('snapshot').get('id'),
                                                    module.params.get('name'),
                                                    module.params.get('description'),
                                                    module.params.get('cluster'),
                                                    CORE.get('start'),
                                                    module.params.get('connect_nics'),
                                                    module.params.get('preserve_mac'))
        else:
            result = client.create_replicated_snapshot_preview(CORE.get('snapshot').get('id'),
                                                               module.params.get('name'),
                                                               module.params.get('description'),
                                                               module.params.get('cluster'),
                                                               CORE.get('start'),
                                                               module.params.get('connect_nics'),
                                                               networks,
                                                               module.params.get('preserve_mac'))
        server_id = next((item for item in result.get('info') if item["name"] == "serverId"), dict()).get('value')
        if not server_id:
            module.fail_json(msg='The Snapshot Preview Server deployment was successful but could not find the server '
                             'to wait for status updates')
        if module.params.get('wait'):
            wait_for_snapshot(module, client, server_id, CORE.get('start'))
            if module.params.get('migrate'):
                result = client.migrate_snapshot_preview(server_id)
                wait_for_snapshot(module, client, server_id, CORE.get('start'))
            module.exit_json(changed=True, msg='The Snapshot Preview Server has successfully been deployed')
        module.exit_json(changed=True, msg='The deployment process is in progress. '
                         'Check the status manually or use ntt_mcp_server_info')
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not create the Snapshot Preview Server - {0}'.format(e))


def check_replica_input(module, client):
    """
    Check the input (specifically network/NIC input)

    :arg module: The Ansible module
    :arg client: The CC API client instance

    :returns: A list of valided networks
    """
    networks = module.params.get('networks')
    network_list = list()
    snapshot_nics = list([CORE.get('snapshot', {}).get('serverConfig', {}).get('networkInfo', {}).get('primaryNic')])

    try:
        snapshot_nics += CORE.get('snapshot', {}).get('serverConfig', {}).get('networkInfo', {}).get('additionalNic')
    except (TypeError):
        module.fail_json(msg='Cannot read the NICs from the snapshot')

    # Check the cluster ID exists

    # Check the Network Domain exists
    try:
        network = client.get_network_domain_by_name(datacenter=CORE.get('datacenter'),
                                                    name=module.params.get('network_domain'))
        CORE['network_domain_id'] = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed to find the Cloud Network Domain - {0}'.format(e))
    # Get a list of VLANs for checking later
    try:
        vlans = client.list_vlans(datacenter=CORE.get('datacenter'), network_domain_id=CORE['network_domain_id'])
    except NTTMCPAPIException as e:
        module.fail_json(msg='Failed to get a list of VLANs to verify against - {0}'.format(e))

    if not networks:
        module.fail_json(msg='An array of networks including nic number, vlan and optionally an ipv4_address must be '
                         'provided when creating a remote preview server from a replicated snapshot')
    if len(networks) != len(snapshot_nics):
        module.fail_json(msg='The list of networks in the arguments ({0}) must equal the number of NICs configured '
                         'within the snapshot ({1}). Use ntt_mcp_snapshot_info to view the snapshot configuration '
                         'including the list of NICS.'.format(len(networks), len(snapshot_nics)))
    try:
        for nic in networks:
            nic_dict = dict()
            if not isinstance(nic.get('nic'), int):
                module.fail_json(msg='NIC number must be an integer that matches the NIC on the parent server')
            # Check the VLAN supplied actually exists
            vlan = next(x for x in vlans if x['name'] == nic.get('vlan'))
            if not vlan:
                module.fail_json(msg='VLAN {0} on NIC {1} is invalid'.format(nic.get('vlan'), nic.get('nic')))
            nic_dict['nic_id'] = snapshot_nics[nic.get('nic')].get('id')
            nic_dict['vlan_id'] = vlan.get('id')
            if nic.get('ipv4_address'):
                nic_dict['ipv4_address'] = nic.get('ipv4_address')
            network_list.append(nic_dict)
    except (KeyError, IndexError, AttributeError):
        module.fail_json(msg='Could not find the associated networks. Check the NIC and VLAN input.')

    return network_list


def wait_for_snapshot(module, client, server_id, check_for_start=False):
    """
    Wait for the preview server.

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server_id: The UUID of the server
    :arg check_for_start: Check if the server is started

    :returns: The server dict
    """
    state = 'NORMAL'
    set_state = vmtools_status = wait_required = False
    actual_state = start_state = ''
    time = 0
    wait_for_vmtools = module.params.get('wait_for_vmtools')
    wait_time = module.params.get('wait_time')
    wait_poll_interval = module.params.get('wait_poll_interval')
    server = None
    while not set_state and time < wait_time:
        try:
            server = client.get_server_by_id(server_id=server_id)
        except NTTMCPAPIException as e:
            module.fail_json(msg='Failed to get a list of servers - {0}'.format(e))

        # Check if VMTools has started - if the user as specified to wait for VMWare Tools to be running
        try:
            if wait_for_vmtools:
                if server.get('guest', {}).get('vmTools', {}).get('runningStatus') == 'RUNNING':
                    vmtools_status = True
        except AttributeError:
            pass
        try:
            actual_state = server.get('state')
            start_state = server.get('started')
        except (KeyError, IndexError):
            module.fail_json(msg='Failed to get the current state for the server with ID - {0}'.format(server_id))

        if actual_state != state:
            wait_required = True
        elif check_for_start and not start_state:
            wait_required = True
        elif wait_for_vmtools and not vmtools_status:
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
    :returns: A message or server ID
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=False, default=None, type='str'),
            cluster=dict(required=False, default=None, type='str'),
            id=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, default=None, type='str'),
            start=dict(required=False, default=False, type='bool'),
            connect_nics=dict(required=False, default=False, type='bool'),
            preserve_mac=dict(required=False, default=False, type='bool'),
            networks=dict(required=False, default=None, type='list'),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=1800, type='int'),
            wait_poll_interval=dict(required=False, default=30, type='int'),
            wait_for_vmtools=dict(required=False, default=False, type='bool'),
            migrate=dict(required=False, default=False, type='bool')
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

    try:
        client = NTTMCPClient(credentials, module.params.get('region'))
    except NTTMCPAPIException as e:
        module.fail_json(msg=e.msg)

    try:
        snapshot = client.get_snapshot_by_id(module.params.get('id'))
        CORE['datacenter'] = snapshot.get('datacenterId')
        CORE['snapshot'] = snapshot
        CORE['start'] = module.params.get('start')
        if module.check_mode:
            module.exit_json(msg='Snapshot with ID {0} will be used to create the Preview server {1}'.format(
                snapshot.get('id'),
                module.params.get('name')))
        if module.params.get('wait_for_vmtools'):
            CORE['start'] = True
        if snapshot.get('replica'):
            networks = check_replica_input(module, client)
            create_preview_server(module, client, True, networks)
        else:
            create_preview_server(module, client, False, None)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not retrieve the Snapshot - {0}'.format(e))


if __name__ == '__main__':
    main()
