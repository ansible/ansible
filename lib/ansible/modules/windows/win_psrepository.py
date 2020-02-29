#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Brian Scholer <@briantist>
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
  source_location:
    description:
      - Specifies the URI for discovering and installing modules from this repository.
      - A URI can be a NuGet server feed (most common situation), HTTP, HTTPS, FTP or file location.
      - Required when registering a new repository or using I(force=True).
      - Before 2.10, this option was called C(source). The name can be still be used as an alias.
    type: str
    aliases:
      - source
  script_source_location:
    description:
      - Specifies the URI for discovering and installing scripts from this repository.
    type: str
    version_added: '2.10'
  publish_location:
    description:
      - Specifies the URI for publishing modules to this repository.
    type: str
    version_added: '2.10'
  script_publish_location:
    description:
      - Specifies the URI for publishing scripts to this repository.
    type: str
    version_added: '2.10'
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
      - Will default to C(trusted) when creating a new repository or used with I(force=True).
    type: str
    choices: [ trusted, untrusted ]
  force:
    description:
      - If C(True), any differences from the desired state will result in the repository being unregistered, and then re-registered.
      - I(force) has no effect when I(state=absent). See notes for additional context.
    type: bool
    default: False
    version_added: '2.10'
requirements:
  - PowerShell Module L(PowerShellGet >= 1.6.0,https://www.powershellgallery.com/packages/PowerShellGet/)
  - PowerShell Module L(PackageManagement >= 1.1.7,https://www.powershellgallery.com/packages/PackageManagement/)
  - PowerShell Package Provider C(NuGet) >= 2.8.5.201
notes:
  - See the examples on how to update the NuGet package provider.
  - You can not use C(win_psrepository) to re-register (add) removed PSGallery, use the command C(Register-PSRepository -Default) instead.
  - When registering or setting I(source_location), PowerShellGet will transform the location according to internal rules, such as following HTTP/S redirects.
  - This can result in a C(CHANGED) status on each run as the values will never match and will be "reset" each time.
  - To work around that, find the true destination value with M(win_psrepository_info) or C(Get-PSRepository) and update the playbook to match.
  - When updating an existing repository, all options except I(name) are optional. Only supplied options will be updated. Use I(force=True) to exactly match.
  - I(script_location), I(publish_location), and I(script_publish_location) are optional but once set can only be cleared with I(force=True).
  - Using I(force=True) will unregister and re-register the repository if there are any changes, so that it exactly matches the options specified.
seealso:
  - module: win_psrepository_info
  - module: win_psmodule
author:
  - Wojciech Sciesinski (@it-praktyk)
  - Brian Scholer (@briantist)
'''

EXAMPLES = '''
---
- name: Ensure the required NuGet package provider version is installed
  win_shell: Find-PackageProvider -Name Nuget -ForceBootstrap -IncludeDependencies -Force

- name: Register a PowerShell repository
  win_psrepository:
    name: MyRepository
    source_location: https://myrepo.com
    state: present

- name: Remove a PowerShell repository
  win_psrepository:
    name: MyRepository
    state: absent

- name: Add an untrusted repository
  win_psrepository:
    name: MyRepository
    installation_policy: untrusted

- name: Add a repository with different locations
  win_psrepository:
    name: NewRepo
    source_location: https://myrepo.example/module/feed
    script_source_location: https://myrepo.example/script/feed
    publish_location: https://myrepo.example/api/module/publish
    script_publish_location: https://myrepo.example/api/script/publish

- name: Update only two properties on the above repository
  win_psrepository:
    name: NewRepo
    installation_policy: untrusted
    script_publish_location: https://scriptprocessor.example/publish

- name: Clear script locations from the above repository by re-registering it
  win_psrepository:
    name: NewRepo
    installation_policy: untrusted
    source_location: https://myrepo.example/module/feed
    publish_location: https://myrepo.example/api/module/publish
    force: True
'''

RETURN = '''
'''
