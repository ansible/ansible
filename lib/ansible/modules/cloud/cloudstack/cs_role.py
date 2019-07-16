#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_role
short_description: Manages user roles on Apache CloudStack based clouds.
description:
  - Create, update, delete user roles.
version_added: '2.3'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the role.
    type: str
    required: true
  id:
    description:
      - ID of the role.
      - If provided, I(id) is used as key.
    type: str
    aliases: [ uuid ]
  role_type:
    description:
      - Type of the role.
      - Only considered for creation.
    type: str
    default: User
    choices: [ User, DomainAdmin, ResourceAdmin, Admin ]
  description:
    description:
      - Description of the role.
    type: str
  state:
    description:
      - State of the role.
    type: str
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Ensure an user role is present
  cs_role:
    name: myrole_user
  delegate_to: localhost

- name: Ensure a role having particular ID is named as myrole_user
  cs_role:
    name: myrole_user
    id: 04589590-ac63-4ffc-93f5-b698b8ac38b6
  delegate_to: localhost

- name: Ensure a role is absent
  cs_role:
    name: myrole_user
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the role.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the role.
  returned: success
  type: str
  sample: myrole
description:
  description: Description of the role.
  returned: success
  type: str
  sample: "This is my role description"
role_type:
  description: Type of the role.
  returned: success
  type: str
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
