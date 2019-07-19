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
module: onyx_qos
version_added: "2.9"
author: "Anas Badaha (@anasb)"
short_description: Configures QoS
description:
  - This module provides declarative management of Onyx QoS configuration
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.8130
options:
  interfaces:
    description:
      - list of interfaces name.
    required: true
  trust:
    description:
      - trust type.
    choices: ['L2', 'L3', 'both']
    default: L2
  rewrite_pcp:
    description:
      - rewrite with type pcp.
    choices: ['enabled', 'disabled']
    default: disabled
  rewrite_dscp:
    description:
      - rewrite with type dscp.
    choices: ['enabled', 'disabled']
    default: disabled
"""

EXAMPLES = """
- name: configure QoS
  onyx_QoS:
    interfaces:
      - Mpo7
      - Mpo7
    trust: L3
    rewrite_pcp: disabled
    rewrite_dscp: enabled

- name: configure QoS
  onyx_QoS:
    interfaces:
      - Eth1/1
      - Eth1/2
    trust: both
    rewrite_pcp: disabled
    rewrite_dscp: enabled
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface ethernet 1/16 qos trust L3
    - interface mlag-port-channel 7 qos trust L3
    - interface port-channel 1 qos trust L3
    - interface mlag-port-channel 7 qos trust L2
    - interface mlag-port-channel 7 qos rewrite dscp
    - interface ethernet 1/16 qos rewrite pcp
    - interface ethernet 1/1 no qos rewrite pcp
