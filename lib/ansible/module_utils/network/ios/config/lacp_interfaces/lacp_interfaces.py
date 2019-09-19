#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_lacp_interfaces class
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
from ansible.module_utils.network.ios.utils.utils import remove_command_from_config_list, add_command_to_config_list
from ansible.module_utils.network.ios.utils.utils import filter_dict_having_none_value, remove_duplicate_interface


class Lacp_Interfaces(ConfigBase):
    """
    The ios_lacp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lacp_interfaces',
    ]

    def __init__(self, module):
        super(Lacp_Interfaces, self).__init__(module)

    def get_lacp_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lacp_interfaces_facts = facts['ansible_network_resources'].get('lacp_interfaces')

        if not lacp_interfaces_facts:
            return []
        return lacp_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_lacp_interfaces_facts = self.get_lacp_interfaces_facts()
        commands.extend(self.set_config(existing_lacp_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lacp_interfaces_facts = self.get_lacp_interfaces_facts()

        result['before'] = existing_lacp_interfaces_facts
        if result['changed']:
            result['after'] = changed_lacp_interfaces_facts

        result['warnings'] = warnings

        return result

    def set_config(self, existing_lacp_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lacp_interfaces_facts
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
        commands = []

        state = self._module.params['state']
        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
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

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            commands.extend(self._clear_config(dict(), have_dict))
            commands.extend(self._set_config(interface, each))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for each in have:
            for interface in want:
                if each['name'] == interface['name']:
                    break
            else:
                # We didn't find a matching desired state, which means we can
                # pretend we recieved an empty desired state.
                interface = dict(name=each['name'])
                commands.extend(self._clear_config(interface, each))
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            commands.extend(self._clear_config(dict(), have_dict))
            commands.extend(self._set_config(interface, each))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        for interface in want:
            for each in have:
                if interface['name'] == each['name']:
                    break
            else:
                continue
            commands.extend(self._set_config(interface, each))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if want:
            for interface in want:
                for each in have:
                    if each['name'] == interface['name']:
                        break
                else:
                    continue
                interface = dict(name=interface['name'])
                commands.extend(self._clear_config(interface, each))
        else:
            for each in have:
                commands.extend(self._clear_config(dict(), each))

        return commands

    def _set_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []
        interface = 'interface ' + have['name']

        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)
        diff = want_dict - have_dict

        if diff:
            port_priotity = dict(diff).get('port_priority')
            max_bundle = dict(diff).get('max_bundle')
            fast_switchover = dict(diff).get('fast_switchover')
            if port_priotity:
                cmd = 'lacp port-priority {0}'.format(port_priotity)
                add_command_to_config_list(interface, cmd, commands)
            if max_bundle:
                cmd = 'lacp max-bundle {0}'.format(max_bundle)
                add_command_to_config_list(interface, cmd, commands)
            if fast_switchover:
                cmd = 'lacp fast-switchover'
                add_command_to_config_list(interface, cmd, commands)

        return commands

    def _clear_config(self, want, have):
        # Delete the interface config based on the want and have config
        commands = []
        if want.get('name'):
            interface = 'interface ' + want['name']
        else:
            interface = 'interface ' + have['name']

        if have.get('port_priority') and have.get('port_priority') != want.get('port_priority'):
            cmd = 'lacp port-priority'
            remove_command_from_config_list(interface, cmd, commands)
        if have.get('max_bundle') and have.get('max_bundle') != want.get('max_bundle'):
            cmd = 'lacp max-bundle'
            remove_command_from_config_list(interface, cmd, commands)
        if have.get('fast_switchover'):
            cmd = 'lacp fast-switchover'
            remove_command_from_config_list(interface, cmd, commands)

        return commands
