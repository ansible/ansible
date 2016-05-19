#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Paul Durivage <paul.durivage@rackspace.com>, Trond Hindenes <trond@hindenes.com> and others
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

DOCUMENTATION = '''
---
module: win_feature
version_added: "1.7"
short_description: Installs and uninstalls Windows Features
description:
     - Installs or uninstalls Windows Roles or Features
options:
  name:
    description:
      - Names of roles or features to install as a single feature or a comma-separated list of features
    required: true
    default: null
  state:
    description:
      - State of the features or roles on the system
    required: false
    choices:
      - present
      - absent
    default: present
  restart:
    description:
      - Restarts the computer automatically when installation is complete, if restarting is required by the roles or features installed.
    choices:
      - yes
      - no
    default: null
    required: false
  include_sub_features:
    description:
      - Adds all subfeatures of the specified feature
    choices:
      - yes
      - no
    default: null
    required: false
  include_management_tools:
    description:
      - Adds the corresponding management tools to the specified feature
    choices:
      - yes
      - no
    default: null
    required: false
  source:
    description:
      - Specify a source to install the feature from
    required: false
    choices: [ ' {driveletter}:\sources\sxs', ' {IP}\Share\sources\sxs' ]
    version_added: "2.1"
author:
    - "Paul Durivage (@angstwad)"
    - "Trond Hindenes (@trondhindenes)"
'''

EXAMPLES = r'''
# This installs IIS.
# The names of features available for install can be run by running the following Powershell Command:
# PS C:\Users\Administrator> Import-Module ServerManager; Get-WindowsFeature
$ ansible -i hosts -m win_feature -a "name=Web-Server" all
$ ansible -i hosts -m win_feature -a "name=Web-Server,Web-Common-Http" all
ansible -m "win_feature" -a "name=NET-Framework-Core source=C:/Temp/iso/sources/sxs" windows


# Playbook example
---
- name: Install IIS
  hosts: all
  gather_facts: false
  tasks:
    - name: Install IIS
      win_feature:
        name: "Web-Server"
        state: present
        restart: yes
        include_sub_features: yes
        include_management_tools: yes
'''
