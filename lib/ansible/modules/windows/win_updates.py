#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Matt Davis <mdavis_ansible@rolpdog.com>
# Copyright: (c) 2017, Ansible Project
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
    - Searches, downloads, and installs Windows updates synchronously by automating the Windows Update client.
options:
    blacklist:
        description:
        - A list of update titles or KB numbers that can be used to specify
          which updates are to be excluded from installation.
        - If an available update does match one of the entries, then it is
          skipped and not installed.
        - Each entry can either be the KB article or Update title as a regex
          according to the PowerShell regex rules.
        type: list
        version_added: '2.5'
    category_names:
        description:
        - A scalar or list of categories to install updates from. To get the list
          of categories, run the module with C(state=searched). The category must
          be the full category string, but is case insensitive.
        - Some possible categories are Application, Connectors, Critical Updates,
          Definition Updates, Developer Kits, Feature Packs, Guidance, Security
          Updates, Service Packs, Tools, Update Rollups and Updates.
        type: list
        default: [ CriticalUpdates, SecurityUpdates, UpdateRollups ]
    reboot:
        description:
        - Ansible will automatically reboot the remote host if it is required
          and continue to install updates after the reboot.
        - This can be used instead of using a M(win_reboot) task after this one
          and ensures all updates for that category is installed in one go.
        - Async does not work when C(reboot=yes).
        type: bool
        default: no
        version_added: '2.5'
    reboot_timeout:
        description:
        - The time in seconds to wait until the host is back online from a
          reboot.
        - This is only used if C(reboot=yes) and a reboot is required.
        default: 1200
        version_added: '2.5'
    server_selection:
        description:
        - Defines the Windows Update source catalog.
        - C(default) Use the default search source. For many systems default is
          set to the Microsoft Windows Update catalog. Systems participating in
          Windows Server Update Services (WSUS), Systems Center Configuration
          Manager (SCCM), or similar corporate update server environments may
          default to those managed update sources instead of the Windows Update
          catalog.
        - C(managed_server) Use a managed server catalog. For environments
          utilizing Windows Server Update Services (WSUS), Systems Center
          Configuration Manager (SCCM), or similar corporate update servers, this
          option selects the defined corporate update source.
        - C(windows_update) Use the Microsoft Windows Update catalog.
        type: str
        choices: [ default, managed_server, windows_update ]
        default: default
        version_added: '2.8'
    state:
        description:
        - Controls whether found updates are returned as a list or actually installed.
        - This module also supports Ansible check mode, which has the same effect as setting state=searched
        type: str
        choices: [ installed, searched ]
        default: installed
    log_path:
        description:
        - If set, C(win_updates) will append update progress to the specified file. The directory must already exist.
        type: path
    whitelist:
        description:
        - A list of update titles or KB numbers that can be used to specify
          which updates are to be searched or installed.
        - If an available update does not match one of the entries, then it
          is skipped and not installed.
        - Each entry can either be the KB article or Update title as a regex
          according to the PowerShell regex rules.
        - The whitelist is only validated on updates that were found based on
          I(category_names). It will not force the module to install an update
          if it was not in the category specified.
        type: list
        version_added: '2.5'
    use_scheduled_task:
        description:
        - Will not auto elevate the remote process with I(become) and use a
          scheduled task instead.
        - Set this to C(yes) when using this module with async on Server 2008,
          2008 R2, or Windows 7, or on Server 2008 that is not authenticated
          with basic or credssp.
        - Can also be set to C(yes) on newer hosts where become does not work
          due to further privilege restrictions from the OS defaults.
        type: bool
        default: no
        version_added: '2.6'
notes:
- C(win_updates) must be run by a user with membership in the local Administrators group.
- C(win_updates) will use the default update service configured for the machine (Windows Update, Microsoft Update, WSUS, etc).
- By default C(win_updates) does not manage reboots, but will signal when a
  reboot is required with the I(reboot_required) return value, as of Ansible v2.5
  C(reboot) can be used to reboot the host if required in the one task.
