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
module: ntt_mcp_server_vapp
short_description: Enable/Disable and set/delete vApp properties on a server
description:
    - Enable/Disable and set/delete vApp properties on a server
    - https://docs.mcp-services.net/x/qIAkAQ
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
            - The name of the Cloud Network Domain
        required: true
        type: str
    server:
        description:
            - The name of the server
        required: true
        type: str
    iso:
        description:
            - Use ISO transport. vCenter uses a small ISO image on the first available CDROM drive to store the
            - ovf-env.xml file with the vApp properties
        required: false
        type: bool
        default: false
    vmtools:
        description:
            - Use VMWare Tools transport. The vApp properties are available through VMWare Tools or Open-VM-Tools
            - within the guest OS
        required: false
        type: bool
        default: true
    vapp_properties:
        description:
            - List of vApp property objects
        required: false
        type: list
        suboptions:
            key:
                description:
                    - Integer used for identifying a target property for update by set or for deletion by delete
                    - IMPORTANT: key is not directly retrievable within the Guest OS. Instead guestKey can be retrieved
                required: false
                type: int
            class_id:
                description:
                    - Optional hypervisor class name for the property
                required: false
                type: str
            id:
                description:
                    - Hypervisor id name for the property..
                required: false
                type: str
            instance_id:
                description:
                    - Optional hypervisor instanceId name for the property
                required: false
                type: str
            category:
                description:
                    - Optional string intended for property categorization
                required: false
                type: str
            label:
                description:
                    - Optional string display name for the property
                required: false
                type: str
            description:
                description:
                    - Optional string descriptive metadata about the property
                required: false
                type: str
            type:
                description:
                    - Defines the data type of the property
                    - For definitions of the supported vApp Property type formats refer to the Response Codes table
                    - below and to Introduction to vApp Properties "https://docs.mcp-services.net/x/qIAkAQ"
                    - When using some types e.g. ip it is best to set a default_value if an actual value is not set
                    - even if its 0.0.0.0
            userConfigurable:
                description:
                    - Boolean defining whether or not the property can have a user defined value
                required: false
                type: bool
                default: true
            value:
                description:
                    - value for the property
                    - Can only be provided if userConfigurable is true either in the same payload or already existing
                    - in the persisted schema definition for the vApp Property
                required: false
                type: str
            default_value:
                description:
                    - String default value for the property if no value is specified
                required: false
                type: str
    stop:
        description:
            - Should the server be stopped if it is running
            - Disk operations can only be performed while the server is stopped
        required: false
        type: bool
        default: true
    start:
        description:
            - Should the server be started after the NIC operations have completed
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
        default: 1200
    wait_poll_interval:
        description:
            - The time in between checking the status of the task in seconds
        required: false
        type: int
        default: 30
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

  - name: Enable and Set vApp properties on a server
    ntt_mcp_server_vapp:
      region: na
      datacenter: NA12
      network_domain: myCND
      server: myServer01
      iso: True
      vmtools: True
      vapp:
        - key: 0
          id: ipv4_address
          class_id: my_vapp
          instance_id: 1
          category: Network_Properties
          label: "Management IPv4 Address"
          description: "vApp Management IPv4 Address"
          type: ip
          value: 10.0.0.10
        - key: 1
          id: default_password
          class_id: my_vapp
          instance_id: 1
          category: System_Properties
          label: "Initial system password"
          description: "Initial system password"
          type: "password(8..20)"
          value: cool_password

  - name: Update a property
    ntt_mcp_server_vapp:
      region: na
      datacenter: NA12
      network_domain: myCND
      server: myServer01
      iso: True
      vmtools: True
      vapp:
        - key: 1
          id: default_password
          class_id: my_vapp
          instance_id: 1
          category: System_Properties
          label: "Initial system password"
          description: "Initial system password - new description"
          type: "password(8..20)""
          value: new_cool_password

  - name: Delete a property
    ntt_mcp_server_vapp:
      region: na
      datacenter: NA12
      network_domain: myCND
      server: myServer01
      vapp:
        - key: 1
      state: absent

  - name: Disable vApp completely and remove all properties
    ntt_mcp_server_vapp:
      region: na
      datacenter: NA12
      network_domain: myCND
      server: myServer01
      state: absent
'''

RETURN = '''
msg:
    description: A helpful message
    returned: failure and on no change
    type: string
    sample: No update required
