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
  - This module helps to install, remove and update Windows PowerShell repository on Windows-based systems.
options:
  name:
    description:
      - Name of the repository to work with.
    required: yes
  source:
    description:
      - Specifies the URI for discovering and installing modules from this repository.
        URI can be a NuGet server feed (most common situation), HTTP, HTTPS, FTP or local folder location.
  state:
    description:
      - If C(present) a new repository is added or existing updated.
      - If C(absent) a repository is removed.
    choices: [ absent, present ]
    default: present
  installation_policy:
    description:
      - Set's the C(InstallationPolicy) of a repository.
    choices: [ trusted, untrusted ]
    default: trusted
notes:
  - The PowerShellGet module (version 1.6.0 or newer) and the NuGet package provider (version 2.8.5.201 or newer) are required.
    To update the NuGet package provider use the command `Install-PackageProvider -Name NuGet -RequiredVersion 2.8.5.201 -Force`.
  - You can't use M(win_psrepository) to re-register (add) removed PSGallery, use the command `Register-PSRepository -Default` instead.
author:
- Wojciech Sciesinski (@it-praktyk)
'''

EXAMPLES = r'''
---
- name: Add a PowerShell module and register a repository
  win_psrepository:
    name: MyRepository
    url: https://myrepo.com
    state: present

- name: Remove a PowerShell repository
  win_psrepository:
    name: MyRepository
    state: absent
'''

RETURN = r'''
'''
