#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
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

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_network
short_description: Creates/removes networks from OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
   - Add or remove network from OpenStack.
options:
   name:
     description:
        - Name to be assigned to the network.
     required: true
   shared:
     description:
        - Whether this network is shared or not.
     required: false
     default: false
   admin_state_up:
     description:
        - Whether the state should be marked as up or down.
     required: false
     default: true
   external:
     description:
        - Whether this network is externally accessible.
     required: false
     default: false
   state:
     description:
        - Indicate desired state of the resource.
     choices: ['present', 'absent']
     required: false
     default: present
requirements: ["shade"]
'''

EXAMPLES = '''
# Create an externally accessible network named 'ext_network'.
- os_network:
    cloud: mycloud
    state: present
    name: ext_network
    external: true
'''

RETURN = '''
network:
    description: Dictionary describing the network.
    returned: On success when I(state) is 'present'.
    type: dictionary
    contains:
        id:
            description: Network ID.
            type: string
            sample: "4bb4f9a5-3bd2-4562-bf6a-d17a6341bb56"
        name:
            description: Network name.
            type: string
            sample: "ext_network"
        shared:
            description: Indicates whether this network is shared across all tenants.
            type: bool
            sample: false
        status:
            description: Network status.
            type: string
            sample: "ACTIVE"
        mtu:
            description: The MTU of a network resource.
            type: integer
            sample: 0
        admin_state_up:
            description: The administrative state of the network.
            type: bool
            sample: true
        port_security_enabled:
            description: The port security status
            type: bool
            sample: true
        router:external:
            description: Indicates whether this network is externally accessible.
            type: bool
            sample: true
        tenant_id:
            description: The tenant ID.
            type: string
            sample: "06820f94b9f54b119636be2728d216fc"
        subnets:
            description: The associated subnets.
            type: list
            sample: []
'''


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        shared=dict(default=False, type='bool'),
        admin_state_up=dict(default=True, type='bool'),
        external=dict(default=False, type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    name = module.params['name']
    shared = module.params['shared']
    admin_state_up = module.params['admin_state_up']
    external = module.params['external']

    try:
        cloud = shade.openstack_cloud(**module.params)
        net = cloud.get_network(name)

        if state == 'present':
            if not net:
                net = cloud.create_network(name, shared, admin_state_up, external)
                changed = True
            else:
                changed = False
            module.exit_json(changed=changed, network=net, id=net['id'])

        elif state == 'absent':
            if not net:
                module.exit_json(changed=False)
            else:
                cloud.delete_network(name)
                module.exit_json(changed=True)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == "__main__":
    main()
