#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: wakeonlan
version_added: '2.2'
short_description: Send a magic Wake-on-LAN (WoL) broadcast packet
description:
- The C(wakeonlan) module sends magic Wake-on-LAN (WoL) broadcast packets.
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
  - Add arping support to check whether the system is up (before and after)
  - Enable check-mode support (when we have arping support)
  - Does not have SecureOn password support
notes:
  - This module sends a magic packet, without knowing whether it worked
  - Only works if the target system was properly configured for Wake-on-LAN (in the BIOS and/or the OS)
  - Some BIOSes have a different (configurable) Wake-on-LAN boot order (i.e. PXE first).
'''

EXAMPLES = r'''
- name: Send a magic Wake-on-LAN packet to 00:00:5E:00:53:66
  wakeonlan:
    mac: '00:00:5E:00:53:66'
    broadcast: 192.0.2.23
  delegate_to: localhost

- wakeonlan:
    mac: 00:00:5E:00:53:66
    port: 9
  delegate_to: localhost
'''

RETURN = r'''
# Default return values
'''
import socket
import struct
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def wakeonlan(module, mac, broadcast, port):
    """ Send a magic Wake-on-LAN packet. """

    mac_orig = mac

    # Remove possible separator from MAC address
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
    data = b''
    padding = ''.join(['FFFFFFFFFFFF', mac * 20])
    for i in range(0, len(padding), 2):
        data = b''.join([data, struct.pack('B', int(padding[i: i + 2], 16))])

    # Broadcast payload to network
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    if not module.check_mode:

        try:
            sock.sendto(data, (broadcast, port))
        except socket.error as e:
            sock.close()
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    sock.close()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            mac=dict(type='str', required=True),
            broadcast=dict(type='str', default='255.255.255.255'),
            port=dict(type='int', default=7),
        ),
        supports_check_mode=True,
    )

    mac = module.params['mac']
    broadcast = module.params['broadcast']
    port = module.params['port']

    wakeonlan(module, mac, broadcast, port)

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
