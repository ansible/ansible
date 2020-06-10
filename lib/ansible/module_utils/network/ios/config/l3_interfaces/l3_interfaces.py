# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_l3_interfaces class
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
from ansible.module_utils.network.ios.utils.utils import dict_to_set, normalize_interface
from ansible.module_utils.network.ios.utils.utils import remove_command_from_config_list, add_command_to_config_list
from ansible.module_utils.network.ios.utils.utils import filter_dict_having_none_value, remove_duplicate_interface
from ansible.module_utils.network.ios.utils.utils import validate_n_expand_ipv4, validate_ipv6


class L3_Interfaces(ConfigBase):
    """
    The ios_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces'
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
        config = self._module.params.get("config")
        want = []
        if config:
            for each in config:
                each.update({"name": normalize_interface(each["name"])})
                want.append(each)
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
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                if '.' in interface['name']:
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

        for each in have:
            for interface in want:
                if each['name'] == interface['name']:
                    break
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
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                if '.' in interface['name']:
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
                elif each_want.get('dhcp_client') != every_have.get('dhcp_client') and each_want.get(
                        'dhcp_client') is not None:
                    diff = True
                    break
                elif each_want.get('dhcp_hostname') != every_have.get('dhcp_hostname') and each_want.get(
                        'dhcp_hostname') is not None:
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

        # Convert the want and have dict to set
        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)

        # To handle L3 IPV4 configuration
        if want.get('ipv4'):
            # Get the diff b/w want and have IPV4
            if have.get('ipv4'):
                ipv4 = tuple(set(dict(want_dict).get('ipv4')) - set(dict(have_dict).get('ipv4')))
                if ipv4:
                    ipv4 = ipv4 if self.verify_diff_again(dict(want_dict).get('ipv4'), dict(have_dict).get('ipv4')) else ()
            else:
                diff = want_dict - have_dict
                ipv4 = dict(diff).get('ipv4')
            if ipv4:
                for each in ipv4:
                    ipv4_dict = dict(each)
                    if ipv4_dict.get('address') != 'dhcp':
                        cmd = "ip address {0}".format(ipv4_dict['address'])
                        if ipv4_dict.get("secondary"):
                            cmd += " secondary"
                    elif ipv4_dict.get('address') == 'dhcp':
                        cmd = "ip address dhcp"
                        if ipv4_dict.get('dhcp_client') is not None and ipv4_dict.get('dhcp_hostname'):
                            cmd = "ip address dhcp client-id GigabitEthernet 0/{0} hostname {1}"\
                                .format(ipv4_dict.get('dhcp_client'), ipv4_dict.get('dhcp_hostname'))
                        elif ipv4_dict.get('dhcp_client') and not ipv4_dict.get('dhcp_hostname'):
                            cmd = "ip address dhcp client-id GigabitEthernet 0/{0}"\
                                .format(ipv4_dict.get('dhcp_client'))
                        elif not ipv4_dict.get('dhcp_client') and ipv4_dict.get('dhcp_hostname'):
                            cmd = "ip address dhcp hostname {0}".format(ipv4_dict.get('dhcp_client'))

                    add_command_to_config_list(interface, cmd, commands)

        # To handle L3 IPV6 configuration
        if want.get('ipv6'):
            # Get the diff b/w want and have IPV6
            if have.get('ipv6'):
                ipv6 = tuple(set(dict(want_dict).get('ipv6')) - set(dict(have_dict).get('ipv6')))
            else:
                diff = want_dict - have_dict
                ipv6 = dict(diff).get('ipv6')
            if ipv6:
                for each in ipv6:
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
        if have.get('ipv4') and not want.get('ipv4'):
            remove_command_from_config_list(interface, 'ip address', commands)
        if have.get('ipv6') and not want.get('ipv6'):
            remove_command_from_config_list(interface, 'ipv6 address', commands)
        return commands
