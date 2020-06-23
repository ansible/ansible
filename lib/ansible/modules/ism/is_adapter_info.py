#!/usr/bin/python
# coding: utf-8 -*-

# Copyright(C) 2020 Inspur Inc. All Rights Reserved.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: is_adapter_info
version_added: 1.0
author:
    - WangBaoshan
short_description: Get adapter information
description:
   - Get adapter information on Inspur server.
options: {}
'''

EXAMPLES = '''
- name: adapter test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "get adapter information"
    is_adapter_info:
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
import collections

class Adapter(object):
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
        self.module.params['subcommand'] = 'getnic'
        self.results = get_connection(self.module)

    def show_result(self):
        """Show result"""
        nic_result = self.results
        if nic_result.State == "Success":
            nic = nic_result.Message[0]
            sysadapter_len = nic.get('Maximum', 0)
            idx = 0
            sortedRes = collections.OrderedDict()
            if sysadapter_len > 0:
                print("-" * 50)
                nic = nic.get('NIC', [])
                while idx < sysadapter_len:
                    nic_info = nic[idx]
                    sysadapter_info = nic_info.get('Controller')[0]
                sortedRes["State"] = "Success"
                sortedRes["Message"] = sysadapter_info
            else:
                sortedRes["State"] = "Failure"
                sortedRes["Message"] = "cannot get information"
            self.module.exit_json(**sortedRes)
        else:
            self.module.exit_json(**self.results)

    def work(self):
        """Worker"""
        self.run_command()
        self.show_result()

def main():
    argument_spec = dict()
    argument_spec.update(ism_argument_spec)
    adapter_obj = Adapter(argument_spec)
    adapter_obj.work()
    


if __name__ == '__main__':
    main()
