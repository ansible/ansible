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
module: is_edit_ldisk
version_added: 1.0
author:
    - WangBaoshan
short_description: Set logical disk
description:
   - Set logical disk on Inspur server.
options:
    info:
        description:
            - Show controller and ldisk info.
        choices: ['show']
        type: str
    ctrl_id:
        description:
            - Raid controller ID,Required when I(Info=None).
        type: int
    ldisk_id:
        description:
            - logical disk ID,Required when I(Info=None).
        type: int
    option:
        description:
            - Set operation options fo logical disk,
            - LOC is Locate Logical Drive,STL is Stop Locate LogicalDrive,
            - FI is Fast Initialization,SFI is Slow/Full Initialization,
            - SI is Stop Initialization,DEL is Delete LogicalDrive,
            - Required when I(Info=None).
        choices: ['LOC', 'STL', 'FI', 'SFI', 'SI', 'DEL']
        type: str
'''

EXAMPLES = '''
- name: edit ldisk test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "show ldisk information"
    is_edit_ldisk:
      Info: "show"
      provider: "{{ ism }}"
      
  - name: "edit ldisk"
    is_edit_ldisk:
      ctrl_id: 0
      ldisk_id: 1
      option: "LOC"
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

class Disk(object):
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
        self.module.params['subcommand'] = 'setldisk'
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
        info=dict(type='str', required=False, choices=['show']),
        ctrl_id=dict(type='int', required=False),
        ldisk_id=dict(type='int', required=False),
        option=dict(type='str', required=False, choices=['LOC', 'STL', 'FI', 'SFI', 'SI', 'DEL']),
    )
    argument_spec.update(ism_argument_spec)
    disk_obj = Disk(argument_spec)
    disk_obj.work()
    


if __name__ == '__main__':
    main()
