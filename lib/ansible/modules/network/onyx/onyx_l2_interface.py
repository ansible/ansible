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
module: onyx_l2_interface
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage Layer-2 interface on Mellanox ONYX network devices
description:
  - This module provides declarative management of Layer-2 interface
    on Mellanox ONYX network devices.
options:
  name:
    description:
      - Name of the interface.
  aggregate:
    description:
      - List of Layer-2 interface definitions.
  mode:
    description:
      - Mode in which interface needs to be configured.
    default: access
    choices: ['access', 'trunk', 'hybrid']
  access_vlan:
    description:
      - Configure given VLAN in access port.
  trunk_allowed_vlans:
    description:
      - List of allowed VLANs in a given trunk port.
  state:
    description:
      - State of the Layer-2 Interface configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure Layer-2 interface
  onyx_l2_interface:
    name: Eth1/1
    mode: access
    access_vlan: 30

- name: remove Layer-2 interface configuration
  onyx_l2_interface:
    name: Eth1/1
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - interface ethernet 1/1
    - switchport mode access
    - switchport access vlan 30
"""
from copy import deepcopy
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import remove_default_spec

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import get_interfaces_config


class OnyxL2InterfaceModule(BaseOnyxModule):
    IFNAME_REGEX = re.compile(r"^.*(Eth\d+\/\d+|Mpo\d+|Po\d+)")

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(),
            access_vlan=dict(type='int'),
            trunk_allowed_vlans=dict(type='list', elements='int'),
            state=dict(default='present',
                       choices=['present', 'absent']),
            mode=dict(default='access',
                      choices=['access', 'hybrid', 'trunk']),
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
        )
        argument_spec.update(element_spec)
        required_one_of = [['name', 'aggregate']]
        mutually_exclusive = [['name', 'aggregate']]
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

    def get_required_config(self):
        self._required_config = list()
        module_params = self._module.params
        aggregate = module_params.get('aggregate')
        if aggregate:
            for item in aggregate:
                for key in item:
                    if item.get(key) is None:
                        item[key] = module_params[key]
                self.validate_param_values(item, item)
                req_item = item.copy()
                self._required_config.append(req_item)
        else:
            params = {
                'name': module_params['name'],
                'access_vlan': module_params['access_vlan'],
                'trunk_allowed_vlans': module_params['trunk_allowed_vlans'],
                'mode': module_params['mode'],
                'state': module_params['state'],
            }
            self.validate_param_values(params)
            self._required_config.append(params)

    def validate_access_vlan(self, value):
        if value and not 1 <= int(value) <= 4094:
            self._module.fail_json(msg='vlan id must be between 1 and 4094')

    @classmethod
    def get_allowed_vlans(cls, if_data):
        allowed_vlans = cls.get_config_attr(if_data, 'Allowed vlans')
        if allowed_vlans:
            vlans = allowed_vlans.split(',')
            allowed_vlans = [int(vlan.strip()) for vlan in vlans]
        return allowed_vlans

    @classmethod
    def get_access_vlan(cls, if_data):
        access_vlan = cls.get_config_attr(if_data, 'Access vlan')
        if access_vlan:
            return int(access_vlan)

    def _create_switchport_data(self, if_name, if_data):
        if self._os_version >= self.ONYX_API_VERSION:
            if_data = if_data[0]

        return {
            'name': if_name,
            'mode': self.get_config_attr(if_data, 'Mode'),
            'access_vlan': self.get_access_vlan(if_data),
            'trunk_allowed_vlans': self.get_allowed_vlans(if_data)
        }

    def _get_switchport_config(self):
        return get_interfaces_config(self._module, 'switchport')

    def load_current_config(self):
        # called in base class in run function
        self._os_version = self._get_os_version()
        self._current_config = dict()
        switchports_config = self._get_switchport_config()
        if not switchports_config:
            return
        for if_name, if_data in iteritems(switchports_config):
            self._current_config[if_name] = \
                self._create_switchport_data(if_name, if_data)

    def _get_switchport_command_name(self, if_name):
        if if_name.startswith('Eth'):
            return if_name.replace("Eth", "ethernet ")
        if if_name.startswith('Po'):
            return if_name.replace("Po", "port-channel ")
        if if_name.startswith('Mpo'):
            return if_name.replace("Mpo", "mlag-port-channel ")
        self._module.fail_json(
            msg='invalid interface name: %s' % if_name)

    def _add_interface_commands(self, if_name, commands):
        if_cmd_name = self._get_switchport_command_name(if_name)
        self._commands.append("interface %s" % if_cmd_name)
        self._commands.extend(commands)
        self._commands.append('exit')

    def _generate_no_switchport_commands(self, if_name):
        commands = ['no switchport force']
        self._add_interface_commands(if_name, commands)

    def _generate_switchport_commands(self, if_name, req_conf):
        commands = []
        curr_conf = self._current_config.get(if_name, {})
        curr_mode = curr_conf.get('mode')
        req_mode = req_conf.get('mode')
        if req_mode != curr_mode:
            commands.append('switchport mode %s' % req_mode)
        curr_access_vlan = curr_conf.get('access_vlan')
        req_access_vlan = req_conf.get('access_vlan')
        if curr_access_vlan != req_access_vlan and req_access_vlan:
            commands.append('switchport access vlan %s' % req_access_vlan)
        curr_trunk_vlans = curr_conf.get('trunk_allowed_vlans') or set()
        if curr_trunk_vlans:
            curr_trunk_vlans = set(curr_trunk_vlans)
        req_trunk_vlans = req_conf.get('trunk_allowed_vlans') or set()
        if req_trunk_vlans:
            req_trunk_vlans = set(req_trunk_vlans)
        if req_mode != 'access' and curr_trunk_vlans != req_trunk_vlans:
            removed_vlans = curr_trunk_vlans - req_trunk_vlans
            for vlan_id in removed_vlans:
                commands.append('switchport %s allowed-vlan remove %s' %
                                (req_mode, vlan_id))
            added_vlans = req_trunk_vlans - curr_trunk_vlans
            for vlan_id in added_vlans:
                commands.append('switchport %s allowed-vlan add %s' %
                                (req_mode, vlan_id))

        if commands:
            self._add_interface_commands(if_name, commands)

    def generate_commands(self):
        for req_conf in self._required_config:
            state = req_conf['state']
            if_name = req_conf['name']
            if state == 'absent':
                if if_name in self._current_config:
                    self._generate_no_switchport_commands(if_name)
            else:
                self._generate_switchport_commands(if_name, req_conf)

    def _generate_vlan_commands(self, vlan_id, req_conf):
        curr_vlan = self._current_config.get(vlan_id, {})
        if not curr_vlan:
            cmd = "vlan " + vlan_id
            self._commands.append("vlan %s" % vlan_id)
            self._commands.append("exit")
        vlan_name = req_conf['vlan_name']
        if vlan_name:
            if vlan_name != curr_vlan.get('vlan_name'):
                self._commands.append("vlan %s name %s" % (vlan_id, vlan_name))
        curr_members = set(curr_vlan.get('interfaces', []))
        req_members = req_conf['interfaces']
        mode = req_conf['mode']
        for member in req_members:
            if member in curr_members:
                continue
            if_name = self.get_switchport_command_name(member)
            cmd = "interface %s switchport mode %s" % (if_name, mode)
            self._commands.append(cmd)
            cmd = "interface %s switchport %s allowed-vlan add %s" % (
                if_name, mode, vlan_id)
            self._commands.append(cmd)
        req_members = set(req_members)
        for member in curr_members:
            if member in req_members:
                continue
            if_name = self.get_switchport_command_name(member)
            cmd = "interface %s switchport %s allowed-vlan remove %s" % (
                if_name, mode, vlan_id)
            self._commands.append(cmd)


def main():
    """ main entry point for module execution
    """
    OnyxL2InterfaceModule.main()


if __name__ == '__main__':
    main()
