#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Trond Hindenes <trond@hindenes.com>, and others
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
module: win_dsc
version_added: "2.4"
short_description: Invokes a PowerShell DSC configuration
description: |
     Invokes a PowerShell DSC Configuration. Requires PowerShell version 5 (February release or newer). Note that most of the parameters are dynamic and will vary
     depending on the DSC Resource. If the DSC resource takes a parameter named "Name", use the parameter "item_name" in Ansible to represent it.
     Also note that credentials are handled as follows: If the resource accepts a credential type property called "cred", the ansible parameters would be cred_username and cred_password.
     These will be used to inject a credential object on the fly for the DSC resource.
options:
  resource_name:
    description:
      - The DSC Resource to use. Must be accessible to PowerShell using any of the default paths.
    required: true
    default: null
author: Trond Hindenes
'''

EXAMPLES = '''
# Playbook example
  - name: Extract zip file
    win_dsc5:
      resource_name="archive"
      ensure="Present"
      path="C:\Temp\zipfile.zip"
      destination="C:\Temp\Temp2"
'''
