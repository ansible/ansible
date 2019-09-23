#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_static_routes class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff, remove_empties
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network. vyos.utils.utils import search_obj_in_list, get_route_type, \
    diff_list_of_dicts, get_lst_diff_for_dicts, dict_delete


class Static_routes(ConfigBase):
    """
    The vyos_static_routes class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'static_routes',
    ]

    params = ['address', 'blackhole_config', 'next_hop']

    def __init__(self, module):
        super(Static_routes, self).__init__(module)

    def get_static_routes_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        static_routes_facts = facts['ansible_network_resources'].get('static_routes')
        if not static_routes_facts:
            return []
        return static_routes_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_static_routes_facts = self.get_static_routes_facts()
        commands.extend(self.set_config(existing_static_routes_facts))
        if commands:
            if self._module.check_mode:
                resp = self._connection.edit_config(commands, commit=False)
            else:
                resp = self._connection.edit_config(commands)
            result['changed'] = True

        result['commands'] = commands

        if self._module._diff:
            result['diff'] = resp['diff'] if result['changed'] else None

        changed_static_routes_facts = self.get_static_routes_facts()

        result['before'] = existing_static_routes_facts
        if result['changed']:
            result['after'] = changed_static_routes_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_static_routes_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_static_routes_facts
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
            commands.extend(self._state_overridden(want=want, have=have))
        elif state == 'deleted':
            if want:
                for item in want:
                    route = item['address']
                    have_item = search_obj_in_list(route, have, 'address')
                    commands.extend(self._state_deleted(want=None, have=have_item))
            else:
                for have_item in have:
                    commands.extend(self._state_deleted(want=None, have=have_item))
        else:
            for want_item in want:
                route = want_item['address']
                have_item = search_obj_in_list(route, have, 'address')
                if state == 'merged':
                    commands.extend(self._state_merged(want=want_item, have=have_item))
                else:
                    commands.extend(self._state_replaced(want=want_item, have=have_item))
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
        for have_item in have:
            route_address = have_item['address']
            route_in_want = search_obj_in_list(route_address, want, 'address')
            if not route_in_want:
                commands.append(
                    self._compute_command(have_item['address'], remove=True)
                )

        for want_item in want:
            route_address = want_item['address']
            route_in_have = search_obj_in_list(route_address, have, 'address')
            commands.extend(self._state_replaced(want_item, route_in_have))
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        if have:
            commands.extend(self._render_updates(want, have))
        else:
            commands.extend(self._render_set_commands(want))
        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:
            params = Static_routes.params
            for attrib in params:
                if attrib == 'next_hop':
                    commands.extend(self._update_next_hop(want, have))
                elif attrib == 'blackhole_config':
                    commands.extend(self._update_blackhole(attrib, want, have))
        elif have:
            commands.append(
                self._compute_command(address=have['address'], remove=True)
            )
        return commands

    def _render_set_commands(self, want):
        commands = []
        have = {}
        for key, value in iteritems(want):
            if value:
                if key == 'address':
                        commands.append(
                            self._compute_command(address=want['address'])
                        )
                elif key == 'blackhole_config':
                    commands.extend(self._add_blackhole(key, want, have))

                elif key == 'next_hop':
                    commands.extend(self._add_next_hop(want, have))

        return commands

    def _add_blackhole(self, key, want, have):
        commands = []
        want_copy = deepcopy(remove_empties(want))
        have_copy = deepcopy(remove_empties(have))

        want_blackhole = want_copy.get(key) or {}
        have_blackhole = have_copy.get(key) or {}

        updates = dict_delete(want_blackhole, have_blackhole)
        if updates:
            for attrib, value in iteritems(updates):
                if value:
                    if attrib == 'distance':
                        commands.append(
                            self._compute_command(address=want['address'], key='blackhole',
                                                  attrib=attrib, remove=False, value=str(value))
                        )
                    elif attrib == 'type':
                        commands.append(
                            self._compute_command(address=want['address'], key='blackhole')
                        )
        return commands

    def _add_next_hop(self, want, have):
        commands = []
        want_copy = deepcopy(remove_empties(want))
        have_copy = deepcopy(remove_empties(have))
        diff_next_hops = get_lst_diff_for_dicts(want_copy, have_copy, 'next_hop')
        if diff_next_hops:
            for hop in diff_next_hops:
                for element in hop:
                    if element == 'address':
                        commands.append(
                            self._compute_command(address=want['address'],
                                                  key='next-hop', value=hop[element])
                        )
                    elif element == 'enabled' and not hop[element]:
                        commands.append(
                            self._compute_command(address=want['address'],
                                                  key='next-hop', attrib=hop['address'], value='disable')
                        )
                    elif element == 'distance':
                        commands.append(
                            self._compute_command(address=want['address'], key='next-hop',
                                                  attrib=hop['address'] + element, value=str(hop[element]))
                        )
        return commands

    def _update_blackhole(self, key, want, have):
        commands = []
        want_copy = deepcopy(remove_empties(want))
        have_copy = deepcopy(remove_empties(have))

        want_blackhole = want_copy.get(key) or {}
        have_blackhole = have_copy.get(key) or {}
        updates = dict_delete(have_blackhole, want_blackhole)
        if updates:
            for attrib, value in iteritems(updates):
                if value:
                    if attrib == 'distance':
                        commands.append(
                            self._compute_command(address=want['address'], key='blackhole',
                                                  attrib=attrib, remove=True, value=str(value))
                        )
                    elif attrib == 'type':
                        commands.append(
                            self._compute_command(address=want['address'], key='blackhole', remove=True)
                        )
        return commands

    def _update_next_hop(self, want, have):
        commands = []

        want_copy = deepcopy(remove_empties(want))
        have_copy = deepcopy(remove_empties(have))

        diff_next_hops = get_lst_diff_for_dicts(have_copy, want_copy, 'next_hop')
        if diff_next_hops:
            for hop in diff_next_hops:
                for element in hop:
                    if element == 'address':
                        commands.append(
                            self._compute_command(address=want['address'], key='next-hop', value=hop[element], remove=True)
                        )
                    elif element == 'enabled':
                        commands.append(
                            self._compute_command(address=want['address'],
                                                  key='next-hop', attrib=hop['address'], value='disable', remove=True)
                        )
                    elif element =='distance':
                        commands.append(
                            self._compute_command(address=want['address'], key='next-hop',
                                                  attrib=hop['address'] + element, value=str(hop[element]), remove=True)
                        )
        return commands

    def _render_updates(self, want, have):
        commands = []

        temp_have_next_hops = have.pop('next_hop', None)
        temp_want_next_hops = want.pop('next_hop', None)

        updates = dict_diff(have, want)

        if temp_have_next_hops:
            have['next_hop'] = temp_have_next_hops
        if temp_want_next_hops:
            want['next_hop'] = temp_want_next_hops

        commands.extend(self._add_next_hop(want, have))

        if updates:
            for key, value in iteritems(updates):
                if value:
                    if key == 'blackhole_config':
                        commands.extend(
                            self._add_blackhole(key, want, have)
                        )
                    elif key == 'next_hop':
                        commands.extend(
                            self._add_next_hop(want, have)
                        )
        return commands

    def _compute_command(self, address, key=None, attrib=None, value=None, remove=False):
        if remove:
            cmd = 'delete protocols static ' + get_route_type(address)
        else:
            cmd = 'set protocols static ' + get_route_type(address)
        cmd += (' ' + address)
        if key:
            cmd += (' ' + key)
        if attrib:
            cmd += (' ' + attrib)
        if value:
            cmd += (" '" + value + "'")
        return cmd



