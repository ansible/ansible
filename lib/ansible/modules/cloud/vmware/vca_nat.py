#!/usr/bin/python

# Copyright (c) 2015 VMware, Inc. All Rights Reserved.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vca_nat
short_description: add remove nat rules in a gateway  in a vca
description:
  - Adds or removes nat rules from a gateway in a vca environment
version_added: "2.0"
author: Peter Sprygada (@privateip)
options:
    purge_rules:
      description:
        - If set to true, it will delete all rules in the gateway that are not given as parameter to this module.
      required: false
      default: false
    nat_rules:
      description:
        - A list of rules to be added to the gateway, Please see examples on valid entries
      required: True
      default: false
extends_documentation_fragment: vca.documentation
'''

EXAMPLES = '''

#An example for a source nat

- hosts: localhost
  connection: local
  tasks:
   - vca_nat:
       instance_id: 'b15ff1e5-1024-4f55-889f-ea0209726282'
       vdc_name: 'benz_ansible'
       state: 'present'
       nat_rules:
         - rule_type: SNAT
           original_ip: 192.0.2.42
           translated_ip: 203.0.113.23

#example for a DNAT
- hosts: localhost
  connection: local
  tasks:
   - vca_nat:
       instance_id: 'b15ff1e5-1024-4f55-889f-ea0209726282'
       vdc_name: 'benz_ansible'
       state: 'present'
       nat_rules:
         - rule_type: DNAT
           original_ip: 203.0.113.23
           original_port: 22
           translated_ip: 192.0.2.42
           translated_port: 22

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vca import VcaError, vca_argument_spec, vca_login


VALID_RULE_KEYS = ['rule_type', 'original_ip', 'original_port',
                   'translated_ip', 'translated_port', 'protocol']


def validate_nat_rules(nat_rules):
    for rule in nat_rules:
        if not isinstance(rule, dict):
            raise VcaError("nat rules must be a list of dictionaries, "
                           "Please check", valid_keys=VALID_RULE_KEYS)

        for k in rule.keys():
            if k not in VALID_RULE_KEYS:
                raise VcaError("%s is not a valid key in nat rules, please "
                               "check above.." % k, valid_keys=VALID_RULE_KEYS)

        rule['original_port'] = str(rule.get('original_port', 'any')).lower()
        rule['original_ip'] = rule.get('original_ip', 'any').lower()
        rule['translated_ip'] = rule.get('translated_ip', 'any').lower()
        rule['translated_port'] = str(rule.get('translated_port', 'any')).lower()
        rule['protocol'] = rule.get('protocol', 'any').lower()
        rule['rule_type'] = rule.get('rule_type', 'DNAT').lower()

    return nat_rules


def nat_rules_to_dict(nat_rules):
    result = []
    for rule in nat_rules:
        gw_rule = rule.get_GatewayNatRule()
        result.append(
            dict(
                rule_type=rule.get_RuleType().lower(),
                original_ip=gw_rule.get_OriginalIp().lower(),
                original_port=(gw_rule.get_OriginalPort().lower() or 'any'),
                translated_ip=gw_rule.get_TranslatedIp().lower(),
                translated_port=(gw_rule.get_TranslatedPort().lower() or 'any'),
                protocol=(gw_rule.get_Protocol().lower() or 'any')
            )
        )
    return result

def rule_to_string(rule):
    strings = list()
    for key, value in rule.items():
        strings.append('%s=%s' % (key, value))
    return ', '.join(strings)

def main():
    argument_spec = vca_argument_spec()
    argument_spec.update(
        dict(
            nat_rules = dict(type='list', default=[]),
            gateway_name = dict(default='gateway'),
            purge_rules = dict(default=False, type='bool'),
            state = dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    vdc_name = module.params.get('vdc_name')
    nat_rules = module.params['nat_rules']
    gateway_name = module.params['gateway_name']
    purge_rules = module.params['purge_rules']

    if not purge_rules and not nat_rules:
        module.fail_json(msg='Must define purge_rules or nat_rules')

    vca = vca_login(module)

    gateway = vca.get_gateway(vdc_name, gateway_name)
    if not gateway:
        module.fail_json(msg="Not able to find the gateway %s, please check "
                             "the gateway_name param" % gateway_name)

    try:
        desired_rules = validate_nat_rules(nat_rules)
    except VcaError as e:
        module.fail_json(msg=e.message)

    rules = gateway.get_nat_rules()

    result = dict(changed=False, rules_purged=0)

    deletions = 0
    additions = 0

    if purge_rules is True and len(rules) > 0:
        result['rules_purged'] = len(rules)
        deletions = result['rules_purged']
        rules = list()
        if not module.check_mode:
            gateway.del_all_nat_rules()
            task = gateway.save_services_configuration()
            vca.block_until_completed(task)
            rules = gateway.get_nat_rules()
        result['changed'] = True

    current_rules = nat_rules_to_dict(rules)

    result['current_rules'] = current_rules
    result['desired_rules'] = desired_rules

    for rule in desired_rules:
        if rule not in current_rules:
            additions += 1
            if not module.check_mode:
                gateway.add_nat_rule(**rule)
            result['changed'] = True
    result['rules_added'] = additions

    result['delete_rule'] = list()
    result['delete_rule_rc'] = list()
    for rule in current_rules:
        if rule not in desired_rules:
            deletions += 1
            if not module.check_mode:
                result['delete_rule'].append(rule)
                rc = gateway.del_nat_rule(**rule)
                result['delete_rule_rc'].append(rc)
            result['changed'] = True
    result['rules_deleted'] = deletions

    if not module.check_mode and (additions > 0 or deletions > 0):
        task = gateway.save_services_configuration()
        vca.block_until_completed(task)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
