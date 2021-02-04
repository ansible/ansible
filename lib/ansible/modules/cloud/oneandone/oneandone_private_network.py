#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: oneandone_private_network
short_description: Configure 1&1 private networking.
description:
     - Create, remove, reconfigure, update a private network.
       This module has a dependency on 1and1 >= 1.0
version_added: "2.5"
options:
  state:
    description:
      - Define a network's state to create, remove, or update.
    required: false
    default: 'present'
    choices: [ "present", "absent", "update" ]
  auth_token:
    description:
      - Authenticating API token provided by 1&1.
    required: true
  private_network:
    description:
      - The identifier (id or name) of the network used with update state.
    required: true
  api_url:
    description:
      - Custom API URL. Overrides the
        ONEANDONE_API_URL environement variable.
    required: false
  name:
    description:
      - Private network name used with present state. Used as identifier (id or name) when used with absent state.
    required: true
  description:
    description:
      - Set a description for the network.
  datacenter:
    description:
      - The identifier of the datacenter where the private network will be created
  network_address:
    description:
      - Set a private network space, i.e. 192.168.1.0
  subnet_mask:
    description:
      - Set the netmask for the private network, i.e. 255.255.255.0
  add_members:
    description:
      - List of server identifiers (name or id) to be added to the private network.
  remove_members:
    description:
      - List of server identifiers (name or id) to be removed from the private network.
  wait:
    description:
      - wait for the instance to be in state 'running' before returning
    required: false
    default: "yes"
    type: bool
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  wait_interval:
    description:
      - Defines the number of seconds to wait when using the _wait_for methods
    default: 5

requirements:
     - "1and1"
     - "python >= 2.6"

author:
  - Amel Ajdinovic (@aajdinov)
  - Ethan Devenport (@edevenport)
'''

EXAMPLES = '''

# Provisioning example. Create and destroy private networks.

- oneandone_private_network:
    auth_token: oneandone_private_api_key
    name: backup_network
    description: Testing creation of a private network with ansible
    network_address: 70.35.193.100
    subnet_mask: 255.0.0.0
    datacenter: US

- oneandone_private_network:
    auth_token: oneandone_private_api_key
    state: absent
    name: backup_network

# Modify the private network.

- oneandone_private_network:
    auth_token: oneandone_private_api_key
    state: update
    private_network: backup_network
    network_address: 192.168.2.0
    subnet_mask: 255.255.255.0

# Add members to the private network.

- oneandone_private_network:
    auth_token: oneandone_private_api_key
    state: update
    private_network: backup_network
    add_members:
     - server identifier (id or name)

# Remove members from the private network.

- oneandone_private_network:
    auth_token: oneandone_private_api_key
    state: update
    private_network: backup_network
    remove_members:
     - server identifier (id or name)

'''

RETURN = '''
private_network:
    description: Information about the private network.
    type: dict
    sample: '{"name": "backup_network", "id": "55726DEDA20C99CF6F2AF8F18CAC9963"}'
    returned: always
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oneandone import (
    get_private_network,
    get_server,
    get_datacenter,
    OneAndOneResources,
    wait_for_resource_creation_completion,
    wait_for_resource_deletion_completion
)

HAS_ONEANDONE_SDK = True

try:
    import oneandone.client
except ImportError:
    HAS_ONEANDONE_SDK = False

DATACENTERS = ['US', 'ES', 'DE', 'GB']


def _check_mode(module, result):
    if module.check_mode:
        module.exit_json(
            changed=result
        )


def _add_servers(module, oneandone_conn, name, members):
    try:
        private_network_id = get_private_network(oneandone_conn, name)

        if module.check_mode:
            if private_network_id and members:
                return True
            return False

        network = oneandone_conn.attach_private_network_servers(
            private_network_id=private_network_id,
            server_ids=members)

        return network
    except Exception as e:
        module.fail_json(msg=str(e))


def _remove_member(module, oneandone_conn, name, member_id):
    try:
        private_network_id = get_private_network(oneandone_conn, name)

        if module.check_mode:
            if private_network_id:
                network_member = oneandone_conn.get_private_network_server(
                    private_network_id=private_network_id,
                    server_id=member_id)
                if network_member:
                    return True
            return False

        network = oneandone_conn.remove_private_network_server(
            private_network_id=name,
            server_id=member_id)

        return network
    except Exception as ex:
        module.fail_json(msg=str(ex))


def create_network(module, oneandone_conn):
    """
    Create new private network

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object

    Returns a dictionary containing a 'changed' attribute indicating whether
    any network was added.
    """
    name = module.params.get('name')
    description = module.params.get('description')
    network_address = module.params.get('network_address')
    subnet_mask = module.params.get('subnet_mask')
    datacenter = module.params.get('datacenter')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    wait_interval = module.params.get('wait_interval')

    if datacenter is not None:
        datacenter_id = get_datacenter(oneandone_conn, datacenter)
        if datacenter_id is None:
            module.fail_json(
                msg='datacenter %s not found.' % datacenter)

    try:
        _check_mode(module, True)
        network = oneandone_conn.create_private_network(
            private_network=oneandone.client.PrivateNetwork(
                name=name,
                description=description,
                network_address=network_address,
                subnet_mask=subnet_mask,
                datacenter_id=datacenter_id
            ))

        if wait:
            wait_for_resource_creation_completion(
                oneandone_conn,
                OneAndOneResources.private_network,
                network['id'],
                wait_timeout,
                wait_interval)
            network = get_private_network(oneandone_conn,
                                          network['id'],
                                          True)

        changed = True if network else False

        _check_mode(module, False)

        return (changed, network)
    except Exception as e:
        module.fail_json(msg=str(e))


