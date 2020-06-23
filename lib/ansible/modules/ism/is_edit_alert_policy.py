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
module: is_edit_alert_policy
version_added: 1.0
author:
    - WangBaoshan
short_description: Set alert policy
description:
   - Set alert policy on Inspur server.
options:
    id:
        description:
            - Alert id.
        choices: [1, 2, 3]
        required: true
        type: int
    status:
        description:
            - Alert policy status.
        choices: ['enable', 'disable']
        type: str
    type:
        description:
            - Alert Type.
        choices: ['snmp', 'email', 'snmpdomain']
        type: str
    destination:
        description:
            - Alert destination,when type is snmp,fill in IP;
            - when type is email,fill in user name;
            - when type is snmpdomain,fill in domain.
        type: str
    channel:
        description:
            - LAN Channel.
        choices: ['shared', 'dedicated']
        type: str
'''

EXAMPLES = '''
- name: alert policy test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "set alert policy"
    is_edit_alert_policy:
      id: 1
      status: "enable"
      type: "snmp"
      destination: "100.2.2.2"
      channel: "shared"
      provider: "{{ ism }}"

  - name: "set alert policy"
    is_edit_alert_policy:
      id: 1
      status: "disable"
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

class SNMP(object):
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
        self.module.params['subcommand'] = 'setalertpolicy'
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
        id=dict(type='int', required=True, choices=[1, 2, 3]),
        status=dict(type='str', required=False, choices=['enable', 'disable']),
        type=dict(type='str', required=False, choices=['snmp', 'email', 'snmpdomain']),
        destination=dict(type='str', required=False),
        channel=dict(type='str', required=False, choices=['shared', 'dedicated']),
    )
    argument_spec.update(ism_argument_spec)
    snmp_obj = SNMP(argument_spec)
    snmp_obj.work()
    


if __name__ == '__main__':
    main()
