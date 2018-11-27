#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub, actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_hotfix
version_added: '2.4'
short_description: Install and uninstalls Windows hotfixes
description:
- Install, uninstall a Windows hotfix.
options:
  hotfix_identifier:
    description:
    - The name of the hotfix as shown in DISM, see examples for details.
    - This or C(hotfix_kb) MUST be set when C(state=absent).
    - If C(state=present) then the hotfix at C(source) will be validated
      against this value, if it does not match an error will occur.
    - You can get the identifier by running
      'Get-WindowsPackage -Online -PackagePath path-to-cab-in-msu' after
      expanding the msu file.
  hotfix_kb:
    description:
    - The name of the KB the hotfix relates to, see examples for details.
    - This of C(hotfix_identifier) MUST be set when C(state=absent).
    - If C(state=present) then the hotfix at C(source) will be validated
      against this value, if it does not match an error will occur.
    - Because DISM uses the identifier as a key and doesn't refer to a KB in
      all cases it is recommended to use C(hotfix_identifier) instead.
  state:
    description:
    - Whether to install or uninstall the hotfix.
    - When C(present), C(source) MUST be set.
    - When C(absent), C(hotfix_identifier) or C(hotfix_kb) MUST be set.
    default: present
    choices: [ absent, present ]
  source:
    description:
    - The path to the downloaded hotfix .msu file.
    - This MUST be set if C(state=present) and MUST be a .msu hotfix file.
    type: path
notes:
- This must be run on a host that has the DISM powershell module installed and
  a Powershell version >= 4.
- This module is installed by default on Windows 8 and Server 2012 and newer.
- You can manually install this module on Windows 7 and Server 2008 R2 by
  installing the Windows ADK
  U(https://developer.microsoft.com/en-us/windows/hardware/windows-assessment-deployment-kit),
  see examples to see how to do it with chocolatey.
- You can download hotfixes from U(https://www.catalog.update.microsoft.com/Home.aspx).
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: install Windows ADK with DISM for Server 2008 R2
  win_chocolatey:
    name: windows-adk
    version: 8.100.26866.0
    state: present
    install_args: /features OptionId.DeploymentTools

- name: install hotfix without validating the KB and Identifier
  win_hotfix:
    source: C:\temp\windows8.1-kb3172729-x64_e8003822a7ef4705cbb65623b72fd3cec73fe222.msu
    state: present
  register: hotfix_install

- win_reboot:
  when: hotfix_install.reboot_required

- name: install hotfix validating KB
  win_hotfix:
    hotfix_kb: KB3172729
    source: C:\temp\windows8.1-kb3172729-x64_e8003822a7ef4705cbb65623b72fd3cec73fe222.msu
    state: present
  register: hotfix_install

- win_reboot:
  when: hotfix_install.reboot_required

- name: install hotfix validating Identifier
  win_hotfix:
    hotfix_identifier: Package_for_KB3172729~31bf3856ad364e35~amd64~~6.3.1.0
    source: C:\temp\windows8.1-kb3172729-x64_e8003822a7ef4705cbb65623b72fd3cec73fe222.msu
    state: present
  register: hotfix_install

- win_reboot:
  when: hotfix_install.reboot_required

- name: uninstall hotfix with Identifier
  win_hotfix:
    hotfix_identifier: Package_for_KB3172729~31bf3856ad364e35~amd64~~6.3.1.0
    state: absent
  register: hotfix_uninstall

- win_reboot:
  when: hotfix_uninstall.reboot_required

- name: uninstall hotfix with KB (not recommended)
  win_hotfix:
    hotfix_kb: KB3172729
    state: absent
  register: hotfix_uninstall

- win_reboot:
  when: hotfix_uninstall.reboot_required
'''

RETURN = r'''
identifier:
  description: The DISM identifier for the hotfix.
  returned: success
  type: str
  sample: Package_for_KB3172729~31bf3856ad364e35~amd64~~6.3.1.0
kb:
  description: The KB the hotfix relates to.
  returned: success
  type: str
  sample: KB3172729
reboot_required:
  description: Whether a reboot is required for the install or uninstall to
    finalise.
  returned: success
  type: str
  sample: True
'''
