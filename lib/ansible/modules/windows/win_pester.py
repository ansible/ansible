#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_pester
short_description: Run Pester tests on Windows hosts
version_added: "2.6"
description:
  - Run Pester tests on Windows hosts.
  - Test files have to be available on the remote host.
requirements:
  - Pester
options:
  path:
    description:
      - Path to a pester test file or a folder where tests can be found.
      - If the path is a folder, the module will consider all ps1 files as Pester tests.
    type: str
    required: true
  version:
    description:
      - Minimum version of the pester module that has to be available on the remote host.
author:
    - Erwan Quelin (@equelin)
'''

EXAMPLES = r'''
- name: Get facts
  setup:

- name: Add Pester module
  action:
    module_name: "{{ 'win_psmodule' if ansible_powershell_version >= 5 else 'win_chocolatey' }}"
    name: Pester
    state: present

- name: Run the pester test provided in the path parameter.
  win_pester:
    path: C:\Pester

# Run pesters tests files that are present in the specified folder
# ensure that the pester module version available is greater or equal to the version parameter.
- name: Run the pester test present in a folder and check the Pester module version.
  win_pester:
    path: C:\Pester\test01.test.ps1
    version: 4.1.0
'''

RETURN = r'''
pester_version:
    description: Version of the pester module found on the remote host.
    returned: always
    type: str
    sample: 4.3.1
output:
    description: Results of the Pester tests.
    returned: success
    type: list
    sample: false
'''
