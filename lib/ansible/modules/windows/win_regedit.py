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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'core',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: win_regedit
version_added: "2.0"
short_description: Add, Edit, or Remove Registry Keys and Values
description:
    - Add, Edit, or Remove Registry Keys and Values using ItemProperties Cmdlets
options:
  key:
    description:
      - Name of Registry Key
    required: true
  value:
    description:
      - Name of Registry Value
      - When left out, the default entry for that key is being used.
    default: '(default)'
  data:
    description:
      - Registry Value Data.  Binary data should be expressed a yaml byte array or as comma separated hex values.  An easy way to generate this is to run C(regedit.exe) and use the I(Export) option to save the registry values to a file.  In the exported file binary values will look like C(hex:be,ef,be,ef).  The C(hex:) prefix is optional.
  datatype:
    description:
      - Registry Value Data Type
    choices:
      - binary
      - dword
      - expandstring
      - multistring
      - string
      - qword
    default: string
  state:
    description:
      - State of Registry Value
    choices:
      - present
      - absent
    default: present
author: "Adam Keech (@smadam813), Josh Ludwig (@joshludwig)"
'''

EXAMPLES = r'''
- name: Create Registry Key called MyCompany
  win_regedit:
    key: HKCU:\Software\MyCompany

- name: Create Registry Key called MyCompany with default value "Ansible"
  win_regedit:
    key: HKCU:\Software\MyCompany
    data: Ansible

- name: Create Registry Key called MyCompany, a value within MyCompany Key called "hello", and data for the value "hello" containing "world".
  win_regedit:
    key: HKCU:\Software\MyCompany
    value: hello
    data: world

- name: Create Registry Key called MyCompany, a value within MyCompany Key called "hello", and data for the value "hello" containing "1337" as type "dword".
  win_regedit:
    key: HKCU:\Software\MyCompany
    value: hello
    data: 1337
    datatype: dword

- name: Create Registry Key called MyCompany, a value within MyCompany Key called "hello", and binary data for the value "hello" as type "binary" data expressed as comma separated list
  win_regedit:
    key: HKCU:\Software\MyCompany
    value: hello
    data: hex:be,ef,be,ef,be,ef,be,ef,be,ef
    datatype: binary

- name: Create Registry Key called MyCompany, a value within MyCompany Key called "hello", and binary data for the value "hello" as type "binary" data expressed as yaml array of bytes
  win_regedit:
    key: HKCU:\Software\MyCompany
    value: hello
    data: [0xbe,0xef,0xbe,0xef,0xbe,0xef,0xbe,0xef,0xbe,0xef]
    datatype: binary

- name: Delete Registry Key MyCompany. Not specifying a value will delete the root key which means all values will be deleted
  win_regedit:
    key: HKCU:\Software\MyCompany
    state: absent

- name: Delete Registry Value "hello" from MyCompany Key
  win_regedit:
    key: HKCU:\Software\MyCompany
    value: hello
    state: absent
'''

RETURN = '''
data_changed:
    description: whether this invocation changed the data in the registry value 
    returned: success
    type: boolean
    sample: False
data_type_changed:
    description: whether this invocation changed the datatype of the registry value 
    returned: success
    type: boolean
    sample: True
'''
