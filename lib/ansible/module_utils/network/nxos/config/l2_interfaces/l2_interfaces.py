#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_l2_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import dict_diff, to_list, remove_empties
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import flatten_dict, get_interface_type, normalize_interface, search_obj_in_list, vlan_range_to_list


class L2_interfaces(ConfigBase):
    """
    The nxos_l2_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l2_interfaces',
    ]

    exclude_params = [
        'vlan',
        'allowed_vlans',
        'native_vlans',
    ]

    def __init__(self, module):
        super(L2_interfaces, self).__init__(module)

    def get_l2_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        l2_interfaces_facts = facts['ansible_network_resources'].get('l2_interfaces')
        if not l2_interfaces_facts:
            return []
        return l2_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l2_interfaces_facts = self.get_l2_interfaces_facts()
        commands.extend(self.set_config(existing_l2_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_l2_interfaces_facts = self.get_l2_interfaces_facts()

        result['before'] = existing_l2_interfaces_facts
        if result['changed']:
            result['after'] = changed_l2_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l2_interfaces_facts):
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
                w.update({'name': normalize_interface(w['name'])})
                self.expand_trunk_allowed_vlans(w)
                want.append(remove_empties(w))
        have = existing_l2_interfaces_facts
        for h in have:
            self.expand_trunk_allowed_vlans(h)
        resp = self.set_state(want, have)
        return to_list(resp)

    def expand_trunk_allowed_vlans(self, d):
        if not d:
            return None
        if 'trunk' in d and d['trunk']:
            if 'allowed_vlans' in d['trunk']:
                allowed_vlans = vlan_range_to_list(d['trunk']['allowed_vlans'])
                vlans_list = [str(l) for l in sorted(allowed_vlans)]
                d['trunk']['allowed_vlans'] = ",".join(vlans_list)

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
        if obj_in_have:
            diff = dict_diff(w, obj_in_have)
        else:
            diff = w
        merged_commands = self.set_commands(w, have, True)
        if 'name' not in diff:
            diff['name'] = w['name']
        wkeys = w.keys()
        dkeys = diff.keys()
        for k in w.copy():
            if k in self.exclude_params and k in dkeys:
                del diff[k]
        replaced_commands = self.del_attribs(diff)

        if merged_commands or replaced_commands:
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
            commands.extend(self.set_commands(flatten_dict(w), have, True))
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

        cmd = 'no switchport '
        if 'vlan' in obj:
            commands.append(cmd + 'access vlan')
        if 'allowed_vlans' in obj:
            commands.append(cmd + 'trunk allowed vlan')
        if 'native_vlan' in obj:
            commands.append(cmd + 'trunk native vlan')
        if commands:
            commands.insert(0, 'interface ' + obj['name'])
        return commands

    def diff_of_dicts(self, w, obj):
        diff = set(w.items()) - set(obj.items())
        diff = dict(diff)
        if diff and w['name'] == obj['name']:
            diff.update({'name': w['name']})
        return diff

    def add_commands(self, d, vlan_exists=False):
        commands = []
        if not d:
            return commands

        cmd = 'switchport '
        if 'vlan' in d:
            commands.append(cmd + 'access vlan ' + str(d['vlan']))
        if 'allowed_vlans' in d:
            if vlan_exists:
                commands.append(cmd + 'trunk allowed vlan add ' + str(d['allowed_vlans']))
            else:
                commands.append(cmd + 'trunk allowed vlan ' + str(d['allowed_vlans']))
        if 'native_vlan' in d:
            commands.append(cmd + 'trunk native vlan ' + str(d['native_vlan']))
        if commands:
            commands.insert(0, 'interface ' + d['name'])
        return commands

    def set_commands(self, w, have, replace=False):
        commands = []
        vlan_tobe_added = []
        obj_in_have = flatten_dict(search_obj_in_list(w['name'], have, 'name'))
        if not obj_in_have:
            commands = self.add_commands(w)
        else:
            diff = self.diff_of_dicts(w, obj_in_have)
            if diff and not replace:
                if "allowed_vlans" in diff.keys() and diff["allowed_vlans"]:
                    vlan_tobe_added = diff["allowed_vlans"].split(',')
                    vlan_list = vlan_tobe_added[:]
                    have_vlans = obj_in_have["allowed_vlans"].split(',')
                    for w_vlans in vlan_list:
                        if w_vlans in have_vlans:
                            vlan_tobe_added.pop(vlan_tobe_added.index(w_vlans))
                    if vlan_tobe_added:
                        diff.update({"allowed_vlans": ','.join(vlan_tobe_added)})
                        commands = self.add_commands(diff, True)
                    return commands
            commands = self.add_commands(diff)
        return commands
