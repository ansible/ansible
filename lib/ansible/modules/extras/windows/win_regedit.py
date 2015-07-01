#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Adam Keech <akeech@chathamfinancial.com>, Josh Ludwig <jludwig@chathamfinancial.com>
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
module: win_regedit
version_added: "2.0"
short_description: Add, Edit, or Remove Registry Value
description:
    - Add, Edit, or Remove Registry Value using ItemProperties Cmdlets
options:
  name:
    description:
      - Name of Registry Value
    required: true
    default: null
    aliases: []
  data:
    description:
      - Registry Value Data
    required: false
    default: null
    aliases: []
  type:
    description:
      - Registry Value Data Type
    required: false
    choices:
      - binary
      - dword
      - expandstring
      - multistring
      - string
      - qword
    default: string
    aliases: []
  path:
    description:
      - Path of Registry Value
    required: true
    default: null
    aliases: []
  state:
    description:
      - State of Registry Value
    required: false
    choices:
      - present
      - absent
    default: present
    aliases: []
author: "Adam Keech (@smadam813), Josh Ludwig (@joshludwig)"
'''

EXAMPLES = '''
  # Add Registry Value (Default is String)
  win_regedit:
    name: testvalue
    data: 1337
    path: HKCU:\Software\MyCompany

  # Add Registry Value with Type DWord
  win_regedit:
    name: testvalue
    data: 1337
    type: dword
    path: HKCU:\Software\MyCompany

  # Edit Registry Value called testvalue
  win_regedit:
    name: testvalue
    data: 8008
    path: HKCU:\Software\MyCompany

  # Remove Registry Value called testvalue
  win_regedit:
    name: testvalue
    path: HKCU:\Software\MyCompany
    state: absent
'''
