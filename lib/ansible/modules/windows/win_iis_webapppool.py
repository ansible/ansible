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
module: win_iis_webapppool
version_added: "2.0"
short_description: Configures an IIS Web Application Pool.
description:
     - Creates, Removes and configures an IIS Web Application Pool
options:
  name:
    description:
      - Name of application pool
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
  attributes:
    description:
      - Application Pool attributes from string where attributes are separated by a pipe and attribute name/values by colon Ex. "foo:1|bar:2".
      - The following attributes may only have the following names.
      - managedPipelineMode may be either "Integrated" or  "Classic".
      - startMode may be either "OnDemand" or  "AlwaysRunning".
      - state may be one of "Starting", "Started", "Stopping", "Stopped", "Unknown".
        Use the C(state) module parameter to modify, states shown are reflect the possible runtime values.
    required: false
    default: null
author: Henrik Wallström
'''

EXAMPLES = r'''
- name: return information about an existing application pool
  win_iis_webapppool:
    name: DefaultAppPool

- name: Create a new application pool in 'Started' state
  win_iis_webapppool:
    name: AppPool
    state: started

- name: Stop an application pool
  win_iis_webapppool:
    name: AppPool
    state: stopped

- name: Restart an application pool
  win_iis_webapppool:
    name: AppPool
    state: restart

- name: Changes application pool attributes without touching state
  win_iis_webapppool:
    name: AppPool
    attributes: 'managedRuntimeVersion:v4.0|autoStart:false'

- name: Creates an application pool and sets attributes
  win_iis_webapppool:
    name: AnotherAppPool
    state: started
    attributes: 'managedRuntimeVersion:v4.0|autoStart:false'

# Playbook example
---

- name: App Pool with .NET 4.0
  win_iis_webapppool:
    name: 'AppPool'
    state: started
    attributes: managedRuntimeVersion:v4.0
  register: webapppool

'''

RETURN = '''
attributes:
  description:
    - Application Pool attributes from that were processed by this module invocation.
  returned: success
  type: dictionary
  sample:
     "enable32BitAppOnWin64": "true"
     "managedRuntimeVersion": "v4.0"
     "managedPipelineMode": "Classic"
info:
  description: Information on current state of the Application Pool
  returned: success
  type: dictionary
  sample:
  contains:
    attributes:
      description: key value pairs showing the current Application Pool attributes
      returned: success
      type: dictionary
      sample:
            "autoStart": true
            "managedRuntimeLoader": "webengine4.dll"
            "managedPipelineMode": "Classic"
            "name": "DefaultAppPool"
            "CLRConfigFile": ""
            "passAnonymousToken": true
            "applicationPoolSid": "S-1-5-82-1352790163-598702362-1775843902-1923651883-1762956711"
            "queueLength": 1000
            "managedRuntimeVersion": "v4.0"
            "state": "Started"
            "enableConfigurationOverride": true
            "startMode": "OnDemand"
            "enable32BitAppOnWin64": true
    name:
      description:
        - Name of Application Pool that was processed by this module invocation.
      returned: success
      type: string
      sample: "DefaultAppPool"
    state:
      description:
        - Current runtime state of the pool as the module completed.
      returned: success
      type: string
      sample: "Started"
'''

