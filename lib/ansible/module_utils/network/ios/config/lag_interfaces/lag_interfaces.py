#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import re
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts
from ansible.module_utils.network.ios.utils.utils import dict_to_set
from ansible.module_utils.network.ios.utils.utils import filter_dict_having_none_value, remove_duplicate_interface


class Lag_interfaces(ConfigBase):
    """
    The ios_lag_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lag_interfaces',
    ]

    def __init__(self, module):
        super(Lag_interfaces, self).__init__(module)

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
        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        module = self._module
        if state == 'overridden':
            commands = self._state_overridden(want, have, module)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have, module)
        elif state == 'replaced':
            commands = self._state_replaced(want, have, module)
        return commands

    def _state_replaced(self, want, have, module):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for interface in want:
            for each_interface in interface.get('members'):
                for each in have:
                    if each.get('members'):
                        for every in each.get('members'):
                            match = False
                            if every['member'] == each_interface['member']:
                                match = True
                                break
                            else:
                                continue
                        if match:
                            have_dict = filter_dict_having_none_value(interface, each)
                            commands.extend(self._clear_config(dict(), have_dict))
                            commands.extend(self._set_config(interface, each, module))
                    elif each.get('name') == each_interface['member']:
                        have_dict = filter_dict_having_none_value(interface, each)
                        commands.extend(self._clear_config(dict(), have_dict))
                        commands.extend(self._set_config(interface, each, module))
                        break
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    def _state_overridden(self, want, have, module):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for interface in want:
            for each_interface in interface.get('members'):
                for each in have:
                    if each.get('members'):
                        for every in each.get('members'):
                            match = False
                            if every['member'] == each_interface['member']:
                                match = True
                                break
                            else:
                                commands.extend(self._clear_config(interface, each))
                                continue
                        if match:
                            have_dict = filter_dict_having_none_value(interface, each)
                            commands.extend(self._clear_config(dict(), have_dict))
                            commands.extend(self._set_config(interface, each, module))
                    elif each.get('name') == each_interface['member']:
                        have_dict = filter_dict_having_none_value(interface, each)
                        commands.extend(self._clear_config(dict(), have_dict))
                        commands.extend(self._set_config(interface, each, module))
                        break
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    def _state_merged(self, want, have, module):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        for interface in want:
            for each_interface in interface.get('members'):
                for each in have:
                    if each.get('members'):
                        for every in each.get('members'):
                            if every['member'] == each_interface['member']:
                                break
                    elif each.get('name') == each_interface['member']:
                        break
                else:
                    continue
                commands.extend(self._set_config(interface, each, module))

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
                    if each.get('name') == interface['name']:
                        break
                else:
                    continue
                commands.extend(self._clear_config(interface, each))
        else:
            for each in have:
                commands.extend(self._clear_config(dict(), each))

        return commands

    def remove_command_from_config_list(self, interface, cmd, commands):
        # To delete the passed config
        if interface not in commands:
            commands.append(interface)
        commands.append('no %s' % cmd)
        return commands

    def add_command_to_config_list(self, interface, cmd, commands):
        # To set the passed config
        if interface not in commands:
            commands.append(interface)
        commands.append(cmd)
        return commands

    def _set_config(self, want, have, module):
        # Set the interface config based on the want and have config
        commands = []

        # To remove keys with None values from want dict
        want = utils.remove_empties(want)
        # Get the diff b/w want and have
        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)
        diff = want_dict - have_dict

        # To get the channel-id from lag port-channel name
        lag_config = dict(diff).get('members')
        channel_name = re.search(r'(\d+)', want.get('name'))
        if channel_name:
            channel_id = channel_name.group()
        else:
            module.fail_json(msg="Lag Interface Name is not correct!")
        if lag_config:
            for each in lag_config:
                each = dict(each)
                each_interface = 'interface {0}'.format(each.get('member'))
                if have.get('name') == want['members'][0]['member'] or have.get('name').lower().startswith('po'):
                    if each.get('mode'):
                        cmd = 'channel-group {0} mode {1}'.format(channel_id, each.get('mode'))
                        self.add_command_to_config_list(each_interface, cmd, commands)
                    elif each.get('link'):
                        cmd = 'channel-group {0} link {1}'.format(channel_id, each.get('link'))
                        self.add_command_to_config_list(each_interface, cmd, commands)

        return commands

    def _clear_config(self, want, have):
        # Delete the interface config based on the want and have config
        commands = []

        if have.get('members'):
            for each in have['members']:
                interface = 'interface ' + each['member']
                if want.get('members'):
                    if each.get('member') and each.get('member') != want['members'][0]['member']:
                        self.remove_command_from_config_list(interface, 'channel-group', commands)
                elif each.get('member'):
                    self.remove_command_from_config_list(interface, 'channel-group', commands)

        return commands
