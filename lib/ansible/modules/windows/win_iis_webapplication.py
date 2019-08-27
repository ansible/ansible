#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
    type: str
    required: yes
  site:
    description:
    - Name of the site on which the application is created.
    type: str
    required: yes
  state:
    description:
    - State of the web application.
    type: str
    choices: [ absent, present ]
    default: present
  physical_path:
    description:
    - The physical path on the remote host to use for the new application.
    - The specified folder must already exist.
    type: str
  application_pool:
    description:
    - The application pool in which the new site executes.
    type: str
seealso:
- module: win_iis_virtualdirectory
- module: win_iis_webapppool
- module: win_iis_webbinding
- module: win_iis_website
author:
- Henrik Wallström (@henrikwallstrom)
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
    description: The used/implemented application_pool value.
    returned: success
    type: str
    sample: DefaultAppPool
physical_path:
    description: The used/implemented physical_path value.
    returned: success
    type: str
    sample: C:\apps\acme\api
'''
