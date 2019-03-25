#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, IBM Corp
# Author(s): Andreas Nafpliotis <nafpliot@de.ibm.com>
#
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
    - Manage local users on an ESXi host
version_added: "2.2"
author:
- Andreas Nafpliotis (@nafpliot-ibm)
notes:
    - Tested on ESXi 6.0
    - Be sure that the ESXi user used for login, has the appropriate rights to create / delete / edit users
requirements:
    - "python >= 2.6"
    - PyVmomi installed
options:
    local_user_name:
        description:
            - The local user name to be changed.
        required: True
    local_user_password:
        description:
            - The password to be set.
        required: False
    local_user_description:
        description:
            - Description for the user.
        required: False
    state:
        description:
            - Indicate desired state of the user. If the user already exists when C(state=present), the user info is updated
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


class VMwareLocalUserManager(PyVmomi):

    def __init__(self, module):
        super(VMwareLocalUserManager, self).__init__(module)
        self.local_user_name = self.module.params['local_user_name']
        self.local_user_password = self.module.params['local_user_password']
        self.local_user_description = self.module.params['local_user_description']
        self.state = self.module.params['state']

        if self.is_vcenter():
            self.module.fail_json(msg="Failed to get local account manager settings "
                                      "from ESXi server: %s" % self.module.params['hostname'],
                                  details="It seems that %s is a vCenter server instead of an "
                                          "ESXi server" % self.module.params['hostname'])

    def process_state(self):
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
        user_account = self.find_user_account()
        if not user_account:
            return 'absent'
        else:
            return 'present'

    def find_user_account(self):
        searchStr = self.local_user_name
        exactMatch = True
        findUsers = True
        findGroups = False
        user_account = self.content.userDirectory.RetrieveUserGroups(None, searchStr, None, None, exactMatch, findUsers, findGroups)
        return user_account

    def create_account_spec(self):
        account_spec = vim.host.LocalAccountManager.AccountSpecification()
        account_spec.id = self.local_user_name
        account_spec.password = self.local_user_password
        account_spec.description = self.local_user_description
        return account_spec

    def state_create_user(self):
        account_spec = self.create_account_spec()

        try:
            self.content.accountManager.CreateUser(account_spec)
            self.module.exit_json(changed=True)
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)

    def state_update_user(self):
        account_spec = self.create_account_spec()

        try:
            self.content.accountManager.UpdateUser(account_spec)
            self.module.exit_json(changed=True)
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)

    def state_remove_user(self):
        try:
            self.content.accountManager.RemoveUser(self.local_user_name)
            self.module.exit_json(changed=True)
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(local_user_name=dict(required=True, type='str'),
                              local_user_password=dict(type='str', no_log=True),
                              local_user_description=dict(type='str'),
                              state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    vmware_local_user_manager = VMwareLocalUserManager(module)
    vmware_local_user_manager.process_state()


if __name__ == '__main__':
    main()
