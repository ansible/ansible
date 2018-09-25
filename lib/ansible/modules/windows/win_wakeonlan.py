#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_wakeonlan
version_added: '2.4'
short_description: Send a magic Wake-on-LAN (WoL) broadcast packet
description:
- The C(win_wakeonlan) module sends magic Wake-on-LAN (WoL) broadcast packets.
options:
  mac:
    description:
    - MAC address to send Wake-on-LAN broadcast packet for.
    required: yes
  broadcast:
    description:
    - Network broadcast address to use for broadcasting magic Wake-on-LAN packet.
    default: 255.255.255.255
  port:
    description:
    - UDP port to use for magic Wake-on-LAN packet.
    type: int
    default: 7
author:
- Dag Wieers (@dagwieers)
todo:
- Does not have SecureOn password support
notes:
- This module sends a magic packet, without knowing whether it worked. It always report a change.
- Only works if the target system was properly configured for Wake-on-LAN (in the BIOS and/or the OS).
- Some BIOSes have a different (configurable) Wake-on-LAN boot order (i.e. PXE first).
'''

EXAMPLES = r'''
- name: Send a magic Wake-on-LAN packet to 00:00:5E:00:53:66
  win_wakeonlan:
    mac: 00:00:5E:00:53:66
    broadcast: 192.0.2.23

- name: Send a magic Wake-On-LAN packet on port 9 to 00-00-5E-00-53-66
  win_wakeonlan:
    mac: 00-00-5E-00-53-66
    port: 9
  delegate_to: remote_system
'''

RETURN = r'''
# Default return values
'''
