#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties, dict_diff, search_obj_in_list
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import normalize_interface


class Lag_interfaces(ConfigBase):
    """
    The nxos_lag_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lag_interfaces',
    ]

    def __init__(self, module):
        super(Lag_interfaces, self).__init__(module)

    def get_lag_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lag_interfaces_facts = facts['ansible_network_resources'].get('lag_interfaces')
        if not lag_interfaces_facts:
            return []
        return lag_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_lag_interfaces_facts = self.get_lag_interfaces_facts()
        commands.extend(self.set_config(existing_lag_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                resp = self._connection.edit_config(commands)
                if 'response' in resp:
                    for item in resp['response']:
                        if item:
                            err_str = item
                            if err_str.lower().startswith('cannot add'):
                                self._module.fail_json(msg=err_str)
            result['changed'] = True
        result['commands'] = commands

        changed_lag_interfaces_facts = self.get_lag_interfaces_facts()

        result['before'] = existing_lag_interfaces_facts
        if result['changed']:
            result['after'] = changed_lag_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lag_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params.get('config')
        if want:
            for w in want:
                w.update(remove_empties(w))
                if 'members' in w and w['members']:
                    for item in w['members']:
                        item.update({'member': normalize_interface(item['member'])})
        have = existing_lag_interfaces_facts
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
        commands = list()

        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        elif state == 'deleted':
            commands.extend(self._state_deleted(want, have))
        else:
            for w in want:
                if state == 'merged':
                    commands.extend(self._state_merged(w, have))
                if state == 'replaced':
                    commands.extend(self._state_replaced(w, have))
        return commands

    def _state_replaced(self, w, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        merged_commands = self.set_commands(w, have)
        replaced_commands = self.del_intf_commands(w, have)
        if merged_commands:
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
            obj_in_want = search_obj_in_list(h['name'], want, 'name')
            if h == obj_in_want:
                continue
            commands.extend(self.del_all_commands(h))
        for w in want:
            commands.extend(self.set_commands(w, have))
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
                obj_in_have = search_obj_in_list(w['name'], have, 'name')
                commands.extend(self.del_all_commands(obj_in_have))
        else:
            if not have:
                return commands
            for h in have:
                commands.extend(self.del_all_commands(h))
        return commands

    def diff_list_of_dicts(self, want, have):
        if not want:
            want = []

        if not have:
            have = []

        diff = []
        for w_item in want:
            h_item = search_obj_in_list(w_item['member'], have, key='member') or {}
            delta = dict_diff(h_item, w_item)
            if delta:
                if 'member' not in delta.keys():
                    delta['member'] = w_item['member']
                diff.append(delta)

        return diff

    def intersect_list_of_dicts(self, w, h):
        intersect = []
        wmem = []
        hmem = []
        for d in w:
            wmem.append({'member': d['member']})
        for d in h:
            hmem.append({'member': d['member']})
        set_w = set(tuple(sorted(d.items())) for d in wmem)
        set_h = set(tuple(sorted(d.items())) for d in hmem)
        intersection = set_w.intersection(set_h)
        for element in intersection:
            intersect.append(dict((x, y) for x, y in element))
        return intersect

    def add_commands(self, diff, name):
        commands = []
        name = name.strip('port-channel')
        for d in diff:
            commands.append('interface' + ' ' + d['member'])
            cmd = ''
            group_cmd = 'channel-group {0}'.format(name)
            if 'force' in d:
                cmd = group_cmd + ' force ' + d['force']
            if 'mode' in d:
                if cmd:
                    cmd = cmd + ' mode ' + d['mode']
                else:
                    cmd = group_cmd + ' mode ' + d['mode']
            if not cmd:
                cmd = group_cmd
            commands.append(cmd)
        return commands

    def set_commands(self, w, have):
        commands = []
        obj_in_have = search_obj_in_list(w['name'], have, 'name')
        if not obj_in_have:
            commands = self.add_commands(w['members'], w['name'])
        else:
            diff = self.diff_list_of_dicts(w['members'], obj_in_have['members'])
            commands = self.add_commands(diff, w['name'])
        return commands

    def del_all_commands(self, obj_in_have):
        commands = []
        if not obj_in_have:
            return commands
        for m in obj_in_have['members']:
            commands.append('interface' + ' ' + m['member'])
            commands.append('no channel-group')
        return commands

    def del_intf_commands(self, w, have):
        commands = []
        obj_in_have = search_obj_in_list(w['name'], have, 'name')
        if obj_in_have:
            lst_to_del = self.intersect_list_of_dicts(w['members'], obj_in_have['members'])
            if lst_to_del:
                for item in lst_to_del:
                    commands.append('interface' + ' ' + item['member'])
                    commands.append('no channel-group')
        return commands
