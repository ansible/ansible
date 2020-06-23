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
module: is_edit_smtp
version_added: 1.0
author:
    - WangBaoshan
short_description: Set SMTP information
description:
   - Set SMTP information on Inspur server.
options:
    interface:
        description:
            - LAN Channel,eth0 is shared,eth1 is dedicated.
        choices: ['eth0', 'eth1', 'bond0']
        type: str
        required: true
    email:
        description:
            - Sender email
        type: str
    primary_status:
        description:
            - primary SMTP Support.
        choices: ['enable', 'disable']
        type: str
    primary_ip:
        description:
            - primary SMTP server IP
        type: str
    primary_name:
        description:
            - primary SMTP server name
        type: str
    primary_port:
        description:
            - primary SMTP server port,The Identification for retry count configuration(1-65535)
        type: int
    primary_auth:
        description:
            - primary SMTP server authentication
        choices: ['enable', 'disable']
        type: str
    primary_username:
        description:
            - primary SMTP server Username,lenth be 4 to 64 bits,must start with letters and cannot contain ','(comma) ':'(colon) ' '(space) ';'(semicolon) '\\'(backslash)
        type: str
    primary_password:
        description:
            - primary SMTP server Password,lenth be 4 to 64 bits,cannot contain ' '(space),
            - Required when I(primary_auth=enable).
        type: str
    secondary_status:
        description:
            - secondary SMTP Support.
        choices: ['enable', 'disable']
        type: str
    secondary_ip:
        description:
            - secondary SMTP server IP
        type: str
    secondary_name:
        description:
            - secondary SMTP server name
        type: str
    secondary_port:
        description:
            - secondary SMTP server port,The Identification for retry count configuration(1-65535)
        type: int
    secondary_auth:
        description:
            - secondary SMTP server authentication
        choices: ['enable', 'disable']
        type: str
    secondary_username:
        description:
            - secondary SMTP server Username,lenth be 4 to 64 bits,must start with letters and cannot contain ','(comma) ':'(colon) ' '(space) ';'(semicolon) '\\'(backslash)
        type: str
    secondary_password:
        description:
            - secondary SMTP server Password,lenth be 4 to 64 bits,cannot contain ' '(space),
            - Required when I(secondary_auth=enable).
        type: str
'''

EXAMPLES = '''
- name: smtp test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "set smtp information"
    is_edit_smtp:
      interface: "eth0"
      email: "inspur@Inspur.com"
      primary_status: "enable"
      primary_ip: "100.2.2.2"
      primary_name: "inspur"
      primary_auth: "disable"
      provider: "{{ ism }}"

  - name: "set smtp information"
    is_edit_smtp:
      interface: "eth0"
      email: "inspur@Inspur.com"
      primary_status: "enable"
      primary_ip: "100.2.2.2"
      primary_name: "inspur"
      primary_auth: "enable"
      primary_username: "test"
      primary_password: "123456"
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

class SMTP(object):
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
        self.module.params['subcommand'] = 'setsmtp'
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
        interface=dict(type='str', required=True, choices=['eth0', 'eth1','bond0']),
        email=dict(type='str', required=False),
        primary_status=dict(type='str', required=False, choices=['enable', 'disable']),
        primary_ip=dict(type='str', required=False),
        primary_name=dict(type='str', required=False),
        primary_port=dict(type='int', required=False),
        primary_auth=dict(type='str', required=False, choices=['enable', 'disable']),
        primary_username=dict(type='str', required=False),
        primary_password=dict(type='str', required=False),
        secondary_status=dict(type='str', required=False, choices=['enable', 'disable']),
        secondary_ip=dict(type='str', required=False),
        secondary_name=dict(type='str', required=False),
        secondary_port=dict(type='int', required=False),
        secondary_auth=dict(type='str', required=False, choices=['enable', 'disable']),
        secondary_username=dict(type='str', required=False),
        secondary_password=dict(type='str', required=False),

    )
    argument_spec.update(ism_argument_spec)
    smtp_obj = SMTP(argument_spec)
    smtp_obj.work()
    


if __name__ == '__main__':
    main()
