#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Derek Rushing <derek.rushing@geekops.com>
# Copyright: (c) 2018, VMware, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_object_role_permission
short_description: Manage local roles on an ESXi host
description: This module can be used to manage object permissions on the given host.
version_added: 2.8
author:
- Derek Rushing (@kryptsi)
- Joseph Andreatta (@vmwjoseph)
notes:
    - Tested on ESXi 6.5, vSphere 6.7
    - The ESXi login user must have the appropriate rights to administer permissions.
    - Permissions for a distributed switch must be defined and managed on either the datacenter or a folder containing the switch.
requirements:
    - "python >= 2.7"
    - PyVmomi
options:
  role:
    description:
    - The role to be assigned permission.
    required: True
    type: str
  principal:
    description:
    - The user to be assigned permission.
    - Required if C(group) is not specified.
    type: str
  group:
    description:
    - The group to be assigned permission.
    - Required if C(principal) is not specified.
    type: str
  object_name:
    description:
    - The object name to assigned permission.
    type: str
    required: True
  object_type:
    description:
    - The object type being targeted.
    default: 'Folder'
    choices: ['Folder', 'VirtualMachine', 'Datacenter', 'ResourcePool',
              'Datastore', 'Network', 'HostSystem', 'ComputeResource',
              'ClusterComputeResource', 'DistributedVirtualSwitch']
    type: str
  recursive:
    description:
    - Should the permissions be recursively applied.
    default: True
    type: bool
  state:
    description:
    - Indicate desired state of the object's permission.
    - When C(state=present), the permission will be added if it doesn't already exist.
    - When C(state=absent), the permission is removed if it exists.
    choices: ['present', 'absent']
    default: present
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Assign user to VM folder
  vmware_object_role_permission:
    role: Admin
    principal: user_bob
    object_name: services
    state: present
  delegate_to: localhost

- name: Remove user from VM folder
  vmware_object_role_permission:
    role: Admin
    principal: user_bob
    object_name: services
    state: absent
  delegate_to: localhost

- name: Assign finance group to VM folder
  vmware_object_role_permission:
    role: Limited Users
    group: finance
    object_name: Accounts
    state: present
  delegate_to: localhost

- name: Assign view_user Read Only permission at root folder
  vmware_object_role_permission:
    role: ReadOnly
    principal: view_user
    object_name: rootFolder
    state: present
  delegate_to: localhost
'''

RETURN = r'''
changed:
    description: whether or not a change was made to the object's role
    returned: always
    type: bool
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, find_obj


class VMwareObjectRolePermission(PyVmomi):
    def __init__(self, module):
        super(VMwareObjectRolePermission, self).__init__(module)
        self.module = module
        self.params = module.params
        self.is_group = False

        if self.params.get('principal', None) is not None:
            self.applied_to = self.params['principal']
        elif self.params.get('group', None) is not None:
            self.applied_to = self.params['group']
            self.is_group = True

        self.get_role()
        self.get_object()
        self.get_perms()
        self.perm = self.setup_permission()
        self.state = self.params['state']

    def get_perms(self):
        self.current_perms = self.content.authorizationManager.RetrieveEntityPermissions(self.current_obj, False)

    def same_permission(self, perm_one, perm_two):
        return perm_one.principal.lower() == perm_two.principal.lower() \
            and perm_one.roleId == perm_two.roleId

    def get_state(self):
        for perm in self.current_perms:
            if self.same_permission(self.perm, perm):
                return 'present'
        return 'absent'

    def process_state(self):
        local_permission_states = {
            'absent': {
                'present': self.remove_permission,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_exit_unchanged,
                'absent': self.add_permission,
            }
        }
        try:
            local_permission_states[self.state][self.get_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def setup_permission(self):
        perm = vim.AuthorizationManager.Permission()
        perm.entity = self.current_obj
        perm.group = self.is_group
        perm.principal = self.applied_to
        perm.roleId = self.role.roleId
        perm.propagate = self.params['recursive']
        return perm

    def add_permission(self):
        if not self.module.check_mode:
            self.content.authorizationManager.SetEntityPermissions(self.current_obj, [self.perm])
        self.module.exit_json(changed=True)

    def remove_permission(self):
        if not self.module.check_mode:
            self.content.authorizationManager.RemoveEntityPermission(self.current_obj, self.applied_to, self.is_group)
        self.module.exit_json(changed=True)

    def get_role(self):
        for role in self.content.authorizationManager.roleList:
            if role.name == self.params['role']:
                self.role = role
                return
        self.module.fail_json(msg="Specified role (%s) was not found" % self.params['role'])

    def get_object(self):
        # find_obj doesn't include rootFolder
        if self.params['object_type'] == 'Folder' and self.params['object_name'] == 'rootFolder':
            self.current_obj = self.content.rootFolder
            return
        try:
            object_type = getattr(vim, self.params['object_type'])
        except AttributeError:
            self.module.fail_json(msg="Object type %s is not valid." % self.params['object_type'])
        self.current_obj = find_obj(content=self.content,
                                    vimtype=[getattr(vim, self.params['object_type'])],
                                    name=self.params['object_name'])

        if self.current_obj is None:
            self.module.fail_json(
                msg="Specified object %s of type %s was not found."
                % (self.params['object_name'], self.params['object_type'])
            )
        if self.params['object_type'] == 'DistributedVirtualSwitch':
            msg = "You are applying permissions to a Distributed vSwitch. " \
                  "This will probably fail, since Distributed vSwitches inherits permissions " \
                  "from the datacenter or a folder level. " \
                  "Define permissions on the datacenter or the folder containing the switch."
            self.module.warn(msg)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            role=dict(required=True, type='str'),
            object_name=dict(required=True, type='str'),
            object_type=dict(
                type='str',
                default='Folder',
                choices=[
                    'Folder',
                    'VirtualMachine',
                    'Datacenter',
                    'ResourcePool',
                    'Datastore',
                    'Network',
                    'HostSystem',
                    'ComputeResource',
                    'ClusterComputeResource',
                    'DistributedVirtualSwitch',
                ],
            ),
            principal=dict(type='str'),
            group=dict(type='str'),
            recursive=dict(type='bool', default=True),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['principal', 'group']],
        required_one_of=[['principal', 'group']],
    )

    vmware_object_permission = VMwareObjectRolePermission(module)
    vmware_object_permission.process_state()


if __name__ == '__main__':
    main()
