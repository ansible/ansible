#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_aggregate
version_added: "2.9"
author: Frederic Bor (@f-bor)
short_description: Manage multiple pfSense aliases, rules, rule separators, interfaces and vlans
description:
  - Manage multiple pfSense aliases, rules, rule separators, interfaces and vlans
notes:
  - aggregated_* use the same options definitions than pfsense corresponding module
options:
  aggregated_aliases:
    description: Dict of aliases to apply on the target
    required: False
    type: list
    suboptions:
      name:
        description: The name of the alias
        required: true
        type: str
      state:
        description: State in which to leave the alias
        required: true
        choices: [ "present", "absent" ]
        default: present
        type: str
      type:
        description: The type of the alias
        choices: [ "host", "network", "port", "urltable", "urltable_ports" ]
        default: null
        type: str
      address:
        description: The address of the alias. Use a space separator for multiple values
        default: null
        type: str
      descr:
        description: The description of the alias
        default: null
        type: str
      detail:
        description: The descriptions of the items. Use || separator between items
        default: null
        type: str
      updatefreq:
        description: Update frequency in days for urltable
        default: null
        type: int
  aggregated_interfaces:
    description: Dict of interfaces to apply on the target
    required: False
    type: list
    suboptions:
      state:
        description: State in which to leave the interface.
        required: true
        choices: [ "present", "absent" ]
        default: present
        type: str
      descr:
        description: Description (name) for the interface.
        required: true
        type: str
      interface:
        description: Network port to which assign the interface.
        required: true
        type: str
      enable:
        description: Enable interface.
        required: true
        type: bool
      ipv4_type:
        description: IPv4 Configuration Type.
        choices: [ "none", "static" ]
        default: 'none'
        type: str
      mac:
        description: Used to modify ("spoof") the MAC address of this interface.
        required: false
        type: str
      mtu:
        description: Maximum transmission unit
        required: false
        type: int
      mss:
        description: MSS clamping for TCP connections.
        required: false
        type: int
      speed_duplex:
        description: Set speed and duplex mode for this interface.
        required: false
        default: autoselect
        type: str
      ipv4_address:
        description: IPv4 Address.
        required: false
        type: str
      ipv4_prefixlen:
        description: IPv4 subnet prefix length.
        required: false
        default: 24
        type: int
      ipv4_gateway:
        description: IPv4 gateway for this interface.
        required: false
        type: str
      blockpriv:
        description: Blocks traffic from IP addresses that are reserved for private networks.
        required: false
        type: bool
      blockbogons:
        description: Blocks traffic from reserved IP addresses (but not RFC 1918) or not yet assigned by IANA.
        required: false
        type: bool
      create_ipv4_gateway:
        description: Create the specified IPv4 gateway if it does not exist
        required: false
        type: bool
      ipv4_gateway_address:
        description: IPv4 gateway address to set on the interface
        required: false
        type: str
  aggregated_rules:
    description: Dict of rules to apply on the target
    required: False
    type: list
    suboptions:
      name:
        description: The name the rule
        required: true
        default: null
        type: str
      action:
        description: The action of the rule
        required: true
        default: pass
        choices: [ "pass", "block", "reject" ]
        type: str
      state:
        description: State in which to leave the rule
        default: present
        choices: [ "present", "absent" ]
        type: str
      disabled:
        description: Is the rule disabled
        default: false
        type: bool
      interface:
        description: The interface for the rule
        required: true
        type: str
      floating:
        description: Is the rule floating
        type: bool
      direction:
        description: Direction floating rule applies to
        choices: [ "any", "in", "out" ]
        type: str
      ipprotocol:
        description: The IP protocol
        default: inet
        choices: [ "inet", "inet46", "inet6" ]
        type: str
      protocol:
        description: The protocol
        default: any
        choices: [ "any", "tcp", "udp", "tcp/udp", "icmp", "igmp" ]
        type: str
      source:
        description: The source address, in [!]{IP,HOST,ALIAS,any,(self)}[:port], IP:INTERFACE or NET:INTERFACE format
        required: true
        default: null
        type: str
      destination:
        description: The destination address, in [!]{IP,HOST,ALIAS,any,(self)}[:port], IP:INTERFACE or NET:INTERFACE format
        required: true
        default: null
        type: str
      log:
        description: Log packets matched by rule
        type: bool
      after:
        description: Rule to go after, or "top"
        type: str
      before:
        description: Rule to go before, or "bottom"
        type: str
      statetype:
        description: State type
        default: keep state
        choices: ["keep state", "sloppy state", "synproxy state", "none"]
        type: str
      queue:
        description: QOS default queue
        type: str
      ackqueue:
        description: QOS acknowledge queue
        type: str
      in_queue:
        description: Limiter queue for traffic coming into the chosen interface
        type: str
      out_queue:
        description: Limiter queue for traffic leaving the chosen interface
        type: str
      gateway:
        description: Leave as 'default' to use the system routing table or choose a gateway to utilize policy based routing.
        type: str
        default: default
  aggregated_rule_separators:
    description: Dict of rule separators to apply on the target
    required: False
    type: list
    suboptions:
      name:
        description: The name of the separator
        required: true
        type: str
      state:
        description: State in which to leave the separator
        required: true
        choices: [ "present", "absent" ]
        default: present
        type: str
      interface:
        description: The interface for the separator
        required: true
        type: str
      floating:
        description: Is the rule on floating tab
        type: bool
      after:
        description: Rule to go after, or "top"
        type: str
      before:
        description: Rule to go before, or "bottom"
        type: str
      color:
        description: The separator's color
        default: info
        choices: [ 'info', 'warning', 'danger', 'success' ]
        type: str
  aggregated_vlans:
    description: Dict of vlans to apply on the target
    required: False
    type: list
    suboptions:
      vlan_id:
        description: The vlan tag. Must be between 1 and 4094.
        required: true
        type: int
      interface:
        description: The interface on which to declare the vlan. Friendly name (assignments) can be used.
        required: true
        type: str
      priority:
        description: 802.1Q VLAN Priority code point. Must be between 0 and 7.
        required: false
        type: int
      descr:
        description: The description of the vlan
        default: null
        type: str
      state:
        description: State in which to leave the vlan
        required: true
        choices: [ "present", "absent" ]
        default: present
        type: str
  purge_aliases:
    description: delete all the aliases that are not defined into aggregated_aliases
    required: False
    default: False
    type: bool
  purge_interfaces:
    description: delete all the interfaces that are not defined into aggregated_interfaces
    required: False
    default: False
    type: bool
  purge_rules:
    description: delete all the rules that are not defined into aggregated_rules
    required: False
    default: False
    type: bool
  purge_rule_separators:
    description: delete all the rule separators that are not defined into aggregated_rule_separators
    required: False
    default: False
    type: bool
  purge_vlans:
    description: delete all the vlans that are not defined into aggregated_vlans
    required: False
    default: False
    type: bool
