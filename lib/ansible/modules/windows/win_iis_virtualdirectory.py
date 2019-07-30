#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_iis_virtualdirectory
version_added: "2.0"
short_description: Configures a virtual directory in IIS
description:
     - Creates, Removes and configures a virtual directory in IIS.
options:
  name:
    description:
      - The name of the virtual directory to create or remove.
    type: str
    required: yes
  state:
    description:
      - Whether to add or remove the specified virtual directory.
      - Removing will remove the virtual directory and all under it (Recursively).
    type: str
    choices: [ absent, present ]
    default: present
  site:
    description:
      - The site name under which the virtual directory is created or exists.
    type: str
    required: yes
  application:
    description:
      - The application under which the virtual directory is created or exists.
    type: str
  physical_path:
    description:
      - The physical path to the folder in which the new virtual directory is created.
      - The specified folder must already exist.
    type: str
seealso:
- module: win_iis_webapplication
- module: win_iis_webapppool
- module: win_iis_webbinding
- module: win_iis_website
author:
- Henrik Wallström (@henrikwallstrom)
'''

EXAMPLES = r'''
- name: Create a virtual directory if it does not exist
  win_iis_virtualdirectory:
    name: somedirectory
    site: somesite
    state: present
    physical_path: C:\virtualdirectory\some

- name: Remove a virtual directory if it exists
  win_iis_virtualdirectory:
    name: somedirectory
    site: somesite
    state: absent

- name: Create a virtual directory on an application if it does not exist
  win_iis_virtualdirectory:
    name: somedirectory
    site: somesite
    application: someapp
    state: present
    physical_path: C:\virtualdirectory\some
'''
