#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communications Cloud Infrastructure Services
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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nttc_cis_vip_ssl_info
short_description: List/Get VIP SSL Configuration
description:
    - List/Get VIP SSL Configuration
    - It is quicker to use the option "id" to locate the SSL configuration if the UUID is known rather than search by name
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        default: na
        choices:
          - Valid values can be found in nttcis.common.config.py under APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTTC CIS Cloud Web UI
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    id:
        description:
            - The UUID of the node
        required: false
    name:
        description:
            - The name of the node
        required: false
    ip_address:
        description:
            - The IPv4 or IPv6 address of the node
        required: false
notes:
    - MCP SSL Certificates, Chains, Profile documentation https://docs.mcp-services.net/x/aIJk
    - List of F5 ciphers https://support.f5.com/csp/article/K13171
'''

EXAMPLES = '''
# List all SSL certificates for a Network Domain
- nttc_cis_vip_ssl_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
# List all SSL Chains for a Network Domain
- nttc_cis_vip_ssl_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      type: chain
# Get a specific SSL Profile by ID
- nttc_cis_vip_ssl_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      type: profile
      id: bbc866b0-2f13-44b4-8339-49890f10dc3c
# Get a specific SSL Profile by name
- nttc_cis_vip_ssl_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      type: profile
      name: "My_SSL_Profile"
'''

RETURN = '''
ssl_certificate:
    description: List of SSL Certificates
    returned: when type == 'certificate' (default)
    type: complex
    contains:
        datacenterId:
            description: The MCP ID
            type: str
            sample: NA9
        networkDomainId:
            description: The UUID of the Cloud Network Domain
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        description:
            description: SSL certificate description
            type: str
            sample: "My Cert"
        createTime:
            description: The creation date of the SSL certificate
            type: str
            sample: "2019-01-14T11:12:31.000Z"
        name:
            description: The SSL certificate display name
            type: str
            sample: "my_cert"
        expiryTime:
            description: The expiry date of the SSL certificate
            type: str
            sample: "2019-01-14T11:12:31.000Z"
        id:
            description:  The UUID of the SSL certificate
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
ssl_chain:
    description: List of SSL Chain
    returned: when type == 'chain' (default)
    type: complex
    contains:
        datacenterId:
            description: The MCP ID
            type: existing_member
            sample: NA9
        networkDomainId:
            description: The UUID of the Cloud Network Domain
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        description:
            description: SSL chain description
            type: str
            sample: "My Cert"
        createTime:
            description: The creation date of the SSL chain
            type: str
            sample: "2019-01-14T11:12:31.000Z"
        name:
            description: The SSL chain display name
            type: str
            sample: "my_chain"
        expiryTime:
            description: The expiry date of the SSL chain
            type: str
            sample: "2019-01-14T11:12:31.000Z"
        id:
            description:  The UUID of the SSL chain
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
ssl_profile:
    description: SSL Profile Object
    returned: when type == 'profile' (default)
    type: complex
    contains:
        networkDomainId:
            description: The UUID of the Cloud Network Domain
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        sslDomainCertificate:
            description: List of SSL Certificates
            type: complex
            contains:
                expiryTime:
                    description: The expiry date of the SSL certificate
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                id:
                    description:  The UUID of the SSL certificate
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                name:
                    description: The SSL certificate display name
                    type: str
                    sample: "my_cert"
        name:
            description: The name of the SSL Offload Profile
            type: str
            sample: "my_ssl_profile"
        ciphers:
            description: Cipher needs to be a valid F5 Cipher string - https://support.f5.com/csp/article/K13171
            type: str
            sample: "DHE+AES:DHE+AES-GCM:RSA+AES:RSA+3DES:RSA+AES-GCM:DHE+3DES"
        id:
            description: The UUID of the SSL Offload Profile
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        datacenterId:
            description: The MCP ID
            type: str
            sample: NA9
        state:
            description: The operational state of the SSL Offload Profile
            type: str
            sample: "NORMAL"
        sslCertificateChain:
            description: The optional SSL certificate chain
            type: complex
            contains:
                expiryTime:
                    description: The expiry date of the SSL chain
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                id:
                    description:  The UUID of the SSL chain
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                name:
                    description: The SSL chain display name
                    type: str
                    sample: "my_chain"
        createTime:
            description: The creation date of the SSL chain
            type: str
            sample: "2019-01-14T11:12:31.000Z"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def main():
    """
    Main function

    :returns: SSL Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(default=None, required=False, type='str'),
            type=dict(default='certificate', required=False, choices=['certificate', 'chain', 'profile']),
            name=dict(default=None, required=False, type='str')
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    object_id = module.params.get('id')
    object_type = module.params.get('type')
    api_object_type = None
    name = module.params.get('name')
    return_data = return_object('ssl_{0}'.format(object_type))

    # Assign the actual CC API attribute name for the object type
    if object_type == 'certificate':
        api_object_type = 'sslDomainCertificate'
    elif object_type == 'chain':
        api_object_type = 'sslCertificateChain'
    elif object_type == 'profile':
        api_object_type = 'sslOffloadProfile'

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    try:
        if object_id:
            return_data['ssl_{0}'.format(object_type)] = client.get_vip_ssl(api_object_type, object_id)
        else:
            return_data['ssl_{0}'.format(object_type)] = client.list_vip_ssl(network_domain_id, api_object_type, name)
    except (KeyError, IndexError, NTTCCISAPIException) as exc:
        module.fail_json(msg='Could not find the SSL object(s): {0}'.format(exc))
    return_data['count'] = len(return_data['ssl_{0}'.format(object_type)])
    module.exit_json(results=return_data)


if __name__ == '__main__':
    main()
