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
      - The adapter name used is the connection caption in the Network Control Panel or the InterfaceAlias of C(Get-DnsClientServerAddress).
    type: list
    required: yes
  dns_servers:
    description:
      - Single or ordered list of DNS servers (IPv4 and IPv6 addresses) to configure for lookup.
      - An empty list will configure the adapter to use the DHCP-assigned values on connections where DHCP is enabled,
        or disable DNS lookup on statically-configured connections.
      - IPv6 DNS servers can only be set on Windows Server 2012 or newer, older hosts can only set IPv4 addresses.
      - Before 2.10 use ipv4_addresses instead.
    type: list
    required: yes
    aliases: [ "ipv4_addresses", "ip_addresses", "addresses" ]
notes:
  - Before 2.10, when setting an empty list of DNS server addresses on an adapter with DHCP enabled, a change was always registered.
  - In 2.10, DNS servers will always be reset if the format of nameservers in the registry is not comma delimited.
    See U(https://www.welivesecurity.com/2016/06/02/crouching-tiger-hidden-dns/)
author:
- Matt Davis (@nitzmahone)
- Brian Scholer (@briantist)
'''

EXAMPLES = r'''
- name: Set a single address on the adapter named Ethernet
  win_dns_client:
    adapter_names: Ethernet
    dns_servers: 192.168.34.5

- name: Set multiple lookup addresses on all visible adapters (usually physical adapters that are in the Up state), with debug logging to a file
  win_dns_client:
    adapter_names: '*'
    dns_servers:
    - 192.168.34.5
    - 192.168.34.6
    log_path: C:\dns_log.txt

- name: Set IPv6 DNS servers on the adapter named Ethernet
  win_dns_client:
    adapter_names: Ethernet
    dns_servers:
    - '2001:db8::2'
    - '2001:db8::3'

- name: Configure all adapters whose names begin with Ethernet to use DHCP-assigned DNS values
  win_dns_client:
    adapter_names: 'Ethernet*'
    dns_servers: []
'''

RETURN = r'''
'''
