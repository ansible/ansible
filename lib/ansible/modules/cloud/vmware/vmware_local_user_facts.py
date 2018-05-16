#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_local_user_facts
short_description: Gather facts about users on the given ESXi host
description:
    - This module can be used to gather facts about users present on the given ESXi host system in VMware infrastructure.
    - All variables and VMware object names are case sensitive.
    - User must hold the 'Authorization.ModifyPermissions' privilege to invoke this module.
version_added: "2.6"
author:
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
notes:
    - Tested on ESXi 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather facts about all Users on given ESXi host system
  vmware_local_user_facts:
    hostname: esxi_hostname
    username: root
    password: vmware
  register: all_user_facts
'''

RETURN = r'''
local_user_facts:
    description: metadata about all local users
    returned: always
    type: dict
    sample: [
        {
            "full_name": "Administrator",
            "principal": "root",
            "user_group": false,
            "user_id": 0,
            "user_shell_access": true
        },
        {
            "full_name": "DCUI User",
            "principal": "dcui",
            "user_group": false,
            "user_id": 100,
            "user_shell_access": false
        },
    ]
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec


class VMwareUserFactsManager(PyVmomi):
    def __init__(self, module):
        super(VMwareUserFactsManager, self).__init__(module)

        if self.is_vcenter():
            self.module.fail_json(msg="Failed to get local authorization manager settings.",
                                  details="It seems that %s is a vCenter server "
                                          "instead of an ESXi server." % self.params['hostname'])

    def gather_user_facts(self):
        """
        Function to gather facts about local users

        """
        results = dict(changed=False, local_user_facts=[])
        user_account = self.content.userDirectory.RetrieveUserGroups(None, '', None, None, False, True, False)
        if user_account:
            for user in user_account:
                temp_user = dict(principal=user.principal,
                                 full_name=user.fullName,
                                 user_group=user.group,
                                 user_id=user.id,
                                 user_shell_access=user.shellAccess)
                results['local_user_facts'].append(temp_user)
        self.module.exit_json(**results)


def main():
    argument_spec = vmware_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec)
    vmware_local_user_facts = VMwareUserFactsManager(module)
    vmware_local_user_facts.gather_user_facts()

if __name__ == '__main__':
    main()