"""

import re
from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxQosModule(BaseOnyxModule):
    TRUST_CMD = "interface {0} {1} qos trust {2}"
    NO_REWRITE_PCP_CMD = "interface {0} {1} no qos rewrite pcp"
    NO_REWRITE_DSCP_CMD = "interface {0} {1} no qos rewrite dscp"
    REWRITE_PCP_CMD = "interface {0} {1} qos rewrite pcp"
    REWRITE_DSCP_CMD = "interface {0} {1} qos rewrite dscp"

    REWRITE_PCP = "pcp"
    REWRITE_DSCP = "dscp"

    IF_ETH_REGEX = re.compile(r"^Eth(\d+\/\d+|Eth\d+\/\d+\d+)$")
    IF_PO_REGEX = re.compile(r"^Po(\d+)$")
    MLAG_NAME_REGEX = re.compile(r"^Mpo(\d+)$")

    IF_TYPE_ETH = "ethernet"
    PORT_CHANNEL = "port-channel"
    MLAG_PORT_CHANNEL = "mlag-port-channel"

    IF_TYPE_MAP = {
        IF_TYPE_ETH: IF_ETH_REGEX,
        PORT_CHANNEL: IF_PO_REGEX,
        MLAG_PORT_CHANNEL: MLAG_NAME_REGEX
    }

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            interfaces=dict(type='list', required=True),
            trust=dict(choices=['L2', 'L3', 'both'], default='L2'),
            rewrite_pcp=dict(choices=['enabled', 'disabled'], default='disabled'),
            rewrite_dscp=dict(choices=['enabled', 'disabled'], default='disabled')
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def _get_interface_type(self, if_name):
        if_type = None
        if_id = None
        for interface_type, interface_regex in iteritems(self.IF_TYPE_MAP):
            match = interface_regex.match(if_name)
            if match:
                if_type = interface_type
                if_id = match.group(1)
                break
        return if_type, if_id

    def _set_interface_qos_config(self, interface_qos_config, interface, if_type, if_id):
        interface_qos_config = interface_qos_config[0].get(interface)
        trust = interface_qos_config[0].get("Trust mode")
        rewrite_dscp = interface_qos_config[0].get("DSCP rewrite")
        rewrite_pcp = interface_qos_config[0].get("PCP,DEI rewrite")

        self._current_config[interface] = dict(trust=trust, rewrite_dscp=rewrite_dscp,
                                               rewrite_pcp=rewrite_pcp, if_type=if_type, if_id=if_id)

    def _show_interface_qos(self, if_type, interface):
        cmd = "show qos interface {0} {1}".format(if_type, interface)
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        for interface in self._required_config.get("interfaces"):
            if_type, if_id = self._get_interface_type(interface)
            if not if_id:
                self._module.fail_json(
                    msg='unsupported interface: {0}'.format(interface))
            interface_qos_config = self._show_interface_qos(if_type, if_id)
            if interface_qos_config is not None:
                self._set_interface_qos_config(interface_qos_config, interface, if_type, if_id)
            else:
                self._module.fail_json(
                    msg='Interface {0} does not exist on switch'.format(interface))

    def generate_commands(self):
        trust = self._required_config.get("trust")
        rewrite_pcp = self._required_config.get("rewrite_pcp")
        rewrite_dscp = self._required_config.get("rewrite_dscp")
        for interface in self._required_config.get("interfaces"):
            ignored1, ignored2, current_trust, if_type, if_id = self._get_current_rewrite_config(interface)
            self._add_interface_trust_cmds(if_type, if_id, interface, trust, current_trust)
            self._add_interface_rewrite_cmds(if_type, if_id, interface,
                                             rewrite_pcp, rewrite_dscp)

    def _get_current_rewrite_config(self, interface):
        current_interface_qos_config = self._current_config.get(interface)
        current_rewrite_pcp = current_interface_qos_config.get('rewrite_pcp')
        current_rewrite_dscp = current_interface_qos_config.get('rewrite_dscp')
        if_type = current_interface_qos_config.get("if_type")
        if_id = current_interface_qos_config.get("if_id")
        current_trust = current_interface_qos_config.get('trust')

        return current_rewrite_pcp, current_rewrite_dscp, current_trust, if_type, if_id

    def _add_interface_trust_cmds(self, if_type, if_id, interface, trust, current_trust):

        current_rewrite_pcp, current_rewrite_dscp, ignored1, ignored2, ignored3 = self._get_current_rewrite_config(
            interface)

        if trust == "L3" and trust != current_trust:
            self._add_no_rewrite_cmd(if_type, if_id, interface, self.REWRITE_DSCP, current_rewrite_dscp)
            self._commands.append(self.TRUST_CMD.format(if_type, if_id, trust))
        elif trust == "L2" and trust != current_trust:
            self._add_no_rewrite_cmd(if_type, if_id, interface, self.REWRITE_PCP, current_rewrite_pcp)
            self._commands.append(self.TRUST_CMD.format(if_type, if_id, trust))
        elif trust == "both" and trust != current_trust:
            self._add_no_rewrite_cmd(if_type, if_id, interface, self.REWRITE_DSCP, current_rewrite_dscp)
            self._add_no_rewrite_cmd(if_type, if_id, interface, self.REWRITE_PCP, current_rewrite_pcp)
            self._commands.append(self.TRUST_CMD.format(if_type, if_id, trust))

    def _add_interface_rewrite_cmds(self, if_type, if_id, interface, rewrite_pcp, rewrite_dscp):
        current_rewrite_pcp, current_rewrite_dscp, ignored1, ignored2, ignored3 = self._get_current_rewrite_config(
            interface)

        if rewrite_pcp == "enabled" and rewrite_pcp != current_rewrite_pcp:
            self._commands.append(self.REWRITE_PCP_CMD.format(if_type, if_id))
        elif rewrite_pcp == "disabled" and rewrite_pcp != current_rewrite_pcp:
            self._commands.append(self.NO_REWRITE_PCP_CMD.format(if_type, if_id))

        if rewrite_dscp == "enabled" and rewrite_dscp != current_rewrite_dscp:
            self._commands.append(self.REWRITE_DSCP_CMD.format(if_type, if_id))
        elif rewrite_dscp == "disabled" and rewrite_dscp != current_rewrite_dscp:
            self._commands.append(self.NO_REWRITE_DSCP_CMD.format(if_type, if_id))

    def _add_no_rewrite_cmd(self, if_type, if_id, interface, rewrite_type, current_rewrite):
        if rewrite_type == self.REWRITE_PCP and current_rewrite == "enabled":
            self._commands.append(self.NO_REWRITE_PCP_CMD.format(if_type, if_id))
            self._current_config[interface]["rewrite_pcp"] = "disabled"
        elif rewrite_type == self.REWRITE_DSCP and current_rewrite == "enabled":
            self._commands.append(self.NO_REWRITE_DSCP_CMD.format(if_type, if_id))
            self._current_config[interface]["rewrite_dscp"] = "disabled"


def main():
    """ main entry point for module execution
    """
    OnyxQosModule.main()


if __name__ == '__main__':
    main()
