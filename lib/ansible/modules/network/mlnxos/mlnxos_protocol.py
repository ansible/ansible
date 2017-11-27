#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_protocol
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Enables/Disables protocols on MLNX-OS network devices
description:
  - >-
      This module provides a mechanism for enabling disabling protocols
      on MLNX-OS network devices.
notes:
  - tested on Mellanox OS 3.6.4000
options:
  mlag:
    description: MLAG protocol
    choices: ['enabled', 'disabled']
  magp:
    description: MAGPdisabled
  spanning_tree:
    description: Spanning Tree support
    choices: ['enabled', 'disabled']
  dcb_pfc:
    description: DCB priority flow control
    choices: ['enabled', 'disabled']
  igmp_snooping:
    description: IP IGMP snooping
    choices: ['enabled', 'disabled']
  lacp:
    description: LACP protocol
    choices: ['enabled', 'disabled']
  ip_routing:
    description: IP routing support
    choices: ['enabled', 'disabled']
  lldp:
    description: LLDP protocol
    choices: ['enabled', 'disabled']
  bgp:
    description: BGP protocol
    choices: ['enabled', 'disabled']
  ospf:
    description: OSPF protocol
    choices: ['enabled', 'disabled']
"""

EXAMPLES = """
- name: enable protocols for MLAG
  mlnxos_protocol:
      lacp: enabled
      spanning_tree: disabled
      ip_routing: enabled
      mlag: enabled
      dcb_pfc: enabled
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - no spanning-tree
    - protocol mlag
    - exit
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

from ansible.module_utils.mlnxos import BaseMlnxosApp
from ansible.module_utils.mlnxos import mlnxos_argument_spec
from ansible.module_utils.mlnxos import show_cmd


class MlnxosProtocolApp(BaseMlnxosApp):
    PROTOCOL_MAPPING = dict(
        mlag="mlag",
        magp="magp",
        spanning_tree="spanning-tree",
        dcb_pfc="priority-flow-control",
        igmp_snooping="igmp-snooping",
        lacp="lacp",
        ip_routing="IP L3",
        lldp="lldp",
        bgp="bgp",
        ospf="ospf",
    )

    PROTOCOL_COMMANDS = dict(
        mlag=("protocol mlag", "no protocol mlag"),
        magp=("protocl magp", "no protocol magp"),
        spanning_tree=("spanning-tree", "no spanning-tree"),
        dcb_pfc=("dcb priority-flow-control enable force",
                 "no dcb priority-flow-control enable force"),
        igmp_snooping=("ip igmp snooping", "no ip igmp snooping"),
        lacp=("lacp", "no lacp"),
        ip_routing=("ip routing", "no ip routing"),
        lldp=("lldp", "no lldp"),
        bgp=("protocol bgp", "no protocol bgp"),
        ospf=("protocol ospf", "no protocol ospf"),
    )

    @classmethod
    def _get_element_spec(cls):
        element_spec = dict()
        for protocol in cls.PROTOCOL_MAPPING:
            element_spec[protocol] = dict(choices=['enabled', 'disabled'])
        return element_spec

    def init_module(self):
        """ main entry point for module execution
        """
        element_spec = self._get_element_spec()
        argument_spec = dict()
        argument_spec.update(element_spec)
        argument_spec.update(mlnxos_argument_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
        )

    def get_required_config(self):
        self._required_config = dict()
        module_params = self._module.params
        for key, val in iteritems(module_params):
            if key in self.PROTOCOL_MAPPING and val is not None:
                self._required_config[key] = val

    def load_current_config(self):
        self._current_config = dict()
        config = show_cmd(self._module, "show protocols")
        for protocol, protocol_json_attr in iteritems(self.PROTOCOL_MAPPING):
            val = config.get(protocol_json_attr, 'disabled')
            if val not in ('enabled', 'disabled'):
                val = 'enabled'
            self._current_config[protocol] = val

    def generate_commands(self):
        for protocl, req_val in iteritems(self._required_config):
            curr_val = self._current_config.get(protocl, 'disabled')
            if curr_val != req_val:
                enable_command, disable_command = \
                    self.PROTOCOL_COMMANDS[protocl]
                if req_val == 'disabled':
                    command = disable_command
                else:
                    command = enable_command
                self._commands.append(command)
        if self._commands:
            self._commands.append("exit")


def main():
    """ main entry point for module execution
    """
    MlnxosProtocolApp.main()


if __name__ == '__main__':
    main()
