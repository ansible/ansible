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
module: is_edit_fan
version_added: 1.0
author:
    - WangBaoshan
short_description: Set fan information
description:
   - Set fan information on Inspur server.
options:
    mode:
        description:
            - control mode: Manual or Automatic ,Manual must be used with -s(fanspeedlevel).
        choices: ['Automatic', 'Manual']
        type: str
    id:
        description:
            - fan id 255 is for all fans,0~n.
        type: int
    fan_speed:
        description:
            - fan speed (duty ratio), range in 1 - 100.
        type: int
'''

EXAMPLES = '''
- name: fan test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "set fan information"
    is_edit_fan:
      mode: "Automatic"
      provider: "{{ ism }}"
      
  - name: "set fan information"
    is_edit_fan:
      mode: "Manual"
      id: 1
      fan_speed: 80
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

class Fan(object):
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
        self.module.params['subcommand'] = 'fancontrol'
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
        mode=dict(type='str', required=False, choices=['Automatic', 'Manual']),
        id=dict(type='int', required=False),
        fan_speed=dict(type='int', required=False),
    )
    argument_spec.update(ism_argument_spec)
    fan_obj = Fan(argument_spec)
    fan_obj.work()
    


if __name__ == '__main__':
    main()
