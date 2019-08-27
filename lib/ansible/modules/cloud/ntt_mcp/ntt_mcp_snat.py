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
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_snat
short_description: Add and Remove SNAT exclusions entries for a Cloud Network Domain
description:
    - Add and Remove SNAT exclusions entries for a Cloud Network Domain
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: true
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
    id:
        description:
            - The UUID of an existing SNAT exclusion record
        required: false
        type: str
    description:
        description:
            - The description for the SNAT exclusion
        required: false
        type: str
    cidr:
        description:
            - The IPv4 or IPv6 destination network address to modify in CIDR format for e.g. 192.168.0.0/24
        required: false
        type: str
    new_cidr:
        description:
            - The IPv4 or IPv6 destination network address to modify in CIDR format for e.g. 192.168.0.0/24
            - Used for update purposes
        required: false
        type: str
    state:
        description:
            - The action to be performed
            - Restore will restore the SNAT exclusions back to the MCP baseline defaults for the Cloud Network Domain
        required: true
        type: str
        default: present
        choices:
            - present
            - absent
            - restore
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

- name: Create a SNAT Exclusion
  ntt_mcp_snat:
    region: na
    datacenter: NA9
    network_domain: my_network_domain
    description: "My SNAT Exclusion"
    cidr: "192.168.0.0/24"
    state: present

- name: Update a SNAT Exclusion
  ntt_mcp_snat:
    region: na
    datacenter: NA9
    network_domain: my_network_domain
    description: "My Updated SNAT Exclusion"
    cidr: "192.168.0.0/24"
    new_cidr: "192.168.1.0/25"
    state: present

- name: Delete a SNAT Exclusion by ID
  ntt_mcp_snat:
    region: na
    datacenter: NA9
    network_domain: my_network_domain
    id: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
    state: absent

- name: Delete a SNAT Exclusion by network and prefix
  ntt_mcp_snat:
    region: na
    datacenter: NA9
    network_domain: my_network_domain
    cidr: "192.168.0.0/24"
    state: absent

- name: Restoring Static Routes to default
  ntt_mcp_snat:
    region: na
    datacenter: NA9
    network_domain: my_network_domain
    state: restore
'''

RETURN = '''
data:
    description: Array of Port List objects
    returned: success
    type: complex
    contains:
        snat:
            description: The SNAT exclusion object or string(s)
            type: complex
            contains:
                id:
                    description: The UUID of the SNAT exclusion
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                datacenterId:
                    description: Datacenter id/location
                    type: str
                    sample: NA3
                createTime:
                    description: The creation date of the image
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                description:
                    description: Optional description for the SNAT exclusion
                    type: str
                    sample: "something"
                networkDomainId:
                    description: Network Domain ID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                state:
                    state:
                    description: Status of the static route
                    type: str
                    sample: NORMAL
                destinationPrefixSize:
                    description: The destination prefix for the static route
                    type: int
                    sample: 24
                destinationIpv4NetworkAddress:
                    description: The destination network address for the static route
                    type: str
                    sample: "192.168.0.0"
                type:
                    description: The type of static route e.g. SYSTEM or CLIENT
                    type: str
                    sample: "CLIENT"
            returned: when state == present
        msg:
            description: A useful return message
            type: str
            returned: when state == absent or state == restore
