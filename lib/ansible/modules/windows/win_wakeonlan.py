#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Dag Wieers <dag@wieers.com>
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
    required: true
  broadcast:
    description:
    - Network broadcast address to use for broadcasting magic Wake-on-LAN packet.
    default: 255.255.255.255
  port:
    description:
    - UDP port to use for magic Wake-on-LAN packet.
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
