#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_role
short_description: Manages user roles on Apache CloudStack based clouds.
description:
  - Create, update, delete user roles.
version_added: "2.3"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the role.
    required: true
  id:
    description:
      - ID of the role.
      - If provided, C(id) is used as key.
    aliases: [ 'uuid' ]
  role_type:
    description:
      - Type of the role.
      - Only considered for creation.
    default: User
    choices: [ 'User', 'DomainAdmin', 'ResourceAdmin', 'Admin' ]
  description:
    description:
      - Description of the role.
  state:
    description:
      - State of the role.
    default: 'present'
    choices: [ 'present', 'absent' ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure an user role is present
- local_action:
    module: cs_role
    name: myrole_user

# Ensure a role having particular ID is named as myrole_user
- local_action:
    module: cs_role
    name: myrole_user
    id: 04589590-ac63-4ffc-93f5-b698b8ac38b6

# Ensure a role is absent
- local_action:
    module: cs_role
    name: myrole_user
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the role.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the role.
  returned: success
  type: string
  sample: myrole
description:
  description: Description of the role.
  returned: success
  type: string
  sample: "This is my role description"
role_type:
  description: Type of the role.
  returned: success
  type: string
  sample: User
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackRole(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackRole, self).__init__(module)
        self.returns = {
            'type': 'role_type',
        }

    def get_role(self):
        uuid = self.module.params.get('uuid')
        if uuid:
            args = {
                'id': uuid,
            }
            roles = self.query_api('listRoles', **args)
            if roles:
                return roles['role'][0]
        else:
            args = {
                'name': self.module.params.get('name'),
            }
            roles = self.query_api('listRoles', **args)
            if roles:
                return roles['role'][0]
        return None

    def present_role(self):
        role = self.get_role()
        if role:
            role = self._update_role(role)
        else:
            role = self._create_role(role)
        return role

    def _create_role(self, role):
        self.result['changed'] = True
        args = {
            'name': self.module.params.get('name'),
            'type': self.module.params.get('role_type'),
            'description': self.module.params.get('description'),
        }
        if not self.module.check_mode:
            res = self.query_api('createRole', **args)
            role = res['role']
        return role

    def _update_role(self, role):
        args = {
            'id': role['id'],
            'name': self.module.params.get('name'),
            'description': self.module.params.get('description'),
        }
        if self.has_changed(args, role):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('updateRole', **args)

                # The API as in 4.9 does not return an updated role yet
                if 'role' not in res:
                    role = self.get_role()
                else:
                    role = res['role']
        return role

    def absent_role(self):
        role = self.get_role()
        if role:
            self.result['changed'] = True
            args = {
                'id': role['id'],
            }
            if not self.module.check_mode:
                self.query_api('deleteRole', **args)
        return role


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        uuid=dict(aliases=['id']),
        name=dict(required=True),
        description=dict(),
        role_type=dict(choices=['User', 'DomainAdmin', 'ResourceAdmin', 'Admin'], default='User'),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_role = AnsibleCloudStackRole(module)
    state = module.params.get('state')
    if state == 'absent':
        role = acs_role.absent_role()
    else:
        role = acs_role.present_role()

    result = acs_role.get_result(role)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
