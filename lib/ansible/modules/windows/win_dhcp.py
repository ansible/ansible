#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: GPL-3.0-only
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_dhcp
version_added: '2.10'
short_description: Manages IP Addresses on a Windows DHCP Server
author: Joe Zollo (@joezollo)
requirements:
  - This module requires Windows Server 2012 or Newer
description:
  - Manages IP Addresses on a Windows DHCP Server
  - Adds or Removes DHCP Leases and Reservations
  - Task should be delegated to a Windows DHCP Server
options:
  type:
    description:
      - The type of DHCP address
    type: str
    default: reservation
    choices: [ reservation, lease ]
  state:
    description:
      - Specifies the desired state of the DHCP lease or reservation
    type: str
    choices: [ present, absent ]
  ip:
    description:
      - The IP address of the client server/computer
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
    type: str
  duration:
    description:
      - Specifies the duration of the DHCP lease in days
      - The duration value only applies to l(type=lease)
      - Defaults to the duration specified by the DHCP server
        configuration
    type: int
  dns_hostname:
    description:
      - Specifies the DNS hostname of the client for which the IP address
        lease is to be added
  dns_regtype:
    description:
      - Indicates the type of DNS record to be registered by the DHCP
        server service for this lease
      - Defaults to the type specified by the DHCP server configuration
    type: str
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
  win_dhcp:
    type: reservation
    ip: 192.168.100.205
    scope_id: 192.168.100.0
    mac: 00b18ad15a1f
    dns_hostname: "{{ ansible_inventory }}"
    description: Testing Server
  delegate_to: dhcp-ericb-euc.vmware.com

- name: Ensure DHCP lease or reservation does not exist
  win_dhcp:
    mac: 00b18ad15a1f
    state: absent
  delegate_to: dhcp-marshallb-euc.vmware.com

- name: Ensure DHCP lease or reservation does not exist
  win_dhcp:
    ip: 192.168.100.205
    state: absent
  delegate_to: dhcp-willp-euc.vmware.com

- name: Convert DHCP lease to reservation & update description
  win_dhcp:
    type: reservation
    ip: 192.168.100.205
    description: Testing Server
  delegate_to: dhcp-danielg-euc.vmware.com

- name: Convert DHCP reservation to lease
  win_dhcp:
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

original:
  description: Original DHCP object parameters
  returned: When an existing lease is found
  type: dict
  sample:
    address_state: InactiveReservation
    client_id: 0a-0b-0c-04-05-aa
    description: Really Fancy
    ip_address: 172.16.98.230
    name: null
    scope_id: 172.16.98.0
'''
