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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_unzip
version_added: "2.0"
short_description: Unzips compressed files and archives on the Windows node
description:
- Unzips compressed files and archives.
- Supports .zip files natively
- Supports other formats supported by the Powershell Community Extensions (PSCX) module (basically everything 7zip supports)
- For non-Windows targets, use the M(unarchive) module instead.
requirements:
- PSCX
options:
  src:
    description:
      - File to be unzipped (provide absolute path).
    required: true
  dest:
    description:
      - Destination of zip file (provide absolute path of directory). If it does not exist, the directory will be created.
    required: true
  delete_archive:
    description:
      - Remove the zip file, after unzipping.
    type: bool
    default: 'no'
    aliases: [ rm ]
  recurse:
    description:
      - Recursively expand zipped files within the src file.
      - Setting to a value of C(yes) requires the PSCX module to be installed.
    type: bool
    default: 'no'
  creates:
    description:
      - If this file or directory exists the specified src will not be extracted.
notes:
- This module is not really idempotent, it will extract the archive every time, and report a change.
- For extracting any compression types other than .zip, the PowerShellCommunityExtensions (PSCX) Module is required.  This module (in conjunction with PSCX)
  has the ability to recursively unzip files within the src zip file provided and also functionality for many other compression types. If the destination
  directory does not exist, it will be created before unzipping the file.  Specifying rm parameter will force removal of the src file after extraction.
- For non-Windows targets, use the M(unarchive) module instead.
author:
- Phil Schwartz (@schwartzmx)
'''

EXAMPLES = r'''
# This unzips a library that was downloaded with win_get_url, and removes the file after extraction
# $ ansible -i hosts -m win_unzip -a "src=C:\LibraryToUnzip.zip dest=C:\Lib remove=true" all

- name: Unzip a bz2 (BZip) file
  win_unzip:
    src: C:\Users\Phil\Logs.bz2
    dest: C:\Users\Phil\OldLogs
    creates: C:\Users\Phil\OldLogs

- name: Unzip gz log
  win_unzip:
    src: C:\Logs\application-error-logs.gz
    dest: C:\ExtractedLogs\application-error-logs

# Unzip .zip file, recursively decompresses the contained .gz files and removes all unneeded compressed files after completion.
- name: Unzip ApplicationLogs.zip and decompress all GZipped log files
  hosts: all
  gather_facts: false
  tasks:
    - name: Recursively decompress GZ files in ApplicationLogs.zip
      win_unzip:
        src: C:\Downloads\ApplicationLogs.zip
        dest: C:\Application\Logs
        recurse: yes
        delete_archive: yes

# Install PSCX to use for extracting a gz file
- name: Grab PSCX msi
  win_get_url:
    url: http://download-codeplex.sec.s-msft.com/Download/Release?ProjectName=pscx&DownloadId=923562&FileTime=130585918034470000&Build=20959
    dest: C:\Windows\Temp\pscx.msi

- name: Install PSCX
  win_msi:
    path: C:\Windows\Temp\pscx.msi
'''

RETURN = r'''
dest:
    description: The provided destination path
    returned: always
    type: string
    sample: C:\ExtractedLogs\application-error-logs
removed:
    description: Whether the module did remove any files during task run
    returned: always
    type: boolean
    sample: True
src:
    description: The provided source path
    returned: always
    type: string
    sample: C:\Logs\application-error-logs.gz
'''
