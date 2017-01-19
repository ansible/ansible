#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Phil Schwartz <schwartzmx@gmail.com>
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
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = r'''
---
module: win_unzip
version_added: "2.0"
short_description: Unzips compressed files and archives on the Windows node
description:
     - Unzips compressed files and archives. For extracting any compression types other than .zip, the PowerShellCommunityExtensions (PSCX) Module is required.  This module (in conjunction with PSCX) has the ability to recursively unzip files within the src zip file provided and also functionality for many other compression types. If the destination directory does not exist, it will be created before unzipping the file.  Specifying rm parameter will force removal of the src file after extraction.
options:
  src:
    description:
      - File to be unzipped (provide absolute path)
    required: true
  dest:
    description:
      - Destination of zip file (provide absolute path of directory). If it does not exist, the directory will be created.
    required: true
  rm:
    description:
      - Remove the zip file, after unzipping
    required: no
    choices:
      - true
      - false
      - yes
      - no
    default: false
  recurse:
    description:
      - Recursively expand zipped files within the src file.
    required: no
    default: false
    choices:
      - true
      - false
      - yes
      - no
  creates:
    description:
      - If this file or directory exists the specified src will not be extracted.
    required: no
    default: null
author: Phil Schwartz
'''

EXAMPLES = r'''
- name: Unzip a bz2 (BZip) file
  win_unzip:
    src: C:\Users\Phil\Logs.bz2
    dest: C:\Users\Phil\OldLogs
    creates: C:\Users\Phil\OldLogs

- name: Recursively decompress GZ files in ApplicationLogs.zip
  win_unzip:
    src: C:\Downloads\ApplicationLogs.zip
    dest: C:\Application\Logs
    recurse: True
    rm: True
'''
