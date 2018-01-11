#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Paul Durivage <paul.durivage@rackspace.com>, Trond Hindenes <trond@hindenes.com> and others
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_feature
version_added: "1.7"
short_description: Installs and uninstalls Windows Features on Windows Server
description:
     - Installs or uninstalls Windows Roles or Features on Windows Server. This module uses the Add/Remove-WindowsFeature Cmdlets on Windows 2008
       and Install/Uninstall-WindowsFeature Cmdlets on Windows 2012, which are not available on client os machines.
options:
  name:
    description:
      - Names of roles or features to install as a single feature or a comma-separated list of features
    required: true
  state:
    description:
      - State of the features or roles on the system
    choices:
      - present
      - absent
    default: present
  restart:
    description:
      - Restarts the computer automatically when installation is complete, if restarting is required by the roles or features installed.
      - DEPRECATED in Ansible 2.4, as unmanaged reboots cause numerous issues under Ansible. Check the C(reboot_required) return value
        from this module to determine if a reboot is necessary, and if so, use the M(win_reboot) action to perform it.
    choices:
      - yes
      - no
  include_sub_features:
    description:
      - Adds all subfeatures of the specified feature
    choices:
      - yes
      - no
  include_management_tools:
    description:
      - Adds the corresponding management tools to the specified feature.
      - Not supported in Windows 2008. If present when using Windows 2008 this option will be ignored.
    choices:
      - yes
      - no
  source:
    description:
      - Specify a source to install the feature from.
      - Not supported in Windows 2008. If present when using Windows 2008 this option will be ignored.
    choices: [ ' {driveletter}:\sources\sxs', ' {IP}\Share\sources\sxs' ]
    version_added: "2.1"
author:
    - "Paul Durivage (@angstwad)"
    - "Trond Hindenes (@trondhindenes)"
'''

EXAMPLES = r'''
- name: Install IIS (Web-Server only)
  win_feature:
    name: Web-Server
    state: present

- name: Install IIS (Web-Server and Web-Common-Http)
  win_feature:
    name: Web-Server,Web-Common-Http
    state: present

- name: Install NET-Framework-Core from file
  win_feature:
    name: NET-Framework-Core
    source: C:\Temp\iso\sources\sxs
    state: present

- name: Install IIS Web-Server with sub features and management tools
  win_feature:
    name: Web-Server
    state: present
    include_sub_features: True
    include_management_tools: True
  register: win_feature

- name: reboot if installing Web-Server feature requires it
  win_reboot:
  when: win_feature.reboot_required
'''

RETURN = r'''
exitcode:
    description: The stringified exit code from the feature installation/removal command
    returned: always
    type: string
    sample: Success
feature_result:
    description: List of features that were installed or removed
    returned: success
    type: complex
    sample:
    contains:
        display_name:
            description: Feature display name
            returned: always
            type: string
            sample: "Telnet Client"
        id:
            description: A list of KB article IDs that apply to the update
            returned: always
            type: int
            sample: 44
        message:
            description: Any messages returned from the feature subsystem that occurred during installation or removal of this feature
            returned: always
            type: list of strings
            sample: []
        reboot_required:
            description: True when the target server requires a reboot as a result of installing or removing this feature
            returned: always
            type: boolean
            sample: True
        restart_needed:
            description: DEPRECATED in Ansible 2.4 (refer to C(reboot_required) instead). True when the target server requires a reboot as a
                         result of installing or removing this feature
            returned: always
            type: boolean
            sample: True
        skip_reason:
            description: The reason a feature installation or removal was skipped
            returned: always
            type: string
            sample: NotSkipped
        success:
            description: If the feature installation or removal was successful
            returned: always
            type: boolean
            sample: True
reboot_required:
    description: True when the target server requires a reboot to complete updates (no further updates can be installed until after a reboot)
    returned: success
    type: boolean
    sample: True
restart_needed:
    description: DEPRECATED in Ansible 2.4 (refer to C(reboot_required) instead). True when the target server requires a reboot to complete updates
                 (no further updates can be installed until after a reboot)
    returned: success
    type: boolean
    sample: True
'''
