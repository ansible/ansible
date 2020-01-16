#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_gateway
version_added: "2.9"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense gateways
description:
  - Manage pfSense gateways
notes:
options:
  name:
    description: Gateway name
    required: true
    type: str
  interface:
    description: Choose which interface this gateway applies to.
    required: false
    type: str
  ipprotocol:
    description: Choose the Internet Protocol this gateway uses.
    required: false
    choices: [ "inet", "inet6" ]
    default: inet
    type: str
  gateway:
    description: Gateway IP address
    required: false
    type: str
  descr:
    description: The description of the gateway
    required: false
    type: str
  disabled:
    description: Set this option to disable this gateway without removing it from the list.
    default: false
    type: bool
  monitor:
    description: Enter an alternative address here to be used to monitor the link.
    required: false
    type: str
  monitor_disable:
    description: This will consider this gateway as always being up.
    default: false
    type: bool
  action_disable:
    description: No action will be taken on gateway events. The gateway is always considered up.
    default: false
    type: bool
  force_down:
    description: This will force this gateway to be considered down.
    default: false
    type: bool
  weight:
    description: Weight for this gateway when used in a Gateway Group. Must be between 1 and 30.
    default: 1
    type: int
  state:
    description: State in which to leave the gateway
    required: true
    choices: [ "present", "absent" ]
    default: present
    type: str
"""

EXAMPLES = """
- name: Add gateway
  pfsense_gateway:
    name: default_gw
    interface: wan
    gateway: 1.2.3.4
    state: present

- name: Remove gateway
  pfsense_gateway:
    name: vpn_gw
    state: absent
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: ["create gateway 'default_gw', interface='wan', address='1.2.3.4'", "delete gateway 'vpn_gw'"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.gateway import PFSenseGatewayModule, GATEWAY_ARGUMENT_SPEC, GATEWAY_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=GATEWAY_ARGUMENT_SPEC,
        required_if=GATEWAY_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseGatewayModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
