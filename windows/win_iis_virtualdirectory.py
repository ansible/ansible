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
version_added: "2.0"
short_description: Configures a virtual directory in IIS.
description:
     - Creates, Removes and configures a virtual directory in IIS.
options:
  name:
    description:
      - The name of the virtual directory to create or remove
    required: true
  state:
    description:
      - Whether to add or remove the specified virtual directory
    choices:
      - absent
      - present
    required: false
    default: present
  site:
    description:
      - The site name under which the virtual directory is created or exists.
    required: true
  application:
    description:
      - The application under which the virtual directory is created or exists.
    required: false
    default: null
  physical_path:
    description:
      - The physical path to the folder in which the new virtual directory is created. The specified folder must already exist.
    required: false
    default: null
author: Henrik Wallström
'''

EXAMPLES = '''
# This creates a virtual directory if it doesn't exist.
$ ansible -i hosts -m win_iis_virtualdirectory -a "name='somedirectory' site=somesite state=present physical_path=c:\\virtualdirectory\\some" host

# This removes a virtual directory if it exists.
$ ansible -i hosts -m win_iis_virtualdirectory -a "name='somedirectory' site=somesite state=absent" host

# This creates a virtual directory on an application if it doesn't exist.
$ ansible -i hosts -m win_iis_virtualdirectory -a "name='somedirectory' site=somesite application=someapp state=present physical_path=c:\\virtualdirectory\\some" host
'''