data:
    description: Server objects
    returned: success
    type: complex
    contains:
        vAppProperty:
            description: The list of vApp properties
            type: list
            contains:
                value:
                    description: The property value. This is used inside the guest OS
                    type: string
                    sample: 10.0.0.11
                key:
                    description: The unique key identifier
                    type: int
                    sample: 2
                schema:
                    description: The schema for the vApp property
                    type: complex
                    contains:
                        category:
                            description: User defined property category
                            type: string
                            sample: Network_Properties
                        classId:
                            description: User defined Class ID
                            type: string
                            sample: my_vapp
                        description:
                            description: The vApp property description
                            type: string
                            sample: vApp Management IPv4 Address2
                        instanceId:
                            description: User defined instance ID
                            type: string
                            sample: 1
                        defaultValue:
                            description: The default value for the vApp property
                            type: string
                            sample: 0.0.0.0
                        userConfigurable:
                            description: Can the user configure this vApp property
                            type: bool
                        label:
                            description: User defined optional label
                            type: string
                            sample: Management IPv4 Address2
                        type:
                            description: The vApp property type
                            type: string
                            sample: ip
                        id:
                            description: The string ID of the property. This is used inside the guest OS
                            type: string
                            sample: ipv4_address2
        vmwareTransport:
            description: Enable VMWare Tools/Open-VM-Tools transport for vApp properties
            type: bool
        isoTransport:
            description: Enable ISO transport for vApp properties
            type: bool
