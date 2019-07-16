#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Paul Durivage <paul.durivage@rackspace.com>
# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
    - Installs or uninstalls Windows Roles or Features on Windows Server.
    - This module uses the Add/Remove-WindowsFeature Cmdlets on Windows 2008 R2
      and Install/Uninstall-WindowsFeature Cmdlets on Windows 2012, which are not available on client os machines.
options:
  name:
    description:
      - Names of roles or features to install as a single feature or a comma-separated list of features.
      - To list all available features use the PowerShell command C(Get-WindowsFeature).
    type: list
    required: yes
  state:
    description:
      - State of the features or roles on the system.
    type: str
    choices: [ absent, present ]
    default: present
  include_sub_features:
    description:
      - Adds all subfeatures of the specified feature.
    type: bool
    default: no
  include_management_tools:
    description:
      - Adds the corresponding management tools to the specified feature.
      - Not supported in Windows 2008 R2 and will be ignored.
    type: bool
    default: no
  source:
    description:
      - Specify a source to install the feature from.
      - Not supported in Windows 2008 R2 and will be ignored.
      - Can either be C({driveletter}:\sources\sxs) or C(\\{IP}\share\sources\sxs).
    type: str
    version_added: "2.1"
seealso:
- module: win_chocolatey
- module: win_package
author:
    - Paul Durivage (@angstwad)
    - Trond Hindenes (@trondhindenes)
'''

EXAMPLES = r'''
- name: Install IIS (Web-Server only)
  win_feature:
    name: Web-Server
    state: present

- name: Install IIS (Web-Server and Web-Common-Http)
  win_feature:
    name:
    - Web-Server
    - Web-Common-Http
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
    include_sub_features: yes
    include_management_tools: yes
  register: win_feature

- name: Reboot if installing Web-Server feature requires it
  win_reboot:
  when: win_feature.reboot_required
'''

RETURN = r'''
exitcode:
    description: The stringified exit code from the feature installation/removal command.
    returned: always
    type: str
    sample: Success
feature_result:
    description: List of features that were installed or removed.
    returned: success
    type: complex
    sample:
    contains:
        display_name:
            description: Feature display name.
            returned: always
            type: str
            sample: "Telnet Client"
        id:
            description: A list of KB article IDs that apply to the update.
            returned: always
            type: int
            sample: 44
        message:
            description: Any messages returned from the feature subsystem that occurred during installation or removal of this feature.
            returned: always
            type: list of strings
            sample: []
        reboot_required:
            description: True when the target server requires a reboot as a result of installing or removing this feature.
            returned: always
            type: bool
            sample: true
        restart_needed:
            description: DEPRECATED in Ansible 2.4 (refer to C(reboot_required) instead). True when the target server requires a reboot as a
                         result of installing or removing this feature.
            returned: always
            type: bool
            sample: true
        skip_reason:
            description: The reason a feature installation or removal was skipped.
            returned: always
            type: str
            sample: NotSkipped
        success:
            description: If the feature installation or removal was successful.
            returned: always
            type: bool
            sample: true
reboot_required:
    description: True when the target server requires a reboot to complete updates (no further updates can be installed until after a reboot).
    returned: success
    type: bool
    sample: true
'''
