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


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.network.iosxr.utils.utils import normalize_interface, dict_to_set
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
        l2_interfaces_facts = facts['ansible_network_resources'].get('l2_interfaces')

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

        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands = self._state_overridden(want, have, self._module)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have, self._module)
        elif state == 'replaced':
            commands = self._state_replaced(want, have, self._module)

        return commands

    def _state_replaced(self, want, have, module):
        """ The command generator when state is replaced
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for interface in want:
            interface['name'] = normalize_interface(interface['name'])
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                commands.extend(self._set_config(interface, {}, module))
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            commands.extend(self._clear_config(dict(), have_dict))
            commands.extend(self._set_config(interface, each, module))
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
        not_in_have = set()
        in_have = set()
        for each in have:
            for interface in want:
                interface['name'] = normalize_interface(interface['name'])
                if each['name'] == interface['name']:
                    in_have.add(interface['name'])
                    break
                elif interface['name'] != each['name']:
                    not_in_have.add(interface['name'])
            else:
                # We didn't find a matching desired state, which means we can
                # pretend we recieved an empty desired state.
                interface = dict(name=each['name'])
                commands.extend(self._clear_config(interface, each))
                continue
            have_dict = filter_dict_having_none_value(interface, each)
            commands.extend(self._clear_config(dict(), have_dict))
            commands.extend(self._set_config(interface, each, module))
        # Add the want interface that's not already configured in have interface
        for each in (not_in_have - in_have):
            for every in want:
                interface = 'interface {0}'.format(every['name'])
                if each and interface not in commands:
                    commands.extend(self._set_config(every, {}, module))

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
            interface['name'] = normalize_interface(interface['name'])
            for each in have:
                if each['name'] == interface['name']:
                    break
                elif interface['name'] in each['name']:
                    break
            else:
                commands.extend(self._set_config(interface, {}, module))
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
                interface['name'] = normalize_interface(interface['name'])
                for each in have:
                    if each['name'] == interface['name']:
                        break
                    elif interface['name'] in each['name']:
                        break
                else:
                    continue
                interface = dict(name=interface['name'])
                commands.extend(self._clear_config(interface, each))
        else:
            for each in have:
                want = dict()
                commands.extend(self._clear_config(want, each))

        return commands

    def _set_config(self, want, have, module):
        # Set the interface config based on the want and have config
        commands = []
        interface = 'interface ' + want['name']
        l2_protocol_bool = False

        # Get the diff b/w want and have
        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)
        diff = want_dict - have_dict

        if diff:
            # For merging with already configured l2protocol
            if have.get('l2protocol') and len(have.get('l2protocol')) > 1:
                l2_protocol_diff = []
                for each in want.get('l2protocol'):
                    for every in have.get('l2protocol'):
                        if every == each:
                            break
                    if each not in have.get('l2protocol'):
                        l2_protocol_diff.append(each)
                l2_protocol_bool = True
                l2protocol = tuple(l2_protocol_diff)
            else:
                l2protocol = {}

            diff = dict(diff)
            wants_native = diff.get('native_vlan')
            l2transport = diff.get('l2transport')
            q_vlan = diff.get('q_vlan')
            propagate = diff.get('propagate')
            if l2_protocol_bool is False:
                l2protocol = diff.get('l2protocol')

            if wants_native:
                cmd = 'dot1q native vlan {0}'.format(wants_native)
                add_command_to_config_list(interface, cmd, commands)

            if l2transport or l2protocol:
                for each in l2protocol:
                    each = dict(each)
                    if isinstance(each, dict):
                        cmd = 'l2transport l2protocol {0} {1}'.format(list(each.keys())[0], list(each.values())[0])
                    add_command_to_config_list(interface, cmd, commands)
                if propagate and not have.get('propagate'):
                    cmd = 'l2transport propagate remote-status'
                    add_command_to_config_list(interface, cmd, commands)
            elif want.get('l2transport') is False and (want.get('l2protocol') or want.get('propagate')):
                module.fail_json(msg='L2transport L2protocol or Propagate can only be configured when '
                                     'L2transport set to True!')

            if q_vlan and '.' in interface:
                q_vlans = (" ".join(map(str, want.get('q_vlan'))))
                if q_vlans != have.get('q_vlan'):
                    cmd = 'dot1q vlan {0}'.format(q_vlans)
                    add_command_to_config_list(interface, cmd, commands)

        return commands

    def _clear_config(self, want, have):
        # Delete the interface config based on the want and have config
        commands = []

        if want.get('name'):
            interface = 'interface ' + want['name']
        else:
            interface = 'interface ' + have['name']
        if have.get('native_vlan'):
            remove_command_from_config_list(interface, 'dot1q native vlan', commands)

        if have.get('q_vlan'):
            remove_command_from_config_list(interface, 'encapsulation dot1q', commands)

        if have.get('l2protocol') and (want.get('l2protocol') is None or want.get('propagate') is None):
            if 'no l2transport' not in commands:
                remove_command_from_config_list(interface, 'l2transport', commands)
        elif have.get('l2transport') and have.get('l2transport') != want.get('l2transport'):
            if 'no l2transport' not in commands:
                remove_command_from_config_list(interface, 'l2transport', commands)

        return commands
