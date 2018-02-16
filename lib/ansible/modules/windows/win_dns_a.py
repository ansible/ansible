#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, AMTEGA - Xunta de Galicia
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_dns_a
short_description: Manage DNS A records of Active Directory Computers
description:
  - Create, read, update and delete DNS A records in Active Directory using a
    windows brigde computer.
options:
  computer_name:
    description:
      - Specifies a DNS server. You can specify an IP address or any value that
        resolves to an IP address, such as a fully qualified domain name
        (FQDN), host name, or NETBIOS name.
    required: true
  zone_name:
    description: Specifies the name of a DNS server zone.
    required: true
  name:
    description: Host name.
    required: true
  ipv4_address:
    description: Host IP. Required when I(state=present).
  state:
    description:
      - Specified whether the A record should be C(present) or C(absent) in
        Active Directory DNS.
    choices:
      - present
      - absent
    default: present
notes:
  - Enabled --check --diff options
version_added: 2.6
author: Daniel Sánchez Fábregas (@Daniel-Sanchez-Fabregas)
'''

EXAMPLES = r'''
  - name: Add linux computer DNS A record in Active Directory using a windows machine
    win_dns_a:
      computer_name: dns_controller.example.com
      zone_name: example.com
      name: linux_server.example.com
      ipv4_address: 192.168.0.1
      state: present
    delegate_to: windows_brigde.example.com

  - name: Remove linux computer DNS A record in Active Directory using a windows machine
    win_dns_a:
      computer_name: dns_controller.example.com
      zone_name: example.com
      name: linux_server.example.com
      state: absent
    delegate_to: windows_brigde.example.com
'''

RETURN = '''
'''
