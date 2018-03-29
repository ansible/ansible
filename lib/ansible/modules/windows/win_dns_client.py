#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_dns_client
version_added: "2.3"
short_description: Configures DNS lookup on Windows hosts
description:
  - The C(win_dns_client) module configures the DNS client on Windows network adapters.
options:
  adapter_names:
    description:
      - Adapter name or list of adapter names for which to manage DNS settings ('*' is supported as a wildcard value).
        The adapter name used is the connection caption in the Network Control Panel or via C(Get-NetAdapter), eg C(Local Area Connection).
    required: yes
  ipv4_addresses:
    description:
      - Single or ordered list of DNS server IPv4 addresses to configure for lookup. An empty list will configure the adapter to use the
        DHCP-assigned values on connections where DHCP is enabled, or disable DNS lookup on statically-configured connections.
    required: yes
notes:
  - When setting an empty list of DNS server addresses on an adapter with DHCP enabled, a change will always be registered, since it is not possible to
    detect the difference between a DHCP-sourced server value and one that is statically set.
author:
- Matt Davis (@nitzmahone)
'''

EXAMPLES = r'''
- name: Set a single address on the adapter named Ethernet
  win_dns_client:
    adapter_names: Ethernet
    ipv4_addresses: 192.168.34.5

- name: Set multiple lookup addresses on all visible adapters (usually physical adapters that are in the Up state), with debug logging to a file
  win_dns_client:
    adapter_names: '*'
    ipv4_addresses:
    - 192.168.34.5
    - 192.168.34.6
    log_path: C:\dns_log.txt

- name: Configure all adapters whose names begin with Ethernet to use DHCP-assigned DNS values
  win_dns_client:
    adapter_names: 'Ethernet*'
    ipv4_addresses: []
'''

RETURN = '''

'''
