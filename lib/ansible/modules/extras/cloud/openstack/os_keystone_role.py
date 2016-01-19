#!/usr/bin/python
# Copyright (c) 2016 IBM
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
module: os_keystone_role
short_description: Manage OpenStack Identity Roles
extends_documentation_fragment: openstack
version_added: "2.1"
author: "Monty Taylor (@emonty), David Shrewsbury (@Shrews)"
description:
    - Manage OpenStack Identity Roles.
options:
   name:
     description:
        - Role Name
     required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a role named "demo"
- os_keystone_role:
    cloud: mycloud
    state: present
    name: demo

# Delete the role named "demo"
- os_keystone_role:
    cloud: mycloud
    state: absent
    name: demo
'''

RETURN = '''
role:
    description: Dictionary describing the role.
    returned: On success when I(state) is 'present'.
    type: dictionary
    contains:
        id:
            description: Unique role ID.
            type: string
            sample: "677bfab34c844a01b88a217aa12ec4c2"
        name:
            description: Role name.
            type: string
            sample: "demo"
'''


def _system_state_change(state, role):
    if state == 'present' and not role:
        return True
    if state == 'absent' and role:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params.pop('name')
    state = module.params.pop('state')

    try:
        cloud = shade.operator_cloud(**module.params)

        role = cloud.get_role(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(state, role))

        if state == 'present':
            if role is None:
                role = cloud.create_role(name)
                changed = True
            else:
                changed = False
            module.exit_json(changed=changed, role=role)
        elif state == 'absent':
            if role is None:
                changed=False
            else:
                cloud.delete_role(name)
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *


if __name__ == '__main__':
    main()
