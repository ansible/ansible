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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nttc_cis_vip_listener
short_description: Create, update and delete VIP Virtual Listeners
description:
    - Create, update and delete VIP Virtual Listeners
    - It is quicker to use the option "id" to locate the VIP Listener if the UUID is known rather than search by name
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
          - Valid values can be found in nttc_cis.nttc_cis_config.py under APIENDPOINTS
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
            - The UUID of the VIP Listener. Takes precendence over name
        required: false
    name:
        description:
            - The name of the VIP Listener
        required: false
    description:
        description:
            - The description for the VIP Listener
        required: false
    ip_address:
        description:
            - The IPv4 address to listen on
        required: false
    protocol:
        description:
            - The service protocol for the VIP Listener
        required: false
    port:
        description:
            - The port to use for the VIP Listener
            - If port is excluded or None the listener will be created for ANY port
        required: false
        default: None
    pool:
        description:
            - The name of a VIP Pool
        required: false
    connectionLimit:
            description:
                -The maximum number of simultaneous connections permitted on the Node. Should be an integer between 1 and 100,000
            required: false
            default: 100000
    connectionRateLimit:
            description:
                - The amount of new connections permitted every second. Should be an integer between 1 and 4,000.
            type: int
            required: false
            default: 4000
    persistence_profile:
        description:
            - The name of a Persistence Profile
            - Provides a method for ensuring that traffic from a client is sent to the same server in a pool based on an attribute of the connection.
            - Each is a set of parameters that optimize the handling of traffic based on application type and network protocol.
        required: false
    fallback_persistence_profile:
        description:
            - The name of a Persistence Profile - cannot be the same as the primary Persistence Profile
            - Fallback Persistence is used when the primary Persistence Profile fails
        required: false
    optimization_profile:
        description:
            - The name of a Optimization Profile
            - For certain combinations of Virtual Listener type and protocol, it is possible to specify an additional optimization profile.
        required: false
    irules:
        description:
            - A list of iRule names
            - Custom configured rules that are applied to Virtual Servers to perform a wide array of actions.
        required: false
    ssl_offload_profile:
        description:
            - The name of an SSL Offload Profile
            - SSL Offloading allows you to set up proxies for SSL certificates at the Virtual Listener level rather than having to set up SSL certificates on individual virtual servers.
    state:
        description:
            - The action to be performed
        default: present
        choices: [present, absent]

notes:
    - Introduction to Virtual Listeners https://docs.mcp-services.net/x/CwIu
    - How to Create a Virtual Listener https://docs.mcp-services.net/x/7gM
'''

EXAMPLES = '''
# Create a VIP Listener
- nttc_cis_vip_listener:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_vip_listener"
      description: "My VIP Listener"
      ip_address: "10.0.0.10"
      protocol: "TCP"
      port: 443
      pool: "my_pool"
      connection_limit: 60000
      connection_rate_limit: 3000
      persistence_profile: "CCDEFAULT.SourceAddress"
      fallback_persistence_profile: "CCDEFAULT.DestinationAddress"
      optimization_profile: "TCP"
      irules:
        - name: CCDEFAULT.IpProtocolTimers
      ssl_offload_profile: "my_ssl_profile"
      state: present
# Update a specific VIP Listener - Remove the fallback persistence profile and irules from the example above
- nttc_cis_vip_listener:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_vip_listener"
      description: "My VIP Listener"
      ip_address: "10.0.0.10"
      protocol: "TCP"
      port: 443
      pool: "my_pool"
      connection_limit: 60000
      connection_rate_limit: 3000
      persistence_profile: "CCDEFAULT.SourceAddress"
      optimization_profile: "TCP"
      ssl_offload_profile: "my_ssl_profile"
      state: present
# Delete a specific VIP Pool by name
- nttc_cis_vip_listener:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_vip_listener"
      state: absent
# Delete a specific VIP Pool by id
- nttc_cis_vip_listener:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      id: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
      state: absent
