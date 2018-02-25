#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2017 Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_tempfile
version_added: "2.3"
author:
- Dag Wieers (@dagwieers)
short_description: Creates temporary files and directories
description:
  - Creates temporary files and directories.
  - For non-Windows targets, please use the M(tempfile) module instead.
options:
  state:
    description:
      - Whether to create file or directory.
    choices: [ directory, file ]
    default: file
  path:
    description:
      - Location where temporary file or directory should be created.
      - If path is not specified default system temporary directory (%TEMP%) will be used.
    default: '%TEMP%'
  prefix:
    description:
      - Prefix of file/directory name created by module.
    default: ansible.
  suffix:
    description:
      - Suffix of file/directory name created by module.
    default: ''
notes:
  - For non-Windows targets, please use the M(tempfile) module instead.
'''

EXAMPLES = r"""
- name: Create temporary build directory
  win_tempfile:
    state: directory
    suffix: build

- name: Create temporary file
  win_tempfile:
    state: file
    suffix: temp
"""

RETURN = r'''
path:
  description: Path to created file or directory
  returned: success
  type: string
  sample: C:\Users\Administrator\AppData\Local\Temp\ansible.bMlvdk
'''
