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
      - Name of the PowerShell module that has to be installed.
    required: no
state:
    description:
      - If C(present) a new module is installed.
      - If C(absent) a module is removed.
      - If C(latest) a module is updated.
    choices: [ absent, present, latest ]
    default: present
  required_version:
    description:
      - The exact version of the PowerShell module that has to be installed.
    type: str
    required: no
  minimum_version:
    description:
      - The minimum version of the PowerShell module that has to be installed.
    type: str
    required: no
  maximum_version:
    description:
      - The maximum version of the PowerShell module that has to be installed.
    type: str
    required: no
  allow_clobber:
    description:
      - If C(yes) imports all commands, even if they have the same names as commands that already exists. Available only in Powershell 5.1 or higher.
    type: bool
    default: no
  skip_publisher_check:
    description:
      - If C(yes) allows installs a newer version of a module that already exists on your computer in the case when a newer one is not digitally signed by a trusted publisher and the newest existing module is digitally signed by a trusted publisher.
    type: bool
    default: no
  allow_prerelease:
    description:
      - If C(yes) installs modules marked as prereleases.
      - It doesn't work with the parameters minimum_version and/or maximum_version.
    type: bool
    default: no
  repository:
    description:
      - Name of the custom repository to register or use.
    type: str
  url:
    description:
      - URL of the custom repository to register.
notes:
   -  Powershell 5.0 or higher is needed.
seealso:
- module: win_psrepository
author:
- Daniele Lazzari (@dlazz)
- Wojciech Sciesinski (@it-praktyk)
'''

EXAMPLES = r'''
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

RETURN = r'''
---
output:
  description: A message describing the task result.
  returned: always
  sample: "Module PowerShellCookbook installed"
  type: str
nuget_changed:
  description: True when Nuget package provider is installed.
  returned: always
  type: bool
  sample: true
repository_changed:
  description: True when a custom repository is installed or removed.
  returned: always
  type: bool
  sample: True
powershellget_changed:
  description: true when the PowerShellGet module is updated
  returned: always
  type: boolean
  sample: True
packagemanagement_changed:
  description: true when the PackageManagement module is updated
  returned: always
  type: boolean
  sample: True
'''
