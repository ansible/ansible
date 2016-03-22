#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
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
    required: true
  state:
    description:
      - Specify whether to enable I(present) or disable I(absent) ACL inheritance
    required: false
    choices:
      - present
      - absent
    default: absent
  reorganize:
    description:
      - For P(state) = I(absent), indicates if the inherited ACE's should be copied from the parent directory. This is necessary (in combination with removal) for a simple ACL instead of using multiple ACE deny entries.
      - For P(state) = I(present), indicates if the inherited ACE's should be deduplicated compared to the parent directory. This removes complexity of the ACL structure.
    required: false
    choices:
      - no
      - yes
    default: no
author: Hans-Joachim Kliemeck (@h0nIg)
'''

EXAMPLES = '''
# Playbook example
---
- name: Disable inherited ACE's
  win_acl_inheritance:
    path: 'C:\\apache\\'
    state: absent

- name: Disable and copy inherited ACE's
  win_acl_inheritance:
    path: 'C:\\apache\\'
    state: absent
    reorganize: yes

- name: Enable and remove dedicated ACE's
  win_acl_inheritance:
    path: 'C:\\apache\\'
    state: present
    reorganize: yes
'''

RETURN = '''

'''