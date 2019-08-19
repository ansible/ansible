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
module: ntt_mcp_vip_ssl_certificate
short_description: Create and Delete VIP SSL Certificate/Chain
description:
    - Create and Delete VIP SSL Certificate/Chain
    - Certificates/Chains cannot be updated or removed while still associated with an SSL Offload Profile
    - Adding certifications/chains can also be done a single step as part of creating an SSL Offload Profile using
    - ntt_mcp_vip_ssl
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
          - Valid values can be found in nttmcp.common.config.py under
            APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTT LTD Cloud Web UI
    description:
        description:
            - The description of the Cloud Network Domain
        required: false
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    name:
        description:
            - The name of the SSL certificate/chain name
        required: false
    id:
        description:
            - The UUID of the SSL certificate/chain  (can be used for deletion)
        required: false
    type:
        description:
            -The type of SSL certificate (certificate or chain)
        required: false
        default: certificate
        choices: [certificate, chain]
    path:
        description:
            - The path to a valid SSL certificate (including certificate chain) file
        required: false
    key_path:
        description:
            - The path to the associated SSL certificate private key
            - Only required type == 'certificate' (default)
        required: false
    state:
        description:
            - The action to be performed
        default: absent
        choices: [present, absent]
notes:
    - MCP SSL Certificates/Chains/Profile documentation https://docs.mcp-services.net/x/aIJk
    - List of F5 ciphers https://support.f5.com/csp/article/K13171
requirements:
    - pyOpenSSL>=19.0.0
'''

EXAMPLES = '''
# Import a SSL certificate
- ntt_mcp_vip_ssl_certificate:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_cert"
      description: "my ssl cert"
      type: certificate
      path: "/path/my_cert.pem"
      key_path: "/path/my_cert_key.pem"
      state: present
# Import a SSL chain
- ntt_mcp_vip_ssl_certificate:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_chain"
      description: "my ssl chain"
      type: chain
      path: "/path/my_chain.pem"
      state: present
# Delete an SSL Offload Profile - If this profile is the last associated profile with the cert and chain they will also be removed
- ntt_mcp_vip_ssl_certificate:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_ssl_cert"
      state: absent
'''

RETURN = '''
data:
    description: The UUID of the SSL Certifcate/Chain being created or updated
    type: str
    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
    returned: when state == present
msg:
    description: A useful message
    type: str
    returned: when state == absent
