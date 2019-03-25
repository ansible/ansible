#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_acl_inheritance
version_added: "2.1"
short_description: Change ACL inheritance
description:
    - Change ACL (Access Control List) inheritance and optionally copy inherited ACE's (Access Control Entry) to dedicated ACE's or vice versa.
options:
  path:
    description:
      - Path to be used for changing inheritance
    required: yes
    type: path
  state:
    description:
      - Specify whether to enable I(present) or disable I(absent) ACL inheritance.
    type: str
    choices: [ absent, present ]
    default: absent
  reorganize:
    description:
      - For P(state) = I(absent), indicates if the inherited ACE's should be copied from the parent directory.
        This is necessary (in combination with removal) for a simple ACL instead of using multiple ACE deny entries.
      - For P(state) = I(present), indicates if the inherited ACE's should be deduplicated compared to the parent directory.
        This removes complexity of the ACL structure.
    type: bool
    default: no
seealso:
- module: win_acl
- module: win_file
- module: win_stat
author:
- Hans-Joachim Kliemeck (@h0nIg)
'''

EXAMPLES = r'''
- name: Disable inherited ACE's
  win_acl_inheritance:
    path: C:\apache
    state: absent

- name: Disable and copy inherited ACE's
  win_acl_inheritance:
    path: C:\apache
    state: absent
    reorganize: yes

- name: Enable and remove dedicated ACE's
  win_acl_inheritance:
    path: C:\apache
    state: present
    reorganize: yes
'''

RETURN = r'''

'''
