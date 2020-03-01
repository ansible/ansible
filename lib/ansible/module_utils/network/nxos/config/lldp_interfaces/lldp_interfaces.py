#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_lldp_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties, dict_diff
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import flatten_dict, search_obj_in_list, get_interface_type, normalize_interface


class Lldp_interfaces(ConfigBase):
    """
    The nxos_lldp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_interfaces',
    ]

    def __init__(self, module):
        super(Lldp_interfaces, self).__init__(module)

    def get_lldp_interfaces_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data=data)
        lldp_interfaces_facts = facts['ansible_network_resources'].get(
            'lldp_interfaces')
        if not lldp_interfaces_facts:
            return []
        return lldp_interfaces_facts

    def edit_config(self, commands):
        """Wrapper method for `_connection.edit_config()`
        This exists solely to allow the unit test framework to mock device connection calls.
        """
        return self._connection.edit_config(commands)

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()
        state = self._module.params['state']
        action_states = ['merged', 'replaced', 'deleted', 'overridden']

        if state == 'gathered':
            result['gathered'] = self.get_lldp_interfaces_facts()
        elif state == 'rendered':
            result['rendered'] = self.set_config({})
        elif state == 'parsed':
            result['parsed'] = self.set_config({})
        else:
            existing_lldp_interfaces_facts = self.get_lldp_interfaces_facts()
            commands.extend(self.set_config(existing_lldp_interfaces_facts))
            if commands and state in action_states:
                if not self._module.check_mode:
                    self._connection.edit_config(commands)
                result['changed'] = True
                result['before'] = existing_lldp_interfaces_facts
                result['commands'] = commands
            result['commands'] = commands

            changed_lldp_interfaces_facts = self.get_lldp_interfaces_facts()

            if result['changed']:
                result['after'] = changed_lldp_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lldp_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params['config']
        want = []
        if config:
            for w in config:
                if get_interface_type(w['name']) not in ('management',
                                                         'ethernet'):
                    self._module.fail_json(
                        msg='This module works with either management or ethernet')
                w.update({'name': normalize_interface(w['name'])})
                want.append(remove_empties(w))
        have = existing_lldp_interfaces_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'rendered':
            commands = self._state_rendered(want)
        elif state == 'parsed':
            want = self._module.params['running_config']
            commands = self._state_parsed(want)
        else:
            for w in want:
                if state == 'merged':
                    commands.extend(self._state_merged(flatten_dict(w), have))
                elif state == 'replaced':
                    commands.extend(self._state_replaced(
                        flatten_dict(w), have))
        return commands

    def _state_parsed(self, want):
        return self.get_lldp_interfaces_facts(want)

    def _state_rendered(self, want):
        commands = []
        for w in want:
            commands.extend(self.set_commands(w, {}))
        return commands

    def _state_gathered(self, have):
        """ The command generator when state is gathered

        :rtype: A list
        :returns: the commands necessary to reproduce the current configuration
        """
        commands = []
        want = {}
        commands.append(self.set_commands(want, have))
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        del_commands = []
        delete_dict = {}
        obj_in_have = flatten_dict(
            search_obj_in_list(want['name'], have, 'name'))
        for k1 in obj_in_have.keys():
            if k1 not in want.keys():
                delete_dict.update({k1: obj_in_have[k1]})

        if delete_dict:
            delete_dict.update({'name': want['name']})
            del_commands = self.del_commands(delete_dict)
        merged_commands = self.set_commands(want, have)

        if merged_commands:
            cmds = set(del_commands).intersection(set(merged_commands))
            for cmd in cmds:
                merged_commands.remove(cmd)

        commands.extend(del_commands)
        commands.extend(merged_commands)
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_intfs = [w['name'] for w in want]
        for h in have:
            h = flatten_dict(h)
            delete_dict = {}
            if h['name'] in want_intfs:
                for w in want:
                    if w['name'] == h['name']:
                        delete_keys = list(set(h) - set(flatten_dict(w)))
                        for k in delete_keys:
                            delete_dict.update({k: h[k]})
                        delete_dict.update({'name': h['name']})
                        break
            else:
                delete_dict.update(h)
            commands.extend(self.del_commands(delete_dict))
        for w in want:
            commands.extend(self.set_commands(flatten_dict(w), have))
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return self.set_commands(want, have)

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
        of the provided objects
        """
        commands = []
        if want:
            for w in want:
                obj_in_have = flatten_dict(
                    search_obj_in_list(w['name'], have, 'name'))
                commands.extend(self.del_commands(obj_in_have))
        else:
            if not have:
                return commands
            for h in have:
                commands.extend(self.del_commands(flatten_dict(h)))
        return commands

    def set_commands(self, want, have):
        commands = []
        obj_in_have = flatten_dict(
            search_obj_in_list(want['name'], have, 'name'))
        if not obj_in_have:
            commands = self.add_commands(flatten_dict(want))
        else:
            diff = dict_diff(obj_in_have, want)
            if diff:
                diff.update({'name': want['name']})
                commands = self.add_commands(diff)
        return commands

    def add_commands(self, d):
        commands = []
        if not d:
            return commands
        commands.append('interface ' + d['name'])
        if 'transmit' in d:
            if (d['transmit']):
                commands.append('lldp transmit')
            else:
                commands.append('no lldp transmit')
        if 'receive' in d:
            if (d['receive']):
                commands.append('lldp receive')
            else:
                commands.append('no lldp receive')
        if 'management_address' in d:
            commands.append('lldp tlv-set management-address ' +
                            d['management_address'])
        if 'vlan' in d:
            commands.append('lldp tlv-set vlan ' + str(d['vlan']))

        return commands

    def del_commands(self, obj):
        commands = []
        if not obj or len(obj.keys()) == 1:
            return commands
        commands.append('interface ' + obj['name'])
        if 'transmit' in obj:
            commands.append('lldp transmit')
        if 'receive' in obj:
            commands.append('lldp receive')
        if 'management_address' in obj:
            commands.append('no lldp tlv-set management-address ' +
                            obj['management_address'])
        if 'vlan' in obj:
            commands.append('no lldp tlv-set vlan ' + str(obj['vlan']))

        return commands
