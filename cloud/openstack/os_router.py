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
module: os_router
short_description: Create or Delete routers from OpenStack
extends_documentation_fragment: openstack
version_added: "1.10"
description:
   - Create or Delete routers from OpenStack. Although Neutron allows
     routers to share the same name, this module enforces name uniqueness
     to be more user friendly.
options:
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   name:
     description:
        - Name to be give to the router
     required: true
   admin_state_up:
     description:
        - Desired admin state of the created router.
     required: false
     default: true
requirements: ["shade"]
'''

EXAMPLES = '''
# Creates a router for tenant admin
- os_router:
    state=present
    name=router1
    admin_state_up=True
'''


def _needs_update(router, admin_state_up):
    """Decide if the given router needs an update.

    The only attribute of the router that we allow to change is the value
    of admin_state_up. Name changes are not supported here.
    """
    if router['admin_state_up'] != admin_state_up:
        return True
    return False

def _system_state_change(module, router):
    """Check if the system state would be changed."""
    state = module.params['state']
    if state == 'absent' and router:
        return True
    if state == 'present':
        if not router:
            return True
        return _needs_update(router, module.params['admin_state_up'])
    return False

def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        admin_state_up=dict(type='bool', default=True),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    admin_state_up = module.params['admin_state_up']
    state = module.params['state']

    try:
        cloud = shade.openstack_cloud(**module.params)
        router = cloud.get_router(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, router))

        if state == 'present':
            if not router:
                router = cloud.create_router(name, admin_state_up)
                module.exit_json(changed=True, result="created",
                                 id=router['id'])
            else:
                if _needs_update(router, admin_state_up):
                    cloud.update_router(router['id'],
                                        admin_state_up=admin_state_up)
                    module.exit_json(changed=True, result="updated",
                                     id=router['id'])
                else:
                    module.exit_json(changed=False, result="success",
                                     id=router['id'])

        elif state == 'absent':
            if not router:
                module.exit_json(changed=False, result="success")
            else:
                cloud.delete_router(name)
                module.exit_json(changed=True, result="deleted")

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
