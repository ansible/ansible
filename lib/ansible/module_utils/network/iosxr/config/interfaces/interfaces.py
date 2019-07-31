# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.network.iosxr.utils.utils import get_interface_type, dict_diff
from ansible.module_utils.network.iosxr.utils.utils import remove_command_from_interface, add_command_to_interface
from ansible.module_utils.network.iosxr.utils.utils import filter_dict_having_none_value, remove_duplicate_interface


class Interfaces(ConfigBase, InterfacesArgs):
    """
    The iosxr_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'interfaces',
    ]

    params = ('description', 'mtu', 'speed', 'duplex')

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        result = Facts().get_facts(self._module, self._connection, self.gather_subset, self.gather_network_resources)
        facts = result
        interfaces_facts = facts['ansible_network_resources'].get('interfaces')
        if not interfaces_facts:
            return []
        return interfaces_facts

    def execute_module(self):
        """ Execute the module
        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_interfaces_facts = self.get_interfaces_facts()
        commands.extend(self.set_config(existing_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_interfaces_facts = self.get_interfaces_facts()

        result['before'] = existing_interfaces_facts
        if result['changed']:
            result['after'] = changed_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_interfaces_facts
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
        if state == 'overridden':
            kwargs = {'want': want, 'have': have}
            commands = self._state_overridden(**kwargs)
        elif state == 'deleted':
            kwargs = {'want': want, 'have': have}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {'want': want, 'have': have}
            commands = self._state_merged(**kwargs)
        elif state == 'replaced':
            kwargs = {'want': want, 'have': have}
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
        want = kwargs['want']
        have = kwargs['have']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            kwargs = {'want': {}, 'have': have_dict}
            commands.extend(Interfaces._clear_config(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands}
            commands.extend(Interfaces._set_config(**kwargs))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    @staticmethod
    def _state_overridden(**kwargs):
        """ The command generator when state is overridden
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']

        for each in have:
            for interface in want:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                # We didn't find a matching desired state, which means we can
                # pretend we recieved an empty desired state.
                interface = dict(name=each['name'])
                kwargs = {'want': interface, 'have': each}
                commands.extend(Interfaces._clear_config(**kwargs))
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            kwargs = {'want': {}, 'have': have_dict}
            commands.extend(Interfaces._clear_config(**kwargs))
            kwargs = {'want': interface, 'have': each, 'commands': commands}
            commands.extend(Interfaces._set_config(**kwargs))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    @staticmethod
    def _state_merged(**kwargs):
        """ The command generator when state is merged
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            kwargs = {'want': interface, 'have': each}
            commands.extend(Interfaces._set_config(**kwargs))

        return commands

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        want = kwargs['want']
        have = kwargs['have']

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            interface = dict(name=interface['name'])
            kwargs = {'want': interface, 'have': each}
            commands.extend(Interfaces._clear_config(**kwargs))

        return commands

    @staticmethod
    def _set_config(**kwargs):
        # Set the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        # clear_cmds = []
        #
        # if kwargs.get('commands'):
        #     clear_cmds = kwargs['commands']

        interface = 'interface ' + want['name']

        # Get the diff b/w want and have
        want_dict = dict_diff(want)
        have_dict = dict_diff(have)
        diff = want_dict - have_dict

        if diff:
            diff = dict(diff)
            for item in Interfaces.params:
                if diff.get(item):
                    cmd = item + ' ' + str(want.get(item))
                    add_command_to_interface(interface, cmd, commands)
            if diff.get('enabled'):
                add_command_to_interface(interface, 'no shutdown', commands)
            elif diff.get('enabled') is False:
                add_command_to_interface(interface, 'shutdown', commands)

        return commands

    @staticmethod
    def _clear_config(**kwargs):
        # Delete the interface config based on the want and have config
        commands = []
        want = kwargs['want']
        have = kwargs['have']
        interface_type = get_interface_type(want['name'])
        interface = 'interface ' + want['name']

        if have.get('description') and want.get('description') != have.get('description'):
            _remove_command_from_interface(interface, 'description', commands)
        if not have.get('enabled') and want.get('enabled') != have.get('enabled'):
            # if enable is False set enable as True which is the default behavior
            _remove_command_from_interface(interface, 'shutdown', commands)

        if interface_type.lower() == 'gigabitethernet':
            if have.get('speed') and have.get('speed') != 'auto' and want.get('speed') != have.get('speed'):
                _remove_command_from_interface(interface, 'speed', commands)
            if have.get('duplex') and have.get('duplex') != 'auto' and want.get('duplex') != have.get('duplex'):
                _remove_command_from_interface(interface, 'duplex', commands)
            if have.get('mtu') and want.get('mtu') != have.get('mtu'):
                _remove_command_from_interface(interface, 'mtu', commands)

        return commands
