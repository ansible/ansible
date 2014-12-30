#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Phil Schwartz <schwartzmx@gmail.com>
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

DOCUMENTATION = '''
---
module: win_unzip
version_added: ""
short_description: Unzips compressed files on the Windows node
description:
     - Unzips compressed files, and can force reboot (if needed, i.e. such as hotfixes). If the destination directory does not exist, it will be created before unzipping the file. Specifying rm parameter will allow removal of the zip file after extraction.
options:
  zip:
    description:
      - Zip file to be unzipped (provide absolute path)
    required: true
    default: null
    aliases: []
  dest:
    description:
      - Destination of zip file (provide absolute path of directory). If it does not exist, the directory will be created.
    required: true
    default: null
    aliases: []
  rm:
    description:
      - Remove the zip file, after unzipping
    required: no
    default: false
    aliases: []
  restart:
    description:
      - Restarts the computer after unzip, can be useful for hotfixes such as http://support.microsoft.com/kb/2842230 (Restarts will have to be accounted for with wait_for module)
    choices:
      - true
      - false
    required: false
    default: false
    aliases: []
author: Phil Schwartz
'''

EXAMPLES = '''
# This unzips hotfix http://support.microsoft.com/kb/2842230 and forces reboot (for hotfix to take effect)
$ ansible -i hosts -m win_unzip -a "zip=C:\\463984_intl_x64_zip.exe dest=C:\\Hotfix restart=true" all
# This unzips a library that was downloaded with win_get_url, and removes the file after extraction
$ ansible -i hosts -m win_unzip -a "zip=C:\\LibraryToUnzip.zip dest=C:\\Lib rm=true" all
# Playbook example
---
- name: Install WinRM PowerShell Hotfix for Windows Server 2008 SP1
  hosts: all
  gather_facts: false
  tasks:
  - name: Grab Hotfix from URL
    win_get_url:
      url: 'http://hotfixv4.microsoft.com/Windows%207/Windows%20Server2008%20R2%20SP1/sp2/Fix467402/7600/free/463984_intl_x64_zip.exe'
      dest: 'C:\\463984_intl_x64_zip.exe'
  - name: Unzip hotfix
    win_unzip:
      zip: "C:\\463984_intl_x64_zip.exe"
      dest: "C:\\Hotfix"
      restart: true
  - name: Wait for server reboot...
  local_action:
    module: wait_for
      host={{ inventory_hostname }}
      port={{ansible_ssh_port|default(5986)}}
      delay=15
      timeout=600
      state=started
'''
