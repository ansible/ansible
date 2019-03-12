#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Carson Anderson <rcanderson23@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_optional_feature
version_added: "2.8"
short_description: Installs and uninstalls Optional Windows Features on Windows
description:
    - Installs or uninstalls Windows Features on non-Server Windows.
    - This module uses the Enable/Disable-WindowsOptionalFeature Cmdlets
options:
  name:
    description:
      - FeatureName of feature to install.
      - To list all available features use the PowerShell command C(Get-WindowsOptionalFeature).
    type: str
    required: yes
  state:
    description:
      - State of the feature on the system.
    type: str
    choices: [ absent, present ]
    default: present
  include_parent:
    description:
      - Enables the parent feature and the parent's dependencies
    type: bool
    default: no
  source:
    description:
      - Specify a source to install the feature from.
      - Can either be C({driveletter}:\sources\sxs) or C(\\{IP}\share\sources\sxs).
    type: str
seealso:
- module: win_chocolatey
- module: win_package
author:
    - Carson Anderson (@rcanderson23)
'''

EXAMPLES = r'''
- name: Install .Net 3.5
  win_optional_feature:
    name: NetFx3
    state: present

- name: Install .Net 3.5 from source
  win_optional_feature:
    name: NetFx3
    source: \\share01\win10\sources\sxs
    state: present

- name: Install Microsoft Subsystem for Linux
  win_optional_feature:
    name: Microsoft-Windows-Subsystem-Linux
    state: present
  register: win_optional_feature

- name: Reboot if installing Linux Subsytem as feature requires it
  win_reboot:
  when: win_optional_feature.reboot_required
'''

RETURN = r'''
rc:
    description: The exit code from the feature installation/removal command.
    returned: always
    type: int
    sample: Success
feature_result:
    description: List of features that were installed or removed.
    returned: always
    type: complex
    sample:
    contains:
        name:
            description: Feature name.
            returned: always
            type: str
            sample: "NetFx3"
        display_name:
            description: Feature display name.
            returned: always
            type: str
            sample: ".NET Framework 3.5 (includes .NET 2.0 and 3.0)"
        description:
            description: Description of feature
            returned: always
            type: str
            sample: ".NET Framework 3.5 (includes .NET 2.0 and 3.0)"
        state:
            description: Whether the feature is enabled or disabled
            returned: always
            type: str
            sample: "Enabled"
reboot_required:
    description: True when the target server requires a reboot to complete updates
    returned: success
    type: bool
    sample: true
'''
