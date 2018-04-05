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
module: onyx_vlan
version_added: "2.5"
author: "Samer Deeb (@samerd) Alex Tabachnik (@atabachnik)"
short_description: Manage VLANs on Mellanox ONYX network devices
description:
  - This module provides declarative management of VLANs
    on Mellanox ONYX network devices.
options:
  name:
    description:
      - Name of the VLAN.
  vlan_id:
    description:
      - ID of the VLAN.
  aggregate:
    description: List of VLANs definitions.
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure VLAN ID and name
  onyx_vlan:
    vlan_id: 20
    name: test-vlan

- name: remove configuration
  onyx_vlan:
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - vlan 20
    - name test-vlan
    - exit
"""

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import remove_default_spec

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxVlanModule(BaseOnyxModule):
    _purge = False

    @classmethod
    def _get_element_spec(cls):
        return dict(
            vlan_id=dict(type='int'),
            name=dict(type='str'),
            state=dict(default='present', choices=['present', 'absent']),
        )

    @classmethod
    def _get_aggregate_spec(cls, element_spec):
        aggregate_spec = deepcopy(element_spec)
        aggregate_spec['vlan_id'] = dict(required=True)

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
        required_one_of = [['vlan_id', 'aggregate']]
        mutually_exclusive = [['vlan_id', 'aggregate']]
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

    def validate_vlan_id(self, value):
        if value and not 1 <= int(value) <= 4094:
            self._module.fail_json(msg='vlan id must be between 1 and 4094')

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
                req_item['vlan_id'] = int(req_item['vlan_id'])
                self._required_config.append(req_item)
        else:
            params = {
                'vlan_id': module_params['vlan_id'],
                'name': module_params['name'],
                'state': module_params['state'],
            }
            self.validate_param_values(params)
            self._required_config.append(params)

    def _create_vlan_data(self, vlan_id, vlan_data):
        if self._os_version >= self.ONYX_API_VERSION:
            vlan_data = vlan_data[0]
        return {
            'vlan_id': vlan_id,
            'name': self.get_config_attr(vlan_data, 'Name')
        }

    def _get_vlan_config(self):
        return show_cmd(self._module, "show vlan")

    def load_current_config(self):
        # called in base class in run function
        self._os_version = self._get_os_version()
        self._current_config = dict()
        vlan_config = self._get_vlan_config()
        if not vlan_config:
            return
        for vlan_id, vlan_data in iteritems(vlan_config):
            try:
                vlan_id = int(vlan_id)
            except ValueError:
                continue
            self._current_config[vlan_id] = \
                self._create_vlan_data(vlan_id, vlan_data)

    def generate_commands(self):
        req_vlans = set()
        for req_conf in self._required_config:
            state = req_conf['state']
            vlan_id = req_conf['vlan_id']
            if state == 'absent':
                if vlan_id in self._current_config:
                    self._commands.append('no vlan %s' % vlan_id)
            else:
                req_vlans.add(vlan_id)
                self._generate_vlan_commands(vlan_id, req_conf)
        if self._purge:
            for vlan_id in self._current_config:
                if vlan_id not in req_vlans:
                    self._commands.append('no vlan %s' % vlan_id)

    def _generate_vlan_commands(self, vlan_id, req_conf):
        curr_vlan = self._current_config.get(vlan_id, {})
        if not curr_vlan:
            self._commands.append("vlan %s" % vlan_id)
            self._commands.append("exit")
        req_name = req_conf['name']
        curr_name = curr_vlan.get('name')
        if req_name:
            if req_name != curr_name:
                self._commands.append("vlan %s name %s" % (vlan_id, req_name))
        elif req_name is not None:
            if curr_name:
                self._commands.append("vlan %s no name" % vlan_id)


def main():
    """ main entry point for module execution
    """
    OnyxVlanModule.main()


if __name__ == '__main__':
    main()
