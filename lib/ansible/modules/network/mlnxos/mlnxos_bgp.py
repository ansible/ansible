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

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.mlnxos import get_bgp_summary
from ansible.module_utils.mlnxos import mlnxos_argument_spec
from ansible.modules.network.mlnxos import BaseMlnxosApp


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_bgp
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: configuresBGP mlnxos network devices
description:
  - This module provides declarative management of BGP router and neighbors
    on MLNX-OS network devices.
notes:
  -
options:
  as_number:
    description:
      - local AS number.
    required: true
  router_id:
    description:
      - router IP address
    required: true
  neighbors:
    description:
      - list of neighbors
    suboptions:
      remote_as:
        description:
          - local AS number
        required: true
      neighbor:
        description:
          - neighbor IP address
        required: true
  state:
    description:
      - BGP state.
    choices: ['present', 'absent'].
"""

EXAMPLES = """
- name: configure bgp
  mlnxos_bgp:
    as_number: 320
    router_id: 10.3.3.3
    neighbors:
      - remote_as: 321
        neighbor: 10.3.3.4
    state: present
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
    - exit
"""


class MlnxosLagApp(BaseMlnxosApp):
    LOCAL_AS_REGEX = \
        r"BGP router identifier ([0-9\.]+), local AS number (\d+)"
    NEIGHBOR_REGEX = \
        r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+\d+\s+(\d+)"

    def init_module(self):
        """ initialize module
        """
        neighbor_spec = dict(
            remote_as=dict(type='int'),
            neighbor=dict(),
        )
        element_spec = dict(
            as_number=dict(type='int'),
            router_id=dict(),
            neighbors=dict(type='list', elements='dict',
                           options=neighbor_spec),
            state=dict(choices=['present', 'absent'], default='present'),
        )
        argument_spec = dict()

        argument_spec.update(element_spec)
        argument_spec.update(mlnxos_argument_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        bgp_params = {
            'as_number': module_params['as_number'],
            'router_id': module_params['router_id'],
            'state': module_params['state'],
        }
        neighbors = module_params['neighbors'] or []
        req_neighbors = bgp_params['neighbors'] = []
        for neighbor_data in neighbors:
            req_neighbors.append(
                (neighbor_data['neighbor'], neighbor_data['remote_as']))
        self.validate_param_values(bgp_params)
        self._required_config = bgp_params

    def _set_bgp_config(self, bgp_config):
        match = re.search(self.LOCAL_AS_REGEX, bgp_config, re.M)
        if match:
            self._current_config['router_id'] = match.group(1)
            self._current_config['as_number'] = int(match.group(2))
        matches = re.findall(self.NEIGHBOR_REGEX, bgp_config, re.M) or []
        neighbors = self._current_config['neighbors'] = []
        for match in matches:
            neighbors.append((match[0], int(match[1])))

    def load_current_config(self):
        self._current_config = dict()
        bgp_config = get_bgp_summary(self._module)
        if bgp_config:
            self._set_bgp_config(bgp_config)

    def generate_commands(self):
        state = self._required_config['state']
        if state == 'present':
            self._generate_bgp_cmds()
        else:
            self._generate_no_bgp_cmds()
        if self._commands:
            self._commands.append('exit')

    def _generate_bgp_cmds(self):
        as_number = self._required_config['as_number']
        curr_as_num = self._current_config.get('as_number')
        bgp_removed = False
        if curr_as_num != as_number:
            if curr_as_num:
                self._commands.append('no router bgp %d' % curr_as_num)
                bgp_removed = True
            else:
                self._commands.append('router bgp %d' % as_number)
                self._commands.append('exit')
        curr_route_id = self._current_config.get('router_id')
        req_router_id = self._required_config['router_id']
        if req_router_id and req_router_id != curr_route_id:
            self._commands.append('router bgp %d router-id %s force' %
                                  (as_number, req_router_id))

        req_neighbors = self._required_config['neighbors']
        curr_neighbors = self._current_config.get('neighbors', [])
        if not bgp_removed:
            for neighbor_data in curr_neighbors:
                if neighbor_data not in req_neighbors:
                    (neighbor, remote_as) = neighbor_data
                    self._commands.append(
                        'router bgp %s no neighbor %s remote-as %s' %
                        (as_number, neighbor, remote_as))

        for neighbor_data in req_neighbors:
            if neighbor_data not in curr_neighbors:
                (neighbor, remote_as) = neighbor_data
                self._commands.append(
                    'router bgp %s neighbor %s remote-as %s' %
                    (as_number, neighbor, remote_as))

    def _generate_no_bgp_cmds(self):
        as_number = self._required_config['as_number']
        curr_as_num = self._current_config.get('as_number')
        if curr_as_num and curr_as_num == as_number:
            self._commands.append('no router bgp %d' % as_number)


if __name__ == '__main__':
    MlnxosLagApp.main()
