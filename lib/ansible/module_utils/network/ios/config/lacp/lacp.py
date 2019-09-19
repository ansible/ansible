#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_lacp class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts
from ansible.module_utils.network.ios.utils.utils import dict_to_set


class Lacp(ConfigBase):
    """
    The ios_lacp class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lacp',
    ]

    def __init__(self, module):
        super(Lacp, self).__init__(module)

    def get_lacp_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lacp_facts = facts['ansible_network_resources'].get('lacp')
        if not lacp_facts:
            return []

        return lacp_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_lacp_facts = self.get_lacp_facts()
        commands.extend(self.set_config(existing_lacp_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lacp_facts = self.get_lacp_facts()

        result['before'] = existing_lacp_facts
        if result['changed']:
            result['after'] = changed_lacp_facts
        result['warnings'] = warnings

        return result

    def set_config(self, existing_lacp_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lacp_facts
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
        if state in ('merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
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

        commands.extend(self._set_config(want, have))

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        commands.extend(self._set_config(want, have))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if want:
            commands.extend(self._clear_config(have))
        else:
            commands.extend(self._clear_config(have))

        return commands

    def _remove_command_from_config_list(self, cmd, commands):
        commands.append('no %s' % cmd)
        return commands

    def _add_command_to_config_list(self, cmd, commands):
        if cmd not in commands:
            commands.append(cmd)

    def _set_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []

        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)
        diff = want_dict - have_dict

        if diff:
            cmd = 'lacp system-priority {0}'.format(want.get('system').get('priority'))
            self._add_command_to_config_list(cmd, commands)

        return commands

    def _clear_config(self, have):
        # Delete the interface config based on the want and have config
        commands = []

        if have.get('system').get('priority') and have.get('system').get('priority') != 32768:
            cmd = 'lacp system-priority'
            self._remove_command_from_config_list(cmd, commands)

        return commands
