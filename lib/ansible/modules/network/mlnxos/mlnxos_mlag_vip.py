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

from ansible.module_utils.mlnxos import show_cmd
from ansible.module_utils.mlnxos import mlnxos_argument_spec
from ansible.modules.network.mlnxos import BaseMlnxosApp


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_mlag_vip
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: configures MLAG VIP on mlnxos network devices
description:
  - This module provides declarative management of MLAG virtual IPs
    on MLNX-OS network devices.
notes:
  -
  =dict(),
            group_name=dict(),

options:
  ipaddress:
    description:
      - virtual IP address of the MLAG.
    required: true if state is present
  group_name:
    description:
      - MLAG group name
    required: true if state is present
  mac_address:
    description:
      - MLAG system mac address
    required: true if state is present
  state:
    description:
      - MLAG VIP state.
    choices: ['present', 'absent'].
"""

EXAMPLES = """
- name: configure mlag-vip
  mlnxos_mlag_vip:
    ipaddress: 50.3.3.1/24
    group_name: ansible-test-group
    mac_address: 00:11:12:23:34:45
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to
  type: list
  sample:
    - mlag-vip ansible_test_group ip 50.3.3.1 /24 force
    - no mlag shutdown
"""


class MlnxosLagApp(BaseMlnxosApp):
    LAG_ID_REGEX = re.compile(r"^(.*)(Po|Mpo)(\d+)(.*)$")
    IF_NAME_REGEX = re.compile(r"^Eth(\d+\/\d+)(.*)$")

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            ipaddress=dict(),
            group_name=dict(),
            mac_address=dict(),
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
        lag_params = {
            'ipaddress': module_params['ipaddress'],
            'group_name': module_params['group_name'],
            'mac_address': module_params['mac_address'],
            'state': module_params['state'],
        }

        self.validate_param_values(lag_params)
        self._required_config = lag_params

    def load_current_config(self):
        cmd = "show mlag"
        mlag_config = show_cmd(
            self._module, cmd, json_fmt=True, fail_on_error=False)
        cmd = "show mlag-vip"
        mlag_vip_config = show_cmd(
            self._module, cmd, json_fmt=True, fail_on_error=False)
        self._current_config = {}
        if mlag_vip_config:
            mlag_vip = mlag_vip_config.get("MLAG-VIP", {})
            self._current_config['group_name'] = \
                mlag_vip.get("MLAG group name")
            self._current_config['ipaddress'] = \
                mlag_vip.get("MLAG VIP address")
        if mlag_config:
            self._current_config['mac_address'] = \
                mlag_config.get("System-mac")

    def generate_commands(self):
        state = self._required_config['state']
        if state == 'present':
            self._generate_mlag_vip_cmds()
        else:
            self._generate_no_mlag_vip_cmds()
        if self._commands:
            self._commands.append('exit')

    def _generate_mlag_vip_cmds(self):
        current_group = self._current_config.get('group_name')
        current_ip = self._current_config.get('ipaddress')
        current_mac = self._current_config.get('mac_address')

        req_group = self._required_config.get('group_name')
        req_ip = self._required_config.get('ipaddress')
        req_mac = self._required_config.get('mac_address')

        if req_group != current_group or req_ip != current_ip:
            ip, mask = req_ip.split('/')
            self._commands.append(
                'mlag-vip %s ip %s /%s force' % (req_group, ip, mask))
        if req_mac != current_mac:
            self._commands.append(
                'mlag system-mac %s' % (req_mac))
        if self._commands:
            self._commands.append('no mlag shutdown')





    def _generate_no_mlag_vip_cmds(self):
        if self._current_config.get('group_name'):
            self._commands.append('no mlag-vip')


if __name__ == '__main__':
    MlnxosLagApp.main()