'''

RETURN = '''
results:
    description: The UUID of the created or updated VIP Listener Object
    type: str
    returned: when state == present
    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
msg:
    description: A useful message
    type: str
    returned: when state == absent
    sample: "The object was successfully deleted"
'''

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, compare_json
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException
from ansible.module_utils.nttc_cis.nttc_cis_config import (VIP_LISTENER_TYPES, VIP_LISTENER_PRESERVATION, VIP_LISTENER_OPTOMIZATION)


def get_optomization_profile(module):
    """
    Get a VIP optimization Profile

    :arg module: The Ansible module instance
    :returns: A VIP optimization profile
    """
    if module.params.get('protocol') == 'UDP':
        if module.params.get('optimization_profile') in VIP_LISTENER_OPTOMIZATION.get('UDP'):
            return module.params.get('optimization_profile')
    else:
        if module.params.get('optimization_profile') in VIP_LISTENER_OPTOMIZATION.get('TCP'):
            return module.params.get('optimization_profile')
    return None

def get_irules(module, client, network_domain_id):
    """
    Get a VIP iRule

    :arg module: The Ansible module instance
    :returns: A VIP iRule
    """
    irule_id_list = []
    if module.params.get('irules'):
        try:
            cc_irules = client.list_irule(network_domain_id)
            for irule in module.params.get('irules'):
                for cc_irule in cc_irules:
                    if irule == cc_irule.get('irule').get('name'):
                        irule_id_list.append(cc_irule.get('irule').get('id'))
        except (KeyError, IndexError, NTTCCISAPIException):
            module.warn(warning='The supplied iRule list will not be included as the module could not get a list of iRules from the API.')
    return irule_id_list


def get_ssl_offload_profile(module, client, network_domain_id):
    """
    Get a VIP SSL offload profile

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the Cloud Network Domain
    :returns: A VIP SSL offload profile
    """
    ssl_profile_id = None
    if module.params.get('ssl_offload_profile'):
        try:
            ssl_profile = client.list_vip_ssl(network_domain_id, 'sslOffloadProfile', module.params.get('ssl_offload_profile'))[0]
            ssl_profile_id = ssl_profile.get('id')
        except (KeyError, IndexError, NTTCCISAPIException) as exc:
            module.fail_json(msg='Could not find the SSL Offload Profile {0}: {1}'.format(module.params.get('ssl_offload_profile'), exc))
    return ssl_profile_id


def get_persistence_profiles(module, client, network_domain_id):
    """
    Get a VIP SSL persistence profile

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the Cloud Network Domain
    :returns: A VIP SSL persistence profile
    """
    persistence_profile_id_1 = persistence_profile_id_2 = None
    if module.params.get('persistence_profile'):
        try:
            persistence_profile_list = client.list_persistence_profile(network_domain_id)
            for persistence_profile in persistence_profile_list:
                if module.params.get('persistence_profile') == persistence_profile.get('name'):
                    persistence_profile_id_1 = persistence_profile.get('id')
                if module.params.get('fallback_persistence_profile'):
                    if module.params.get('fallback_persistence_profile') == persistence_profile.get('name'):
                        persistence_profile_id_2 = persistence_profile.get('id')
            if not persistence_profile_id_1:
                module.fail_json(msg='Could not find the Persistence Profile {0}'.format(module.params.get('persistence_profile')))
            if module.params.get('fallback_persistence_profile') and not persistence_profile_id_2:
                module.warn(warning='Excluding the Fallback Persistence Profile as profile {0} could not be found'.format(
                    module.params.get('fallback_persistence_profile')))
        except (KeyError, IndexError, NTTCCISAPIException) as exc:
            module.fail_json(msg='Could not get a list of Persistence Profiles: {0}'.format(exc))
    return (persistence_profile_id_1, persistence_profile_id_2)


def get_vip_pools(module, client, network_domain_id):
    """
    Get a VIP SSL pools

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the Cloud Network Domain
    :returns: A turple containing the VIP SSL pool dicts
    """
    pool_id_1 = pool_id_2 = None
    try:
        pools = client.list_vip_pool(network_domain_id)
        for pool in pools:
            if module.params.get('pool') == pool.get('name'):
                pool_id_1 = pool.get('id')
            elif module.params.get('client_pool') == pool.get('name'):
                pool_id_2 = pool.get('id')
        if module.params.get('pool') and not pool_id_1:
            module.fail_json(msg='Could not find the VIP Pool {0}'.format(module.params.get('pool')))
        if module.params.get('client_pool') and not pool_id_2:
            module.warn(warning='Excluding the Client Pool as pool {0} could not be found'.format(
                module.params.get('client_pool')))
    except (KeyError, IndexError, NTTCCISAPIException):
        pass
    return (pool_id_1, pool_id_2)


def create_vip_listener(module, client, network_domain_id):
    """
    Create a VIP listener

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the Cloud Network Domain
    :returns: A VIP listener
    """
    irule_id_list = []
    persistence_profile_id_1 = persistence_profile_id_2 = None
    pool_id_1 = pool_id_2 = None
    optimization_profile = None
    ssl_profile_id = None

    if not module.params.get('name'):
        module.fail_json(msg='A valid name is required')

    # Determine the Optimization type if any otherwise go with the default None
    optimization_profile = get_optomization_profile(module)
    # Get a list of existing irules if it fails then continue but warn the user that no irules will be included
    irule_id_list = get_irules(module, client, network_domain_id)
    if module.params.get('irules'):
        if len(module.params.get('irules')) != len(irule_id_list):
            module.warn(warning='Not all of the supplied iRules could be found. Missing iRules will be skipped.')
    # Get the SSL Offload Profile if a name is provided
    ssl_profile_id = get_ssl_offload_profile(module, client, network_domain_id)
    # Get the Persistence Profile(s) if a name is provided - fail on not finding the profile.
    (persistence_profile_id_1, persistence_profile_id_2) = get_persistence_profiles(module, client, network_domain_id)
    # Get the VIP Pool(s)
    (pool_id_1, pool_id_2) = get_vip_pools(module, client, network_domain_id)

    # Create the Virtual Listener
    try:
        listener_id = client.create_vip_listener(network_domain_id,
                                                 module.params.get('name'),
                                                 module.params.get('description'),
                                                 module.params.get('type'),
                                                 module.params.get('protocol'),
                                                 module.params.get('ip_address'),
                                                 module.params.get('port'),
                                                 module.params.get('enabled'),
                                                 module.params.get('connection_limit'),
                                                 module.params.get('connection_rate_limit'),
                                                 module.params.get('preservation'),
                                                 pool_id_1,
                                                 pool_id_2,
                                                 persistence_profile_id_1,
                                                 persistence_profile_id_2,
                                                 optimization_profile,
                                                 ssl_profile_id,
                                                 irule_id_list
                                                )
    except (KeyError, IndexError, NTTCCISAPIException) as exc:
        module.fail_json(msg='Could not create the Virtual Listener: {0}'.format(exc))

    module.exit_json(changed=True, results=listener_id)


def update_vip_listener(module, client, network_domain_id, listener):
    """
    Update a VIP listener

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg listener: The dict containing the existing listener to be updated
    :returns: The updated listener dict
    """
    irule_id_list = []
    persistence_profile_id_1 = persistence_profile_id_2 = None
    pool_id_1 = pool_id_2 = None
    optimization_profile = None
    ssl_profile_id = None

    # Determine the Optimization type if any otherwise go with the default None
    optimization_profile = get_optomization_profile(module)
    # Get a list of existing irules if it fails then continue but warn the user that no irules will be included
    irule_id_list = get_irules(module, client, network_domain_id)
    if not irule_id_list:
        irule_id_list.append({'nil': True})
    # Get the SSL Offload Profile if a name is provided
    ssl_profile_id = get_ssl_offload_profile(module, client, network_domain_id)
    # Get the Persistence Profile(s) if a name is provided - fail on not finding the profile.
    (persistence_profile_id_1, persistence_profile_id_2) = get_persistence_profiles(module, client, network_domain_id)
    # Get the VIP Pool(s)
    (pool_id_1, pool_id_2) = get_vip_pools(module, client, network_domain_id)

    try:
        listener_id = client.update_vip_listener(listener.get('id'),
                                                 module.params.get('description'),
                                                 module.params.get('type'),
                                                 module.params.get('protocol'),
                                                 module.params.get('enabled'),
                                                 module.params.get('connection_limit'),
                                                 module.params.get('connection_rate_limit'),
                                                 module.params.get('preservation'),
                                                 pool_id_1,
                                                 pool_id_2,
                                                 persistence_profile_id_1,
                                                 persistence_profile_id_2,
                                                 optimization_profile,
                                                 ssl_profile_id,
                                                 irule_id_list
                                                )
    except (KeyError, IndexError, NTTCCISAPIException) as exc:
        module.fail_json(msg='Could not update the VIP Listener - {0}'.format(exc))

    module.exit_json(changed=True, results=listener_id)


def delete_vip_listener(module, client, listener_id):
    """
    Delete a VIP listener

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg listener_id: The UUID of the existing VIP listener to be deleted
    :returns: A message
    """
    if listener_id is None:
        module.fail_json(msg='A value for id is required')
    try:
        client.remove_vip_listener(listener_id)
    except NTTCCISAPIException as exc:
        module.fail_json(msg='Could not delete the Virtual Listener - {0}'.format(exc))

    module.exit_json(changed=True, msg='Successfully deleted the VIP Virtual Listener')


def compare_vip_listener(module, client, network_domain_id, vip_listener):
    """
    Compare two VIP listeners

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of a Cloud Network Domain
    :arg cip_listener: The dict of the existing VIP listener to be compared to
    :returns: Any differences between the two VIP listeners
    """
    new_vip_listener = deepcopy(vip_listener)
    existing_vip_listener = deepcopy(vip_listener)

    (pool_id_1, pool_id_2) = get_vip_pools(module, client, network_domain_id)
    (persistence_profile_id_1, persistence_profile_id_2) = get_persistence_profiles(module, client, network_domain_id)
    ssl_profile_id = get_ssl_offload_profile(module, client, network_domain_id)
    optimization_profile = get_optomization_profile(module)
    irule_id_list = get_irules(module, client, network_domain_id)

    # Handle the schema differences
    if existing_vip_listener.get('description'):
        new_vip_listener['description'] = module.params.get('description')
    new_vip_listener['enabled'] = module.params.get('enabled')
    new_vip_listener['connectionLimit'] = module.params.get('connection_limit')
    new_vip_listener['connectionRateLimit'] = module.params.get('connection_rate_limit')
    new_vip_listener['sourcePortPreservation'] = module.params.get('preservation')
    if existing_vip_listener.get('pool'):
        existing_vip_listener['poolId'] = existing_vip_listener.get('pool').get('id')
    if not(existing_vip_listener.get('pool') is None and pool_id_1 is None):
        new_vip_listener['poolId'] = pool_id_1
    if existing_vip_listener.get('clientClonePool'):
        existing_vip_listener['clientClonePoolId'] = existing_vip_listener.get('clientClonePool').get('id')
    if not(existing_vip_listener.get('clientClonePool') is None and pool_id_2 is None):
        new_vip_listener['clientClonePoolId'] = pool_id_2
    if existing_vip_listener.get('persistenceProfile'):
        existing_vip_listener['persistenceProfileId'] = existing_vip_listener.get('persistenceProfile').get('id')
    if not(existing_vip_listener.get('persistenceProfile') is None and persistence_profile_id_1 is None):
        new_vip_listener['persistenceProfileId'] = persistence_profile_id_1
    if existing_vip_listener.get('fallbackPersistenceProfile'):
        existing_vip_listener['fallbackPersistenceProfileId'] = existing_vip_listener.get('fallbackPersistenceProfile').get('id')
    if not(existing_vip_listener.get('fallbackPersistenceProfile') is None and persistence_profile_id_2 is None):
        new_vip_listener['fallbackPersistenceProfileId'] = persistence_profile_id_2
    new_vip_listener['optimizationProfile'] = optimization_profile
    if existing_vip_listener.get('sslOffloadProfile'):
        existing_vip_listener['sslOffloadProfileId'] = existing_vip_listener.get('sslOffloadProfile').get('id')
    if not(existing_vip_listener.get('sslOffloadProfile') is None and ssl_profile_id is None):
        new_vip_listener['sslOffloadProfileId'] = ssl_profile_id
    if existing_vip_listener.get('irule'):
        existing_irules = existing_vip_listener.get('irule')
        existing_vip_listener['irule'] = []
        for existing_irule in existing_irules:
            existing_vip_listener.get('irule').append(existing_irule.get('id'))
    new_vip_listener['irule'] = irule_id_list

    compare_result = compare_json(new_vip_listener, existing_vip_listener, None)
    return compare_result['changes']


def main():
    """
    Main function
    :returns: VIP Listener Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(default=None, required=False, type='str'),
            name=dict(default=None, required=False, type='str'),
            description=dict(required=False, default=None, type='str'),
            type=dict(required=False, default='STANDARD', choices=VIP_LISTENER_TYPES),
            protocol=dict(required=False, default='ANY', type='str'),
            ip_address=dict(required=False, default=False, type='str'),
            port=dict(required=False, default=None, type='int', choices=[None] + list(range(1, 65535))),
            enabled=dict(required=False, default=True, type='bool'),
            preservation=dict(required=False, default='PRESERVE', choices=VIP_LISTENER_PRESERVATION),
            connection_limit=dict(required=False, default=100000, type='int', choices=range(1, 100001)),
            connection_rate_limit=dict(required=False, default=4000, type='int', choices=range(1, 4001)),
            pool=dict(required=False, default=None, type='str'),
            client_pool=dict(required=False, default=None, type='str'),
            persistence_profile=dict(required=False, default=None, type='str'),
            fallback_persistence_profile=dict(required=False, default=None, type='str'),
            optimization_profile=dict(required=False, default=None, type='str'),
            ssl_offload_profile=dict(required=False, default=None, type='str'),
            irules=dict(required=False, default=None, type='list'),
            state=dict(default='present', required=False, choices=['present', 'absent'])
        )
    )
    credentials = get_credentials()
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    v_listener = None

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if the Listener already exists
    try:
        if module.params.get('id'):
            v_listener = client.get_vip_listener(module.params.get('id'))
        else:
            v_listeners = client.list_vip_listener(network_domain_id=network_domain_id, name=module.params.get('name'))
            if len(v_listeners) == 1:
                v_listener = v_listeners[0]
    except (KeyError, IndexError, NTTCCISAPIException) as exc:
        module.fail_json(msg='Could not get a list of existing Virtual Listeners to check against - {0}'.format(exc))

    if state == 'present':
        if not v_listener:
            create_vip_listener(module, client, network_domain_id)
        else:
            if compare_vip_listener(module, client, network_domain_id, v_listener):
                update_vip_listener(module, client, network_domain_id, v_listener)
            module.exit_json(result=v_listener.get('id'))
    elif state == 'absent':
        if not v_listener:
            module.exit_json(msg='No Virtual Listener found. Nothing to remove.')
        delete_vip_listener(module, client, v_listener.get('id'))


if __name__ == '__main__':
    main()
