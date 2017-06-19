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

ANSIBLE_METADATA = {'metadata_version': '1.0',
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
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Add the demo user to the demo group
- os_user_group:
  cloud: mycloud
  user: demo
  group: demo
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


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

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    user = module.params['user']
    group = module.params['group']
    state = module.params['state']

    try:
        cloud = shade.operator_cloud(**module.params)

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
                changed=True

        module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
