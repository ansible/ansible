#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Prasoon Karunan V (@prasoonkarunan)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_auto_logon
short_description: Adds or Sets auto logon registry keys.
description:
  - Used to apply auto logon registry setting.
version_added: "2.10"
options:
  user:
    description:
      - Username to login automatically.
      - Value of this input will be set to DefaultUsername registry key..
    type: str
    required: yes
  password:
    description:
      - Password to be used for automatic login.
      - Value of this input will be used as password for Default user.
    type: str
    required: yes
  domain:
    description:
      - Domain name to be used while automatic login.
    type: str
    default: default user domain.
  state:
    description:
      - Whether the registry key should be C(present) or C(absent).
    type: str
    choices: [ absent, present ]
    default: present
author:
  - Prasoon Karunan V (@prasoonkarunan)
'''

EXAMPLES = r'''
- name: Set autologon for user1
  win_auto_logon:
    user: User1
    password: str0ngp@ssword

- name: Set autologon for abc.com\\user1
  win_auto_logon:
    user: User1
    password: str0ngp@ssword
    domain: abc.com

- name: Remove autologon for user1
  win_auto_logon:
    state: absent
'''

RETURN = r'''
changed:
    description: Returns true if autologon keys successfully set.
    returned: true/false
    type: bool
    sample: true
'''
