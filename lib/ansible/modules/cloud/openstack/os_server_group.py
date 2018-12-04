#!/usr/bin/python

# Copyright (c) 2016 Catalyst IT Limited
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Create a server group with 'affinity' policy.
- os_server_group:
    state: present
    auth:
      auth_url: https://identity.example.com
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
      auth_url: https://identity.example.com
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
    type: list
members:
    description: A list of members in the server group.
    returned: success
    type: list
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


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

    name = module.params['name']
    policies = module.params['policies']
    state = module.params['state']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
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
    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
