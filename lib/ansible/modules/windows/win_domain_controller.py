#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Red Hat, Inc.
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION='''
module: win_domain_controller
short_description: Manage domain controller/member server state for a Windows host
version_added: 2.3
description:
     - Ensure that a Windows Server 2012+ host is configured as a domain controller or demoted to member server. This module may require
       subsequent use of the M(win_reboot) action if changes are made.
options:
  dns_domain_name:
    description:
      - when C(state) is C(domain_controller), the DNS name of the domain for which the targeted Windows host should be a DC
  domain_admin_user:
    description:
      - username of a domain admin for the target domain (necessary to promote or demote a domain controller)
    required: true
  domain_admin_password:
    description:
      - password for the specified C(domain_admin_user)
    required: true
  safe_mode_password:
    description:
      - safe mode password for the domain controller (required when C(state) is C(domain_controller))
  local_admin_password:
    description:
      - password to be assigned to the local C(Administrator) user (required when C(state) is C(member_server))
  state:
    description:
      - whether the target host should be a domain controller or a member server
    choices:
      - domain_controller
      - member_server
author:
    - Matt Davis (@nitzmahone)
'''

RETURN='''
reboot_required:
    description: True if changes were made that require a reboot.
    returned: always
    type: boolean
    sample: true

'''

EXAMPLES=r'''
# ensure a server is a domain controller
- hosts: winclient
  gather_facts: no
  tasks:
  - win_domain_controller:
      dns_domain_name: ansible.vagrant
      domain_admin_user: testguy@ansible.vagrant
      domain_admin_password: password123!
      safe_mode_password: password123!
      state: domain_controller
      log_path: c:\ansible_win_domain_controller.txt

# ensure a server is not a domain controller
# note that without an action wrapper, in the case where a DC is demoted,
# the task will fail with a 401 Unauthorized, because the domain credential
# becomes invalid to fetch the final output over WinRM. This requires win_async
# with credential switching (or other clever credential-switching
# mechanism to get the output and trigger the required reboot)
- hosts: winclient
  gather_facts: no
  tasks:
  - win_domain_controller:
      domain_admin_user: testguy@ansible.vagrant
      domain_admin_password: password123!
      local_admin_password: password123!
      state: member_server
      log_path: c:\ansible_win_domain_controller.txt

'''

