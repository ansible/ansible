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
module: is_restore
version_added: 1.0
author:
    - WangBaoshan
short_description: Restore server settings
description:
   -  Restore server settings on Inspur server.
options:
    bak_file:
        description:
            - select backup file or bak folder.
        required: true
        type: str
    item:
        description:
            - select export item.
        choices: ['all', 'network', 'dns', 'service', 'ntp', 'smtp', 'snmptrap', 'ad', 'ldap', 'user','bios']
        required: true
        type: str
'''

EXAMPLES = '''
- name: backup test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: " restore server settings"
    is_restore:
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

class Restore(object):
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
        self.module.params['subcommand'] = 'restore'
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
        bak_file=dict(type='str', required=True),
        item=dict(type='str', required=True, choices=['all', 'network', 'dns', 'service', 'ntp', 'smtp', 'snmptrap', 'ad', 'ldap', 'user','bios']),
    )
    argument_spec.update(ism_argument_spec)
    restore_obj = Restore(argument_spec)
    restore_obj.work()
    


if __name__ == '__main__':
    main()
