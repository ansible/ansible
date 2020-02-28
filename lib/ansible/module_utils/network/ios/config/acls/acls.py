#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_acls class
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


class Acls(ConfigBase):
    """
    The ios_acls class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'acls',
    ]

    def __init__(self, module):
        super(Acls, self).__init__(module)

    def get_acl_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources, data=data)
        acl_facts = facts['ansible_network_resources'].get('acls')
        if not acl_facts:
            return []

        return acl_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from moduel execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        if self.state in self.ACTION_STATES:
            existing_acl_facts = self.get_acl_facts()
        else:
            existing_acl_facts = []

        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_acl_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True

        if self.state in self.ACTION_STATES:
            result['commands'] = commands

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_acl_facts = self.get_acl_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            running_config = self._module.params['running_config']
            if not running_config:
                self._module.fail_json(msg="value of running_config parameter must not be empty for state parsed")
            result['parsed'] = self.get_acl_facts(data=running_config)
        else:
            changed_acl_facts = []

        if self.state in self.ACTION_STATES:
            result['before'] = existing_acl_facts
            if result['changed']:
                result['after'] = changed_acl_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_acl_facts

        result['warnings'] = warnings

        return result

    def set_config(self, existing_acl_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        want = self._module.params['config']
        have = existing_acl_facts
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

        for config_want in want:
            for acls_want in config_want.get('acls'):
                for ace_want in acls_want.get('aces'):
                    check = False
                    for config_have in have:
                        for acls_have in config_have.get('acls'):
                            for ace_have in acls_have.get('aces'):
                                if acls_want.get('name') == acls_have.get('name'):
                                    ace_want = remove_empties(ace_want)
                                    acls_want = remove_empties(acls_want)
                                    cmd, change = self._set_config(ace_want,
                                                                   ace_have,
                                                                   acls_want,
                                                                   config_want['afi'])
                                    if cmd:
                                        for temp_acls_have in config_have.get('acls'):
                                            for temp_ace_have in temp_acls_have.get('aces'):
                                                if acls_want.get('name') == temp_acls_have.get('name'):
                                                    commands.extend(
                                                        self._clear_config(temp_acls_have,
                                                                           config_have,
                                                                           temp_ace_have.get('sequence')))
                                        commands.extend(cmd)
                                    check = True
                            if check:
                                break
                        if check:
                            break
                    if not check:
                        # For configuring any non-existing want config
                        ace_want = remove_empties(ace_want)
                        cmd, change = self._set_config(ace_want,
                                                       {},
                                                       acls_want,
                                                       config_want['afi'])
                        commands.extend(cmd)
        # Split and arrange the config commands
        commands = self.split_set_cmd(commands)

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
        # Creating a copy of want, so that want dict is intact even after delete operation
        # performed during override want n have comparison
        temp_want = copy.deepcopy(want)

        for config_have in have:
            for acls_have in config_have.get('acls'):
                for ace_have in acls_have.get('aces'):
                    check = False
                    for config_want in temp_want:
                        count = 0
                        for acls_want in config_want.get('acls'):
                            for ace_want in acls_want.get('aces'):
                                if acls_want.get('name') == acls_have.get('name'):
                                    ace_want = remove_empties(ace_want)
                                    acls_want = remove_empties(acls_want)
                                    cmd, change = self._set_config(ace_want, ace_have, acls_want, config_want['afi'])
                                    if cmd:
                                        for temp_acls_have in config_have.get('acls'):
                                            for temp_ace_have in temp_acls_have.get('aces'):
                                                if acls_want.get('name') == temp_acls_have.get('name'):
                                                    commands.extend(
                                                        self._clear_config(temp_acls_have,
                                                                           config_have,
                                                                           temp_ace_have.get('sequence')))
                                        commands.extend(cmd)
                                    check = True
                                    if check:
                                        del config_want.get('acls')[count]
                                else:
                                    count += 1
                        if check:
                            break
                    if check:
                        break
                if not check:
                    # Delete the config not present in want config
                    commands.extend(self._clear_config(acls_have, config_have))

        # For configuring any non-existing want config
        for config_want in temp_want:
            for acls_want in config_want.get('acls'):
                for ace_want in acls_want.get('aces'):
                    ace_want = remove_empties(ace_want)
                    cmd, change = self._set_config(ace_want,
                                                   {},
                                                   acls_want,
                                                   config_want['afi'])
                    commands.extend(cmd)

        # Split and arrange the config commands
        commands = self.split_set_cmd(commands)
        # Arranging the cmds suct that all delete cmds are fired before all set cmds
        negate_commands = [each for each in commands if 'no' in each and 'access-list' in each]
        negate_commands.extend([each for each in commands if each not in negate_commands])
        commands = negate_commands

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

        for config_want in want:
            for acls_want in config_want.get('acls'):
                for ace_want in acls_want.get('aces'):
                    check = False
                    for config_have in have:
                        for acls_have in config_have.get('acls'):
                            for ace_have in acls_have.get('aces'):
                                if acls_want.get('name') == acls_have.get('name') and \
                                        ace_want.get('sequence') == ace_have.get('sequence'):
                                    ace_want = remove_empties(ace_want)
                                    cmd, change = self._set_config(ace_want,
                                                                   ace_have,
                                                                   acls_want,
                                                                   config_want['afi'])
                                    # clear config will be fired only when there's command wrt to config
                                    if config_want.get('afi') == 'ipv4' and change:
                                        # for ipv4 only inplace update cannot be done, so deleting the sequence ace
                                        # and then updating the want ace changes
                                        commands.extend(self._clear_config(acls_want,
                                                                           config_want,
                                                                           ace_want.get('sequence')))
                                    commands.extend(cmd)
                                    check = True
                                elif acls_want.get('name') == acls_have.get('name'):
                                    ace_want = remove_empties(ace_want)
                                    cmd, check = self.common_condition_check(ace_want,
                                                                             ace_have,
                                                                             acls_want,
                                                                             config_want,
                                                                             check,
                                                                             acls_have)
                                    if acls_have.get('acl_type') == 'standard':
                                        check = True
                                    commands.extend(cmd)
                            if check:
                                break
                        if check:
                            break
                    if not check:
                        # For configuring any non-existing want config
                        ace_want = remove_empties(ace_want)
                        cmd, change = self._set_config(ace_want,
                                                       {},
                                                       acls_want,
                                                       config_want['afi'])
                        commands.extend(cmd)
        # Split and arrange the config commands
        commands = self.split_set_cmd(commands)

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
            for config_want in want:
                if config_want.get('acls'):
                    for acls_want in config_want.get('acls'):
                        if acls_want.get('aces'):
                            for ace_want in acls_want.get('aces'):
                                for config_have in have:
                                    for acls_have in config_have.get('acls'):
                                        if acls_want.get('name') == acls_have.get('name'):
                                            if ace_want.get('sequence'):
                                                commands.extend(self._clear_config(acls_want,
                                                                                   config_want,
                                                                                   ace_want.get('sequence')))
                                            else:
                                                commands.extend(self._clear_config(acls_want,
                                                                                   config_want))
                        else:
                            for config_have in have:
                                for acls_have in config_have.get('acls'):
                                    if acls_want.get('name') == acls_have.get('name'):
                                        commands.extend(self._clear_config(acls_want,
                                                                           config_want))
                else:
                    afi_want = config_want.get('afi')
                    for config_have in have:
                        if config_have.get('afi') == afi_want:
                            for acls_have in config_have.get('acls'):
                                commands.extend(self._clear_config(acls_have, config_want))
            # Split and arrange the config commands
            commands = self.split_set_cmd(commands)
        else:
            for config_have in have:
                for acls_have in config_have.get('acls'):
                    commands.extend(self._clear_config(acls_have, config_have))

        return commands

    def common_condition_check(self, want, have, acls_want, config_want, check, state='', acls_have=None):
        """ The command formatter from the generated command
        :param want: want config
        :param have: have config
        :param acls_want: acls want config
        :param config_want: want config list
        :param check: for same acls in want and have config, check=True
        :param state: operation state
        :rtype: A list
        :returns: commands generated from want n have config diff
        """
        commands = []

        if want.get('source') and want.get('destination') and have.get('source') and have.get('destination'):
            if want.get('destination') and have.get('destination') or \
                    want.get('source').get('address') and have.get('source'):
                if want.get('destination').get('address') == \
                        have.get('destination').get('address') and \
                        want.get('source').get('address') == \
                        have.get('source').get('address'):
                    cmd, change = self._set_config(want,
                                                   have,
                                                   acls_want,
                                                   config_want['afi'])
                    commands.extend(cmd)
                    check = True
                    if commands:
                        if state == 'replaced' or state == 'overridden':
                            commands.extend(self._clear_config(acls_want, config_want))
                elif want.get('destination').get('any') == \
                        have.get('destination').get('any') and \
                        want.get('source').get('address') == \
                        have.get('source').get('address') and \
                        want.get('destination').get('any'):
                    cmd, change = self._set_config(want,
                                                   have,
                                                   acls_want,
                                                   config_want['afi'])
                    commands.extend(cmd)
                    check = True
                    if commands:
                        if state == 'replaced' or state == 'overridden':
                            commands.extend(self._clear_config(acls_want, config_want))
                elif want.get('destination').get('address') == \
                        have.get('destination').get('address') and \
                        want.get('source').get('any') == have.get('source').get('any') and \
                        want.get('source').get('any'):
                    cmd, change = self._set_config(want,
                                                   have,
                                                   acls_want,
                                                   config_want['afi'])
                    commands.extend(cmd)
                    check = True
                    if commands:
                        if state == 'replaced' or state == 'overridden':
                            commands.extend(self._clear_config(acls_want, config_want))
                elif want.get('destination').get('any') == \
                        have.get('destination').get('any') and \
                        want.get('source').get('any') == have.get('source').get('any') and \
                        want.get('destination').get('any'):
                    cmd, change = self._set_config(want,
                                                   have,
                                                   acls_want,
                                                   config_want['afi'])
                    commands.extend(cmd)
                    check = True
                    if commands:
                        if state == 'replaced' or state == 'overridden':
                            commands.extend(self._clear_config(acls_want, config_want))
                elif acls_have and acls_have.get('acl_type') == 'standard':
                    check = True
                    if want.get('source') == have.get('source'):
                        cmd, change = self._set_config(want,
                                                       have,
                                                       acls_want,
                                                       config_want['afi'])
                        commands.extend(cmd)

        return commands, check

    def split_set_cmd(self, cmds):
        """ The command formatter from the generated command
        :param cmds: generated command
        :rtype: A list
        :returns: the formatted commands which is compliant and
        actually fired on the device
        """
        command = []

        def common_code(access_grant, cmd, command):
            cmd = cmd.split(access_grant)
            access_list = cmd[0].strip(' ')
            if access_list not in command:
                command.append(access_list)
            command_items = len(command)
            # get the last index of the list and push the trimmed cmd at the end of list
            index = command.index(access_list) + (command_items - command.index(access_list))
            cmd = access_grant + cmd[1]
            command.insert(index + 1, cmd)

        def sequence_common_code(sequence_index, each_list, command):
            # Command to split
            def join_list_to_str(temp_list, cmd=''):
                for item in temp_list:
                    cmd += item
                    cmd += ' '
                return cmd

            temp_list = each_list[:sequence_index]
            cmd = join_list_to_str(temp_list).rstrip(' ')
            if cmd not in command:
                command.append(cmd)
            temp_list = each_list[sequence_index:]
            cmd = join_list_to_str(temp_list).rstrip(' ')
            command.append(cmd)

        def grant_common_code(cmd_list, grant_type, command):
            index = cmd_list.index(grant_type)
            if 'extended' in each_list:
                if cmd_list.index('extended') == (index - 2):
                    common_code(grant_type, each, command)
                else:
                    sequence_common_code((index - 1), each_list, command)
            elif 'standard' in each_list:
                if cmd_list.index('standard') == (index - 2):
                    common_code(grant_type, each, command)
                else:
                    sequence_common_code((index - 1), each_list, command)
            elif 'ipv6' in each_list:
                if 'sequence' in each_list:
                    sequence_index = each_list.index('sequence')
                    sequence_common_code(sequence_index, each_list, command)
                else:
                    common_code(grant_type, each, command)
            return command

        for each in cmds:
            each_list = each.split(' ')
            if 'no' in each:
                if each_list.index('no') == 0:
                    command.append(each)
                else:
                    common_code('no', each, command)
            if 'deny' in each:
                grant_common_code(each_list, 'deny', command)
            if 'permit' in each:
                grant_common_code(each_list, 'permit', command)

        return command

    def source_dest_config(self, config, cmd, protocol_option):
        """ Function to populate source/destination address and port protocol options
        :param config: want and have diff config
        :param cmd: source/destination command
        :param protocol_option: source/destination protocol option
        :rtype: A list
        :returns: the commands generated based on input source/destination params
        """
        if 'ipv6' in cmd:
            address = config.get('address')
            host = config.get('host')
            if (address and '::' not in address) or (host and '::' not in host):
                self._module.fail_json(msg='Incorrect IPV6 address!')
        else:
            address = config.get('address')
            wildcard = config.get('wildcard_bits')
            host = config.get('host')
        any = config.get('any')
        if 'standard' in cmd and address and not wildcard:
            cmd = cmd + ' {0}'.format(address)
        elif address and wildcard:
            cmd = cmd + ' {0} {1}'.format(address, wildcard)
        elif host:
            cmd = cmd + ' host {0}'.format(host)
        if any:
            cmd = cmd + ' {0}'.format('any')
        port_protocol = config.get('port_protocol')
        if port_protocol and (protocol_option.get('tcp') or protocol_option.get('udp')):
            cmd = cmd + ' {0} {1}'.format(list(port_protocol)[0], list(port_protocol.values())[0])
        elif port_protocol and not (protocol_option.get('tcp') or protocol_option.get('udp')):
            self._module.fail_json(msg='Port Protocol option is valid only with TCP/UDP Protocol option!')

        return cmd

    def _set_config(self, want, have, acl_want, afi):
        """ Function that sets the acls config based on the want and have config
        :param want: want config
        :param have: have config
        :param acl_want: want acls config
        :param afi: acls afi type
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

        # Populate the config only when there's a diff b/w want and have config
        if diff:
            name = acl_want.get('name')
            if afi == 'ipv4':
                try:
                    name = int(name)
                    # If name is numbered acls
                    if name <= 99:
                        cmd = 'ip access-list standard {0}'.format(name)
                    elif name >= 100:
                        cmd = 'ip access-list extended {0}'.format(name)
                except ValueError:
                    # If name is named acls
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
            protocol = want.get('protocol')
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
                if protocol and protocol != po_key:
                    self._module.fail_json(msg='Protocol value cannot be different from Protocol option protocol value!')
                cmd = cmd + ' {0}'.format(po_key)
                if po.get('icmp'):
                    po_val = po.get('icmp')
                elif po.get('igmp'):
                    po_val = po.get('igmp')
                elif po.get('tcp'):
                    po_val = po.get('tcp')
            elif protocol:
                cmd = cmd + ' {0}'.format(protocol)
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

    def _clear_config(self, acls, config, sequence=''):
        """ Function that deletes the acls config based on the want and have config
        :param acls: acls config
        :param config: config
        :rtype: A list
        :returns: the commands generated based on input acls/config params
        """
        commands = []
        afi = config.get('afi')
        name = acls.get('name')
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
                acl_type = acls.get('acl_type')
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
