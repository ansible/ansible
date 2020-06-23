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
module: is_edit_ncsi
version_added: 1.0
author:
    - WangBaoshan
short_description: Get ncsi information
description:
   - Get ncsi information on Inspur server.
options:
    nic_type:
        description:
            - nic type.
        choices: ['PHY', 'OCP', 'PCIE', 'auto']
        type: str
    mode:
        description:
            - NCSI mode, auto-Auto Failover,  manual-Manual Switch.
        choices: ['auto', 'manual']
        type: str
    interface_name:
        description:
            - interface name, for example eth0.
        type: str
    channel_number:
        description:
            - channel number, like 0,1,2...
        type: int
'''

EXAMPLES = '''
- name: ncsi test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "set ncsi information"
    is_ncsi_info:
      mode: "manual"
      nic_type: "PCIE"
      interface_name: "eth0"
      channel_number: 1
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

class NCSI(object):
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
        self.module.params['subcommand'] = 'setncsi'
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
        nic_type=dict(type='str', required=False, choices=['PHY', 'OCP', 'PCIE', 'auto']),
        mode=dict(type='str', required=False, choices=['auto', 'manual']),
        interface_name=dict(type='str', required=False),
        channel_number=dict(type='int', required=False),
    )
    argument_spec.update(ism_argument_spec)
    ncsi_obj = NCSI(argument_spec)
    ncsi_obj.work()
    


if __name__ == '__main__':
    main()
