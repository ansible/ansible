#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_firewall_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff, remove_empties, search_obj_in_list
from ansible.module_utils.network.vyos.facts.facts import Facts


class Firewall_interfaces(ConfigBase):
    """
    The vyos_firewall_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'firewall_interfaces',
    ]

    def __init__(self, module):
        super(Firewall_interfaces, self).__init__(module)

    def get_firewall_interfaces_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources, data=data)
        firewall_interfaces_facts = facts['ansible_network_resources'].get('firewall_interfaces')
        if not firewall_interfaces_facts:
            return []
        return firewall_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_firewall_interfaces_facts = self.get_firewall_interfaces_facts()
        else:
            existing_firewall_interfaces_facts = []

        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_firewall_interfaces_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True

        if self.state in self.ACTION_STATES:
            result['commands'] = commands

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_firewall_interfaces_facts = self.get_firewall_interfaces_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            running_config = self._module.params['running_config']
            if not running_config:
                self._module.fail_json(
                    msg="value of running_config parameter must not be empty for state parsed"
                )
            result['parsed'] = self.get_firewall_interfaces_facts(data=running_config)
        else:
            changed_firewall_interfaces_facts = []

        if self.state in self.ACTION_STATES:
            result['before'] = existing_firewall_interfaces_facts
            if result['changed']:
                result['after'] = changed_firewall_interfaces_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_firewall_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_firewall_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_firewall_interfaces_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, w, h):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if self.state in ('merged', 'replaced', 'overridden', 'rendered') and not w:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(self.state))
        if self.state == 'overridden':
            commands.extend(self._state_overridden(w, h))
        elif self.state == 'deleted':
            commands.extend(self._state_deleted(w, h))
        elif w:
            if self.state == 'merged' or self.state == 'rendered':
                commands.extend(self._state_merged(w, h))
            elif self.state == 'replaced':
                commands.extend(self._state_replaced(w, h))
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if have:
            for h in have:
                w = search_obj_in_list(h['name'], want)
                commands.extend(self._render_access_rules(h, w, opr=False))
        commands.extend(self._state_merged(want, have))
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if have:
            for h_ar in have:
                w_ar = search_obj_in_list(h_ar['name'], want)
                if not w_ar and 'access_rules' in h_ar:
                    commands.append(self._compute_command(name=h_ar['name'], opr=False))
                else:
                    h_rules = h_ar.get('access_rules') or []
                    key = 'direction'
                    if w_ar:
                        w_rules = w_ar.get('access_rules') or []
                        if not w_rules and h_rules:
                            commands.append(self._compute_command(name=h_ar['name'], opr=False))
                    if h_rules:
                        for h_rule in h_rules:
                            w_rule = search_obj_in_list(h_rule['afi'], w_rules, key='afi')
                            have_rules = h_rule.get('rules') or []
                            if w_rule:
                                want_rules = w_rule.get('rules') or []
                            for h in have_rules:
                                if key in h:
                                    w = search_obj_in_list(h[key], want_rules, key=key)
                                    if not w or key not in w or ('name' in h and w and 'name' not in w):
                                        commands.append(
                                            self._compute_command(
                                                afi=h_rule['afi'], name=h_ar['name'], attrib=h[key], opr=False
                                            )
                                        )

        commands.extend(self._state_merged(want, have))
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for w in want:
            h = search_obj_in_list(w['name'], have)
            commands.extend(self._render_access_rules(w, h))
        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if want:
            for w in want:
                h = search_obj_in_list(w['name'], have)
                if h and 'access_rules' in h:
                    commands.extend(self._delete_access_rules(w, h, opr=False))
        elif have:
            for h in have:
                if 'access_rules' in h:
                    commands.append(self._compute_command(name=h['name'], opr=False))
        return commands

    def _delete_access_rules(self, want, have, opr=False):
        """
        This function forms the delete commands based on the 'opr' type
        for 'access_rules' attributes.
        :param want: desired config.
        :param have: target config.
        :param opr: True/False.
        :return: generated commands list.
        """
        commands = []
        h_rules = {}
        w_rs = deepcopy(remove_empties(want))
        w_rules = w_rs.get('access_rules') or []
        if have:
            h_rs = deepcopy(remove_empties(have))
            h_rules = h_rs.get('access_rules') or []

        # if all firewall config needed to be deleted for specific interface
        # when operation is delete.
        if not w_rules and h_rules:
            commands.append(self._compute_command(name=want['name'], opr=opr))
        if w_rules:
            for w in w_rules:
                h = search_obj_in_list(w['afi'], h_rules, key='afi')
                commands.extend(self._delete_rules(want['name'], w, h))
        return commands

    def _delete_rules(self, name, want, have, opr=False):
        """
        This function forms the delete commands based on the 'opr' type
        for rules attributes.
        :param name: interface id/name.
        :param want: desired config.
        :param have: target config.
        :param opr: True/False.
        :return: generated commands list.
        """
        commands = []
        h_rules = []
        key = 'direction'
        w_rules = want.get('rules') or []
        if have:
            h_rules = have.get('rules') or []
        # when rule set needed to be removed on
        # (inbound|outbound|local interface)
        if h_rules and not w_rules:
            for h in h_rules:
                if key in h:
                    commands.append(self._compute_command(afi=want['afi'], name=name, attrib=h[key], opr=opr))
        for w in w_rules:
            h = search_obj_in_list(w[key], h_rules, key=key)
            if key in w and h and key in h and 'name' in w and 'name' in h and w['name'] == h['name']:
                commands.append(self._compute_command(
                    afi=want['afi'],
                    name=name,
                    attrib=w[key],
                    value=w['name'],
                    opr=opr)
                )
        return commands

    def _render_access_rules(self, want, have, opr=True):
        """
        This function forms the set/delete commands based on the 'opr' type
        for 'access_rules' attributes.
        :param want: desired config.
        :param have: target config.
        :param opr: True/False.
        :return: generated commands list.
        """
        commands = []
        h_rules = {}
        w_rs = deepcopy(remove_empties(want))
        w_rules = w_rs.get('access_rules') or []
        if have:
            h_rs = deepcopy(remove_empties(have))
            h_rules = h_rs.get('access_rules') or []
        if w_rules:
            for w in w_rules:
                h = search_obj_in_list(w['afi'], h_rules, key='afi')
                commands.extend(self._render_rules(want['name'], w, h, opr))
        return commands

    def _render_rules(self, name, want, have, opr=True):
        """
        This function forms the set/delete commands based on the 'opr' type
        for rules attributes.
        :param name: interface id/name.
        :param want: desired config.
        :param have: target config.
        :param opr: True/False.
        :return: generated commands list.
        """
        commands = []
        h_rules = []
        key = 'direction'
        w_rules = want.get('rules') or []
        if have:
            h_rules = have.get('rules') or []
        for w in w_rules:
            h = search_obj_in_list(w[key], h_rules, key=key)
            if key in w:
                if opr:
                    if 'name' in w and not (h and h[key] == w[key] and h['name'] == w['name']):
                        commands.append(self._compute_command(afi=want['afi'], name=name, attrib=w[key], value=w['name']))
                    elif not (h and key in h):
                        commands.append(self._compute_command(afi=want['afi'], name=name, attrib=w[key]))
                elif not opr:
                    if not h or key not in h or ('name' in w and h and 'name' not in h):
                        commands.append(self._compute_command(afi=want['afi'], name=name, attrib=w[key], opr=opr))
        return commands

    def _compute_command(self, afi=None, name=None, attrib=None, value=None, opr=True):
        """
        This function construct the add/delete command based on passed attributes.
        :param afi:  address type.
        :param name: interface name.
        :param attrib: attribute name.
        :param value: attribute value.
        :param opr: operation flag.
        :return: generated command.
        """
        if not opr:
            cmd = 'delete interfaces ethernet' + ' ' + name + ' firewall'
        else:
            cmd = 'set interfaces ethernet' + ' ' + name + ' firewall'
        if attrib:
            cmd += (' ' + attrib)
        if afi:
            cmd += ' ' + self._get_fw_type(afi)
        if value:
            cmd += (" '" + str(value) + "'")
        return cmd

    def _get_fw_type(self, afi):
        """
        This function returns the firewall rule-set type based on IP address.
        :param afi: address type
        :return: rule-set type.
        """
        return 'ipv6-name' if afi == 'ipv6' else 'name'
