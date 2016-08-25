#!/usr/bin/python

# Copyright (c) 2016 Catalyst IT Limited
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
module: os_server_group
short_description: Manage OpenStack server groups
extends_documentation_fragment: openstack
version_added: "2.2"
author: "Lingxian Kong (@kong)"
description:
   - Add or remove server groups from OpenStack.
options:
   state:
     description:
        - Indicate desired state of the resource. When I(state) is 'present',
          then I(policies) is required.
     choices: ['present', 'absent']
     required: false
     default: present
   name:
     description:
        - Server group name.
     required: true
   policies:
     description:
        - A list of one or more policy names to associate with the server
          group. The list must contain at least one policy name. The current
          valid policy names are anti-affinity, affinity, soft-anti-affinity
          and soft-affinity.
     required: false
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a server group with 'affinity' policy.
- os_server_group:
    state: present
    auth:
      auth_url: https://api.cloud.catalyst.net.nz:5000/v2.0
      username: admin
      password: admin
      project_name: admin
    name: my_server_group
    policies:
      - affinity

# Delete 'my_server_group' server group.
- os_server_group:
    state: absent
    auth:
      auth_url: https://api.cloud.catalyst.net.nz:5000/v2.0
      username: admin
      password: admin
      project_name: admin
    name: my_server_group
'''

RETURN = '''
id:
    description: Unique UUID.
    returned: success
    type: string
name:
    description: The name of the server group.
    returned: success
    type: string
policies:
    description: A list of one or more policy names of the server group.
    returned: success
    type: list of strings
members:
    description: A list of members in the server group.
    returned: success
    type: list of strings
metadata:
    description: Metadata key and value pairs.
    returned: success
    type: dict
project_id:
    description: The project ID who owns the server group.
    returned: success
    type: string
user_id:
    description: The user ID who owns the server group.
    returned: success
    type: string
'''


def _system_state_change(state, server_group):
    if state == 'present' and not server_group:
        return True
    if state == 'absent' and server_group:
        return True

    return False


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        policies=dict(required=False, type='list'),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        **module_kwargs
    )

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    policies = module.params['policies']
    state = module.params['state']

    try:
        cloud = shade.openstack_cloud(**module.params)
        server_group = cloud.get_server_group(name)

        if module.check_mode:
            module.exit_json(
                changed=_system_state_change(state, server_group)
            )

        changed = False
        if state == 'present':
            if not server_group:
                if not policies:
                    module.fail_json(
                        msg="Parameter 'policies' is required in Server Group "
                            "Create"
                    )
                server_group = cloud.create_server_group(name, policies)
                changed = True

            module.exit_json(
                changed=changed,
                id=server_group['id'],
                server_group=server_group
            )
        if state == 'absent':
            if server_group:
                cloud.delete_server_group(server_group['id'])
                changed = True
            module.exit_json(changed=changed)
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
