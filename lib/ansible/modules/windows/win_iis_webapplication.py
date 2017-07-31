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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_iis_webapplication
version_added: "2.0"
short_description: Configures IIS web applications
description:
- Creates, removes, and configures IIS web applications.
options:
  name:
    description:
    - Name of the web application.
    required: true
  site:
    description:
    - Name of the site on which the application is created.
    required: true
  state:
    description:
    - State of the web application.
    choices: [ absent, present ]
    default: present
  physical_path:
    description:
    - The physical path on the remote host to use for the new application.
    - The specified folder must already exist.
  application_pool:
    description:
    - The application pool in which the new site executes.
author:
- Henrik Wallström
'''

EXAMPLES = r'''
- name: Add ACME webapplication on IIS.
  win_iis_webapplication:
    name: api
    site: acme
    state: present
    physical_path: C:\apps\acme\api
'''

RETURN = r'''
application_pool:
    description: The used/implemented application_pool value
    returned: success
    type: string
    sample: DefaultAppPool
physical_path:
    description: The used/implemented physical_path value
    returned: success
    type: string
    sample: C:\apps\acme\api
'''
