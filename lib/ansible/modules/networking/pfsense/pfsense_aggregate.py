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
version_added: "2.8"
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
"""

EXAMPLES = """
- name: "Add three aliases, six rules, and delete everything else"
  pfsense_aggregate:
    purge_aliases: true
    purge_rules: true
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
"""

from ansible.module_utils.networking.pfsense.pfsense import PFSenseModule
from ansible.module_utils.networking.pfsense.pfsense_rule import PFSenseRuleModule, RULES_ARGUMENT_SPEC, RULES_REQUIRED_IF
from ansible.module_utils.networking.pfsense.pfsense_alias import PFSenseAliasModule, ALIASES_ARGUMENT_SPEC, ALIASES_REQUIRED_IF
from ansible.module_utils.basic import AnsibleModule


class PFSenseModuleAggregate(object):
    """ module managing pfsense aggregated aliases and rules """

    def __init__(self, module):
        self.module = module
        self.pfsense = PFSenseModule(module)
        self.pfsense_rules = PFSenseRuleModule(module, self.pfsense)
        self.pfsense_aliases = PFSenseAliasModule(module, self.pfsense)

    def _update(self):
        cmd = 'require_once("filter.inc");\n'
        cmd += 'if (filter_configure() == 0) { \n'
        if self.pfsense_aliases.result['changed']:
            cmd += 'clear_subsystem_dirty(\'aliases\');\n'
        if self.pfsense_rules.changed:
            cmd += 'clear_subsystem_dirty(\'rules\');\n'
        cmd += '}'
        return self.pfsense.phpshell(cmd)

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
            if rule['name'] == descr.text and self.pfsense_rules._parse_interface(rule['interface']) == interface.text:
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

    def run_rules(self):
        """ process input params to add/update/delete all rules """
        want = self.module.params['aggregated_rules']

        if want is None:
            return

        # processing aggregated parameter
        for param in want:
            self.pfsense_rules.run(param)

        # delete every other rule if required
        if self.module.params['purge_rules']:
            todel = []
            for rule_elt in self.pfsense_rules.rules:
                if not self.want_rule(rule_elt, want):
                    todel.append(rule_elt)

            for rule_elt in todel:
                self.pfsense_rules._remove_rule_elt(rule_elt)

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
                    todel.append(alias_elt)

            for alias_elt in todel:
                alias = {}
                alias['name'] = alias_elt.find('name').text
                self.pfsense_aliases.remove(alias)

    def commit_changes(self):
        """ apply changes and exit module """
        stdout = ''
        stderr = ''
        changed = self.pfsense_aliases.result['changed'] or self.pfsense_rules.changed
        if changed and not self.module.check_mode:
            self.pfsense.write_config(descr='aggregated change')
            (_, stdout, stderr) = self._update()

        result = {}
        result['result_aliases'] = self.pfsense_aliases.result['commands']
        result['aggregated_rules'] = {}
        result['aggregated_rules'].update(self.pfsense_rules.results)
        result['changed'] = changed
        result['stdout'] = stdout
        result['stderr'] = stderr
        self.module.exit_json(**result)


def main():
    argument_spec = dict(
        aggregated_aliases=dict(type='list', elements='dict', options=ALIASES_ARGUMENT_SPEC, required_if=ALIASES_REQUIRED_IF),
        aggregated_rules=dict(type='list', elements='dict', options=RULES_ARGUMENT_SPEC, required_if=RULES_REQUIRED_IF),
        purge_aliases=dict(default=False, type='bool'),
        purge_rules=dict(default=False, type='bool'),
    )

    required_one_of = [['aggregated_aliases', 'aggregated_rules']]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=required_one_of,
        supports_check_mode=True)

    pfmodule = PFSenseModuleAggregate(module)

    pfmodule.run_aliases()
    pfmodule.run_rules()
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
