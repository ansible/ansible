#!/usr/bin/python
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_user_group
short_description: Associate OpenStack Identity users and groups
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
    - Add and remove users from groups
options:
   user:
     description:
        - Name or id for the user
     required: true
   group:
     description:
        - Name or id for the group.
     required: true
   state:
     description:
       - Should the user be present or absent in the group
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Add the demo user to the demo group
- os_user_group:
  cloud: mycloud
  user: demo
  group: demo
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _system_state_change(state, in_group):
    if state == 'present' and not in_group:
        return True
    if state == 'absent' and in_group:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        user=dict(required=True),
        group=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    user = module.params['user']
    group = module.params['group']
    state = module.params['state']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        in_group = cloud.is_user_in_group(user, group)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(state, in_group))

        changed = False
        if state == 'present':
            if not in_group:
                cloud.add_user_to_group(user, group)
                changed = True

        elif state == 'absent':
            if in_group:
                cloud.remove_user_from_group(user, group)
                changed = True

        module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
