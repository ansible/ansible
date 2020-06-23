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
module: is_add_ldisk
version_added: 1.0
author:
    - WangBaoshan
short_description: Create logical disk
description:
   - Create logical disk on Inspur server.
options:
    info:
        description:
            - Show controller and physical drive info.
        choices: ['show']
        type: str
    ctrl_id:
        description:
            - Raid controller ID,Required when I(Info=None).
        type: int
    level:
        description:
            - RAID Level, 0: RAID0, 1: RAID1, 5: RAID5, 6: RAID6, 10: RAID10,Required when I(Info=None).
        choices: [0, 1, 5, 6, 10]
        type: int
    size:
        description:
            - Strip Size, 1: 64k, 2: 128k, 3: 256k, 4: 512k, 5: 1024k,Required when I(Info=None).
        choices: [1, 2, 3, 4, 5]
        type: int
    access:
        description:
            - Access Policy, 1: Read Write, 2: Read Only, 3: Blocked,Required when I(Info=None).
        choices: [1, 2, 3]
        type: int
    r:
        description:
            - Read Policy, 1: Read Ahead, 2: No Read Ahead,Required when I(Info=None).
        choices: [1, 2]
        type: int
    w:
        description:
            - Write Policy, 1: Write Throgh, 2: Write Back, 3: Write caching ok if bad BBU,Required when I(Info=None).
        choices: [1, 2, 3]
        type: int
    io:
        description:
            - IO Policy, 1: Direct IO, 2: Cached IO,Required when I(Info=None).
        choices: [1, 2]
        type: int
    cache:
        description:
            - Drive Cache, 1: Unchanged, 2: Enabled,3: Disabled,Required when I(Info=None).
        choices: [1, 2, 3]
        type: int
    init:
        description:
            - Init State, 1: No Init, 2: Quick Init, 3: Full Init,Required when I(Info=None).
        choices: [1, 2, 3]
        type: int
    select:
        description:
            - Select Size, from 1 to 100,Required when I(Info=None).
        type: int
    slot:
        description:
            - Slot Num,input multiple slotNumber like 0,1,2...,Required when I(Info=None).
        type: list
        elements: int
'''

EXAMPLES = '''
- name: add ldisk test
  hosts: ism
  connection: local
  gather_facts: no
  vars:
    ism:
      host: "{{ ansible_ssh_host }}"
      username: "{{ username }}"
      password: "{{ password }}"

  tasks:

  - name: "show pdisk information"
    is_add_ldisk:
      info: "show"
      provider: "{{ ism }}"
      
  - name: "add ldisk"
    is_add_ldisk:
      ctrl_id: 0
      level: 1
      size: 1
      access: 1
      r: 1
      w: 1
      io: 1
      cache: 1
      init: 2
      select: 10
      slot: 0,1
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

class Disk(object):
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
        self.module.params['subcommand'] = 'addldisk'
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
        info=dict(type='str', required=False, choices=['show']),
        ctrl_id=dict(type='int', required=False),
        level=dict(type='int', required=False, choices=[0, 1, 5, 6, 10]),
        size=dict(type='int', required=False, choices=[1, 2, 3, 4, 5]),
        access=dict(type='int', required=False, choices=[1, 2, 3]),
        r=dict(type='int', required=False, choices=[1, 2]),
        w=dict(type='int', required=False, choices=[1, 2, 3]),
        io=dict(type='int', required=False, choices=[1, 2]),
        cache=dict(type='int', required=False, choices=[1, 2, 3]),
        init=dict(type='int', required=False, choices=[1, 2, 3]),
        select=dict(type='int', required=False),
        slot=dict(type='list', elements='int', required=False),
    )
    argument_spec.update(ism_argument_spec)
    disk_obj = Disk(argument_spec)
    disk_obj.work()
    


if __name__ == '__main__':
    main()
