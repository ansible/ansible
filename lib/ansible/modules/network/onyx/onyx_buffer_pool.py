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
module: onyx_buffer_pool
version_added: "2.8"
author: "Anas Badaha (@anasb)"
short_description: Configures Buffer Pool
description:
  - This module provides declarative management of Onyx Buffer Pool configuration
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.8130
options:
  name:
    description:
      - pool name.
    required: true
  pool_type:
    description:
      - pool type.
    choices: ['lossless', 'lossy']
    default: lossy
  memory_percent:
    description:
      - memory percent.
  switch_priority:
    description:
      - switch priority, range 1-7.
"""

EXAMPLES = """
- name: configure buffer pool
  onyx_buffer_pool:
    name: roce
    pool_type: lossless
    memory_percent: 50.00
    switch_priority: 3

"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - traffic pool roce type lossless
    - traffic pool roce memory percent 50.00
    - traffic pool roce map switch-priority 3
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxBufferPoolModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            name=dict(type='str', required=True),
            pool_type=dict(choices=['lossless', 'lossy'], default='lossy'),
            memory_percent=dict(type='float'),
            switch_priority=dict(type='int')
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def validate_switch_priority(self, value):
        if value and not 0 <= int(value) <= 7:
            self._module.fail_json(msg='switch_priority value must be between 0 and 7')

    def _set_traffic_pool_config(self, traffic_pool_config):
        if traffic_pool_config is None:
            return
        traffic_pool_config = traffic_pool_config.get(self._required_config.get('name'))
        self._current_config['pool_type'] = traffic_pool_config[0].get("Type")
        self._current_config['switch_priority'] = int(traffic_pool_config[0].get("Switch Priorities"))
        self._current_config['memory_percent'] = float(traffic_pool_config[0].get("Memory [%]"))

    def _show_traffic_pool(self):
        cmd = "show traffic pool {0}".format(self._required_config.get("name"))
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        traffic_pool_config = self._show_traffic_pool()
        self._set_traffic_pool_config(traffic_pool_config)

    def generate_commands(self):
        name = self._required_config.get("name")
        pool_type = self._required_config.get("pool_type")

        if self._current_config is None:
            self._add_add_traffic_pool_cmds(name, pool_type)
        else:
            current_pool_type = self._current_config.get("pool_type")
            if pool_type != current_pool_type:
                self._add_add_traffic_pool_cmds(name, pool_type)

        memory_percent = self._required_config.get("memory_percent")
        if memory_percent is not None:
            curr_memory_percent = self._current_config.get("memory_percent")
            if curr_memory_percent is None or memory_percent != curr_memory_percent:
                self._commands.append('traffic pool {0} memory percent {1}'.format(name, memory_percent))

        switch_priority = self._required_config.get("switch_priority")
        if switch_priority is not None:
            curr_switch_priority = self._current_config.get("switch_priority")
            if curr_switch_priority is None or switch_priority != curr_switch_priority:
                self._commands.append('traffic pool {0} map switch-priority {1}'.format(name, switch_priority))

    def _add_add_traffic_pool_cmds(self, name, pool_type):
        self._commands.append('traffic pool {0} type {1}'.format(name, pool_type))


def main():
    """ main entry point for module execution
    """
    OnyxBufferPoolModule.main()


if __name__ == '__main__':
    main()
