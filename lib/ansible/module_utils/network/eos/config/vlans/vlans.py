# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_vlans class
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


class Vlans(ConfigBase):
    """
    The eos_vlans class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'vlans',
    ]

    def get_vlans_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        vlans_facts = facts['ansible_network_resources'].get('vlans')
        if not vlans_facts:
            return []
        return vlans_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_vlans_facts = self.get_vlans_facts()
        commands.extend(self.set_config(existing_vlans_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_vlans_facts = self.get_vlans_facts()

        result['before'] = existing_vlans_facts
        if result['changed']:
            result['after'] = changed_vlans_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_vlans_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_vlans_facts
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
        want = param_list_to_dict(want, "vlan_id", remove_key=False)
        have = param_list_to_dict(have, "vlan_id", remove_key=False)
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
        for vlan_id, desired in want.items():
            if vlan_id in have:
                extant = have[vlan_id]
            else:
                extant = dict()

            add_config = dict_diff(extant, desired)
            del_config = dict_diff(desired, extant)

            commands.extend(generate_commands(vlan_id, add_config, del_config))

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for vlan_id, extant in have.items():
            if vlan_id in want:
                desired = want[vlan_id]
            else:
                desired = dict()

            add_config = dict_diff(extant, desired)
            del_config = dict_diff(desired, extant)

            commands.extend(generate_commands(vlan_id, add_config, del_config))

        # Handle vlans not already in config
        new_vlans = [vlan_id for vlan_id in want if vlan_id not in have]
        for vlan_id in new_vlans:
            desired = want[vlan_id]
            extant = dict(vlan_id=vlan_id)
            add_config = dict_diff(extant, desired)

            commands.extend(generate_commands(vlan_id, add_config, {}))

        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for vlan_id, desired in want.items():
            if vlan_id in have:
                extant = have[vlan_id]
            else:
                extant = dict()

            add_config = dict_diff(extant, desired)

            commands.extend(generate_commands(vlan_id, add_config, {}))

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for vlan_id in want:
            desired = dict()
            if vlan_id in have:
                extant = have[vlan_id]
            else:
                continue

            del_config = dict_diff(desired, extant)

            commands.extend(generate_commands(vlan_id, {}, del_config))

        return commands


def generate_commands(vlan_id, to_set, to_remove):
    commands = []
    if "vlan_id" in to_remove:
        return ["no vlan {0}".format(vlan_id)]

    for key in to_remove:
        if key in to_set.keys():
            continue
        commands.append("no {0}".format(key))

    for key, value in to_set.items():
        if key == "vlan_id" or value is None:
            continue

        commands.append("{0} {1}".format(key, value))

    if commands:
        commands.insert(0, "vlan {0}".format(vlan_id))
    return commands
