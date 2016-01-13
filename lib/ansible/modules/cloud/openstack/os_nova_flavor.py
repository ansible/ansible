#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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
module: os_nova_flavor
short_description: Manage OpenStack compute flavors
extends_documentation_fragment: openstack
version_added: "2.0"
author: "David Shrewsbury (@Shrews)"
description:
   - Add or remove flavors from OpenStack.
options:
   state:
     description:
        - Indicate desired state of the resource. When I(state) is 'present',
          then I(ram), I(vcpus), and I(disk) are all required. There are no
          default values for those parameters.
     choices: ['present', 'absent']
     required: false
     default: present
   name:
     description:
        - Flavor name.
     required: true
   ram:
     description:
        - Amount of memory, in MB.
     required: false
     default: null
   vcpus:
     description:
        - Number of virtual CPUs.
     required: false
     default: null
   disk:
     description:
        - Size of local disk, in GB.
     required: false
     default: null
   ephemeral:
     description:
        - Ephemeral space size, in GB.
     required: false
     default: 0
   swap:
     description:
        - Swap space size, in MB.
     required: false
     default: 0
   rxtx_factor:
     description:
        - RX/TX factor.
     required: false
     default: 1.0
   is_public:
     description:
        - Make flavor accessible to the public.
     required: false
     default: true
   flavorid:
     description:
        - ID for the flavor. This is optional as a unique UUID will be
          assigned if a value is not specified.
     required: false
     default: "auto"
requirements: ["shade"]
'''

EXAMPLES = '''
# Create 'tiny' flavor with 1024MB of RAM, 1 virtual CPU, and 10GB of
# local disk, and 10GB of ephemeral.
- os_nova_flavor:
    cloud=mycloud
    state=present
    name=tiny
    ram=1024
    vcpus=1
    disk=10
    ephemeral=10

# Delete 'tiny' flavor
- os_nova_flavor:
    cloud=mycloud
    state=absent
    name=tiny
'''

RETURN = '''
flavor:
    description: Dictionary describing the flavor.
    returned: On success when I(state) is 'present'
    type: dictionary
    contains:
        id:
            description: Flavor ID.
            returned: success
            type: string
            sample: "515256b8-7027-4d73-aa54-4e30a4a4a339"
        name:
            description: Flavor name.
            returned: success
            type: string
            sample: "tiny"
        disk:
            description: Size of local disk, in GB.
            returned: success
            type: int
            sample: 10
        ephemeral:
            description: Ephemeral space size, in GB.
            returned: success
            type: int
            sample: 10
        ram:
            description: Amount of memory, in MB.
            returned: success
            type: int
            sample: 1024
        swap:
            description: Swap space size, in MB.
            returned: success
            type: int
            sample: 100
        vcpus:
            description: Number of virtual CPUs.
            returned: success
            type: int
            sample: 2
        is_public:
            description: Make flavor accessible to the public.
            returned: success
            type: bool
            sample: true
'''


def _system_state_change(module, flavor):
    state = module.params['state']
    if state == 'present' and not flavor:
        return True
    if state == 'absent' and flavor:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        state        = dict(required=False, default='present',
                            choices=['absent', 'present']),
        name         = dict(required=False),

        # required when state is 'present'
        ram          = dict(required=False, type='int'),
        vcpus        = dict(required=False, type='int'),
        disk         = dict(required=False, type='int'),

        ephemeral    = dict(required=False, default=0, type='int'),
        swap         = dict(required=False, default=0, type='int'),
        rxtx_factor  = dict(required=False, default=1.0, type='float'),
        is_public    = dict(required=False, default=True, type='bool'),
        flavorid     = dict(required=False, default="auto"),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['ram', 'vcpus', 'disk'])
        ],
        **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    name = module.params['name']

    try:
        cloud = shade.operator_cloud(**module.params)
        flavor = cloud.get_flavor(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, flavor))

        if state == 'present':
            if not flavor:
                flavor = cloud.create_flavor(
                    name=name,
                    ram=module.params['ram'],
                    vcpus=module.params['vcpus'],
                    disk=module.params['disk'],
                    flavorid=module.params['flavorid'],
                    ephemeral=module.params['ephemeral'],
                    swap=module.params['swap'],
                    rxtx_factor=module.params['rxtx_factor'],
                    is_public=module.params['is_public']
                )
                changed=True
            else:
                changed=False

            module.exit_json(changed=changed,
                             flavor=flavor,
                             id=flavor['id'])

        elif state == 'absent':
            if flavor:
                cloud.delete_flavor(name)
                module.exit_json(changed=True)
            module.exit_json(changed=False)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
