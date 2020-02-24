#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_acl_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import itertools

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, search_obj_in_list
from ansible.module_utils.network.eos.facts.facts import Facts


class Acl_interfaces(ConfigBase):
    """
    The eos_acl_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'acl_interfaces',
    ]

    def __init__(self, module):
        super(Acl_interfaces, self).__init__(module)

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
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()
        changed = False

        if self.state in self.ACTION_STATES:
            existing_acl_interfaces_facts = self.get_acl_interfaces_facts()
        else:
            existing_acl_interfaces_facts = []
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_acl_interfaces_facts))
        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
                changed = True
            if changed:
                result['changed'] = True
        if self.state in self.ACTION_STATES:
            result['commands'] = commands
        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_acl_interfaces_facts = self.get_acl_interfaces_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            if not self._module.params['running_config']:
                self._module.fail_json(msg="Value of running_config parameter must not be empty for state parsed")
            result['parsed'] = self.get_acl_interfaces_facts(data=self._module.params['running_config'])
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
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_acl_interfaces_facts
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
        if self.state in ('merged', 'replaced', 'overridden') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(self.state))
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged' or self.state == 'rendered':
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
        commandset = []
        want_interface = []
        for w in want:
            commands = []
            diff_access_group = []
            want_interface.append(w['name'])
            obj_in_have = search_obj_in_list(w['name'], have, 'name')
            if not obj_in_have or 'access_groups' not in obj_in_have.keys():
                commands.append(add_commands(w['access_groups'], w['name']))
            else:
                if 'access_groups' in obj_in_have.keys():
                    obj = self.get_acl_diff(obj_in_have, w)
                    if obj[0]:
                        to_delete = {'access_groups': [{'acls': obj[0], 'afi': 'ipv4'}]}
                        commands.append(remove_commands(to_delete, w['name']))
                    if obj[1]:
                        to_delete = {'access_groups': [{'acls': obj[1], 'afi': 'ipv6'}]}
                        commands.append(remove_commands(to_delete, w['name']))
                    diff = self.get_acl_diff(w, obj_in_have)
                    if diff[0]:
                        diff_access_group.append({'afi': 'ipv4', 'acls': diff[0]})
                    if diff[1]:
                        diff_access_group.append({'afi': 'ipv6', 'acls': diff[1]})
                    if diff_access_group:
                        commands.append(add_commands(diff_access_group, w['name']))
            if commands:
                intf_command = ["interface " + w['name']]
                commands = list(itertools.chain(*commands))
                commandset.append(intf_command)
                commandset.append(commands)

        if commandset:
            commandset = list(itertools.chain(*commandset))
        return commandset

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commandset = []
        want_interface = []
        for w in want:
            commands = []
            diff_access_group = []
            want_interface.append(w['name'])
            obj_in_have = search_obj_in_list(w['name'], have, 'name')
            if not obj_in_have or 'access_groups' not in obj_in_have.keys():
                commands.append(add_commands(w['access_groups'], w['name']))
            else:
                if 'access_groups' in obj_in_have.keys():
                    obj = self.get_acl_diff(obj_in_have, w)
                    if obj[0]:
                        to_delete = {'access_groups': [{'acls': obj[0], 'afi': 'ipv4'}]}
                        commands.append(remove_commands(to_delete, w['name']))
                    if obj[1]:
                        to_delete = {'access_groups': [{'acls': obj[1], 'afi': 'ipv6'}]}
                        commands.append(remove_commands(to_delete, w['name']))
                    diff = self.get_acl_diff(w, obj_in_have)
                    if diff[0]:
                        diff_access_group.append({'afi': 'ipv4', 'acls': diff[0]})
                    if diff[1]:
                        diff_access_group.append({'afi': 'ipv6', 'acls': diff[1]})
                    if diff_access_group:
                        commands.append(add_commands(diff_access_group, w['name']))
            if commands:
                intf_command = ["interface " + w['name']]
                commands = list(itertools.chain(*commands))
                commandset.append(intf_command)
                commandset.append(commands)
        for h in have:
            commands = []
            if 'access_groups' in h.keys() and h['access_groups']:
                if h['name'] not in want_interface:
                    for h_group in h['access_groups']:
                        to_delete = {'access_groups': [h_group]}
                        commands.append(remove_commands(to_delete, h['name']))
            if commands:
                intf_command = ["interface " + h['name']]
                commands = list(itertools.chain(*commands))
                commandset.append(intf_command)
                commandset.append(commands)

        if commandset:
            commandset = list(itertools.chain(*commandset))

        return commandset

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commandset = []
        for w in want:
            commands = []
            diff_access_group = []
            obj_in_have = search_obj_in_list(w['name'], have, 'name')
            if not obj_in_have:
                commands = add_commands(w['access_groups'], w['name'])
            else:
                if 'access_groups' in obj_in_have.keys():
                    diff = self.get_acl_diff(w, obj_in_have)
                    if diff[0]:
                        diff_access_group.append({'afi': 'ipv4', 'acls': diff[0]})
                    if diff[1]:
                        diff_access_group.append({'afi': 'ipv6', 'acls': diff[1]})
                    if diff_access_group:
                        commands = add_commands(diff_access_group, w['name'])
                else:
                    commands = add_commands(w['access_groups'], w['name'])
            if commands:
                intf_command = ["interface " + w['name']]
                commandset.append(intf_command)
                commandset.append(commands)
        if commandset:
            commandset = list(itertools.chain(*commandset))
        return commandset

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commandset = []
        for w in want:
            commands = []
            intf_command = ["interface " + w['name']]
            obj_in_have = search_obj_in_list(w['name'], have, 'name')
            if 'access_groups' not in w.keys() or not w['access_groups']:
                commands = remove_commands(obj_in_have, w['name'])
            if w['access_groups']:
                for w_grp in w['access_groups']:
                    if 'acls' not in w_grp.keys() or not w_grp['acls']:
                        obj = self.get_acls_from_afi(w['name'], w_grp['afi'], have)
                        to_delete = {'access_groups': [{'acls': obj, 'afi': w_grp['afi']}]}
                        commands = remove_commands(to_delete, w['name'])
                    else:
                        if 'access_groups' not in obj_in_have.keys() or not obj_in_have['access_groups']:
                            continue
                        group = {'access_groups': [w_grp]}
                        obj = self.get_acl_diff(group, obj_in_have, True)
                        if obj[0]:
                            to_delete = {'access_groups': [{'acls': obj[0], 'afi': 'ipv4'}]}
                            commands.append(remove_commands(to_delete, w['name']))
                        if obj[1]:
                            to_delete = {'access_groups': [{'acls': obj[1], 'afi': 'ipv6'}]}
                            commands.append(remove_commands(to_delete, w['name']))
                        if commands:
                            commands = list(itertools.chain(*commands))
            if commands:
                commandset.append(intf_command)
                commandset.append(commands)

        if commandset:
            commandset = list(itertools.chain(*commandset))
        return commandset

    def get_acl_diff(self, w, h, intersection=False):
        diff_v4 = []
        diff_v6 = []
        w_acls_v4 = []
        w_acls_v6 = []
        h_acls_v4 = []
        h_acls_v6 = []
        for w_group in w['access_groups']:
            if w_group['afi'] == 'ipv4':
                w_acls_v4 = w_group['acls']
            if w_group['afi'] == 'ipv6':
                w_acls_v6 = w_group['acls']
        for h_group in h['access_groups']:
            if h_group['afi'] == 'ipv4':
                h_acls_v4 = h_group['acls']
            if h_group['afi'] == 'ipv6':
                h_acls_v6 = h_group['acls']
        for item in w_acls_v4:
            match = list(filter(lambda x: x['name'] == item['name'], h_acls_v4))
            if match:
                if item['direction'] == match[0]['direction']:
                    if intersection:
                        diff_v4.append(item)
                else:
                    if not intersection:
                        diff_v4.append(item)
            else:
                if not intersection:
                    diff_v4.append(item)
        for item in w_acls_v6:
            match = list(filter(lambda x: x['name'] == item['name'], h_acls_v6))
            if match:
                if item['direction'] == match[0]['direction']:
                    if intersection:
                        diff_v6.append(item)
                else:
                    if not intersection:
                        diff_v6.append(item)
            else:
                if not intersection:
                    diff_v6.append(item)
        return diff_v4, diff_v6

    def get_acls_from_afi(self, interface, afi, have):
        config = []
        for h in have:
            if h['name'] == interface:
                if 'access_groups' not in h.keys() or not h['access_groups']:
                    continue
                if h['access_groups']:
                    for h_grp in h['access_groups']:
                        if h_grp['afi'] == afi:
                            config = h_grp['acls']
        return config


def add_commands(want, interface):
    commands = []

    for w in want:
        # This module was verified on an ios device since vEOS doesnot support
        # acl_interfaces cnfiguration. In ios, ipv6 acl is configured as
        # traffic-filter and in eos it is access-group

        # a_cmd = "traffic-filter" if w['afi'] == 'ipv6' else "access-group"
        a_cmd = "access-group"
        afi = 'ip' if w['afi'] == 'ipv4' else w['afi']
        if 'acls' in w.keys():
            for acl in w['acls']:
                commands.append(afi + " " + a_cmd + " " + acl['name'] + " " + acl['direction'])
    return commands


def remove_commands(want, interface):
    commands = []
    if 'access_groups' not in want.keys() or not want['access_groups']:
        return commands
    for w in want['access_groups']:
        # This module was verified on an ios device since vEOS doesnot support
        # acl_interfaces cnfiguration. In ios, ipv6 acl is configured as
        # traffic-filter and in eos it is access-group

        # a_cmd = "traffic-filter" if w['afi'] == 'ipv6' else "access-group"
        a_cmd = "access-group"

        afi = 'ip' if w['afi'] == 'ipv4' else w['afi']
        if 'acls' in w.keys():
            for acl in w['acls']:
                commands.append("no " + afi + " " + a_cmd + " " + acl['name'] + " " + acl['direction'])
    return commands
