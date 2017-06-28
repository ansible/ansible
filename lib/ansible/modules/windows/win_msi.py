#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Matt Martz <matt@sivel.net>, and others
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
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_msi
version_added: '1.7'
short_description: Installs and uninstalls Windows MSI files
description:
    - Installs or uninstalls a Windows MSI file that is already located on the
      target server.
options:
    path:
        description:
            - File system path to the MSI file to install
        required: true
    extra_args:
        description:
            - Additional arguments to pass to the msiexec.exe command.
    state:
        description:
            - Whether the MSI file should be installed or uninstalled.
        choices: [ absent, present ]
        default: present
    creates:
        description:
            - Path to a file created by installing the MSI to prevent from
              attempting to reinstall the package on every run.
    removes:
        description:
            - Path to a file removed by uninstalling the MSI to prevent from
              attempting to re-uninstall the package on every run.
        version_added: '2.4'
    wait:
        description:
            - Specify whether to wait for install or uninstall to complete before continuing.
        type: bool
        default: 'no'
        version_added: '2.1'
notes:
- This module is not idempotent and will report a change every time.
  Use the C(creates) and C(removes) options to your advantage.
- Please look into M(win_package) instead, this package will be deprecated in the future.
author:
- Matt Martz (@sivel)
'''

EXAMPLES = r'''
- name: Install an MSI file
  win_msi:
    path: C:\7z920-x64.msi

- name: Install an MSI, and wait for it to complete before continuing
  win_msi:
    path: C:\7z920-x64.msi
    wait: yes

- name: Uninstall an MSI file
  win_msi:
    path: C:\7z920-x64.msi
    state: absent
'''

RETURN = r'''
log:
  description: The logged output from the installer
  returned: always
  type: string
  sample: N/A
'''
