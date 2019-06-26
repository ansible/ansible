#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_tms_global class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from ansible.module_utils.network.common.utils import to_list

from ansible.module_utils.network.nxos.argspec.tms_global.tms_global import Tms_globalArgs
from ansible.module_utils.network.nxos.config.base import ConfigBase
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.cmdref.tms_global import TMS_CMD_REF
from ansible.module_utils.network.nxos.nxos import NxosCmdRef, normalize_interface


class Tms_global(ConfigBase, Tms_globalArgs):
    """
    The nxos_tms_global class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'tms_global',
    ]

    def get_tms_global_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts().get_facts(self._module,
                                             self._connection,
                                             self.gather_subset,
                                             self.gather_network_resources)
        tms_global_facts = facts['ansible_network_resources'].get('tms_global')
        if not tms_global_facts:
            return []
        return tms_global_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_tms_global_facts = self.get_tms_global_facts()
        commands.extend(self.set_config(existing_tms_global_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_tms_global_facts = self.get_tms_global_facts()

        result['before'] = existing_tms_global_facts
        if result['changed']:
            result['after'] = changed_tms_global_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_tms_global_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_tms_global_facts
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
        # Compare want and have states first.  If equal then return.
        state = self._module.params['state']
        cmd_ref = NxosCmdRef(self._module, TMS_CMD_REF)
        cmd_ref.set_context()
        cmd_ref.get_existing()
        cmd_ref.get_playvals()
        if state == 'overridden':
            if want[0] == have:
                return []
            kwargs = {}
            self._state_deleted(cmd_ref, **kwargs)
            commands = self._state_merged(cmd_ref, **kwargs)
        elif state == 'deleted':
            kwargs = {}
            commands = self._state_deleted(cmd_ref, **kwargs)
        elif state == 'merged':
            if want[0] == have:
                return []
            kwargs = {}
            commands = self._state_merged(cmd_ref, **kwargs)
        elif state == 'replaced':
            if want[0] == have:
                return []
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
    def _state_merged(cmd_ref, **kwargs):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = cmd_ref.get_proposed()
        return commands

    @staticmethod
    def _state_deleted(cmd_ref, **kwargs):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = cmd_ref.get_proposed()
        return commands
