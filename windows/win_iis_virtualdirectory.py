#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
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

DOCUMENTATION = '''
---
module: win_iis_virtualdirectory
version_added: "1.9"
short_description: Configures a IIS virtual directories.
description:
     - Creates, Removes and configures a IIS Web site
options:
  name:
    description:
      - The name of the virtual directory to create.
    required: true
    default: null
    aliases: []
  state:
    description:
      -
    choices:
      - absent
      - present
    required: false
    default: null
    aliases: []
  site:
    description:
      - The site name under which the virtual directory is created or exists.
    required: false
    default: null
    aliases: []
  application:
    description:
      - The application under which the virtual directory is created or exists.
    required: false
    default: null
    aliases: []
  physical_path:
    description:
      - The physical path to the folder in which the new virtual directory is created. The specified folder must already exist.
    required: false
    default: null
    aliases: []
author: Henrik Wallström
'''

EXAMPLES = '''

'''
