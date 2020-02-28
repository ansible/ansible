#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_acl_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties, dict_diff
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import flatten_dict, search_obj_in_list, get_interface_type, normalize_interface


class Acl_interfaces(ConfigBase):
    """
    The nxos_acl_interfaces class
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
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data=data)
        acl_interfaces_facts = facts['ansible_network_resources'].get(
            'acl_interfaces')
        if not acl_interfaces_facts:
            return []
        return acl_interfaces_facts

    def edit_config(self, commands):
        """Wrapper method for `_connection.edit_config()`
        This exists solely to allow the unit test framework to mock device connection calls.
        """
        return self._connection.edit_config(commands)

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()
        state = self._module.params['state']
        action_states = ['merged', 'replaced', 'deleted', 'overridden']

        if state == 'gathered':
            result['gathered'] = self.get_acl_interfaces_facts()
        elif state == 'rendered':
            result['rendered'] = self.set_config({})
            # no need to fetch facts for rendered
        elif state == 'parsed':
            result['parsed'] = self.set_config({})
            # no need to fetch facts for parsed
        else:
            existing_acl_interfaces_facts = self.get_acl_interfaces_facts()
            commands.extend(self.set_config(existing_acl_interfaces_facts))
            if commands and state in action_states:
                if not self._module.check_mode:
                    self._connection.edit_config(commands)
                result['changed'] = True
                result['before'] = existing_acl_interfaces_facts
                result['commands'] = commands

            changed_acl_interfaces_facts = self.get_acl_interfaces_facts()
            if result['changed']:
                result['after'] = changed_acl_interfaces_facts
        result['warnings'] = warnings
        return result

    def set_config(self, existing_acl_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params['config']
        want = []
        if config:
            for w in config:
                if get_interface_type(w['name']) == 'loopback':
                    self._module.fail_json(
                        msg='This module works with ethernet, management or port-channe')
                w.update({'name': normalize_interface(w['name'])})
                want.append(remove_empties(w))
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
        state = self._module.params['state']
        commands = []
        if state == 'overridden':
            commands = (self._state_overridden(want, have))
        elif state == 'deleted':
            commands = (self._state_deleted(want, have))
        elif state == 'rendered':
            commands = self._state_rendered(want)
        elif state == 'parsed':
            want = self._module.params['running_config']
            commands = self._state_parsed(want)
        else:
            for w in want:
                if state == 'merged':
                    commands.extend(self._state_merged(w, have))
                elif state == 'replaced':
                    commands.extend(self._state_replaced(w, have))
        return commands

    def _state_parsed(self, want):
        return self.get_acl_interfaces_facts(want)

    def _state_rendered(self, want):
        commands = []
        for w in want:
            commands.extend(self.set_commands(w, {}))
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        new_commands = []
        del_dict = {'name': want['name'], 'access_groups': []}
        obj_in_have = search_obj_in_list(want['name'], have, 'name')
        if obj_in_have != want:
            commands = []
            if obj_in_have and 'access_groups' in obj_in_have.keys():
                for ag in obj_in_have['access_groups']:
                    want_afi = []
                    if want.get('access_groups'):
                        want_afi = search_obj_in_list(
                            ag['afi'], want['access_groups'], 'afi')
                    if not want_afi:
                        # whatever in have is not in want
                        del_dict['access_groups'].append(ag)
                    else:
                        del_acl = []
                        for acl in ag['acls']:
                            if want_afi.get('acls'):
                                if acl not in want_afi['acls']:
                                    del_acl.append(acl)
                            else:
                                del_acl.append(acl)
                        afi = want_afi['afi']
                        del_dict['access_groups'].append(
                            {'afi': afi, 'acls': del_acl})

            commands.extend(self._state_deleted([del_dict], have))
            commands.extend(self._state_merged(want, have))
            new_commands.append(commands[0])
            commands = [commands[i]
                        for i in range(1, len(commands)) if commands[i] != commands[0]]
            new_commands.extend(commands)
        return new_commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_intf = [w['name'] for w in want]
        for h in have:
            if h['name'] not in want_intf:
                commands.extend(self._state_deleted([h], have))
        for w in want:
            commands.extend(self._state_replaced(w, have))
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return self.set_commands(want, have)

    def set_commands(self, want, have, deleted=False):
        commands = []
        have_name = search_obj_in_list(want['name'], have, 'name')
        if have_name and have_name.get('access_groups'):
            if want.get('access_groups'):
                for w_afi in want['access_groups']:
                    ip = 'ipv6'
                    if w_afi['afi'] == 'ipv4':
                        ip = 'ip'
                    have_afi = search_obj_in_list(
                        w_afi['afi'], have_name['access_groups'], 'afi')
                    if have_afi:
                        new_acls = []
                        if deleted:
                            if w_afi.get('acls') and have_afi.get('acls'):
                                new_acls = [
                                    acl for acl in w_afi.get('acls') if acl in have_afi.get('acls')]
                            elif 'acls' not in w_afi.keys():
                                new_acls = have_afi.get('acls')
                        else:
                            if w_afi.get('acls'):
                                new_acls = [
                                    acl for acl in w_afi['acls'] if acl not in have_afi['acls']]
                        commands.extend(self.process_acl(
                            new_acls, ip, deleted))
                    else:
                        if not deleted:
                            if w_afi.get('acls'):
                                commands.extend(
                                    self.process_acl(w_afi['acls'], ip))
            else:
                # only name is given to delete
                if deleted and 'access_groups' in have_name.keys():
                    commands.extend(self.process_access_group(have_name, True))
        else:
            if not deleted:  # and 'access_groups' in have_name.keys():
                commands.extend(self.process_access_group(want))

        if len(commands) > 0:
            commands.insert(0, 'interface ' + want['name'])
        return commands

    def process_access_group(self, item, deleted=False):
        commands = []
        for ag in item['access_groups']:
            ip = 'ipv6'
            if ag['afi'] == 'ipv4':
                ip = 'ip'
            if ag.get('acls'):
                commands.extend(self.process_acl(
                    ag['acls'], ip, deleted))
        return commands

    def process_acl(self, acls, ip, deleted=False):
        commands = []
        no = ''
        if deleted:
            no = 'no '
        for acl in acls:
            port = ''
            if acl.get('port'):
                port = ' port'
            ag = ' access-group '
            if ip == 'ipv6':
                ag = ' traffic-filter '
            commands.append(no + ip + port + ag +
                            acl['name'] + ' ' + acl['direction'])
        return commands

    def _state_deleted(self, main_want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if main_want:
            for want in main_want:
                commands.extend(self.set_commands(want, have, deleted=True))
        else:
            for h in have:
                commands.extend(self.set_commands(h, have, deleted=True))

        return commands
