#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Red Hat, Inc.
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
module: win_domain_controller
short_description: Manage domain controller/member server state for a Windows host
version_added: '2.3'
description:
    - Ensure that a Windows Server 2012+ host is configured as a domain controller or demoted to member server.
    - This module may require subsequent use of the M(win_reboot) action if changes are made.
options:
  dns_domain_name:
    description:
      - When C(state) is C(domain_controller), the DNS name of the domain for which the targeted Windows host should be a DC.
    type: str
  domain_admin_user:
    description:
      - Username of a domain admin for the target domain (necessary to promote or demote a domain controller).
    type: str
    required: true
  domain_admin_password:
    description:
      - Password for the specified C(domain_admin_user).
    type: str
    required: true
  safe_mode_password:
    description:
      - Safe mode password for the domain controller (required when C(state) is C(domain_controller)).
    type: str
  local_admin_password:
    description:
      - Password to be assigned to the local C(Administrator) user (required when C(state) is C(member_server)).
    type: str
  read_only:
    description:
      - Whether to install the domain controller as a read only replica for an existing domain.
    type: bool
    default: no
    version_added: '2.5'
  site_name:
    description:
      - Specifies the name of an existing site where you can place the new domain controller.
      - This option is required when I(read_only) is C(yes).
    type: str
    version_added: '2.5'
  state:
    description:
      - Whether the target host should be a domain controller or a member server.
    type: str
    choices: [ domain_controller, member_server ]
  database_path:
    description:
    - The path to a directory on a fixed disk of the Windows host where the
      domain database will be created..
    - If not set then the default path is C(%SYSTEMROOT%\NTDS).
    type: path
    version_added: '2.5'
  sysvol_path:
    description:
    - The path to a directory on a fixed disk of the Windows host where the
      Sysvol folder will be created.
    - If not set then the default path is C(%SYSTEMROOT%\SYSVOL).
    type: path
    version_added: '2.5'
seealso:
- module: win_domain
- module: win_domain_computer
- module: win_domain_group
- module: win_domain_membership
- module: win_domain_user
author:
    - Matt Davis (@nitzmahone)
'''

RETURN = r'''
reboot_required:
    description: True if changes were made that require a reboot.
    returned: always
    type: bool
    sample: true
'''

EXAMPLES = r'''
- name: Ensure a server is a domain controller
  win_domain_controller:
    dns_domain_name: ansible.vagrant
    domain_admin_user: testguy@ansible.vagrant
    domain_admin_password: password123!
    safe_mode_password: password123!
    state: domain_controller
    log_path: C:\ansible_win_domain_controller.txt

# ensure a server is not a domain controller
# note that without an action wrapper, in the case where a DC is demoted,
# the task will fail with a 401 Unauthorized, because the domain credential
# becomes invalid to fetch the final output over WinRM. This requires win_async
# with credential switching (or other clever credential-switching
# mechanism to get the output and trigger the required reboot)
- win_domain_controller:
    domain_admin_user: testguy@ansible.vagrant
    domain_admin_password: password123!
    local_admin_password: password123!
    state: member_server
    log_path: C:\ansible_win_domain_controller.txt

- name: Promote server as a read only domain controller
  win_domain_controller:
    dns_domain_name: ansible.vagrant
    domain_admin_user: testguy@ansible.vagrant
    domain_admin_password: password123!
    safe_mode_password: password123!
    state: domain_controller
    read_only: yes
    site_name: London
'''
