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
module: win_owner
version_added: "2.1"
short_description: Set owner
description:
    - Set owner of files or directories
options:
  path:
    description:
      - Path to be used for changing owner
    required: true
  user:
    description:
      - Name to be used for changing owner
    required: true
  recurse:
    description:
      - Indicates if the owner should be changed recursively
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
- name: Change owner of Path
  win_owner:
    path: 'C:\\apache\\'
    user: apache
    recurse: yes

- name: Set the owner of root directory
  win_owner:
    path: 'C:\\apache\\'
    user: SYSTEM
    recurse: no
'''

RETURN = '''

'''