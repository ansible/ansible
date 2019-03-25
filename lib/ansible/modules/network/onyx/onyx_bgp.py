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
module: onyx_bgp
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Configures BGP on Mellanox ONYX network devices
description:
  - This module provides declarative management of BGP router and neighbors
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.4000
options:
  as_number:
    description:
      - Local AS number.
    required: true
  router_id:
    description:
      - Router IP address. Required if I(state=present).
  neighbors:
    description:
      - List of neighbors. Required if I(state=present).
    suboptions:
      remote_as:
        description:
          - Remote AS number.
        required: true
      neighbor:
        description:
          - Neighbor IP address.
        required: true
  networks:
    description:
      - List of advertised networks.
  state:
    description:
      - BGP state.
    default: present
    choices: ['present', 'absent']
  purge:
    description:
      - will remove all neighbors when it is True.
    type: bool
    default: false
    version_added: 2.8
"""

EXAMPLES = """
- name: configure bgp
  onyx_bgp:
    as_number: 320
    router_id: 10.3.3.3
    neighbors:
      - remote_as: 321
        neighbor: 10.3.3.4
    purge: True
    state: present
    networks:
      - 172.16.1.0/24
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - router bgp 172
    - exit
    - router bgp 172 router-id 2.3.4.5 force
    - router bgp 172 neighbor 2.3.4.6 remote-as 173
    - router bgp 172 network 172.16.1.0 /24
"""

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import get_bgp_summary
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxBgpModule(BaseOnyxModule):
    LOCAL_AS_REGEX = re.compile(r'^\s+router bgp\s+(\d+).*')
    ROUTER_ID_REGEX = re.compile(
        r'^\s+router bgp\s+(\d+).*router-id\s+(\S+)\s+.*')
    NEIGHBOR_REGEX = re.compile(
        r'^\s+router bgp\s+(\d+).*neighbor\s+(\S+)\s+remote\-as\s+(\S+).*')
    NETWORK_REGEX = re.compile(
        r'^\s+router bgp\s+(\d+).*network\s+(\S+)\s+(\S+).*')
    _purge = False

    def init_module(self):
        """ initialize module
        """
        neighbor_spec = dict(
            remote_as=dict(type='int', required=True),
            neighbor=dict(required=True),
        )
        element_spec = dict(
            as_number=dict(type='int', required=True),
            router_id=dict(),
            neighbors=dict(type='list', elements='dict',
                           options=neighbor_spec),
            networks=dict(type='list', elements='str'),
            state=dict(choices=['present', 'absent'], default='present'),
            purge=dict(default=False, type='bool'),
        )
        argument_spec = dict()

        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        req_neighbors = list()
        self._required_config = dict(
            as_number=module_params['as_number'],
            router_id=module_params['router_id'],
            state=module_params['state'],
            neighbors=req_neighbors,
            networks=module_params['networks'])
        neighbors = module_params['neighbors'] or list()
        self._purge = module_params.get('purge', False)
        for neighbor_data in neighbors:
            req_neighbors.append(
                (neighbor_data['neighbor'], neighbor_data['remote_as']))
        self.validate_param_values(self._required_config)

    def _set_bgp_config(self, bgp_config):
        lines = bgp_config.split('\n')
        self._current_config['router_id'] = None
        self._current_config['as_number'] = None
        neighbors = self._current_config['neighbors'] = []
        networks = self._current_config['networks'] = []
        for line in lines:
            if line.startswith('#'):
                continue
            if not self._current_config['as_number']:
                match = self.LOCAL_AS_REGEX.match(line)
                if match:
                    self._current_config['as_number'] = int(match.group(1))
                    continue
            if not self._current_config['router_id']:
                match = self.ROUTER_ID_REGEX.match(line)
                if match:
                    self._current_config['router_id'] = match.group(2)
                    continue
            match = self.NEIGHBOR_REGEX.match(line)
            if match:
                neighbors.append((match.group(2), int(match.group(3))))
                continue
            match = self.NETWORK_REGEX.match(line)
            if match:
                network = match.group(2) + match.group(3)
                networks.append(network)
                continue

    def _get_bgp_summary(self):
        return get_bgp_summary(self._module)

    def load_current_config(self):
        self._current_config = dict()
        bgp_config = self._get_bgp_summary()
        if bgp_config:
            self._set_bgp_config(bgp_config)

    def generate_commands(self):
        state = self._required_config['state']
        if state == 'present':
            self._generate_bgp_cmds()
        else:
            self._generate_no_bgp_cmds()

    def _generate_bgp_cmds(self):
        as_number = self._required_config['as_number']
        curr_as_num = self._current_config.get('as_number')
        bgp_removed = False
        if curr_as_num != as_number:
            if curr_as_num:
                self._commands.append('no router bgp %d' % curr_as_num)
                bgp_removed = True
            self._commands.append('router bgp %d' % as_number)
            self._commands.append('exit')
        curr_route_id = self._current_config.get('router_id')
        req_router_id = self._required_config['router_id']
        if req_router_id and req_router_id != curr_route_id or bgp_removed:
            self._commands.append('router bgp %d router-id %s force' %
                                  (as_number, req_router_id))
        self._generate_neighbors_cmds(as_number, bgp_removed)
        self._generate_networks_cmds(as_number, bgp_removed)

    def _generate_neighbors_cmds(self, as_number, bgp_removed):
        req_neighbors = self._required_config['neighbors']
        curr_neighbors = self._current_config.get('neighbors', [])
        if self._purge:
            for neighbor_data in curr_neighbors:
                (neighbor, remote_as) = neighbor_data
                self._commands.append('router bgp %s no neighbor %s remote-as %s' % (as_number, neighbor, remote_as))

        for neighbor_data in req_neighbors:
            if bgp_removed or neighbor_data not in curr_neighbors:
                (neighbor, remote_as) = neighbor_data
                self._commands.append(
                    'router bgp %s neighbor %s remote-as %s' %
                    (as_number, neighbor, remote_as))

    def _generate_networks_cmds(self, as_number, bgp_removed):
        req_networks = self._required_config['networks'] or []
        curr_networks = self._current_config.get('networks', [])
        if not bgp_removed:
            for network in curr_networks:
                if network not in req_networks:
                    net_attrs = network.split('/')
                    if len(net_attrs) != 2:
                        self._module.fail_json(
                            msg='Invalid network %s' % network)

                    net_address, netmask = net_attrs
                    cmd = 'router bgp %s no network %s /%s' % (
                        as_number, net_address, netmask)
                    self._commands.append(cmd)

        for network in req_networks:
            if bgp_removed or network not in curr_networks:
                net_attrs = network.split('/')
                if len(net_attrs) != 2:
                    self._module.fail_json(
                        msg='Invalid network %s' % network)
                net_address, netmask = net_attrs
                cmd = 'router bgp %s network %s /%s' % (
                    as_number, net_address, netmask)
                self._commands.append(cmd)

    def _generate_no_bgp_cmds(self):
        as_number = self._required_config['as_number']
        curr_as_num = self._current_config.get('as_number')
        if curr_as_num and curr_as_num == as_number:
            self._commands.append('no router bgp %d' % as_number)


def main():
    """ main entry point for module execution
    """
    OnyxBgpModule.main()


if __name__ == '__main__':
    main()
