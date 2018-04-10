#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Ansible, inc
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_reg_stat
version_added: "2.3"
short_description: returns information about a Windows registry key or property of a key
description:
- Like M(win_file), M(win_reg_stat) will return whether the key/property exists.
- It also returns the sub keys and properties of the key specified.
- If specifying a property name through I(property), it will return the information specific for that property.
options:
  path:
    description: The full registry key path including the hive to search for.
    required: true
    aliases: [ key ]
  name:
    description:
    - The registry property name to get information for, the return json will not include the sub_keys and properties entries for the I(key) specified.
    required: false
    aliases: [ entry, value, property ]
author: "Jordan Borean (@jborean93)"
'''

EXAMPLES = r'''
# Obtain information about a registry key using short form
- win_reg_stat:
    path: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion
  register: current_version

# Obtain information about a registry key property
- win_reg_stat:
    path: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion
    name: CommonFilesDir
  register: common_files_dir
'''

RETURN = r'''
changed:
  description: Whether anything was changed.
  returned: always
  type: boolean
  sample: True
exists:
  description: States whether the registry key/property exists.
  returned: success and path/property exists
  type: boolean
  sample: True
properties:
  description: A dictionary containing all the properties and their values in the registry key.
  returned: success, path exists and property not specified
  type: dict
  sample: {
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
  type: string
  sample: '%ProgramDir%\\Common Files'
type:
  description: The property type.
  returned: success, path/property exists and property specified
  type: string
  sample: "REG_EXPAND_SZ"
value:
  description: The value of the property.
  returned: success, path/property exists and property specified
  type: string
  sample: 'C:\\Program Files\\Common Files'
'''
