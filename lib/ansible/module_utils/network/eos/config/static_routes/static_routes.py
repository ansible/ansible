#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_static_routes class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import remove_empties
from ansible.module_utils.network.eos.facts.facts import Facts


class Static_routes(ConfigBase):
    """
    The eos_static_routes class
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
                for command in commands:
                    self._connection.edit_config(command)
            result['changed'] = True
        if self.state in self.ACTION_STATES:
            result['commands'] = commands
        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_static_routes_facts = self.get_static_routes_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            if not self._module.params['running_config']:
                self._module.fail_json(msg="Value of running_config parameter must not be empty for state parsed")
            result['parsed'] = self.get_static_routes_facts(data=self._module.params['running_config'])
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
        commands = []
        onbox_configs = []
        for h in existing_static_routes_facts:
            return_command = add_commands(h)
            for command in return_command:
                onbox_configs.append(command)
        config = self._module.params.get('config')
        want = []
        if config:
            for w in config:
                want.append(remove_empties(w))
        have = existing_static_routes_facts
        resp = self.set_state(want, have)
        for want_config in resp:
            if want_config not in onbox_configs:
                commands.append(want_config)
        return commands

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if self.state in ('merged', 'replaced', 'overridden') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(self.state))
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged' or self.state == 'rendered':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        haveconfigs = []
        vrf = get_vrf(want)
        dest = get_dest(want)
        for h in have:
            return_command = add_commands(h)
            for command in return_command:
                for d in dest:
                    if d in command:
                        if vrf is None:
                            if "vrf" not in command:
                                haveconfigs.append(command)
                        else:
                            if vrf in command:
                                haveconfigs.append(command)
        wantconfigs = set_commands(want, have)

        removeconfigs = list(set(haveconfigs) - set(wantconfigs))
        for command in removeconfigs:
            commands.append("no " + command)
        for wantcmd in wantconfigs:
            commands.append(wantcmd)
        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        haveconfigs = []
        for h in have:
            return_command = add_commands(h)
            for command in return_command:
                haveconfigs.append(command)
        wantconfigs = set_commands(want, have)
        idempotentconfigs = list(set(haveconfigs) - set(wantconfigs))
        if not idempotentconfigs:
            return idempotentconfigs
        removeconfigs = list(set(haveconfigs) - set(wantconfigs))
        for command in removeconfigs:
            commands.append("no " + command)
        for wantcmd in wantconfigs:
            commands.append(wantcmd)
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return set_commands(want, have)

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if not want:
            for h in have:
                return_command = add_commands(h)
                for command in return_command:
                    command = "no " + command
                    commands.append(command)
        else:
            for w in want:
                return_command = del_commands(w, have)
                for command in return_command:
                    commands.append(command)
        return commands


def set_commands(want, have):
    commands = []
    for w in want:
        return_command = add_commands(w)
        for command in return_command:
            commands.append(command)
    return commands


def add_commands(want):
    commandset = []
    if not want:
        return commandset
    vrf = want["vrf"] if "vrf" in want.keys() and want["vrf"] is not None else None
    for address_family in want["address_families"]:
        for route in address_family["routes"]:
            for next_hop in route["next_hops"]:
                commands = []
                if address_family["afi"] == "ipv4":
                    commands.append('ip route')
                else:
                    commands.append('ipv6 route')
                if vrf:
                    commands.append(' vrf ' + vrf)
                if not re.search(r'/', route["dest"]):
                    mask = route["dest"].split()[1]
                    cidr = get_net_size(mask)
                    commands.append(' ' + route["dest"].split()[0] + '/' + cidr)
                else:
                    commands.append(' ' + route["dest"])
                if "interface" in next_hop.keys():
                    commands.append(' ' + next_hop["interface"])
                if "nexthop_grp" in next_hop.keys():
                    commands.append(' Nexthop-Group' + ' ' + next_hop["nexthop_grp"])
                if "forward_router_address" in next_hop.keys():
                    commands.append(' ' + next_hop["forward_router_address"])
                if "mpls_label" in next_hop.keys():
                    commands.append(' label ' + str(next_hop["mpls_label"]))
                if "track" in next_hop.keys():
                    commands.append(' track ' + next_hop["track"])
                if "admin_distance" in next_hop.keys():
                    commands.append(' ' + str(next_hop["admin_distance"]))
                if "description" in next_hop.keys():
                    commands.append(' name ' + str(next_hop["description"]))
                if "tag" in next_hop.keys():
                    commands.append(' tag ' + str(next_hop["tag"]))

                config_commands = "".join(commands)
                commandset.append(config_commands)
    return commandset


def del_commands(want, have):
    commandset = []
    haveconfigs = []
    for h in have:
        return_command = add_commands(h)
        for command in return_command:
            command = "no " + command
            haveconfigs.append(command)
    if want is None or "address_families" not in want.keys():
        commandset = haveconfigs
    if "address_families" not in want.keys() and "vrf" in want.keys():
        commandset = []
        for command in haveconfigs:
            if want["vrf"] in command:
                commandset.append(command)
    elif want is not None and "vrf" not in want.keys() and "address_families" not in want.keys():
        commandset = []
        for command in haveconfigs:
            if "vrf" not in command:
                commandset.append(command)

    elif want["address_families"]:
        vrf = want["vrf"] if "vrf" in want.keys() and want["vrf"] else None
        for address_family in want["address_families"]:
            if "routes" not in address_family.keys():
                for command in haveconfigs:
                    afi = "ip " if address_family["afi"] == "ipv4" else "ipv6"
                    if afi in command:
                        if vrf:
                            if vrf in command:
                                commandset.append(command)
                        else:
                            commandset.append(command)
            else:
                for route in address_family["routes"]:
                    if not re.search(r'/', route["dest"]):
                        mask = route["dest"].split()[1]
                        cidr = get_net_size(mask)
                        destination = route["dest"].split()[0] + '/' + cidr
                    else:
                        destination = route["dest"]
                    if "next_hops" not in route.keys():
                        for command in haveconfigs:
                            if destination in command:
                                if vrf:
                                    if vrf in command:
                                        commandset.append(command)
                                else:
                                    commandset.append(command)
                    else:
                        for next_hop in route["next_hops"]:
                            commands = []
                            if address_family["afi"] == "ipv4":
                                commands.append('no ip route')
                            else:
                                commands.append('no ipv6 route')
                            if vrf:
                                commands.append(' vrf ' + vrf)
                            commands.append(' ' + destination)
                            if "interface" in next_hop.keys():
                                commands.append(' ' + next_hop["interface"])
                            if "nexhop_grp" in next_hop.keys():
                                commands.append(' Nexthop-Group' + ' ' + next_hop["nexthop_grp"])
                            if "forward_router_address" in next_hop.keys():
                                commands.append(' ' + next_hop["forward_router_address"])
                            if "mpls_label" in next_hop.keys():
                                commands.append(' label ' + str(next_hop["mpls_label"]))
                            if "track" in next_hop.keys():
                                commands.append(' track ' + next_hop["track"])
                            if "admin_distance" in next_hop.keys():
                                commands.append(' ' + str(next_hop["admin_distance"]))
                            if "description" in next_hop.keys():
                                commands.append(' name ' + str(next_hop["description"]))
                            if "tag" in next_hop.keys():
                                commands.append(' tag ' + str(next_hop["tag"]))

                            config_commands = "".join(commands)
                            commandset.append(config_commands)
    return commandset


def get_net_size(netmask):
    binary_str = ''
    netmask = netmask.split('.')
    for octet in netmask:
        binary_str += bin(int(octet))[2:].zfill(8)
    return str(len(binary_str.rstrip('0')))


def get_vrf(config):
    vrf = ""
    for c in config:
        vrf = c["vrf"] if "vrf" in c.keys() and c["vrf"] else None
    return vrf


def get_dest(config):
    dest = []
    for c in config:
        for address_family in c["address_families"]:
            for route in address_family["routes"]:
                dest.append(route['dest'])
    return dest