'''

from copy import deepcopy
try:
    from ipaddress import (ip_network as ip_net, AddressValueError)
    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException

# Python3 workaround for unicode function so the same code can be used with ipaddress later
try:
    unicode('')
except NameError:
    unicode = str


def create_snat_exclusion(module, client, network_domain_id, network_cidr):
    """
    Create a SNAT exclusion

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg network_cidr: The network CIDR for the SNAT exclusion
    :returns: The created SNAT exclusion
    """
    return_data = return_object('snat')
    description = module.params.get('description')
    network = str(network_cidr.network_address)
    prefix = network_cidr.prefixlen

    if None in [network_domain_id, network, prefix]:
        module.fail_json(msg='A valid value is required for network_domain, network and prefix')
    try:
        client.create_snat_exclusion(network_domain_id, description, network, prefix)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not create the SNAT exclusion - {0}'.format(e))

    try:
        return_data['snat'] = client.list_snat_exclusion(network_domain_id=network_domain_id, network=network, prefix=prefix)[0]
    except (KeyError, IndexError, NTTMCPAPIException) as e:
        module.exit_json(changed=True, msg='Could not verify the SNAT exclusion was created - {0}'.format(e), results=None)

    module.exit_json(changed=True, data=return_data['snat'])


def delete_snat_exclusion(module, client, static_route_id):
    """
    Delete a SNAT exclusion

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg static_route_id: The UUID of the static route to exclude from SNAT
    :returns: A message
    """
    if static_route_id is None:
        module.exit_json(msg='No existing SNAT exclusion was matched for the ID: {0}'.format(module.params.get('id')))
    try:
        client.remove_snat_exclusion(static_route_id)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not delete the SNAT exclusion - {0}'.format(e))


def compare_snat_exclusion(module, new_network_cidr, snat):
    """
    Compare two SNAT exclusions

    :arg module: The Ansible module instance
    :arg snat: The dict containing the SNAT exclusion to compare to
    :returns: Any differences between the two SNAT exclusions
    """
    new_snat = deepcopy(snat)
    if module.params.get('description'):
        new_snat['description'] = module.params.get('description')
    if new_network_cidr:
        new_snat['destinationIpv4NetworkAddress'] = str(new_network_cidr.network_address)
        new_snat['destinationIpv4PrefixSize'] = new_network_cidr.prefixlen

    compare_result = compare_json(new_snat, snat, None)
    # Implement Check Mode
    if module.check_mode:
        module.exit_json(data=compare_result)
    return compare_result['changes']


def main():
    """
    Main function

    :returns: SNAT exclusion Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(default=None, required=False, type='str'),
            description=dict(default=None, required=False, type='str'),
            cidr=dict(default=None, required=False, type='str'),
            new_cidr=dict(default=None, required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent', 'restore'])
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    snat = new_network_cidr = network_cidr = None
    snats = []

    # Check Imports
    if not HAS_IPADDRESS:
        module.fail_json(msg='Missing Python module: ipaddress')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params['region'])

    # Check to see the CIDR provided is valid
    if module.params.get('cidr'):
        try:
            network_cidr = ip_net(unicode(module.params.get('cidr')))
        except (AddressValueError, ValueError) as e:
            module.fail_json(msg='Invalid network CIDR format {0}: {1}'.format(module.params.get('cidr'), e))
        if network_cidr.version != 4:
            module.fail_json(msg='The cidr argument must be in valid IPv4 CIDR notation')
    if module.params.get('new_cidr'):
        try:
            new_network_cidr = ip_net(unicode(module.params.get('new_cidr')))
        except (AddressValueError, ValueError) as e:
            module.fail_json(msg='Invalid network CIDR format {0}: {1}'.format(module.params.get('new_cidr'), e))
        if new_network_cidr.version != 4:
            module.fail_json(msg='The new_cidr argument must be in valid IPv4 CIDR notation')

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if a SNAT exclusion already exists for this ID
    if not state == 'restore':
        try:
            if module.params.get('id'):
                snat = client.get_snat_exclusion(module.params.get('id'))
            if not snat and network_cidr:
                # If no matching routes were found for the name check to see if the supplied network parameters match a rule with a different name
                snats = client.list_snat_exclusion(network_domain_id=network_domain_id,
                                                   network=str(network_cidr.network_address),
                                                   prefix=network_cidr.prefixlen)
                if len(snats) == 1:
                    snat = snats[0]
        except (IndexError, AttributeError, NTTMCPAPIException) as e:
            module.fail_json(msg='Failed to get a list of existing SNAT exclusions - {0}'.format(e))

    try:
        if state == 'present':
            if not snat:
                # Implement Check Mode
                if module.check_mode:
                    module.exit_json(msg='A new SNAT exclusion will be created for {0}'.format(str(network_cidr)))
                create_snat_exclusion(module, client, network_domain_id, network_cidr)
            else:
                # SNAT exclusions cannot be updated. The old one must be removed and a new one created with the new parameters
                if compare_snat_exclusion(module, new_network_cidr, snat):
                    delete_snat_exclusion(module, client, snat.get('id'))
                    create_snat_exclusion(module, client, network_domain_id, new_network_cidr)
                module.exit_json(data=snat)
        elif state == 'restore':
            client.restore_snat_exclusion(network_domain_id)
            module.exit_json(changed=True, msg='Successfully restored the default SNAT exclusions')
        elif state == 'absent':
            if snat:
                # Implement Check Mode
                if module.check_mode:
                    module.exit_json(msg='An existing SNAT exclusion was found for {0} and will be removed'.format(
                        snat.get('id')))
                delete_snat_exclusion(module, client, snat.get('id'))
                module.exit_json(changed=True, msg='Successfully deleted the SNAT exclusion')
            else:
                module.exit_json(msg='No existing SNAT exclusion was matched')
    except (KeyError, IndexError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not update the SNAT exclusion - {0}'.format(e))


if __name__ == '__main__':
    main()
