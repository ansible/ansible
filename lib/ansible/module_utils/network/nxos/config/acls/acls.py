#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_acls class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
import q
import socket
import re
from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties, dict_diff
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import flatten_dict, search_obj_in_list, get_interface_type, normalize_interface


class Acls(ConfigBase):
    """
    The nxos_acls class
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
        acls_facts = facts['ansible_network_resources'].get('acls')
        if not acls_facts:
            return []
        return acls_facts

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
            result['gathered'] = self.get_acls_facts()
        elif state == 'rendered':
            result['rendered'] = self.set_config({})
        elif state == 'parsed':
            result['parsed'] = self.set_config({})
        else:
            existing_acls_facts = self.get_acls_facts()
            commands.extend(self.set_config(existing_acls_facts))
            if commands and state in action_states:
                if not self._module.check_mode:
                    self._connection.edit_config(commands)
                result['changed'] = True
                result['before'] = existing_acls_facts
                result['commands'] = commands

            changed_acls_facts = self.get_acls_facts()
            if result['changed']:
                result['after'] = changed_acls_facts
        result['warnings'] = warnings
        return result

    def set_config(self, existing_acls_facts):
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
                want.append(remove_empties(w))
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
        q(commands)
        if state != 'parsed':
            commands = [c.strip() for c in commands]
        return commands

    def _state_parsed(self, want):
        q(want)
        return self.get_acls_facts(want)

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
        commands = []
        have_afi = search_obj_in_list(want['afi'], have, 'afi')
        del_dict = {'acls': []}
        q(want)
        flag = 0
        want_names = []
        if have_afi != want:
            if have_afi:
                q(have_afi, want)
                del_dict.update({'afi': have_afi['afi'], 'acls': []})
                if want.get('acls'):
                    want_names = [w['name'] for w in want['acls']]
                    q(want_names)
                    for h in have_afi['acls']:
                        q(h)
                        if h['name'] in want_names:
                            want_aces = search_obj_in_list(
                                h['name'], want['acls'], 'name')
                            q(want_aces)
                            del_acl = {}
                            aces = []  # that will be deleted
                            if h.get('aces'):
                                for h_ace in h['aces']:
                                    q(h_ace)
                                    if want_aces.get('aces'):
                                        if h_ace not in want_aces['aces']:
                                            aces.append(h_ace)
                                    else:
                                        aces.append(h_ace)
                            if aces:
                                del_acl['name'] = h['name']
                                del_acl['aces'] = aces
                            q(aces, del_acl)

                            if del_acl:
                                del_dict['acls'].append(del_acl)
                                del_dict.update(
                                    {'afi': have_afi['afi']})
                else:
                    acls = []
                    for acl in have_afi['acls']:
                        acls.append({'name': acl['name']})
                    del_dict['acls'] = acls
            q(del_dict)
            if del_dict['acls']:
                commands.extend(self._state_deleted([del_dict], have))
            q(commands)
            commands.extend(self._state_merged(want, have))
            q('after merged')
            q(commands)
            # for i in range(1, len(commands)):
            #     if commands[i] == commands[0]:
            #         commands[i] = ''
            commands = list(filter(None, commands))
            q(commands)
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_afi = [w['afi'] for w in want]
        q(want_afi)
        for h in have:
            if h['afi'] in want_afi:
                q(h)
                w = search_obj_in_list(h['afi'], want, 'afi')
                for h_acl in h['acls']:
                    w_acl = search_obj_in_list(
                        h_acl['name'], w['acls'], 'name')
                    q(h_acl, w_acl)
                    if not w_acl:
                        del_dict = {'afi': h['afi'], 'acls': [
                            {'name': h_acl['name']}]}
                        q(del_dict)
                        commands.extend(self._state_deleted([del_dict], have))
            else:
                q(h)
                # if afi is not in want
                commands.extend(self._state_deleted([{'afi': h['afi']}], have))
        q(commands)
        for w in want:
            q(w)
            commands.extend(self._state_replaced(w, have))
        q(commands)
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        q('inside merged')
        return self.set_commands(want, have)

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        q('inside deleted')
        q(want, have)
        if want:  # and have != want:
            q('delete want')
            for w in want:
                q(w)
                ip = 'ipv6' if w['afi'] == 'ipv6' else 'ip'
                acl_names = []
                have_afi = search_obj_in_list(w['afi'], have, 'afi')
                # if want['afi] not in have, ignore
                q(have_afi)
                if have_afi:
                    if w.get('acls'):
                        for acl in w['acls']:
                            q(acl)
                            if 'aces' in acl.keys():
                                have_name = search_obj_in_list(
                                    acl['name'], have_afi['acls'], 'name')
                                if have_name:
                                    q(have_name)
                                    ace_commands = []
                                    flag = 0
                                    for ace in acl['aces']:
                                        q(ace)
                                        if ace.keys() == ['sequence']:
                                            q('sequence')
                                            # only sequence number is specified to be deleted
                                            if 'aces' in have_name.keys():
                                                for h_ace in have_name['aces']:
                                                    q(h_ace)
                                                    if h_ace['sequence'] == ace['sequence']:
                                                        ace_commands.append(
                                                            'no ' + str(ace['sequence']))
                                                        flag = 1
                                        else:
                                            q(have_name)
                                            if 'aces' in have_name.keys():
                                                for h_ace in have_name['aces']:
                                                    q(h_ace)
                                                    # when want['ace'] does not have seq number
                                                    if 'sequence' not in ace.keys():
                                                        del h_ace['sequence']
                                                    q(h_ace, ace)
                                                    if ace == h_ace:
                                                        ace_commands.append(
                                                            'no ' + self.process_ace(ace))
                                                        flag = 1
                                    if flag:
                                        ace_commands.insert(
                                            0, ip + ' access-list ' + acl['name'])
                                    q(ace_commands)
                                    commands.extend(ace_commands)
                            else:
                                # only name given
                                for h in have_afi['acls']:
                                    if h['name'] == acl['name']:
                                        acl_names.append(acl['name'])
                        q(acl_names)
                        for name in acl_names:
                            commands.append(
                                'no ' + ip + ' access-list ' + name)

                    else:
                        q('only afi is given')
                        if have_afi.get('acls'):
                            for h in have_afi['acls']:
                                q(h)
                                acl_names.append(h['name'])
                            q(acl_names)
                            for name in acl_names:
                                commands.append(
                                    'no ' + ip + ' access-list ' + name)
        else:
            v6 = []
            v4 = []
            v6_local = v4_local = None
            for h in have:
                q(h)
                if h['afi'] == 'ipv6':
                    v6 = (acl['name'] for acl in h['acls'])
                    if 'match_local_traffic' in h.keys():
                        v6_local = True
                else:
                    v4 = (acl['name'] for acl in h['acls'])
                    if 'match_local_traffic' in h.keys():
                        v4_local = True
            # q(v4)

            self.no_commands(v4, commands, v4_local, 'ip')
            self.no_commands(v6, commands, v6_local, 'ipv6')

            for name in v6:
                commands.append('no ipv6 access-list ' + name)
            if v4_local:
                commands.append('no ipv6 access-list match-local-traffic')

        q(commands)
        return commands

    def no_commands(self, v_list, commands, match_local, ip):
        for name in v_list:
            commands.append('no '+ip+' access-list ' + name)
        if match_local:
            commands.append('no '+ip+' access-list match-local-traffic')

    def set_commands(self, want, have):
        commands = []
        have_afi = search_obj_in_list(want['afi'], have, 'afi')
        ip = ''
        if 'v6' in want['afi']:
            ip = 'ipv6 '
        else:
            ip = 'ip '

        q(want, have_afi)
        if have_afi:
            if want.get('acls'):
                for w_acl in want['acls']:
                    have_acl = search_obj_in_list(
                        w_acl['name'], have_afi['acls'], 'name')
                    name = w_acl['name']
                    q(have_acl, w_acl)
                    flag = 0
                    ace_commands = []
                    if have_acl != w_acl:
                        if have_acl:
                            ace_list = []
                            q(ace_commands)
                            if w_acl.get('aces') and have_acl.get('aces'):
                                ace_list = [item for item in w_acl['aces']
                                            if item not in have_acl['aces']]
                            elif w_acl.get('aces'):
                                ace_list = [item for item in w_acl['aces']]
                            q(ace_list)
                            for w_ace in ace_list:
                                ace_commands.append(
                                    self.process_ace(w_ace).strip())
                                flag = 1

                            if flag:
                                ace_commands.insert(
                                    0, ip + 'access-list ' + name)
                            q(ace_commands, commands)

                        else:
                            q(commands, name)
                            commands.append(ip + 'access-list ' + name)
                            if 'aces' in w_acl.keys():
                                for w_ace in w_acl['aces']:
                                    commands.append(
                                        self.process_ace(w_ace).strip())
                    commands.extend(ace_commands)
                    q(commands)
        else:
            if want.get('acls'):
                for w_acl in want['acls']:
                    name = w_acl['name']
                    commands.append(ip + 'access-list ' + name)
                    if 'aces' in w_acl.keys():
                        for w_ace in w_acl['aces']:
                            commands.append(self.process_ace(w_ace).strip())

        return commands

    def process_ace(self, w_ace):
        command = ''
        # q(w_ace)
        ace_keys = w_ace.keys()
        q(ace_keys)
        if 'remark' in ace_keys:
            command += 'remark ' + w_ace['remark'] + ' '
        else:
            command += w_ace['grant'] + ' '
            if 'protocol' in ace_keys:
                command += w_ace['protocol'] + ' '
                src = self.get_address(
                    w_ace['source'], w_ace['protocol'])
                dest = self.get_address(
                    w_ace['destination'], w_ace['protocol'])
                command += src+dest
                if 'protocol_options' in ace_keys:
                    q('protocol_options')
                    pro = w_ace['protocol_options'].keys()[0]
                    q(pro)
                    flags = ''
                    for k in w_ace['protocol_options'][pro].keys():
                        q(k)
                        k = re.sub('_', '-', k)
                        flags += k + ' '
                    command += flags
                if 'dscp' in ace_keys:
                    command += 'dscp '+w_ace['dscp'] + ' '
                if 'fragments' in ace_keys:
                    command += 'fragments '

            if 'log' in ace_keys:
                command += 'log '
        if 'sequence' in ace_keys:
            command = str(w_ace['sequence']) + ' ' + command
        # q(command)
        return command

    def get_address(self, endpoint, pro=''):
        ret_addr = ''
        keys = endpoint.keys()
        if 'address' in keys:
            if 'wildcard_bits' not in keys:
                self._module.fail_json(
                    msg='wildcard bits not specified for address')
            else:
                ret_addr = endpoint['address'] + \
                    ' ' + endpoint['wildcard_bits']+' '
        elif 'any' in keys:
            ret_addr = 'any '
        elif 'host' in keys:
            ret_addr = 'host ' + endpoint['host']+' '
        elif 'prefix' in keys:
            ret_addr = endpoint['prefix'] + ' '

        if pro in ['tcp', 'udp']:
            if 'port_protocol' in keys:
                options = self.get_options(endpoint['port_protocol'])
                ret_addr += options
        return ret_addr

    def get_options(self, item):
        com = ''
        subkey = item.keys()
        if 'range' in subkey:
            com = 'range ' + item['range']['start'] + \
                ' ' + item['range']['end']+' '
        else:
            com = subkey[0]+' ' + item[subkey[0]]+' '
        return com
