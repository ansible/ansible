# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_lldp_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff, param_list_to_dict
from ansible.module_utils.network.eos.facts.facts import Facts
from ansible.module_utils.network.eos.utils.utils import normalize_interface


class Lldp_interfaces(ConfigBase):
    """
    The eos_lldp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_interfaces',
    ]

    def get_lldp_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lldp_interfaces_facts = facts['ansible_network_resources'].get('lldp_interfaces')
        if not lldp_interfaces_facts:
            return []
        return lldp_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_lldp_interfaces_facts = self.get_lldp_interfaces_facts()
        commands.extend(self.set_config(existing_lldp_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lldp_interfaces_facts = self.get_lldp_interfaces_facts()

        result['before'] = existing_lldp_interfaces_facts
        if result['changed']:
            result['after'] = changed_lldp_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lldp_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lldp_interfaces_facts
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
        want = param_list_to_dict(want, remove_key=False)
        have = param_list_to_dict(have, remove_key=False)
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
        for key, desired in want.items():
            interface_name = normalize_interface(key)
            if interface_name in have:
                extant = have[interface_name]
            else:
                extant = dict(name=interface_name)

            add_config = dict_diff(extant, desired)
            del_config = dict_diff(desired, extant)

            commands.extend(generate_commands(interface_name, add_config, del_config))

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for key, extant in have.items():
            if key in want:
                desired = want[key]
            else:
                desired = dict(name=key)

            add_config = dict_diff(extant, desired)
            del_config = dict_diff(desired, extant)

            commands.extend(generate_commands(key, add_config, del_config))

        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for key, desired in want.items():
            interface_name = normalize_interface(key)
            if interface_name in have:
                extant = have[interface_name]
            else:
                extant = dict(name=interface_name)

            add_config = dict_diff(extant, desired)

            commands.extend(generate_commands(interface_name, add_config, {}))

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for key in want.keys():
            interface_name = normalize_interface(key)
            desired = dict(name=interface_name)
            if interface_name in have:
                extant = have[interface_name]
            else:
                continue

            del_config = dict_diff(desired, extant)

            commands.extend(generate_commands(interface_name, {}, del_config))

        return commands


def generate_commands(name, to_set, to_remove):
    commands = []
    for key, value in to_set.items():
        if value is None:
            continue

        prefix = "" if value else "no "
        commands.append("{0}lldp {1}".format(prefix, key))

    for key in to_remove:
        commands.append("lldp {0}".format(key))

    if commands:
        commands.insert(0, "interface {0}".format(name))

    return commands
