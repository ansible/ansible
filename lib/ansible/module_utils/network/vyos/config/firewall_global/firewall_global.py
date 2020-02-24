#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_firewall_global class
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


class Firewall_global(ConfigBase):
    """
    The vyos_firewall_global class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'firewall_global',
    ]

    def __init__(self, module):
        super(Firewall_global, self).__init__(module)

    def get_firewall_global_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources, data=data)
        firewall_global_facts = facts['ansible_network_resources'].get('firewall_global')
        if not firewall_global_facts:
            return []
        return firewall_global_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_firewall_global_facts = self.get_firewall_global_facts()
        else:
            existing_firewall_global_facts = []

        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_firewall_global_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True

        if self.state in self.ACTION_STATES:
            result['commands'] = commands

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_firewall_global_facts = self.get_firewall_global_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            running_config = self._module.params['running_config']
            if not running_config:
                self._module.fail_json(
                    msg="value of running_config parameter must not be empty for state parsed"
                )
            result['parsed'] = self.get_firewall_global_facts(data=running_config)
        else:
            changed_firewall_global_facts = []

        if self.state in self.ACTION_STATES:
            result['before'] = existing_firewall_global_facts
            if result['changed']:
                result['after'] = changed_firewall_global_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_firewall_global_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_firewall_global_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_firewall_global_facts
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
        if self.state in ('merged', 'replaced', 'rendered') and not w:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(self.state))
        if self.state == 'deleted':
            commands.extend(self._state_deleted(want=None, have=h))
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
            commands.extend(self._state_deleted(have, want))
        commands.extend(self._state_merged(want, have))
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        commands.extend(self._add_global_attr(want, have))
        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        b_set = ('config_trap',
                 'validation',
                 'log_martians',
                 'syn_cookies',
                 'twa_hazards_protection')
        if want:
            for key, val in iteritems(want):
                if val and key in b_set and not have:
                    commands.append(self._form_attr_cmd(attr=key, opr=False))
                elif val and key in b_set and have and key in have and have[key] != val:
                    commands.append(self._form_attr_cmd(attr=key, opr=False))
                else:
                    commands.extend(self._render_attr_config(want, have, key))
        elif not want and have:
            commands.append(self._compute_command(opr=False))
        elif have:
            for key, val in iteritems(have):
                if val and key in b_set:
                    commands.append(self._form_attr_cmd(attr=key, opr=False))
                else:
                    commands.extend(self._render_attr_config(want, have, key))
        return commands

    def _render_attr_config(self, w, h, key, opr=False):
        """
        This function invoke the function to extend commands
        based on the key.
        :param w: the desired configuration.
        :param h: the current configuration.
        :param key: attribute name
        :param opr: operation
        :return: list of commands
        """
        commands = []
        if key == 'ping':
            commands.extend(self._render_ping(key, w, h, opr=opr))
        elif key == 'group':
            commands.extend(self._render_group(key, w, h, opr=opr))
        elif key == 'state_policy':
            commands.extend(self._render_state_policy(key, w, h, opr=opr))
        elif key == 'route_redirects':
            commands.extend(self._render_route_redirects(key, w, h, opr=opr))
        return commands

    def _add_global_attr(self, w, h, opr=True):
        """
        This function forms the set/delete commands based on the 'opr' type
        for firewall_global attributes.
        :param w: the desired config.
        :param h: the target config.
        :param opr: True/False.
        :return: generated commands list.
        """
        commands = []
        w_fg = deepcopy(remove_empties(w))
        l_set = ('config_trap',
                 'validation',
                 'log_martians',
                 'syn_cookies',
                 'twa_hazards_protection')
        if w_fg:
            for key, val in iteritems(w_fg):
                if opr and key in l_set and not (h and self._is_w_same(w_fg, h, key)):
                    commands.append(self._form_attr_cmd(attr=key, val=self._bool_to_str(val), opr=opr))
                elif not opr:
                    if key and self._is_del(l_set, h):
                        commands.append(self._form_attr_cmd(attr=key, key=self._bool_to_str(val), opr=opr))
                        continue
                    elif key in l_set and not (h and self._in_target(h, key)) and not self._is_del(l_set, h):
                        commands.append(self._form_attr_cmd(attr=key, val=self._bool_to_str(val), opr=opr))
                else:
                    commands.extend(self._render_attr_config(w_fg, h, key, opr))
        return commands

    def _render_ping(self, attr, w, h, opr):
        """
        This function forms the commands for 'ping' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: the desired configuration.
        :param h: the target config.
        :param opr: True/False.
        :return: generated list of commands.
        """
        commands = []
        h_ping = {}
        l_set = ('all', 'broadcast')
        if h:
            h_ping = h.get(attr) or {}
        if self._is_root_del(w[attr], h_ping, attr):
            for item, value in iteritems(h[attr]):
                if not opr and item in l_set:
                    commands.append(self._form_attr_cmd(attr=item, opr=opr))
        elif w[attr]:
            if h and attr in h.keys():
                h_ping = h.get(attr) or {}
            for item, value in iteritems(w[attr]):
                if opr and item in l_set and not (h_ping and self._is_w_same(w[attr], h_ping, item)):
                    commands.append(self._form_attr_cmd(attr=item, val=self._bool_to_str(value), opr=opr))
                elif not opr and item in l_set and not (h_ping and self._is_w_same(w[attr], h_ping, item)):
                    commands.append(self._form_attr_cmd(attr=item, opr=opr))
        return commands

    def _render_group(self, attr, w, h, opr):
        """
        This function forms the commands for 'group' attribute based on the 'opr'.
        :param attr: attribute name.
        :param w: base config.
        :param h: target config.
        :param opr: True/False.
        :return: generated list of commands.
        """
        commands = []
        h_grp = {}
        if not opr and self._is_root_del(h, w, attr):
            commands.append(self._form_attr_cmd(attr=attr, opr=opr))
        else:
            if h:
                h_grp = h.get('group') or {}
            if w:
                commands.extend(self._render_grp_mem('port-group', w['group'], h_grp, opr))
                commands.extend(self._render_grp_mem('address_group', w['group'], h_grp, opr))
                commands.extend(self._render_grp_mem('network_group', w['group'], h_grp, opr))
        return commands

    def _render_grp_mem(self, attr, w, h, opr):
        """
        This function forms the commands for group list/members attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: the desired config.
        :param h: the target config.
        :param opr: True/False.
        :return: generated list of commands.
        """
        commands = []
        h_grp = []
        w_grp = []
        l_set = ('name', 'description')
        if w:
            w_grp = w.get(attr) or []
        if h:
            h_grp = h.get(attr) or []

        if w_grp:
            for want in w_grp:
                cmd = self._compute_command(key='group', attr=attr, opr=opr)
                h = self.search_attrib_in_have(h_grp, want, 'name')
                for key, val in iteritems(want):
                    if val:
                        if opr and key in l_set and not (h and self._is_w_same(want, h, key)):
                            if key == 'name':
                                commands.append(cmd + ' ' + str(val))
                            else:
                                commands.append(cmd + ' ' + want['name'] + ' ' + key + " '" + str(want[key]) + "'")
                        elif not opr and key in l_set:
                            if key == 'name' and self._is_grp_del(h, want, key):
                                commands.append(cmd + ' ' + want['name'])
                                continue
                            elif not (h and self._in_target(h, key)) and not self._is_grp_del(h, want, key):
                                commands.append(cmd + ' ' + want['name'] + ' ' + key)
                        elif key == 'members':
                            commands.extend(self._render_ports_addrs(key, want, h, opr, cmd, want['name'], attr))
        return commands

    def _render_ports_addrs(self, attr, w, h, opr, cmd, name, type):
        """
        This function forms the commands for port/address/network group members
        based on the 'opr'.
        :param attr: attribute name.
        :param w: the desired config.
        :param h: the target config.
        :param cmd: commands to be prepend.
        :param name: name of group.
        :param type: group type.
        :return: generated list of commands.
        """
        commands = []
        have = []
        if w:
            want = w.get(attr) or []
        if h:
            have = h.get(attr) or []

        if want:
            if opr:
                members = list_diff_want_only(want, have)
                for member in members:
                    commands.append(
                        cmd + ' ' + name + ' ' + self._grp_type(type) + ' ' + member[self._get_mem_type(type)]
                    )
            elif not opr and have:
                members = list_diff_want_only(want, have)
                for member in members:
                    commands.append(
                        cmd + ' ' + name + ' ' + self._grp_type(type) + ' ' + member[self._get_mem_type(type)]
                    )
        return commands

    def _get_mem_type(self, group):
        """
        This function returns the member type
        based on the type of group.
        """
        return 'port' if group == 'port_group' else 'address'

    def _render_state_policy(self, attr, w, h, opr):
        """
        This function forms the commands for 'state-policy' attributes
        based on the 'opr'.
        :param attr: attribute name.
        :param w: the desired config.
        :param h: the target config.
        :param opr: True/False.
        :return: generated list of commands.
        """
        commands = []
        have = []
        l_set = ('log', 'action', 'connection_type')
        if not opr and self._is_root_del(h, w, attr):
            commands.append(self._form_attr_cmd(attr=attr, opr=opr))
        else:
            w_sp = deepcopy(remove_empties(w))
            want = w_sp.get(attr) or []
            if h:
                have = h.get(attr) or []
            if want:
                for w in want:
                    h = self.search_attrib_in_have(have, w, 'connection_type')
                    for key, val in iteritems(w):
                        if val and key != 'connection_type':
                            if opr and key in l_set and not (h and self._is_w_same(w, h, key)):
                                commands.append(self._form_attr_cmd(key=attr + ' ' + w['connection_type'], attr=key, val=self._bool_to_str(val), opr=opr))
                            elif not opr and key in l_set:
                                if not (h and self._in_target(h, key)) and not self._is_del(l_set, h):
                                    if key == 'action':
                                        commands.append(self._form_attr_cmd(attr=attr + ' ' + w['connection_type'], opr=opr))
                                    else:
                                        commands.append(self._form_attr_cmd(attr=attr + ' ' + w['connection_type'], val=self._bool_to_str(val), opr=opr))
        return commands

    def _render_route_redirects(self, attr, w, h, opr):
        """
        This function forms the commands for 'route_redirects' attributes based on the 'opr'.
        :param attr: attribute name.
        :param w: the desired config.
        :param h: the target config.
        :param opr: True/False.
        :return: generated list of commands.
        """
        commands = []
        have = []
        l_set = ('afi', 'ip_src_route')

        if w:
            want = w.get(attr) or []
        if h:
            have = h.get(attr) or []

        if want:
            for w in want:
                h = self.search_attrib_in_have(have, w, 'afi')
                for key, val in iteritems(w):
                    if val and key != 'afi':
                        if opr and key in l_set and not (h and self._is_w_same(w, h, key)):
                            commands.append(self._form_attr_cmd(attr=key, val=self._bool_to_str(val), opr=opr))
                        elif not opr and key in l_set:
                            if self._is_del(l_set, h):
                                commands.append(self._form_attr_cmd(attr=key, val=self._bool_to_str(val), opr=opr))
                                continue
                            elif not (h and self._in_target(h, key)) and not self._is_del(l_set, h):
                                commands.append(self._form_attr_cmd(attr=key, val=self._bool_to_str(val), opr=opr))
                        elif key == 'icmp_redirects':
                            commands.extend(self._render_icmp_redirects(key, w, h, opr))
        return commands

    def _render_icmp_redirects(self, attr, w, h, opr):
        """
        This function forms the commands for 'icmp_redirects' attributes
        based on the 'opr'.
        :param attr: attribute name.
        :param w: the desired config.
        :param h: the target config.
        :param opr: True/False.
        :return: generated list of commands.
        """
        commands = []
        h_red = {}
        l_set = ('send', 'receive')
        if w[attr]:
            if h and attr in h.keys():
                h_red = h.get(attr) or {}
            for item, value in iteritems(w[attr]):
                if opr and item in l_set and not (h_red and self._is_w_same(w[attr], h_red, item)):
                    commands.append(self._form_attr_cmd(attr=item, val=self._bool_to_str(value), opr=opr))
                elif not opr and item in l_set and not (h_red and self._is_w_same(w[attr], h_red, item)):
                    commands.append(self._form_attr_cmd(attr=item, opr=opr))
        return commands

    def search_attrib_in_have(self, have, want, attr):
        """
        This function  returns the attribute if it is present in target config.
        :param have: the target config.
        :param want: the desired config.
        :param attr: attribute name .
        :return: attribute/None
        """
        if have:
            for h in have:
                if h[attr] == want[attr]:
                    return h
        return None

    def _form_attr_cmd(self, key=None, attr=None, val=None, opr=True):
        """
        This function forms the command for leaf attribute.
        :param key: parent key.
        :param attr: attribute name
        :param value: value
        :param opr: True/False.
        :return: generated command.
        """
        command = self._compute_command(key=key, attr=self._map_attrib(attr), val=val, opr=opr)
        return command

    def _compute_command(self, key=None, attr=None, val=None, remove=False, opr=True):
        """
        This function construct the add/delete command based on passed attributes.
        :param key: parent key.
        :param attr: attribute name
        :param value: value
        :param remove: True/False.
        :param opr: True/False.
        :return: generated command.
        """
        if remove or not opr:
            cmd = 'delete firewall '
        else:
            cmd = 'set firewall '
        if key:
            cmd += (key.replace("_", "-") + " ")
        if attr:
            cmd += (attr.replace("_", "-"))
        if val and opr:
            cmd += (" '" + str(val) + "'")
        return cmd

    def _bool_to_str(self, val):
        """
        This function converts the bool value into string.
        :param val: bool value.
        :return: enable/disable.
        """
        return 'enable' if str(val) == 'True' else 'disable' if str(val) == 'False' else val

    def _grp_type(self, val):
        """
        This function returns the group member type based on value argument.
        :param val: value.
        :return: member type.
        """
        return 'address' if val == 'address_group' else 'network' if val == 'network_group' else 'port'

    def _is_w_same(self, w, h, key):
        """
        This function checks whether the key value is same in desired and
        target config dictionary.
        :param w: base config.
        :param h: target config.
        :param key:attribute name.
        :return: True/False.
        """
        return True if h and key in h and h[key] == w[key] else False

    def _in_target(self, h, key):
        """
        This function checks whether the target exist and key present in target config.
        :param h: target config.
        :param key: attribute name.
        :return: True/False.
        """
        return True if h and key in h else False

    def _is_grp_del(self, w, h, key):
        """
        This function checks whether group needed to be deleted based on
        desired and target configs.
        :param w: the desired config.
        :param h: the target config.
        :param key: group name.
        :return: True/False.
        """
        return True if h and key in h and (not w or key not in w or not w[key]) else False

    def _is_root_del(self, w, h, key):
        """
        This function checks whether a root attribute which can have
        further child attributes needed to be deleted.
        :param w: the desired config.
        :param h: the target config.
        :param key: attribute name.
        :return: True/False.
        """
        return True if h and key in h and (not w or key not in w or not w[key]) else False

    def _is_del(self, b_set, h, key='number'):
        """
        This function checks whether attribute needs to be deleted
        when operation is false and attribute present in present target config.
        :param b_set: attribute set.
        :param h: target config.
        :param key: number.
        :return: True/False.
        """
        return key in b_set and not (h and self._in_target(h, key))

    def _map_attrib(self, attrib, type=None):
        """
        - This function construct the regex string.
        - replace the underscore with hyphen.
        :param attrib: attribute
        :return: regex string
        """
        regex = attrib.replace("_", "-")
        if attrib == 'send':
            if type == 'ipv6':
                regex = 'ipv6-send-redirects'
            else:
                regex = 'send-redirects'
        elif attrib == 'ip_src_route':
            if type == 'ipv6':
                regex = 'ipv6-src-route'
        elif attrib == 'receive':
            if type == 'ipv6':
                regex = 'ipv6-receive-redirects'
            else:
                regex = 'receive-redirects'
        elif attrib == 'disabled':
            regex = 'disable'
        elif attrib == 'all':
            regex = 'all-ping'
        elif attrib == 'broadcast':
            regex = 'broadcast-ping'
        elif attrib == 'validation':
            regex = 'source-validation'
        return regex
