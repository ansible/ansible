#!/usr/bin/python

# Copyright (c) 2015 VMware, Inc. All Rights Reserved.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
module: vca_fw
short_description: add remove firewall rules in a gateway  in a vca
description:
  - Adds or removes firewall rules from a gateway in a vca environment
version_added: "2.0"
author: Peter Sprygada (@privateip)
options:
    fw_rules:
      description:
        - A list of firewall rules to be added to the gateway, Please see examples on valid entries
      required: True
      default: false
extends_documentation_fragment: vca.documentation
'''

EXAMPLES = '''

#Add a set of firewall rules

- hosts: localhost
  connection: local
  tasks:
   - vca_fw:
       instance_id: 'b15ff1e5-1024-4f55-889f-ea0209726282'
       vdc_name: 'benz_ansible'
       state: 'absent'
       fw_rules:
         - description: "ben testing"
           source_ip: "Any"
           dest_ip: 192.0.2.23
         - description: "ben testing 2"
           source_ip: 192.0.2.50
           source_port: "Any"
           dest_port: "22"
           dest_ip: 192.0.2.101
           is_enable: "true"
           enable_logging: "false"
           protocol: "Tcp"
           policy: "allow"

'''

try:
    from pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType import FirewallRuleType
    from pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType import ProtocolsType
except ImportError:
    # normally set a flag here but it will be caught when testing for
    # the existence of pyvcloud (see module_utils/vca.py).  This just
    # protects against generating an exception at runtime
    pass

VALID_PROTO = ['Tcp', 'Udp', 'Icmp', 'Other', 'Any']
VALID_RULE_KEYS = ['policy', 'is_enable', 'enable_logging', 'description',
                   'dest_ip', 'dest_port', 'source_ip', 'source_port',
                   'protocol']

def protocol_to_tuple(protocol):
    return (protocol.get_Tcp(),
            protocol.get_Udp(),
            protocol.get_Icmp(),
            protocol.get_Other(),
            protocol.get_Any())

def protocol_to_string(protocol):
    protocol = protocol_to_tuple(protocol)
    if protocol[0] is True:
        return 'Tcp'
    elif protocol[1] is True:
        return 'Udp'
    elif protocol[2] is True:
        return 'Icmp'
    elif protocol[3] is True:
        return 'Other'
    elif protocol[4] is True:
        return 'Any'

def protocol_to_type(protocol):
    try:
        protocols = ProtocolsType()
        setattr(protocols, protocol, True)
        return protocols
    except AttributeError:
        raise VcaError("The value in protocol is not valid")

def validate_fw_rules(fw_rules):
    for rule in fw_rules:
        for k in rule.keys():
            if k not in VALID_RULE_KEYS:
                raise VcaError("%s is not a valid key in fw rules, please "
                               "check above.." % k, valid_keys=VALID_RULE_KEYS)

        rule['dest_port'] = str(rule.get('dest_port', 'Any')).lower()
        rule['dest_ip'] = rule.get('dest_ip', 'Any').lower()
        rule['source_port'] = str(rule.get('source_port', 'Any')).lower()
        rule['source_ip'] = rule.get('source_ip', 'Any').lower()
        rule['protocol'] = rule.get('protocol', 'Any').lower()
        rule['policy'] = rule.get('policy', 'allow').lower()
        rule['is_enable'] = rule.get('is_enable', True)
        rule['enable_logging'] = rule.get('enable_logging', False)
        rule['description'] = rule.get('description', 'rule added by Ansible')

    return fw_rules

def fw_rules_to_dict(rules):
    fw_rules = list()
    for rule in rules:
        fw_rules.append(
            dict(
                dest_port=rule.get_DestinationPortRange().lower(),
                dest_ip=rule.get_DestinationIp().lower().lower(),
                source_port=rule.get_SourcePortRange().lower(),
                source_ip=rule.get_SourceIp().lower(),
                protocol=protocol_to_string(rule.get_Protocols()).lower(),
                policy=rule.get_Policy().lower(),
                is_enable=rule.get_IsEnabled(),
                enable_logging=rule.get_EnableLogging(),
                description=rule.get_Description()
            )
        )
    return fw_rules

def create_fw_rule(is_enable, description, policy, protocol, dest_port,
                   dest_ip, source_port, source_ip, enable_logging):

    return FirewallRuleType(IsEnabled=is_enable,
                            Description=description,
                            Policy=policy,
                            Protocols=protocol_to_type(protocol),
                            DestinationPortRange=dest_port,
                            DestinationIp=dest_ip,
                            SourcePortRange=source_port,
                            SourceIp=source_ip,
                            EnableLogging=enable_logging)

def main():
    argument_spec = vca_argument_spec()
    argument_spec.update(
        dict(
            fw_rules = dict(required=True, type='list'),
            gateway_name = dict(default='gateway'),
            state = dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    fw_rules = module.params.get('fw_rules')
    gateway_name = module.params.get('gateway_name')
    vdc_name = module.params['vdc_name']

    vca = vca_login(module)

    gateway = vca.get_gateway(vdc_name, gateway_name)
    if not gateway:
        module.fail_json(msg="Not able to find the gateway %s, please check "
                             "the gateway_name param" % gateway_name)

    fwservice = gateway._getFirewallService()

    rules = gateway.get_fw_rules()
    current_rules = fw_rules_to_dict(rules)

    try:
        desired_rules = validate_fw_rules(fw_rules)
    except VcaError as e:
        module.fail_json(msg=e.message)

    result = dict(changed=False)
    result['current_rules'] = current_rules
    result['desired_rules'] = desired_rules

    updates = list()
    additions = list()
    deletions = list()

    for (index, rule) in enumerate(desired_rules):
        try:
            if rule != current_rules[index]:
                updates.append((index, rule))
        except IndexError:
            additions.append(rule)

    eol = len(current_rules) > len(desired_rules)
    if eol > 0:
        for rule in current_rules[eos:]:
            deletions.append(rule)

    for rule in additions:
        if not module.check_mode:
            rule['protocol'] = rule['protocol'].capitalize()
            gateway.add_fw_rule(**rule)
        result['changed'] = True

    for index, rule in updates:
        if not module.check_mode:
            rule = create_fw_rule(**rule)
            fwservice.replace_FirewallRule_at(index, rule)
        result['changed'] = True

    keys = ['protocol', 'dest_port', 'dest_ip', 'source_port', 'source_ip']
    for rule in deletions:
        if not module.check_mode:
            kwargs = dict([(k, v) for k, v in rule.items() if k in keys])
            kwargs['protocol'] = protocol_to_string(kwargs['protocol'])
            gateway.delete_fw_rule(**kwargs)
        result['changed'] = True

    if not module.check_mode and result['changed'] == True:
        task = gateway.save_services_configuration()
        if task:
            vca.block_until_completed(task)

    result['rules_updated'] = count=len(updates)
    result['rules_added'] = count=len(additions)
    result['rules_deleted'] = count=len(deletions)

    return module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.vca import *
if __name__ == '__main__':
        main()
