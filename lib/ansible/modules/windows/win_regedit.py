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
version_added: '2.0'
short_description: Add, change, or remove registry keys and values
description:
- Add, modify or remove registry keys and values.
- More information about the windows registry from Wikipedia
  U(https://en.wikipedia.org/wiki/Windows_Registry).
options:
  path:
    description:
    - Name of the registry path.
    - 'Should be in one of the following registry hives: HKCC, HKCR, HKCU,
      HKLM, HKU.'
    required: true
    aliases: [ key ]
  name:
    description:
    - Name of the registry entry in the above C(path) parameters.
    - If not provided, or empty then the '(Default)' property for the key will
      be used.
    aliases: [ entry ]
  data:
    description:
    - Value of the registry entry C(name) in C(path).
    - If not specified then the value for the property will be null for the
      corresponding C(type).
    - Binary and None data should be expressed in a yaml byte array or as comma
      separated hex values.
    - An easy way to generate this is to run C(regedit.exe) and use the
      I(export) option to save the registry values to a file.
    - In the exported file, binary value will look like C(hex:be,ef,be,ef), the
      C(hex:) prefix is optional.
    - DWORD and QWORD values should either be represented as a decimal number
      or a hex value.
    - Multistring values should be passed in as a list.
    - See the examples for more details on how to format this data.
  type:
    description:
    - The registry value data type.
    choices: [ binary, dword, expandstring, multistring, string, qword ]
    default: string
    aliases: [ datatype ]
  state:
    description:
    - The state of the registry entry.
    choices: [ present, absent ]
    default: present
  delete_key:
    description:
    - When C(state) is 'absent' then this will delete the entire key.
    - If this is False then it will only clear out the '(Default)' property for
      that key.
    type: bool
    default: 'yes'
    version_added: '2.4'
notes:
- Check-mode C(-C/--check) and diff output C(-D/--diff) are supported, so that you can test every change against the active configuration before
  applying changes.
- Beware that some registry hives (C(HKEY_USERS) in particular) do not allow to create new registry paths.
- Since ansible 2.4, when checking if a string registry value has changed, a case-sensitive test is used. Previously the test was case-insensitive.
author:
- Adam Keech (@smadam813)
- Josh Ludwig (@joshludwig)
- Jordan Borean (@jborean93)
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

- name: Add or update registry path MyCompany, with dword entry 'hello', and containing 1337 as the decimal value
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: 1337
    type: dword

- name: Add or update registry path MyCompany, with dword entry 'hello', and containing 0xff2500ae as the hex value
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: 0xff2500ae
    type: dword

- name: Add or update registry path MyCompany, with binary entry 'hello', and containing binary data in hex-string format
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: hex:be,ef,be,ef,be,ef,be,ef,be,ef
    type: binary

- name: Add or update registry path MyCompany, with binary entry 'hello', and containing binary data in yaml format
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: [0xbe,0xef,0xbe,0xef,0xbe,0xef,0xbe,0xef,0xbe,0xef]
    type: binary

- name: Add or update registry path MyCompany, with expand string entry 'hello'
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: '%appdata%\local'
    type: expandstring

- name: Add or update registry path MyCompany, with multi string entry 'hello'
  win_regedit:
    path: HKCU:\Software\MyCompany
    name: hello
    data: ['hello', 'world']
    type: multistring

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
    delete_key: yes

- name: Clear the existing (Default) entry at path MyCompany
  win_regedit:
    path: HKCU:\Software\MyCompany
    state: absent
    delete_key: no

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
