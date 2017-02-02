#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Anatoliy Ivashina <tivrobo@gmail.com>
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_git
version_added: "2.0"
short_description: Deploy software (or files) from git checkouts
description:
    - Deploy software (or files) from git checkouts
    - SSH only
notes:
    - git for Windows need to be installed
    - SSH only
options:
  name:
    description:
      - address of the repository
    required: true
  dest:
    description:
      - destination folder
    required: true
  replace_dest:
    description:
      - replace destination folder if exists (recursive!)
    default: false
  accept_hostkey:
    description:
      - add hostkey to known_hosts (before connecting to git)
    default: false
author: Anatoliy Ivashina
'''

EXAMPLES = '''
  # git clone cool-thing.
  win_git:
    name: "git@github.com:tivrobo/Ansible-win_git.git"
    dest: "{{ ansible_env.TEMP }}\\Ansible-win_git"
    replace_dest: no
    accept_hostkey: yes

'''

ANSIBLE_METADATA = {
    'version': '0.1',
    'supported_by': 'unmaintained',
    'status': ['preview']
}