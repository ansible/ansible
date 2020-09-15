#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_lacp_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff, remove_empties
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import flatten_dict, search_obj_in_list, get_interface_type, normalize_interface


class Lacp_interfaces(ConfigBase):
    """
    The nxos_lacp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lacp_interfaces',
    ]

    exclude_params = [
        'port_priority',
        'rate',
        'min',
        'max',
    ]

    def __init__(self, module):
        super(Lacp_interfaces, self).__init__(module)

    def get_lacp_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lacp_interfaces_facts = facts['ansible_network_resources'].get('lacp_interfaces')
        if not lacp_interfaces_facts:
            return []
        return lacp_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_lacp_interfaces_facts = self.get_lacp_interfaces_facts()
        commands.extend(self.set_config(existing_lacp_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lacp_interfaces_facts = self.get_lacp_interfaces_facts()

        result['before'] = existing_lacp_interfaces_facts
        if result['changed']:
            result['after'] = changed_lacp_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lacp_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params.get('config')
        want = []
        if config:
            for w in config:
                if get_interface_type(w['name']) not in ('portchannel', 'ethernet'):
                    self._module.fail_json(msg='This module works with either portchannel or ethernet')
                w.update({'name': normalize_interface(w['name'])})
                want.append(remove_empties(w))
        have = existing_lacp_interfaces_facts
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
        state = self._module.params['state']
        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='config is required for state {0}'.format(state))
        commands = list()

        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        elif state == 'deleted':
            commands.extend(self._state_deleted(want, have))
        else:
            for w in want:
                if state == 'merged':
                    commands.extend(self._state_merged(flatten_dict(w), have))
                elif state == 'replaced':
                    commands.extend(self._state_replaced(flatten_dict(w), have))
        return commands

    def _state_replaced(self, w, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        obj_in_have = flatten_dict(search_obj_in_list(w['name'], have, 'name'))
        diff = dict_diff(w, obj_in_have)
        merged_commands = self.set_commands(w, have)
        if 'name' not in diff:
            diff['name'] = w['name']
        wkeys = w.keys()
        dkeys = diff.keys()
        for k in wkeys:
            if k in self.exclude_params and k in dkeys:
                del diff[k]
        replaced_commands = self.del_attribs(diff)

        if merged_commands:
            cmds = set(replaced_commands).intersection(set(merged_commands))
            for cmd in cmds:
                merged_commands.remove(cmd)
            commands.extend(replaced_commands)
            commands.extend(merged_commands)
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for h in have:
            h = flatten_dict(h)
            obj_in_want = flatten_dict(search_obj_in_list(h['name'], want, 'name'))
            if h == obj_in_want:
                continue
            for w in want:
                w = flatten_dict(w)
                if h['name'] == w['name']:
                    wkeys = w.keys()
                    hkeys = h.keys()
                    for k in wkeys:
                        if k in self.exclude_params and k in hkeys:
                            del h[k]
            commands.extend(self.del_attribs(h))
        for w in want:
            commands.extend(self.set_commands(flatten_dict(w), have))
        return commands

    def _state_merged(self, w, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return self.set_commands(w, have)

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:
            for w in want:
                obj_in_have = flatten_dict(search_obj_in_list(w['name'], have, 'name'))
                commands.extend(self.del_attribs(obj_in_have))
        else:
            if not have:
                return commands
            for h in have:
                commands.extend(self.del_attribs(flatten_dict(h)))
        return commands

    def del_attribs(self, obj):
        commands = []
        if not obj or len(obj.keys()) == 1:
            return commands
        commands.append('interface ' + obj['name'])
        if 'graceful' in obj:
            commands.append('lacp graceful-convergence')
        if 'vpc' in obj:
            commands.append('no lacp vpn-convergence')
        if 'suspend_individual' in obj:
            commands.append('lacp suspend_individual')
        if 'mode' in obj:
            commands.append('no lacp mode ' + obj['mode'])
        if 'max' in obj:
            commands.append('no lacp max-bundle')
        if 'min' in obj:
            commands.append('no lacp min-links')
        if 'port_priority' in obj:
            commands.append('no lacp port-priority')
        if 'rate' in obj:
            commands.append('no lacp rate')
        return commands

    def diff_of_dicts(self, w, obj):
        diff = set(w.items()) - set(obj.items())
        diff = dict(diff)
        if diff and w['name'] == obj['name']:
            diff.update({'name': w['name']})
        return diff

    def add_commands(self, d):
        commands = []
        if not d:
            return commands
        commands.append('interface' + ' ' + d['name'])

        if 'port_priority' in d:
            commands.append('lacp port-priority ' + str(d['port_priority']))
        if 'rate' in d:
            commands.append('lacp rate ' + str(d['rate']))
        if 'min' in d:
            commands.append('lacp min-links ' + str(d['min']))
        if 'max' in d:
            commands.append('lacp max-bundle ' + str(d['max']))
        if 'mode' in d:
            commands.append('lacp mode ' + d['mode'])
        if 'suspend_individual' in d:
            if d['suspend_individual'] is True:
                commands.append('lacp suspend-individual')
            else:
                commands.append('no lacp suspend-individual')
        if 'graceful' in d:
            if d['graceful'] is True:
                commands.append('lacp graceful-convergence')
            else:
                commands.append('no lacp graceful-convergence')
        if 'vpc' in d:
            if d['vpc'] is True:
                commands.append('lacp vpc-convergence')
            else:
                commands.append('no lacp vpc-convergence')
        return commands

    def set_commands(self, w, have):
        commands = []
        obj_in_have = flatten_dict(search_obj_in_list(w['name'], have, 'name'))
        if not obj_in_have:
            commands = self.add_commands(w)
        else:
            diff = self.diff_of_dicts(w, obj_in_have)
            commands = self.add_commands(diff)
        return commands
