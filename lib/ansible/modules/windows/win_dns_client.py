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
    required: true
  ipv4_addresses:
    description:
      - Single or ordered list of DNS server IPv4 addresses to configure for lookup. An empty list will configure the adapter to use the
        DHCP-assigned values on connections where DHCP is enabled, or disable DNS lookup on statically-configured connections.
    required: true
notes:
  - When setting an empty list of DNS server addresses on an adapter with DHCP enabled, a change will always be registered, since it is not possible to
    detect the difference between a DHCP-sourced server value and one that is statically set.
author: "Matt Davis (@nitzmahone)"
'''

EXAMPLES = r'''
  # set a single address on the adapter named Ethernet
  - win_dns_client:
      adapter_names: Ethernet
      ipv4_addresses: 192.168.34.5

  # set multiple lookup addresses on all visible adapters (usually physical adapters that are in the Up state), with debug logging to a file
  - win_dns_client:
      adapter_names: "*"
      ipv4_addresses:
      - 192.168.34.5
      - 192.168.34.6
      log_path: c:\dns_log.txt

  # configure all adapters whose names begin with Ethernet to use DHCP-assigned DNS values
  - win_dns_client:
      adapter_names: "Ethernet*"
      ipv4_addresses: []
'''

RETURN = '''

'''
