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
module: is_edit_ad
version_added: 1.0
author:
    - WangBaoshan
short_description: Set active directory information
description:
   - Set active directory information on Inspur server.
options:
    enable:
        description: 
            - Active Directory Authentication Status.
        choices: ['enable', 'disable']
        type: str
    name:
        description:
            - Secret Username.
        type: str            
    code:
        description:
            - Secret Password.
        type: str
    timeout:
        description:
            - The Time Out configuration(15-300).
        type: int
    domain:
        description:
            - User Domain Name.
        type: str
    addr1:
        description:
            - Domain Controller Server Address1.
        type: str
    addr2:
        description:
            - Domain Controller Server Address2.
        type: str
    addr3:
        description:
            - Domain Controller Server Address3.
        type: str
'''

EXAMPLES = '''
- name: ad test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "set active directory information"
    is_edit_ad:
      enable: "disable"
      provider: "{{ ism }}"

  - name: "set active directory information"
    is_edit_ad:
      enable: "enable"
      name: "inspur"
      code: "123456"
      timeout: 120
      domain: "inspur.com"
      addr1: "100.2.2.2"
      addr2: "100.2.2.3"
      addr3: "100.2.2.4"
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

class AD(object):
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
        self.module.params['subcommand'] = 'setad'
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
        enable=dict(type='str', required=False, choices=['enable', 'disable']),
        name=dict(type='str', required=False),
        code=dict(type='str', required=False),
        timeout=dict(type='int', required=False),
        domain=dict(type='str', required=False),
        addr1=dict(type='str', required=False),
        addr2=dict(type='str', required=False),
        addr3=dict(type='str', required=False),
    )
    argument_spec.update(ism_argument_spec)
    ad_obj = AD(argument_spec)
    ad_obj.work()
    


if __name__ == '__main__':
    main()