'''
from ansible.module_utils.basic import AnsibleModule
from OpenSSL import crypto
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def import_ssl_cert(module, client, network_domain_id):
    """
    Deletes a SSL certificate/chain
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    """
    cert_path = module.params.get('path')
    key_path = module.params.get('key_path')
    name = module.params.get('name')
    description = module.params.get('description')
    ssl_type = module.params.get('type')

    if not name:
        module.fail_json('A valid SSL certificate/chain name is required')

    # Attempt to load the certificate and key and verify they are valid
    try:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cert_path).read())
        if ssl_type == 'certificate':
            cert_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(key_path).read())
    except IOError as exc:
        module.fail_json(msg='The file {0} cannot be found'.format(exc.filename))
    except crypto.Error as exc:
        module.fail_json(msg='The certificate or key is invalid - {0}'.format(exc))

    try:
        if ssl_type == 'certificate':
            import_result = client.import_ssl_cert(network_domain_id,
                                                   name,
                                                   description,
                                                   crypto.dump_certificate(crypto.FILETYPE_PEM, cert),
                                                   crypto.dump_privatekey(crypto.FILETYPE_PEM, cert_key))
        elif ssl_type == 'chain':
            import_result = client.import_ssl_cert_chain(network_domain_id,
                                                         name, description,
                                                         crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as exc:
        module.fail_json(msg='Could not import the SSL certificate/chain - {0}'.format(exc))

    module.exit_json(changed=True, data=import_result)


def delete_ssl_cert(module, client, ssl_id):
    """
    Deletes a SSL certificate/chain
    :arg module: The Ansible module instance
    :arg ssl_id: The UUID of the SSL certificate/chain
    """
    if not ssl_id:
        module.fail_json('A valid SSL certificate/chain ID is required')
    try:
        client.remove_ssl(module.params.get('type'), ssl_id)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as exc:
        module.fail_json(msg='Could not remove the SSL certificate or certificate chain: {0}'.format(exc))


def is_used(ssl_type, ssl_name, ssl_profiles):
    """
    Checks if an SSL certificate/chain (ssl_name) is still used by any SSL profiles
    :arg ssl_type: The type of SSL certificate/chain
    :arg ssl_name: The name of the SSL certificate/chain
    :arg ssl_profiles: A list of SSL Profiles
    :returns: a list of associated SSL profiles
    """
    associated_ssl_profiles = []
    try:
        for ssl_profile in ssl_profiles:
            if ssl_type == 'certificate':
                if ssl_profile.get('sslDomainCertificate').get('name') == ssl_name:
                    associated_ssl_profiles.append(ssl_profile.get('name'))
            elif ssl_type == 'chain':
                if ssl_profile.get('sslCertificateChain').get('name') == ssl_name:
                    associated_ssl_profiles.append(ssl_profile.get('name'))
        return associated_ssl_profiles
    except AttributeError:
        return associated_ssl_profiles


def main():
    """
    Main function
    :returns: SSL Certificate Information
    """
    ntt_mcp_regions = get_ntt_mcp_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=ntt_mcp_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(required=False, default=None, type='str'),
            name=dict(required=False, default=None, type='str'),
            description=dict(required=False, default=None, type='str'),
            type=dict(required=False, default='certificate', choices=['certificate', 'chain']),
            path=dict(required=False, default=None, type='str'),
            key_path=dict(required=False, default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    cert = None
    associated_ssl_profiles = []

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if the SSL certificate already exists
    try:
        if module.params.get('id'):
            if module.params.get('type') == 'certificate':
                cert = client.get_vip_ssl('sslDomainCertificate', module.params.get('id'))
            elif module.params.get('type') == 'chain':
                cert = client.get_vip_ssl('sslCertificateChain', module.params.get('id'))
        else:
            if module.params.get('type') == 'certificate':
                certs = client.list_vip_ssl(network_domain_id=network_domain_id,
                                            name=module.params.get('name'),
                                            ssl_type='sslDomainCertificate')
            elif module.params.get('type') == 'chain':
                certs = client.list_vip_ssl(network_domain_id=network_domain_id,
                                            name=module.params.get('name'),
                                            ssl_type='sslCertificateChain')
            if len(certs) == 1:
                cert = certs[0]
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as exc:
        module.fail_json(msg='Could not get a list of existing SSL certificates/chains to check against - {0}'.format(exc))

    # Check if the cert is associated with any SSL Offload profiles. SSL certs cannot be updated or removed while still associated with an Offload Profile
        try:
            ssl_profiles = client.list_vip_ssl(network_domain_id=network_domain_id, ssl_type='sslOffloadProfile')
            associated_ssl_profiles = is_used(module.params.get('type'), module.params.get('name'), ssl_profiles)
            if associated_ssl_profiles:
                module.fail_json(msg='Cannot operate on the SSL {0} {1} as it is still associated with the following'
                                 'SSL Offload profiles: {2}'.format(module.params.get('type'), module.params.get('name'),
                                                                    associated_ssl_profiles))
        except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as exc:
            module.fail_json(msg='Failed getting a list of SSL Offload Profiles to check against - {0}'.format(exc))

    if state == 'present':
        if not cert:
            # Implement Check Mode
            if module.check_mode:
                module.exit_json(msg='The new SSL certificate will be imported')
            import_ssl_cert(module, client, network_domain_id)
        else:
            # Implement Check Mode
            if module.check_mode:
                module.exit_json(msg='An SSL certificate already exists, the old certificate will be removed and the new one imported')
            delete_ssl_cert(module, client, cert.get('id'))
            import_ssl_cert(module, client, network_domain_id)
    elif state == 'absent':
        if not cert:
            module.exit_json(msg='The SSL certificate/chain was not found. Nothing to remove.')
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='The SSL certificate with ID {0} will be removed'.format(cert.get('id')))
        delete_ssl_cert(module, client, cert.get('id'))
        module.exit_json(changed=True, msg='The SSL certificate/chain was successfully removed.')


if __name__ == '__main__':
    main()
