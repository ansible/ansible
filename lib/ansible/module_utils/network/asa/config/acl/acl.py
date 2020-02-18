#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The asa_acl class
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
from ansible.module_utils.network.asa.facts.facts import Facts
from ansible.module_utils.network.common.utils import remove_empties
from ansible.module_utils.network.asa.utils.utils import new_dict_to_set


class Acl(ConfigBase):
    """
    The asa_acl class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'acl',
    ]

    def __init__(self, module):
        super(Acl, self).__init__(module)

    def get_acl_facts(self):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        acl_facts = facts['ansible_network_resources'].get('acl')
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
                self._module.fail_json(msg="Value of running_config parameter must not be empty for state parsed")
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
                                    cmd, check = self.common_condition_check(ace_want,
                                                                             ace_have,
                                                                             acls_want,
                                                                             config_want,
                                                                             check,
                                                                             "replaced")
                                    if not cmd:
                                        # Delete the configured aces which are not in want
                                        temp = self._clear_config(ace_have, acls_have)
                                        commands.extend(temp)
                            if check:
                                break
                        if check:
                            break
                    if not check:
                        # For configuring any non-existing want config
                        ace_want = remove_empties(ace_want)
                        commands.extend(self._set_config(ace_want,
                                                         {},
                                                         acls_want))
        # Arranging the cmds suct that all delete cmds are fired before all set cmds
        # and reversing the negate/no access-list as otherwise if deleted from top the
        # next ace takes the line position of deleted ace from top and results in unexpected output
        commands = [each for each in commands if 'no' in each][::-1] + [each for each in commands if 'no' not in each]

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
                                    cmd, check = self.common_condition_check(ace_want,
                                                                             ace_have,
                                                                             acls_want,
                                                                             config_want,
                                                                             check,
                                                                             "overridden")
                                    if not cmd:
                                        # Delete the configured aces which are not in want
                                        temp = self._clear_config(ace_have, acls_have)
                                        commands.extend(temp)
                                    if check:
                                        # Delete all the have acls that are present in want post configuration
                                        # and the only want acls left will be new acls which is not in have and
                                        # need to be configured
                                        del config_want.get('acls')[count]
                                else:
                                    count += 1
                        if check:
                            break
                    if not check:
                        # Delete the config not present in want config
                        temp = self._clear_config(ace_have, acls_have)
                        if temp and temp[0] not in commands:
                            commands.extend(temp)

        # For configuring any non-existing want config
        for config_want in temp_want:
            for acls_want in config_want.get('acls'):
                for ace_want in acls_want.get('aces'):
                    ace_want = remove_empties(ace_want)
                    commands.extend(self._set_config(ace_want,
                                                     {},
                                                     acls_want))

        # Arranging the cmds suct that all delete cmds are fired before all set cmds
        # and reversing the negate/no access-list as otherwise if deleted from top the
        # next ace takes the line position of deleted ace from top and results in unexpected output
        commands = [each for each in commands if 'no' in each][::-1] + [each for each in commands if 'no' not in each]

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
                                        ace_want.get('line') == ace_have.get('line'):
                                    ace_want = remove_empties(ace_want)
                                    cmd = self._set_config(ace_want,
                                                           ace_have,
                                                           acls_want)
                                    commands = self.add_config_cmd(cmd, commands)
                                    check = True
                                if not ace_want.get('line'):
                                    if acls_want.get('name') == acls_have.get('name'):
                                        ace_want = remove_empties(ace_want)
                                        cmd, check = self.common_condition_check(ace_want,
                                                                                 ace_have,
                                                                                 acls_want,
                                                                                 config_want,
                                                                                 check,
                                                                                 acls_have)
                                        if acls_have.get('acl_type') == 'standard':
                                            check = True
                                        commands = self.add_config_cmd(cmd, commands)
                            if check:
                                break
                        if check:
                            break
                    if not check:
                        # For configuring any non-existing want config
                        ace_want = remove_empties(ace_want)
                        cmd = self._set_config(ace_want,
                                               {},
                                               acls_want)
                        commands = self.add_config_cmd(cmd, commands)

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
                for acls_want in config_want.get('acls'):
                    for ace_want in acls_want.get('aces'):
                        for config_have in have:
                            for acls_have in config_have.get('acls'):
                                for ace_have in acls_have.get('aces'):
                                    if acls_want.get('name') == acls_have.get('name') and \
                                            ace_want.get('line') == ace_have.get('line'):
                                        commands.extend(self._clear_config(ace_have, acls_have))
        else:
            for config_have in have:
                for acls_have in config_have.get('acls'):
                    for ace_have in acls_have.get('aces'):
                        commands.extend(self._clear_config(ace_have, acls_have))
        # Reversing the negate/no access-list as otherwise if deleted from top the
        # next ace takes the line position of deleted ace from top and only one ace
        # will be deleted instead of expected aces and results in unexpected output
        commands = commands[::-1]

        return commands

    def add_config_cmd(self, cmd, commands):
        if cmd and cmd[0] not in commands:
            commands.extend(cmd)
        return commands

    def common_condition_check(self, ace_want, ace_have, acls_want, config_want, check, state=''):
        """ The command formatter from the generated command
        :param ace_want: ace want config
        :param ace_have: ace have config
        :param acls_want: acl want config
        :param config_want: want config list
        :param check: for same acl in want and have config, check=True
        :param state: operation state
        :rtype: A list
        :returns: commands generated from want n have config diff
        """
        commands = []
        if ace_want.get('destination') and ace_have.get('destination') or \
                ace_want.get('source').get('address') and ace_have.get('source'):
            if ace_want.get('destination').get('address') == \
                    ace_have.get('destination').get('address') and \
                    ace_want.get('source').get('address') == \
                    ace_have.get('source').get('address') and \
                    ace_want.get('protocol_options') == \
                    ace_have.get('protocol_options'):
                cmd = self._set_config(ace_want,
                                       ace_have,
                                       acls_want)
                commands.extend(cmd)
                check = True
                if commands:
                    if state == 'replaced' or state == 'overridden':
                        commands.extend(self._clear_config(ace_want, acls_want))
            elif ace_want.get('destination').get('any') == \
                    ace_have.get('destination').get('any') and \
                    ace_want.get('source').get('address') == \
                    ace_have.get('source').get('address') and \
                    ace_want.get('destination').get('any') and \
                    ace_want.get('protocol_options') == \
                    ace_have.get('protocol_options'):
                cmd = self._set_config(ace_want,
                                       ace_have,
                                       acls_want)
                commands.extend(cmd)
                check = True
                if commands:
                    if state == 'replaced' or state == 'overridden':
                        commands.extend(self._clear_config(ace_want, acls_want))
            elif ace_want.get('destination').get('address') == \
                    ace_have.get('destination').get('address') and \
                    ace_want.get('source').get('any') == ace_have.get('source').get('any') and \
                    ace_want.get('source').get('any') and \
                    ace_want.get('protocol_options') == \
                    ace_have.get('protocol_options'):
                cmd = self._set_config(ace_want,
                                       ace_have,
                                       acls_want)
                commands.extend(cmd)
                check = True
                if commands:
                    if state == 'replaced' or state == 'overridden':
                        commands.extend(self._clear_config(ace_want, acls_want))
            elif ace_want.get('destination').get('any') == \
                    ace_have.get('destination').get('any') and \
                    ace_want.get('source').get('any') == ace_have.get('source').get('any') and \
                    ace_want.get('destination').get('any') and \
                    ace_want.get('protocol_options') == \
                    ace_have.get('protocol_options'):
                cmd = self._set_config(ace_want,
                                       ace_have,
                                       acls_want)
                commands.extend(cmd)
                check = True
                if commands:
                    if state == 'replaced' or state == 'overridden':
                        commands.extend(self._clear_config(ace_want, acls_want))

        return commands, check

    def source_dest_config(self, config, cmd, protocol_option):
        """ Function to populate source/destination address and port protocol options
        :param config: want and have diff config
        :param cmd: source/destination command
        :param protocol_option: source/destination protocol option
        :rtype: A list
        :returns: the commands generated based on input source/destination params
        """
        address = config.get('address')
        netmask = config.get('netmask')
        any = config.get('any')
        if address and netmask:
            cmd = cmd + ' {0} {1}'.format(address, netmask)
        elif address:
            cmd = cmd + ' {0}'.format(address.lower())
        if any:
            cmd = cmd + ' {0}'.format('any')
        port_protocol = config.get('port_protocol')
        if port_protocol and (protocol_option.get('tcp') or protocol_option.get('udp')):
            cmd = cmd + ' {0} {1}'.format(list(port_protocol)[0], list(port_protocol.values())[0])
        elif port_protocol and not (protocol_option.get('tcp') or protocol_option.get('udp')):
            self._module.fail_json(msg="Port Protocol option is valid only with TCP/UDP Protocol option!")

        return cmd

    def common_config_cmd(self, want, acl_want, cmd, type=''):
        """ Common Function that prepares the acls config cmd based on the want config
        :param want: want ace config
        :param acl_want: want acl config
        :param cmd: cmd passed
        :rtype: string
        :returns: the commands generated based on input ace want/acl want params
        """
        line = want.get('line')
        if line:
            cmd = cmd + ' line {0}'.format(line)
        else:
            if type == 'clear':
                self._module.fail_json(msg="For Delete operation LINE param is required!")
        acl_type = acl_want.get('acl_type')
        if acl_type:
            cmd = cmd + ' {0}'.format(acl_type)
        # Get all of aces option values from diff dict
        grant = want.get('grant')
        source = want.get('source')
        destination = want.get('destination')
        po = want.get('protocol_options')
        log = want.get('log')
        time_range = want.get('time_range')
        inactive = want.get('inactive')

        if grant:
            cmd = cmd + ' {0}'.format(grant)
        po_val = None
        if po and isinstance(po, dict):
            po_key = list(po)[0]
            cmd = cmd + ' {0}'.format(po_key)
            if po.get('icmp'):
                po_val = po.get('icmp')
            elif po.get('icmp6'):
                po_val = po.get('igmp')
        if source:
            cmd = self.source_dest_config(source, cmd, po)
        if destination:
            cmd = self.source_dest_config(destination, cmd, po)
        if po_val and list(po_val)[0] != 'set':
            cmd = cmd + ' {0}'.format(list(po_val)[0])
        if log:
            cmd = cmd + ' log {0}'.format(log)
        if time_range:
            cmd = cmd + ' time-range {0}'.format(time_range)
        if inactive:
            cmd = cmd + ' inactive'

        return cmd

    def _set_config(self, want, have, acl_want):
        """ Function that sets the acls config based on the want and have config
        :param want: want config
        :param have: have config
        :param acl_want: want acl config
        :param afi: acl afi type
        :rtype: A list
        :returns: the commands generated based on input want/have params
        """
        commands = []
        # To change the want IPV6 address to lower case, as Cisco ASA configures the IPV6
        # access-list always in Lowercase even if the input is given in Uppercase
        if want.get('destination') and want.get('destination').get('address') and \
                ':' in want.get('destination').get('address'):
            want['destination']['address'] = want.get('destination').get('address').lower()
        # Convert the want and have dict to its respective set for taking the set diff
        want_set = set()
        have_set = set()
        new_dict_to_set(want, [], want_set)
        new_dict_to_set(have, [], have_set)
        diff = want_set - have_set

        # Populate the config only when there's a diff b/w want and have config
        if diff:
            name = acl_want.get('name')
            cmd = 'access-list {0}'.format(name)
            cmd = self.common_config_cmd(want, acl_want, cmd)

            commands.append(cmd)

        return commands

    def _clear_config(self, ace, acl):
        """ Function that deletes the acl config based on the want and have config
        :param acl: acl config
        :param config: config
        :rtype: A list
        :returns: the commands generated based on input acl/config params
        """
        commands = []
        name = acl.get('name')
        cmd = 'no access-list {0}'.format(name)
        cmd = self.common_config_cmd(ace, acl, cmd, 'clear')

        commands.append(cmd)

        return commands
