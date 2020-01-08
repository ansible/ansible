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
module: onyx_bfd
version_added: "2.10"
author: "Sara Touqan (@sarato)"
short_description: Configures BFD parameters
description:
  - This module provides declarative management of BFD protocol params
    on Mellanox ONYX network devices.
options:
  shutdown:
    description:
      - Administratively shut down BFD protection.
    type: bool
  vrf:
    description:
      - Specifys the vrf name.
    type: str
  interval_min_rx:
    description:
      - Minimum desired receive rate, should be between 50 and 6000.
    type: int
  interval_multiplier:
    description:
      - Desired detection multiplier, should be between 3 and 50.
    type: int
  interval_transmit_rate:
    description:
      - Minimum desired transmit rate, should be between 50 and 60000.
    type: int
  iproute_network_prefix:
    description:
      - Configures the ip route network prefix, e.g 1.1.1.1.
    type: str
  iproute_mask_length:
    description:
      - Configures the mask length of the ip route network prefix, e.g 24.
    type: int
  iproute_next_hop:
    description:
      - Configures the ip route next hop, e.g 2.2.2.2.
    type: str
"""

EXAMPLES = """
- name: configures bfd
  onyx_bfd:
    shutdown: yes
    vrf: 5
    interval_min_rx: 55
    interval_multiplier: 8
    interval_transmit_rate: 88
    iproute_network_prefix: 1.1.1.0
    iproute_mask_length: 24
    iproute_next_hop: 3.2.2.2
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - ip bfd shutdown
    - no ip bfd shutdown
    - ip bfd shutdown vrf <vrf_name>
    - no ip bfd shutdown vrf <vrf_name>
    - ip bfd vrf <vrf_name> interval min-rx <min_rx> multiplier <multiplier> transmit-rate <transmit_rate> force
    - ip bfd interval min-rx <min_rx> multiplier <multiplier> transmit-rate <transmit_rate> force
    - ip route vrf <vrf_name> <network_prefix>/<mask_length> <next_hop> bfd
    - ip route <network_prefix>/<mask_length> <next_hop> bfd
