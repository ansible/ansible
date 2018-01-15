#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2015, Matt Davis <mdavis_ansible@rolpdog.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
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
    reboot:
        description:
        - Ansible will automatically reboot the remote host if it is required
          and continue to install updates after the reboot.
        - This can be used instead of using a M(win_reboot) task after this one
          and ensures all updates for that category is installed in one go.
        - Async does not work when C(reboot=True).
        type: bool
        default: 'no'
        version_added: '2.5'
    reboot_timeout:
        description:
        - The time in seconds to wait until the host is back online from a
          reboot.
        - This is only used if C(reboot=True) and a reboot is required.
        default: 1200
        version_added: '2.5'
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
        - If set, C(win_updates) will append update progress to the specified file. The directory must already exist.
        required: false
author: "Matt Davis (@nitzmahone)"
notes:
- C(win_updates) must be run by a user with membership in the local Administrators group.
- C(win_updates) will use the default update service configured for the machine (Windows Update, Microsoft Update, WSUS, etc).
- By default C(win_updates) does not manage reboots, but will signal when a
  reboot is required with the I(reboot_required) return value, as of Ansible 2.5
  C(reboot) can be used to reboot the host if required in the one task.
- C(win_updates) can take a significant amount of time to complete (hours, in some cases).
  Performance depends on many factors, including OS version, number of updates, system load, and update server load.
'''

EXAMPLES = r'''
- name: Install all security, critical, and rollup updates
  win_updates:
    category_names:
      - SecurityUpdates
      - CriticalUpdates
      - UpdateRollups

- name: Install only security updates
  win_updates:
    category_names: SecurityUpdates

- name: Search-only, return list of found updates (if any), log to c:\ansible_wu.txt
  win_updates:
    category_names: SecurityUpdates
    state: searched
    log_path: c:\ansible_wu.txt

- name: Install all security updates with automatic reboots
  win_updates:
    category_names:
    - SecurityUpdates
    reboot: yes

# Note async on works on Windows Server 2012 or newer - become must be explicitly set on the task for this to work
- name: Search for Windows updates asynchronously
  win_updates:
    category_names:
    - SecurityUpdates
    state: searched
  async: 180
  poll: 10
  register: updates_to_install
  become: yes
  become_method: runas
  become_user: SYSTEM

# Async can also be run in the background in a fire and forget fashion
- name: Search for Windows updates asynchronously (poll and forget)
  win_updates:
    category_names:
    - SecurityUpdates
    state: searched
  async: 180
  poll: 0
  register: updates_to_install_async

- name: get status of Windows Update async job
  async_status:
    jid: '{{ updates_to_install_async.ansible_job_id }}'
  register: updates_to_install_result
  become: yes
  become_method: runas
  become_user: SYSTEM
'''

RETURN = r'''
reboot_required:
    description: True when the target server requires a reboot to complete updates (no further updates can be installed until after a reboot)
    returned: success
    type: boolean
    sample: True

updates:
    description: List of updates that were found/installed
    returned: success
    type: complex
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
