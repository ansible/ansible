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
    from shade import meta
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_user_group
short_description: Associate OpenStack Identity users and groups
extends_documentation_fragment: openstack
version_added: "2.0"
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
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Add the demo user to the demo group
- os_user_group: user=demo group=demo
'''


def main():

    argument_spec = openstack_full_argument_spec(
    argument_spec = dict(
        user=dict(required=True),
        group=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
    ))

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    user = module.params.pop('user')
    group = module.params.pop('group')
    state = module.params.pop('state')

    try:
        cloud = shade.openstack_cloud(**module.params)

        in_group = cloud.is_user_in_group(user, group)

        if state == 'present':

            if in_group:
                changed = False
            else:
                cloud.add_user_to_group(
                    user_name_or_id=user, group_name_or_id=group)
                changed = True
        elif state == 'absent':
            if in_group:
                cloud.remove_user_from_group(
                    user_name_or_id=user, group_name_or_id=group)
                changed=True
            else:
                changed=False
        module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *


if __name__ == '__main__':
    main()