"""

EXAMPLES = """
- name: "Setup two vlans, three aliases, six rules, four separators, and delete everything else"
  pfsense_aggregate:
    purge_aliases: true
    purge_rules: true
    purge_rule_separators: true
    purge_vlans: true
    aggregated_aliases:
      - { name: port_ssh, type: port, address: 22, state: present }
      - { name: port_http, type: port, address: 80, state: present }
      - { name: port_https, type: port, address: 443, state: present }
    aggregated_rules:
      - { name: "allow_all_ssh", source: any, destination: "any:port_ssh", protocol: tcp, interface: lan, state: present }
      - { name: "allow_all_http", source: any, destination: "any:port_http", protocol: tcp, interface: lan, state: present }
      - { name: "allow_all_https", source: any, destination: "any:port_https", protocol: tcp, interface: lan, state: present }
      - { name: "allow_all_ssh", source: any, destination: "any:port_ssh", protocol: tcp, interface: wan, state: present }
      - { name: "allow_all_http", source: any, destination: "any:port_http", protocol: tcp, interface: wan, state: present }
      - { name: "allow_all_https", source: any, destination: "any:port_https", protocol: tcp, interface: wan, state: present }
    aggregated_rule_separators:
      - { name: "SSH", interface: lan, state: present, before: allow_all_ssh }
      - { name: "HTTP", interface: lan, state: present, before: allow_all_http }
      - { name: "SSH", interface: wan, state: present, before: allow_all_ssh }
      - { name: "HTTP", interface: wan, state: present, before: allow_all_http }
    aggregated_vlans:
      - { descr: voice, vlan_id: 100, interface: mvneta0, state: present }
      - { descr: video, vlan_id: 200, interface: mvneta0, state: present }