"""

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxBFDModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            shutdown=dict(type='bool'),
            vrf=dict(type='str'),
            interval_min_rx=dict(type='int'),
            interval_multiplier=dict(type='int'),
            interval_transmit_rate=dict(type='int'),
            iproute_network_prefix=dict(type='str'),
            iproute_mask_length=dict(type='int'),
            iproute_next_hop=dict(type='str'),
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_together=[
                              ['interval_min_rx', 'interval_multiplier', 'interval_transmit_rate'],
                              ['iproute_network_prefix', 'iproute_mask_length', 'iproute_next_hop']])

    def validate_bfd_interval_values(self):
        interval_min_rx = self._required_config.get('interval_min_rx')
        if interval_min_rx:
            if ((interval_min_rx < 50) or (interval_min_rx > 6000)):
                self._module.fail_json(msg='Receive interval should be between 50 and 6000.')
        interval_multiplier = self._required_config.get('interval_multiplier')
        if interval_multiplier:
            if ((interval_multiplier < 3) or (interval_multiplier > 50)):
                self._module.fail_json(msg='Multiplier should be between 3 and 50.')
        interval_transmit_rate = self._required_config.get('interval_transmit_rate')
        if interval_transmit_rate:
            if ((interval_transmit_rate < 50) or (interval_transmit_rate > 60000)):
                self._module.fail_json(msg='Transmit interval should be between 50 and 60000.')

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)
        self.validate_bfd_interval_values()

    def _set_bfd_config(self, bfd_config):
        curr_config_arr = []
        bfd_config = bfd_config.get('Lines')
        if bfd_config is None:
            return
        for runn_config in bfd_config:
            curr_config_arr.append(runn_config.strip())
        if 'ip bfd shutdown vrf default' in curr_config_arr:
            self._current_config['bfd_shutdown'] = True
        else:
            self._current_config['bfd_shutdown'] = False
        self._current_config['curr_config_arr'] = curr_config_arr

    def _show_bfd_config(self):
        cmd = "show running-config | include bfd"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        bfd_config = self._show_bfd_config()
        if bfd_config:
            self._set_bfd_config(bfd_config)

    def generate_shutdown_commands(self, curr_config_arr):
        shutdown_enabled = self._required_config.get('shutdown')
        vrf_name = self._required_config.get('vrf')
        current_shutdown = self._current_config.get("bfd_shutdown")
        if shutdown_enabled is not None:
            if vrf_name is not None:
                if curr_config_arr is not None:
                    if ('ip bfd shutdown vrf {0}' .format(vrf_name)) not in curr_config_arr:
                        if shutdown_enabled is True:
                            self._commands.append('ip bfd shutdown vrf {0}' .format(vrf_name))
                else:
                    if shutdown_enabled is False:
                        self._commands.append('no ip bfd shutdown vrf {0}' .format(vrf_name))
            else:
                if ((current_shutdown is not None and (current_shutdown != shutdown_enabled)) or (current_shutdown is None)):
                    if shutdown_enabled is True:
                        self._commands.append('ip bfd shutdown')
                    else:
                        self._commands.append('no ip bfd shutdown')

    def generate_interval_commands(self, curr_config_arr):
        interval_min_rx = self._required_config.get('interval_min_rx')
        interval_multiplier = self._required_config.get('interval_multiplier')
        interval_transmit_rate = self._required_config.get('interval_transmit_rate')
        vrf_name = self._required_config.get('vrf')
        if ((interval_min_rx is not None) and (interval_multiplier is not None) and (interval_transmit_rate is not None)):
            if vrf_name is not None:
                if curr_config_arr is not None:
                    if ((('ip bfd vrf {0} interval transmit-rate {1} force' .format(vrf_name, interval_transmit_rate)) not in curr_config_arr) or
                       (('ip bfd vrf {0} interval min-rx {1} force' .format(vrf_name, interval_min_rx)) not in curr_config_arr) or
                       (('ip bfd vrf {0} interval multiplier {1} force' .format(vrf_name, interval_multiplier)) not in curr_config_arr)):
                        self._commands.append('ip bfd vrf {0} interval min-rx {1} multiplier {2} transmit-rate {3} force'
                                              .format(vrf_name, interval_min_rx, interval_multiplier, interval_transmit_rate))
                else:
                    self._commands.append('ip bfd vrf {0} interval min-rx {1} multiplier {2} transmit-rate {3} force'
                                          .format(vrf_name, interval_min_rx, interval_multiplier, interval_transmit_rate))
            else:
                if curr_config_arr is not None:
                    if ((('ip bfd vrf default interval transmit-rate {0} force' .format(interval_transmit_rate)) not in curr_config_arr) or
                       (('ip bfd vrf default interval min-rx {0} force' .format(interval_min_rx)) not in curr_config_arr) or
                       (('ip bfd vrf default interval multiplier {0} force' .format(interval_multiplier)) not in curr_config_arr)):
                        self._commands.append('ip bfd interval min-rx {0} multiplier {1} transmit-rate {2} force'
                                              .format(interval_min_rx, interval_multiplier, interval_transmit_rate))
                else:
                    self._commands.append('ip bfd interval min-rx {0} multiplier {1} transmit-rate {2} force'
                                          .format(interval_min_rx, interval_multiplier, interval_transmit_rate))

    def generate_iproute_commands(self, curr_config_arr):
        iproute_network_prefix = self._required_config.get('iproute_network_prefix')
        iproute_mask_length = self._required_config.get('iproute_mask_length')
        iproute_next_hop = self._required_config.get('iproute_next_hop')
        vrf_name = self._required_config.get('vrf')
        if ((iproute_network_prefix is not None) and (iproute_mask_length is not None) and
           (iproute_next_hop is not None)):
            if vrf_name is not None:
                if curr_config_arr is not None:
                    if ('ip route vrf {0} {1}/{2} {3} bfd' .format(vrf_name, iproute_network_prefix,
                                                                   iproute_mask_length, iproute_next_hop)) not in curr_config_arr:
                        self._commands.append('ip route vrf {0} {1} /{2} {3} bfd'
                                              .format(vrf_name, iproute_network_prefix, iproute_mask_length, iproute_next_hop))
                else:
                    self._commands.append('ip route vrf {0} {1} /{2} {3} bfd' .format(vrf_name, iproute_network_prefix, iproute_mask_length, iproute_next_hop))
            else:
                if curr_config_arr is not None:
                    if ('ip route vrf default {0}/{1} {2} bfd' .format(iproute_network_prefix,
                                                                       iproute_mask_length, iproute_next_hop)) not in curr_config_arr:
                        self._commands.append('ip route {0} /{1} {2} bfd' .format(iproute_network_prefix, iproute_mask_length, iproute_next_hop))
                else:
                    self._commands.append('ip route {0} /{1} {2} bfd' .format(iproute_network_prefix, iproute_mask_length, iproute_next_hop))

    def generate_commands(self):
        curr_config_arr = self._current_config.get("curr_config_arr")
        self.generate_shutdown_commands(curr_config_arr)
        self.generate_interval_commands(curr_config_arr)
        self.generate_iproute_commands(curr_config_arr)


def main():
    """ main entry point for module execution
    """
    OnyxBFDModule.main()


if __name__ == '__main__':
    main()
