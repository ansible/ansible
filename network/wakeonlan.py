#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Dag Wieers <dag@wieers.com>
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

DOCUMENTATION = '''
---
module: wakeonlan
version_added: 2.2
short_description: Send a magic Wake-on-LAN (WoL) broadcast packet
description:
   - The M(wakeonlan) module sends magic Wake-on-LAN (WoL) broadcast packets.
options:
  mac:
    description:
      - MAC address to send Wake-on-LAN broadcast packet for
    required: true
    default: null
  broadcast:
    description:
      - Network broadcast address to use for broadcasting magic Wake-on-LAN packet
    required: false
    default: 255.255.255.255
  port:
    description:
      - UDP port to use for magic Wake-on-LAN packet
    required: false
    default: 7
author: "Dag Wieers (@dagwieers)"
todo:
  - Add arping support to check whether the system is up (before and after)
  - Enable check-mode support (when we have arping support)
  - Does not have SecureOn password support
notes:
  - This module sends a magic packet, without knowing whether it worked
  - Only works if the target system was properly configured for Wake-on-LAN (in the BIOS and/or the OS)
  - Some BIOSes have a different (configurable) Wake-on-LAN boot order (i.e. PXE first) when turned off
'''

EXAMPLES = '''
# Send a magic Wake-on-LAN packet to 00:00:5E:00:53:66
- local_action: wakeonlan mac=00:00:5E:00:53:66 broadcast=192.0.2.23

- wakeonlan: mac=00:00:5E:00:53:66 port=9
  delegate_to: localhost
'''

RETURN='''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
import socket
import struct


def wakeonlan(module, mac, broadcast, port):
    """ Send a magic Wake-on-LAN packet. """

    mac_orig = mac

    # Remove possible seperator from MAC address
    if len(mac) == 12 + 5:
        mac = mac.replace(mac[2], '')

    # If we don't end up with 12 hexadecimal characters, fail
    if len(mac) != 12:
        module.fail_json(msg="Incorrect MAC address length: %s" % mac_orig)

    # Test if it converts to an integer, otherwise fail
    try:
        int(mac, 16)
    except ValueError:
        module.fail_json(msg="Incorrect MAC address format: %s" % mac_orig)
 
    # Create payload for magic packet
    data = ''
    padding = ''.join(['FFFFFFFFFFFF', mac * 20])
    for i in range(0, len(padding), 2):
        data = ''.join([data, struct.pack('B', int(padding[i: i + 2], 16))])

    # Broadcast payload to network
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.sendto(data, (broadcast, port))
    except socket.error:
        e = get_exception()
        module.fail_json(msg=str(e))


def main():
    module = AnsibleModule(
        argument_spec = dict(
            mac = dict(required=True, type='str'),
            broadcast = dict(required=False, default='255.255.255.255'),
            port = dict(required=False, type='int', default=7),
        ),
    )

    mac = module.params.get('mac')
    broadcast = module.params.get('broadcast')
    port = module.params.get('port')

    wakeonlan(module, mac, broadcast, port)
    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
