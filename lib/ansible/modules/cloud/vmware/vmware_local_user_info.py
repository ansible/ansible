#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_local_user_info
short_description: Gather info about users on the given ESXi host
description:
    - This module can be used to gather information about users present on the given ESXi host system in VMware infrastructure.
    - All variables and VMware object names are case sensitive.
    - User must hold the 'Authorization.ModifyPermissions' privilege to invoke this module.
version_added: "2.9"
author:
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
    - Tested on ESXi 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather info about all Users on given ESXi host system
  vmware_local_user_info:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
  delegate_to: localhost
  register: all_user_info
'''

RETURN = r'''
local_user_info:
    description: metadata about all local users
    returned: always
    type: dict
    sample: [
        {
            "role": "admin",
            "description": "Administrator",
            "group": false,
            "user_id": 0,
            "user_name": "root",
            "shell_access": true
        },
        {
            "role": "admin",
            "description": "DCUI User",
            "group": false,
            "user_id": 100,
            "user_name": "dcui",
            "shell_access": false
        },
    ]
'''

try:
    from pyVmomi import vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VMwareUserInfoManager(PyVmomi):
    """Class to manage local user info"""
    def __init__(self, module):
        super(VMwareUserInfoManager, self).__init__(module)

        if self.is_vcenter():
            self.module.fail_json(
                msg="Failed to get local account manager settings.",
                details="It seems that '%s' is a vCenter server instead of an ESXi server" % self.module.params['hostname']
            )

    def gather_user_info(self):
        """Gather info about local users"""
        results = dict(changed=False, local_user_info=[])
        search_string = ''
        exact_match = False
        find_users = True
        find_groups = False
        user_accounts = self.content.userDirectory.RetrieveUserGroups(
            None, search_string, None, None, exact_match, find_users, find_groups
        )
        if user_accounts:
            for user in user_accounts:
                temp_user = dict()
                temp_user['user_name'] = user.principal
                temp_user['description'] = user.fullName
                temp_user['group'] = user.group
                temp_user['user_id'] = user.id
                temp_user['shell_access'] = user.shellAccess
                temp_user['role'] = None
                try:
                    permissions = self.content.authorizationManager.RetrieveEntityPermissions(
                        entity=self.content.rootFolder,
                        inherited=False
                    )
                except vmodl.fault.ManagedObjectNotFound as not_found:
                    self.module.fail_json(
                        msg="The entity doesn't exist" % to_native(not_found)
                    )
                for permission in permissions:
                    if permission.principal == user.principal:
                        temp_user['role'] = self.get_role_name(permission.roleId, self.content.authorizationManager.roleList)
                        break

                results['local_user_info'].append(temp_user)
        self.module.exit_json(**results)

    @staticmethod
    def get_role_name(role_id, role_list):
        """Get role name from role ID"""
        role_name = None
        # Default role: No access
        if role_id == -5:
            role_name = 'no-access'
        # Default role: Read-only
        elif role_id == -2:
            role_name = 'read-only'
        # Default role: Administrator
        elif role_id == -1:
            role_name = 'admin'
        # Custom roles
        else:
            for role in role_list:
                if role.roleId == role_id:
                    role_name = role.name
                    break
        return role_name


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    vmware_local_user_info = VMwareUserInfoManager(module)
    vmware_local_user_info.gather_user_info()


if __name__ == '__main__':
    main()
