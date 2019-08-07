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
from __future__ import absolute_import, division, print_function
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
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lldp_global_facts = facts['ansible_network_resources'].get('lldp_global')
        if not lldp_global_facts:
            return []
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
        if len(have) == 0:
            have = {}
        resp = self.set_state(remove_empties(want), have)
        return resp.split('\n')[:-1]

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
        commands = ''
        diff = dict_diff(have, want)  # diff will contain unique and new values in want
        wantk = want.keys()  # find keys in want to ignore them for defaults
        havek = have.keys()
        wantk = self.get_nested_keys(want, wantk)
        havek = self.get_nested_keys(have, havek)
        include_params = list(set(havek) - set(wantk))  # keys in have and not in want; they need to be defaulted
        for param in include_params:
            commands += 'lldp '
            if 'holdtime' in param:
                commands += 'holdtime 120\n'
            elif 'timer' in param:
                commands += 'timer 30\n'
            elif 'reinit' in param:
                commands += 'reinit 2\n'
            elif 'port_id' in param:
                commands += 'portid-subtype 0\n'
            else:
                commands += param + '\n'
        commands += self.set_commands(diff)
        return commands

    def get_nested_keys(self, dict_param, keys):
        """
        Returns names of keys nested inside tlv_select
        """
        if 'tlv_select' in keys:
            keys.remove('tlv_select')
            for key in dict_param['tlv_select'].keys():
                if not isinstance(dict_param['tlv_select'][key], dict):
                    x = 'tlv_select ' + key
                    x = x.replace('_', '-')
                    keys.append(x)  # tlv-select dcbxp, tlv-select power-management
                else:
                    for k1 in dict_param['tlv_select'][key].keys():
                        key = key.replace('_', '-')
                        if k1 == 'v4' or k1 == 'v6':
                            x = 'tlv-select ' + key + ' ' + k1
                        else:
                            x = 'tlv-select ' + key + '-' + k1
                        keys.append(x)
        return keys

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = ''
        diff = dict_diff(have, want)
        commands += self.set_commands(diff)
        return commands

    def _state_deleted(self, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = ''
        for key, val in have.items():
            if 'holdtime' in key:
                if val != 120:
                    commands += 'lldp holdtime 120\n'
            elif 'timer' in key:
                if val != 30:
                    commands += 'lldp timer 30\n'
            elif 'reinit' in key:
                if val != 2:
                    commands += 'lldp reinit 2\n'
            elif 'port_id' in key:
                if val != 0:
                    commands += 'lldp portid-subtype 0\n'
            elif 'tlv_select' in key:
                commands += self.process_nested_dict(val)
        return commands

    def set_commands(self, diff):
        commands = ''
        for key, val in diff.items():
            commands += (self.add_commands(key, val))
        return commands

    def add_commands(self, key, val):
        command = ''
        if 'port_id' in key:
            command = 'lldp portid-subtype ' + str(val) + '\n'
        elif 'tlv_select' in key:
            command = self.process_nested_dict(val)
        else:
            if val:
                command = 'lldp ' + key + ' ' + str(val) + '\n'
        return command

    def process_nested_dict(self, val):
        nested_commands = ''
        state = self._module.params['state']
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
                    com1 += com2 + '\n'

                    if state != 'deleted':
                        if not v1:
                            com1 = 'no ' + com1
                    nested_commands += com1
            else:
                com1 = 'lldp tlv-select '
                if 'power_management' in k:
                    com1 += 'power-management'
                else:
                    com1 += k

                if state != 'deleted':  # deleted state will not have 'no lldp ' command
                    if not v:
                        com1 = 'no ' + com1
                nested_commands += com1 + '\n'
        return nested_commands
