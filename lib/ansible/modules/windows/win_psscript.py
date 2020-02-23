#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Brian Scholer <@briantist>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_psscript
version_added: '2.10'
short_description: Install and manage PowerShell scripts from a PSRepository
description:
  - Add or remove PowerShell scripts from registered PSRepositories.
options:
  name:
    description:
      - The name of the script you want to install or remove.
    type: str
    required: True
  repository:
    description:
      - The registered name of the repository you want to install from.
      - Cannot be used when I(state=absent).
      - If ommitted, all repositories will be searched.
      - To register a repository, use M(win_psrepository).
    type: str
  scope:
    description:
      - Determines whether the script is installed for only the C(current_user) or for C(all_users).
    type: str
    choices:
      - current_user
      - all_users
    default: all_users
  state:
    description:
      - The desired state of the script. C(absent) removes the script.
      - C(latest) will ensure the most recent version available is installed.
      - C(present) only installs if the script is missing.
    type: str
    choices:
      - present
      - absent
      - latest
    default: present
  required_version:
    description:
      - The exact version of the script to install.
      - Cannot be used with I(minimum_version) or I(maximum_version).
      - Cannot be used when I(state=latest).
    type: str
  minimum_version:
    description:
      - The minimum version of the script to install.
      - Cannot be used when I(state=latest).
    type: str
  maximum_version:
    description:
      - The maximum version of the script to install.
      - Cannot be used when I(state=latest).
    type: str
  allow_prerelease:
    description:
      - If C(yes) installs scripts flagged as prereleases.
    type: bool
    default: no
  source_username:
    description:
      - The username portion of the credential required to access the repository.
      - Must be used together with I(source_password).
    type: str
  source_password:
    description:
      - The password portion of the credential required to access the repository.
      - Must be used together with I(source_username).
    type: str
requirements:
  - C(PowerShellGet) module v1.6.0+
seealso:
  - module: win_psrepository
  - module: win_psrepository_info
  - module: win_psmodule
notes:
  - Unlike PowerShell modules, scripts do not support side-by-side installations of multiple versions. Installing a new version will replace the existing one.
author:
  - Brian Scholer (@briantist)
'''

EXAMPLES = r'''
- name: Install a script from PSGallery
  win_psscript:
    name: Test-RPC
    repository: PSGallery

- name: Find and install the latest version of a script from any repository
  win_psscript:
    name: Get-WindowsAutoPilotInfo
    state: latest

- name: Remove a script that isn't needed
  win_psscript:
    name: Defrag-Partition
    state: absent

- name: Install a specific version of a script for the current user
  win_psscript:
    name: CleanOldFiles
    scope: current_user
    required_version: 3.10.2

- name: Install a script below a certain version
  win_psscript:
    name: New-FeatureEnable
    maximum_version: 2.99.99

- name: Ensure a minimum version of a script is present
  win_psscript:
    name: OldStandby
    minimum_version: 3.0.0

- name: Install any available version that fits a specific range
  win_psscript:
    name: FinickyScript
    minimum_version: 2.5.1
    maximum_version: 2.6.19
'''

RETURN = r'''
'''
