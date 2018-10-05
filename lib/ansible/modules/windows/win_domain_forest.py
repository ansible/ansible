#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Red Hat, Inc.
# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
module: win_domain_forest
short_description: Set up an Active Directory forest
version_added: 2.8
description:
- Set up an Active Directory forest on Windows Server.
- This module may require subsequent use of the M(win_reboot) action if changes are made.
options:
  dns_domain_name:
    description:
    - When I(state) is I(domain_controller), the DNS name of the domain for which the targeted Windows host should be a DC.
    type: str
  safe_mode_password:
    description:
    - Safe mode password for the domain controller (required when I(state) is I(domain_controller)).
    type: str
  database_path:
    description:
    - The path to a directory on a fixed disk of the Windows host where the
      domain database will be created..
    - If not set then the default path is C(%SYSTEMROOT%\NTDS).
    type: path
  sysvol_path:
    description:
    - The path to a directory on a fixed disk of the Windows host where the
      Sysvol folder will be created.
    - If not set then the default path is C(%SYSTEMROOT%\SYSVOL).
    type: path
  create_dns_delegation:
    description:
    - Whether to create a DNS delegation that references the new DNS server that you install along with the domain controller.
    - Valid for Active Directory-integrated DNS only.
    - The default is computed automatically based on the environment.
    type: bool
  domain_mode:
    description:
    - Specifies the domain functional level of the first domain in the creation of a new forest.
    - The domain functional level cannot be lower than the forest functional level, but it can be higher.
    - The default is automatically computed and set.
    type: str
    choices: [ Win2003, Win2008, Win2008R2, Win2012, Win2012R2, WinTreshold ]
  domain_netbios_name:
    description:
    - Specifies the NetBIOS name for the root domain in the new forest.
    - For NetBIOS names to be valid for use with this parameter they must be single label names of 15 characters or less, if not it will fail.
    - If this parameter is not set, then the default is automatically computed from the value of the I(domain_name) parameter.
    type: str
  forest_mode:
    description:
    - Specifies the forest functional level for the new forest.
    - The default forest functional level in Windows Server is typically the same as the version you are running.
    - Beware that the default forest functional level in Windows Server 2008 R2 when you create a new forest is C(Win2003).
    type: str
    choices: [ Win2003, Win2008, Win2008R2, Win2012, Win2012R2, WinTreshold ]
author:
- Matt Davis (@nitzmahone)
- Dag Wieers (@dagwieers)
'''

RETURN = r'''
reboot_required:
    description: True if changes were made that require a reboot.
    returned: always
    type: boolean
    sample: true
'''

EXAMPLES = r'''
- name: Create a domain forest
  win_domain_forest:
    dns_domain_name: ansible.vagrant
    safe_mode_password: password123!
    log_path: C:\ansible_win_domain_controller.txt
'''
