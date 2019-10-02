#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_l3_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import normalize_interface, search_obj_in_list
from ansible.module_utils.network.nxos.utils.utils import remove_rsvd_interfaces, get_interface_type


class L3_interfaces(ConfigBase):
    """
    The nxos_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces',
    ]

    exclude_params = [
    ]

    def __init__(self, module):
        super(L3_interfaces, self).__init__(module)

    def get_l3_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        l3_interfaces_facts = facts['ansible_network_resources'].get('l3_interfaces')

        if not l3_interfaces_facts:
            return []
        return remove_rsvd_interfaces(l3_interfaces_facts)

    def edit_config(self, commands):
        return self._connection.edit_config(commands)

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
                self.edit_config(commands)
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
        config = self._module.params.get('config')
        want = []
        if config:
            for w in config:
                w.update({'name': normalize_interface(w['name'])})
                if get_interface_type(w['name']) == 'management':
                    self._module.fail_json(msg="The 'management' interface is not allowed to be managed by this module")
                want.append(remove_empties(w))
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
        state = self._module.params['state']
        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='config is required for state {0}'.format(state))

        commands = list()
        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        elif state == 'deleted':
            commands.extend(self._state_deleted(want, have))
        else:
            for w in want:
                if state == 'merged':
                    commands.extend(self._state_merged(w, have))
                elif state == 'replaced':
                    commands.extend(self._state_replaced(w, have))
        return commands

    def _state_replaced(self, w, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        merged_commands = self.set_commands(w, have)
        replaced_commands = self.del_delta_attribs(w, have)

        if merged_commands:
            cmds = set(replaced_commands).intersection(set(merged_commands))
            for cmd in cmds:
                merged_commands.remove(cmd)
            commands.extend(replaced_commands)
            commands.extend(merged_commands)
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for h in have:
            obj_in_want = search_obj_in_list(h['name'], want, 'name')
            if h == obj_in_want:
                continue
            commands.extend(self.del_all_attribs(h))
        for w in want:
            commands.extend(self.set_commands(w, have))
        return commands

    def _state_merged(self, w, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return self.set_commands(w, have)

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:
            for w in want:
                obj_in_have = search_obj_in_list(w['name'], have, 'name')
                commands.extend(self.del_all_attribs(obj_in_have))
        else:
            if not have:
                return commands
            for h in have:
                commands.extend(self.del_all_attribs(h))
        return commands

    def del_all_attribs(self, obj):
        commands = []
        if not obj or len(obj.keys()) == 1:
            return commands
        commands = self.generate_delete_commands(obj)
        if commands:
            commands.insert(0, 'interface ' + obj['name'])
        return commands

    def del_delta_attribs(self, w, have):
        commands = []
        obj_in_have = search_obj_in_list(w['name'], have, 'name')
        if obj_in_have:
            lst_to_del = []
            ipv4_intersect = self.intersect_list_of_dicts(w.get('ipv4'), obj_in_have.get('ipv4'))
            ipv6_intersect = self.intersect_list_of_dicts(w.get('ipv6'), obj_in_have.get('ipv6'))
            if ipv4_intersect:
                lst_to_del.append({'ipv4': ipv4_intersect})
            if ipv6_intersect:
                lst_to_del.append({'ipv6': ipv6_intersect})
            if lst_to_del:
                for item in lst_to_del:
                    commands.extend(self.generate_delete_commands(item))
            else:
                commands.extend(self.generate_delete_commands(obj_in_have))
            if commands:
                commands.insert(0, 'interface ' + obj_in_have['name'])
        return commands

    def generate_delete_commands(self, obj):
        commands = []
        if 'ipv4' in obj:
            commands.append('no ip address')
        if 'ipv6' in obj:
            commands.append('no ipv6 address')
        return commands

    def diff_of_dicts(self, w, obj):
        diff = set(w.items()) - set(obj.items())
        diff = dict(diff)
        if diff and w['name'] == obj['name']:
            diff.update({'name': w['name']})
        return diff

    def diff_list_of_dicts(self, w, h):
        diff = []
        set_w = set(tuple(sorted(d.items())) for d in w) if w else set()
        set_h = set(tuple(sorted(d.items())) for d in h) if h else set()
        difference = set_w.difference(set_h)
        for element in difference:
            diff.append(dict((x, y) for x, y in element))
        return diff

    def intersect_list_of_dicts(self, w, h):
        intersect = []
        waddr = []
        haddr = []
        set_w = set()
        set_h = set()
        if w:
            for d in w:
                waddr.append({'address': d['address']})
            set_w = set(tuple(sorted(d.items())) for d in waddr) if waddr else set()
        if h:
            for d in h:
                haddr.append({'address': d['address']})
            set_h = set(tuple(sorted(d.items())) for d in haddr) if haddr else set()
        intersection = set_w.intersection(set_h)
        for element in intersection:
            intersect.append(dict((x, y) for x, y in element))
        return intersect

    def add_commands(self, diff, name):
        commands = []
        if not diff:
            return commands

        if 'ipv4' in diff:
            commands.extend(self.generate_commands(diff['ipv4'], flag='ipv4'))
        if 'ipv6' in diff:
            commands.extend(self.generate_commands(diff['ipv6'], flag='ipv6'))
        if commands:
            commands.insert(0, 'interface ' + name)
        return commands

    def generate_commands(self, d, flag=None):
        commands = []

        for i in d:
            cmd = ''
            if flag == 'ipv4':
                cmd = 'ip address '
            elif flag == 'ipv6':
                cmd = 'ipv6 address '

            cmd += i['address']
            if 'secondary' in i and i['secondary'] is True:
                cmd += ' ' + 'secondary'
                if 'tag' in i:
                    cmd += ' ' + 'tag ' + str(i['tag'])
            elif 'tag' in i:
                cmd += ' ' + 'tag ' + str(i['tag'])
            commands.append(cmd)
        return commands

    def set_commands(self, w, have):
        commands = []
        obj_in_have = search_obj_in_list(w['name'], have, 'name')
        if not obj_in_have:
            commands = self.add_commands(w, w['name'])
        else:
            diff = {}
            diff.update({'ipv4': self.diff_list_of_dicts(w.get('ipv4'), obj_in_have.get('ipv4'))})
            diff.update({'ipv6': self.diff_list_of_dicts(w.get('ipv6'), obj_in_have.get('ipv6'))})
            commands = self.add_commands(diff, w['name'])
        return commands
