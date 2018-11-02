#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Denis Pastukhov <past20005@yandex.ru>
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
      - If C(absent) all versions of a module are removed. If I(version) is set - removes only this specific version.
      - >
        If C(latest) searches for new versions in repository. If module present - updates module, else installs latest version. This is mutually
        exclusive with I(version).
    choices: [ absent, present, latest ]
    default: present
  version:
    description:
      - Allows to select version of powershell module to install or remove.
      - If there is no version present on target host a selected version will be installed.
      - If lower versions of module are present a selected version will be installed.
      - >
        If there is higher version present warning will be returned. No changed will be done. I(force_version) can be used to change this behavior.
        This is mutually exclusive with I(state=latest).
    default: 'null'
    version_added: '2.8'
  force_version:
    description:
      - Changes behavior of I(version). If there is higher version present all versions will be uninstalled, selected version will be installed.
      - Requires I(version).
    type: bool
    default: 'no'
    version_added: '2.8'
notes:
   -  Powershell 5.0 or higher is needed.

author:
- Daniele Lazzari
- Denis Pastukhov
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

- name: Always install latest version of module when possible
  win_psmodule:
    name: MyCustomModule
    state: latest

- name: Install a specific version of module from a specific repository
  win_psmodule:
    name: MyCustomModule
    repository: MyRepository
    state: present
    version: 1.6.0.0

- name: Install a specific version of module from a specific repository even if highest version already installed
  win_psmodule:
    name: MyCustomModule
    repository: MyRepository
    state: present
    version: 1.6.0.0
    force_version: yes

- name: Remove a powershell module
  win_psmodule:
    name: PowershellModule
    state: absent

- name: Remove a specific version of powershell module
  win_psmodule:
    name: PowershellModule
    state: absent
    version: 1.0.0

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
version:
  description: show changes of versions
  returned: on version change
  type: string
  sample: 1.0.0.9 => 1.0.0.5
'''
