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
module: onyx_mlag_ipl
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage IPL (inter-peer link) on Mellanox ONYX network devices
description:
  - This module provides declarative management of IPL (inter-peer link)
    management on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.4000
options:
  name:
    description:
      - Name of the interface (port-channel) IPL should be configured on.
    required: true
  vlan_interface:
    description:
      - Name of the IPL vlan interface.
  state:
    description:
      - IPL state.
    default: present
    choices: ['present', 'absent']
  peer_address:
    description:
      - IPL peer IP address.
"""

EXAMPLES = """
- name: run configure ipl
  onyx_mlag_ipl:
    name: Po1
    vlan_interface: Vlan 322
    state: present
    peer_address: 192.168.7.1

- name: run remove ipl
  onyx_mlag_ipl:
    name: Po1
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface port-channel 1 ipl 1
    - interface vlan 1024 ipl 1 peer-address 10.10.10.10
"""
import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxMlagIplModule(BaseOnyxModule):
    VLAN_IF_REGEX = re.compile(r'^Vlan \d+')

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(required=True),
            state=dict(default='present',
                       choices=['present', 'absent']),
            peer_address=dict(),
            vlan_interface=dict(),
        )

    def init_module(self):
        """ module initialization
        """
        element_spec = self._get_element_spec()
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(
            name=module_params['name'],
            state=module_params['state'],
            peer_address=module_params['peer_address'],
            vlan_interface=module_params['vlan_interface'])
        self.validate_param_values(self._required_config)

    def _update_mlag_data(self, mlag_data):
        if not mlag_data:
            return
        mlag_summary = mlag_data.get("MLAG IPLs Summary", {})
        ipl_id = "1"
        ipl_list = mlag_summary.get(ipl_id)
        if ipl_list:
            ipl_data = ipl_list[0]
            vlan_id = ipl_data.get("Vlan Interface")
            vlan_interface = ""
            if vlan_id != "N/A":
                vlan_interface = "Vlan %s" % vlan_id
            peer_address = ipl_data.get("Peer IP address")
            name = ipl_data.get("Group Port-Channel")
            self._current_config = dict(
                name=name,
                peer_address=peer_address,
                vlan_interface=vlan_interface)

    def _show_mlag_data(self):
        cmd = "show mlag"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        # called in base class in run function
        self._current_config = dict()
        mlag_data = self._show_mlag_data()
        self._update_mlag_data(mlag_data)

    def _get_interface_cmd_name(self, if_name):
        if if_name.startswith('Po'):
            return if_name.replace("Po", "port-channel ")
        self._module.fail_json(
            msg='invalid interface name: %s' % if_name)

    def _generate_port_channel_command(self, if_name, enable):
        if_cmd_name = self._get_interface_cmd_name(if_name)
        if enable:
            ipl_cmd = 'ipl 1'
        else:
            ipl_cmd = "no ipl 1"
        cmd = "interface %s %s" % (if_cmd_name, ipl_cmd)
        return cmd

    def _generate_vlan_if_command(self, if_name, enable, peer_address):
        if_cmd_name = if_name.lower()
        if enable:
            ipl_cmd = 'ipl 1 peer-address %s' % peer_address
        else:
            ipl_cmd = "no ipl 1"
        cmd = "interface %s %s" % (if_cmd_name, ipl_cmd)
        return cmd

    def _generate_no_ipl_commands(self):
        curr_interface = self._current_config.get('name')
        req_interface = self._required_config.get('name')
        if curr_interface == req_interface:
            cmd = self._generate_port_channel_command(
                req_interface, enable=False)
            self._commands.append(cmd)

    def _generate_ipl_commands(self):
        curr_interface = self._current_config.get('name')
        req_interface = self._required_config.get('name')
        if curr_interface != req_interface:
            if curr_interface and curr_interface != 'N/A':
                cmd = self._generate_port_channel_command(
                    curr_interface, enable=False)
                self._commands.append(cmd)
            cmd = self._generate_port_channel_command(
                req_interface, enable=True)
            self._commands.append(cmd)
        curr_vlan = self._current_config.get('vlan_interface')
        req_vlan = self._required_config.get('vlan_interface')
        add_peer = False
        if curr_vlan != req_vlan:
            add_peer = True
            if curr_vlan:
                cmd = self._generate_vlan_if_command(curr_vlan, enable=False,
                                                     peer_address=None)
                self._commands.append(cmd)
        curr_peer = self._current_config.get('peer_address')
        req_peer = self._required_config.get('peer_address')
        if req_peer != curr_peer:
            add_peer = True
        if add_peer and req_peer:
            cmd = self._generate_vlan_if_command(req_vlan, enable=True,
                                                 peer_address=req_peer)
            self._commands.append(cmd)

    def generate_commands(self):
        state = self._required_config['state']
        if state == 'absent':
            self._generate_no_ipl_commands()
        else:
            self._generate_ipl_commands()


def main():
    """ main entry point for module execution
    """
    OnyxMlagIplModule.main()


if __name__ == '__main__':
    main()
