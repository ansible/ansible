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
  logon_count:
    description:
      - The number of times to do an automatic logon.
      - This count is deremented by Windows everytime an automatic logon is
        performed.
      - Once the count reaches C(0) then the automatic logon process is
        disabled.
    type: int
  username:
    description:
      - Username to login automatically.
      - Must be set when C(state=present).
      - This can be the Netlogon or UPN of a domain account and is
        automatically parsed to the C(DefaultUserName) and C(DefaultDomainName)
        registry properties.
    type: str
  password:
    description:
      - Password to be used for automatic login.
      - Must be set when C(state=present).
      - Value of this input will be used as password for I(username).
      - While this value is encrypted by LSA it is decryptable to any user who
        is an Administrator on the remote host.
    type: str
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
    username: User1
    password: str0ngp@ssword

- name: Set autologon for abc.com\user1
  win_auto_logon:
    username: abc.com\User1
    password: str0ngp@ssword

- name: Remove autologon for user1
  win_auto_logon:
    state: absent

- name: Set autologon for user1 with a limited logon count
  win_auto_logon:
    username: User1
    password: str0ngp@ssword
    logon_count: 5
'''

RETURN = r'''
#
'''
