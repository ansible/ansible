# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_l3_interfaces class
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
from ansible.module_utils.network.iosxr.utils.utils import validate_n_expand_ipv4, validate_ipv6


class L3_Interfaces(ConfigBase):
    """
    The iosxr_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces',
    ]

    def get_l3_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        l3_interfaces_facts = facts['ansible_network_resources'].get('l3_interfaces')
        if not l3_interfaces_facts:
            return []

        return l3_interfaces_facts

    def execute_module(self):
        """ Execute the module
        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l3_interfaces_facts = self.get_l3_interfaces_facts()
        commands.extend(self.set_config(existing_l3_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_l3_interfaces_facts = self.get_l3_interfaces_facts()

        result['before'] = existing_l3_interfaces_facts
        if result['changed']:
            result['after'] = changed_l3_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l3_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l3_interfaces_facts
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
                commands.extend(self._set_config(interface, dict(), module))
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
                kwargs = {'want': interface, 'have': each}
                commands.extend(self._clear_config(**kwargs))
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
            else:
                commands.extend(self._set_config(interface, dict(), module))
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

    def verify_diff_again(self, want, have):
        """
        Verify the IPV4 difference again as sometimes due to
        change in order of set, set difference may result into change,
        when there's actually no difference between want and have
        :param want: want_dict IPV4
        :param have: have_dict IPV4
        :return: diff
        """
        diff = False
        for each in want:
            each_want = dict(each)
            for every in have:
                every_have = dict(every)
                if each_want.get('address') != every_have.get('address') and \
                        each_want.get('secondary') != every_have.get('secondary') and \
                        len(each_want.keys()) == len(every_have.keys()):
                    diff = True
                    break
                elif each_want.get('address') != every_have.get('address') and len(each_want.keys()) == len(
                        every_have.keys()):
                    diff = True
                    break
            if diff:
                break

        return diff

    def _set_config(self, want, have, module):
        # Set the interface config based on the want and have config
        commands = []
        interface = 'interface ' + want['name']

        # To handle L3 IPV4 configuration
        if want.get("ipv4"):
            for each in want.get("ipv4"):
                if each.get('address') != 'dhcp':
                    ip_addr_want = validate_n_expand_ipv4(module, each)
                    each['address'] = ip_addr_want

        # Get the diff b/w want and have
        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)

        # To handle L3 IPV4 configuration
        want_ipv4 = dict(want_dict).get('ipv4')
        have_ipv4 = dict(have_dict).get('ipv4')
        if want_ipv4:
            if have_ipv4:
                diff_ipv4 = set(want_ipv4) - set(dict(have_dict).get('ipv4'))
                if diff_ipv4:
                    diff_ipv4 = diff_ipv4 if self.verify_diff_again(want_ipv4, have_ipv4) else ()
            else:
                diff_ipv4 = set(want_ipv4)
            for each in diff_ipv4:
                ipv4_dict = dict(each)
                if ipv4_dict.get('address') != 'dhcp':
                    cmd = "ipv4 address {0}".format(ipv4_dict['address'])
                    if ipv4_dict.get("secondary"):
                        cmd += " secondary"
                add_command_to_config_list(interface, cmd, commands)

        # To handle L3 IPV6 configuration
        want_ipv6 = dict(want_dict).get('ipv6')
        have_ipv6 = dict(have_dict).get('ipv6')
        if want_ipv6:
            if have_ipv6:
                diff_ipv6 = set(want_ipv6) - set(have_ipv6)
            else:
                diff_ipv6 = set(want_ipv6)
            for each in diff_ipv6:
                ipv6_dict = dict(each)
                validate_ipv6(ipv6_dict.get('address'), module)
                cmd = "ipv6 address {0}".format(ipv6_dict.get('address'))
                add_command_to_config_list(interface, cmd, commands)

        return commands

    def _clear_config(self, want, have):
        # Delete the interface config based on the want and have config
        count = 0
        commands = []
        if want.get('name'):
            interface = 'interface ' + want['name']
        else:
            interface = 'interface ' + have['name']

        if have.get('ipv4') and want.get('ipv4'):
            for each in have.get('ipv4'):
                if each.get('secondary') and not (want.get('ipv4')[count].get('secondary')):
                    cmd = 'ipv4 address {0} secondary'.format(each.get('address'))
                    remove_command_from_config_list(interface, cmd, commands)
                count += 1
        if have.get('ipv4') and not (want.get('ipv4')):
            remove_command_from_config_list(interface, 'ipv4 address', commands)
        if have.get('ipv6') and not (want.get('ipv6')):
            remove_command_from_config_list(interface, 'ipv6 address', commands)

        return commands
