#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: GPL-3.0-only
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = r'''
---
module: win_dhcp_lease
version_added: "2.10"
short_description: Manage Windows Server DHCP Leases
author: Joe Zollo (@joezollo)
requirements:
  - This module requires Windows Server 2012 or Newer
description:
  - Manage Windows Server DHCP Leases (IPv4 Only)
  - Adds, Removes and Modifies DHCP Leases and Reservations
  - Task should be delegated to a Windows DHCP Server
options:
  type:
    description:
      - The type of DHCP address
      - Leases expire as defined by l(duration)
      - When l(duration) is not specified, the server default is used
      - Reservations are permanent
    type: str
    default: reservation
    choices: [ reservation, lease ]
  state:
    description:
      - Specifies the desired state of the DHCP lease or reservation
    type: str
    default: present
    choices: [ present, absent ]
  ip:
    description:
      - The IPv4 address of the client server/computer
    type: str
    required: yes
  scope_id:
    description:
      - Specifies the scope identifier
      - Required when creating a new DHCP reservation/lease
    type: str
  mac:
    description:
      - Specifies the client identifier to be set on the IPv4 address
      - Windows clients use the MAC address as the client ID
      - Linux and other operating systems can use other types of identifiers
      - Can be used to identify an existing lease/reservation, instead of l(ip)
    type: str
  duration:
    description:
      - Specifies the duration of the DHCP lease in days
      - The duration value only applies to l(type=lease)
      - Defaults to the duration specified by the DHCP server
        configuration
      - Only applicable to l(type=lease)
    type: int
  dns_hostname:
    description:
      - Specifies the DNS hostname of the client for which the IP address
        lease is to be added
    type: str
  dns_regtype:
    description:
      - Indicates the type of DNS record to be registered by the DHCP
        server service for this lease
      - l(a) results in an A record being registered
      - l(aptr) results in both A and PTR records to be registered
      - l(noreg) results in no DNS records being registered
    type: str
    default: aptr
    choices: [ aptr, a, noreg ]
  reservation_name:
    description:
      - Specifies the name of the reservation being created
      - Only applicable to l(type=reservation)
    type: str
  description:
    description:
      - Specifies the description for reservation being created
      - Only applicable to l(type=reservation)
    type: str
'''

EXAMPLES = r'''
- name: Ensure DHCP reservation exists
  win_dhcp_lease:
    type: reservation
    ip: 192.168.100.205
    scope_id: 192.168.100.0
    mac: 00b18ad15a1f
    dns_hostname: "{{ ansible_inventory }}"
    description: Testing Server
  delegate_to: dhcp-ericb-euc.vmware.com

- name: Ensure DHCP lease or reservation does not exist
  win_dhcp_lease:
    mac: 00b18ad15a1f
    state: absent
  delegate_to: dhcp-marshallb-euc.vmware.com

- name: Ensure DHCP lease or reservation does not exist
  win_dhcp_lease:
    ip: 192.168.100.205
    state: absent
  delegate_to: dhcp-willp-euc.vmware.com

- name: Convert DHCP lease to reservation & update description
  win_dhcp_lease:
    type: reservation
    ip: 192.168.100.205
    description: Testing Server
  delegate_to: dhcp-danielg-euc.vmware.com

- name: Convert DHCP reservation to lease
  win_dhcp_lease:
    type: lease
    ip: 192.168.100.205
  delegate_to: dhcp-devangm-euc.vmware.com
'''

RETURN = r'''
lease:
  description: New/Updated DHCP object parameters
  returned: When l(state=present)
  type: dict
  sample:
    address_state: InactiveReservation
    client_id: 0a-0b-0c-04-05-aa
    description: Really Fancy
    ip_address: 172.16.98.230
    name: null
    scope_id: 172.16.98.0
'''