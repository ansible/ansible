#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible Project
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_pester
short_description: Run Pester tests on Windows hosts.
version_added: "2.6"
description:
     - Run Pester tests on Windows hosts. Test files have to be available on the remote host.
options:
  src:
    description:
      - Path to a pester test file or a folder where tests can be found. If the path is a folder, the module will consider all ps1 files as Pester tests.
    required: true
  version:
    description:
      - Minimum version of the pester module that has to be available on the remote host.
    required: false
author:
    - Erwan Quelin (@erwanquelin)
'''

RETURN = r'''
pester_version:
    description: Version of the pester module found on the remote host.
    returned: always
    type: string
    sample: 4.3.1
pester_result:
    description: Results of the Pester tests.
    returned: success
    type: list
    sample: False
'''

EXAMPLES = r'''
# Playbook example"
- name: Get facts
  setup:

- name: Add Pester module with win_psmodule if PowerShell version is greater than 5.
  win_psmodule:
    name: Pester
    state: present
  when: ansible_powershell_version >= 5

- name: Add Pester module with Chocolatey if PowerShell version is less than 5.
  win_chocolatey:
    name: Pester
    state: present
  when: ansible_powershell_version < 5

- name: Copy test file(s).
  win_copy:
    src: ".\test01.test.ps1"
    dest: "C:\Pester\test01.test.ps1"

- name: run the pester test provided in the src parameter. 
  win_pester:
    src: "C:\Pester"  

- name: run all test present in the folder provided in the src parameter.
  win_pester:
    src: "C:\Pester\"

- name: run the pester test provided in the src parameter, ensure that the pester module version available is greater or equal to the version parameter.
  win_pester:
    src: "C:\Pester\test01.test.ps1"
    version: 4.1.0
'''
