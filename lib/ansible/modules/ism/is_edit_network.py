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
module: is_edit_network
version_added: 1.0
author:
    - WangBaoshan
short_description: Set network information
description:
   - Set netowrk information on Inspur server.
options:
    interface_name:
        description:
            - set interface_name.
        choices: ['eth0', 'eth1', 'bond0']
        required: true
        type: str
    lan_enable:
        description:
            - enable or disable this interface. If disable , you cannot use this interface any more.
        choices: ['enable', 'disable']
        required: true
        type: str
'''

EXAMPLES = '''
- name: network test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "set network information"
    is_edit_network:
      interface_name: "eth0"
      lan_enable: "enable"
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

class Network(object):
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
        self.module.params['subcommand'] = 'setnetwork'
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
        interface_name=dict(type='str', required=True, choices=['eth0', 'eth1', 'bond0']),
        lan_enable=dict(type='str', required=True, choices=['enable', 'disable']),
    )
    argument_spec.update(ism_argument_spec)
    net_obj = Network(argument_spec)
    net_obj.work()
    


if __name__ == '__main__':
    main()
