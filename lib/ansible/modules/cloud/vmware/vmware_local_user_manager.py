#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, IBM Corp
# Author(s): Andreas Nafpliotis <nafpliot@de.ibm.com>
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
module: vmware_local_user_manager
short_description: Manage local users on an ESXi host
description:
    - Manage local users on an ESXi host.
version_added: "2.2"
author:
- Andreas Nafpliotis (@nafpliot-ibm)
- Christian Kotte (@ckotte)
notes:
    - Tested on ESXi 6.0
    - Be sure that the ESXi user used for login, has the appropriate rights to create, delete, or edit users
requirements:
    - "python >= 2.6"
    - PyVmomi installed
options:
    local_user_name:
        description:
            - The local user name to be changed.
        required: True
        type: str
    local_user_password:
        description:
            - The password to be set.
        required: False
        type: str
    local_user_description:
        description:
            - Description for the user.
        required: False
        type: str
    local_user_role:
        description:
            - Role to assign to the user account.
            - You can specify default or custom roles.
            - The role names can be found with C(vmware_local_role_facts) module.
            - The most important default roles are C(no-access), C(read-only), and C(admin).
        required: False
        aliases: [role]
        type: str
        version_added: 2.8
    propagate:
        description:
            - Propagate permissions to all children.
        type: bool
        default: True
        version_added: 2.8
    update_password:
        description:
            - Update the password of an existing user.
        type: bool
        required: False
        version_added: 2.8
    state:
        description:
            - Indicate desired state of the user. If the user already exists when C(state=present), the user info is updated.
        type: str
        choices: ['present', 'absent']
        default: present
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Add local user to ESXi
  vmware_local_user_manager:
    hostname: esxi_hostname
    username: root
    password: vmware
    local_user_name: foo
  delegate_to: localhost
