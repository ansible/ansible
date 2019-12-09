#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_static_routes class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties, dict_diff
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import flatten_dict, search_obj_in_list, get_interface_type, normalize_interface


class Static_routes(ConfigBase):
    """
    The nxos_static_routes class
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
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data=data)
        static_routes_facts = facts['ansible_network_resources'].get(
            'static_routes')
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
        state = self._module.params['state']
        existing_static_routes_facts = self.get_static_routes_facts()
        action_states = ['merged', 'replaced', 'deleted', 'overridden']
        result['before'] = existing_static_routes_facts
        if state == 'gathered':
            result['gathered'] = result['before']
        else:
            commands.extend(self.set_config(existing_static_routes_facts))
            if commands and state in action_states:
                if not self._module.check_mode:
                    self._connection.edit_config(commands)
                result['changed'] = True
                result['commands'] = commands
            if state == 'rendered':
                result['rendered'] = commands
            elif state == 'parsed':
                result['parsed'] = commands
            changed_static_routes_facts = self.get_static_routes_facts()
            if result['changed']:
                result['after'] = changed_static_routes_facts

        if state not in action_states:
            del result['before']
        result['warnings'] = warnings
        return result

    def set_config(self, existing_static_routes_facts):
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
                want.append(remove_empties(w))
        have = existing_static_routes_facts
        want = self.add_default_vrf(deepcopy(want))
        have = self.add_default_vrf(deepcopy(have))
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
        commands = []
        if state == 'overridden':
            commands = (self._state_overridden(want, have))
        elif state == 'deleted':
            commands = (self._state_deleted(want, have))
        elif state == 'rendered':
            commands = self._state_rendered(want, have=[])
        elif state == 'parsed':
            want = self._module.params['running_config']
            commands = self._state_parsed(want)
        else:
            for w in want:
                if state == 'merged':
                    commands.extend(self._state_merged(w, have))
                elif state == 'replaced':
                    commands.extend(self._state_replaced(w, have))
        return commands

    def _state_parsed(self, want):
        return self.get_static_routes_facts(want)

    def _state_rendered(self, want, have):
        commands = []
        for w in want:
            commands.extend(self.set_commands(w, {}))
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        delete_commands = []
        merged_commands = []
        obj_in_have = search_obj_in_list(want['vrf'], have, 'vrf')
        # in replaced, we check if whatever in have is in want, unlike merged. This is because we need to apply deleted on have config
        if obj_in_have and obj_in_have != {'vrf': 'default'}:
            want_afi_list = [w['afi'] for w in want['address_families']]
            for h in obj_in_have['address_families']:
                if h['afi'] in want_afi_list:
                    want_afi = search_obj_in_list(
                        h['afi'], want['address_families'], 'afi')
                    want_dest_list = [w['dest'] for w in want_afi['routes']]
                    for ro in h['routes']:
                        if ro['dest'] in want_dest_list:
                            want_dest = search_obj_in_list(
                                ro['dest'], want_afi['routes'], 'dest')
                            want_next_hops = [
                                nh for nh in want_dest['next_hops']]
                            for next_hop in ro['next_hops']:
                                if next_hop not in want_next_hops:
                                    # have's next hop not in want, so delete it
                                    delete_dict = {'vrf': obj_in_have['vrf'], 'address_families': [
                                        {'afi': h['afi'], 'routes':[{'dest': ro['dest'], 'next_hops':[next_hop]
                                                                     }]
                                         }
                                    ]
                                    }
                                    delete_commands.extend(
                                        self.del_commands([delete_dict]))
                        else:
                            # have's dest not in want, so delete ro['dest']
                            delete_dict = {'vrf': obj_in_have['vrf'], 'address_families': [
                                {'afi': h['afi'], 'routes':[ro]}]}
                            delete_commands.extend(
                                self.del_commands([delete_dict]))
                else:
                    # have's afi not in want, so delete h['afi']
                    delete_commands.extend(self.del_commands(
                        [{'address_families': [h], 'vrf': obj_in_have['vrf']}]))
        final_delete_commands = []
        for d in delete_commands:
            if d not in final_delete_commands:
                final_delete_commands.append(d)
        # if there are two afis, 'vrf context..' is added twice fom del_commands. The above code removes the redundant 'vrf context ..'
        merged_commands = (self.set_commands(want, have))
        if merged_commands:
            cmds = set(final_delete_commands).intersection(
                set(merged_commands))
            for c in cmds:
                merged_commands.remove(c)

        # set_commands adds a 'vrf context..' line.  The above code removes the redundant 'vrf context ..'
        commands.extend(final_delete_commands)
        commands.extend(merged_commands)
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_vrfs = [w['vrf'] for w in want]
        for h in have:
            if h['vrf'] not in want_vrfs:
                commands.extend(self._state_deleted([h], have))
        for w in want:
            commands.extend(self._state_replaced(w, have))
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
                delete_dict = {}
                obj_in_have = search_obj_in_list(w['vrf'], have, 'vrf')
                if obj_in_have:
                    if 'address_families' in w.keys():
                        o1 = obj_in_have['address_families']
                        afi_list = [o['afi'] for o in o1]
                        for w1 in w['address_families']:
                            if w1['afi'] in afi_list:
                                o2 = search_obj_in_list(
                                    w1['afi'], o1, 'afi')
                                if 'routes' in w1.keys():
                                    for w2 in w1['routes']:
                                        o3 = search_obj_in_list(
                                            w2['dest'], o2['routes'], 'dest')
                                        if o3:
                                            delete_dict = {'vrf': obj_in_have['vrf'], 'address_families': [
                                                {'afi': w1['afi'], 'routes':[{'dest': w2['dest'], 'next_hops':o3['next_hops']}]}]}
                                            commands.extend(
                                                self.del_commands([delete_dict]))
                                        # else, dest's route does not exist in device, ignore
                                else:
                                    # case when only afi given for delete
                                    delete_dict = {'vrf': obj_in_have['vrf'], 'address_families': [
                                        {'afi': o2['afi'], 'routes':o2['routes']}]}
                                    commands.extend(
                                        self.del_commands([delete_dict]))
                    else:
                        commands.extend(self.del_commands([obj_in_have]))
        else:
            if have:
                commands = self.del_commands(have)

        final_delete_commands = []
        # del_commands might add 'vrf context..' twice for two routes in the same vrf. This removes it
        for c in commands:
            if c not in final_delete_commands:
                final_delete_commands.append(c)
        return final_delete_commands

    def del_commands(self, have):
        commands = []
        for h in have:
            if h != {'vrf': 'default'}:
                vrf = h['vrf']
                commands.append('vrf context ' + vrf)
                for af in h['address_families']:
                    for route in af['routes']:
                        for next_hop in route['next_hops']:
                            command = self.del_next_hop(af, route, next_hop)
                            commands.append(command.strip())
        return commands

    def del_next_hop(self, af, route, next_hop):
        command = ''
        if af['afi'] == 'ipv4':
            command = 'no ip route ' + \
                route['dest'] + ' ' + self.add_commands(next_hop)
        else:
            command = 'no ipv6 route ' + \
                route['dest'] + ' ' + self.add_commands(next_hop)
        return command

    def add_commands(self, want):
        command = ''
        params = want.keys()
        pref = vrf = ip = intf = name = tag = track = ''
        if 'admin_distance' in params:
            pref = str(want['admin_distance']) + ' '
        if 'track' in params:
            track = 'track ' + str(want['track'])+' '
        if 'dest_vrf' in params:
            vrf = 'vrf '+str(want['dest_vrf']) + ' '
        if 'forward_router_address' in params:
            ip = want['forward_router_address']+' '
        if 'interface' in params:
            intf = normalize_interface(want['interface'])+' '
        if 'route_name' in params:
            name = 'name ' + str(want['route_name'])+' '
        if 'tag' in params:
            tag = 'tag '+str(want['tag'])+' '
        command = intf+ip+vrf+name+tag+track+pref
        return command

    def set_commands(self, want, have):
        commands = []
        h1 = h2 = h3 = {}
        want = remove_empties(want)
        vrf_list = []
        if have:
            vrf_list = [h['vrf'] for h in have]
        if want['vrf'] in vrf_list and have != [{'vrf': 'default'}]:
            for x in have:
                if x['vrf'] == want['vrf']:
                    h1 = x  # this has the 'have' dict with same vrf as want
            if 'address_families' in h1.keys():
                afi_list = [h['afi'] for h in h1['address_families']]
                for af in want['address_families']:
                    if af['afi'] in afi_list:
                        for x in h1['address_families']:
                            if x['afi'] == af['afi']:
                                h2 = x  # this has the have dict with same vrf and afi as want
                        dest_list = [h['dest'] for h in h2['routes']]
                        for ro in af['routes']:
                            if ro['dest'] in dest_list:
                                for x in h2['routes']:
                                    if x['dest'] == ro['dest']:
                                        h3 = x  # this has the have dict with same vrf, afi and dest as want
                                next_hop_list = [h for h in h3['next_hops']]
                                for nh in ro['next_hops']:
                                    if 'interface' in nh.keys():
                                        nh['interface'] = normalize_interface(
                                            nh['interface'])
                                    if nh not in next_hop_list:
                                        # no match for next hop in have
                                        commands = self.set_next_hop(
                                            want, h2, nh, ro, commands)
                                        vrf_list.append(want['vrf'])
                            else:
                                # no match for dest
                                for nh in ro['next_hops']:
                                    commands = self.set_next_hop(
                                        want, h2, nh, ro, commands)
                    else:
                        # no match for afi
                        for ro in af['routes']:
                            for nh in ro['next_hops']:
                                commands = self.set_next_hop(
                                    want, af, nh, ro, commands)
        else:
            # no match for vrf
            vrf_list.append(want['vrf'])
            for af in want['address_families']:
                for ro in af['routes']:
                    for nh in ro['next_hops']:
                        commands = self.set_next_hop(
                            want, af, nh, ro, commands)
        return commands

    def set_next_hop(self, want, h2, nh, ro, commands):
        vrf = want['vrf']
        if h2['afi'] == 'ipv4':
            com = 'ip route ' + \
                ro['dest'] + ' ' + \
                self.add_commands(nh)
        else:
            com = 'ipv6 route ' + \
                ro['dest'] + ' ' + \
                self.add_commands(nh)
        commands.append(com.strip())
        string = 'vrf context ' + \
            str(vrf)
        if string not in commands:
            commands.insert(0, string)
        return commands

    def add_default_vrf(self, dictionary):
        '''
        This method is used to add 'default' vrf to the facts collected as global/default vrf 
        is not shown in facts. vrf key exists for all vrfs except global. 
        '''
        for d in dictionary:
            if 'vrf' not in d.keys():
                d.update({'vrf': 'default'})
        return dictionary
