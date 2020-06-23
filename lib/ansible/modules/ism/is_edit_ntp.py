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
module: is_edit_ntp
version_added: 1.0
author:
    - WangBaoshan
short_description: Set NTP
description:
   - Set NTP on Inspur server.
options:
    auto_date:
        description:
            - date auto synchronize.
        choices: ['enable', 'disable']
        type: str
    ntp_time:
        description:
            - NTP time(YYYYmmddHHMMSS).
        type: str
    time_zone:
        description:
            - UTC time zone,chose from {-12, -11.5, -11, ... ,11,11.5,12}.
        type: str
    server1:
        description:
            - NTP Server1(ipv4 or ipv6 or domain name), set when auto_dateis enable.
        type: str
    server2:
        description:
            - NTP Server2(ipv4 or ipv6 or domain name), set when auto_date is enable.
        type: str
    server3:
        description:
            - NTP Server3(ipv4 or ipv6 or domain name), set when auto_date is enable.
        type: str
    syn_cycle:
        description:
            - NTP syn cycle(minute).
        type: int
'''

EXAMPLES = '''
- name: NTP test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "set ntp"
    is_edit_ntp:
      auto_date: "enable"
      server2: "time.nist.gov"
      provider: "{{ ism }}"

  - name: "set ntp"
    is_edit_ntp:
      ntp_time: "20200609083600"
      provider: "{{ ism }}"

  - name: "set ntp"
    is_edit_ntp:
      time_zone: 8
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

class NTP(object):
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
        self.module.params['subcommand'] = 'settime'
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
        auto_date=dict(type='str', required=False, choices=['enable', 'disable']),
        ntp_time=dict(type='str', required=False),
        time_zone=dict(type='str', required=False),
        server1=dict(type='str', required=False),
        server2=dict(type='str', required=False),
        server3=dict(type='str', required=False),
        syn_cycle=dict(type='int', required=False),
    )
    argument_spec.update(ism_argument_spec)
    ntp_obj = NTP(argument_spec)
    ntp_obj.work()
    


if __name__ == '__main__':
    main()
