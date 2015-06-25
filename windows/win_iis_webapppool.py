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
      - Application Pool attributes from string where attributes are seperated by a pipe and attribute name/values by colon Ex. "foo:1|bar:2"
    required: false
    default: null
    aliases: []
author: Henrik Wallström
'''

EXAMPLES = '''
# This return information about an existing application pool
$ansible -i inventory -m win_iis_webapppool -a "name='DefaultAppPool'" windows
host | success >> {
    "attributes": {},
    "changed": false,
    "info": {
        "attributes": {
            "CLRConfigFile": "",
            "applicationPoolSid": "S-1-5-82-3006700770-424185619-1745488364-794895919-4004696415",
            "autoStart": true,
            "enable32BitAppOnWin64": false,
            "enableConfigurationOverride": true,
            "managedPipelineMode": 0,
            "managedRuntimeLoader": "webengine4.dll",
            "managedRuntimeVersion": "v4.0",
            "name": "DefaultAppPool",
            "passAnonymousToken": true,
            "queueLength": 1000,
            "startMode": 0,
            "state": 1
        },
        "name": "DefaultAppPool",
        "state": "Started"
    }
}

# This creates a new application pool in 'Started' state
$  ansible -i inventory -m win_iis_webapppool -a "name='AppPool' state=started" windows

# This stoppes an application pool
$  ansible -i inventory -m win_iis_webapppool -a "name='AppPool' state=stopped" windows

# This restarts an application pool
$  ansible -i inventory -m win_iis_webapppool -a "name='AppPool' state=restart" windows

# This restarts an application pool
$  ansible -i inventory -m win_iis_webapppool -a "name='AppPool' state=restart" windows

# This change application pool attributes without touching state
$  ansible -i inventory -m win_iis_webapppool -a "name='AppPool' attributes='managedRuntimeVersion:v4.0|autoStart:false'" windows

# This creates an application pool and sets attributes
$  ansible -i inventory -m win_iis_webapppool -a "name='AnotherAppPool' state=started attributes='managedRuntimeVersion:v4.0|autoStart:false'" windows


# Playbook example
---

- name: App Pool with .NET 4.0
  win_iis_webapppool:
    name: 'AppPool'
    state: started
    attributes: managedRuntimeVersion:v4.0
  register: webapppool

'''