'''

from time import sleep
import ast
from operator import itemgetter
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def validate_vapp_args(module, client):
    """
    Validate the user input for vApp properties

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :returns: True/False
    """
    try:
        vapp = module.params.get('vapp')

        if module.params.get('state') == 'absent':
            if not vapp or not len(vapp) > 0:
                module.fail_json(msg='A least one vApp key is required when deleting a vApp property')
            for prop in vapp:
                if not prop.get('key'):
                    module.fail_json(msg='A valid key is a required for each vApp property')
            return True

        for prop in vapp:
            if prop.get('key') is None:
                module.fail_json(msg='A valid key is a required for each vApp property')
            if prop.get('type') is None:
                module.fail_json(msg='A valid type is a required for each vApp property')
            if prop.get('id') is None:
                module.fail_json(msg='A valid id is a required for each vApp property')
        return True
    except (KeyError, IndexError, AttributeError) as e:
        module.fail_json(msg='Error validating vapp input: {0}'.format(e))


def configure_vapp(module, client, server_id):
    """
    Add monitoring to an existing server

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server_id: The UUID of the server to be updated
    :returns: True/False
    """
    try:
        client.set_vapp(server_id, module.params.get('iso'),
                        module.params.get('vmtools'),
                        module.params.get('vapp'))
        if module.params.get('wait'):
            wait_for_server(module, client, server_id)
        return True
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not enable vApp - {0}'.format(e))


def compare_vapp(module, vapp):
    """
    Compare an existing vApp configuration to one using the supplied arguments

    :arg module: The Ansible module instance
    :arg vapp: The existing vApp configuration
    :returns: the comparison result
    """
    new_vapp = dict()
    old_vapp_props = list()
    vapp_spec = module.params.get('vapp')
    new_vapp['vAppProperty'] = list()
    try:
        for prop in vapp.get('vAppProperty', list()):
            if 'password' in prop.get('schema').get('type'):
                if prop.get('value'):
                    del(prop['value'])
                if prop.get('schema').get('defaultValue'):
                    del(prop['schema']['defaultValue'])

        new_vapp['isoTransport'] = module.params.get('iso')
        new_vapp['vmwareTransport'] = module.params.get('vmtools')

        for prop in vapp_spec:
            for old_prop in vapp.get('vAppProperty', list()):
                if prop.get('key') == old_prop.get('key'):
                    old_vapp_props.append(old_prop)
            temp_prop = dict()
            temp_prop['key'] = prop.get('key')
            if 'password' not in prop.get('type'):
                temp_prop['value'] = prop.get('value')
            temp_prop['schema'] = dict()
            temp_prop['schema']['id'] = prop.get('id')
            temp_prop['schema']['type'] = prop.get('type')
            if prop.get('class_id') is not None:
                temp_prop['schema']['classId'] = prop.get('class_id')
            if prop.get('instance_id') is not None:
                temp_prop['schema']['instanceId'] = str(prop.get('instance_id'))
            if prop.get('category') is not None:
                temp_prop['schema']['category'] = prop.get('category')
            if prop.get('label') is not None:
                temp_prop['schema']['label'] = prop.get('label')
            if prop.get('description') is not None:
                temp_prop['schema']['description'] = prop.get('description')
            if prop.get('configurable') is not None:
                temp_prop['schema']['userConfigurable'] = prop.get('configurable')
            else:
                temp_prop['schema']['userConfigurable'] = True
            if prop.get('default_value') is not None and 'password' not in prop.get('type'):
                temp_prop['schema']['defaultValue'] = prop.get('default_value')
            new_vapp['vAppProperty'].append(temp_prop)

        vapp['vAppProperty'] = old_vapp_props
        new_vapp['vAppProperty'] = sorted(new_vapp.get('vAppProperty'), key=itemgetter('key'))
        vapp['vAppProperty'] = sorted(vapp.get('vAppProperty'), key=itemgetter('key'))
        compare_result = compare_json(new_vapp, vapp, None)
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(data=compare_result)
        return compare_result.get('changes')
    except (KeyError, IndexError, AttributeError) as e:
        module.fail_json(msg='Error determining state changes (if any): {0}'.format(e))


def remove_vapp(module, client, server_id, vapp):
    """
    Remove monitoring from an existing server

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server_id: The UUID of the server to be updated
    :returns: The updated server
    """

    try:
        vapp_keys = list()
        for prop in module.params.get('vapp'):
            vapp_keys.append(prop.get('key'))
        client.remove_vapp_property(server_id, vapp.get('isoTransport'), vapp.get('vmwareTransport'), vapp_keys)
        if module.params.get('wait'):
            wait_for_server(module, client, server_id)
        return True
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could remove the vApp property(s) - {0}'.format(e))


def disable_vapp(module, client, server_id):
    try:
        client.disable_vapp(server_id)
        if module.params.get('wait'):
            wait_for_server(module, client, server_id)
        module.exit_json(msg='vApp has been successfully disabled on the server with ID {0}'.format(server_id))
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could remove the server monitoring - {0}'.format(e))


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
            if server.get('state') == 'NORMAL':
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
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            server=dict(required=True, type='str'),
            iso=dict(required=False, default=False, type='bool'),
            vmtools=dict(required=False, default=True, type='bool'),
            vapp=dict(required=False, default=None, type='list'),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=600, type='int'),
            wait_poll_interval=dict(required=False, default=5, type='int'),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    name = module.params.get('server')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    network_domain_name = module.params.get('network_domain')
    server = vapp = dict()
    server_id = None

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

    # Get the CND object based on the supplied name
    try:
        if network_domain_name is None:
            module.fail_json(msg='No network_domain or network_info.network_domain was provided')
        network = client.get_network_domain_by_name(datacenter=datacenter, name=network_domain_name)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Failed to find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if the Server exists based on the supplied name
    try:
        server = client.get_server_by_name(datacenter, network_domain_id, None, name)
        server_id = server.get('id')
        if server.get('started'):
            module.fail_json(msg='vApp properties cannot be modified while the server is running')
        if not server_id:
            module.fail_json(msg='Failed to locate the server')
        vapp = ast.literal_eval(str(server.get('vAppProperties')).encode('ascii')) or dict()
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed to locate the server - {0}'.format(e))

    # Check vApp dictionary is valid
    if not (state == 'absent' and module.params.get('vapp') is None):
        validate_vapp_args(module, client)

    if state == 'present':
        if compare_vapp(module, vapp):
            configure_vapp(module, client, server_id)
        else:
            module.exit_json(msg='No update required', data=server.get('vAppProperties'))
        try:
            server = client.get_server_by_name(datacenter, network_domain_id, None, name)
        except NTTMCPAPIException:
            module.warn(warning='The update was successfull but there was an issue getting the updated server')
            pass
        module.exit_json(changed=True, data=server.get('vAppProperties'))
    elif state == 'absent':
        try:
            if not vapp:
                module.exit_json(msg='Server {0} does not currently have vApp enabled'.format(server.get('name')))
            # Implement Check Mode
            if module.check_mode:
                if not module.params.get('vapp'):
                    module.exit_json(msg='vApp will be disabled on the server with ID {0}'.format(server.get('id')))
                module.exit_json(msg='The following vApp keys will be removed from the server with ID {0}'.format(
                                 server.get('id')), data=module.params.get('vapp'))

            if module.params.get('vapp'):
                remove_vapp(module, client, server.get('id'), vapp)
                try:
                    server = client.get_server_by_name(datacenter, network_domain_id, None, name)
                except NTTMCPAPIException:
                    module.warn(warning='The update was successfull but there was an issue getting the updated server')
                    pass
                module.exit_json(changed=True, data=server.get('vAppProperties'))
            else:
                disable_vapp(module, client, server.get('id'))
        except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
            module.fail_json(msg='Could not remove vApp from server {0} - {1}'.format(server.get('id'),
                                                                                      e))


if __name__ == '__main__':
    main()
