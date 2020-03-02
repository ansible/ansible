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
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import socket
import re
from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties, dict_diff
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.argspec.acls.acls import AclsArgs
from ansible.module_utils.network.common import utils
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
        if want:
            want = self.convert_values(want)
        resp = self.set_state(want, have)
        return to_list(resp)

    def convert_values(self, want):
        '''
        This method is used to map and convert the user given values with what will actually be present in the device configuation
        '''
        port_protocol = {
            515: 'lpd',
            517: 'talk',
            7: 'echo',
            9: 'discard',
            12: 'exec',
            13: 'login',
            14: 'cmd',
            109: 'pop2',
            19: 'chargen',
            20: 'ftp-data',
            21: 'ftp',
            23: 'telnet',
            25: 'smtp',
            540: 'uucp',
            543: 'klogin',
            544: 'kshell',
            37: 'time',
            43: 'whois',
            49: 'tacacs',
            179: 'bgp',
            53: 'domain',
            194: 'irc',
            70: 'gopher',
            79: 'finger',
            80: 'www',
            101: 'hostname',
            3949: 'drip',
            110: 'pop3',
            111: 'sunrpc',
            496: 'pim-auto-rp',
            113: 'ident',
            119: 'nntp'
        }
        protocol = {
            1: 'icmp',
            2: 'igmp',
            4: 'ip',
            6: 'tcp',
            103: 'pim',
            108: 'pcp',
            47: 'gre',
            17: 'udp',
            50: 'esp',
            51: 'ahp',
            88: 'eigrp',
            89: 'ospf',
            94: 'nos'
        }
        precedence = {
            0: 'routine',
            1: 'priority',
            2: 'immediate',
            3: 'flash',
            4: 'flash-override',
            5: 'critical',
            6: 'internet',
            7: 'network'
        }
        dscp = {
            10: 'AF11',
            12: 'AF12',
            14: 'AF13',
            18: 'AF21',
            20: 'AF22',
            22: 'AF23',
            26: 'AF31',
            28: 'AF32',
            30: 'AF33',
            34: 'AF41',
            36: 'AF42',
            38: 'AF43',
            8: 'CS1',
            16: 'CS2',
            24: 'CS3',
            32: 'CS4',
            40: 'CS5',
            48: 'CS6',
            56: 'CS7',
            0: 'Default',
            46: 'EF'
        }
        # port_pro_num = list(protocol.keys())
        for afi in want:
            if 'acls' in afi.keys():
                for acl in afi['acls']:
                    if 'aces' in acl.keys():
                        for ace in acl['aces']:
                            if 'dscp' in ace.keys():
                                if ace['dscp'].isdigit():
                                    ace['dscp'] = dscp[int(ace['dscp'])]
                                ace['dscp'] = ace['dscp'].lower()
                            if 'precedence' in ace.keys():
                                if ace['precedence'].isdigit():
                                    ace['precedence'] = precedence[int(
                                        ace['precedence'])]
                            if 'protocol' in ace.keys(
                            ) and ace['protocol'].isdigit() and int(
                                    ace['protocol']) in protocol.keys():
                                ace['protocol'] = protocol[int(
                                    ace['protocol'])]
                                # convert number to name
                            if 'protocol' in ace.keys(
                            ) and ace['protocol'] in ['tcp', 'udp']:
                                for end in ['source', 'destination']:
                                    if 'port_protocol' in ace[end].keys():
                                        key = list(ace[end]
                                                   ['port_protocol'].keys())[0]
                                        # key could be eq,gt,lt,neq or range
                                        if key != 'range':
                                            val = ace[end]['port_protocol'][
                                                key]
                                            if val.isdigit() and int(val) in port_protocol.keys(
                                            ):
                                                ace[end]['port_protocol'][
                                                    key] = port_protocol[int(
                                                        val)]
                                        else:
                                            st = int(ace[end]['port_protocol']
                                                     ['range']['start'])

                                            end = int(ace[end]['port_protocol']
                                                      ['range']['end'])

                                            if st in port_protocol.keys():
                                                ace[end]['port_protocol'][
                                                    'range'][
                                                        'start'] = port_protocol[
                                                            st]
                                            if end in port_protocol.keys():
                                                ace[end]['port_protocol'][
                                                    'range'][
                                                        'end'] = port_protocol[
                                                            end]
        return want

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
        if state != 'parsed':
            commands = [c.strip() for c in commands]
        return commands

    def _state_parsed(self, want):
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
        want_names = []
        if have_afi != want:
            if have_afi:
                del_dict.update({'afi': have_afi['afi'], 'acls': []})
                if want.get('acls'):
                    want_names = [w['name'] for w in want['acls']]
                    have_names = [h['name'] for h in have_afi['acls']]
                    want_acls = want.get('acls')
                    for w in want_acls:
                        acl_commands = []
                        if w['name'] not in have_names:
                            # creates new ACL in replaced state
                            merge_dict = {'afi': want['afi'], 'acls': [w]}
                            commands.extend(
                                self._state_merged(merge_dict, have))
                        else:
                            # acl in want exists in have
                            have_name = search_obj_in_list(
                                w['name'], have_afi['acls'], 'name')
                            have_aces = have_name.get('aces') if have_name.get(
                                'aces') else []
                            merge_aces = []
                            del_aces = []
                            w_aces = w.get('aces') if w.get('aces') else []

                            for ace in have_aces:
                                if ace not in w_aces:
                                    del_aces.append(ace)
                            for ace in w_aces:
                                if ace not in have_aces:
                                    merge_aces.append(ace)
                            merge_dict = {
                                'afi': want['afi'],
                                'acls': [{
                                    'name': w['name'],
                                    'aces': merge_aces
                                }]
                            }
                            del_dict = {
                                'afi': want['afi'],
                                'acls': [{
                                    'name': w['name'],
                                    'aces': del_aces
                                }]
                            }
                            if del_dict['acls']:
                                acl_commands.extend(
                                    self._state_deleted([del_dict], have))
                            acl_commands.extend(
                                self._state_merged(merge_dict, have))

                            for i in range(1, len(acl_commands)):
                                if acl_commands[i] == acl_commands[0]:
                                    acl_commands[i] = ''
                            commands.extend(acl_commands)
                else:
                    acls = []
                    # no acls given in want, so delete all have acls
                    for acl in have_afi['acls']:
                        acls.append({'name': acl['name']})
                    del_dict['acls'] = acls
                    if del_dict['acls']:
                        commands.extend(self._state_deleted([del_dict], have))

            else:
                # want_afi is not present in have
                commands.extend(self._state_merged(want, have))

        commands = list(filter(None, commands))
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        want_afi = [w['afi'] for w in want]
        for h in have:
            if h['afi'] in want_afi:
                w = search_obj_in_list(h['afi'], want, 'afi')
                for h_acl in h['acls']:
                    w_acl = search_obj_in_list(h_acl['name'], w['acls'],
                                               'name')
                    if not w_acl:
                        del_dict = {
                            'afi': h['afi'],
                            'acls': [{
                                'name': h_acl['name']
                            }]
                        }
                        commands.extend(self._state_deleted([del_dict], have))
            else:
                # if afi is not in want
                commands.extend(self._state_deleted([{'afi': h['afi']}], have))
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

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:  # and have != want:
            for w in want:
                ip = 'ipv6' if w['afi'] == 'ipv6' else 'ip'
                acl_names = []
                have_afi = search_obj_in_list(w['afi'], have, 'afi')
                # if want['afi] not in have, ignore
                if have_afi:
                    if w.get('acls'):
                        for acl in w['acls']:
                            if 'aces' in acl.keys():
                                have_name = search_obj_in_list(
                                    acl['name'], have_afi['acls'], 'name')
                                if have_name:
                                    ace_commands = []
                                    flag = 0
                                    for ace in acl['aces']:
                                        if list(ace.keys()) == ['sequence']:
                                            # only sequence number is specified to be deleted
                                            if 'aces' in have_name.keys():
                                                for h_ace in have_name['aces']:
                                                    if h_ace[
                                                            'sequence'] == ace[
                                                                'sequence']:
                                                        ace_commands.append(
                                                            'no ' +
                                                            str(ace['sequence']
                                                                ))
                                                        flag = 1
                                        else:
                                            if 'aces' in have_name.keys():
                                                for h_ace in have_name['aces']:
                                                    # when want['ace'] does not have seq number
                                                    if 'sequence' not in ace.keys(
                                                    ):
                                                        del h_ace['sequence']
                                                    if ace == h_ace:
                                                        ace_commands.append(
                                                            'no ' +
                                                            self.process_ace(
                                                                ace))
                                                        flag = 1
                                    if flag:
                                        ace_commands.insert(
                                            0,
                                            ip + ' access-list ' + acl['name'])
                                    commands.extend(ace_commands)
                            else:
                                # only name given
                                for h in have_afi['acls']:
                                    if h['name'] == acl['name']:
                                        acl_names.append(acl['name'])
                        for name in acl_names:
                            commands.append('no ' + ip + ' access-list ' +
                                            name)

                    else:
                        # 'only afi is given'
                        if have_afi.get('acls'):
                            for h in have_afi['acls']:
                                acl_names.append(h['name'])
                            for name in acl_names:
                                commands.append('no ' + ip + ' access-list ' +
                                                name)
        else:
            v6 = []
            v4 = []
            v6_local = v4_local = None
            for h in have:
                if h['afi'] == 'ipv6':
                    v6 = (acl['name'] for acl in h['acls'])
                    if 'match_local_traffic' in h.keys():
                        v6_local = True
                else:
                    v4 = (acl['name'] for acl in h['acls'])
                    if 'match_local_traffic' in h.keys():
                        v4_local = True

            self.no_commands(v4, commands, v4_local, 'ip')
            self.no_commands(v6, commands, v6_local, 'ipv6')

            for name in v6:
                commands.append('no ipv6 access-list ' + name)
            if v4_local:
                commands.append('no ipv6 access-list match-local-traffic')

        return commands

    def no_commands(self, v_list, commands, match_local, ip):
        for name in v_list:
            commands.append('no ' + ip + ' access-list ' + name)
        if match_local:
            commands.append('no ' + ip + ' access-list match-local-traffic')

    def set_commands(self, want, have):
        commands = []
        have_afi = search_obj_in_list(want['afi'], have, 'afi')
        ip = ''
        if 'v6' in want['afi']:
            ip = 'ipv6 '
        else:
            ip = 'ip '

        if have_afi:
            if want.get('acls'):
                for w_acl in want['acls']:
                    have_acl = search_obj_in_list(w_acl['name'],
                                                  have_afi['acls'], 'name')
                    name = w_acl['name']
                    flag = 0
                    ace_commands = []
                    if have_acl != w_acl:
                        if have_acl:
                            ace_list = []
                            if w_acl.get('aces') and have_acl.get('aces'):
                                # case 1 --> sequence number not given in want --> new ace
                                # case 2 --> new sequence number in want --> new ace
                                # case 3 --> existing sequence number given --> update rule (only for merged state.
                                #            For replaced and overridden, rule is deleted in the state's config)

                                ace_list = [
                                    item for item in w_acl['aces']
                                    if 'sequence' not in item.keys()
                                ]  # case 1

                                want_seq = [
                                    item['sequence'] for item in w_acl['aces']
                                    if 'sequence' in item.keys()
                                ]

                                have_seq = [
                                    item['sequence']
                                    for item in have_acl['aces']
                                ]

                                new_seq = list(set(want_seq) - set(have_seq))
                                common_seq = list(
                                    set(want_seq).intersection(set(have_seq)))

                                temp_list = [
                                    item for item in w_acl['aces']
                                    if 'sequence' in item.keys()
                                    and item['sequence'] in new_seq
                                ]  # case 2
                                ace_list.extend(temp_list)
                                for w in w_acl['aces']:
                                    self.argument_spec = AclsArgs.argument_spec
                                    params = utils.validate_config(
                                        self.argument_spec, {
                                            'config': [{
                                                'afi':
                                                want['afi'],
                                                'acls': [{
                                                    'name': name,
                                                    'aces': ace_list
                                                }]
                                            }]
                                        })
                                    if 'sequence' in w.keys(
                                    ) and w['sequence'] in common_seq:
                                        temp_obj = search_obj_in_list(
                                            w['sequence'], have_acl['aces'],
                                            'sequence')  # case 3
                                        if temp_obj != w:
                                            for key, val in w.items():
                                                temp_obj[key] = val
                                            ace_list.append(temp_obj)
                                            if self._module.params[
                                                    'state'] == 'merged':
                                                ace_commands.append(
                                                    'no ' + str(w['sequence']))
                                        # remove existing rule to update it
                            elif w_acl.get('aces'):
                                # 'have' has ACL defined without any ACE
                                ace_list = [item for item in w_acl['aces']]
                            for w_ace in ace_list:
                                ace_commands.append(
                                    self.process_ace(w_ace).strip())
                                flag = 1

                            if flag:
                                ace_commands.insert(0,
                                                    ip + 'access-list ' + name)

                        else:
                            commands.append(ip + 'access-list ' + name)
                            if 'aces' in w_acl.keys():
                                for w_ace in w_acl['aces']:
                                    commands.append(
                                        self.process_ace(w_ace).strip())
                    commands.extend(ace_commands)
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
        ace_keys = w_ace.keys()
        if 'remark' in ace_keys:
            command += 'remark ' + w_ace['remark'] + ' '
        else:
            command += w_ace['grant'] + ' '
            if 'protocol' in ace_keys:
                command += w_ace['protocol'] + ' '
                src = self.get_address(w_ace['source'], w_ace['protocol'])
                dest = self.get_address(w_ace['destination'],
                                        w_ace['protocol'])
                command += src + dest
                if 'protocol_options' in ace_keys:
                    pro = list(w_ace['protocol_options'].keys())[0]
                    if pro != w_ace['protocol']:
                        self._module.fail_json(
                            msg='protocol and protocol_options mismatch')
                    flags = ''
                    for k in w_ace['protocol_options'][pro].keys():
                        k = re.sub('_', '-', k)
                        flags += k + ' '
                    command += flags
                if 'dscp' in ace_keys:
                    command += 'dscp ' + w_ace['dscp'] + ' '
                if 'fragments' in ace_keys:
                    command += 'fragments '
                if 'precedence' in ace_keys:
                    command += 'precedence ' + w_ace['precedence'] + ' '
            if 'log' in ace_keys:
                command += 'log '
        if 'sequence' in ace_keys:
            command = str(w_ace['sequence']) + ' ' + command
        return command

    def get_address(self, endpoint, pro=''):
        ret_addr = ''
        keys = list(endpoint.keys())
        if 'address' in keys:
            if 'wildcard_bits' not in keys:
                self._module.fail_json(
                    msg='wildcard bits not specified for address')
            else:
                ret_addr = endpoint['address'] + \
                    ' ' + endpoint['wildcard_bits'] + ' '
        elif 'any' in keys:
            ret_addr = 'any '
        elif 'host' in keys:
            ret_addr = 'host ' + endpoint['host'] + ' '
        elif 'prefix' in keys:
            ret_addr = endpoint['prefix'] + ' '

        if pro in ['tcp', 'udp']:
            if 'port_protocol' in keys:
                options = self.get_options(endpoint['port_protocol'])
                ret_addr += options
        return ret_addr

    def get_options(self, item):
        com = ''
        subkey = list(item.keys())
        if 'range' in subkey:
            com = 'range ' + item['range']['start'] + \
                ' ' + item['range']['end'] + ' '
        else:
            com = subkey[0] + ' ' + item[subkey[0]] + ' '
        return com
