#
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
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.eos.facts.facts import Facts


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

    def __init__(self, module):
        super(Lldp_interfaces, self).__init__(module)

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
        if state == 'overridden':
            kwargs = {}
            commands = self._state_overridden(**kwargs)
        elif state == 'deleted':
            kwargs = {}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {}
            commands = self._state_merged(**kwargs)
        elif state == 'replaced':
            kwargs = {}
            commands = self._state_replaced(**kwargs)
        return commands
    @staticmethod
    def _state_replaced(**kwargs):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    @staticmethod
    def _state_overridden(**kwargs):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    @staticmethod
    def _state_merged(**kwargs):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        return commands

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        return commands
