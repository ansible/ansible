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
module: onyx_bgp_peer_groups
version_added: "2.10"
author: "Sara Touqan (@sarato)"
short_description: Configures bgp peer groups parameters
description:
  - This module provides declarative management of bgp peer groups protocol params
    on Mellanox ONYX network devices.
options:
  peer_groups:
    type: list
    description:
      - List of bgp peer groups.
    suboptions:
      name:
        description:
          - Bgp peer group name.
        required: true
        type: str
      router_bgp:
        description:
          - configures the router-bgp number (as-number).
        type: int
        required: true
      state:
        description:
          - Indicates if the peer group should be created or should be deleted
        choices: ['present', 'absent']
        type: str
      next_hop_peer_enabled:
        description:
          - Used to decide if we want to List the peer address as next hop in routes
        type: bool
      remote_as:
        description:
          -  Specifys remote AS for dynamic peers in this IP range
      listen_range_ip_prefix:
        description:
          -  Specifys range of IP addresses to accept dynamic peering requests from
      mask_length:
        description:
          -  IP mask length.
      listen_range_state:
        description:
          - Indicates if the peer group should be created or should be deleted.
        choices: ['present', 'absent']
        type: str

  neighbors:
    type: list
    description:
      - List of bgp neighbors.
    suboptions:
      ip_address:
        description:
          - Bgp neighbor ip address.
        required: true
        type: str
      router_bgp:
        description:
          - configures the router-bgp number (as-number).
        type: int
        required: true
      group_name:
        description:
          - Bgp peer group name.
      state:
        description:
          - Indicates if the neighbor should be assigned or unassigned form the specified peer group.
        choices: ['present', 'absent']
        type: str
      next_hop_peer_enabled:
        description:
          - Used to decide if we want to List the peer address as next hop in routes
        type: bool

"""

EXAMPLES = """
- name: Creates peer group
  onyx_bgp_peer_groups:
     peer_groups:
        - name: group1
          router_bgp: 1
          state: present
- name: Deletes peer group
  onyx_bgp_peer_groups:
     peer_groups:
        - name: group1
          router_bgp: 1
          state: absent
- name: Assign a neighbor to a peer-group
  onyx_bgp_peer_groups:
     peer_groups:
        - group_name: group1
          ip_address: 1.1.1.0
          router_bgp: 1
          state: present
- name: Unassign a neighbor to a peer-group
  onyx_bgp_peer_groups:
     peer_groups:
        - group_name: group1
          ip_address: 1.1.1.0
          router_bgp: 1
          state: absent
- name: Enables next-hop for a peer-group.
  onyx_bgp_peer_groups:
     peer_groups:
        - name: group1
          next_hop_peer_enabled: yes
- name: configures listen range for a peer group
  onyx_bgp_peer_groups:
     peer_groups:
        - name: group1
          router_bgp: 1
          router_bgp: 1
          state: present
          mask_length: 24
          remote_as: 3
          listen_range_ip_prefix: 3.3.3.0

"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - neighbor <ip-address > peer-group <peer-group-name>
    - neighbor <peer-group-name> peer-group
    - no neighbor <ip-address > peer-group <peer-group-name>
    - no neighbor <peer-group-name> peer-group
    - neighbor {<ip-address> | <peer-group-name>} next-hop-peer [disable]
    - no neighbor {<ip-address> | <peer-group-name>} next-hop-peer
    - bgp listen range <ip-prefix> peer-group <peer-group-name> remote-as <as-number>
    - no bgp listen range <ip-prefix> /<mask-length> peer-group <peer-group-name>

