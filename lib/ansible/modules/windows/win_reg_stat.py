#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ansible, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_reg_stat
version_added: "2.3"
short_description: Get information about Windows registry keys
description:
- Like M(win_file), M(win_reg_stat) will return whether the key/property exists.
- It also returns the sub keys and properties of the key specified.
- If specifying a property name through I(property), it will return the information specific for that property.
options:
  path:
    description: The full registry key path including the hive to search for.
    type: str
    required: yes
    aliases: [ key ]
  name:
    description:
    - The registry property name to get information for, the return json will not include the sub_keys and properties entries for the I(key) specified.
    - Set to an empty string to target the registry key's C((Default)) property value.
    type: str
    aliases: [ entry, value, property ]
notes:
- The C(properties) return value will contain an empty string key C("") that refers to the key's C(Default) value. If
  the value has not been set then this key is not returned.
seealso:
- module: win_regedit
- module: win_regmerge
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Obtain information about a registry key using short form
  win_reg_stat:
    path: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion
  register: current_version

- name: Obtain information about a registry key property
  win_reg_stat:
    path: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion
    name: CommonFilesDir
  register: common_files_dir

- name: Obtain the registry key's (Default) property
  win_reg_stat:
    path: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion
    name: ''
  register: current_version_default
'''

RETURN = r'''
changed:
  description: Whether anything was changed.
  returned: always
  type: bool
  sample: true
exists:
  description: States whether the registry key/property exists.
  returned: success and path/property exists
  type: bool
  sample: true
properties:
  description: A dictionary containing all the properties and their values in the registry key.
  returned: success, path exists and property not specified
  type: dict
  sample: {
    "" : {
      "raw_value": "",
      "type": "REG_SZ",
      "value": ""
    },
    "binary_property" : {
      "raw_value": ["0x01", "0x16"],
      "type": "REG_BINARY",
      "value": [1, 22]
    },
    "multi_string_property" : {
      "raw_value": ["a", "b"],
      "type": "REG_MULTI_SZ",
      "value": ["a", "b"]
    }
  }
sub_keys:
  description: A list of all the sub keys of the key specified.
  returned: success, path exists and property not specified
  type: list
  sample: [
    "AppHost",
    "Casting",
    "DateTime"
  ]
raw_value:
  description: Returns the raw value of the registry property, REG_EXPAND_SZ has no string expansion, REG_BINARY or REG_NONE is in hex 0x format.
    REG_NONE, this value is a hex string in the 0x format.
  returned: success, path/property exists and property specified
  type: str
  sample: '%ProgramDir%\\Common Files'
type:
  description: The property type.
  returned: success, path/property exists and property specified
  type: str
  sample: "REG_EXPAND_SZ"
value:
  description: The value of the property.
  returned: success, path/property exists and property specified
  type: str
  sample: 'C:\\Program Files\\Common Files'
'''
