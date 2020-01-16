#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_interface
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense interfaces
description:
  - Manage pfSense interfaces.
notes:
  - EXPERIMENTAL MODULE, not suited for production.
options:
  state:
    description: State in which to leave the interface.
    choices: [ "present", "absent" ]
    default: present
    type: str
  descr:
    description: Description (name) for the interface.
    required: true
    type: str
  interface:
    description: Network port to which assign the interface.
    type: str
  enable:
    description: Enable interface.
    type: bool
  ipv4_type:
    description: IPv4 Configuration Type.
    choices: [ "none", "static" ]
    default: 'none'
    type: str
  mac:
    description: Used to modify ("spoof") the MAC address of this interface.
    required: false
    type: str
  mtu:
    description: Maximum transmission unit
    required: false
    type: int
  mss:
    description: MSS clamping for TCP connections.
    required: false
    type: int
  speed_duplex:
    description: Set speed and duplex mode for this interface.
    required: false
    default: autoselect
    type: str
  ipv4_address:
    description: IPv4 Address.
    required: false
    type: str
  ipv4_prefixlen:
    description: IPv4 subnet prefix length.
    required: false
    default: 24
    type: int
  ipv4_gateway:
    description: IPv4 gateway for this interface.
    required: false
    type: str
  blockpriv:
    description: Blocks traffic from IP addresses that are reserved for private networks.
    required: false
    type: bool
  blockbogons:
    description: Blocks traffic from reserved IP addresses (but not RFC 1918) or not yet assigned by IANA.
    required: false
    type: bool
  create_ipv4_gateway:
    description: Create the specified IPv4 gateway if it does not exist
    required: false
    type: bool
  ipv4_gateway_address:
    description: IPv4 gateway address to set on the interface
    required: false
    type: str
"""

EXAMPLES = """
- name: Add interface
  pfsense_interface:
    descr: voice
    interface: mvneta0.100
    enable: True

- name: Remove interface
  pfsense_interface:
    state: absent
    descr: voice
    interface: mvneta0.100
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: [
        "create interface 'voice', port='mvneta0.100', speed_duplex='autoselect', enable='True'",
        "delete interface 'voice'"
    ]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.interface import PFSenseInterfaceModule, INTERFACE_ARGUMENT_SPEC, INTERFACE_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=INTERFACE_ARGUMENT_SPEC,
        required_if=INTERFACE_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseInterfaceModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
