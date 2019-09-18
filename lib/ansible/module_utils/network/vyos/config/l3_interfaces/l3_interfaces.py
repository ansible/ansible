#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_l3_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.network. \
    vyos.utils.utils import search_obj_in_list, get_interface_type, diff_list_of_dicts


class L3_interfaces(ConfigBase):
    """
    The vyos_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces',
    ]

    def __init__(self, module):
        super(L3_interfaces, self).__init__(module)

    def get_l3_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        l3_interfaces_facts = facts['ansible_network_resources'].get('l3_interfaces')
        if not l3_interfaces_facts:
            return []
        return l3_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_l3_interfaces_facts = self.get_l3_interfaces_facts()
        commands.extend(self.set_config(existing_l3_interfaces_facts))
        if commands:
            if self._module.check_mode:
                resp = self._connection.edit_config(commands, commit=False)
            else:
                resp = self._connection.edit_config(commands)
            result['changed'] = True

        result['commands'] = commands

        if self._module._diff:
            result['diff'] = resp['diff'] if result['changed'] else None

        changed_l3_interfaces_facts = self.get_l3_interfaces_facts()

        result['before'] = existing_l3_interfaces_facts
        if result['changed']:
            result['after'] = changed_l3_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l3_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l3_interfaces_facts
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

        if state in ('merged', 'replaced', 'overridden') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands.extend(self._state_overridden(want=want, have=have))

        elif state == 'deleted':
            if not want:
                for intf in have:
                    commands.extend(
                        self._state_deleted(
                            {'name': intf['name']},
                            intf
                        )
                    )
            else:
                for item in want:
                    obj_in_have = search_obj_in_list(item['name'], have)
                    commands.extend(
                        self._state_deleted(
                            item, obj_in_have
                        )
                    )
        else:
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)

                if not obj_in_have:
                    obj_in_have = {'name': item['name']}

                if state == 'merged':
                    commands.extend(
                        self._state_merged(
                            item, obj_in_have
                        )
                    )

                elif state == 'replaced':
                    commands.extend(
                        self._state_replaced(
                            item, obj_in_have
                        )
                    )

        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if have:
            commands.extend(self._state_deleted(want, have))

        commands.extend(self._state_merged(want, have))

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for intf in have:
            intf_in_want = search_obj_in_list(intf['name'], want)
            if not intf_in_want:
                commands.extend(self._state_deleted({'name': intf['name']}, intf))

        for intf in want:
            intf_in_have = search_obj_in_list(intf['name'], have)
            commands.extend(self._state_replaced(intf, intf_in_have))

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want_copy = deepcopy(remove_empties(want))
        have_copy = deepcopy(remove_empties(have))

        want_vifs = want_copy.pop('vifs', [])
        have_vifs = have_copy.pop('vifs', [])

        for update in self._get_updates(want_copy, have_copy):
            for key, value in iteritems(update):
                commands.append(self._compute_commands(key=key, value=value, interface=want_copy['name']))

        if want_vifs:
            for want_vif in want_vifs:
                have_vif = search_obj_in_list(want_vif['vlan_id'], have_vifs, key='vlan_id')
                if not have_vif:
                    have_vif = {}

                for update in self._get_updates(want_vif, have_vif):
                    for key, value in iteritems(update):
                        commands.append(self._compute_commands(key=key, value=value, interface=want_copy['name'], vif=want_vif['vlan_id']))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        want_copy = deepcopy(remove_empties(want))
        have_copy = deepcopy(have)

        want_vifs = want_copy.pop('vifs', [])
        have_vifs = have_copy.pop('vifs', [])

        for update in self._get_updates(have_copy, want_copy):
            for key, value in iteritems(update):
                commands.append(self._compute_commands(key=key, value=value, interface=want_copy['name'], remove=True))

        if have_vifs:
            for have_vif in have_vifs:
                want_vif = search_obj_in_list(have_vif['vlan_id'], want_vifs, key='vlan_id')
                if not want_vif:
                    want_vif = {'vlan_id': have_vif['vlan_id']}

                for update in self._get_updates(have_vif, want_vif):
                    for key, value in iteritems(update):
                        commands.append(self._compute_commands(key=key, interface=want_copy['name'], value=value, vif=want_vif['vlan_id'], remove=True))

        return commands

    def _compute_commands(self, interface, key, vif=None, value=None, remove=False):
        intf_context = 'interfaces {0} {1}'.format(get_interface_type(interface), interface)
        set_cmd = 'set {0}'.format(intf_context)
        del_cmd = 'delete {0}'.format(intf_context)

        if vif:
            set_cmd = set_cmd + (' vif {0}'.format(vif))
            del_cmd = del_cmd + (' vif {0}'.format(vif))

        if remove:
            command = "{0} {1} '{2}'".format(del_cmd, key, value)
        else:
            command = "{0} {1} '{2}'".format(set_cmd, key, value)

        return command

    def _get_updates(self, want, have):
        updates = []

        updates = diff_list_of_dicts(want.get('ipv4', []), have.get('ipv4', []))
        updates.extend(diff_list_of_dicts(want.get('ipv6', []), have.get('ipv6', [])))

        return updates
