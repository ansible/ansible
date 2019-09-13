#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
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
module: vmware_local_role_manager
short_description: Manage local roles on an ESXi host
description:
    - This module can be used to manage local roles on an ESXi host.
version_added: 2.5
author:
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
    - Tested on ESXi 6.5
    - Be sure that the ESXi user used for login, has the appropriate rights to create / delete / edit roles
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
  local_role_name:
    description:
    - The local role name to be managed.
    required: True
  local_privilege_ids:
    description:
    - The list of privileges that role needs to have.
    - Please see U(https://docs.vmware.com/en/VMware-vSphere/6.0/com.vmware.vsphere.security.doc/GUID-ED56F3C4-77D0-49E3-88B6-B99B8B437B62.html)
    default: []
  state:
    description:
    - Indicate desired state of the role.
    - If the role already exists when C(state=present), the role info is updated.
    choices: ['present', 'absent']
    default: present
  force_remove:
    description:
    - If set to C(False) then prevents the role from being removed if any permissions are using it.
    default: False
    type: bool
  action:
    description:
    - This parameter is only valid while updating an existing role with privileges.
    - C(add) will add the privileges to the existing privilege list.
    - C(remove) will remove the privileges from the existing privilege list.
    - C(set) will replace the privileges of the existing privileges with user defined list of privileges.
    default: set
    choices: [ add, remove, set ]
    version_added: 2.8
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Add local role to ESXi
  vmware_local_role_manager:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    local_role_name: vmware_qa
    state: present
  delegate_to: localhost

- name: Add local role with privileges to ESXi
  vmware_local_role_manager:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    local_role_name: vmware_qa
    local_privilege_ids: [ 'Folder.Create', 'Folder.Delete']
    state: present
  delegate_to: localhost

- name: Remove local role from ESXi
  vmware_local_role_manager:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    local_role_name: vmware_qa
    state: absent
  delegate_to: localhost

- name: Add a privilege to an existing local role
  vmware_local_role_manager:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    local_role_name: vmware_qa
    local_privilege_ids: [ 'Folder.Create' ]
    action: add
  delegate_to: localhost

- name: Remove a privilege to an existing local role
  vmware_local_role_manager:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    local_role_name: vmware_qa
    local_privilege_ids: [ 'Folder.Create' ]
    action: remove
  delegate_to: localhost

- name: Set a privilege to an existing local role
  vmware_local_role_manager:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    local_role_name: vmware_qa
    local_privilege_ids: [ 'Folder.Create' ]
    action: set
  delegate_to: localhost
'''

RETURN = r'''
role_name:
    description: Name of local role
    returned: always
    type: str
role_id:
    description: ESXi generated local role id
    returned: always
    type: int
privileges:
    description: List of privileges
    returned: always
    type: list
privileges_previous:
    description: List of privileges of role before the update
    returned: on update
    type: list
# NOTE: the following keys are deprecated from 2.11 onwards
local_role_name:
    description: Name of local role
    returned: always
    type: str
new_privileges:
    description: List of privileges
    returned: always
    type: list
old_privileges:
    description: List of privileges of role before the update
    returned: on update
    type: list
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec


class VMwareLocalRoleManager(PyVmomi):
    """Class to manage local roles"""

    def __init__(self, module):
        super(VMwareLocalRoleManager, self).__init__(module)
        self.module = module
        self.params = module.params
        self.role_name = self.params['local_role_name']
        self.state = self.params['state']
        self.priv_ids = self.params['local_privilege_ids']
        self.force = not self.params['force_remove']
        self.current_role = None
        self.action = self.params['action']

        if self.content.authorizationManager is None:
            self.module.fail_json(
                msg="Failed to get local authorization manager settings.",
                details="It seems that '%s' is a vCenter server instead of an ESXi server" % self.params['hostname']
            )

    def process_state(self):
        """Process the state of the local role"""
        local_role_manager_states = {
            'absent': {
                'present': self.state_remove_role,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_update_role,
                'absent': self.state_create_role,
            }
        }
        try:
            local_role_manager_states[self.state][self.check_local_role_manager_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def check_local_role_manager_state(self):
        """Check local roles"""
        auth_role = self.find_authorization_role()
        if auth_role:
            self.current_role = auth_role
            return 'present'
        return 'absent'

    def find_authorization_role(self):
        """Find local role"""
        desired_role = None
        for role in self.content.authorizationManager.roleList:
            if role.name == self.role_name:
                desired_role = role
        return desired_role

    def state_create_role(self):
        """Create local role"""
        role_id = None
        results = dict()
        results['role_name'] = self.role_name
        results['privileges'] = self.priv_ids
        # NOTE: the following code is deprecated from 2.11 onwards
        results['local_role_name'] = self.role_name
        results['new_privileges'] = self.priv_ids

        if self.module.check_mode:
            results['msg'] = "Role would be created"
        else:
            try:
                role_id = self.content.authorizationManager.AddAuthorizationRole(
                    name=self.role_name,
                    privIds=self.priv_ids
                )
                results['role_id'] = role_id
                results['msg'] = "Role created"
            except vim.fault.AlreadyExists as already_exists:
                self.module.fail_json(
                    msg="Failed to create role '%s' as the user specified role name already exists." %
                    self.role_name, details=already_exists.msg
                )
            except vim.fault.InvalidName as invalid_name:
                self.module.fail_json(
                    msg="Failed to create a role %s as the user specified role name is empty" %
                    self.role_name, details=invalid_name.msg
                )
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(
                    msg="Failed to create a role %s as the user specified privileges are unknown" %
                    self.role_name, etails=invalid_argument.msg
                )
        self.module.exit_json(changed=True, result=results)

    def state_remove_role(self):
        """Remove local role"""
        results = dict()
        results['role_name'] = self.role_name
        results['role_id'] = self.current_role.roleId
        # NOTE: the following code is deprecated from 2.11 onwards
        results['local_role_name'] = self.role_name
        if self.module.check_mode:
            results['msg'] = "Role would be deleted"
        else:
            try:
                self.content.authorizationManager.RemoveAuthorizationRole(
                    roleId=self.current_role.roleId,
                    failIfUsed=self.force
                )
                results['msg'] = "Role deleted"
            except vim.fault.NotFound as not_found:
                self.module.fail_json(
                    msg="Failed to remove a role %s as the user specified role name does not exist." %
                    self.role_name, details=not_found.msg
                )
            except vim.fault.RemoveFailed as remove_failed:
                msg = "Failed to remove role '%s' as the user specified role name." % self.role_name
                if self.force:
                    msg += " Use force_remove as True."
                self.module.fail_json(msg=msg, details=remove_failed.msg)
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(
                    msg="Failed to remove a role %s as the user specified role is a system role" %
                    self.role_name, details=invalid_argument.msg
                )
        self.module.exit_json(changed=True, result=results)

    def state_exit_unchanged(self):
        """Don't do anything"""
        results = dict()
        results['role_name'] = self.role_name
        # NOTE: the following code is deprecated from 2.11 onwards
        results['local_role_name'] = self.role_name
        results['msg'] = "Role not present"
        self.module.exit_json(changed=False, result=results)

    def state_update_role(self):
        """Update local role"""
        changed = False
        changed_privileges = []
        results = dict()
        results['role_name'] = self.role_name
        results['role_id'] = self.current_role.roleId
        # NOTE: the following code is deprecated from 2.11 onwards
        results['local_role_name'] = self.role_name

        current_privileges = self.current_role.privilege
        results['privileges'] = current_privileges
        # NOTE: the following code is deprecated from 2.11 onwards
        results['new_privileges'] = current_privileges

        if self.action == 'add':
            # Add to existing privileges
            for priv in self.params['local_privilege_ids']:
                if priv not in current_privileges:
                    changed_privileges.append(priv)
                    changed = True
            if changed:
                changed_privileges.extend(current_privileges)
        elif self.action == 'set':
            # Set given privileges
            # Add system-defined privileges, "System.Anonymous", "System.View", and "System.Read".
            self.params['local_privilege_ids'].extend(['System.Anonymous', 'System.Read', 'System.View'])
            changed_privileges = self.params['local_privilege_ids']
            changes_applied = list(set(current_privileges) ^ set(changed_privileges))
            if changes_applied:
                changed = True
        elif self.action == 'remove':
            changed_privileges = list(current_privileges)
            # Remove given privileges from existing privileges
            for priv in self.params['local_privilege_ids']:
                if priv in current_privileges:
                    changed = True
                    changed_privileges.remove(priv)

        if changed:
            results['privileges'] = changed_privileges
            results['privileges_previous'] = current_privileges
            # NOTE: the following code is deprecated from 2.11 onwards
            results['new_privileges'] = changed_privileges
            results['old_privileges'] = current_privileges
            if self.module.check_mode:
                results['msg'] = "Role privileges would be updated"
            else:
                try:
                    self.content.authorizationManager.UpdateAuthorizationRole(
                        roleId=self.current_role.roleId,
                        newName=self.current_role.name,
                        privIds=changed_privileges
                    )
                    results['msg'] = "Role privileges updated"
                except vim.fault.NotFound as not_found:
                    self.module.fail_json(
                        msg="Failed to update role. Please check privileges provided for update", details=not_found.msg
                    )
                except vim.fault.InvalidName as invalid_name:
                    self.module.fail_json(
                        msg="Failed to update role as role name is empty", details=invalid_name.msg
                    )
                except vim.fault.AlreadyExists as already_exists:
                    self.module.fail_json(
                        msg="Failed to update role", details=already_exists.msg
                    )
                except vmodl.fault.InvalidArgument as invalid_argument:
                    self.module.fail_json(
                        msg="Failed to update role as user specified role is system role which can not be changed",
                        details=invalid_argument.msg
                    )
                except vim.fault.NoPermission as no_permission:
                    self.module.fail_json(
                        msg="Failed to update role as current session doesn't have any privilege to update specified role",
                        details=no_permission.msg
                    )
        else:
            results['msg'] = "Role privileges are properly configured"

        self.module.exit_json(changed=changed, result=results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(local_role_name=dict(required=True, type='str'),
                              local_privilege_ids=dict(default=[], type='list'),
                              force_remove=dict(default=False, type='bool'),
                              action=dict(type='str', default='set', choices=[
                                  'add',
                                  'set',
                                  'remove',
                              ]),
                              state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    vmware_local_role_manager = VMwareLocalRoleManager(module)
    vmware_local_role_manager.process_state()


if __name__ == '__main__':
    main()
