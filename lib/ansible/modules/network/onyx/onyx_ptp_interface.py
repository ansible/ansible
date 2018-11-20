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
module: onyx_ptp_interface
version_added: '2.8'
author: 'Anas Badaha (@anasb)'
short_description: 'Configures PTP on interface'
description:
    - "This module provides declarative management of PTP interfaces configuration\non Mellanox ONYX network devices."
notes:
    - 'Tested on ONYX 3.6.8130'
    - 'PTP Protocol must be enabled on switch.'
    - 'Interface must not be a switch port interface.'
options:
    name:
        description:
            - 'ethernet or vlan interface name that we want to configure PTP on it'
        required: true
    state:
        description:
            - 'Enable/Disable PTP on Interface'
        default: enabled
        choices:
            - enabled
            - disabled
    delay_request:
        description:
            - 'configure PTP delay request interval, Range 0-5'
    announce_interval:
        description:
            - 'configure PTP announce setting for interval, Range -3-1'
    announce_timeout:
        description:
            - 'configure PTP announce setting for timeout, Range 2-10'
    sync_interval:
        description:
            - 'configure PTP sync interval, Range -7--1'
"""

EXAMPLES = """
- name: configure PTP interface
  onyx_ptp_interface:
    state: enabled
    name: Eth1/1
    delay_request: 0
    announce_interval: -2
    announce_timeout: 3
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface ethernet 1/16 ptp enable
    - interface ethernet 1/16 ptp delay-req interval 0
    - interface ethernet 1/16 ptp announce interval -1
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxPtpInterfaceModule(BaseOnyxModule):
    IF_ETH_REGEX = re.compile(r"^Eth(\d+\/\d+|Eth\d+\/\d+\d+)$")
    IF_VLAN_REGEX = re.compile(r"^Vlan (\d+)$")

    IF_TYPE_ETH = "ethernet"
    IF_TYPE_VLAN = "vlan"

    IF_TYPE_MAP = {
        IF_TYPE_ETH: IF_ETH_REGEX,
        IF_TYPE_VLAN: IF_VLAN_REGEX
    }

    RANGE_ATTR = {
        "delay_request": (0, 5),
        "announce_interval": (-3, -1),
        "announce_timeout": (2, 10),
        "sync_interval": (-7, -1)
    }

    _interface_type = None
    _interface_id = None

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            name=dict(required=True),
            state=dict(choices=['enabled', 'disabled'], default='enabled'),
            delay_request=dict(type=int),
            announce_interval=dict(type=int),
            announce_timeout=dict(type=int),
            sync_interval=dict(type=int)
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    @classmethod
    def _get_interface_type(cls, if_name):
        if_type = None
        if_id = None
        for interface_type, interface_regex in iteritems(cls.IF_TYPE_MAP):
            match = interface_regex.match(if_name)
            if match:
                if_type = interface_type
                if_id = match.group(1)
                break
        return if_type, if_id

    def _set_if_type(self, module_params):
        if_name = module_params['name']
        self._interface_type, self._interface_id = self._get_interface_type(if_name)
        if not self._interface_id:
            self._module.fail_json(
                msg='unsupported interface name/type: %s' % if_name)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self._set_if_type(self._required_config)
        self.validate_param_values(self._required_config)

    def _validate_attr_is_not_none(self, attr_name, attr_value):
        if attr_value is not None:
            self._module.fail_json(msg='Can not set %s value on switch while state is disabled' % attr_name)

    def validate_param_values(self, obj, param=None):
        if obj['state'] == 'disabled':
            for attr_name in self.RANGE_ATTR:
                self._validate_attr_is_not_none(attr_name, obj[attr_name])
        super(OnyxPtpInterfaceModule, self).validate_param_values(obj, param)

    def _validate_range(self, value, attr_name):
        min_value, max_value = self.RANGE_ATTR[attr_name]
        if value and not min_value <= int(value) <= max_value:
            self._module.fail_json(msg='%s value must be between %d and %d' % (attr_name, min_value, max_value))

    def validate_delay_request(self, value):
        self._validate_range(value, "delay_request")

    def validate_announce_interval(self, value):
        self._validate_range(value, "announce_interval")

    def validate_announce_timeout(self, value):
        self._validate_range(value, "announce_timeout")

    def validate_sync_interval(self, value):
        self._validate_range(value, "sync_interval")

    def _set_ptp_interface_config(self, ptp_interface_config):
        if ptp_interface_config is None:
            self._current_config['state'] = 'disabled'
            return
        ptp_interface_config = ptp_interface_config[0]
        self._current_config['state'] = 'enabled'
        self._current_config['delay_request'] = int(ptp_interface_config['Delay request interval(log mean)'])
        self._current_config['announce_interval'] = int(ptp_interface_config['Announce interval(log mean)'])
        self._current_config['announce_timeout'] = int(ptp_interface_config['Announce receipt time out'])
        self._current_config['sync_interval'] = int(ptp_interface_config['Sync interval(log mean)'])

    def _show_ptp_interface_config(self):
        cmd = "show ptp interface %s %s" % (self._interface_type, self._interface_id)
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        ptp_interface_config = self._show_ptp_interface_config()
        self._set_ptp_interface_config(ptp_interface_config)

    def _generate_attr_command(self, attr_name, attr_cmd_name):
        attr_val = self._required_config.get(attr_name)
        if attr_val is not None:
            curr_val = self._current_config.get(attr_name)
            if attr_val != curr_val:
                self._commands.append(
                    'interface %s %s ptp %s %d' % (self._interface_type, self._interface_id, attr_cmd_name, attr_val))

    def generate_commands(self):
        state = self._required_config.get("state", "enabled")
        self._gen_ptp_commands(state)

        self._generate_attr_command("delay_request", "delay-req interval")
        self._generate_attr_command("announce_interval", "announce interval")
        self._generate_attr_command("announce_timeout", "announce timeout")
        self._generate_attr_command("sync_interval", "sync interval")

    def _add_if_ptp_cmd(self, req_state):
        if req_state == 'enabled':
            if_ptp_cmd = 'interface %s %s ptp enable' % (self._interface_type, self._interface_id)
        else:
            if_ptp_cmd = 'no interface %s %s ptp enable' % (self._interface_type, self._interface_id)
        self._commands.append(if_ptp_cmd)

    def _gen_ptp_commands(self, req_state):
        curr_state = self._current_config.get('state')
        if curr_state != req_state:
            self._add_if_ptp_cmd(req_state)


def main():
    """ main entry point for module execution
    """
    OnyxPtpInterfaceModule.main()


if __name__ == '__main__':
    main()
