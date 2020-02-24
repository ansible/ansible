#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_acls class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.iosxr.utils.utils \
    import (
        flatten_dict,
        prefix_to_address_wildcard,
        is_ipv4_address
    )
from ansible.module_utils.network.common.utils \
    import (
        to_list,
        search_obj_in_list,
        dict_diff,
        remove_empties,
    )
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.iosxr.facts.facts import Facts


class Acls(ConfigBase):
    """
    The iosxr_acls class
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

    def get_acls_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data=data)
        acls_facts = facts["ansible_network_resources"].get("acls")
        if not acls_facts:
            return []
        return acls_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_acls_facts = self.get_acls_facts()
        else:
            existing_acls_facts = []

        if self.state in self.ACTION_STATES or self.state == "rendered":
            commands.extend(self.set_config(existing_acls_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result["changed"] = True

        if self.state in self.ACTION_STATES:
            result["commands"] = commands

        if self.state in self.ACTION_STATES or self.state == "gathered":
            changed_acls_facts = self.get_acls_facts()

        elif self.state == "rendered":
            result["rendered"] = commands

        elif self.state == "parsed":
            running_config = self._module.params["running_config"]
            if not running_config:
                self._module.fail_json(
                    msg="value of running_config parameter must not be empty for state parsed"
                )
            result["parsed"] = self.get_acls_facts(data=running_config)

        if self.state in self.ACTION_STATES:
            result["before"] = existing_acls_facts
            if result["changed"]:
                result["after"] = changed_acls_facts

        elif self.state == "gathered":
            result["gathered"] = changed_acls_facts

        result["warnings"] = warnings
        return result

    def set_config(self, existing_acls_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_acls_facts
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
        state = self._module.params['state']
        commands = []

        if state in ('overridden', 'merged', 'replaced',
                     'rendered') and not want:
            self._module.fail_json(
                msg='value of config parameter must not be empty for state {0}'
                .format(state))

        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))

        elif state == 'deleted':
            commands.extend(self._state_deleted(want, have))

        else:
            # Instead of passing entire want and have
            # list of dictionaries to the respective
            # _state_* methods we are passing the want
            # and have dictionaries per AFI
            for item in want:
                afi = item['afi']
                obj_in_have = search_obj_in_list(afi, have, key='afi')

                if state == 'merged' or self.state == 'rendered':
                    commands.extend(
                        self._state_merged(remove_empties(item), obj_in_have))

                elif state == 'replaced':
                    commands.extend(
                        self._state_replaced(remove_empties(item),
                                             obj_in_have))

        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for want_acl in want['acls']:
            have_acl = search_obj_in_list(want_acl['name'], have['acls']) or {}
            acl_updates = []

            for have_ace in have_acl.get('aces', []):
                want_ace = search_obj_in_list(have_ace['sequence'], want_acl['aces'], key='sequence') or {}
                if not want_ace:
                    acl_updates.append('no {0}'.format(have_ace['sequence']))

            for want_ace in want_acl.get('aces', []):
                have_ace = search_obj_in_list(want_ace.get('sequence'), have_acl.get('aces', []), key='sequence') or {}
                set_cmd = self._set_commands(want_ace, have_ace)
                if set_cmd:
                    acl_updates.append(set_cmd)

            if acl_updates:
                acl_updates.insert(0, '{0} access-list {1}'.format(want['afi'], want_acl['name']))
                commands.extend(acl_updates)

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        # Remove extraneous AFI that are present in config but not
        # specified in `want`
        for have_afi in have:
            want_afi = search_obj_in_list(have_afi['afi'], want, key='afi') or {}
            if not want_afi:
                for acl in have_afi.get('acls', []):
                    commands.append('no {0} access-list {1}'.format(have_afi['afi'], acl['name']))

        # First we remove the extraneous ACLs from the AFIs that
        # are present both in `want` and in `have` and then
        # we call `_state_replaced` to update the ACEs within those ACLs
        for want_afi in want:
            want_afi = remove_empties(want_afi)
            have_afi = search_obj_in_list(want_afi['afi'], have, key='afi') or {}
            if have_afi:
                for have_acl in have_afi.get('acls', []):
                    want_acl = search_obj_in_list(have_acl['name'], want_afi.get('acls', [])) or {}
                    if not want_acl:
                        commands.append('no {0} access-list {1}'.format(have_afi['afi'], have_acl['name']))

            commands.extend(self._state_replaced(want_afi, have_afi))

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        if not have:
            have = {}

        for want_acl in want['acls']:
            have_acl = search_obj_in_list(want_acl['name'], have.get('acls', {})) or {}

            acl_updates = []
            for want_ace in want_acl['aces']:
                have_ace = search_obj_in_list(want_ace.get('sequence'), have_acl.get('aces', []), key='sequence') or {}
                set_cmd = self._set_commands(want_ace, have_ace)
                if set_cmd:
                    acl_updates.append(set_cmd)

            if acl_updates:
                acl_updates.insert(0, '{0} access-list {1}'.format(want['afi'], want_acl['name']))
                commands.extend(acl_updates)

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if not want:
            want = [{'afi': 'ipv4'}, {'afi': 'ipv6'}]

        for item in want:
            item = remove_empties(item)
            have_item = search_obj_in_list(item['afi'], have, key='afi') or {}
            if 'acls' not in item:
                if have_item:
                    for acl in have_item['acls']:
                        commands.append('no {0} access-list {1}'.format(have_item['afi'], acl['name']))
            else:
                for want_acl in item['acls']:
                    have_acl = search_obj_in_list(want_acl['name'], have_item.get('acls', [])) or {}
                    if have_acl:
                        if 'aces' not in want_acl:
                            commands.append('no {0} access-list {1}'.format(have_item['afi'], have_acl['name']))
                        else:
                            acl_updates = []
                            for want_ace in want_acl['aces']:
                                have_ace = search_obj_in_list(want_ace.get('sequence'), have_acl.get('aces', []), key='sequence') or {}
                                if have_ace:
                                    acl_updates.append('no {0}'.format(have_ace['sequence']))

                            if acl_updates:
                                acl_updates.insert(0, '{0} access-list {1}'.format(have_item['afi'], have_acl['name']))
                                commands.extend(acl_updates)

        return commands

    def _compute_commands(self, want_ace):
        """This command creates an ACE line from an ACE dictionary

        :rtype: A string
        :returns: An ACE generated from a structured ACE dictionary
        """
        def __compute_src_dest(dir_dict):
            cmd = ""
            if 'any' in dir_dict:
                cmd += 'any '
            elif 'host' in dir_dict:
                cmd += 'host {0} '.format(dir_dict['host'])
            elif 'prefix' in dir_dict:
                cmd += '{0} '.format(dir_dict['prefix'])
            else:
                cmd += '{0} {1} '.format(dir_dict['address'],
                                         dir_dict['wildcard_bits'])

            if 'port_protocol' in dir_dict:
                protocol_range = dir_dict['port_protocol'].get('range')
                if protocol_range:
                    cmd += 'range {0} {1} '.format(protocol_range['start'],
                                                   protocol_range['end'])
                else:
                    for key, value in iteritems(dir_dict['port_protocol']):
                        cmd += '{0} {1} '.format(key, value)

            return cmd

        def __compute_protocol_options(protocol_dict):
            cmd = ""
            for value in protocol_options.values():
                for subkey, subvalue in iteritems(value):
                    if subvalue:
                        cmd += '{0} '.format(subkey.replace('_', '-'))
            return cmd

        def __compute_match_options(want_ace):
            cmd = ""

            if 'precedence' in want_ace:
                cmd += 'precedence {0} '.format(want_ace['precedence'])

            for x in ['dscp', 'packet_length', 'ttl']:
                if x in want_ace:
                    opt_range = want_ace[x].get('range')
                    if opt_range:
                        cmd += '{0} range {1} {2} '.format(
                            x.replace('_', '-'), opt_range['start'],
                            opt_range['end'])
                    else:
                        for key, value in iteritems(want_ace[x]):
                            cmd += '{0} {1} {2} '.format(
                                x.replace('_', '-'), key, value)

            for x in ('authen', 'capture', 'fragments', 'routing', 'log',
                      'log_input', 'icmp_off', 'destopts', 'hop_by_hop'):
                if x in want_ace:
                    cmd += '{0} '.format(x.replace('_', '-'))

            return cmd

        cmd = ""
        if 'sequence' in want_ace:
            cmd += '{0} '.format(want_ace['sequence'])

        if 'remark' in want_ace:
            cmd += 'remark {0}'.format(want_ace['remark'])

        elif 'line' in want_ace:
            cmd += want_ace['line']

        else:
            cmd += '{0} '.format(want_ace['grant'])
            if 'protocol' in want_ace:
                cmd += '{0} '.format(want_ace['protocol'])

            cmd += __compute_src_dest(want_ace['source'])
            cmd += __compute_src_dest(want_ace['destination'])

            protocol_options = want_ace.get('protocol_options', {})
            if protocol_options:
                cmd += __compute_protocol_options(protocol_options)

            cmd += __compute_match_options(want_ace)

        return cmd.strip()

    def _set_commands(self, want_ace, have_ace):
        """A helped method that checks if there is
           a delta between the `have_ace` and `want_ace`.
           If there is a delta then it calls `_compute_commands`
           to create the ACE line.

        :rtype: A string
        :returns: An ACE generated from a structured ACE dictionary
                  via a call to `_compute_commands`
        """

        if 'line' in want_ace:
            if want_ace['line'] != have_ace.get('line'):
                return self._compute_commands(want_ace)

        else:
            if ('prefix' in want_ace.get('source', {})) or ('prefix' in want_ace.get('destination', {})):
                self._prepare_for_diff(want_ace)

            protocol_opt_delta = {}
            delta = dict_diff(have_ace, want_ace)

            # `dict_diff` doesn't work properly for `protocol_options` diff,
            # so we need to handle it separately
            if want_ace.get('protocol_options', {}):
                protocol_opt_delta = set(flatten_dict(have_ace.get('protocol_options', {}))) ^ \
                    set(flatten_dict(want_ace.get('protocol_options', {})))

            if delta or protocol_opt_delta:
                want_ace = self._dict_merge(have_ace, want_ace)
                return self._compute_commands(want_ace)

    def _prepare_for_diff(self, ace):
        """This method prepares the want ace dict
           for diff calculation against the have ace dict.

        :param ace: The want ace to prepare for diff calculation
        """
        # Convert prefixes to "address wildcard bits" format for IPv4 addresses
        # Not valid for IPv6 addresses because those can only be specified as prefixes
        # and are always rendered in running-config as prefixes too
        for x in ['source', 'destination']:
            prefix = ace.get(x, {}).get('prefix')
            if prefix and is_ipv4_address(prefix):
                del ace[x]['prefix']
                ace[x]['address'], ace[x]['wildcard_bits'] = prefix_to_address_wildcard(prefix)

    def _dict_merge(self, have_ace, want_ace):
        for x in want_ace:
            have_ace[x] = want_ace[x]
        return have_ace
