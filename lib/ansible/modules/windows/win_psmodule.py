#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Daniele Lazzari <lazzari@mailup.com>
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_psmodule
version_added: "2.4"
short_description: Adds or removes a Powershell Module.
description:
    - This module helps to install Powershell modules and register custom modules repository on Windows Server. Powershell 5.0 is needed.
options:
  name:
    description:
      - Name of the powershell module that has to be installed.
    required: true
  repository:
    description:
      - Name of the custom repository to register.
  url:
    description:
      - Url of the custom repository.
  state:
    description:
      - If present a new module is installed. If absent a module is removed.
    default: present
    choices:
      - present
      - absent
author: Daniele Lazzari
'''

EXAMPLES = '''
---
- name: Add a powershell module
  win_route:
    name: PowershellModule
    state: present

- name: Add a powershell module and register a repository
  win_psmodule:
    name: MyCustomModule
    repository: MyRepository
    url: https://myrepo.com
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
'''