- C(win_updates) can take a significant amount of time to complete (hours, in some cases).
  Performance depends on many factors, including OS version, number of updates, system load, and update server load.
- Beware that just after C(win_updates) reboots the system, the Windows system may not have settled yet
  and some base services could be in limbo. This can result in unexpected behavior.
  Check the examples for ways to mitigate this.
- More information about PowerShell and how it handles RegEx strings can be
  found at U(https://technet.microsoft.com/en-us/library/2007.11.powershell.aspx).
seealso:
- module: win_chocolatey
- module: win_feature
- module: win_hotfix
- module: win_package
author:
- Matt Davis (@nitzmahone)
'''

EXAMPLES = r'''
- name: Install all security, critical, and rollup updates without a scheduled task
  win_updates:
    category_names:
      - SecurityUpdates
      - CriticalUpdates
      - UpdateRollups

- name: Install only security updates as a scheduled task for Server 2008
  win_updates:
    category_names: SecurityUpdates
    use_scheduled_task: yes

- name: Search-only, return list of found updates (if any), log to C:\ansible_wu.txt
  win_updates:
    category_names: SecurityUpdates
    state: searched
    log_path: C:\ansible_wu.txt

- name: Install all security updates with automatic reboots
  win_updates:
    category_names:
    - SecurityUpdates
    reboot: yes

- name: Install only particular updates based on the KB numbers
  win_updates:
    category_name:
    - SecurityUpdates
    whitelist:
    - KB4056892
    - KB4073117

- name: Exclude updates based on the update title
  win_updates:
    category_name:
    - SecurityUpdates
    - CriticalUpdates
    blacklist:
    - Windows Malicious Software Removal Tool for Windows
    - \d{4}-\d{2} Cumulative Update for Windows Server 2016

# One way to ensure the system is reliable just after a reboot, is to set WinRM to a delayed startup
- name: Ensure WinRM starts when the system has settled and is ready to work reliably
  win_service:
    name: WinRM
    start_mode: delayed

# Optionally, you can increase the reboot_timeout to survive long updates during reboot
- name: Ensure we wait long enough for the updates to be applied during reboot
  win_updates:
    reboot: yes
    reboot_timeout: 3600
'''

RETURN = r'''
reboot_required:
    description: True when the target server requires a reboot to complete updates (no further updates can be installed until after a reboot).
    returned: success
    type: bool
    sample: true

updates:
    description: List of updates that were found/installed.
    returned: success
    type: complex
    sample:
    contains:
        title:
            description: Display name.
            returned: always
            type: str
            sample: "Security Update for Windows Server 2012 R2 (KB3004365)"
        kb:
            description: A list of KB article IDs that apply to the update.
            returned: always
            type: list of strings
            sample: [ '3004365' ]
        id:
            description: Internal Windows Update GUID.
            returned: always
            type: str (guid)
            sample: "fb95c1c8-de23-4089-ae29-fd3351d55421"
        installed:
            description: Was the update successfully installed.
            returned: always
            type: bool
            sample: true
        categories:
            description: A list of category strings for this update.
            returned: always
            type: list of strings
            sample: [ 'Critical Updates', 'Windows Server 2012 R2' ]
        failure_hresult_code:
            description: The HRESULT code from a failed update.
            returned: on install failure
            type: bool
            sample: 2147942402

filtered_updates:
    description: List of updates that were found but were filtered based on
      I(blacklist), I(whitelist) or I(category_names). The return value is in
      the same form as I(updates), along with I(filtered_reason).
    returned: success
    type: complex
    sample: see the updates return value
    contains:
        filtered_reason:
            description: The reason why this update was filtered.
            returned: always
            type: str
            sample: 'skip_hidden'

found_update_count:
    description: The number of updates found needing to be applied.
    returned: success
    type: int
    sample: 3
installed_update_count:
    description: The number of updates successfully installed.
    returned: success
    type: int
    sample: 2
failed_update_count:
    description: The number of updates that failed to install.
    returned: always
    type: int
    sample: 0
'''
