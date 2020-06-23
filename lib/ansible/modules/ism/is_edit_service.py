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
module: is_edit_service
version_added: 1.0
author:
    - WangBaoshan
short_description: Set service settings
description:
   - Set service settings on Inspur server.
options:
    service_name:
        description:
            - Displays service name of the selected slot(readonly)..
        choices: ['web', 'kvm', 'cd-media', 'fd-media', 'hd-media', 'ssh', 'telnet', 'solssh', 'snmp']
        type: str
        required: true
    state:
        description:
            - Displays the current status of the service, either active or inactive state. 
            - Check this option to start the inactive service.
        choices: ['active', 'inactive']
        type: str
    interface:
        description:
            - It shows the interface in which service is running. 
            - The user can choose any one of the available interfaces. 
        choices: ['eth0', 'eth1', 'both', 'bond0']
        type: str
    non_secure_port:
        description:
            - Used to configure non secure port number for the service.
            - Port value ranges from 1 to 65535.
        type: int
    secure_port:
        description:
            - Used to configure secure port number for the service. 
            Port value ranges from 1 to 65535.
        type: int
    timeout:
        description:
            - Displays the session timeout value of the service.
            - For web, SSH and telnet service, user can configure the session timeout value.
            - Web timeout value ranges from 300 to 1800 seconds.
            - SSH and Telnet timeout value ranges from 60 to 1800 seconds.
            - timeout value should be in multiples of 60 seconds.
        type: int
'''

EXAMPLES = '''
- name: edit service test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "edit kvm"
    is_edit_service:
      service_name: "kvm"
      state: "active"
      timeout: "1200"
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

class Service(object):
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
        self.module.params['subcommand'] = 'setservice'
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
        service_name=dict(type='str', required=True, choices=['web', 'kvm', 'cd-media', 'fd-media', 'hd-media', 'ssh', 'telnet', 'solssh', 'snmp']),
        state=dict(type='str', required=False, choices=['active', 'inactive']),
        interface=dict(type='str', required=False, choices=['eth0', 'eth1', 'both', 'bond0']),
        non_secure_port=dict(type='int', required=False),
        secure_port=dict(type='int', required=False),
        timeout=dict(type='int', required=False)
    )
    argument_spec.update(ism_argument_spec)
    service_obj = Service(argument_spec)
    service_obj.work()
    


if __name__ == '__main__':
    main()
