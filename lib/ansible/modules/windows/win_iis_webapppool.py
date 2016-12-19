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


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: win_iis_webapppool
version_added: "2.0"
short_description: Configures a IIS Web Application Pool.
description:
     - Creates, Removes and configures a IIS Web Application Pool
options:
  name:
    description:
      - Names of application pool
    required: true
    default: null
    aliases: []
  state:
    description:
      - State of the binding
    choices:
      - absent
      - stopped
      - started
      - restarted
    required: false
    default: null
    aliases: []
  attributes:
    description:
      - Application Pool attributes from string where attributes are separated by a pipe and attribute name/values by colon Ex. "foo:1|bar:2"
    required: false
    default: null
    aliases: []
author: Henrik Wallström
'''

EXAMPLES = '''
- name: Return information about an existing application pool
  win_iis_webapppool:
    name: DefaultAppPool

- name: Ensure AppPool is started
  win_iis_webapppool:
    name: AppPool
    state: started

- name: Ensure AppPool is stopped
  win_iis_webapppool:
    name: AppPool
    state: stopped

- name: Restart AppPool
  win_iis_webapppool:
    name: AppPool
    state: restart

- name: Change application pool attributes without touching state
  win_iis_webapppool:
    name: AppPool
    attributes: managedRuntimeVersion:v4.0|autoStart:false

- name: Create AnotherAppPool and start it using .NET 4.0 and disabling autostart
  win_iis_webapppool:
    name: AnotherAppPool
    state: started
    attributes: managedRuntimeVersion:v4.0|autoStart:false

- name: Create AppPool and start it using .NET 4.0
  win_iis_webapppool:
    name: AppPool
    state: started
    attributes: managedRuntimeVersion:v4.0
  register: webapppool
'''
