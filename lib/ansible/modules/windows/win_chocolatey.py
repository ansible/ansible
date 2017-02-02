#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Trond Hindenes <trond@hindenes.com>
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
                    'supported_by': 'curated'}


DOCUMENTATION = r'''
---
module: win_chocolatey
version_added: "1.9"
short_description: Installs packages using chocolatey
description:
    - Installs packages using Chocolatey (U(http://chocolatey.org/)).
    - If Chocolatey is missing from the system, the module will install it.
    - List of packages can be found at U(http://chocolatey.org/packages)
options:
  name:
    description:
      - Name of the package to be installed.
    required: true
  state:
    description:
      - State of the package on the system.
    choices:
      - present
      - absent
      - latest
      - reinstalled
    default: present
  force:
    description:
      - Forces install of the package (even if it already exists).
      - Using C(force) will cause ansible to always report that a change was made.
    choices:
      - yes
      - no
    default: no
  upgrade:
    description:
      - If package is already installed it, try to upgrade to the latest version or to the specified version.
      - As of Ansible v2.3 this is deprecated, set parameter C(state) to "latest" for the same result.
    choices:
      - yes
      - no
    default: no
  version:
    description:
      - Specific version of the package to be installed.
      - Ignored when C(state) is set to "absent".
  source:
    description:
      - Specify source rather than using default chocolatey repository.
  install_args:
    description:
      - Arguments to pass to the native installer.
    version_added: '2.1'
  params:
    description:
      - Parameters to pass to the package
    version_added: '2.1'
  allow_empty_checksums:
    description:
      - Allow empty checksums to be used.
    default: false
    version_added: '2.2'
  ignore_checksums:
    description:
      - Ignore checksums altogether.
    default: false
    version_added: '2.2'
  ignore_dependencies:
    description:
      - Ignore dependencies, only install/upgrade the package itself.
    default: false
    version_added: '2.1'
  timeout:
    description:
      - The time to allow chocolatey to finish before timing out.
    default: 2700
    version_added: '2.3'
    aliases: [ execution_timeout ]
author: "Trond Hindenes (@trondhindenes), Peter Mounce (@petemounce), Pepe Barbe (@elventear), Adam Keech (@smadam813)"
'''

# TODO:
# * Better parsing when a package has dependencies - currently fails
# * Time each item that is run
# * Support 'changed' with gems - would require shelling out to `gem list` first and parsing, kinda defeating the point of using chocolatey.

EXAMPLES = r'''
  # Install git
  win_chocolatey:
    name: git
    state: present

  # Upgrade installed packages
  win_chocolatey:
    name: all
    state: latest

  # Install notepadplusplus version 6.6
  win_chocolatey:
    name: notepadplusplus.install
    version: '6.6'

  # Install git from specified repository
  win_chocolatey:
    name: git
    source: https://someserver/api/v2/

  # Uninstall git
  win_chocolatey:
    name: git
    state: absent
'''
