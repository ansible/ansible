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
module: win_iis_webapplication
version_added: "2.0"
short_description: Configures a IIS Web application.
description:
     - Creates, Removes and configures a IIS Web applications
options:
  name:
    description:
      - Name of the Web applicatio
    required: true
    default: null
    aliases: []
  site:
    description:
      - Name of the site on which the application is created.
    required: true
    default: null
    aliases: []
  state:
    description:
      - State of the web application
    choices:
      - present
      - absent
    required: false
    default: null
    aliases: []
  physical_path:
    description:
      - The physical path on the remote host to use for the new applicatiojn. The specified folder must already exist.
    required: false
    default: null
    aliases: []
  application_pool:
    description:
      - The application pool in which the new site executes.
    required: false
    default: null
    aliases: []
author: Henrik Wallström
'''

EXAMPLES = '''
$ ansible -i hosts -m win_iis_webapplication -a "name=api site=acme physical_path=c:\\apps\\acme\\api" host

'''
