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
    required: yes
  state:
    description:
      - Whether to add or remove the specified virtual directory.
    choices: [ absent, present ]
    default: present
  site:
    description:
      - The site name under which the virtual directory is created or exists.
    required: yes
  application:
    description:
      - The application under which the virtual directory is created or exists.
  physical_path:
    description:
      - The physical path to the folder in which the new virtual directory is created.
      - The specified folder must already exist.
author:
- Henrik Wallström
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
