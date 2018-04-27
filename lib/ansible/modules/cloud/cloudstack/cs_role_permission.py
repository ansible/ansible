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
    - Managing role permissions only supported in CloudStack >= 4.9.
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
    default: deny
  state:
    description:
      - State of the role permission.
    choices: [ present, absent ]
    default: present
  description:
    description:
      - The description of the role permission.
  parent:
    description:
      - The parent role permission uuid. use 0 to move this rule at the top of the list.
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

# Update a system role permission
- local_action:
    module: cs_role_permission
    role: "Domain Admin"
    name: "createVPC"
    permission: "deny"

# Update rules order. Move the rule at the top of list
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
role_id:
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

from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackRolePermission(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackRolePermission, self).__init__(module)
        cloudstack_min_version = LooseVersion('4.9.2')

        self.returns = {
            'id': 'id',
            'roleid': 'role_id',
            'rule': 'name',
            'permission': 'permission',
            'description': 'description',
        }
        self.role_permission = None

        self.cloudstack_version = self._cloudstack_ver()

        if self.cloudstack_version < cloudstack_min_version:
            self.fail_json(msg="This module requires CloudStack >= %s." % cloudstack_min_version)

    def _cloudstack_ver(self):
        capabilities = self.get_capabilities()
        return LooseVersion(capabilities['cloudstackversion'])

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

    def _get_role_perm(self):
        role_permission = self.role_permission

        args = {
            'roleid': self._get_role_id(),
        }

        rp = self.query_api('listRolePermissions', **args)

        if rp:
            role_permission = rp['rolepermission']

        return role_permission

    def _get_rule(self, rule=None):
        if not rule:
            rule = self.module.params.get('name')

        if self._get_role_perm():
            for _rule in self._get_role_perm():
                if rule == _rule['rule'] or rule == _rule['id']:
                    return _rule

        return None

    def _get_rule_order(self):
        perms = self._get_role_perm()
        rules = []

        if perms:
            for i, rule in enumerate(perms):
                rules.append(rule['id'])

        return rules

    def replace_rule(self):
        old_rule = self._get_rule()

        if old_rule:
            rules_order = self._get_rule_order()
            old_pos = rules_order.index(old_rule['id'])

            self.remove_role_perm()

            new_rule = self.create_role_perm()

            if new_rule:
                perm_order = self.order_permissions(int(old_pos - 1), new_rule['id'])

                return perm_order

        return None

    def order_permissions(self, parent, rule_id):
        rules = self._get_rule_order()

        if isinstance(parent, int):
            parent_pos = parent
        elif parent == '0':
            parent_pos = -1
        else:
            parent_rule = self._get_rule(parent)
            if not parent_rule:
                self.fail_json(msg="Parent rule '%s' not found" % parent)

            parent_pos = rules.index(parent_rule['id'])

        r_id = rules.pop(rules.index(rule_id))

        rules.insert((parent_pos + 1), r_id)
        rules = ','.join(map(str, rules))

        return rules

    def create_or_update_role_perm(self):
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

            if self.has_changed(args, role_perm, only_keys=['permission']):
                self.result['changed'] = True

                if not self.module.check_mode:
                    if self.cloudstack_version >= LooseVersion('4.11.0'):
                        self.query_api('updateRolePermission', **args)
                        role_perm = self._get_rule()
                    else:
                        perm_order = self.replace_rule()
        else:
            perm_order = self.order_permissions(self.module.params.get('parent'), role_perm['id'])

        if perm_order:
            args = {
                'roleid': role_perm['roleid'],
                'ruleorder': perm_order,
            }

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
