#!/usr/bin/python

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_lldp
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage LLDP configuration on Mellanox ONYX network devices
description:
  - This module provides declarative management of LLDP service configuration
    on Mellanox ONYX network devices.
options:
  state:
    description:
      - State of the LLDP protocol configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Enable LLDP protocol
  onyx_lldp:
    state: present

- name: Disable LLDP protocol
  onyx_lldp:
    state: lldp
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - lldp
"""

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxLldpModule(BaseOnyxModule):
    LLDP_ENTRY = 'LLDP'
    SHOW_LLDP_CMD = 'show lldp local'

    @classmethod
    def _get_element_spec(cls):
        return dict(
            state=dict(default='present', choices=['present', 'absent']),
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
        self._required_config = dict()
        module_params = self._module.params
        params = {
            'state': module_params['state'],
        }

        self.validate_param_values(params)
        self._required_config.update(params)

    def _get_lldp_config(self):
        return show_cmd(self._module, self.SHOW_LLDP_CMD)

    def load_current_config(self):
        self._current_config = dict()
        state = 'absent'
        config = self._get_lldp_config() or dict()
        for item in config:
            lldp_state = item.get(self.LLDP_ENTRY)
            if lldp_state is not None:
                if lldp_state == 'enabled':
                    state = 'present'
                break
        self._current_config['state'] = state

    def generate_commands(self):
        req_state = self._required_config['state']
        curr_state = self._current_config['state']
        if curr_state != req_state:
            cmd = 'lldp'
            if req_state == 'absent':
                cmd = 'no %s' % cmd
            self._commands.append(cmd)


def main():
    """ main entry point for module execution
    """
    OnyxLldpModule.main()


if __name__ == '__main__':
    main()
