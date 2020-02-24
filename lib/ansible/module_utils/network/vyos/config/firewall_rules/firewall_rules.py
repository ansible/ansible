#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_firewall_rules class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.vyos.utils.utils import list_diff_want_only


class Firewall_rules(ConfigBase):
    """
    The vyos_firewall_rules class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'firewall_rules',
    ]

    def __init__(self, module):
        super(Firewall_rules, self).__init__(module)

    def get_firewall_rules_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources, data=data)
        firewall_rules_facts = facts['ansible_network_resources'].get('firewall_rules')
        if not firewall_rules_facts:
            return []
        return firewall_rules_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_firewall_rules_facts = self.get_firewall_rules_facts()
        else:
            existing_firewall_rules_facts = []

        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_firewall_rules_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True

        if self.state in self.ACTION_STATES:
            result['commands'] = commands

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_firewall_rules_facts = self.get_firewall_rules_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            running_config = self._module.params['running_config']
            if not running_config:
                self._module.fail_json(
                    msg="value of running_config parameter must not be empty for state parsed"
                )
            result['parsed'] = self.get_firewall_rules_facts(data=running_config)
        else:
            changed_firewall_rules_facts = []

        if self.state in self.ACTION_STATES:
            result['before'] = existing_firewall_rules_facts
            if result['changed']:
                result['after'] = changed_firewall_rules_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_firewall_rules_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_firewall_rules_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_firewall_rules_facts
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
                r_sets = self._get_r_sets(h)
                for rs in r_sets:
                    w = self.search_r_sets_in_have(want, rs['name'], 'r_list')
                    commands.extend(self._add_r_sets(h['afi'], rs, w, opr=False))
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
            for h in have:
                r_sets = self._get_r_sets(h)
                for rs in r_sets:
                    w = self.search_r_sets_in_have(want, rs['name'], 'r_list')
                    if not w:
                        commands.append(self._compute_command(h['afi'], rs['name'], remove=True))
                    else:
                        commands.extend(self._add_r_sets(h['afi'], rs, w, opr=False))
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
            r_sets = self._get_r_sets(w)
            for rs in r_sets:
                h = self.search_r_sets_in_have(have, rs['name'], 'r_list')
                commands.extend(self._add_r_sets(w['afi'], rs, h))
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
                r_sets = self._get_r_sets(w)
                if r_sets:
                    for rs in r_sets:
                        h = self.search_r_sets_in_have(have, rs['name'], 'r_list')
                        if h:
                            w_rules = rs.get('rules') or []
                            h_rules = h.get('rules') or []
                            if w_rules and h_rules:
                                for rule in w_rules:
                                    if self.search_r_sets_in_have(h_rules, rule['number'], 'rules'):
                                        commands.append(self._add_r_base_attrib(w['afi'], rs['name'], 'number', rule, opr=False))
                            else:
                                commands.append(self._compute_command(w['afi'], h['name'], remove=True))
                elif have:
                    for h in have:
                        if h['afi'] == w['afi']:
                            commands.append(self._compute_command(w['afi'], remove=True))
        elif have:
            for h in have:
                r_sets = self._get_r_sets(h)
                if r_sets:
                    commands.append(self._compute_command(afi=h['afi'], remove=True))
        return commands

    def _add_r_sets(self, afi, want, have, opr=True):
        """
        This function forms the set/delete commands based on the 'opr' type
        for rule-sets attributes.
        :param afi: address type.
        :param want: desired config.
        :param have: target config.
        :param opr: True/False.
        :return: generated commands list.
        """
        commands = []
        l_set = ('description',
                 'default_action',
                 'enable_default_log')
        h_rs = {}
        h_rules = {}
        w_rs = deepcopy(remove_empties(want))
        w_rules = w_rs.pop('rules', None)
        if have:
            h_rs = deepcopy(remove_empties(have))
            h_rules = h_rs.pop('rules', None)
        if w_rs:
            for key, val in iteritems(w_rs):
                if opr and key in l_set and not (h_rs and self._is_w_same(w_rs, h_rs, key)):
                    if key == 'enable_default_log':
                        if val and (not h_rs or key not in h_rs or not h_rs[key]):
                            commands.append(self._add_rs_base_attrib(afi, want['name'], key, w_rs))
                    else:
                        commands.append(self._add_rs_base_attrib(afi, want['name'], key, w_rs))
                elif not opr and key in l_set:
                    if key == 'enable_default_log' and val and h_rs and (key not in h_rs or not h_rs[key]):
                        commands.append(self._add_rs_base_attrib(afi, want['name'], key, w_rs, opr))
                    elif not (h_rs and self._in_target(h_rs, key)):
                        commands.append(self._add_rs_base_attrib(afi, want['name'], key, w_rs, opr))
            commands.extend(self._add_rules(afi, want['name'], w_rules, h_rules, opr))
        if h_rules:
            have['rules'] = h_rules
        if w_rules:
            want['rules'] = w_rules
        return commands

    def _add_rules(self, afi, name, w_rules, h_rules, opr=True):
        """
        This function forms the set/delete commands based on the 'opr' type
        for rules attributes.
        :param want: desired config.
        :param have: target config.
        :return: generated commands list.
        """
        commands = []
        l_set = ('ipsec',
                 'action',
                 'number',
                 'protocol',
                 'fragment',
                 'disabled',
                 'description')
        if w_rules:
            for w in w_rules:
                cmd = self._compute_command(afi, name, w['number'], opr=opr)
                h = self.search_r_sets_in_have(h_rules, w['number'], type='rules')
                for key, val in iteritems(w):
                    if val:
                        if opr and key in l_set and not (h and self._is_w_same(w, h, key)):
                            if key == 'disabled':
                                if not (not val and (not h or key not in h or not h[key])):
                                    commands.append(self._add_r_base_attrib(afi, name, key, w))
                            else:
                                commands.append(self._add_r_base_attrib(afi, name, key, w))
                        elif not opr:
                            if key == 'number' and self._is_del(l_set, h):
                                commands.append(self._add_r_base_attrib(afi, name, key, w, opr=opr))
                                continue
                            elif key == 'disabled' and val and h and (key not in h or not h[key]):
                                commands.append(self._add_r_base_attrib(afi, name, key, w, opr=opr))
                            elif key in l_set and not (h and self._in_target(h, key)) and not self._is_del(l_set, h):
                                commands.append(self._add_r_base_attrib(afi, name, key, w, opr=opr))
                        elif key == 'p2p':
                            commands.extend(self._add_p2p(key, w, h, cmd, opr))
                        elif key == 'tcp':
                            commands.extend(self._add_tcp(key, w, h, cmd, opr))
                        elif key == 'time':
                            commands.extend(self._add_time(key, w, h, cmd, opr))
                        elif key == 'icmp':
                            commands.extend(self._add_icmp(key, w, h, cmd, opr))
                        elif key == 'state':
                            commands.extend(self._add_state(key, w, h, cmd, opr))
                        elif key == 'limit':
                            commands.extend(self._add_limit(key, w, h, cmd, opr))
                        elif key == 'recent':
                            commands.extend(self._add_recent(key, w, h, cmd, opr))
                        elif key == 'destination' or key == 'source':
                            commands.extend(self._add_src_or_dest(key, w, h, cmd, opr))
        return commands

    def _add_p2p(self, attr, w, h, cmd, opr):
        """
        This function forms the set/delete commands based on the 'opr' type
        for p2p applications attributes.
        :param want: desired config.
        :param have: target config.
        :return: generated commands list.
        """
        commands = []
        have = []
        if w:
            want = w.get(attr) or []
        if h:
            have = h.get(attr) or []
        if want:
            if opr:
                applications = list_diff_want_only(want, have)
                for app in applications:
                    commands.append(cmd + (' ' + attr + ' ' + app['application']))
            elif not opr and have:
                applications = list_diff_want_only(want, have)
                for app in applications:
                    commands.append(cmd + (' ' + attr + ' ' + app['application']))
        return commands

    def _add_state(self, attr, w, h, cmd, opr):
        """
        This function forms the command for 'state' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: base config.
        :param h: target config.
        :param cmd: commands to be prepend.
        :return: generated list of commands.
        """
        h_state = {}
        commands = []
        l_set = ('new',
                 'invalid',
                 'related',
                 'established')
        if w[attr]:
            if h and attr in h.keys():
                h_state = h.get(attr) or {}
            for item, val in iteritems(w[attr]):
                if opr and item in l_set and not (h_state and self._is_w_same(w[attr], h_state, item)):
                    commands.append(cmd + (' ' + attr + ' ' + item + ' ' + self._bool_to_str(val)))
                elif not opr and item in l_set and not (h_state and self._in_target(h_state, item)):
                    commands.append(cmd + (' ' + attr + ' ' + item))
        return commands

    def _add_recent(self, attr, w, h, cmd, opr):
        """
        This function forms the command for 'recent' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: base config.
        :param h: target config.
        :param cmd: commands to be prepend.
        :return: generated list of commands.
        """
        commands = []
        h_recent = {}
        l_set = ('count', 'time')
        if w[attr]:
            if h and attr in h.keys():
                h_recent = h.get(attr) or {}
            for item, val in iteritems(w[attr]):
                if opr and item in l_set and not (h_recent and self._is_w_same(w[attr], h_recent, item)):
                    commands.append(cmd + (' ' + attr + ' ' + item + ' ' + str(val)))
                elif not opr and item in l_set and not (h_recent and self._in_target(h_recent, item)):
                    commands.append(cmd + (' ' + attr + ' ' + item))
        return commands

    def _add_icmp(self, attr, w, h, cmd, opr):
        """
        This function forms the commands for 'icmp' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: base config.
        :param h: target config.
        :param cmd: commands to be prepend.
        :return: generated list of commands.
        """
        commands = []
        h_icmp = {}
        l_set = ('code', 'type', 'type_name')
        if w[attr]:
            if h and attr in h.keys():
                h_icmp = h.get(attr) or {}
            for item, val in iteritems(w[attr]):
                if opr and item in l_set and not (h_icmp and self._is_w_same(w[attr], h_icmp, item)):
                    if item == 'type_name':
                        if 'ipv6-name' in cmd:
                            commands.append(cmd + (' ' + 'icmpv6' + ' ' + 'type' + ' ' + val))
                        else:
                            commands.append(cmd + (' ' + attr + ' ' + item.replace("_", "-") + ' ' + val))
                    else:
                        commands.append(cmd + (' ' + attr + ' ' + item + ' ' + str(val)))
                elif not opr and item in l_set and not (h_icmp and self._in_target(h_icmp, item)):
                    commands.append(cmd + (' ' + attr + ' ' + item))
        return commands

    def _add_time(self, attr, w, h, cmd, opr):
        """
        This function forms the commands for 'time' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: base config.
        :param h: target config.
        :param cmd: commands to be prepend.
        :return: generated list of commands.
        """
        commands = []
        h_time = {}
        l_set = ('utc',
                 'stopdate',
                 'stoptime',
                 'weekdays',
                 'monthdays',
                 'startdate',
                 'starttime')
        if w[attr]:
            if h and attr in h.keys():
                h_time = h.get(attr) or {}
            for item, val in iteritems(w[attr]):
                if opr and item in l_set and not (h_time and self._is_w_same(w[attr], h_time, item)):
                    if item == 'utc':
                        if not (not val and (not h_time or item not in h_time)):
                            commands.append(cmd + (' ' + attr + ' ' + item))
                    else:
                        commands.append(cmd + (' ' + attr + ' ' + item + ' ' + val))
                elif not opr and item in l_set and not (h_time and self._is_w_same(w[attr], h_time, item)):
                    commands.append(cmd + (' ' + attr + ' ' + item))
        return commands

    def _add_tcp(self, attr, w, h, cmd, opr):
        """
        This function forms the commands for 'tcp' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: base config.
        :param h: target config.
        :param cmd: commands to be prepend.
        :return: generated list of commands.
        """
        h_tcp = {}
        commands = []
        if w[attr]:
            key = 'flags'
            flags = w[attr].get(key) or {}
            if flags:
                if h and key in h[attr].keys():
                    h_tcp = h[attr].get(key) or {}
                if flags:
                    if opr and not (h_tcp and self._is_w_same(w[attr], h[attr], key)):
                        commands.append(cmd + (' ' + attr + ' ' + key + ' ' + flags))
                    if not opr and not (h_tcp and self._is_w_same(w[attr], h[attr], key)):
                        commands.append(cmd + (' ' + attr + ' ' + key + ' ' + flags))
        return commands

    def _add_limit(self, attr, w, h, cmd, opr):
        """
        This function forms the commands for 'limit' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: base config.
        :param h: target config.
        :param cmd: commands to be prepend.
        :return: generated list of commands.
        """
        h_limit = {}
        commands = []
        if w[attr]:
            key = 'burst'
            if opr and key in w[attr].keys() and not (h and attr in h.keys() and self._is_w_same(w[attr], h[attr], key)):
                commands.append(cmd + (' ' + attr + ' ' + key + ' ' + str(w[attr].get(key))))
            elif not opr and key in w[attr].keys() and not (h and attr in h.keys() and self._in_target(h[attr], key)):
                commands.append(cmd + (' ' + attr + ' ' + key + ' ' + str(w[attr].get(key))))
            key = 'rate'
            rate = w[attr].get(key) or {}
            if rate:
                if h and key in h[attr].keys():
                    h_limit = h[attr].get(key) or {}
                if 'unit' in rate and 'number' in rate:
                    if opr and not (h_limit and self._is_w_same(rate, h_limit, 'unit') and self.is_w_same(rate, h_limit, 'number')):
                        commands.append(cmd + (' ' + attr + ' ' + key + ' ' + str(rate['number']) + '/' + rate['unit']))
                    if not opr and not (h_limit and self._is_w_same(rate, h_limit, 'unit') and self._is_w_same(rate, h_limit, 'number')):
                        commands.append(cmd + (' ' + attr + ' ' + key))
        return commands

    def _add_src_or_dest(self, attr, w, h, cmd, opr=True):
        """
        This function forms the commands for 'src/dest' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: base config.
        :param h: target config.
        :param cmd: commands to be prepend.
        :return: generated list of commands.
        """
        commands = []
        h_group = {}
        g_set = ('port_group',
                 'address_group',
                 'network_group')
        if w[attr]:
            keys = ('address', 'mac_address', 'port')
            for key in keys:
                if opr and key in w[attr].keys() and not (h and attr in h.keys() and self._is_w_same(w[attr], h[attr], key)):
                    commands.append(cmd + (' ' + attr + ' ' + key.replace("_", "-") + ' ' + w[attr].get(key)))
                elif not opr and key in w[attr].keys() and not (h and attr in h.keys() and self._in_target(h[attr], key)):
                    commands.append(cmd + (' ' + attr + ' ' + key))

            key = 'group'
            group = w[attr].get(key) or {}
            if group:
                if h and key in h[attr].keys():
                    h_group = h[attr].get(key) or {}
                for item, val in iteritems(group):
                    if val:
                        if opr and item in g_set and not (h_group and self._is_w_same(group, h_group, item)):
                            commands.append(cmd + (' ' + attr + ' ' + key + ' ' + item.replace("_", "-") + ' ' + val))
                        elif not opr and item in g_set and not (h_group and self._in_target(h_group, item)):
                            commands.append(cmd + (' ' + attr + ' ' + key + ' ' + item.replace("_", "-")))
        return commands

    def search_r_sets_in_have(self, have, w_name, type='rule_sets'):
        """
        This function  returns the rule-set/rule if it is present in target config.
        :param have: target config.
        :param w_name: rule-set name.
        :param type: rule_sets/rule/r_list.
        :return: rule-set/rule.
        """
        if have:
            key = 'name'
            if type == 'rules':
                key = 'number'
                for r in have:
                    if r[key] == w_name:
                        return r
            elif type == 'r_list':
                for h in have:
                    r_sets = self._get_r_sets(h)
                    for rs in r_sets:
                        if rs[key] == w_name:
                            return rs
            else:
                for rs in have:
                    if rs[key] == w_name:
                        return rs
        return None

    def _get_r_sets(self, item, type='rule_sets'):
        """
        This function returns the list of rule-sets/rules.
        :param item: config dictionary.
        :param type: rule_sets/rule/r_list.
        :return: list of rule-sets/rules.
        """
        rs_list = []
        r_sets = item[type]
        if r_sets:
            for rs in r_sets:
                rs_list.append(rs)
        return rs_list

    def _compute_command(self, afi, name=None, number=None, attrib=None, value=None, remove=False, opr=True):
        """
        This function construct the add/delete command based on passed attributes.
        :param afi:  address type.
        :param name:  rule-set name.
        :param number: rule-number.
        :param attrib: attribute name.
        :param value: value.
        :param remove: True if delete command needed to be construct.
        :param opr: opeeration flag.
        :return: generated command.
        """
        if remove or not opr:
            cmd = 'delete firewall ' + self._get_fw_type(afi)
        else:
            cmd = 'set firewall ' + self._get_fw_type(afi)
        if name:
            cmd += (' ' + name)
        if number:
            cmd += (' rule ' + str(number))
        if attrib:
            cmd += (' ' + attrib.replace("_", "-"))
        if value and opr and attrib != 'enable_default_log' and attrib != 'disabled':
            cmd += (" '" + str(value) + "'")
        return cmd

    def _add_r_base_attrib(self, afi, name, attr, rule, opr=True):
        """
        This function forms the command for 'rules' attributes which doesn't
        have further sub attributes.
        :param afi: address type.
        :param name: rule-set name
        :param attrib: attribute name
        :param rule: rule config dictionary.
        :param opr: True/False.
        :return: generated command.
        """
        if attr == 'number':
            command = self._compute_command(
                afi=afi, name=name, number=rule['number'], opr=opr
            )
        else:
            command = self._compute_command(
                afi=afi, name=name, number=rule['number'], attrib=attr, value=rule[attr], opr=opr
            )
        return command

    def _add_rs_base_attrib(self, afi, name, attrib, rule, opr=True):
        """

        This function forms the command for 'rule-sets' attributes which doesn't
        have further sub attributes.
        :param afi: address type.
        :param name: rule-set name
        :param attrib: attribute name
        :param rule: rule config dictionary.
        :param opr: True/False.
        :return: generated command.
        """
        command = self._compute_command(afi=afi, name=name, attrib=attrib, value=rule[attrib], opr=opr)
        return command

    def _bool_to_str(self, val):
        """
        This function converts the bool value into string.
        :param val: bool value.
        :return: enable/disable.
        """
        return 'enable' if val else 'disable'

    def _get_fw_type(self, afi):
        """
        This function returns the firewall rule-set type based on IP address.
        :param afi: address type
        :return: rule-set type.
        """
        return 'ipv6-name' if afi == 'ipv6' else 'name'

    def _is_del(self, l_set, h, key='number'):
        """
        This function checks whether rule needs to be deleted based on
        the rule number.
        :param l_set: attribute set.
        :param h: target config.
        :param key: number.
        :return: True/False.
        """
        return key in l_set and not (h and self._in_target(h, key))

    def _is_w_same(self, w, h, key):
        """
        This function checks whether the key value is same in base and
        target config dictionary.
        :param w: base config.
        :param h: target config.
        :param key:attribute name.
        :return: True/False.
        """
        return True if h and key in h and h[key] == w[key] else False

    def _in_target(self, h, key):
        """
        This function checks whether the target nexist and key present in target config.
        :param h: target config.
        :param key: attribute name.
        :return: True/False.
        """
        return True if h and key in h else False

    def _is_base_attrib(self, key):
        """
        This function checks whether key is present in predefined
        based attribute set.
        :param key:
        :return: True/False.
        """
        r_set = ('p2p',
                 'ipsec',
                 'action',
                 'fragment',
                 'protocol',
                 'disabled',
                 'description',
                 'mac_address',
                 'default_action',
                 'enable_default_log')
        return True if key in r_set else False
