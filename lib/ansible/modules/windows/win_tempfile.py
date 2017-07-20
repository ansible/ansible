#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017 Dag Wieers <dag@wieers.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_tempfile
version_added: "2.3"
author: Dag Wieers (@dagwieers)
short_description: Creates temporary files and directories.
description:
  - Creates temporary files and directories.
  - For non-Windows targets, please use the M(tempfile) module instead.
options:
  state:
    description:
      - Whether to create file or directory.
    choices: [ file, directory ]
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
