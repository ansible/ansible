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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_regedit
version_added: "2.0"
short_description: Add, change, or remove registry keys and values
description:
    - Add, modify or remove registry keys and values.
    - More information about the windows registry from Wikipedia (https://en.wikipedia.org/wiki/Windows_Registry).
options:
  path:
    description:
      - Name of registry path.
      - 'Should be in one of the following registry hives: HKCC, HKCR, HKCU, HKLM, HKU.'
    required: true
    aliases: [ key ]
  name:
    description:
      - Name of registry entry in C(path).
      - This is an entry in the above C(key) parameter.
      - If not provided, or empty we use the default name '(default)'
    aliases: [ entry ]
  data:
    description:
      - Value of the registry entry C(name) in C(path).
      - Binary data should be expressed a yaml byte array or as comma separated hex values.  An easy way to generate this is to run C(regedit.exe) and use the I(Export) option to save the registry values to a file.  In the exported file binary values will look like C(hex:be,ef,be,ef).  The C(hex:) prefix is optional.
  type:
    description:
      - Registry value data type.
    choices:
      - binary
      - dword
      - expandstring
      - multistring
      - string
      - qword
    default: string
    aliases: [ datatype ]
  state:
    description:
      - State of registry entry.
    choices:
      - present
      - absent
    default: present
notes:
- Check-mode C(-C/--check) and diff output (-D/--diff) are supported, so that you can test every change against the active configuration before applying changes.
- Beware that some registry hives (HKEY_USERS in particular) do not allow to create new registry paths.
author: "Adam Keech (@smadam813), Josh Ludwig (@joshludwig)"
'''

EXAMPLES = r'''
- name: Create registry path MyCompany
  win_regedit:
    path: HKCU:\Software\MyCompany

- name: Add or update registry path MyCompany, with entry 'hello', and containing 'world'
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: world

- name: Add or update registry path MyCompany, with entry 'hello', and containing 1337
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: 1337
    type: dword

- name: Add or update registry path MyCompany, with entry 'hello', and containing binary data in hex-string format
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: hex:be,ef,be,ef,be,ef,be,ef,be,ef
    type: binary

- name: Add or update registry path MyCompany, with entry 'hello', and containing binary data in yaml format
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: [0xbe,0xef,0xbe,0xef,0xbe,0xef,0xbe,0xef,0xbe,0xef]
    type: binary

- name: Disable keyboard layout hotkey for all users (changes existing)
  win_regedit:
    path: HKU:\.DEFAULT\Keyboard Layout\Toggle
    name: Layout Hotkey
    data: 3
    type: dword

- name: Disable language hotkey for current users (adds new)
  win_regedit:
    path: HKCU:\Keyboard Layout\Toggle
    name: Language Hotkey
    data: 3
    type: dword

- name: Remove registry path MyCompany (including all entries it contains)
  win_regedit:
    path: HKCU:\Software\MyCompany
    state: absent

- name: Remove entry 'hello' from registry path MyCompany
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    state: absent
'''

RETURN = r'''
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