"""

RETURN = """
result_aliases:
    description: the set of aliases commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: success
    type: list
    sample: ["create alias 'adservers', type='host', address='10.0.0.1 10.0.0.2'", "update alias 'one_host' set address='10.9.8.7'", "delete alias 'one_alias'"]
result_interfaces:
    description: the set of interfaces commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: success
    type: list
    sample: ["create interface 'VOICE', port='mvneta1.100'", "create interface 'VIDEO', port='mvneta1.200'"]
aggregated_rules:
    description: final set of rules
    returned: success
    type: list
    sample: []
result_separators:
    description: the set of separators commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: success
    type: list
    sample: ["create rule_separator 'SSH', interface='lan', color='info'", "update rule_separator 'SSH' set color='warning'", "delete rule_separator 'SSH'"]
result_vlans:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: success
    type: list
    sample: ["create vlan 'mvneta.100', descr='voice', priority='5'", "update vlan 'mvneta.100', set priority='6'", "delete vlan 'mvneta.100'"]
"""

from ansible.module_utils.network.pfsense.pfsense import PFSenseModule
from ansible.module_utils.network.pfsense.alias import PFSenseAliasModule, ALIAS_ARGUMENT_SPEC, ALIAS_REQUIRED_IF
from ansible.module_utils.network.pfsense.interface import PFSenseInterfaceModule
from ansible.module_utils.network.pfsense.interface import INTERFACE_ARGUMENT_SPEC
from ansible.module_utils.network.pfsense.interface import INTERFACE_REQUIRED_IF
from ansible.module_utils.network.pfsense.rule import PFSenseRuleModule, RULE_ARGUMENT_SPEC, RULE_REQUIRED_IF
from ansible.module_utils.network.pfsense.rule_separator import PFSenseRuleSeparatorModule
from ansible.module_utils.network.pfsense.rule_separator import RULE_SEPARATOR_ARGUMENT_SPEC
from ansible.module_utils.network.pfsense.rule_separator import RULE_SEPARATOR_REQUIRED_ONE_OF
from ansible.module_utils.network.pfsense.rule_separator import RULE_SEPARATOR_MUTUALLY_EXCLUSIVE
from ansible.module_utils.network.pfsense.vlan import PFSenseVlanModule, VLAN_ARGUMENT_SPEC

from ansible.module_utils.basic import AnsibleModule


class PFSenseModuleAggregate(object):
    """ module managing pfsense aggregated aliases, rules, rule separators, interfaces and vlans """

    def __init__(self, module):
        self.module = module
        self.pfsense = PFSenseModule(module)
        self.pfsense_aliases = PFSenseAliasModule(module, self.pfsense)
        self.pfsense_interfaces = PFSenseInterfaceModule(module, self.pfsense)
        self.pfsense_rules = PFSenseRuleModule(module, self.pfsense)
        self.pfsense_rule_separators = PFSenseRuleSeparatorModule(module, self.pfsense)
        self.pfsense_vlans = PFSenseVlanModule(module, self.pfsense)

    def _update(self):
        run = False
        cmd = 'require_once("filter.inc");\n'
        cmd += 'if (filter_configure() == 0) { \n'
        if self.pfsense_aliases.result['changed']:
            run = True
            cmd += 'clear_subsystem_dirty(\'aliases\');\n'
        if self.pfsense_interfaces.result['changed']:
            run = True
            cmd += 'clear_subsystem_dirty(\'interfaces\');\n'
        if self.pfsense_rules.result['changed'] or self.pfsense_rule_separators.result['changed']:
            run = True
            cmd += 'clear_subsystem_dirty(\'filter\');\n'
        cmd += '}'
        if run:
            return self.pfsense.phpshell(cmd)

        return ('', '', '')

    def want_rule(self, rule_elt, rules):
        """ return True if we want to keep rule_elt """
        descr = rule_elt.find('descr')
        interface = rule_elt.find('interface')

        # probably not a rule
        if descr is None or interface is None:
            return True

        for rule in rules:
            if rule['state'] == 'absent':
                continue
            if rule['name'] == descr.text and self.pfsense.parse_interface(rule['interface']) == interface.text:
                return True
        return False

    def want_rule_separator(self, separator_elt, rule_separators):
        """ return True if we want to keep separator_elt """
        name = separator_elt.find('text').text
        interface = separator_elt.find('if').text

        for separator in rule_separators:
            if separator['state'] == 'absent':
                continue
            if separator['name'] != name:
                continue
            if self.pfsense.parse_interface(separator['interface']) == interface or interface == 'floatingrules' and separator.get('floating'):
                return True
        return False

    @staticmethod
    def want_alias(alias_elt, aliases):
        """ return True if we want to keep alias_elt """
        name = alias_elt.find('name')
        alias_type = alias_elt.find('type')

        # probably not an alias
        if name is None or type is None:
            return True

        for alias in aliases:
            if alias['state'] == 'absent':
                continue
            if alias['name'] == name.text and alias['type'] == alias_type.text:
                return True
        return False

    def want_interface(self, interface_elt, interfaces):
        """ return True if we want to keep interface_elt """
        descr_elt = interface_elt.find('descr')
        if descr_elt is not None and descr_elt.text:
            name = descr_elt.text
        else:
            name = interface_elt.tag

        for interface in interfaces:
            if interface['state'] == 'absent':
                continue
            if interface['descr'] == name:
                return True
        return False

    @staticmethod
    def want_vlan(vlan_elt, vlans):
        """ return True if we want to keep vlan_elt """
        tag = int(vlan_elt.find('tag').text)
        interface = vlan_elt.find('if')

        for vlan in vlans:
            if vlan['state'] == 'absent':
                continue
            if vlan['vlan_id'] == tag and vlan['interface'] == interface.text:
                return True
        return False

    def run_rules(self):
        """ process input params to add/update/delete all rules """
        want = self.module.params['aggregated_rules']

        if want is None:
            return

        # delete every other rule if required
        if self.module.params['purge_rules']:
            todel = []
            for rule_elt in self.pfsense_rules.root_elt:
                if not self.want_rule(rule_elt, want):
                    params = {}
                    params['state'] = 'absent'
                    params['name'] = rule_elt.find('descr').text
                    params['interface'] = rule_elt.find('interface').text
                    if rule_elt.find('floating') is not None:
                        params['floating'] = True
                    todel.append(params)

            for params in todel:
                self.pfsense_rules.run(params)

        # processing aggregated parameters
        for params in want:
            self.pfsense_rules.run(params)

    def run_aliases(self):
        """ process input params to add/update/delete all aliases """
        want = self.module.params['aggregated_aliases']

        if want is None:
            return

        # processing aggregated parameter
        for param in want:
            self.pfsense_aliases.run(param)

        # delete every other alias if required
        if self.module.params['purge_aliases']:
            todel = []
            for alias_elt in self.pfsense_aliases.root_elt:
                if not self.want_alias(alias_elt, want):
                    params = {}
                    params['state'] = 'absent'
                    params['name'] = alias_elt.find('name').text
                    todel.append(params)

            for params in todel:
                self.pfsense_aliases.run(params)

    def run_interfaces(self):
        """ process input params to add/update/delete all interfaces """
        want = self.module.params['aggregated_interfaces']

        if want is None:
            return

        # processing aggregated parameter
        for param in want:
            self.pfsense_interfaces.run(param)

        # delete every other if required
        if self.module.params['purge_interfaces']:
            todel = []
            for interface_elt in self.pfsense_interfaces.interfaces:
                if not self.want_interface(interface_elt, want):
                    params = {}
                    params['state'] = 'absent'
                    descr_elt = interface_elt.find('descr')
                    if descr_elt is not None and descr_elt.text:
                        params['descr'] = descr_elt.text
                        todel.append(params)

            for params in todel:
                self.pfsense_interfaces.run(params)

    def run_rule_separators(self):
        """ process input params to add/update/delete all separators """
        want = self.module.params['aggregated_rule_separators']

        if want is None:
            return

        # processing aggregated parameter
        for param in want:
            self.pfsense_rule_separators.run(param)

        # delete every other if required
        if self.module.params['purge_rule_separators']:
            todel = []
            for interface_elt in self.pfsense_rule_separators.separators:
                for separator_elt in interface_elt:
                    if not self.want_rule_separator(separator_elt, want):
                        params = {}
                        params['state'] = 'absent'
                        params['name'] = separator_elt.find('text').text
                        if interface_elt.tag == 'floatingrules':
                            params['floating'] = True
                        else:
                            params['interface'] = interface_elt.tag
                        todel.append(params)

            for params in todel:
                self.pfsense_rule_separators.run(params)

    def run_vlans(self):
        """ process input params to add/update/delete all vlans """
        want = self.module.params['aggregated_vlans']

        if want is None:
            return

        # processing aggregated parameter
        for param in want:
            self.pfsense_vlans.run(param)

        # delete every other if required
        if self.module.params['purge_vlans']:
            todel = []
            for vlan_elt in self.pfsense_vlans.root_elt:
                if not self.want_vlan(vlan_elt, want):
                    params = {}
                    params['state'] = 'absent'
                    params['interface'] = vlan_elt.find('if').text
                    params['vlan_id'] = int(vlan_elt.find('tag').text)
                    todel.append(params)

            for params in todel:
                self.pfsense_vlans.run(params)

    def commit_changes(self):
        """ apply changes and exit module """
        stdout = ''
        stderr = ''
        changed = (
            self.pfsense_aliases.result['changed'] or self.pfsense_interfaces.result['changed'] or self.pfsense_rules.result['changed']
            or self.pfsense_rule_separators.result['changed'] or self.pfsense_vlans.result['changed']
        )

        if changed and not self.module.check_mode:
            self.pfsense.write_config(descr='aggregated change')
            (dummy, stdout, stderr) = self._update()

        result = {}
        result['result_aliases'] = self.pfsense_aliases.result['commands']
        result['result_interfaces'] = self.pfsense_interfaces.result['commands']
        result['result_rules'] = self.pfsense_rules.result['commands']
        result['result_rule_separators'] = self.pfsense_rule_separators.result['commands']
        result['result_vlans'] = self.pfsense_vlans.result['commands']
        result['changed'] = changed
        result['stdout'] = stdout
        result['stderr'] = stderr
        self.module.exit_json(**result)


def main():
    argument_spec = dict(
        aggregated_aliases=dict(type='list', elements='dict', options=ALIAS_ARGUMENT_SPEC, required_if=ALIAS_REQUIRED_IF),
        aggregated_interfaces=dict(type='list', elements='dict', options=INTERFACE_ARGUMENT_SPEC, required_if=INTERFACE_REQUIRED_IF),
        aggregated_rules=dict(type='list', elements='dict', options=RULE_ARGUMENT_SPEC, required_if=RULE_REQUIRED_IF),
        aggregated_rule_separators=dict(
            type='list', elements='dict',
            options=RULE_SEPARATOR_ARGUMENT_SPEC, required_one_of=RULE_SEPARATOR_REQUIRED_ONE_OF, mutually_exclusive=RULE_SEPARATOR_MUTUALLY_EXCLUSIVE),
        aggregated_vlans=dict(type='list', elements='dict', options=VLAN_ARGUMENT_SPEC),
        purge_aliases=dict(default=False, type='bool'),
        purge_interfaces=dict(default=False, type='bool'),
        purge_rules=dict(default=False, type='bool'),
        purge_rule_separators=dict(default=False, type='bool'),
        purge_vlans=dict(default=False, type='bool'),
    )

    required_one_of = [['aggregated_aliases', 'aggregated_interfaces', 'aggregated_rules', 'aggregated_rule_separators', 'aggregated_vlans']]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=required_one_of,
        supports_check_mode=True)

    pfmodule = PFSenseModuleAggregate(module)

    pfmodule.run_vlans()
    pfmodule.run_interfaces()

    pfmodule.run_aliases()
    pfmodule.run_rules()
    pfmodule.run_rule_separators()

    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
