#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Red Hat, Inc
# Written by Seth Vidal <skvidal at fedoraproject.org>
# (c) 2014, Epic Games, Inc.
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
#

DOCUMENTATION = '''
---
module: package
version_added: 2.0
author: Ansible Core Team
short_description: Generic OS package manager
description:
     - Installs, upgrade and removes packages using the underlying OS package manager.
options:
  name:
    description:
      - "Package name, or package specifier with version, like C(name-1.0). When using state=latest, this can be '*' which means run: yum -y update. You can also pass a url or a local path to a rpm file.  To operate on several packages this can accept a comma separated list of packages or (as of 2.0) a list of packages."
    required: true
  state:
    description:
      - Whether to install (C(present), C(latest)), or remove (C(absent)) a package.
    required: true
requirements:
    - Whatever is required for the package plugins specific for each system.
notes:
    - This module actually calls the pertinent package modules for each system (apt, yum, etc).
'''
EXAMPLES = '''
- name: install the latest version of Vim
  package: name=vim-minimal state=latest

- name: remove the Vim package
  package : name=vim-minimal state=absent
'''
