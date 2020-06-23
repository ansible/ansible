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
module: is_edit_log_setting
version_added: 1.0
author:
    - WangBaoshan
short_description: Edit bmc system and audit log setting
description:
   - Edit bmc system and audit log setting on Inspur server.
options:
    status:
        description:
            - System Log Status.
        choices: ['enable', 'disable']
        type: str
    type:
        description:
            - System log type.
        choices: ['local', 'remote', 'both']
        type: str
    file_size:
        description:
            - File Size(3-65535bytes), set when type is local(default 30000).
        type: int
    audit_status:
        description:
            - Audit Log Status.
        choices: ['enable', 'disable']
        type: int
    audit_type:
        description:
            - Audit log type.
        choices: ['local', 'remote', 'both']
        type: int
    rotate_count:
        description:
            - Rotate Count, set when type is local, 0-delete old files(default), 1-bak old files.
        choices: [0, 1]
        type: int
    server_addr:
        description:
            - Server Address, set when type is remote.
        type: str
    server_port:
        description:
            - Server Port(0-65535), set when type is remote.
        type: int
    protocol_type:
        description:
            - Protocol Type, set when type is remote.
        choices: ['UDP', 'TCP']
        type: str
'''

EXAMPLES = '''
- name: edit log setting test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "edit bmc system log setting"
    is_edit_log_setting:
      status: "enable"
      type: "both"
      provider: "{{ ism }}"
    
  - name: "edit bmc audit log setting"
    is_edit_log_setting:
      audit_status: "enable"
      audit_type: "remote"
      server_addr: "100.2.126.11"
      server_port: "514"
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

class LogSetting(object):
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
        self.module.params['subcommand'] = 'setbmclogsettings'
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
        status=dict(type='str', required=False, choices=['enable', 'disable']),
        type=dict(type='str', required=False, choices=['local', 'remote', 'both']),
        file_size=dict(type='int', required=False),
        audit_status=dict(type='str', required=False, choices=['enable', 'disable']),
        audit_type=dict(type='str', required=False, choices=['local', 'remote', 'both']),
        rotate_count=dict(type='int', required=False, choices=[0, 1]),
        server_addr=dict(type='str', required=False),
        server_port=dict(type='str', required=False),
        protocol_type=dict(type='str', required=False, choices=['UDP', 'TCP']),
    )
    argument_spec.update(ism_argument_spec)
    log_obj = LogSetting(argument_spec)
    log_obj.work()
    


if __name__ == '__main__':
    main()
