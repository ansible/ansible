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
module: win_domain
short_description: Ensures the existence of a Windows domain.
version_added: 2.3
description:
     - Ensure that the domain named by C(dns_domain_name) exists and is reachable. If the domain is not reachable, the domain is created in a new forest
       on the target Windows Server 2012R2+ host. This module may require subsequent use of the M(win_reboot) action if changes are made.
options:
  dns_domain_name:
    description:
      - the DNS name of the domain which should exist and be reachable or reside on the target Windows host
    required: true
  safe_mode_password:
    description:
      - safe mode password for the domain controller
    required: true
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
# ensure the named domain is reachable from the target host; if not, create the domain in a new forest residing on the target host
- win_domain:
    dns_domain_name: ansible.vagrant
    safe_mode_password: password123!

'''
