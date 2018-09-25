#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_psmodule
version_added: "2.4"
short_description: Adds or removes a Powershell Module
description:
    - This module helps to install Powershell modules and register custom modules repository on Windows Server.
options:
  name:
    description:
      - Name of the powershell module that has to be installed.
    required: yes
  allow_clobber:
    description:
      - If C(yes) imports all commands, even if they have the same names as commands that already exists. Available only in Powershell 5.1 or higher.
    type: bool
    default: 'no'
  repository:
    description:
      - Name of the custom repository to register or use.
  url:
    description:
      - URL of the custom repository to register.
  state:
    description:
      - If C(present) a new module is installed.
      - If C(absent) a module is removed.
    choices: [ absent, present ]
    default: present
notes:
   -  Powershell 5.0 or higher is needed.

author:
- Daniele Lazzari
'''

EXAMPLES = '''
---
- name: Add a powershell module
  win_psmodule:
    name: PowershellModule
    state: present

- name: Add a powershell module and register a repository
  win_psmodule:
    name: MyCustomModule
    repository: MyRepository
    url: https://myrepo.com
    state: present

- name: Add a powershell module from a specific repository
  win_psmodule:
    name: PowershellModule
    repository: MyRepository
    state: present

- name: Remove a powershell module
  win_psmodule:
    name: PowershellModule
    state: absent

- name: Remove a powershell module and a repository
  win_psmodule:
    name: MyCustomModule
    repository: MyRepository
    state: absent
'''

RETURN = '''
---
output:
  description: a message describing the task result.
  returned: always
  sample: "Module PowerShellCookbook installed"
  type: string
nuget_changed:
  description: true when Nuget package provider is installed
  returned: always
  type: boolean
  sample: True
repository_changed:
  description: true when a custom repository is installed or removed
  returned: always
  type: boolean
  sample: True
'''
