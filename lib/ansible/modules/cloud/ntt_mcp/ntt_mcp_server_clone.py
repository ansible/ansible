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
module: ntt_mcp_server_clone
short_description: Clone an existing server to a customer image
description:
    - Clone an existing server to a customer image
    - https://docs.mcp-services.net/x/pwMk
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
        required: true
        type: str
    server:
        description:
            - The name of the server to be cloned
        required: true
        type: str
    image:
        description:
            - The name of the new image
        required: true
        type: str
    description:
        description:
            - The description of the new customer image
        required: false
        type: str
    cluster:
        description:
            - The name of the cluster when the server is being deployed in a multi-cluster environment
            - This argument can typically be ignored
        required: false
        type: str
    goc:
        description:
            - If set to false this property tells CloudControl that Servers deployed from the resulting Customer Image
            - should NOT utilize Guest OS Customization.
            - https://docs.mcp-services.net/x/XQIu
        required: false
        type: bool
        default: true
    wait:
        description:
            - Should Ansible wait for the task to complete before continuing
        required: false
        type: bool
        default: true
    wait_time:
        description: The maximum time the Ansible should wait for the task to complete in seconds
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

  - name: Clone a server
    ntt_mcp_server_clone:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      name: my_server_01
      image: my_server_01_image
      description: "My Cloned Server"
'''

RETURN = '''
msg:
    description: A helpful message
    returned: always
    type: str
    sample: The server with ID 36071cc0-02a0-46cf-b67c-64245e59e05d was successfully cloned to the new image with ID 71a365c4-f702-4e3c-ac11-34924aa36bf5
'''

from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def wait_for_server(module, client, server_id):
    """
    Wait for an operation on a server. Polls based on wait_time and wait_poll_interval values.

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server_id: The name of the server
    :returns: True/False
    """
    actual_state = False
    time = 0
    wait_time = module.params.get('wait_time')
    server = dict()
    while not actual_state and time < wait_time:
        try:
            server = client.get_server_by_id(server_id=server_id)
        except NTTMCPAPIException as e:
            module.fail_json(msg='Failed to find the server - {0}'.format(e))

        try:
            if not server.get('progress'):
                actual_state = True
        except (KeyError, IndexError):
            pass
        sleep(module.params.get('wait_poll_interval'))
        time = time + module.params.get('wait_poll_interval')

    if not server and time >= wait_time:
        module.fail_json(msg='Timeout waiting for the server to be cloned')
    return True


def main():
    """
    Main function

    :returns: Server Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', typ='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            server=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            image=dict(required=True, type='str'),
            cluster=dict(required=False, type='str'),
            goc=dict(required=False, default=True, type='bool'),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=3600, type='int'),
            wait_poll_interval=dict(required=False, default=30, type='int')
        ),
        supports_check_mode=True
    )

    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    server_name = module.params.get('server')
    datacenter = module.params.get('datacenter')
    network_domain_name = module.params.get('network_domain')
    server = dict()

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
        network = client.get_network_domain_by_name(network_domain_name, datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if the Server exists based on the supplied name
    try:
        server = client.get_server_by_name(datacenter=datacenter,
                                           network_domain_id=network_domain_id,
                                           name=server_name)
        if not server:
            module.fail_json(msg='Failed attempting to locate any existing server')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed attempting to locate any existing server - {0}'.format(e))

    if module.check_mode:
        module.exit_json(msg='The server with ID {0} will be cloned to the image {1}'.format(server.get('id'),
                                                                                             module.params.get('image')))

    try:
        result = client.clone_server_to_image(server_id=server.get('id'),
                                              image_name=module.params.get('image'),
                                              description=module.params.get('description'),
                                              cluster_id=module.params.get('cluster'),
                                              goc=module.params.get('goc'))
        if module.params.get('wait'):
            wait_for_server(module, client, server.get('id'))
        module.exit_json(changed=True,
                         msg='The server with ID {0} was successfully cloned to the new image with ID {1}'.format(server.get('id'),
                                                                                                                  result))
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not clone the server with ID {0} - {1}'.format(server.get('id'), e))


if __name__ == '__main__':
    main()
