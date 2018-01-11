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
module: onyx_ospf
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage OSPF protocol on Mellanox ONYX network devices
description:
  - This module provides declarative management and configuration of OSPF
    protocol on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.4000
options:
  ospf:
    description:
      - "OSPF instance number 1-65535"
    required: true
  router_id:
    description:
      - OSPF router ID. Required if I(state=present).
  interfaces:
    description:
      - List of interfaces and areas. Required if I(state=present).
    suboptions:
      name:
        description:
          - Intrface name.
        required: true
      area:
        description:
          - OSPF area.
        required: true
  state:
    description:
      - OSPF state.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: add ospf router to interface
  onyx_ospf:
    ospf: 2
    router_id: 192.168.8.2
    interfaces:
      - name: Eth1/1
      - area: 0.0.0.0
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - router ospf 2
    - router-id 192.168.8.2
    - exit
    - interface ethernet 1/1 ip ospf area 0.0.0.0
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxOspfModule(BaseOnyxModule):
    OSPF_IF_REGEX = re.compile(
        r'^(Loopback\d+|Eth\d+\/\d+|Vlan\d+|Po\d+)\s+(\S+).*')
    OSPF_ROUTER_REGEX = re.compile(r'^Routing Process (\d+).*ID\s+(\S+).*')

    @classmethod
    def _get_element_spec(cls):
        interface_spec = dict(
            name=dict(required=True),
            area=dict(required=True),
        )
        element_spec = dict(
            ospf=dict(type='int', required=True),
            router_id=dict(),
            interfaces=dict(type='list', elements='dict',
                            options=interface_spec),
            state=dict(choices=['present', 'absent'], default='present'),
        )
        return element_spec

    def init_module(self):
        """ Ansible module initialization
        """
        element_spec = self._get_element_spec()
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def validate_ospf(self, value):
        if value and not 1 <= int(value) <= 65535:
            self._module.fail_json(msg='ospf id must be between 1 and 65535')

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(
            ospf=module_params['ospf'],
            router_id=module_params['router_id'],
            state=module_params['state'],
        )
        interfaces = module_params['interfaces'] or list()
        req_interfaces = self._required_config['interfaces'] = dict()
        for interface_data in interfaces:
            req_interfaces[interface_data['name']] = interface_data['area']
        self.validate_param_values(self._required_config)

    def _update_ospf_data(self, ospf_data):
        match = self.OSPF_ROUTER_REGEX.match(ospf_data)
        if match:
            ospf_id = int(match.group(1))
            router_id = match.group(2)
            self._current_config['ospf'] = ospf_id
            self._current_config['router_id'] = router_id

    def _update_ospf_interfaces(self, ospf_interfaces):
        interfaces = self._current_config['interfaces'] = dict()
        lines = ospf_interfaces.split('\n')
        for line in lines:
            line = line.strip()
            match = self.OSPF_IF_REGEX.match(line)
            if match:
                name = match.group(1)
                area = match.group(2)
                for prefix in ("Vlan", "Loopback"):
                    if name.startswith(prefix):
                        name = name.replace(prefix, prefix + ' ')
                interfaces[name] = area

    def _get_ospf_config(self, ospf_id):
        cmd = 'show ip ospf %s | include Process' % ospf_id
        return show_cmd(self._module, cmd, json_fmt=False, fail_on_error=False)

    def _get_ospf_interfaces_config(self, ospf_id):
        cmd = 'show ip ospf interface %s brief' % ospf_id
        return show_cmd(self._module, cmd, json_fmt=False, fail_on_error=False)

    def load_current_config(self):
        # called in base class in run function
        ospf_id = self._required_config['ospf']
        self._current_config = dict()
        ospf_data = self._get_ospf_config(ospf_id)
        if ospf_data:
            self._update_ospf_data(ospf_data)
            ospf_interfaces = self._get_ospf_interfaces_config(ospf_id)
            if ospf_interfaces:
                self._update_ospf_interfaces(ospf_interfaces)

    def _generate_no_ospf_commands(self):
        req_ospf_id = self._required_config['ospf']
        curr_ospf_id = self._current_config.get('ospf')
        if curr_ospf_id == req_ospf_id:
            cmd = 'no router ospf %s' % req_ospf_id
            self._commands.append(cmd)

    def _get_interface_command_name(self, if_name):
        if if_name.startswith('Eth'):
            return if_name.replace("Eth", "ethernet ")
        if if_name.startswith('Po'):
            return if_name.replace("Po", "port-channel ")
        if if_name.startswith('Vlan'):
            return if_name.replace("Vlan", "vlan")
        if if_name.startswith('Loopback'):
            return if_name.replace("Loopback", "loopback")
        self._module.fail_json(
            msg='invalid interface name: %s' % if_name)

    def _get_interface_area_cmd(self, if_name, area):
        interface_prefix = self._get_interface_command_name(if_name)
        if area:
            area_cmd = 'ip ospf area %s' % area
        else:
            area_cmd = 'no ip ospf area'
        cmd = 'interface %s %s' % (interface_prefix, area_cmd)
        return cmd

    def _generate_ospf_commands(self):
        req_router_id = self._required_config['router_id']
        req_ospf_id = self._required_config['ospf']
        curr_router_id = self._current_config.get('router_id')
        curr_ospf_id = self._current_config.get('ospf')
        if curr_ospf_id != req_ospf_id or req_router_id != curr_router_id:
            cmd = 'router ospf %s' % req_ospf_id
            self._commands.append(cmd)
            if req_router_id != curr_router_id:
                if req_router_id:
                    cmd = 'router-id %s' % req_router_id
                else:
                    cmd = 'no router-id'
                self._commands.append(cmd)
            self._commands.append('exit')
        req_interfaces = self._required_config['interfaces']
        curr_interfaces = self._current_config.get('interfaces', dict())
        for if_name, area in iteritems(req_interfaces):
            curr_area = curr_interfaces.get(if_name)
            if curr_area != area:
                cmd = self._get_interface_area_cmd(if_name, area)
                self._commands.append(cmd)
        for if_name in curr_interfaces:
            if if_name not in req_interfaces:
                cmd = self._get_interface_area_cmd(if_name, None)
                self._commands.append(cmd)

    def generate_commands(self):
        req_state = self._required_config['state']
        if req_state == 'absent':
            return self._generate_no_ospf_commands()
        return self._generate_ospf_commands()


def main():
    """ main entry point for module execution
    """
    OnyxOspfModule.main()


if __name__ == '__main__':
    main()
