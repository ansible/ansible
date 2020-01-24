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

import copy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import remove_empties
from ansible.module_utils.network.ios.utils.utils import new_dict_to_set
import q

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

    def get_acl_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
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
                self._module.fail_json(msg="Value of running_config parameter must not be empty for state parsed")
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
        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []


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
        q(want, have)
        for interface in want:
            for each in have:
                if each['name'] == interface['name']:
                    break
            else:
                # configuring non-existing interface
                commands.extend(self._set_config(interface, dict()))
                continue
            commands.extend(self._set_config(interface, each))

        q(commands)
        commands = []
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
            pass
        else:
            for config_have in have:
                for acls_have in config_have.get('acls'):
                    commands.extend(self._clear_config(acls_have, config_have))

        return commands

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
        change = False
        want_set = set()
        have_set = set()
        # Convert the want and have dict to its respective set for taking the set diff
        new_dict_to_set(want, [], want_set)
        new_dict_to_set(have, [], have_set)
        diff = want_set - have_set
        q(want, have, diff)
        return
        # Populate the config only when there's a diff b/w want and have config
        if diff:
            name = acl_want.get('name')
            if afi == 'ipv4':
                try:
                    name = int(name)
                    # If name is numbered acl
                    if name <= 99:
                        cmd = 'ip access-list standard {0}'.format(name)
                    elif name >= 100:
                        cmd = 'ip access-list extended {0}'.format(name)
                except ValueError:
                    # If name is named acl
                    acl_type = acl_want.get('acl_type')
                    if acl_type:
                        cmd = 'ip access-list {0} {1}'.format(acl_type, name)
                    else:
                        self._module.fail_json(msg='ACL type value is required for Named ACL!')

            elif afi == 'ipv6':
                cmd = 'ipv6 access-list {0}'.format(name)

            # Get all of aces option values from diff dict
            sequence = want.get('sequence')
            grant = want.get('grant')
            source = want.get('source')
            destination = want.get('destination')
            po = want.get('protocol_options')
            dscp = want.get('dscp')
            fragments = want.get('fragments')
            log = want.get('log')
            log_input = want.get('log_input')
            option = want.get('option')
            precedence = want.get('precedence')
            time_range = want.get('time_range')
            tos = want.get('tos')
            ttl = want.get('ttl')

            if sequence:
                if afi == 'ipv6':
                    cmd = cmd + ' sequence {0}'.format(sequence)
                else:
                    cmd = cmd + ' {0}'.format(sequence)
            if grant:
                cmd = cmd + ' {0}'.format(grant)
            if po and isinstance(po, dict):
                po_key = list(po)[0]
                cmd = cmd + ' {0}'.format(po_key)
                if po.get('icmp'):
                    po_val = po.get('icmp')
                elif po.get('igmp'):
                    po_val = po.get('igmp')
                elif po.get('tcp'):
                    po_val = po.get('tcp')
            if source:
                cmd = self.source_dest_config(source, cmd, po)
            if destination:
                cmd = self.source_dest_config(destination, cmd, po)
            if po:
                cmd = cmd + ' {0}'.format(list(po_val)[0])
            if dscp:
                cmd = cmd + ' dscp {0}'.format(dscp)
            if fragments:
                cmd = cmd + ' fragments {0}'.format(fragments)
            if log:
                cmd = cmd + ' log {0}'.format(log)
            if log_input:
                cmd = cmd + ' log-input {0}'.format(log_input)
            if option:
                cmd = cmd + ' option {0}'.format(list(option)[0])
            if precedence:
                cmd = cmd + ' precedence {0}'.format(precedence)
            if time_range:
                cmd = cmd + ' time-range {0}'.format(time_range)
            if tos:
                for k, v in iteritems(tos):
                    if k == 'service_value':
                        cmd = cmd + ' tos {0}'.format(v)
                    else:
                        cmd = cmd + ' tos {0}'.format(v)
            if ttl:
                for k, v in iteritems(ttl):
                    if k == 'range' and v:
                        start = v.get('start')
                        end = v.get('start')
                        cmd = cmd + ' ttl {0} {1}'.format(start, end)
                    elif v:
                        cmd = cmd + ' ttl {0} {1}'.format(k, v)

            commands.append(cmd)
        if commands:
            change = True

        return commands, change

    def _clear_config(self, acl, config, sequence=''):
        """ Function that deletes the acl config based on the want and have config
        :param acl: acl config
        :param config: config
        :rtype: A list
        :returns: the commands generated based on input acl/config params
        """
        commands = []
        afi = config.get('afi')
        name = acl.get('name')
        if afi == 'ipv4' and name:
            try:
                name = int(name)
                if name <= 99 and not sequence:
                    cmd = 'no ip access-list standard {0}'.format(name)
                elif name >= 100 and not sequence:
                    cmd = 'no ip access-list extended {0}'.format(name)
                elif sequence:
                    if name <= 99:
                        cmd = 'ip access-list standard {0} '.format(name)
                    elif name >= 100:
                        cmd = 'ip access-list extended {0} '.format(name)
                    cmd += 'no {0}'.format(sequence)
            except ValueError:
                acl_type = acl.get('acl_type')
                if acl_type == 'extended' and not sequence:
                    cmd = 'no ip access-list extended {0}'.format(name)
                elif acl_type == 'standard' and not sequence:
                    cmd = 'no ip access-list standard {0}'.format(name)
                elif sequence:
                    if acl_type == 'extended':
                        cmd = 'ip access-list extended {0} '.format(name)
                    elif acl_type == 'standard':
                        cmd = 'ip access-list standard {0}'.format(name)
                    cmd += 'no {0}'.format(sequence)
                else:
                    self._module.fail_json(msg="ACL type value is required for Named ACL!")
        elif afi == 'ipv6' and name:
            if sequence:
                cmd = 'no sequence {0}'.format(sequence)
            else:
                cmd = 'no ipv6 access-list {0}'.format(name)
        commands.append(cmd)

        return commands