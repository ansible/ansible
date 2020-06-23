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
module: is_edit_bios
version_added: 1.0
author:
    - WangBaoshan
short_description: set BIOS setup attributes
description:
   - set BIOS setup attributes on Inspur server.
options:
    attribute:
        description:
            - BIOS setup option,Required when I(file_url=None).
        type: str
    value:
        description:
            - BIOS setup option value,Required when I(file_url=None).
        type: str
    file_url:
        description:
            - BIOS option file.attribute must be used with value, 
            - mutually exclusive with fileurl format,"/directory/filename".
        type: str
'''

EXAMPLES = '''
- name: bios test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "set bios setup"
    is_edit_bios:
      attribute: "VMX"
      value: "Disable"
      provider: "{{ ism }}"

  - name: "set bios setup"
    is_edit_bios:
      attribute: "VMX"
      value: "Enable"
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

class BIOS(object):
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
        self.module.params['subcommand'] = 'setbios'
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
        attribute=dict(type='str', required=False),
        value=dict(type='str', required=False),
        file_url=dict(type='str', required=False)
    )
    argument_spec.update(ism_argument_spec)
    bios_obj = BIOS(argument_spec)
    bios_obj.work()
    


if __name__ == '__main__':
    main()
