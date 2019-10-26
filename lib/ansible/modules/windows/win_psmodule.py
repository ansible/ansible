#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski[dot]net>
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
short_description: Adds or removes a Windows PowerShell module
description:
  - This module helps to install Windows PowerShell modules and register custom modules repository on Windows-based systems.
options:
  name:
    description:
      - Name of the Windows PowerShell module that has to be installed.
    type: str
    required: yes
  state:
    description:
      - If C(present) a new module is installed.
      - If C(absent) a module is removed.
      - If C(latest) a module is updated to the newest version. This option was added in version 2.8.
    type: str
    choices: [ absent, latest, present ]
    default: present
  required_version:
    description:
      - The exact version of the PowerShell module that has to be installed.
    type: str
    version_added: "2.8"
  minimum_version:
    description:
      - The minimum version of the PowerShell module that has to be installed.
    type: str
    version_added: "2.8"
  maximum_version:
    description:
      - The maximum version of the PowerShell module that has to be installed.
    type: str
    version_added: "2.8"
  allow_clobber:
    description:
      - If C(yes) allows install modules that contains commands those have the same names as commands that already exists.
    type: bool
    default: no
  skip_publisher_check:
    description:
      - If C(yes), allows you to install a different version of a module that already exists on your computer in the case when a different one
        is not digitally signed by a trusted publisher and the newest existing module is digitally signed by a trusted publisher.
    type: bool
    default: no
    version_added: "2.8"
  allow_prerelease:
    description:
      - If C(yes) installs modules marked as prereleases.
      - It doesn't work with the parameters C(minimum_version) and/or C(maximum_version).
      - It doesn't work with the C(state) set to absent.
    type: bool
    default: no
    version_added: "2.8"
  repository:
    description:
      - Name of the custom repository to use.
    type: str
  url:
    description:
      - URL of the custom repository to register.
      - This option is deprecated and will be removed in Ansible 2.12. Use the
        M(win_psrepository) module instead.
    type: str
notes:
  - PowerShell modules needed
      - PowerShellGet >= 1.6.0
      - PackageManagement >= 1.1.7
  - PowerShell package provider needed
      - NuGet >= 2.8.5.201
  - On PowerShell 5.x required modules and a package provider will be updated under the first run of the win_psmodule module.
  - On PowerShell 3.x and 4.x you have to install them before using the win_psmodule.
seealso:
- module: win_psrepository
author:
- Wojciech Sciesinski (@it-praktyk)
- Daniele Lazzari (@dlazz)
'''

EXAMPLES = r'''
---
- name: Add a PowerShell module
  win_psmodule:
    name: PowerShellModule
    state: present

- name: Add an exact version of PowerShell module
  win_psmodule:
    name: PowerShellModule
    required_version: "4.0.2"
    state: present

- name: Install or update an existing PowerShell module to the newest version
  win_psmodule:
    name: PowerShellModule
    state: latest

- name: Install newer version of built-in Windows module
  win_psmodule:
    name: Pester
    skip_publisher_check: yes
    state: present

- name: Add a PowerShell module and register a repository
  win_psmodule:
    name: MyCustomModule
    repository: MyRepository
    state: present

- name: Add a PowerShell module from a specific repository
  win_psmodule:
    name: PowerShellModule
    repository: MyRepository
    state: present

- name: Remove a PowerShell module
  win_psmodule:
    name: PowerShellModule
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
  sample: true
'''
