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
module: onyx_mlag_vip
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Configures MLAG VIP on Mellanox ONYX network devices
description:
  - This module provides declarative management of MLAG virtual IPs
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.4000
options:
  ipaddress:
    description:
      - Virtual IP address of the MLAG. Required if I(state=present).
  group_name:
    description:
      - MLAG group name. Required if I(state=present).
  mac_address:
    description:
      - MLAG system MAC address. Required if I(state=present).
  state:
    description:
      - MLAG VIP state.
    choices: ['present', 'absent']
  delay:
    description:
      - Delay interval, in seconds, waiting for the changes on mlag VIP to take
        effect.
    default: 12
"""

EXAMPLES = """
- name: configure mlag-vip
  onyx_mlag_vip:
    ipaddress: 50.3.3.1/24
    group_name: ansible-test-group
    mac_address: 00:11:12:23:34:45
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - mlag-vip ansible_test_group ip 50.3.3.1 /24 force
    - no mlag shutdown
"""

import time

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxMLagVipModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            ipaddress=dict(),
            group_name=dict(),
            mac_address=dict(),
            delay=dict(type='int', default=12),
            state=dict(choices=['present', 'absent'], default='present'),
        )
        argument_spec = dict()

        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        lag_params = {
            'ipaddress': module_params['ipaddress'],
            'group_name': module_params['group_name'],
            'mac_address': module_params['mac_address'],
            'delay': module_params['delay'],
            'state': module_params['state'],
        }

        self.validate_param_values(lag_params)
        self._required_config = lag_params

    def _show_mlag_cmd(self, cmd):
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def _show_mlag(self):
        cmd = "show mlag"
        return self._show_mlag_cmd(cmd)

    def _show_mlag_vip(self):
        cmd = "show mlag-vip"
        return self._show_mlag_cmd(cmd)

    def load_current_config(self):
        self._current_config = dict()
        mlag_config = self._show_mlag()
        mlag_vip_config = self._show_mlag_vip()
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

    def _generate_mlag_vip_cmds(self):
        current_group = self._current_config.get('group_name')
        current_ip = self._current_config.get('ipaddress')
        current_mac = self._current_config.get('mac_address')
        if current_mac:
            current_mac = current_mac.lower()

        req_group = self._required_config.get('group_name')
        req_ip = self._required_config.get('ipaddress')
        req_mac = self._required_config.get('mac_address')
        if req_mac:
            req_mac = req_mac.lower()

        if req_group != current_group or req_ip != current_ip:
            ipaddr, mask = req_ip.split('/')
            self._commands.append(
                'mlag-vip %s ip %s /%s force' % (req_group, ipaddr, mask))
        if req_mac != current_mac:
            self._commands.append(
                'mlag system-mac %s' % (req_mac))
        if self._commands:
            self._commands.append('no mlag shutdown')

    def _generate_no_mlag_vip_cmds(self):
        if self._current_config.get('group_name'):
            self._commands.append('no mlag-vip')

    def check_declarative_intent_params(self, result):
        if not result['changed']:
            return
        delay_interval = self._required_config.get('delay')
        if delay_interval > 0:
            time.sleep(delay_interval)
            for cmd in ("show mlag-vip", ""):
                show_cmd(self._module, cmd, json_fmt=False, fail_on_error=False)


def main():
    """ main entry point for module execution
    """
    OnyxMLagVipModule.main()


if __name__ == '__main__':
    main()
