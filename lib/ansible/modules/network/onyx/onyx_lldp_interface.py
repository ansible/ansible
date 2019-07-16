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
module: onyx_lldp_interface
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage LLDP interfaces configuration on Mellanox ONYX network devices
description:
  - This module provides declarative management of LLDP interfaces
    configuration on Mellanox ONYX network devices.
options:
  name:
    description:
      - Name of the interface LLDP should be configured on.
  aggregate:
    description: List of interfaces LLDP should be configured on.
  purge:
    description:
      - Purge interfaces not defined in the aggregate parameter.
    type: bool
    default: false
  state:
    description:
      - State of the LLDP configuration.
    default: present
    choices: ['present', 'absent', 'enabled', 'disabled']
"""

EXAMPLES = """
- name: Configure LLDP on specific interfaces
  onyx_lldp_interface:
    name: Eth1/1
    state: present

- name: Disable LLDP on specific interfaces
  onyx_lldp_interface:
    name: Eth1/1
    state: disabled

- name: Enable LLDP on specific interfaces
  onyx_lldp_interface:
    name: Eth1/1
    state: enabled

- name: Delete LLDP on specific interfaces
  onyx_lldp_interface:
    name: Eth1/1
    state: absent

- name: Create aggregate of LLDP interface configurations
  onyx_lldp_interface:
    aggregate:
    - { name: Eth1/1 }
    - { name: Eth1/2 }
    state: present

- name: Delete aggregate of LLDP interface configurations
  onyx_lldp_interface:
    aggregate:
    - { name: Eth1/1 }
    - { name: Eth1/2 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - interface ethernet 1/1 lldp transmit
    - interface ethernet 1/1 lldp receive
"""
import re
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import remove_default_spec

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxLldpInterfaceModule(BaseOnyxModule):
    IF_NAME_REGEX = re.compile(r"^(Eth\d+\/\d+|Eth\d+\/\d+\d+)$")
    _purge = False

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(type='str'),
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
                self._required_config.append(req_item)
        else:
            params = {
                'name': module_params['name'],
                'state': module_params['state'],
            }
            self.validate_param_values(params)
            self._required_config.append(params)

    def _create_if_lldp_data(self, if_name, if_lldp_data):
        return {
            'name': if_name,
            'receive': self.get_config_attr(if_lldp_data, 'Receive'),
            'transmit': self.get_config_attr(if_lldp_data, 'Transmit'),
        }

    def _get_lldp_config(self):
        return show_cmd(self._module, "show lldp interfaces")

    def load_current_config(self):
        # called in base class in run function
        self._current_config = dict()
        lldp_config = self._get_lldp_config()
        if not lldp_config:
            return
        for if_name, if_lldp_data in iteritems(lldp_config):
            match = self.IF_NAME_REGEX.match(if_name)
            if not match:
                continue
            if if_lldp_data:
                if_lldp_data = if_lldp_data[0]
                self._current_config[if_name] = \
                    self._create_if_lldp_data(if_name, if_lldp_data)

    def _get_interface_cmd_name(self, if_name):
        return if_name.replace("Eth", "ethernet ")

    def _add_if_lldp_commands(self, if_name, flag, enable):
        cmd_prefix = "interface %s " % self._get_interface_cmd_name(if_name)
        lldp_cmd = "lldp %s" % flag
        if not enable:
            lldp_cmd = 'no %s' % lldp_cmd
        self._commands.append(cmd_prefix + lldp_cmd)

    def _gen_lldp_commands(self, if_name, req_state, curr_conf):
        curr_receive = curr_conf.get('receive')
        curr_transmit = curr_conf.get('transmit')
        enable = (req_state == 'Enabled')
        if curr_receive != req_state:
            flag = 'receive'
            self._add_if_lldp_commands(if_name, flag, enable)
        if curr_transmit != req_state:
            flag = 'transmit'
            self._add_if_lldp_commands(if_name, flag, enable)

    def generate_commands(self):
        req_interfaces = set()
        for req_conf in self._required_config:
            state = req_conf['state']
            if_name = req_conf['name']
            if state in ('absent', 'disabled'):
                req_state = 'Disabled'
            else:
                req_interfaces.add(if_name)
                req_state = 'Enabled'
            curr_conf = self._current_config.get(if_name, {})
            self._gen_lldp_commands(if_name, req_state, curr_conf)
        if self._purge:
            for if_name, curr_conf in iteritems(self._current_config):
                if if_name not in req_interfaces:
                    req_state = 'Disabled'
                    self._gen_lldp_commands(if_name, req_state, curr_conf)


def main():
    """ main entry point for module execution
    """
    OnyxLldpInterfaceModule.main()


if __name__ == '__main__':
    main()
