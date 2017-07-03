#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Trond Hindenes <trond@hindenes.com>, and others
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
module: win_package
version_added: "1.7"
author: Trond Hindenes
short_description: Installs/Uninstalls an installable package, either from local file system or url
description:
     - Installs or uninstalls a package.
     - >
       Use a product_id to check if the package needs installing. You can find product ids for installed programs in the windows registry
       either in C(HKLM:Software\Microsoft\Windows\CurrentVersion\Uninstall) or for 32 bit programs
       C(HKLM:Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall)
     - For non-Windows targets, use the M(package) module instead.
options:
  path:
    description:
      - Location of the package to be installed (either on file system, network share or url)
    required: true
  name:
    description:
      - Name of the package, if name isn't specified the path will be used for log messages
    required: false
    default: null
  product_id:
    description:
      - Product id of the installed package (used for checking if already installed)
      - >
        You can find product ids for installed programs in the windows registry either in C(HKLM:Software\Microsoft\Windows\CurrentVersion\Uninstall)
        or for 32 bit programs C(HKLM:Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall)
    required: true
    aliases: [productid]
  arguments:
    description:
      - Any arguments the installer needs
    default: null
    required: false
  state:
    description:
      - Install or Uninstall
    choices:
      - present
      - absent
    default: present
    required: false
    aliases: [ensure]
  user_name:
    description:
      - Username of an account with access to the package if it's located on a file share. Only needed if the winrm user doesn't have access to the package.
        Also specify user_password for this to function properly.
    default: null
    required: false
  user_password:
    description:
      - Password of an account with access to the package if it's located on a file share. Only needed if the winrm user doesn't have access to the package.
        Also specify user_name for this to function properly.
    default: null
    required: false
  expected_return_code:
    description:
      - One or more return codes from the package installation that indicates success.
      - If not provided, defaults to 0
    required: no
    default: 0
notes:
     - For non-Windows targets, use the M(package) module instead.
'''

EXAMPLES = r'''
- name: Install the Visual C thingy
  win_package:
    name: Microsoft Visual C thingy
    path: http://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe
    product_id: '{CF2BEA3C-26EA-32F8-AA9B-331F7E34BA97}'
    arguments: /install /passive /norestart

- name: Install Remote Desktop Connection Manager from msi
  win_package:
    path: https://download.microsoft.com/download/A/F/0/AF0071F3-B198-4A35-AA90-C68D103BDCCF/rdcman.msi
    product_id: '{0240359E-6A4C-4884-9E94-B397A02D893C}'

- name: Uninstall Remote Desktop Connection Manager installed from msi
  win_package:
    path: https://download.microsoft.com/download/A/F/0/AF0071F3-B198-4A35-AA90-C68D103BDCCF/rdcman.msi
    product_id: '{0240359E-6A4C-4884-9E94-B397A02D893C}'
    state: absent

# Specify the expected non-zero return code when successful
# In this case 3010 indicates 'reboot required'
- name: 'Microsoft .NET Framework 4.5.1'
  win_package:
    path: https://download.microsoft.com/download/1/6/7/167F0D79-9317-48AE-AEDB-17120579F8E2/NDP451-KB2858728-x86-x64-AllOS-ENU.exe
    productid: '{7DEBE4EB-6B40-3766-BB35-5CBBC385DA37}'
    arguments: '/q /norestart'
    ensure: present
    expected_return_code: 3010

# Specify multiple non-zero return codes when successful
# In this case we can say that both 0 (SUCCESSFUL) and 3010 (REBOOT REQUIRED) codes are acceptable
- name: 'Microsoft .NET Framework 4.5.1'
  win_package:
    path: https://download.microsoft.com/download/1/6/7/167F0D79-9317-48AE-AEDB-17120579F8E2/NDP451-KB2858728-x86-x64-AllOS-ENU.exe
    productid: '{7DEBE4EB-6B40-3766-BB35-5CBBC385DA37}'
    arguments: '/q /norestart'
    ensure: present
    expected_return_code: [0,3010]
'''
