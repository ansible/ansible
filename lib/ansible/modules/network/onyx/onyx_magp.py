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
module: onyx_magp
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage MAGP protocol on Mellanox ONYX network devices
description:
  - This module provides declarative management of MAGP protocol on vlan
    interface of Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.4000
options:
  magp_id:
    description:
      - "MAGP instance number 1-255"
    required: true
  interface:
    description:
      - VLAN Interface name.
    required: true
  state:
    description:
      - MAGP state.
    default: present
    choices: ['present', 'absent', 'enabled', 'disabled']
  router_ip:
    description:
      - MAGP router IP address.
  router_mac:
    description:
      - MAGP router MAC address.
"""

EXAMPLES = """
- name: run add vlan interface with magp
  onyx_magp:
    magp_id: 103
    router_ip: 192.168.8.2
    router_mac: AA:1B:2C:3D:4E:5F
    interface: Vlan 1002
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface vlan 234 magp 103
    - exit
    - interface vlan 234 magp 103 ip virtual-router address 1.2.3.4
"""
import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxMagpModule(BaseOnyxModule):
    IF_VLAN_REGEX = re.compile(r"^Vlan (\d+)$")

    @classmethod
    def _get_element_spec(cls):
        return dict(
            magp_id=dict(type='int', required=True),
            state=dict(default='present',
                       choices=['present', 'absent', 'enabled', 'disabled']),
            interface=dict(required=True),
            router_ip=dict(),
            router_mac=dict(),
        )

    def init_module(self):
        """ Ansible module initialization
        """
        element_spec = self._get_element_spec()
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def validate_magp_id(self, value):
        if value and not 1 <= int(value) <= 255:
            self._module.fail_json(msg='magp id must be between 1 and 255')

    def get_required_config(self):
        module_params = self._module.params
        interface = module_params['interface']
        match = self.IF_VLAN_REGEX.match(interface)
        vlan_id = 0
        if match:
            vlan_id = int(match.group(1))
        else:
            self._module.fail_json(
                msg='Invalid interface name: should be "Vlan <vlan_id>"')

        self._required_config = dict(
            magp_id=module_params['magp_id'],
            state=module_params['state'],
            vlan_id=vlan_id,
            router_ip=module_params['router_ip'],
            router_mac=module_params['router_mac'])
        self.validate_param_values(self._required_config)

    @classmethod
    def get_magp_id(cls, item):
        header = cls.get_config_attr(item, "header")
        return int(header.split()[1])

    def _create_magp_instance_data(self, magp_id, item):
        vlan_id = int(self.get_config_attr(item, "Interface vlan"))
        state = self.get_config_attr(item, "Admin state").lower()
        return dict(
            magp_id=magp_id,
            state=state,
            vlan_id=vlan_id,
            router_ip=self.get_config_attr(item, "Virtual IP"),
            router_mac=self.get_config_attr(item, "Virtual MAC"))

    def _update_magp_data(self, magp_data):
        for magp_item in magp_data:
            magp_id = self.get_magp_id(magp_item)
            inst_data = self._create_magp_instance_data(magp_id, magp_item)
            self._current_config[magp_id] = inst_data

    def _get_magp_config(self):
        cmd = "show magp"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        # called in base class in run function
        self._current_config = dict()
        magp_data = self._get_magp_config()
        if magp_data:
            self._update_magp_data(magp_data)

    def _generate_no_magp_commands(self):
        req_vlan_id = self._required_config['vlan_id']
        req_magp_id = self._required_config['magp_id']
        curr_magp_data = self._current_config.get(req_magp_id)
        if not curr_magp_data:
            return
        curr_vlan_id = curr_magp_data.get(req_vlan_id)
        if curr_vlan_id == req_vlan_id:
            cmd = 'interface vlan %s no magp %s' % (req_vlan_id, req_magp_id)
            self._commands.append(cmd)

    def _generate_magp_commands(self, req_state):
        req_vlan_id = self._required_config['vlan_id']
        req_magp_id = self._required_config['magp_id']
        curr_magp_data = self._current_config.get(req_magp_id, dict())
        curr_vlan_id = curr_magp_data.get('vlan_id')
        magp_prefix = 'interface vlan %s magp %s' % (req_vlan_id, req_magp_id)
        create_new_magp = False
        if curr_vlan_id != req_vlan_id:
            if curr_vlan_id:
                cmd = 'interface vlan %s no magp %s' % (
                    curr_vlan_id, req_magp_id)
                self._commands.append(cmd)
                create_new_magp = True
            self._commands.append(magp_prefix)
            self._commands.append('exit')
        req_router_ip = self._required_config['router_ip']
        curr_router_ip = curr_magp_data.get('router_ip')
        if req_router_ip:
            if curr_router_ip != req_router_ip or create_new_magp:
                cmd = '%s ip virtual-router address %s' % (
                    magp_prefix, req_router_ip)
                self._commands.append(cmd)
        else:
            if curr_router_ip and curr_router_ip != '0.0.0.0':
                cmd = '%s no ip virtual-router address' % magp_prefix
                self._commands.append(cmd)
        req_router_mac = self._required_config['router_mac']
        curr_router_mac = curr_magp_data.get('router_mac')
        if curr_router_mac:
            curr_router_mac = curr_router_mac.lower()
        if req_router_mac:
            req_router_mac = req_router_mac.lower()
            if curr_router_mac != req_router_mac or create_new_magp:
                cmd = '%s ip virtual-router mac-address %s' % (
                    magp_prefix, req_router_mac)
                self._commands.append(cmd)
        else:
            if curr_router_mac and curr_router_mac != '00:00:00:00:00:00':
                cmd = '%s no ip virtual-router mac-address' % magp_prefix
                self._commands.append(cmd)
        if req_state in ('enabled', 'disabled'):
            curr_state = curr_magp_data.get('state', 'enabled')
            if curr_state != req_state:
                if req_state == 'enabled':
                    suffix = 'no shutdown'
                else:
                    suffix = 'shutdown'
                cmd = '%s %s' % (magp_prefix, suffix)
                self._commands.append(cmd)

    def generate_commands(self):
        req_state = self._required_config['state']
        if req_state == 'absent':
            return self._generate_no_magp_commands()
        return self._generate_magp_commands(req_state)


def main():
    """ main entry point for module execution
    """
    OnyxMagpModule.main()


if __name__ == '__main__':
    main()
