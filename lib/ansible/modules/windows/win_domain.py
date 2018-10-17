#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
module: win_domain
short_description: Ensures the existence of a Windows domain
version_added: 2.3
description:
- Ensure that the domain named by C(dns_domain_name) exists and is reachable.
- If the domain is not reachable, the domain is created in a new forest on the target Windows Server 2012R2+ host.
- This module may require subsequent use of the M(win_reboot) action if changes are made.
options:
  dns_domain_name:
    description:
      - The DNS name of the domain which should exist and be reachable or reside on the target Windows host.
    required: yes
  domain_netbios_name:
    description:
      - The netbios name of the domain.
      - If not set, then the default netbios name will be the first section of dns_domain_name, up to, but not including the first period.
    version_added: '2.6'
  safe_mode_password:
    description:
      - Safe mode password for the domain controller.
    required: yes
  database_path:
    description:
    - The path to a directory on a fixed disk of the Windows host where the
      domain database will be created.
    - If not set then the default path is C(%SYSTEMROOT%\NTDS).
    type: path
    version_added: '2.5'
  sysvol_path:
    description:
    - The path to a directory on a fixed disk of the Windows host where the
      Sysvol file will be created.
    - If not set then the default path is C(%SYSTEMROOT%\SYSVOL).
    type: path
    version_added: '2.5'
author:
    - Matt Davis (@nitzmahone)
'''

RETURN = '''
reboot_required:
    description: True if changes were made that require a reboot.
    returned: always
    type: boolean
    sample: true
'''

EXAMPLES = r'''
- name: Ensure the named domain is reachable from the target host; if not, create the domain in a new forest residing on the target host
  win_domain:
    dns_domain_name: ansible.vagrant
    safe_mode_password: password123!
'''