"""

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxBgpPeerGroupsModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        peer_group_spec = dict(name=dict(required=True),
                               router_bgp=dict(type='int', required=True),
                               state=dict(choices=['present', 'absent']),
                               next_hop_peer_enabled=dict(type='bool'),
                               remote_as=dict(),
                               listen_range_ip_prefix=dict(),
                               mask_length=dict(),
                               listen_range_state=dict(choices=['present', 'absent']))
        neighbor_spec = dict(ip_address=dict(required=True),
                             router_bgp=dict(type='int', required=True),
                             group_name=dict(),
                             state=dict(choices=['present', 'absent']),
                             next_hop_peer_enabled=dict(type='bool'))
        element_spec = dict(
            peer_groups=dict(type='list', elements='dict', options=peer_group_spec),
            neighbors=dict(type='list', elements='dict', options=neighbor_spec),
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def validate_neighbor_peer_values(self):
        neighbors = self._required_config.get("neighbors")
        if neighbors is not None:
            for neighbor in neighbors:
                if neighbor.get('group_name') is None:
                    if neighbor.get('next_hop_peer_enabled') is None:
                        self._module.fail_json(msg='Missing neighbor param values, you need to enter either group_name or next_hop_peer_enabled')

        peer_groups = self._required_config.get("peer_groups")
        if peer_groups is not None:
            for group in peer_groups:
                if group.get('listen_range_ip_prefix') is not None:
                    if ((group.get('remote_as') is None) or (group.get('mask_length') is None)):
                        self._module.fail_json(msg='Missing peer-group param values, remote_as and mask_length are required for the listen range.')

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)
        self.validate_neighbor_peer_values()

    def _set_bgp_config(self, bgp_config):
        curr_config_arr = []
        bgp_config = bgp_config.get('Lines')
        if bgp_config is None:
            self._current_config['curr_config_arr'] = curr_config_arr
            return
        for runn_config in bgp_config:
            curr_config_arr.append(runn_config.strip())
        self._current_config['curr_config_arr'] = curr_config_arr

    def _show_bgp_config(self):
        cmd = "show running-config | include bgp"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        bgp_config = self._show_bgp_config()
        if bgp_config is not None:
            self._set_bgp_config(bgp_config)

    def generate_commands(self):
        curr_config_arr = self._current_config.get("curr_config_arr")
        peer_groups = self._required_config.get("peer_groups")
        neighbors = self._required_config.get("neighbors")
        if peer_groups is not None:
            for group in peer_groups:
                group_name = group.get('name')
                state = group.get('state')
                listen_range = group.get('listen_range_ip_prefix')
                remote_as = group.get('remote_as')
                listen_range_state = group.get('listen_range_state')
                mask_length = group.get('mask_length')
                router_bgp = group.get('router_bgp')
                next_hop_peer_enabled = group.get('next_hop_peer_enabled')
                if state is not None:
                    if state == "absent":
                        if ('router bgp {0} vrf default neighbor {1} peer-group' .format(router_bgp, group_name)) in curr_config_arr:
                            self._commands.append('no router bgp {0} neighbor {1} peer-group' .format(router_bgp, group_name))
                    else:
                        if ('router bgp {0} vrf default neighbor {1} peer-group' .format(router_bgp, group_name)) not in curr_config_arr:
                            self._commands.append('router bgp {0} neighbor {1} peer-group' .format(router_bgp, group_name))
                else:
                    if ('router bgp {0} vrf default neighbor {1} peer-group' .format(router_bgp, group_name)) not in curr_config_arr:
                        self._commands.append('router bgp {0} neighbor {1} peer-group' .format(router_bgp, group_name))

                if next_hop_peer_enabled is not None:
                    if next_hop_peer_enabled is True:
                        if ('router bgp {0} vrf default neighbor {1} next-hop-peer' .format(router_bgp, group_name)) not in curr_config_arr:
                            self._commands.append('router bgp {0} vrf default neighbor {1} next-hop-peer' .format(router_bgp, group_name))
                    else:
                        if ('router bgp {0} vrf default neighbor {1} next-hop-peer disable' .format(router_bgp, group_name)) not in curr_config_arr:
                            self._commands.append('router bgp {0} vrf default neighbor {1} next-hop-peer disable' .format(router_bgp, group_name))

                if listen_range is not None:
                    if listen_range_state is not None:
                        if listen_range_state is "absent":
                            if ('router bgp {0} vrf default bgp listen range {1} /{2} peer-group {3} remote-as {4}' .format(router_bgp, listen_range,
                                                                                                                            mask_length, group_name,
                                                                                                                            remote_as)) in curr_config_arr:
                                self._commands.append('no router bgp {0} bgp listen range {1} /{2} peer-group {3}' .format(router_bgp, listen_range,
                                                                                                                           mask_length, group_name))
                        else:
                            if ('router bgp {0} vrf default bgp listen range {1} /{2} peer-group {3} remote-as {4}' .format(router_bgp, listen_range,
                                                                                                                            mask_length, group_name,
                                                                                                                            remote_as)) not in curr_config_arr:
                                self._commands.append('router bgp {0} bgp listen range {1} /{2} peer-group {3} remote-as {4}' .format(router_bgp, listen_range,
                                                                                                                                      mask_length, group_name,
                                                                                                                                      remote_as))
                    else:
                        if ('router bgp {0} vrf default bgp listen range {1} /{2} peer-group {3} remote-as {4}' .format(router_bgp, listen_range, mask_length,
                                                                                                                        group_name,
                                                                                                                        remote_as)) not in curr_config_arr:
                            self._commands.append('router bgp {0} bgp listen range {1} /{2} peer-group {3} remote-as {4}' .format(router_bgp, listen_range,
                                                                                                                                  mask_length, group_name,
                                                                                                                                  remote_as))

        if neighbors is not None:
            for neighbor in neighbors:
                address = neighbor.get('ip_address')
                group_name = neighbor.get('group_name')
                router_bgp = neighbor.get('router_bgp')
                state = neighbor.get('state')
                next_hop_peer_enabled = neighbor.get('next_hop_peer_enabled')
                if group_name is not None:
                    if state is not None:
                        if state == "absent":
                            if ('router bgp {0} vrf default neighbor {1} peer-group {2}' .format(router_bgp, address, group_name)) in curr_config_arr:
                                self._commands.append('no router bgp {0} neighbor {1} peer-group {2}' .format(router_bgp, address, group_name))
                        else:
                            if ('router bgp {0} vrf default neighbor {1} peer-group {2}' .format(router_bgp, address, group_name)) not in curr_config_arr:
                                self._commands.append('router bgp {0} neighbor {1} peer-group {2}' .format(router_bgp, address, group_name))
                    else:
                        if ('router bgp {0} vrf default neighbor {1} peer-group {2}' .format(router_bgp, address, group_name)) not in curr_config_arr:
                            self._commands.append('router bgp {0} neighbor {1} peer-group {2}' .format(router_bgp, address, group_name))
                if next_hop_peer_enabled is not None:
                    if next_hop_peer_enabled is True:
                        if ('router bgp {0} vrf default neighbor {1} next-hop-peer' .format(router_bgp, address)) not in curr_config_arr:
                            self._commands.append('router bgp {0} vrf default neighbor {1} next-hop-peer' .format(router_bgp, address))
                    else:
                        if ('router bgp {0} vrf default neighbor {1} next-hop-peer disable' .format(router_bgp, address)) not in curr_config_arr:
                            self._commands.append('router bgp {0} vrf default neighbor {1} next-hop-peer disable' .format(router_bgp, address))


def main():
    """ main entry point for module execution
    """
    OnyxBgpPeerGroupsModule.main()


if __name__ == '__main__':
    main()
