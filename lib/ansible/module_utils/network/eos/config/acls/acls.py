#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_acls class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
import socket
import re
import itertools
import q

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.utils import remove_empties, dict_diff
from ansible.module_utils.network.eos.facts.facts import Facts

class Acls(ConfigBase):
    """
    The eos_acls class
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
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources, data=data)
        acls_facts = facts['ansible_network_resources'].get('acls')
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
        changed = False

        if self.state in self.ACTION_STATES:
            existing_acls_facts = self.get_acls_facts()
        else:
            existing_acls_facts = []
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_acls_facts))
        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
                changed = True
            if changed:
                result['changed'] = True
        if self.state in self.ACTION_STATES:
            result['commands'] = commands
        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_acls_facts = self.get_acls_facts()
        elif self.state == 'rendered':
            commands = list(itertools.chain(*commands))
            result['rendered'] = commands
        elif self.state == 'parsed':
            if not self._module.params['running_config']:
                self._module.fail_json(msg="Value of running_config parameter must not be empty for state parsed")
            result['parsed'] = self.get_acls_facts(data=self._module.params['running_config'])
        else:
            changed_acls_facts = []
        if self.state in self.ACTION_STATES:
            result['before'] = existing_acls_facts
            if result['changed']:
                result['after'] = changed_acls_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_acls_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_acls_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params.get('config')
        want = []
        onbox_configs = []
        for h in existing_acls_facts:
            have_configs = add_commands(remove_empties(h))
            onbox_configs.append(have_configs)
        if config:
            for w in config:
                want.append(remove_empties(w))
        have = existing_acls_facts
        resp = self.set_state(want, have)
        if self.state == 'merged':
            to_config = self.compare_configs(onbox_configs, to_list(resp))
        else:
            to_config = resp
        return to_config

    def compare_configs(self, have, want):
        commands = []
        want = list(itertools.chain(*want))
        have = list(itertools.chain(*have))
        h_index = 0
        config = list(want)
        q(want, have)
        for w in want:
            access_list = re.findall(r'(ip.*) access-list (.*)', w)
            if access_list:
                if w in have:
                    h_index = have.index(w)
            else:
                for num, h in enumerate(have, start=h_index + 1):
                    if "access-list" not in h:
                        seq_num = re.search(r'(\d+) (.*)', w)
                        if seq_num:
                            have_seq_num = re.search(r'(\d+) (.*)', h)
                            if seq_num.group(1) == have_seq_num.group(1) and have_seq_num.group(2) != seq_num.group(2):
                                negate_cmd = "no " + seq_num.group(1)
                                config.insert(config.index(w), negate_cmd)
                        if w in h:
                            config.pop(config.index(w))
                            break
        q(config)
        for c in config:
            access_list = re.findall(r'(ip.*) access-list (.*)', c)
            if access_list:
                acl_index = config.index(c)
            else:
                if config[acl_index] not in commands:
                    commands.append(config[acl_index])
                commands.append(c)
        return commands

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if self.state in ('merged', 'replaced', 'overridden') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(self.state))
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged' or self.state == 'rendered':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        have_commands = []
        remove_cmds = []
        ace_diff = {}
        present = False
        for w in want:
            afi = "ipv6" if w["afi"] == "ipv6" else "ipv4"
            for acl in w["acls"]:
                name = acl["name"]
                want_ace = acl["aces"]
        for h in have:
            if h["afi"] == afi:
                for h_acl in h["acls"]:
                    if h_acl["name"] == name:
                        present = True
                        h = {"afi": afi, "acls":[{"name": name}]}
                        ace_diff = get_ace_diff(want_ace, h_acl["aces"])
                        if ace_diff:
                            remove_cmds = del_commands(h, have)
        if ace_diff or not present:
            config_cmds = set_commands(want, have)
            config_cmds = list(itertools.chain(*config_cmds))
            for cmd in have:
                have_configs = add_commands(cmd)
                have_commands.append(have_configs)
            have_commands = list(itertools.chain(*have_commands))
            if remove_cmds:
                commands.append(remove_cmds)
            commands.append(config_cmds)
            commands = list(itertools.chain(*commands))
        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        present = False
        ace_diff = {}
        for w in want:
            afi = "ipv6" if w["afi"] == "ipv6" else "ipv4"
            for acl in w["acls"]:
                name = acl["name"]
                want_ace = acl["aces"]

        for h in have:
            if h["afi"] != afi:
                h = {"afi": h["afi"]}
                remove_cmds = del_commands(h, have)
                commands.append(remove_cmds)
                continue
            for h_acl in h["acls"]:
                if h_acl["name"] == name:
                    present = True
                    ace_diff = get_ace_diff(want_ace, h_acl["aces"])
                    if ace_diff:
                        h = {"afi": afi, "acls":[{"name": name, "aces": h_acl["aces"]}]}
                        remove_cmds = del_commands(h, have)
                        commands.append(remove_cmds)
                else:
                   h = {"afi": afi, "acls":[{"name": h_acl["name"]}]}
                   remove_cmds = del_commands(h, have)
                   commands.append(remove_cmds)
                    
        if ace_diff:
            config_cmds = set_commands(want, have)
            config_cmds = list(itertools.chain(*config_cmds))
            commands.append(config_cmds)
        if commands:
            commands = list(itertools.chain(*commands))
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return set_commands(want, have)

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if not want:
            for h in have:
                return_command = add_commands(h)
                for command in return_command:
                    command = "no " + command
                    commands.append(command)
        else:
            for w in want:
                return_command = del_commands(w, have)
                commands.append(return_command)
        commands = list(itertools.chain(*commands))
        return commands

def set_commands(want, have):
    commands = []
    for w in want:
        return_command = add_commands(w)
        commands.append(return_command)
    return commands

def add_commands(want):
    commandset = []
    protocol_name = {"51": "ahp", "47": "gre", "1": "icmp", "2": "igmp",\
                    "4": "ip", "89": "ospf", "103": "pim", "6": "tcp",\
                    "17": "udp", "112": "vrrp"}
    if not want:
        return commandset
    command = ""
    afi = "ip" if want["afi"] == "ipv4" else "ipv6"
    for acl in want["acls"]:
        if "standard" in acl.keys() and acl["standard"]:
            command = afi + " access-list standard " + acl["name"]
        else:
            command = afi + " access-list " + acl["name"]
        commandset.append(command)
        if "aces" not in acl.keys():
            continue
        for ace in acl["aces"]:
            command = ""
            if "sequence" in ace.keys():
                command = str(ace["sequence"])
            if "remark" in ace.keys():
                command = command + " remark " + ace["remark"]
            if "fragment_rules" in ace.keys() and ace["fragment_rules"]:
                command = command + " fragment-rules"
            if "grant" in ace.keys():
                command = command + " " + ace["grant"]
            if "vlan" in ace.keys():
                command = command + " vlan " + ace["vlan"]
            if "protocol" in ace.keys():
                protocol = ace["protocol"]
                if protocol.isdigit():
                    if protocol in protocol_name.keys():
                        protocol = protocol_name[protocol]
                command = command + " " + protocol
            if "source" in ace.keys():
                if "any" in ace["source"].keys():
                    command = command + " any"
                elif "subnet_address" in ace["source"].keys():
                    command = command + " " + ace["source"]["subnet_address"]
                elif "host" in ace["source"].keys():
                    command = command + " host " + ace["source"]["host"]
                elif "address" in ace["source"].keys():
                    command = command + " " + ace["source"]["address"] + " " + ace["source"]["wildcard_bits"]
                if "port_protocol" in ace["source"].keys():
                    for op, val in ace["source"]["port_protocol"].items():
                        if val.isdigit():
                            val = socket.getservbyport(int(val))
                        command = command + " " + op + " " + val
            if "destination" in ace.keys():
                if "any" in ace["destination"].keys():
                    command = command + " any"
                elif "subnet_address" in ace["destination"].keys():
                    command = command + " " + ace["destination"]["subnet_address"]
                elif "host" in ace["destination"].keys():
                    command = command + " host " + ace["destination"]["host"]
                elif "address" in ace["destination"].keys():
                    command = command + " " + ace["destination"]["address"] + " " + ace["destination"]["wildcard_bits"]
                if "port_protocol" in ace["destination"].keys():
                    for op in ace["destination"]["port_protocol"].keys():
                        command = command + " " + op + " " + ace["destination"]["port_protocol"][op]
            if "protocol_options" in ace.keys():
                for proto in ace["protocol_options"].keys():
                    if proto == "icmp" or proto == "icmpv6":
                        for icmp_msg in ace["protocol_options"][proto].keys():
                            command = command + " " + icmp_msg
                    elif proto == "ip" or proto == "ipv6":
                        command = command + " nexthop-group " + ace["protocol_options"][proto]["nexthop_group"]
                    elif proto == "tcp":
                        for flag, val in ace["prtocol_options"][proto]["flags"].items():
                            command = command + " " + val
            if "hop_limit" in ace.keys():
                for op, val in ace["hop_limit"].items():
                    command = command + " hop-limit " + op + " " + val
            if "tracked" in  ace.keys() and ace["tracked"]:
                command = command + " tracked"
            if "ttl" in ace.keys():
                for op, val in ace["ttl"].items():
                    command = command + " ttl " + op + " " + str(val)
            if "fragments" in ace.keys():
                command = command + " fragments"
            if "log" in ace.keys():
                command = command + " log"
            commandset.append(command.strip())
    return commandset

def del_commands(want, have):
    commandset = []
    command = ""
    have_command = []
    for h in have:
        have_configs = add_commands(h)
        have_command.append(have_configs)
    have_command = list(itertools.chain(*have_command))
    afi = "ip" if want["afi"] == "ipv4" else "ipv6"
    if "acls" not in want.keys():
        for have_cmd in have_command:
            access_list = re.search(r'(ip.*)\s+access-list .*', have_cmd)
            if access_list and access_list.group(1) == afi:
                commandset.append("no " + have_cmd)
        return commandset

    for acl in want["acls"]:
        ace_present = True
        if "standard" in acl.keys() and acl["standard"]:
            command = afi + " access-list standard " + acl["name"]
        else:
            command = afi + " access-list " + acl["name"]
        if "aces" not in acl.keys():
            ace_present = False
            commandset.append("no " + command)
    if ace_present:
        return_command = add_commands(want)
        for cmd in return_command:
            if "access-list" in cmd:
                commandset.append(cmd)
                continue
            seq = re.search(r'(\d+) (permit|deny|fragment-rules|remark) .*', cmd)
            if seq:
                commandset.append("no " + seq.group(1))
            else:
                commandset.append("no " + cmd)
    return commandset

def get_ace_diff( want_ace, have_ace):
    d = dict_diff(want_ace[0], have_ace[0])
    return d
