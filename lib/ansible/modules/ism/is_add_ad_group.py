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
module: is_add_ad_group
version_added: 1.0
author:
    - WangBaoshan
short_description: Add active directory group information
description:
   - Add active directory group information on Inspur server.
options:
    name:
        description:
            - group name.
        type: str
        required: true
    domain:
        description:
            - group domain.
        type: str
        required: true
    pri:
        description:
            - group privilege.
        choices: ['administrator', 'user', 'operator', 'oem', 'none']
        type: str
        required: true
    kvm:
        description:
            - kvm privilege.
        choices: ['enable', 'disable']
        type: str
        required: true
    vm:
        description:
            - vmedia privilege.
        choices: ['enable', 'disable']
        type: str
        required: true
'''

EXAMPLES = '''
- name: ad group test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "add active directory group information"
    is_add_ad_group:
      name: "wbs"
      domain: "inspur.com"
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
        self.module.params['subcommand'] = 'addadgroup'
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
        name=dict(type='str', required=True),
        domain=dict(type='str', required=True),
        pri=dict(type='str', required=True, choices=['administrator', 'user', 'operator', 'oem', 'none']),
        kvm=dict(type='str', required=True, choices=['enable', 'disable']),
        vm=dict(type='str', required=True, choices=['enable', 'disable']),
    )
    argument_spec.update(ism_argument_spec)
    ad_obj = AD(argument_spec)
    ad_obj.work()
    


if __name__ == '__main__':
    main()
