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
module: onyx_l3_interface
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage L3 interfaces on Mellanox ONYX network devices
description:
  - This module provides declarative management of L3 interfaces
    on Mellanox ONYX network devices.
options:
  name:
    description:
      - Name of the L3 interface.
  ipv4:
    description:
      - IPv4 of the L3 interface.
  ipv6:
    description:
      - IPv6 of the L3 interface (not supported for now).
  aggregate:
    description: List of L3 interfaces definitions
  purge:
    description:
      - Purge L3 interfaces not defined in the I(aggregate) parameter.
    default: false
    type: bool
  state:
    description:
      - State of the L3 interface configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Set Eth1/1 IPv4 address
  onyx_l3_interface:
    name: Eth1/1
    ipv4: 192.168.0.1/24

- name: Remove Eth1/1 IPv4 address
  onyx_l3_interface:
    name: Eth1/1
    state: absent

- name: Set IP addresses on aggregate
  onyx_l3_interface:
    aggregate:
      - { name: Eth1/1, ipv4: 192.168.2.10/24 }
      - { name: Eth1/2, ipv4: 192.168.3.10/24 }

- name: Remove IP addresses on aggregate
  onyx_l3_interface:
    aggregate:
      - { name: Eth1/1, ipv4: 192.168.2.10/24 }
      - { name: Eth1/2, ipv4: 192.168.3.10/24 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - interfaces ethernet 1/1 ip address 192.168.0.1 /24
"""
import re
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import remove_default_spec

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import get_interfaces_config


class OnyxL3InterfaceModule(BaseOnyxModule):
    IF_ETH_REGEX = re.compile(r"^Eth(\d+\/\d+|Eth\d+\/\d+\d+)$")
    IF_VLAN_REGEX = re.compile(r"^Vlan (\d+)$")
    IF_LOOPBACK_REGEX = re.compile(r"^Loopback (\d+)$")

    IF_TYPE_ETH = "ethernet"
    IF_TYPE_LOOPBACK = "loopback"
    IF_TYPE_VLAN = "vlan"

    IF_TYPE_MAP = {
        IF_TYPE_ETH: IF_ETH_REGEX,
        IF_TYPE_VLAN: IF_VLAN_REGEX,
        IF_TYPE_LOOPBACK: IF_LOOPBACK_REGEX,
    }

    IP_ADDR_ATTR_MAP = {
        IF_TYPE_ETH: 'IP Address',
        IF_TYPE_VLAN: 'Internet Address',
        IF_TYPE_LOOPBACK: 'Internet Address',
    }

    _purge = False

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(type='str'),
            ipv4=dict(type='str'),
            ipv6=dict(type='str'),
            state=dict(default='present',
                       choices=['present', 'absent', 'enabled', 'disabled']),
        )

    @classmethod
    def _get_aggregate_spec(cls, element_spec):
        aggregate_spec = deepcopy(element_spec)
        aggregate_spec['name'] = dict(required=True)

        # remove default in aggregate spec, to handle common arguments
        remove_default_spec(aggregate_spec)
        return aggregate_spec

    def init_module(self):
        """ module initialization
        """
        element_spec = self._get_element_spec()
        aggregate_spec = self._get_aggregate_spec(element_spec)
        argument_spec = dict(
            aggregate=dict(type='list', elements='dict',
                           options=aggregate_spec),
            purge=dict(default=False, type='bool'),
        )
        argument_spec.update(element_spec)
        required_one_of = [['name', 'aggregate']]
        mutually_exclusive = [['name', 'aggregate']]
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

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

    def _set_if_type(self, params):
        if_name = params['name']
        if_type, if_id = self._get_interface_type(if_name)
        if not if_id:
            self._module.fail_json(
                msg='unsupported interface: %s' % if_name)
        params['if_type'] = if_type
        params['if_id'] = if_id

    def get_required_config(self):
        self._required_config = list()
        module_params = self._module.params
        aggregate = module_params.get('aggregate')
        self._purge = module_params.get('purge', False)
        if aggregate:
            for item in aggregate:
                for key in item:
                    if item.get(key) is None:
                        item[key] = module_params[key]
                self.validate_param_values(item, item)
                req_item = item.copy()
                self._set_if_type(req_item)
                self._required_config.append(req_item)
        else:
            params = {
                'name': module_params['name'],
                'ipv4': module_params['ipv4'],
                'ipv6': module_params['ipv6'],
                'state': module_params['state'],
            }
            self.validate_param_values(params)
            self._set_if_type(params)
            self._required_config.append(params)

    def _get_interfaces_config(self, interface_type):
        return get_interfaces_config(self._module, interface_type)

    def _parse_interfaces_config(self, if_type, if_config):
        if self._os_version < self.ONYX_API_VERSION:
            for if_data in if_config:
                if_name = self.get_config_attr(if_data, 'header')
                self._get_if_attributes(if_type, if_name, if_data)
        else:
            for if_config_item in if_config:
                for if_name, if_data in iteritems(if_config_item):
                    if_data = if_data[0]
                    self._get_if_attributes(if_type, if_name, if_data)

    def _get_if_attributes(self, if_type, if_name, if_data):
        ipaddr_attr = self.IP_ADDR_ATTR_MAP[if_type]
        regex = self.IF_TYPE_MAP[if_type]
        match = regex.match(if_name)
        if not match:
            return
        ipv4 = self.get_config_attr(if_data, ipaddr_attr)
        if ipv4:
            ipv4 = ipv4.replace(' ', '')
        ipv6 = self.get_config_attr(if_data, 'IPv6 address(es)')
        if ipv6:
            ipv6 = ipv6.replace('[primary]', '')
            ipv6 = ipv6.strip()
        if_id = match.group(1)
        switchport = self.get_config_attr(if_data, 'Switchport mode')
        if_obj = {
            'name': if_name,
            'if_id': if_id,
            'if_type': if_type,
            'ipv4': ipv4,
            'ipv6': ipv6,
            'switchport': switchport,
        }
        self._current_config[if_name] = if_obj

    def load_current_config(self):
        # called in base class in run function
        self._os_version = self._get_os_version()
        self._current_config = dict()
        if_types = set([if_obj['if_type'] for if_obj in self._required_config])
        for if_type in if_types:
            if_config = self._get_interfaces_config(if_type)
            if not if_config:
                continue
            self._parse_interfaces_config(if_type, if_config)

    def _generate_no_ip_commands(self, req_conf, curr_conf):
        curr_ip = curr_conf.get('ipv4')
        if_type = req_conf['if_type']
        if_id = req_conf['if_id']
        if curr_ip:
            cmd = "interface %s %s no ip address" % (if_type, if_id)
            self._commands.append(cmd)
        curr_ipv6 = curr_conf.get('ipv6')
        if curr_ipv6:
            cmd = "interface %s %s no ipv6 address %s" % (
                if_type, if_id, curr_ipv6)
            self._commands.append(cmd)

    def _generate_ip_commands(self, req_conf, curr_conf):
        curr_ipv4 = curr_conf.get('ipv4')
        req_ipv4 = req_conf.get('ipv4')
        curr_ipv6 = curr_conf.get('ipv6')
        req_ipv6 = req_conf.get('ipv6')
        if_type = req_conf['if_type']
        if_id = req_conf['if_id']
        switchport = curr_conf.get('switchport')
        if switchport:
            cmd = "interface %s %s no switchport force" % (if_type, if_id)
            self._commands.append(cmd)
        if curr_ipv4 != req_ipv4:
            cmd = "interface %s %s ip address %s" % (if_type, if_id, req_ipv4)
            self._commands.append(cmd)
        if curr_ipv6 != req_ipv6:
            cmd = "interface %s %s ipv6 address %s" % (
                if_type, if_id, req_ipv6)
            self._commands.append(cmd)

    def generate_commands(self):
        req_interfaces = set()
        for req_conf in self._required_config:
            state = req_conf['state']
            if_name = req_conf['name']
            curr_conf = self._current_config.get(if_name, {})
            if state == 'absent':
                self._generate_no_ip_commands(req_conf, curr_conf)
            else:
                req_interfaces.add(if_name)
                self._generate_ip_commands(req_conf, curr_conf)
        if self._purge:
            for if_name, curr_conf in iteritems(self._current_config):
                if if_name not in req_interfaces:
                    self._generate_no_ip_commands(req_conf, curr_conf)


def main():
    """ main entry point for module execution
    """
    OnyxL3InterfaceModule.main()


if __name__ == '__main__':
    main()
