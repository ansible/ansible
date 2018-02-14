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
module: oneandone_vpn
short_description: Configure 1&1 VPN.
description:
     - Create, remove, update vpn
       This module has a dependency on 1and1 >= 1.0
version_added: "2.6"
options:
  state:
    description:
      - Define a VPN state to create, remove, or update.
    required: false
    default: 'present'
    choices: [ "present", "absent", "update" ]
  auth_token:
    description:
      - Authenticating API token provided by 1&1.
    required: true
  api_url:
    description:
      - Custom API URL. Overrides the
        ONEANDONE_API_URL environement variable.
    required: false
  name:
    description:
      - VPN name used with present state. Used as identifier (id or name) when used with absent state.
        maxLength=128
    required: true
  vpn:
    description:
      - The identifier (id or name) of the VPN used with update state.
    required: true
  description:
    description:
      - VPN description. maxLength=256
    required: false
  datacenter:
    description:
      - ID (or name) of the datacenter where the vpn will be created.
    required: false
  wait:
    description:
      - wait for the instance to be in the appropriate state before returning
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
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
  -  "Amel Ajdinovic (@aajdinov)"
  -  "Ethan Devenport (@edevenport)"
'''

EXAMPLES = '''

# Create a VPN.

- oneandone_vpn:
    auth_token: oneandone_private_api_key
    datacenter: US
    name: ansible VPN
    description: Create a VPN using ansible

# Update a VPN.

- oneandone_vpn:
    auth_token: oneandone_private_api_key
    vpn: ansible VPN
    name: ansible VPN updated
    description: Update a VPN using ansible
    state: update


# Delete a VPN

- oneandone_vpn:
    auth_token: oneandone_private_api_key
    name: ansible VPN updated
    state: absent

'''

RETURN = '''
vpn:
    description: Information about the vpn that was processed
    type: dict
    sample: '{"id": "F77CC589EBC120905B4F4719217BFF6D", "name": "My VPN"}'
    returned: always
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oneandone import (
    get_datacenter,
    get_vpn,
    OneAndOneResources,
    wait_for_resource_creation_completion
)

HAS_ONEANDONE_SDK = True

try:
    import oneandone.client
except ImportError:
    HAS_ONEANDONE_SDK = False


def update_vpn(module, oneandone_conn):
    """
    Modify VPN configuration file.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    _vpn_id = module.params.get('vpn')
    _name = module.params.get('name')
    _description = module.params.get('description')

    vpn = get_vpn(oneandone_conn, _vpn_id, True)

    try:
        updated_vpn = oneandone_conn.modify_vpn(vpn_id=vpn['id'],
                                                name=_name,
                                                description=_description)

        changed = True if updated_vpn else False

        return (changed, updated_vpn)
    except Exception as e:
        module.fail_json(msg=str(e))


def create_vpn(module, oneandone_conn):
    """
    Adds a new VPN.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    try:
        name = module.params.get('name')
        description = module.params.get('description')
        datacenter = module.params.get('datacenter')
        wait = module.params.get('wait')
        wait_timeout = module.params.get('wait_timeout')
        wait_interval = module.params.get('wait_interval')

        if datacenter is not None:
            datacenter_id = get_datacenter(oneandone_conn, datacenter)
            if datacenter_id is None:
                module.fail_json(
                    msg='datacenter %s not found.' % datacenter)

        _vpn = oneandone.client.Vpn(name,
                                    description,
                                    datacenter_id)

        vpn = oneandone_conn.create_vpn(_vpn)

        if wait:
            wait_for_resource_creation_completion(
                oneandone_conn,
                OneAndOneResources.vpn,
                vpn['id'],
                wait_timeout,
                wait_interval)

        changed = True if vpn else False

        return (changed, vpn)
    except Exception as e:
        module.fail_json(msg=str(e))


def remove_vpn(module, oneandone_conn):
    """
    Removes a VPN.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object
    """
    try:
        _vpn = module.params.get('name')

        vpn_id = get_vpn(oneandone_conn, _vpn)
        vpn = oneandone_conn.delete_vpn(vpn_id)

        changed = True if vpn else False

        return (changed, {
            'id': vpn['id'],
            'name': vpn['name']
        })
    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth_token=dict(
                type='str',
                default=os.environ.get('ONEANDONE_AUTH_TOKEN')),
            api_url=dict(
                type='str',
                default=os.environ.get('ONEANDONE_API_URL')),
            vpn=dict(type='str'),
            name=dict(type='str'),
            description=dict(type='str'),
            datacenter=dict(type='str'),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            wait_interval=dict(type='int', default=5),
            state=dict(type='str', default='present', choices=['present', 'absent', 'update']),
        )
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
                msg="'name' parameter is required to delete a VPN.")
        try:
            (changed, vpn) = remove_vpn(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))
    elif state == 'update':
        if not module.params.get('vpn'):
            module.fail_json(
                msg="'vpn' parameter is required to update a VPN.")
        try:
            (changed, vpn) = update_vpn(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))

    elif state == 'present':
        if not module.params.get('name'):
            module.fail_json(
                msg="name parameter is required for a new VPN.")
        try:
            (changed, vpn) = create_vpn(module, oneandone_conn)
        except Exception as e:
            module.fail_json(msg=str(e))

    module.exit_json(changed=changed, vpn=vpn)


if __name__ == '__main__':
    main()
