# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_l2_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.network.iosxr.utils.utils import get_interface_type, dict_diff
from ansible.module_utils.network.iosxr.utils.utils import remove_command_from_config_list, add_command_to_config_list
from ansible.module_utils.network.iosxr.utils.utils import filter_dict_having_none_value, remove_duplicate_interface


class L2_Interfaces(ConfigBase):
    """
    The iosxr_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l2_interfaces',
    ]

    def get_l2_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        l2_interfaces_facts = facts['ansible_network_resources'].get('interfaces')

        if not l2_interfaces_facts:
            return []
        return l2_interfaces_facts

    def execute_module(self):
        """ Execute the module
        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l2_interfaces_facts = self.get_l2_interfaces_facts()
        commands.extend(self.set_config(existing_l2_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_l2_interfaces_facts = self.get_l2_interfaces_facts()

        result['before'] = existing_l2_interfaces_facts
        if result['changed']:
            result['after'] = changed_l2_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l2_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l2_interfaces_facts
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
            commands = self._state_overridden(want, have, self._module)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have, self._module)
        elif state == 'replaced':
            commands = self._state_replaced(want, have, self._module)

        return commands

    @staticmethod
    def _state_replaced(want, have, module):
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
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            want = dict()
            commands.extend(L2_Interfaces.clear_interface(want, have_dict))
            commands.extend(L2_Interfaces.set_interface(interface, each, commands, module))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    @staticmethod
    def _state_overridden(want, have, module):
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
                elif interface['name'] in each['name']:
                    break
            else:
                # We didn't find a matching desired state, which means we can
                # pretend we recieved an empty desired state.
                interface = dict(name=each['name'])
                commands.extend(L2_Interfaces.clear_interface(interface, each))
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            want = dict()
            commands.extend(L2_Interfaces._clear_config(want, have_dict))
            commands.extend(L2_Interfaces.set_interface(interface, each, module))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    @staticmethod
    def _state_merged(want, have, module):
        """ The command generator when state is merged
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                continue
            commands.extend(L2_Interfaces.set_interface(interface, each, module))

        return commands

    @staticmethod
    def _state_deleted(want, have):
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
                    elif interface['name'] in each['name']:
                        break
                else:
                    continue
                interface = dict(name=interface['name'])
                commands.extend(L2_Interfaces.clear_interface(interface, each))
        else:
            for each in have:
                want = dict()
                commands.extend(L2_Interfaces._clear_config(want, each))

        return commands

    @staticmethod
    def set_interface(want, have, module):
        # Set the interface config based on the want and have config
        commands = []
        clear_cmds = []

        # Get the diff b/w want and have
        want_dict = dict_diff(want)
        have_dict = dict_diff(have)
        diff = want_dict - have_dict

        if diff:
            diff = dict(diff)

        if kwargs.get('commands'):
            clear_cmds = kwargs['commands']

        interface = 'interface ' + want['name']
        wants_native = want["native_vlan"]
        if wants_native and wants_native != str(have.get("native_vlan", {}).get("vlan")) or \
                'no dot1q native vlan' in clear_cmds:
            cmd = 'dot1q native vlan {}'.format(wants_native)
            add_command_to_config_list(interface, cmd, commands)

        if want.get('l2transport'):
            if want.get('l2protocol'):
                for each in want.get('l2protocol'):
                    for k, v in iteritems(each):
                        l2ptotocol_type = 'l2protocol_' + k
                        if have.get(l2ptotocol_type) != v:
                            cmd = 'l2transport l2protocol ' + k + ' ' + v
                            add_command_to_config_list(interface, cmd, commands)
            if want.get('propagate') and not have.get('propagate'):
                cmd = 'l2transport propagate remote-status'
                add_command_to_config_list(interface, cmd, commands)
        elif want.get('l2protocol') or want.get('propagate'):
            module.fail_json(msg='L2transports L2protocol or Propagate can only be configured when'
                                 'L2transprt set to True!')

        if want.get('q_vlan'):
            q_vlans = (" ".join(map(str, want.get('q_vlan'))))
            if q_vlans != have.get('q_vlan'):
                if 'any' in q_vlans and 'l2transport' in interface:
                    cmd = 'dot1q vlan {}'.format(q_vlans)
                    add_command_to_config_list(interface, cmd, commands)
                else:
                    cmd = 'dot1q vlan {}'.format(q_vlans)
                    add_command_to_config_list(interface, cmd, commands)

        return commands

    @staticmethod
    def clear_interface(want, have):
        # Delete the interface config based on the want and have config
        commands = []

        interface = 'interface ' + want['name']

        if 'q_vlan' in have and 'l2transport' in have['name'] and want['name'] in have['name'] \
                and (" ".join(map(str, want.get('q_vlan')))) != have.get('q_vlan'):
            remove_command_from_config_list(interface, 'dot1q vlan', commands)
        elif 'q_vlan' in have and 'l2transport' not in have['name'] and want['name'] in have['name']:
            remove_command_from_config_list(interface, 'encapsulation dot1q', commands)

        if 'native_vlan' in have and want.get('native_vlan') != str(have.get('native_vlan').get('vlan')):
            remove_command_from_config_list(interface, 'dot1q native vlan', commands)
        if want.get('l2transport'):
            if want.get('l2protocol'):
                for each in want.get('l2protocol'):
                    for k, v in iteritems(each):
                        l2ptotocol_type = 'l2protocol_' + k
                        if have.get(l2ptotocol_type) != v:
                            remove_command_from_config_list(interface, 'l2transport', commands)
        if have.get('l2transport') and not want.get('l2transport'):
            if 'no l2transport' not in commands:
                remove_command_from_config_list(interface, 'l2transport', commands)

        return commands
