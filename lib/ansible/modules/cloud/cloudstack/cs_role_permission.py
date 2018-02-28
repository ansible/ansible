#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, David Passante (@dpassante)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cs_role_permission
short_description: Manages role permissions on Apache CloudStack based clouds.
description:
    - Create, update and remove CloudStack role permissions.
version_added: '2.6'
author: "David Passante (@dpassante)"
options:
  name:
    description:
      - The API name of the permission.
    required: true
  role:
    description:
      - Name or ID of the role.
    required: true
  permission:
    description:
      - The rule permission, allow or deny. Defaulted to deny.
    choices: [ allow, deny ]
    required: false
    default: deny
  state:
    description:
      - State of the role permission.
    choices: [ present, absent ]
    required: false
    default: present
  description:
    description:
      - The description of the role permission.
    required: false
  parent:
    description:
      - The parent role permission uuid. use 0 to move this rule at the top of the list.
    required: false
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create a role permission
- local_action:
    module: cs_role_permission
    role: "My_Custom_role"
    name: "createVPC"
    permission: "allow"
    description: "My comments"

# Remove a role permission
- local_action:
    module: cs_role_permission
    state: absent
    role: "My_Custom_role"
    name: "createVPC"

# Updete a system role permission
- local_action:
    module: cs_role_permission
    role: "Domain Admin"
    name: "createVPC"
    permission: "deny"

# Updade rules order. move the rule at the top of list
- local_action:
    module: cs_role_permission
    role: "Domain Admin"
    name: "createVPC"
    parent: 0
'''

RETURN = '''
---
id:
  description: The ID of the role permission.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: The API name of the permission.
  returned: success
  type: string
  sample: createVPC
permission:
  description: The permission type of the api name.
  returned: success
  type: string
  sample: allow
roleid:
  description: The ID of the role to which the role permission belongs.
  returned: success
  type: string
  sample: c6f7a5fc-43f8-11e5-a151-feff819cdc7f
description:
  description: The description of the role permission
  returned: success
  type: string
  sample: Deny createVPC for users
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackRolePermission(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackRolePermission, self).__init__(module)
        self.returns = {
            'id': 'id',
            'roleid': 'roleid',
            'rule': 'name',
            'permission': 'permission',
            'description': 'description',
        }
        self.role_permission = None

    def _get_role_id(self):
        role = self.module.params.get('role')
        if not role:
            return None

        res = self.query_api('listRoles')
        roles = res['role']
        if roles:
            for r in roles:
                if role in [r['name'], r['id']]:
                    return r['id']
        self.fail_json(msg="Role '%s' not found" % role)

    def _get_rule(self):
        rule = self.module.params.get('name')

        if self._get_role_perm():
            for permission in self._get_role_perm():
                if rule == permission['rule']:
                    return permission

        return None

    def _get_role_perm(self):
        role_permission = self.role_permission

        args = {
            'roleid': self._get_role_id(),
        }

        rp = self.query_api('listRolePermissions', **args)

        if rp:
            role_permission = rp['rolepermission']

        return role_permission

    def order_permissions(self, parent, rule_id):
        perms = self._get_role_perm()
        rules = []
        parent_id = None if parent != '0' else '0'

        if perms:
            for rule in range(len(perms)):
                rules.append(perms[rule]['id'])

                if not parent_id and parent in perms[rule].values():
                    parent_id = perms[rule]['id']

            self.result['diff']['before'] = ','.join(map(str, rules))

            r_id = rules.pop(rules.index(rule_id))

            if not parent_id:
                self.fail_json(msg="Parent rule '%s' not found" % parent)
            elif parent_id == '0':
                p_id = -1
            else:
                p_id = rules.index(parent_id)

            rules.insert((p_id + 1), r_id)
            rules = ','.join(map(str, rules))

            self.result['diff']['after'] = rules

        return rules

    def create_or_update_role_perm(self):
        required_params = [
            'name',
            'permission',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        role_permission = self._get_rule()

        if not role_permission:
            role_permission = self.create_role_perm()
        else:
            role_permission = self.update_role_perm(role_permission)

        return role_permission

    def create_role_perm(self):
        role_permission = None

        self.result['changed'] = True

        args = {
            'rule': self.module.params.get('name'),
            'description': self.module.params.get('description'),
            'roleid': self._get_role_id(),
            'permission': self.module.params.get('permission'),
        }

        if not self.module.check_mode:
            res = self.query_api('createRolePermission', **args)
            role_permission = res['rolepermission']

        return role_permission

    def update_role_perm(self, role_perm):
        perm_order = None

        if not self.module.params.get('parent'):
            args = {
                'ruleid': role_perm['id'],
                'roleid': role_perm['roleid'],
                'permission': self.module.params.get('permission'),
            }
        else:
            perm_order = self.order_permissions(self.module.params.get('parent'), role_perm['id'])
            args = {
                'roleid': role_perm['roleid'],
                'ruleorder': perm_order,
            }

        if self.has_changed(args, role_perm, only_keys=['permission']) or perm_order:
            self.result['changed'] = True

            if not self.module.check_mode:
                self.query_api('updateRolePermission', **args)
                role_perm = self._get_rule()

        return role_perm

    def remove_role_perm(self):
        role_permission = self._get_rule()

        if role_permission:
            self.result['changed'] = True

            args = {
                'id': role_permission['id'],
            }

            if not self.module.check_mode:
                self.query_api('deleteRolePermission', **args)

        return role_permission


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        role=dict(required=True),
        name=dict(required=True),
        permission=dict(choices=['allow', 'deny'], default='deny'),
        description=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        parent=dict(),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        mutually_exclusive=(
            ['permission', 'parent'],
        ),
        supports_check_mode=True
    )

    acs_role_perm = AnsibleCloudStackRolePermission(module)

    state = module.params.get('state')
    if state in ['absent']:
        role_permission = acs_role_perm.remove_role_perm()
    else:
        role_permission = acs_role_perm.create_or_update_role_perm()

    result = acs_role_perm.get_result(role_permission)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
