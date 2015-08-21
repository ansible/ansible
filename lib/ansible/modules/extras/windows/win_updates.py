#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Matt Davis <mdavis_ansible@rolpdog.com>
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

DOCUMENTATION = '''
---
module: win_updates
version_added: "2.0"
short_description: Download and install Windows updates
description:
    - Searches, downloads, and installs Windows updates synchronously by automating the Windows Update client
options:
    category_names:
        description:
        - A scalar or list of categories to install updates from
        required: false
        default: ["CriticalUpdates","SecurityUpdates","UpdateRollups"]
        choices:
        - Application
        - Connectors
        - CriticalUpdates
        - DefinitionUpdates
        - DeveloperKits
        - FeaturePacks
        - Guidance
        - SecurityUpdates
        - ServicePacks
        - Tools
        - UpdateRollups
        - Updates
    state:
        description:
        - Controls whether found updates are returned as a list or actually installed.
        - This module also supports Ansible check mode, which has the same effect as setting state=searched
        required: false
        default: installed
        choices:
        - installed
        - searched
    log_path: 
        description:
        - If set, win_updates will append update progress to the specified file. The directory must already exist.
        required: false
author: "Matt Davis (@mattdavispdx)"
notes:
- win_updates must be run by a user with membership in the local Administrators group
- win_updates will use the default update service configured for the machine (Windows Update, Microsoft Update, WSUS, etc)
- win_updates does not manage reboots, but will signal when a reboot is required with the reboot_required return value.
- win_updates can take a significant amount of time to complete (hours, in some cases). Performance depends on many factors, including OS version, number of updates, system load, and update server load.
'''

EXAMPLES = '''
    # Install all security, critical, and rollup updates
    win_updates:
        category_names: ['SecurityUpdates','CriticalUpdates','UpdateRollups']

    # Install only security updates
    win_updates: category_names=SecurityUpdates

    # Search-only, return list of found updates (if any), log to c:\ansible_wu.txt
    win_updates: category_names=SecurityUpdates status=searched log_path=c:/ansible_wu.txt
'''

RETURN = '''
reboot_required:
    description: True when the target server requires a reboot to complete updates (no further updates can be installed until after a reboot)
    returned: success
    type: boolean
    sample: True

updates:
    description: List of updates that were found/installed 
    returned: success
    type: dictionary
    sample: 
    contains: 
        title:
            description: Display name
            returned: always
            type: string
            sample: "Security Update for Windows Server 2012 R2 (KB3004365)"
        kb:
            description: A list of KB article IDs that apply to the update
            returned: always
            type: list of strings
            sample: [ '3004365' ]
        id:
            description: Internal Windows Update GUID
            returned: always
            type: string (guid)
            sample: "fb95c1c8-de23-4089-ae29-fd3351d55421"
        installed:
            description: Was the update successfully installed
            returned: always
            type: boolean
            sample: True
        failure_hresult_code:
            description: The HRESULT code from a failed update
            returned: on install failure
            type: boolean
            sample: 2147942402

found_update_count:
    description: The number of updates found needing to be applied
    returned: success
    type: int
    sample: 3
installed_update_count:
    description: The number of updates successfully installed
    returned: success
    type: int
    sample: 2
failed_update_count:
    description: The number of updates that failed to install
    returned: always
    type: int
    sample: 0
'''
