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
from ansible.module_utils.network. vyos.utils.utils import get_route_type, \
    get_lst_diff_for_dicts, get_lst_same_for_dicts, dict_delete


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

    def __init__(self, module):
        super(Static_routes, self).__init__(module)

    def get_static_routes_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources, data=data)
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

        if self.state in self.ACTION_STATES:
            existing_static_routes_facts = self.get_static_routes_facts()
        else:
            existing_static_routes_facts = []

        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_static_routes_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True

        if self.state in self.ACTION_STATES:
            result['commands'] = commands

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_static_routes_facts = self.get_static_routes_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            running_config = self._module.params['running_config']
            if not running_config:
                self._module.fail_json(
                    msg="value of running_config parameter must not be empty for state parsed"
                )
            result['parsed'] = self.get_static_routes_facts(data=running_config)
        else:
            changed_static_routes_facts = []

        if self.state in self.ACTION_STATES:
            result['before'] = existing_static_routes_facts
            if result['changed']:
                result['after'] = changed_static_routes_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_static_routes_facts

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
        if self.state in ('merged', 'replaced', 'overridden', 'rendered') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(self.state))
        if self.state == 'overridden':
            commands.extend(self._state_overridden(want=want, have=have))
        elif self.state == 'deleted':
            commands.extend(self._state_deleted(want=want, have=have))
        elif want:
            routes = self._get_routes(want)
            for r in routes:
                h_item = self.search_route_in_have(have, r['dest'])
                if self.state == 'merged' or self.state == 'rendered':
                    commands.extend(self._state_merged(want=r, have=h_item))
                elif self.state == 'replaced':
                    commands.extend(self._state_replaced(want=r, have=h_item))
        return commands

    def search_route_in_have(self, have, want_dest):
        """
        This function  returns the route if its found in
        have config.
        :param have:
        :param dest:
        :return: the matched route
        """
        routes = self._get_routes(have)
        for r in routes:
            if r['dest'] == want_dest:
                return r
        return None

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if have:
            for key, value in iteritems(want):
                if value:
                    if key == 'next_hops':
                        commands.extend(self._update_next_hop(want, have))
                    elif key == 'blackhole_config':
                        commands.extend(self._update_blackhole(key, want, have))
        commands.extend(self._state_merged(want, have))
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        routes = self._get_routes(have)
        for r in routes:
            route_in_want = self.search_route_in_have(want, r['dest'])
            if not route_in_want:
                commands.append(self._compute_command(r['dest'], remove=True))
        routes = self._get_routes(want)
        for r in routes:
            route_in_have = self.search_route_in_have(have, r['dest'])
            commands.extend(self._state_replaced(r, route_in_have))
        return commands

    def _state_merged(self, want, have, opr=True):
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
            routes = self._get_routes(want)
            if not routes:
                for w in want:
                    af = w['address_families']
                    for item in af:
                        if self.afi_in_have(have, item):
                            commands.append(self._compute_command(afi=item['afi'], remove=True))
            for r in routes:
                h_route = self.search_route_in_have(have, r['dest'])
                if h_route:
                    commands.extend(self._render_updates(r, h_route, opr=False))
        else:
            routes = self._get_routes(have)
            if self._is_ip_route_exist(routes):
                commands.append(self._compute_command(afi='ipv4', remove=True))
            if self._is_ip_route_exist(routes, 'route6'):
                commands.append(self._compute_command(afi='ipv6', remove=True))
        return commands

    def _render_set_commands(self, want):
        """
        This function returns the list of commands to add attributes which are
        present in want
        :param want:
        :return: list of commands.
        """
        commands = []
        have = {}
        for key, value in iteritems(want):
            if value:
                if key == 'dest':
                    commands.append(
                        self._compute_command(dest=want['dest'])
                    )
                elif key == 'blackhole_config':
                    commands.extend(self._add_blackhole(key, want, have))

                elif key == 'next_hops':
                    commands.extend(self._add_next_hop(want, have))

        return commands

    def _add_blackhole(self, key, want, have):
        """
        This function gets the diff for blackhole config specific attributes
        and form the commands for attributes which are present in want but not in have.
        :param key:
        :param want:
        :param have:
        :return: list of commands
        """
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
                            self._compute_command(dest=want['dest'], key='blackhole',
                                                  attrib=attrib, remove=False, value=str(value))
                        )
                    elif attrib == 'type':
                        commands.append(
                            self._compute_command(dest=want['dest'], key='blackhole')
                        )
        return commands

    def _add_next_hop(self, want, have, opr=True):
        """
        This function gets the diff for next hop specific attributes
        and form the commands to add attributes which are present in want but not in have.
        :param want:
        :param have:
        :return: list of commands.
        """
        commands = []
        want_copy = deepcopy(remove_empties(want))
        have_copy = deepcopy(remove_empties(have))
        if not opr:
            diff_next_hops = get_lst_same_for_dicts(want_copy, have_copy, 'next_hops')
        else:
            diff_next_hops = get_lst_diff_for_dicts(want_copy, have_copy, 'next_hops')
        if diff_next_hops:
            for hop in diff_next_hops:
                for element in hop:
                    if element == 'forward_router_address':
                        commands.append(
                            self._compute_command(dest=want['dest'],
                                                  key='next-hop',
                                                  value=hop[element],
                                                  opr=opr)
                        )
                    elif element == 'enabled' and not hop[element]:
                        commands.append(
                            self._compute_command(dest=want['dest'],
                                                  key='next-hop',
                                                  attrib=hop['forward_router_address'],
                                                  value='disable',
                                                  opr=opr)
                        )
                    elif element == 'admin_distance':
                        commands.append(
                            self._compute_command(dest=want['dest'],
                                                  key='next-hop',
                                                  attrib=hop['forward_router_address'] + " " + element,
                                                  value=str(hop[element]),
                                                  opr=opr)
                        )
                    elif element == 'interface':
                        commands.append(
                            self._compute_command(dest=want['dest'],
                                                  key='next-hop',
                                                  attrib=hop['forward_router_address'] + " " + element,
                                                  value=hop[element],
                                                  opr=opr)
                        )
        return commands

    def _update_blackhole(self, key, want, have):
        """
        This function gets the difference for blackhole dict and
        form the commands to delete the attributes which are present in have but not in want.
        :param want:
        :param have:
        :return: list of commands
        :param key:
        :param want:
        :param have:
        :return: list of commands
        """
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
                            self._compute_command(dest=want['dest'], key='blackhole',
                                                  attrib=attrib, remove=True, value=str(value))
                        )
                    elif attrib == 'type' and 'distance' not in want_blackhole.keys():
                        commands.append(
                            self._compute_command(dest=want['dest'], key='blackhole', remove=True)
                        )
        return commands

    def _update_next_hop(self, want, have, opr=True):
        """
        This function gets the difference for next_hops list and
        form the commands to delete the attributes which are present in have but not in want.
        :param want:
        :param have:
        :return: list of commands
        """
        commands = []

        want_copy = deepcopy(remove_empties(want))
        have_copy = deepcopy(remove_empties(have))

        diff_next_hops = get_lst_diff_for_dicts(have_copy, want_copy, 'next_hops')
        if diff_next_hops:
            for hop in diff_next_hops:
                for element in hop:
                    if element == 'forward_router_address':
                        commands.append(
                            self._compute_command(dest=want['dest'], key='next-hop', value=hop[element], remove=True)
                        )
                    elif element == 'enabled':
                        commands.append(
                            self._compute_command(dest=want['dest'],
                                                  key='next-hop', attrib=hop['forward_router_address'], value='disable', remove=True)
                        )
                    elif element == 'admin_distance':
                        commands.append(
                            self._compute_command(dest=want['dest'], key='next-hop',
                                                  attrib=hop['forward_router_address'] + " " + element, value=str(hop[element]), remove=True)
                        )
                    elif element == 'interface':
                        commands.append(
                            self._compute_command(dest=want['dest'], key='next-hop',
                                                  attrib=hop['forward_router_address'] + " " + element, value=hop[element], remove=True)
                        )
        return commands

    def _render_updates(self, want, have, opr=True):
        """
        This function takes the diff between want and have and
        invokes the appropriate functions to create the commands
        to update the attributes.
        :param want:
        :param have:
        :return: list of commands
        """
        commands = []
        want_nh = want.get('next_hops') or []
        # delete static route operation per destination
        if not opr and not want_nh:
            commands.append(self._compute_command(dest=want['dest'], remove=True))

        else:
            temp_have_next_hops = have.pop('next_hops', None)
            temp_want_next_hops = want.pop('next_hops', None)
            updates = dict_diff(have, want)
            if temp_have_next_hops:
                have['next_hops'] = temp_have_next_hops
            if temp_want_next_hops:
                want['next_hops'] = temp_want_next_hops
            commands.extend(self._add_next_hop(want, have, opr=opr))

            if opr and updates:
                for key, value in iteritems(updates):
                    if value:
                        if key == 'blackhole_config':
                            commands.extend(self._add_blackhole(key, want, have))
        return commands

    def _compute_command(self, dest=None, key=None, attrib=None, value=None, remove=False, afi=None, opr=True):
        """
        This functions construct the required command based on the passed arguments.
        :param dest:
        :param key:
        :param attrib:
        :param value:
        :param remove:
        :return:  constructed command
        """
        if remove or not opr:
            cmd = 'delete protocols static ' + self.get_route_type(dest, afi)
        else:
            cmd = 'set protocols static ' + self.get_route_type(dest, afi)
        if dest:
            cmd += (' ' + dest)
        if key:
            cmd += (' ' + key)
        if attrib:
            cmd += (' ' + attrib)
        if value:
            cmd += (" '" + value + "'")
        return cmd

    def afi_in_have(self, have, w_item):
        """
        This functions checks for the afi
        list in have
        :param have:
        :param w_item:
        :return:
        """
        if have:
            for h in have:
                af = h.get('address_families') or []
            for item in af:
                if w_item['afi'] == item['afi']:
                    return True
        return False

    def get_route_type(self, dest=None, afi=None):
        """
        This function returns the route type based on
        destination ip address or afi
        :param address:
        :return:
        """
        if dest:
            return get_route_type(dest)
        elif afi == 'ipv4':
            return 'route'
        elif afi == 'ipv6':
            return 'route6'

    def _is_ip_route_exist(self, routes, type='route'):
        """
        This functions checks for the type of route.
        :param routes:
        :param type:
        :return: True/False
        """
        for r in routes:
            if type == self.get_route_type(r['dest']):
                return True
        return False

    def _get_routes(self, lst):
        """
        This function returns the list of routes
        :param lst: list of address families
        :return: list of routes
        """
        r_list = []
        for item in lst:
            af = item['address_families']
            for element in af:
                routes = element.get('routes') or []
                for r in routes:
                    r_list.append(r)
        return r_list
