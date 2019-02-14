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
module: win_psrepository
version_added: "2.8"
short_description: Adds, removes or updates a Windows PowerShell repository.
description:
  - This module helps to add, remove and update Windows PowerShell repository on Windows-based systems.
options:
  name:
    description:
      - Name of the repository to work with.
    type: str
    required: yes
  source:
    description:
      - Specifies the URI for discovering and installing modules from this repository.
      - A URI can be a NuGet server feed (most common situation), HTTP, HTTPS, FTP or file location.
    type: str
  state:
    description:
      - If C(present) a new repository is added or updated.
      - If C(absent) a repository is removed.
    type: str
    choices: [ absent, present ]
    default: present
  installation_policy:
    description:
      - Sets the C(InstallationPolicy) of a repository.
      - Will default to C(trusted) when creating a new repository.
    type: str
    choices: [ trusted, untrusted ]
notes:
  - PowerShell modules needed
      - PowerShellGet >= 1.6.0
      - PackageManagement >= 1.1.7
  - PowerShell package provider needed
      - NuGet >= 2.8.5.201
  - See the examples on how to update the NuGet package provider.
  - You can not use C(win_psrepository) to re-register (add) removed PSGallery, use the command C(Register-PSRepository -Default) instead.
seealso:
- module: win_psmodule
author:
- Wojciech Sciesinski (@it-praktyk)
'''

EXAMPLES = '''
---
- name: Ensure the required NuGet package provider version is installed
  win_shell: Find-PackageProvider -Name Nuget -ForceBootstrap -IncludeDependencies -Force

- name: Add a PowerShell module and register a repository
  win_psrepository:
    name: MyRepository
    source: https://myrepo.com
    state: present

- name: Remove a PowerShell repository
  win_psrepository:
    name: MyRepository
    state: absent
'''

RETURN = '''
'''
