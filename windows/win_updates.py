#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Peter Mounce <public@neverrunwithscissors.com>
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
module: win_updates
version_added: "1.9"
short_description: Lists / Installs windows updates
description:
    - Installs windows updates using PSWindowsUpdate (http://gallery.technet.microsoft.com/scriptcenter/2d191bcd-3308-4edd-9de2-88dff796b0bc).
    - PSWindowsUpdate needs to be installed first - use win_chocolatey.
options:
  category:
    description:
      - Which category to install updates from
    required: false
    default: critical
    choices:
      - critical
      - security
      - (anything that is a valid update category)
    default: critical
    aliases: []
author: Peter Mounce
'''

EXAMPLES = '''
  # Install updates from security category
  win_updates:
    category: security
'''
