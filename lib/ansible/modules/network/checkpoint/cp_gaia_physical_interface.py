#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage CheckPoint Firewall (c) 2019
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
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: cp_gaia_physical_interface
author: Yuval Feiger (@chkp-yuvalfe)
description:
- Set Physical interface
short_description: Set Physical interface
version_added: '2.9'
options:
  auto_negotiation:
    description: Activating Auto-Negotiation will skip the speed and duplex configuration
    required: false
    type: bool
  comments:
    description: interface Comments.
    required: false
    type: str
  duplex:
    description: Duplex for the interface. Duplex is not relevant when 'auto-negotiation' is enabled
    required: false
    type: str
  enabled:
    description: interface State.
    required: false
    type: bool
  ipv4_address:
    description: Interface IPv4 address.
    required: false
    type: str
  ipv4_mask_length:
    description: Interface IPv4 address mask length.
    required: false
    type: str
  ipv6_address:
    description: Interface IPv6 address.
    required: false
    type: str
  ipv6_autoconfig:
    description: Configure IPv6 auto-configuration.
    required: false
    type: bool
  ipv6_mask_length:
    description: Interface IPv6 address mask length.
    required: false
    type: str
  mac_addr:
    description: Configure hardware address.
    required: false
    type: str
  monitor_mode:
    description: set monitor mode for the interface off/on.
    required: false
    type: bool
  mtu:
    description: interface mtu.
    required: false
    type: int
  name:
    description: interface name.
    required: true
    type: str
  rx_ringsize:
    description: Set receive buffer size for interface.
    required: false
    type: int
  speed:
    description: Interface link speed. Speed is not relevant when 'auto-negotiation' is enabled
    required: false
    type: str
  tx_ringsize:
    description: Set transmit buffer size for interfaces.
    required: false
    type: int

"""

EXAMPLES = """
- name: Set comment field of a physical interface
  cp_gaia_physical_interface:
    comments: eth0 interface
    enabled: true
    name: eth0

"""

RETURN = """
cp_gaia_physical_interface:
  description: The updated interface details.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import api_call_gaia


def main():
    # arguments for the module:
    fields = dict(
        monitor_mode=dict(required=False, type="bool"),
        ipv6_address=dict(required=False, type="str"),
        ipv4_mask_length=dict(required=False, type="str"),
        name=dict(required=True, type="str"),
        duplex=dict(required=False, type="str"),
        tx_ringsize=dict(required=False, type="int"),
        ipv6_autoconfig=dict(required=False, type="bool"),
        enabled=dict(required=False, type="bool"),
        comments=dict(required=False, type="str"),
        mtu=dict(required=False, type="int"),
        ipv4_address=dict(required=False, type="str"),
        auto_negotiation=dict(required=False, type="bool"),
        mac_addr=dict(required=False, type="str"),
        rx_ringsize=dict(required=False, type="int"),
        speed=dict(required=False, type="str"),
        ipv6_mask_length=dict(required=False, type="str")
    )
    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)
    was_changed = False
    ignore = ["status"]

    modules_params_original = module.params

    module_params_show = dict((k, v) for k, v in module.params.items() if k in ["name"] and v is not None)

    module.params = module_params_show
    before = api_call_gaia(module=module, api_call_object="show-physical-interface")
    [before.pop(key) for key in ignore]

    # Run the command:
    module.params = modules_params_original
    res = api_call_gaia(module=module, api_call_object="set-physical-interface")
    module.params = module_params_show
    after = api_call_gaia(module=module, api_call_object="show-physical-interface")
    [after.pop(key) for key in ignore]

    was_changed = False if before == after else True
    module.exit_json(response=res, changed=was_changed)


if __name__ == "__main__":
    main()
