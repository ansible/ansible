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
short_description: Manage multiple pfSense rules or aliases
description:
  - Manage multiple pfSense rules or aliases
notes:
  - aggregated_aliases and aggregated_rules use the same options definitions
    than pfsense_alias and pfsense_rule modules.
options:
  aggregated_aliases:
    description: Dict of aliases to apply on the target
    required: False
  aggregated_rules:
    description: Dict of rules to apply on the target
    required: False
  aggregated_rule_separators:
    description: Dict of rule separators to apply on the target
    required: False
  aggregated_vlans:
    description: Dict of vlans to apply on the target
    required: False
  purge_aliases:
    description: delete all the aliases that are not defined into aggregated_aliases
    required: False
    type: bool
    default: False
  purge_rules:
    description: delete all the rules that are not defined into aggregated_rules
    required: False
    type: bool
    default: False
  purge_rule_separators:
    description: delete all the rule separators that are not defined into aggregated_rule_separators
    required: False
    type: bool
    default: False
  purge_vlans:
    description: delete all the vlans that are not defined into aggregated_vlans
    required: False
    type: bool
    default: False
"""

EXAMPLES = """
- name: "Add three aliases, six rules, four separators, and delete everything else"
  pfsense_aggregate:
    purge_aliases: true
    purge_rules: true
    purge_rule_separators: true
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
"""

RETURN = """
result_aliases:
    description: the set of aliases commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: success
    type: list
    sample: ["create alias 'adservers', type='host', address='10.0.0.1 10.0.0.2'", "update alias 'one_host' set address='10.9.8.7'", "delete alias 'one_alias'"]
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
from ansible.module_utils.network.pfsense.pfsense_alias import PFSenseAliasModule, ALIASES_ARGUMENT_SPEC, ALIASES_REQUIRED_IF
from ansible.module_utils.network.pfsense.pfsense_rule import PFSenseRuleModule, RULES_ARGUMENT_SPEC, RULES_REQUIRED_IF
from ansible.module_utils.network.pfsense.pfsense_rule_separator import PFSenseRuleSeparatorModule
from ansible.module_utils.network.pfsense.pfsense_rule_separator import RULE_SEPARATORS_ARGUMENT_SPEC
from ansible.module_utils.network.pfsense.pfsense_rule_separator import RULE_SEPARATORS_REQUIRED_ONE_OF
from ansible.module_utils.network.pfsense.pfsense_rule_separator import RULE_SEPARATORS_MUTUALLY_EXCLUSIVE
from ansible.module_utils.network.pfsense.pfsense_vlan import PFSenseVlanModule, VLANS_ARGUMENT_SPEC

from ansible.module_utils.basic import AnsibleModule


class PFSenseModuleAggregate(object):
    """ module managing pfsense aggregated aliases and rules """

    def __init__(self, module):
        self.module = module
        self.pfsense = PFSenseModule(module)
        self.pfsense_aliases = PFSenseAliasModule(module, self.pfsense)
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
        if self.pfsense_rules.changed or self.pfsense_rule_separators.result['changed']:
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
            for rule_elt in self.pfsense_rules.rules:
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
            for alias_elt in self.pfsense_aliases.aliases:
                if not self.want_alias(alias_elt, want):
                    params = {}
                    params['state'] = 'absent'
                    params['name'] = alias_elt.find('name').text
                    todel.append(params)

            for params in todel:
                self.pfsense_aliases.run(params)

    def run_rule_separators(self):
        """ process input params to add/update/delete all separators """
        want = self.module.params['aggregated_rule_separators']

        if want is None:
            return

        # processing aggregated parameter
        for param in want:
            self.pfsense_rule_separators.run(param)

        # delete every other alias if required
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

        # delete every other vlans if required
        if self.module.params['purge_vlans']:
            todel = []
            for vlan_elt in self.pfsense_vlans.vlans:
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
            self.pfsense_aliases.result['changed'] or self.pfsense_rules.changed
            or self.pfsense_rule_separators.result['changed'] or self.pfsense_vlans.result['changed']
        )

        if changed and not self.module.check_mode:
            self.pfsense.write_config(descr='aggregated change')
            (dummy, stdout, stderr) = self._update()

        result = {}
        result['result_aliases'] = self.pfsense_aliases.result['commands']
        result['result_rules'] = self.pfsense_rules.result['commands']
        result['result_rule_separators'] = self.pfsense_rule_separators.result['commands']
        result['result_vlans'] = self.pfsense_vlans.result['commands']
        result['changed'] = changed
        result['stdout'] = stdout
        result['stderr'] = stderr
        self.module.exit_json(**result)


def main():
    argument_spec = dict(
        aggregated_aliases=dict(type='list', elements='dict', options=ALIASES_ARGUMENT_SPEC, required_if=ALIASES_REQUIRED_IF),
        aggregated_rules=dict(type='list', elements='dict', options=RULES_ARGUMENT_SPEC, required_if=RULES_REQUIRED_IF),
        aggregated_rule_separators=dict(
            type='list', elements='dict',
            options=RULE_SEPARATORS_ARGUMENT_SPEC, required_one_of=RULE_SEPARATORS_REQUIRED_ONE_OF, mutually_exclusive=RULE_SEPARATORS_MUTUALLY_EXCLUSIVE),
        aggregated_vlans=dict(type='list', elements='dict', options=VLANS_ARGUMENT_SPEC),
        purge_aliases=dict(default=False, type='bool'),
        purge_rules=dict(default=False, type='bool'),
        purge_rule_separators=dict(default=False, type='bool'),
        purge_vlans=dict(default=False, type='bool'),
    )

    required_one_of = [['aggregated_aliases', 'aggregated_rules', 'aggregated_rule_separators', 'aggregated_vlans']]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=required_one_of,
        supports_check_mode=True)

    pfmodule = PFSenseModuleAggregate(module)

    pfmodule.run_aliases()
    pfmodule.run_rules()
    pfmodule.run_rule_separators()
    pfmodule.run_vlans()
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
