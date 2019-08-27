#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_lldp_global class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties, dict_diff, dict_merge
from ansible.module_utils.network.nxos.facts.facts import Facts


class Lldp_global(ConfigBase):
    """
    The nxos_lldp_global class
    """
    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_global',
    ]

    def __init__(self, module):
        super(Lldp_global, self).__init__(module)

    def get_lldp_global_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        lldp_global_facts = facts['ansible_network_resources'].get(
            'lldp_global')
        if not lldp_global_facts:
            return {}
        return lldp_global_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_lldp_global_facts = self.get_lldp_global_facts()
        commands.extend(self.set_config(existing_lldp_global_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lldp_global_facts = self.get_lldp_global_facts()

        result['before'] = dict(existing_lldp_global_facts)
        if result['changed']:
            result['after'] = dict(changed_lldp_global_facts)
        result['warnings'] = warnings
        return result

    def set_config(self, existing_lldp_global_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lldp_global_facts
        resp = self.set_state(remove_empties(want), have)
        return resp

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        if state == 'deleted':
            commands = self._state_deleted(have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        merge_dict = dict_diff(have, want)
        #  merge_dict will contain new and unique values in want
        delete_dict = self.find_delete_params(have, want)
        self._module.params['state'] = 'deleted'
        commands.extend(self._state_deleted(delete_dict))  # delete
        self._module.params['state'] = 'merged'
        commands.extend(self.set_commands(merge_dict))  # merge
        self._module.params['state'] = 'replaced'
        return commands

    def delete_nested_dict(self, have, want):
        """
        Returns tlv_select nested dict that needs to be defaulted
        """
        outer_dict = {}
        for key, val in have.items():
            inner_dict = {}
            if not isinstance(val, dict):
                if key not in want.keys():
                    inner_dict.update({key: val})
                    return inner_dict
            else:
                if key in want.keys():
                    outer_dict.update(
                        {key: self.delete_nested_dict(val, want[key])})
                else:
                    outer_dict.update({key: val})
        return outer_dict

    def find_delete_params(self, have, want):
        """
        Returns parameters that are present in have and not in want, that need to be defaulted
        """
        delete_dict = {}
        for key, val in have.items():
            if key not in want.keys():
                delete_dict.update({key: val})
            else:
                if key == 'tlv_select':
                    delete_dict.update({key: self.delete_nested_dict(
                        have['tlv_select'], want['tlv_select'])})
        return delete_dict

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        diff = dict_diff(have, want)
        commands.extend(self.set_commands(diff))
        return commands

    def _state_deleted(self, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if have:
            for key, val in have.items():
                if 'tlv_select' in key:
                    commands.extend(self.process_nested_dict(val))
                else:
                    if key == 'port_id':
                        key = 'portid-subtype'
                    commands.append('no lldp ' + key + ' ' + str(val))

        return commands

    def set_commands(self, diff):
        commands = []
        for key, val in diff.items():
            commands.extend(self.add_commands(key, val))
        return commands

    def add_commands(self, key, val):
        command = []
        if 'port_id' in key:
            command.append('lldp portid-subtype ' + str(val))
        elif 'tlv_select' in key:
            command.extend(self.process_nested_dict(val))
        else:
            if val:
                command.append('lldp ' + key + ' ' + str(val))
        return command

    def process_nested_dict(self, val):
        nested_commands = []
        for k, v in val.items():
            if isinstance(v, dict):
                for k1, v1 in v.items():
                    com1 = 'lldp tlv-select '
                    com2 = ''
                    if 'system' in k:
                        com2 = 'system-' + k1
                    elif 'management_address' in k:
                        com2 = 'management-address ' + k1
                    elif 'port' in k:
                        com2 = 'port-' + k1

                    com1 += com2
                    com1 = self.negate_command(com1, v1)
                    nested_commands.append(com1)
            else:
                com1 = 'lldp tlv-select '
                if 'power_management' in k:
                    com1 += 'power-management'
                else:
                    com1 += k

                com1 = self.negate_command(com1, v)
                nested_commands.append(com1)
        return nested_commands

    def negate_command(self, command, val):
        # for merged, replaced vals need to be checked to add 'no'
        if self._module.params['state'] == 'merged':
            if not val:
                command = 'no ' + command
        return command