def update_network(module, oneandone_conn):
    """
    Modifies a private network.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    try:
        _private_network_id = module.params.get('private_network')
        _name = module.params.get('name')
        _description = module.params.get('description')
        _network_address = module.params.get('network_address')
        _subnet_mask = module.params.get('subnet_mask')
        _add_members = module.params.get('add_members')
        _remove_members = module.params.get('remove_members')

        changed = False

        private_network = get_private_network(oneandone_conn,
                                              _private_network_id,
                                              True)
        if private_network is None:
            _check_mode(module, False)

        if _name or _description or _network_address or _subnet_mask:
            _check_mode(module, True)
            private_network = oneandone_conn.modify_private_network(
                private_network_id=private_network['id'],
                name=_name,
                description=_description,
                network_address=_network_address,
                subnet_mask=_subnet_mask)
            changed = True

        if _add_members:
            instances = []

            for member in _add_members:
                instance_id = get_server(oneandone_conn, member)
                instance_obj = oneandone.client.AttachServer(server_id=instance_id)

                instances.extend([instance_obj])
            private_network = _add_servers(module, oneandone_conn, private_network['id'], instances)
            _check_mode(module, private_network)
            changed = True

        if _remove_members:
            chk_changed = False
            for member in _remove_members:
                instance = get_server(oneandone_conn, member, True)

                if module.check_mode:
                    chk_changed |= _remove_member(module,
                                                  oneandone_conn,
                                                  private_network['id'],
                                                  instance['id'])
                _check_mode(module, instance and chk_changed)

                _remove_member(module,
                               oneandone_conn,
                               private_network['id'],
                               instance['id'])
            private_network = get_private_network(oneandone_conn,
                                                  private_network['id'],
                                                  True)
            changed = True

        return (changed, private_network)
    except Exception as ex:
        module.fail_json(msg=str(ex))


def remove_network(module, oneandone_conn):
    """
    Removes a private network.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object.
    """
    try:
        pn_id = module.params.get('name')
        wait_timeout = module.params.get('wait_timeout')
        wait_interval = module.params.get('wait_interval')

        private_network_id = get_private_network(oneandone_conn, pn_id)
        if module.check_mode:
            if private_network_id is None:
                _check_mode(module, False)
            _check_mode(module, True)
        private_network = oneandone_conn.delete_private_network(private_network_id)
        wait_for_resource_deletion_completion(oneandone_conn,
                                              OneAndOneResources.private_network,
                                              private_network['id'],
                                              wait_timeout,
                                              wait_interval)

        changed = True if private_network else False

        return (changed, {
            'id': private_network['id'],
            'name': private_network['name']
        })
    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth_token=dict(
                type='str',
                default=os.environ.get('ONEANDONE_AUTH_TOKEN'),
                no_log=True),
            api_url=dict(
                type='str',
                default=os.environ.get('ONEANDONE_API_URL')),
            private_network=dict(type='str'),
            name=dict(type='str'),
            description=dict(type='str'),
            network_address=dict(type='str'),
            subnet_mask=dict(type='str'),
            add_members=dict(type='list', default=[]),
            remove_members=dict(type='list', default=[]),
            datacenter=dict(
                choices=DATACENTERS),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            wait_interval=dict(type='int', default=5),
            state=dict(type='str', default='present', choices=['present', 'absent', 'update']),
        ),
        supports_check_mode=True
    )

    if not HAS_ONEANDONE_SDK:
        module.fail_json(msg='1and1 required for this module')

    if not module.params.get('auth_token'):
        module.fail_json(
            msg='auth_token parameter is required.')

    if not module.params.get('api_url'):
        oneandone_conn = oneandone.client.OneAndOneService(
            api_token=module.params.get('auth_token'))
    else:
        oneandone_conn = oneandone.client.OneAndOneService(
            api_token=module.params.get('auth_token'), api_url=module.params.get('api_url'))

    state = module.params.get('state')

    if state == 'absent':
        if not module.params.get('name'):
            module.fail_json(
                msg="'name' parameter is required for deleting a network.")
        try:
            (changed, private_network) = remove_network(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))
    elif state == 'update':
        if not module.params.get('private_network'):
            module.fail_json(
                msg="'private_network' parameter is required for updating a network.")
        try:
            (changed, private_network) = update_network(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))
    elif state == 'present':
        if not module.params.get('name'):
            module.fail_json(
                msg="'name' parameter is required for new networks.")
        try:
            (changed, private_network) = create_network(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))

    module.exit_json(changed=changed, private_network=private_network)


if __name__ == '__main__':
    main()
