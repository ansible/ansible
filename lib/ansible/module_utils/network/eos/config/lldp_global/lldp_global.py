#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_lldp_global class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import dict_diff, to_list
from ansible.module_utils.network.eos.facts.facts import Facts


class Lldp_global(ConfigBase):
    """
    The eos_lldp_global class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_global',
    ]

    def __init__(self, module):
        super(Lldp_global, self).__init__(module)

    def get_lldp_global_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lldp_global_facts = facts['ansible_network_resources'].get('lldp_global')
        if not lldp_global_facts:
            return {}
        return lldp_global_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_lldp_global_facts = self.get_lldp_global_facts()
        commands.extend(self.set_config(existing_lldp_global_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lldp_global_facts = self.get_lldp_global_facts()

        result['before'] = existing_lldp_global_facts
        if result['changed']:
            result['after'] = changed_lldp_global_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lldp_global_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config'] or {}
        have = existing_lldp_global_facts
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
        if state == 'deleted':
            commands = state_deleted(want, have)
        elif state == 'merged':
            commands = state_merged(want, have)
        elif state == 'replaced':
            commands = state_replaced(want, have)
        return commands


def state_replaced(want, have):
    """ The command generator when state is replaced

    :rtype: A list
    :returns: the commands necessary to migrate the current configuration
              to the desired configuration
    """
    commands = set()
    # merged and deleted are likely to emit duplicate tlv-select commands
    commands.update(state_merged(want, have))
    commands.update(state_deleted(want, have))

    return list(commands)


def state_merged(want, have):
    """ The command generator when state is merged

    :rtype: A list
    :returns: the commands necessary to merge the provided into
              the current configuration
    """
    commands = []
    to_set = dict_diff(have, want)
    tlv_options = to_set.pop("tlv_select", {})
    for key, value in to_set.items():
        commands.append("lldp {0} {1}".format(key, value))
    for key, value in tlv_options.items():
        device_option = key.replace("_", "-")
        if value is True:
            commands.append("lldp tlv-select {0}".format(device_option))
        elif value is False:
            commands.append("no lldp tlv-select {0}".format(device_option))

    return commands


def state_deleted(want, have):
    """ The command generator when state is deleted

    :rtype: A list
    :returns: the commands necessary to remove the current configuration
              of the provided objects
    """
    commands = []
    to_remove = dict_diff(want, have)
    tlv_options = to_remove.pop("tlv_select", {})
    for key in to_remove:
        commands.append("no lldp {0}".format(key))
    for key, value in tlv_options.items():
        device_option = key.replace("_", "-")
        if value is False:
            commands.append("lldp tlv-select {0}".format(device_option))
        elif value is True:
            commands.append("no lldp tlv-select {0}".format(device_option))

    return commands
