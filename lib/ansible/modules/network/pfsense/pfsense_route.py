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
module: pfsense_route
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense routes
description:
  - Manage pfSense routes
notes:
options:
  descr:
    description: The description of the route
    required: true
    type: str
  network:
    description: Destination network for this static route
    required: false
    type: str
  gateway:
    description: Gateway this route applies to
    required: false
    type: str
  disabled:
    description: Set this option to disable this static route without removing it from the list.
    default: false
    type: bool
  state:
    description: State in which to leave the route
    choices: [ "present", "absent" ]
    default: present
    type: str
"""

EXAMPLES = """
- name: Add route
  pfsense_route:
    descr: vpn_route
    gateway: VPN_GW
    network: 10.100.0.0/16
    state: present

- name: Remove route
  pfsense_route:
    name: vpn_route
    state: absent
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: ["create route 'vpn_route', gateway='VPN_GW', network='10.100.0.0/16'", "delete route 'vpn_route'"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.route import PFSenseRouteModule, ROUTE_ARGUMENT_SPEC, ROUTE_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=ROUTE_ARGUMENT_SPEC,
        required_if=ROUTE_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseRouteModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