'''

RETURN = '''# '''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VMwareLocalUserManager(PyVmomi):
    """Class to manage local user accounts"""

    def __init__(self, module):
        super(VMwareLocalUserManager, self).__init__(module)
        self.local_user_name = self.module.params['local_user_name']
        self.local_user_password = self.module.params['local_user_password']
        self.local_user_description = self.module.params['local_user_description']
        self.local_user_role = self.module.params['local_user_role']
        self.propagate = self.module.params['propagate']
        self.update_password = self.module.params['update_password']
        self.state = self.module.params['state']
        self.user_account = None

        if self.is_vcenter():
            self.module.fail_json(
                msg="Failed to get local account manager settings.",
                details="It seems that '%s' is a vCenter server instead of an ESXi server" % self.module.params['hostname']
            )

    def process_state(self):
        """Process the state of the account"""
        try:
            local_account_manager_states = {
                'absent': {
                    'present': self.state_remove_user,
                    'absent': self.state_exit_unchanged,
                },
                'present': {
                    'present': self.state_update_user,
                    'absent': self.state_create_user,
                }
            }

            local_account_manager_states[self.state][self.check_local_user_manager_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def check_local_user_manager_state(self):
        """Check user account"""
        user_account = self.find_user_account()
        if user_account:
            self.user_account = user_account[0]
            return 'present'
        return 'absent'

    def find_user_account(self):
        """Try to find the user account"""
        search_string = self.local_user_name
        exact_match = True
        find_users = True
        find_groups = False
        user_account = self.content.userDirectory.RetrieveUserGroups(
            None, search_string, None, None, exact_match, find_users, find_groups
        )
        return user_account

    def create_account_spec(self):
        """Create account specification"""
        account_spec = vim.host.LocalAccountManager.AccountSpecification()
        account_spec.id = self.local_user_name
        account_spec.password = self.local_user_password
        account_spec.description = self.local_user_description
        return account_spec

    def set_permissions(self, user, role_id):
        """Set specified permissions on an entity"""
        permission_spec = vim.AuthorizationManager.Permission()
        permission_spec.principal = user
        permission_spec.group = False
        permission_spec.roleId = role_id
        permission_spec.propagate = self.propagate
        try:
            self.content.authorizationManager.SetEntityPermissions(
                entity=self.content.rootFolder,
                permission=[permission_spec]
            )
        except vim.fault.UserNotFound as user_not_found:
            self.module.fail_json(msg="The specified user or group does not exist : %s" % to_native(user_not_found))
        except vim.fault.NotFound as not_found:
            self.module.fail_json(msg="The role ID isn't valid : %s" % to_native(not_found))
        except vim.fault.AuthMinimumAdminPermission as admin_permission:
            self.module.fail_json(
                msg="This change would leave the system with no Administrator permission on the root node, "
                "or it would grant further permission to a user or group who already has Administrator permission "
                "on the root node : %s" % to_native(admin_permission)
            )
        except vmodl.fault.ManagedObjectNotFound as object_not_found:
            self.module.fail_json(msg="The specified entity doesn't exist : %s" % to_native(object_not_found))
        except vmodl.fault.InvalidArgument as invalid_argument:
            self.module.fail_json(
                msg="The new role ID is the View or Anonymous role, "
                "or the entity does not support assigning permissions : %s" % to_native(invalid_argument)
            )
        except vim.fault.NoPermission as no_permission:
            self.module.fail_json(msg="No priviledge to set permission : %s" % to_native(no_permission))

    @staticmethod
    def get_role_id(role_name, role_list):
        """Get role ID from role name"""
        role_id = None
        # Default roles
        if role_name == 'no-access':
            role_id = -5
        elif role_name == 'read-only':
            role_id = -2
        elif role_name == 'admin':
            role_id = -1
        # Custom roles
        else:
            for role in role_list:
                if role.name == role_name:
                    role_id = role.roleId
                    break
        return role_id

    @staticmethod
    def get_role_name(role_id, role_list):
        """Get role name from role ID"""
        role_name = None
        # Default roles
        if role_id == -5:
            role_name = 'no-access'
        elif role_id == -2:
            role_name = 'read-only'
        elif role_id == -1:
            role_name = 'admin'
        # Custom roles
        else:
            for role in role_list:
                if role.roleId == role_id:
                    role_name = role.name
                    break
        return role_name

    def state_create_user(self):
        """Create the user account"""
        results = dict()
        results['user_name'] = self.local_user_name
        results['description'] = self.local_user_description
        results['role'] = self.local_user_role
        if self.module.check_mode:
            results['msg'] = "User account would be created"
        else:
            account_spec = self.create_account_spec()
            try:
                self.content.accountManager.CreateUser(account_spec)
            except vim.fault.AlreadyExists as already_exists:
                self.module.fail_json(
                    msg="The specified local user account already exists : %s" % to_native(already_exists)
                )
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(
                    msg="The user name or password has an invalid format : %s" % to_native(invalid_argument)
                )
            if self.local_user_role:
                role_id = self.get_role_id(self.local_user_role, self.content.authorizationManager.roleList)
                if not role_id:
                    self.module.fail_json(msg="The role '%s' could not be found!" % self.local_user_role)
                self.set_permissions(self.local_user_name, role_id)
            results['msg'] = "User account created"
        self.module.exit_json(changed=True, result=results)

    def state_update_user(self):
        """Update the user account"""
        changed = False
        results = dict()
        results['user_name'] = self.local_user_name
        results['description'] = self.local_user_description
        results['role'] = self.local_user_role

        # Check description
        if self.user_account.fullName != self.local_user_description:
            results['description_previous'] = self.user_account.fullName
            changed = True

        # Check permissions
        if self.local_user_role:
            role_id = self.get_role_id(self.local_user_role, self.content.authorizationManager.roleList)
            try:
                permissions = self.content.authorizationManager.RetrieveEntityPermissions(
                    entity=self.content.rootFolder,
                    inherited=False
                )
            except vmodl.fault.ManagedObjectNotFound as not_found:
                self.module.fail_json(
                    msg="The entity doesn't exist : %s" % to_native(not_found)
                )
            for permission in permissions:
                if permission.principal == self.local_user_name and permission.roleId != role_id:
                    results['role_previous'] = self.get_role_name(
                        permission.roleId,
                        self.content.authorizationManager.roleList
                    )
                    changed = True
                    break

        # Update password
        if self.update_password and self.local_user_password:
            changed = True

        if changed:
            if self.module.check_mode:
                results['msg'] = "User account would be updated"
            else:
                account_spec = self.create_account_spec()
                try:
                    self.content.accountManager.UpdateUser(account_spec)
                except vim.fault.UserNotFound as user_not_found:
                    self.module.fail_json(msg="The local user account wasn't found : %s" % to_native(user_not_found))
                except vim.fault.AlreadyExists as already_exists:
                    self.module.fail_json(
                        msg="The specified local user account already exists : %s" % to_native(already_exists)
                    )
                except vmodl.fault.InvalidArgument as invalid_argument:
                    self.module.fail_json(
                        msg="The new password or description has an invalid format : %s" % to_native(invalid_argument)
                    )
                if self.local_user_role:
                    role_id = self.get_role_id(self.local_user_role, self.content.authorizationManager.roleList)
                    self.set_permissions(self.local_user_name, role_id)
                results['msg'] = "User account updated"
        else:
            results['msg'] = "User account is properly configured"
        self.module.exit_json(changed=changed, result=results)

    def state_remove_user(self):
        """Remove the user account"""
        results = dict()
        results['user_name'] = self.local_user_name
        results['description'] = self.local_user_description
        results['role'] = self.local_user_role
        if self.module.check_mode:
            results['msg'] = "User account would be removed"
        else:
            try:
                self.content.accountManager.RemoveUser(self.local_user_name)
                results['msg'] = "User account removed"
            except vim.fault.UserNotFound as user_not_found:
                self.module.fail_json(msg="The specified user account doesn't exist : %s" % to_native(user_not_found))
            except vmodl.fault.SecurityError as security_error:
                self.module.fail_json(
                    msg="Failed to remove the user account, this can be due to either of following : "
                    "1. Trying to remove the last local user with DCUI access, "
                    "2. Trying to remove the last local user with full administrative privileges, "
                    "3. The system has encountered an error while trying to remove user's permissions, "
                    "4. The account cannot be removed due to permission issues : %s" % to_native(security_error)
                )
        self.module.exit_json(changed=True, result=results)

    def state_exit_unchanged(self):
        """Don't do anything"""
        results = dict()
        results['user_name'] = self.local_user_name
        results['description'] = self.local_user_description
        results['role'] = self.local_user_role
        results['msg'] = "User account already deleted"
        self.module.exit_json(changed=False, result=results)


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(local_user_name=dict(required=True, type='str'),
                              local_user_password=dict(required=False, type='str', no_log=True),
                              local_user_description=dict(required=False, type='str'),
                              local_user_role=dict(required=False, type='str', aliases=['role']),
                              propagate=dict(type='bool', default=True),
                              update_password=dict(type='bool', default=False),
                              state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ['update_password', True, ['local_user_password']],
        ],
        supports_check_mode=True
    )

    vmware_local_user_manager = VMwareLocalUserManager(module)
    vmware_local_user_manager.process_state()


if __name__ == '__main__':
    main()
