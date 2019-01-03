#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Sam Liu <sam.liu@activenetwork.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_file_version
version_added: "2.1"
short_description: Get DLL or EXE file build version
description:
  - Get DLL or EXE file build version.
notes:
  - This module will always return no change.
options:
  path:
    description:
      - File to get version.
      - Always provide absolute path.
    type: path
    required: yes
seealso:
- module: win_file
author:
- Sam Liu (@SamLiu79)
'''

EXAMPLES = r'''
- name: Get acm instance version
  win_file_version:
    path: C:\Windows\System32\cmd.exe
  register: exe_file_version

- debug:
    msg: '{{ exe_file_version }}'
'''

RETURN = r'''
path:
  description: file path
  returned: always
  type: str

file_version:
  description: File version number..
  returned: no error
  type: str

product_version:
  description: The version of the product this file is distributed with.
  returned: no error
  type: str

file_major_part:
  description: the major part of the version number.
  returned: no error
  type: str

file_minor_part:
  description: the minor part of the version number of the file.
  returned: no error
  type: str

file_build_part:
  description: build number of the file.
  returned: no error
  type: str

file_private_part:
  description: file private part number.
  returned: no error
  type: str
'''
