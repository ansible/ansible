#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_acl_interfaces class
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
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.ios.utils.utils import remove_duplicate_interface, normalize_interface


class Acl_Interfaces(ConfigBase):
    """
    The ios_acl_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'acl_interfaces',
    ]

    def __init__(self, module):
        super(Acl_Interfaces, self).__init__(module)

    def get_acl_interfaces_facts(self, data=None):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources, data=data)
        acl_interfaces_facts = facts['ansible_network_resources'].get('acl_interfaces')
        if not acl_interfaces_facts:
            return []

        return acl_interfaces_facts

    def execute_module(self):
        """ Execute the module
        :rtype: A dictionary
        :returns: The result from moduel execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        if self.state in self.ACTION_STATES:
            existing_acl_interfaces_facts = self.get_acl_interfaces_facts()
        else:
            existing_acl_interfaces_facts = []

        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_acl_interfaces_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True

        if self.state in self.ACTION_STATES:
            result['commands'] = commands

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_acl_interfaces_facts = self.get_acl_interfaces_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            running_config = self._module.params['running_config']
            if not running_config:
                self._module.fail_json(
                    msg="value of running_config parameter must not be empty for state parsed"
                )
            result['parsed'] = self.get_acl_interfaces_facts(data=running_config)
        else:
            changed_acl_interfaces_facts = []

        if self.state in self.ACTION_STATES:
            result['before'] = existing_acl_interfaces_facts
            if result['changed']:
                result['after'] = changed_acl_interfaces_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_acl_interfaces_facts

        result['warnings'] = warnings

        return result

    def set_config(self, existing_acl_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        want = self._module.params['config']
        if want:
            for item in want:
                item['name'] = normalize_interface(item['name'])

        have = existing_acl_interfaces_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided
        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []

        state = self._module.params['state']
        if state in ('overridden', 'merged', 'replaced', 'rendered') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged' or state == 'rendered':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)

        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced
        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []

        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                continue
            commands.extend(self._clear_config(interface, each, 'replaced'))
            commands.extend(self._set_config(interface, each))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden
        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
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
            commands.extend(self._clear_config(interface, each, 'overridden'))
            commands.extend(self._set_config(interface, each))
        # Remove the duplicate interface call
        commands = remove_duplicate_interface(commands)

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged
        :param want: the additive configuration as a dictionary
        :param have: the current configuration as a dictionary
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
                # configuring non-existing interface
                commands.extend(self._set_config(interface, dict()))
                continue
            commands.extend(self._set_config(interface, each))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted
        :param want: the objects from which the configuration should be removed
        :param have: the current configuration as a dictionary
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
                commands.extend(self._clear_config(interface, each))
        else:
            for each in have:
                commands.extend(self._clear_config(dict(), each))

        return commands

    def dict_to_set(self, input_dict, test_set, final_set, count=0):
        # recursive function to convert input dict to set for comparision
        test_dict = dict()
        if isinstance(input_dict, dict):
            input_dict_len = len(input_dict)
            for k, v in sorted(iteritems(input_dict)):
                count += 1
                if isinstance(v, list):
                    for each in v:
                        if isinstance(each, dict):
                            input_dict_len = len(each)
                            if [True for i in each.values() if type(i) == list]:
                                self.dict_to_set(each, set(), final_set, count)
                            else:
                                self.dict_to_set(each, test_set, final_set, 0)
                else:
                    if v is not None:
                        test_dict.update({k: v})
                    if tuple(iteritems(test_dict)) not in test_set and count == input_dict_len:
                        test_set.add(tuple(iteritems(test_dict)))
                        count = 0
                    if count == input_dict_len + 1:
                        test_set.update(tuple(iteritems(test_dict)))
                        final_set.add(tuple(test_set))

    def _set_config(self, want, have):
        """ Function that sets the acls config based on the want and have config
        :param want: want config
        :param have: have config
        :param acl_want: want acl config
        :param afi: acl afi type
        :rtype: A list
        :returns: the commands generated based on input want/have params
        """
        commands = []

        want_set = set()
        have_set = set()
        self.dict_to_set(want, set(), want_set)
        self.dict_to_set(have, set(), have_set)

        for w in want_set:
            want_afi = dict(w).get('afi')
            if have_set:
                def common_diff_config_code(diff_list, cmd, commands):
                    for each in diff_list:
                        try:
                            temp = dict(each)
                            temp_cmd = cmd + ' {0} {1}'.format(temp['name'], temp['direction'])
                            if temp_cmd not in commands:
                                commands.append(temp_cmd)
                        except ValueError:
                            continue
                for h in have_set:
                    have_afi = dict(h).get('afi')
                    if have_afi == want_afi:
                        if want_afi == 'ipv4':
                            diff = set(w) - set(h)
                            if diff:
                                cmd = 'ip access-group'
                                common_diff_config_code(diff, cmd, commands)
                        if want_afi == 'ipv6':
                            diff = set(w) - set(h)
                            if diff:
                                cmd = 'ipv6 traffic-filter'
                                common_diff_config_code(diff, cmd, commands)
                        break
                else:
                    if want_afi == 'ipv4':
                        diff = set(w) - set(h)
                        if diff:
                            cmd = 'ip access-group'
                            common_diff_config_code(diff, cmd, commands)
                    if want_afi == 'ipv6':
                        diff = set(w) - set(h)
                        if diff:
                            cmd = 'ipv6 traffic-filter'
                            common_diff_config_code(diff, cmd, commands)
            else:
                def common_want_config_code(want, cmd, commands):
                    for each in want:
                        if each[0] == 'afi':
                            continue
                        temp = dict(each)
                        temp_cmd = cmd + ' {0} {1}'.format(temp['name'], temp['direction'])
                        commands.append(temp_cmd)
                if want_afi == 'ipv4':
                    cmd = 'ip access-group'
                    common_want_config_code(w, cmd, commands)
                if want_afi == 'ipv6':
                    cmd = 'ipv6 traffic-filter'
                    common_want_config_code(w, cmd, commands)
        commands.sort()
        if commands:
            interface = want.get('name')
            commands.insert(0, 'interface {0}'.format(interface))

        return commands

    def _clear_config(self, want, have, state=''):
        """ Function that deletes the acl config based on the want and have config
        :param acl: acl config
        :param config: config
        :rtype: A list
        :returns: the commands generated based on input acl/config params
        """
        commands = []

        if want.get('name'):
            interface = 'interface ' + want['name']
        else:
            interface = 'interface ' + have['name']

        w_access_group = want.get('access_groups')
        temp_want_afi = []
        temp_want_acl_name = []
        if w_access_group:
            # get the user input afi and acls
            for each in w_access_group:
                want_afi = each.get('afi')
                want_acls = each.get('acls')
                if want_afi:
                    temp_want_afi.append(want_afi)
                if want_acls:
                    for each in want_acls:
                        temp_want_acl_name.append(each.get('name'))

        h_access_group = have.get('access_groups')
        if h_access_group:
            for access_grp in h_access_group:
                for acl in access_grp.get('acls'):
                    have_afi = access_grp.get('afi')
                    acl_name = acl.get('name')
                    acl_direction = acl.get('direction')
                    if temp_want_afi and state not in ['replaced', 'overridden']:
                        # if user want to delete acls based on afi
                        if 'ipv4' in temp_want_afi and have_afi == 'ipv4':
                            if acl_name in temp_want_acl_name:
                                continue
                            cmd = 'no ip access-group'
                            cmd += ' {0} {1}'.format(acl_name, acl_direction)
                            commands.append(cmd)
                        if 'ipv6' in temp_want_afi and have_afi == 'ipv6':
                            if acl_name in temp_want_acl_name:
                                continue
                            cmd = 'no ipv6 traffic-filter'
                            cmd += ' {0} {1}'.format(acl_name, acl_direction)
                            commands.append(cmd)
                    else:
                        # if user want to delete acls based on interface
                        if access_grp.get('afi') == 'ipv4':
                            if acl_name in temp_want_acl_name:
                                continue
                            cmd = 'no ip access-group'
                            cmd += ' {0} {1}'.format(acl_name, acl_direction)
                            commands.append(cmd)
                        elif access_grp.get('afi') == 'ipv6':
                            if acl_name in temp_want_acl_name:
                                continue
                            cmd = 'no ipv6 traffic-filter'
                            cmd += ' {0} {1}'.format(acl_name, acl_direction)
                            commands.append(cmd)
        if commands:
            # inserting the interface at first
            commands.insert(0, interface)

        return commands
