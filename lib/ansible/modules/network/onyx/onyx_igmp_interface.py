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
module: onyx_igmp_interface
version_added: "2.8"
author: "Anas Badaha (@anasb)"
short_description: Configures IGMP interface parameters
description:
  - This module provides declarative management of IGMP interface configuration
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.8130
options:
  name:
    description:
    - interface name that we want to configure IGMP on it
    required: true
  state:
    description:
      - IGMP Interface state.
    choices: ['enabled', 'disabled']
    default: enabled
"""

EXAMPLES = """
- name: configure igmp interfcae
  onyx_igmp_interface:
    state: enabled
    name: Eth1/1
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface ethernet 1/1 ip igmp snooping fast-leave
"""

import re
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxIgmpInterfaceModule(BaseOnyxModule):
    IF_NAME_REGEX = re.compile(r"^(Eth\d+\/\d+|Eth\d+\/\d+\d+)$")

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            state=dict(choices=['enabled', 'disabled'], default='enabled'),
            name=dict(required=True)
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        match = self.IF_NAME_REGEX.match(self._required_config["name"])
        if not match:
            raise AttributeError("Please Insert Valid Interface Name")

        self.validate_param_values(self._required_config)

    def _set_igmp_config(self, igmp_interfaces_config):
        if not igmp_interfaces_config:
            return
        name = self._required_config.get('name')
        interface_state = igmp_interfaces_config[name][0].get('leave-mode')
        if interface_state == "Fast":
            self._current_config['state'] = "enabled"
        else:
            self._current_config['state'] = "disabled"

    def _show_igmp_interfaces(self):
        cmd = "show ip igmp snooping interfaces"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        igmp_interfaces_config = self._show_igmp_interfaces()
        if igmp_interfaces_config:
            self._set_igmp_config(igmp_interfaces_config)

    def generate_commands(self):
        req_state = self._required_config['state']
        self._req_val = self._required_config.get('name').replace("Eth", "ethernet ")

        if req_state == 'enabled':
            self._generate_igmp_interface_cmds()
        else:
            self._generate_no_igmp_cmds()

    def _generate_igmp_interface_cmds(self):
        curr_state = self._current_config.get('state', 'enabled')
        if curr_state == 'enabled':
            pass

        elif curr_state == 'disabled':
            self._commands.append('interface %s ip igmp snooping fast-leave' % self._req_val)

    def _generate_no_igmp_cmds(self):
        curr_state = self._current_config.get('state', 'enabled')
        if curr_state == 'enabled':
            self._commands.append('interface %s no ip igmp snooping fast-leave' % self._req_val)
        else:
            pass


def main():
    """ main entry point for module execution
    """
    OnyxIgmpInterfaceModule.main()


if __name__ == '__main__':
    main()
