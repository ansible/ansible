#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_protocol
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Enables/Disables protocols on Mellanox ONYX network devices
description:
  - This module provides a mechanism for enabling and disabling protocols
    Mellanox on ONYX network devices.
notes:
  - Tested on ONYX 3.6.4000
options:
  mlag:
    description: MLAG protocol
    choices: ['enabled', 'disabled']
  magp:
    description: MAGP protocol
    choices: ['enabled', 'disabled']
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
  ip_l3:
    description: IP L3 support
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
  onyx_protocol:
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
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxProtocolModule(BaseOnyxModule):

    PROTOCOL_MAPPING = dict(
        mlag=dict(name="mlag", enable="protocol mlag",
                  disable="no protocol mlag"),
        magp=dict(name="magp", enable="protocol magp",
                  disable="no protocol magp"),
        spanning_tree=dict(name="spanning-tree", enable="spanning-tree",
                           disable="no spanning-tree"),
        dcb_pfc=dict(name="priority-flow-control",
                     enable="dcb priority-flow-control enable force",
                     disable="no dcb priority-flow-control enable force"),
        igmp_snooping=dict(name="igmp-snooping", enable="ip igmp snooping",
                           disable="no ip igmp snooping"),
        lacp=dict(name="lacp", enable="lacp", disable="no lacp"),
        ip_l3=dict(name="IP L3", enable="ip l3",
                        disable="no ip l3"),
        ip_routing=dict(name="IP routing", enable="ip routing",
                        disable="no ip routing"),
        lldp=dict(name="lldp", enable="lldp", disable="no lldp"),
        bgp=dict(name="bgp", enable="protocol bgp", disable="no protocol bgp"),
        ospf=dict(name="ospf", enable="protocol ospf",
                  disable="no protocol ospf"),
    )

    @classmethod
    def _get_element_spec(cls):
        element_spec = dict()
        for protocol in cls.PROTOCOL_MAPPING:
            element_spec[protocol] = dict(choices=['enabled', 'disabled'])
        return element_spec

    def init_module(self):
        """ Ansible module initialization
        """
        element_spec = self._get_element_spec()
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True
        )

    def get_required_config(self):
        self._required_config = dict()
        module_params = self._module.params
        for key, val in iteritems(module_params):
            if key in self.PROTOCOL_MAPPING and val is not None:
                self._required_config[key] = val

    def _get_protocols(self):
        return show_cmd(self._module, "show protocols")

    def _get_ip_routing(self):
        return show_cmd(self._module, 'show ip routing | include "IP routing"',
                        json_fmt=False)

    def load_current_config(self):
        self._current_config = dict()
        protocols_config = self._get_protocols()
        if not protocols_config:
            protocols_config = dict()
        ip_config = self._get_ip_routing()
        if ip_config:
            lines = ip_config.split('\n')
            for line in lines:
                line = line.strip()
                line_attr = line.split(':')
                if len(line_attr) == 2:
                    attr = line_attr[0].strip()
                    val = line_attr[1].strip()
                    protocols_config[attr] = val
        for protocol, protocol_metadata in iteritems(self.PROTOCOL_MAPPING):
            protocol_json_attr = protocol_metadata['name']
            val = protocols_config.get(protocol_json_attr, 'disabled')
            if val not in ('enabled', 'disabled'):
                val = 'enabled'
            self._current_config[protocol] = val

    def generate_commands(self):
        for protocol, req_val in iteritems(self._required_config):
            protocol_metadata = self.PROTOCOL_MAPPING[protocol]
            curr_val = self._current_config.get(protocol, 'disabled')
            if curr_val != req_val:
                if req_val == 'disabled':
                    command = protocol_metadata['disable']
                else:
                    command = protocol_metadata['enable']
                self._commands.append(command)


def main():
    """ main entry point for module execution
    """
    OnyxProtocolModule.main()


if __name__ == '__main__':
    main()
