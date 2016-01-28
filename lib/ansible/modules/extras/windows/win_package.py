#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Trond Hindenes <trond@hindenes.com>, and others
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
module: win_package
version_added: "1.7"
author: Trond Hindenes
short_description: Installs/Uninstalls a installable package, either from local file system or url
description:
     - Installs or uninstalls a package
options:
  path:
    description:
      - Location of the package to be installed (either on file system, network share or url)
    required: true
    default: null
    aliases: []
  name:
    description:
      - name of the package. Just for logging reasons, will use the value of path if name isn't specified
    required: false
    default: null
    aliases: []
  product_id:
    description:
      - product id of the installed package (used for checking if already installed)
    required: true
    default: null
    aliases: [productid]
  arguments:
    description:
      - Any arguments the installer needs
    default: null
    aliases: []
  state:
    description:
      - Install or Uninstall
    choices:
      - present
      - absent
    default: present
    aliases: [ensure]
  user_name:
    description:
      - Username of an account with access to the package if its located on a file share. Only needed if the winrm user doesn't have access to the package. Also specify user_password for this to function properly.
    default: null
    aliases: []
  user_password:
    description:
      - Password of an account with access to the package if its located on a file share. Only needed if the winrm user doesn't have access to the package. Also specify user_name for this to function properly.
    default: null
    aliases: []
'''

EXAMPLES = '''
# Playbook example
  - name: Install the vc thingy
    win_package:
      name="Microsoft Visual C thingy"
      path="http://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe"
      Product_Id="{CF2BEA3C-26EA-32F8-AA9B-331F7E34BA97}"
      Arguments="/install /passive /norestart"


'''

