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
version_added: "2.0"
short_description: Disable ACL inheritance
description:
    - Disable ACL (Access Control List) inheritance and optionally converts ACE (Access Control Entry) to dedicated ACE
options:
  path:
    description:
      - Path to be used for disabling
    required: true
  copy:
    description:
      - Indicates if the inherited ACE should be copied to dedicated ACE
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
- name: Disable and copy
  win_acl_inheritance:
    path: 'C:\\apache\\'
    copy: yes

- name: Disable
  win_acl_inheritance:
    path: 'C:\\apache\\'
    copy: no
'''
