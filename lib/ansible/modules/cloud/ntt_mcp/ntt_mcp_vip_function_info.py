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
module: ntt_mcp_vip_function_info
short_description: Get information on VIP support functions
description:
    - Get information on VIP support functions
version_added: "2.10"
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        default: na
        type: str
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
    type:
        description:
            - The type of support function
        required: false
        default: health_monitor
        type: str
        choices:
            - health_monitor
            - persistence_profile
            - irule
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: List VIP Health Monitors
    ntt_mcp_vip_function_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd

  - name: List VIP Persistence Profiles
    ntt_mcp_vip_function_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      type: persistence_profile

  - name: List VIP iRules
    ntt_mcp_vip_function_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      type: irule
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
        vip_function:
            description: VIP Support Function
            returned: success
            type: complex
            contains:
                id:
                    description: The UUID of the Virtual Support Function
                    type: str
                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                name:
                    description: The name of the Virtual Support Function
                    type: str
                    sample: CCDEFAULT.Tcp
                nodeCompatible:
                    description: Can this function be used on a VIP Node
                    returned: type == health_monitor
                    type: bool
                poolCompatible:
                    description: Can this function be used on a VIP Pool
                    returned: type == health_monitor
                    type: bool
                fallbackCompatible:
                    description: Can this function be configured as a fallback profile
                    returned: type == persistence_profile
                    type: bool
                virtualListenerCompatibility:
                    description: What type of VIP Listener a Persistence Profile is compatible with
                    returned: type == persistence_profile or type == irule
                    type: list
                    contains:
                        protocol:
                            description: The protocol name
                            type: str
                            sample: HTTP
                        type:
                            description: The protocol group type
                            type: str
                            sample: PERFORMANCE_LAYER_4
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def main():
    """
    Main function
    :returns: VIP support function information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            type=dict(default='health_monitor', choices=['health_monitor', 'persistence_profile', 'irule'], type='str')
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    function_type = module.params.get('type')
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    return_data = return_object('vip_function')
    network_domain_id = None

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
    except (KeyError, IndexError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    try:
        return_data['vip_function'] = client.list_vip_function(network_domain_id=network_domain_id,
                                                               function_type=function_type)
        return_data['count'] = len(return_data.get('vip_function'))
        module.exit_json(data=return_data)
    except (KeyError, IndexError, AttributeError, TypeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not find any VIP Functions of type {0}: {1}'.format(function_type, e.msg))


if __name__ == '__main__':
    main()
