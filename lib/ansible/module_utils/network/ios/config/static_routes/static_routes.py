#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_static_routes class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts
from ansible.module_utils.network.ios.utils.utils import new_dict_to_set, validate_n_expand_ipv4, filter_dict_having_none_value


class Static_Routes(ConfigBase):
    """
    The ios_static_routes class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'static_routes',
    ]

    def __init__(self, module):
        super(Static_Routes, self).__init__(module)

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
        commands = list()
        warnings = list()

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
        state = self._module.params['state']
        if state in ('overridden', 'merged', 'replaced', 'rendered') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))
        commands = []
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged' or state == 'rendered':
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

        # Drill each iteration of want n have and then based on dest and afi tyoe comparison take config call
        for w in want:
            for addr_want in w.get('address_families'):
                for route_want in addr_want.get('routes'):
                    check = False
                    for h in have:
                        if h.get('address_families'):
                            for addr_have in h.get('address_families'):
                                for route_have in addr_have.get('routes'):
                                    if route_want.get('dest') == route_have.get('dest')\
                                            and addr_want['afi'] == addr_have['afi']:
                                        check = True
                                        have_set = set()
                                        new_hops = []
                                        for each in route_want.get('next_hops'):
                                            want_set = set()
                                            new_dict_to_set(each, [], want_set, 0)
                                            new_hops.append(want_set)
                                        new_dict_to_set(addr_have, [], have_set, 0)
                                        # Check if the have dict next_hops value is diff from want dict next_hops
                                        have_dict = filter_dict_having_none_value(route_want.get('next_hops')[0],
                                                                                  route_have.get('next_hops')[0])
                                        # update the have_dict with forward_router_address
                                        have_dict.update({'forward_router_address': route_have.get('next_hops')[0].
                                                         get('forward_router_address')})
                                        # updating the have_dict with next_hops val that's not None
                                        new_have_dict = {}
                                        for k, v in have_dict.items():
                                            if v is not None:
                                                new_have_dict.update({k: v})

                                        # Set the new config from the user provided want config
                                        cmd = self._set_config(w, h, addr_want, route_want, route_have, new_hops, have_set)

                                        if cmd:
                                            # since inplace update isn't allowed for static routes, preconfigured
                                            # static routes needs to be deleted before the new want static routes changes
                                            # are applied
                                            clear_route_have = copy.deepcopy(route_have)
                                            # inplace update is allowed in case of ipv6 static routes, so not deleting it
                                            # before applying the want changes
                                            if ':' not in route_want.get('dest'):
                                                commands.extend(self._clear_config({}, h, {}, addr_have,
                                                                                   {}, clear_route_have))
                                        commands.extend(cmd)
                                if check:
                                    break
                            if check:
                                break
                    if not check:
                        # For configuring any non-existing want config
                        new_hops = []
                        for each in route_want.get('next_hops'):
                            want_set = set()
                            new_dict_to_set(each, [], want_set, 0)
                            new_hops.append(want_set)
                        commands.extend(self._set_config(w, {}, addr_want, route_want, {}, new_hops, set()))
        commands = [each for each in commands if 'no' in each] + \
                   [each for each in commands if 'no' not in each]

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """

        commands = []
        # Creating a copy of want, so that want dict is intact even after delete operation
        # performed during override want n have comparison
        temp_want = copy.deepcopy(want)

        # Drill each iteration of want n have and then based on dest and afi tyoe comparison take config call
        for h in have:
            if h.get('address_families'):
                for addr_have in h.get('address_families'):
                    for route_have in addr_have.get('routes'):
                        check = False
                        for w in temp_want:
                            for addr_want in w.get('address_families'):
                                count = 0
                                for route_want in addr_want.get('routes'):
                                    if route_want.get('dest') == route_have.get('dest') \
                                            and addr_want['afi'] == addr_have['afi']:
                                        check = True
                                        have_set = set()
                                        new_hops = []
                                        for each in route_want.get('next_hops'):
                                            want_set = set()
                                            new_dict_to_set(each, [], want_set, 0)
                                            new_hops.append(want_set)
                                        new_dict_to_set(addr_have, [], have_set, 0)
                                        commands.extend(self._clear_config(w, h, addr_want, addr_have,
                                                                           route_want, route_have))
                                        commands.extend(self._set_config(w, h, addr_want,
                                                                         route_want, route_have, new_hops, have_set))
                                        del addr_want.get('routes')[count]
                                    count += 1
                                if check:
                                    break
                            if check:
                                break
                        if not check:
                            commands.extend(self._clear_config({}, h, {}, addr_have, {}, route_have))
        # For configuring any non-existing want config
        for w in temp_want:
            for addr_want in w.get('address_families'):
                for route_want in addr_want.get('routes'):
                    new_hops = []
                    for each in route_want.get('next_hops'):
                        want_set = set()
                        new_dict_to_set(each, [], want_set, 0)
                        new_hops.append(want_set)
                    commands.extend(self._set_config(w, {}, addr_want, route_want, {}, new_hops, set()))
        # Arranging the cmds suct that all delete cmds are fired before all set cmds
        commands = [each for each in sorted(commands) if 'no' in each] + \
                   [each for each in sorted(commands) if 'no' not in each]

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        # Drill each iteration of want n have and then based on dest and afi tyoe comparison take config call
        for w in want:
            for addr_want in w.get('address_families'):
                for route_want in addr_want.get('routes'):
                    check = False
                    for h in have:
                        if h.get('address_families'):
                            for addr_have in h.get('address_families'):
                                for route_have in addr_have.get('routes'):
                                    if route_want.get('dest') == route_have.get('dest')\
                                            and addr_want['afi'] == addr_have['afi']:
                                        check = True
                                        have_set = set()
                                        new_hops = []
                                        for each in route_want.get('next_hops'):
                                            want_set = set()
                                            new_dict_to_set(each, [], want_set, 0)
                                            new_hops.append(want_set)
                                        new_dict_to_set(addr_have, [], have_set, 0)
                                        commands.extend(self._set_config(w, h, addr_want,
                                                                         route_want, route_have, new_hops, have_set))
                                if check:
                                    break
                            if check:
                                break
                    if not check:
                        # For configuring any non-existing want config
                        new_hops = []
                        for each in route_want.get('next_hops'):
                            want_set = set()
                            new_dict_to_set(each, [], want_set, 0)
                            new_hops.append(want_set)
                        commands.extend(self._set_config(w, {}, addr_want, route_want, {}, new_hops, set()))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if want:
            # Drill each iteration of want n have and then based on dest and afi type comparison fire delete config call
            for w in want:
                if w.get('address_families'):
                    for addr_want in w.get('address_families'):
                        for route_want in addr_want.get('routes'):
                            check = False
                            for h in have:
                                if h.get('address_families'):
                                    for addr_have in h.get('address_families'):
                                        for route_have in addr_have.get('routes'):
                                            if route_want.get('dest') == route_have.get('dest') \
                                                    and addr_want['afi'] == addr_have['afi']:
                                                check = True
                                                if route_want.get('next_hops'):
                                                    commands.extend(self._clear_config({}, w, {}, addr_want, {}, route_want))
                                                else:
                                                    commands.extend(self._clear_config({}, h, {}, addr_have, {}, route_have))
                                        if check:
                                            break
                                    if check:
                                        break
                else:
                    for h in have:
                        for addr_have in h.get('address_families'):
                            for route_have in addr_have.get('routes'):
                                if w.get('vrf') == h.get('vrf'):
                                    commands.extend(self._clear_config({}, h, {}, addr_have, {}, route_have))
        else:
            # Drill each iteration of have and then based on dest and afi type comparison fire delete config call
            for h in have:
                for addr_have in h.get('address_families'):
                    for route_have in addr_have.get('routes'):
                        commands.extend(self._clear_config({}, h, {}, addr_have, {}, route_have))

        return commands

    def prepare_config_commands(self, config_dict, cmd):
        """
            function to parse the input dict and form the prepare the config commands
            :rtype: A str
            :returns: The command necessary to configure the static routes
        """

        dhcp = config_dict.get('dhcp')
        distance_metric = config_dict.get('distance_metric')
        forward_router_address = config_dict.get('forward_router_address')
        global_route_config = config_dict.get('global')
        interface = config_dict.get('interface')
        multicast = config_dict.get('multicast')
        name = config_dict.get('name')
        permanent = config_dict.get('permanent')
        tag = config_dict.get('tag')
        track = config_dict.get('track')
        dest = config_dict.get('dest')
        temp_dest = dest.split('/')
        if temp_dest and ':' not in dest:
            dest = validate_n_expand_ipv4(self._module, {'address': dest})

        cmd = cmd + dest
        if interface:
            cmd = cmd + ' {0}'.format(interface)
        if forward_router_address:
            cmd = cmd + ' {0}'.format(forward_router_address)
        if dhcp:
            cmd = cmd + ' DHCP'
        if distance_metric:
            cmd = cmd + ' {0}'.format(distance_metric)
        if global_route_config:
            cmd = cmd + ' global'
        if multicast:
            cmd = cmd + ' multicast'
        if name:
            cmd = cmd + ' name {0}'.format(name)
        if permanent:
            cmd = cmd + ' permanent'
        elif track:
            cmd = cmd + ' track {0}'.format(track)
        if tag:
            cmd = cmd + ' tag {0}'.format(tag)

        return cmd

    def _set_config(self, want, have, addr_want, route_want, route_have, hops, have_set):
        """
            Set the interface config based on the want and have config
            :rtype: A list
            :returns: The commands necessary to configure the static routes
        """

        commands = []
        cmd = None

        vrf_diff = False
        topology_diff = False
        want_vrf = want.get('vrf')
        have_vrf = have.get('vrf')
        if want_vrf != have_vrf:
            vrf_diff = True
        want_topology = want.get('topology')
        have_topology = have.get('topology')
        if want_topology != have_topology:
            topology_diff = True

        have_dest = route_have.get('dest')
        if have_dest:
            have_set.add(tuple(iteritems({'dest': have_dest})))

        # configure set cmd for each hops under the same destination
        for each in hops:
            diff = each - have_set
            if vrf_diff:
                each.add(tuple(iteritems({'vrf': want_vrf})))
            if topology_diff:
                each.add(tuple(iteritems({'topology': want_topology})))
            if diff or vrf_diff or topology_diff:
                if want_vrf and not vrf_diff:
                    each.add(tuple(iteritems({'vrf': want_vrf})))
                if want_topology and not vrf_diff:
                    each.add(tuple(iteritems({'topology': want_topology})))
                each.add(tuple(iteritems({'afi': addr_want.get('afi')})))
                each.add(tuple(iteritems({'dest': route_want.get('dest')})))
                temp_want = {}
                for each_want in each:
                    temp_want.update(dict(each_want))

                if temp_want.get('afi') == 'ipv4':
                    cmd = 'ip route '
                    vrf = temp_want.get('vrf')
                    if vrf:
                        cmd = cmd + 'vrf {0} '.format(vrf)
                    cmd = self.prepare_config_commands(temp_want, cmd)
                elif temp_want.get('afi') == 'ipv6':
                    cmd = 'ipv6 route '
                    cmd = self.prepare_config_commands(temp_want, cmd)
                commands.append(cmd)

        return commands

    def _clear_config(self, want, have, addr_want, addr_have, route_want, route_have):
        """
            Delete the interface config based on the want and have config
            :rtype: A list
            :returns: The commands necessary to configure the static routes
        """

        commands = []
        cmd = None

        vrf_diff = False
        topology_diff = False
        want_vrf = want.get('vrf')
        have_vrf = have.get('vrf')
        if want_vrf != have_vrf:
            vrf_diff = True
        want_topology = want.get('topology')
        have_topology = have.get('topology')
        if want_topology != have_topology:
            topology_diff = True

        want_set = set()
        new_dict_to_set(addr_want, [], want_set, 0)

        have_hops = []
        for each in route_have.get('next_hops'):
            temp_have_set = set()
            new_dict_to_set(each, [], temp_have_set, 0)
            have_hops.append(temp_have_set)

        # configure delete cmd for each hops under the same destination
        for each in have_hops:
            diff = each - want_set
            if vrf_diff:
                each.add(tuple(iteritems({'vrf': have_vrf})))
            if topology_diff:
                each.add(tuple(iteritems({'topology': want_topology})))
            if diff or vrf_diff or topology_diff:
                if want_vrf and not vrf_diff:
                    each.add(tuple(iteritems({'vrf': want_vrf})))
                if want_topology and not vrf_diff:
                    each.add(tuple(iteritems({'topology': want_topology})))
                if addr_want:
                    each.add(tuple(iteritems({'afi': addr_want.get('afi')})))
                else:
                    each.add(tuple(iteritems({'afi': addr_have.get('afi')})))
                if route_want:
                    each.add(tuple(iteritems({'dest': route_want.get('dest')})))
                else:
                    each.add(tuple(iteritems({'dest': route_have.get('dest')})))
                temp_want = {}
                for each_want in each:
                    temp_want.update(dict(each_want))

                if temp_want.get('afi') == 'ipv4':
                    cmd = 'no ip route '
                    vrf = temp_want.get('vrf')
                    if vrf:
                        cmd = cmd + 'vrf {0} '.format(vrf)
                    cmd = self.prepare_config_commands(temp_want, cmd)
                elif temp_want.get('afi') == 'ipv6':
                    cmd = 'no ipv6 route '
                    cmd = self.prepare_config_commands(temp_want, cmd)
                commands.append(cmd)

        return commands
