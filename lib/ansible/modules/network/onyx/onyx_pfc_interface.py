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
module: onyx_pfc_interface
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage priority flow control on ONYX network devices
description:
  - This module provides declarative management of priority flow control (PFC)
    on interfaces of Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.4000
options:
  name:
    description:
      - Name of the interface PFC should be configured on.
  aggregate:
    description: List of interfaces PFC should be configured on.
  purge:
    description:
      - Purge interfaces not defined in the aggregate parameter.
    type: bool
    default: false
  state:
    description:
      - State of the PFC configuration.
    default: enabled
    choices: ['enabled', 'disabled']
"""

EXAMPLES = """
- name: configure PFC
  onyx_pfc_interface:
    name: Eth1/1
    state: enabled
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface ethernet 1/17 dcb priority-flow-control mode on
"""
from copy import deepcopy
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.six import iteritems

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxPfcInterfaceModule(BaseOnyxModule):
    PFC_IF_REGEX = re.compile(
        r"^(Eth\d+\/\d+)|(Eth\d+\/\d+\/\d+)|(Po\d+)|(Mpo\d+)$")

    _purge = False

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(type='str'),
            state=dict(default='enabled',
                       choices=['enabled', 'disabled']),
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

    def _create_if_pfc_data(self, if_name, if_pfc_data):
        state = self.get_config_attr(if_pfc_data, "PFC oper")
        state = state.lower()
        return dict(
            name=if_name,
            state=state)

    def _get_pfc_config(self):
        return show_cmd(self._module, "show dcb priority-flow-control")

    def load_current_config(self):
        # called in base class in run function
        self._os_version = self._get_os_version()
        self._current_config = dict()
        pfc_config = self._get_pfc_config()
        if not pfc_config:
            return
        if self._os_version >= self.ONYX_API_VERSION:
            if len(pfc_config) >= 3:
                pfc_config = pfc_config[2]
            else:
                pfc_config = dict()
        else:
            if 'Table 2' in pfc_config:
                pfc_config = pfc_config['Table 2']

        for if_name, if_pfc_data in iteritems(pfc_config):
            match = self.PFC_IF_REGEX.match(if_name)
            if not match:
                continue
            if if_pfc_data:
                if_pfc_data = if_pfc_data[0]
                self._current_config[if_name] = \
                    self._create_if_pfc_data(if_name, if_pfc_data)

    def _get_interface_cmd_name(self, if_name):
        if if_name.startswith('Eth'):
            return if_name.replace("Eth", "ethernet ")
        if if_name.startswith('Po'):
            return if_name.replace("Po", "port-channel ")
        if if_name.startswith('Mpo'):
            return if_name.replace("Mpo", "mlag-port-channel ")
        self._module.fail_json(
            msg='invalid interface name: %s' % if_name)

    def _add_if_pfc_commands(self, if_name, req_state):
        cmd_prefix = "interface %s " % self._get_interface_cmd_name(if_name)

        if req_state == 'disabled':
            pfc_cmd = 'no dcb priority-flow-control mode force'
        else:
            pfc_cmd = 'dcb priority-flow-control mode on force'
        self._commands.append(cmd_prefix + pfc_cmd)

    def _gen_pfc_commands(self, if_name, curr_conf, req_state):
        curr_state = curr_conf.get('state', 'disabled')
        if curr_state != req_state:
            self._add_if_pfc_commands(if_name, req_state)

    def generate_commands(self):
        req_interfaces = set()
        for req_conf in self._required_config:
            req_state = req_conf['state']
            if_name = req_conf['name']
            if req_state == 'enabled':
                req_interfaces.add(if_name)
            curr_conf = self._current_config.get(if_name, {})
            self._gen_pfc_commands(if_name, curr_conf, req_state)
        if self._purge:
            for if_name, curr_conf in iteritems(self._current_config):
                if if_name not in req_interfaces:
                    req_state = 'disabled'
                    self._gen_pfc_commands(if_name, curr_conf, req_state)


def main():
    """ main entry point for module execution
    """
    OnyxPfcInterfaceModule.main()


if __name__ == '__main__':
    main()
