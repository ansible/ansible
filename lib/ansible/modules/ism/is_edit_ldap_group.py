#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (C) 2020 Inspur Inc. All Rights Reserved.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: is_edit_ldap_group
version_added: 1.0
author:
    - WangBaoshan
short_description: Set ldap group information
description:
   - Set ldap group information on Inspur server.
options:
    id:
        description:
            - group id.
        choices: ['1', '2', '3', '4', '5']
        type: str
        required: true
    name:
        description:
            - group name.
        type: str
    base:
        description:
            - Search Base
            - Search base is a string of 4 to 64 alpha-numeric characters;
            - It must start with an alphabetical character;
            - Special Symbols like dot(.), comma(,), hyphen(-), underscore(_), equal-to(=) are allowed.
        type: str
    pri:
        description:
            - group privilege.
        choices: ['administrator', 'user', 'operator', 'oem', 'none']
        type: str
    kvm:
        description:
            - kvm privilege.
        choices: ['enable', 'disable']
        type: str
    vm:
        description:
            - vmedia privilege.
        choices: ['enable', 'disable']
        type: str
'''

EXAMPLES = '''
- name: ldap group test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "edit ldap group information"
    is_edit_ldap_group:
      id: "1"
      name: "wbs"
      base: "cn=manager"
      pri: "administrator"
      kvm: "enable"
      vm: "disable"
      provider: "{{ ism }}"
'''

RETURN = '''

message:
    description: messages returned after module execution
    returned: always
    type: str
state:
    description: status after module execution
    returned: always
    type: str
changed:
    description: check to see if a change was made on the device
    returned: always
    type: false
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ism.ism import ism_argument_spec,get_connection

class LDAP(object):
    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()
        self.results = dict()

    def init_module(self):
        """Init module object"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def run_command(self):
        self.module.params['subcommand'] = 'setldapgroup'
        self.results = get_connection(self.module)

    def show_result(self):
        """Show result"""
        self.module.exit_json(**self.results)

    def work(self):
        """Worker"""
        self.run_command()
        self.show_result()

def main():
    argument_spec = dict(
        id=dict(type='str', required=True,choices=['1', '2', '3', '4', '5']),
        name=dict(type='str', required=False),
        base=dict(type='str', required=False),
        pri=dict(type='str', required=False, choices=['administrator', 'user', 'operator', 'oem', 'none']),
        kvm=dict(type='str', required=False, choices=['enable', 'disable']),
        vm=dict(type='str', required=False, choices=['enable', 'disable']),
    )
    argument_spec.update(ism_argument_spec)
    ldap_obj = LDAP(argument_spec)
    ldap_obj.work()
    


if __name__ == '__main__':
    main()
