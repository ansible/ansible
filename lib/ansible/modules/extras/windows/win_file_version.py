#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Get DLL or EXE build version
# Copyright © 2015 Sam Liu <sam.liu@activenetwork.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: win_file_version
version_added: "2.1"
short_description: Get DLL or EXE file build version
description:
  - Get DLL or EXE file build version
  - change state alway be false
options:
  path:
    description:
      - File to get version(provide absolute path)
    required: true
    aliases: []
author: Sam Liu
'''

EXAMPLES = '''
# get C:\Windows\System32\cmd.exe version in playbook
---
- name: Get acm instance version
  win_file_version:
    path: 'C:\Windows\System32\cmd.exe'
  register: exe_file_version

- debug: msg="{{exe_file_version}}"

'''

RETURN = """
win_file_version.path:
  description: file path
  returned: always
  type: string

win_file_version.file_version:
  description: file version number.
  returned: no error
  type: string

win_file_version.product_version:
  description: the version of the product this file is distributed with.
  returned: no error
  type: string

win_file_version.file_major_part:
  description: the major part of the version number.
  returned: no error
  type: string

win_file_version.file_minor_part:
  description: the minor part of the version number of the file.
  returned: no error
  type: string

win_file_version.file_build_part:
  description: build number of the file.
  returned: no error
  type: string

win_file_version.file_private_part:
  description: file private part number.
  returned: no error
  type: string

"""
