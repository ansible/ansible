# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.network.common.utils import to_list, dict_diff
from ansible.module_utils.six import iteritems
from ansible.module_utils.network. \
    vyos.utils.utils import search_obj_in_list, \
    get_lst_diff_for_dicts, list_diff_want_only, list_diff_have_only


class Lag_interfaces(ConfigBase):
    """
    The vyos_lag_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lag_interfaces',
    ]

    params = ['arp-monitor', 'hash-policy', 'members', 'mode', 'name', 'primary']
    set_cmd = 'set interfaces bonding '
    del_cmd = 'delete interfaces bonding '

    def __init__(self, module):
        super(Lag_interfaces, self).__init__(module)

    def get_lag_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset,
                                                         self.gather_network_resources)
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
            if self._module.check_mode:
                resp = self._connection.edit_config(commands, commit=False)
            else:
                resp = self._connection.edit_config(commands)
            result['changed'] = True

        result['commands'] = commands

        if self._module._diff:
            result['diff'] = resp['diff'] if result['changed'] else None

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
        want = self._module.params['config']
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
        commands = []
        state = self._module.params['state']
        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        elif state == 'deleted':
            if want:
                for want_item in want:
                    name = want_item['name']
                    obj_in_have = search_obj_in_list(name, have)
                    commands.extend(self._state_deleted(obj_in_have))
            else:
                for have_item in have:
                    commands.extend(self._state_deleted(have_item))
        else:
            for want_item in want:
                name = want_item['name']
                obj_in_have = search_obj_in_list(name, have)
                if state == 'merged':
                    commands.extend(self._state_merged(want_item, obj_in_have))
                elif state == 'replaced':
                    commands.extend(self._state_replaced(want_item, obj_in_have))

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if have:
            commands.extend(Lag_interfaces._render_del_commands(want, have))
        commands.extend(Lag_interfaces._state_merged(want, have))
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for have_item in have:
            lag_name = have_item['name']
            obj_in_want = search_obj_in_list(lag_name, want)
            if not obj_in_want:
                commands.extend(Lag_interfaces._purge_attribs(have_item))

        for want_item in want:
            name = want_item['name']
            obj_in_have = search_obj_in_list(name, have)
            commands.extend(Lag_interfaces._state_replaced(want_item, obj_in_have))
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        if have:
            commands.extend(Lag_interfaces._render_updates(want, have))
        else:
            commands.extend(Lag_interfaces._render_set_commands(want))
        return commands

    def _state_deleted(self, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if have:
            commands.extend(Lag_interfaces._purge_attribs(have))
        return commands

    def _render_updates(self, want, have):
        commands = []

        lag_name = have['name']

        set_cmd = Lag_interfaces.set_cmd + lag_name
        try:
            temp_have_members = have.pop('members', None)
            temp_want_members = want.pop('members', None)
        except BaseException:
            pass

        updates = dict_diff(have, want)

        if temp_have_members:
            have['members'] = temp_have_members
        if temp_want_members:
            want['members'] = temp_want_members

        commands.extend(Lag_interfaces._add_bond_members(want, have))

        if updates:
            for key, value in iteritems(updates):
                if value:
                    if key == 'arp-monitor':
                        commands.extend(
                            Lag_interfaces._add_arp_monitor(updates, key, want, have)
                        )
                    else:
                        commands.append(
                            set_cmd + ' ' + key + " '" + str(value) + "'"
                        )
        return commands

    def _render_set_commands(self, want):
        commands = []
        have = []

        params = Lag_interfaces.params

        for attrib in params:
            value = want[attrib]
            if value:
                if attrib == 'arp-monitor':
                    commands.extend(
                        Lag_interfaces._add_arp_monitor(want, attrib, want, have)
                    )
                elif attrib == 'members':
                    commands.extend(
                        Lag_interfaces._add_bond_members(want, have)
                    )
                elif attrib != 'name':
                    commands.append(
                        Lag_interfaces.set_cmd + ' ' + attrib + " '" + str(value) + "'"
                    )
        return commands

    def _purge_attribs(self, have):
        commands = []
        del_lag = Lag_interfaces.del_cmd + have['name']

        for item in Lag_interfaces.params:
            if have.get(item):
                if item == 'members':
                    commands.extend(
                        Lag_interfaces._delete_bond_members(have)
                    )
                elif item != 'name':
                    commands.append(del_lag + ' ' + item)
        return commands

    def _render_del_commands(self, want, have):
        commands = []

        params = Lag_interfaces.params
        for attrib in params:
            if attrib == 'members':
                commands.extend(
                    Lag_interfaces._update_bond_members(attrib, want, have)
                )
            elif attrib == 'arp-monitor':
                commands.extend(
                    Lag_interfaces._update_arp_monitor(attrib, want, have)
                )
            elif have.get(attrib) and not want.get(attrib):
                commands.append(Lag_interfaces.del_cmd + ' ' + attrib)
        return commands

    def _add_bond_members(self, want, have):
        commands = []
        bond_name = want['name']
        diff_members = get_lst_diff_for_dicts(want, have, 'member')
        if diff_members:
            for key in diff_members:
                commands.append(
                    'set interfaces ethernet ' + key['member'] + ' bond-group ' + bond_name
                )
        return commands

    def _add_arp_monitor(self, updates, key, want, have):
        commands = []
        set_cmd = Lag_interfaces.set_cmd + ' ' + key
        arp_monitor = updates.get(key) or {}
        diff_targets = Lag_interfaces._get_arp_monitor_target_diff(want, have, key, 'target')

        if 'interval' in arp_monitor:
            commands.append(set_cmd + ' interval ' + str(arp_monitor['interval']))
        if diff_targets:
            for target in diff_targets:
                commands.append(set_cmd + ' target ' + target)
        return commands

    def _delete_bond_members(self, have):
        commands = []
        for member in have['members']:
            commands.append(
                'delete interfaces ethernet ' + member['member'] + ' bond-group ' + have['name']
            )
        return commands

    def _update_arp_monitor(self, key, want, have):
        commands = []
        want_arp_target = []
        have_arp_target = []
        want_arp_monitor = want.get(key) or {}
        have_arp_monitor = have.get(key) or {}
        del_cmd = Lag_interfaces.del_cmd + have['name']

        if want_arp_monitor and 'target' in want_arp_monitor:
            want_arp_target = want_arp_monitor['target']

        if have_arp_monitor and 'target' in have_arp_monitor:
            have_arp_target = have_arp_monitor['target']

        if 'interval' in have_arp_monitor and not want_arp_monitor:
            commands.append(del_cmd + ' ' + key + ' interval')
        if 'target' in have_arp_monitor:
            target_diff = list_diff_have_only(want_arp_target, have_arp_target)
            if target_diff:
                for target in target_diff:
                    commands.append(del_cmd + ' ' + key + ' target ' + target)

        return commands

    def _update_bond_members(self, key, want, have):
        commands = []
        name = have['name']
        want_members = want.get(key) or []
        have_members = have.get(key) or []

        members_diff = list_diff_have_only(want_members, have_members)
        if members_diff:
            for member in members_diff:
                commands.append(
                    'delete interfaces ethernet ' + member[key] + ' bond-group ' + name
                )
        return commands

    def _get_arp_monitor_target_diff(self, want_list, have_list, dict_name, lst):
        want_arp_target = []
        have_arp_target = []

        want_arp_monitor = want_list.get(dict_name) or {}
        if want_arp_monitor and lst in want_arp_monitor:
            want_arp_target = want_arp_monitor[lst]

        if not have_list:
            diff = want_arp_target
        else:
            have_arp_monitor = have_list.get(dict_name) or {}
            if have_arp_monitor and lst in have_arp_monitor:
                have_arp_target = have_arp_monitor[lst]

            diff = list_diff_want_only(want_arp_target, have_arp_target)
        return diff


