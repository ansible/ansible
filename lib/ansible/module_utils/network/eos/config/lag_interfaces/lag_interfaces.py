# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.common.utils import to_list, dict_diff

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.eos.facts.facts import Facts
from ansible.module_utils.network.eos.utils.utils import normalize_interface


class Lag_interfaces(ConfigBase):
    """
    The eos_lag_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lag_interfaces',
    ]

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
                self._connection.edit_config(commands)
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
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
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
        for interface in want:
            interface_name = normalize_interface(interface["name"])
            for extant in have:
                if extant["name"] == interface_name:
                    break
            else:
                extant = dict(name=interface_name)

            commands.extend(set_config(interface, extant))
            commands.extend(remove_config(interface, extant))

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for extant in have:
            for interface in want:
                if normalize_interface(interface["name"]) == extant["name"]:
                    break
            else:
                interface = dict(name=extant["name"])
            commands.extend(remove_config(interface, extant))

        for interface in want:
            interface_name = normalize_interface(interface["name"])
            for extant in have:
                if extant["name"] == interface_name:
                    break
            else:
                extant = dict(name=interface_name)
            commands.extend(set_config(interface, extant))

        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for interface in want:
            interface_name = normalize_interface(interface["name"])
            for extant in have:
                if extant["name"] == interface_name:
                    break
            else:
                extant = dict(name=interface_name)

            commands.extend(set_config(interface, extant))

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for interface in want:
            interface_name = normalize_interface(interface["name"])
            for extant in have:
                if extant["name"] == interface_name:
                    break
            else:
                extant = dict(name=interface_name)

            # Clearing all args, send empty dictionary
            interface = dict(name=interface_name)
            commands.extend(remove_config(interface, extant))

        return commands


def set_config(want, have):
    commands = []
    to_set = dict_diff(have, want)
    for member in to_set.get("members", []):
        channel_id = want["name"][12:]
        commands.extend([
            "interface {0}".format(member["member"]),
            "channel-group {0} mode {1}".format(channel_id, member["mode"]),
        ])

    return commands


def remove_config(want, have):
    commands = []
    if not want.get("members"):
        return ["no interface {0}".format(want["name"])]

    to_remove = dict_diff(want, have)
    for member in to_remove.get("members", []):
        commands.extend([
            "interface {0}".format(member["member"]),
            "no channel-group",
        ])

    return commands
