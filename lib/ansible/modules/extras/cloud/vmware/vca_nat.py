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
module: vca_nat
short_description: add remove nat rules in a gateway  in a vca
description:
  - Adds or removes nat rules from a gateway in a vca environment
version_added: "2.0"
options:
    username:
      description:
        - The vca username or email address, if not set the environment variable VCA_USER is checked for the username.
      required: false
      default: None
    password:
      description:
        - The vca password, if not set the environment variable VCA_PASS is checked for the password
      required: false
      default: None
    org:
      description:
        - The org to login to for creating vapp, mostly set when the service_type is vdc.
      required: false
      default: None
    service_id:
      description:
        - The service id in a vchs environment to be used for creating the vapp
      required: false
      default: None
    host:
      description:
        - The authentication host to be used when service type  is vcd.
      required: false
      default: None
    api_version:
      description:
        - The api version to be used with the vca
      required: false
      default: "5.7"
    service_type:
      description:
        - The type of service we are authenticating against
      required: false
      default: vca
      choices: [ "vca", "vchs", "vcd" ]
    state:
      description:
        - if the object should be added or removed
      required: false
      default: present
      choices: [ "present", "absent" ]
    verify_certs:
      description:
        - If the certificates of the authentication is to be verified
      required: false
      default: True
    vdc_name:
      description:
        - The name of the vdc where the gateway is located.
      required: false
      default: None
    gateway_name:
      description:
        - The name of the gateway of the vdc where the rule should be added
      required: false
      default: gateway
    purge_rules:
      description:
        - If set to true, it will delete all rules in the gateway that are not given as paramter to this module.
      required: false
      default: false
    nat_rules:
      description:
        - A list of rules to be added to the gateway, Please see examples on valid entries
      required: True
      default: false


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
           original_ip: 192.168.2.10
           translated_ip: 107.189.95.208

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
           original_ip: 107.189.95.208
           original_port: 22
           translated_ip: 192.168.2.10
           translated_port: 22

'''

import time, json, xmltodict

HAS_PYVCLOUD = False
try:
    from pyvcloud.vcloudair import VCA
    HAS_PYVCLOUD = True
except ImportError:
        pass

SERVICE_MAP           = {'vca': 'ondemand', 'vchs': 'subscription', 'vcd': 'vcd'}
LOGIN_HOST            = {}
LOGIN_HOST['vca']     = 'vca.vmware.com'
LOGIN_HOST['vchs']    = 'vchs.vmware.com'
VALID_RULE_KEYS       = ['rule_type', 'original_ip', 'original_port', 'translated_ip', 'translated_port', 'protocol']

def serialize_instances(instance_list):
    instances = []
    for i in instance_list:
        instances.append(dict(apiUrl=i['apiUrl'], instance_id=i['id']))
    return instances

def vca_login(module=None):
    service_type    = module.params.get('service_type')
    username        = module.params.get('username')
    password        = module.params.get('password')
    instance        = module.params.get('instance_id')
    org             = module.params.get('org')
    service         = module.params.get('service_id')
    vdc_name        = module.params.get('vdc_name')
    version         = module.params.get('api_version')
    verify          = module.params.get('verify_certs')
    if not vdc_name:
        if service_type == 'vchs':
            vdc_name = module.params.get('service_id')
    if not org:
        if service_type == 'vchs':
            if vdc_name:
                org = vdc_name
            else:
                org = service
    if service_type == 'vcd':
        host = module.params.get('host')
    else:
        host = LOGIN_HOST[service_type]

    if not username:
        if 'VCA_USER' in os.environ:
            username = os.environ['VCA_USER']
    if not password:
        if 'VCA_PASS' in os.environ:
            password = os.environ['VCA_PASS']
    if not username or not password:
        module.fail_json(msg = "Either the username or password is not set, please check")

    if service_type == 'vchs':
        version = '5.6'
    if service_type == 'vcd':
        if not version:
            version == '5.6'


    vca = VCA(host=host, username=username, service_type=SERVICE_MAP[service_type], version=version, verify=verify)

    if service_type == 'vca':
        if not vca.login(password=password):
            module.fail_json(msg = "Login Failed: Please check username or password", error=vca.response.content)
        if not vca.login_to_instance(password=password, instance=instance, token=None, org_url=None):
            s_json = serialize_instances(vca.instances)
            module.fail_json(msg = "Login to Instance failed: Seems like instance_id provided is wrong .. Please check",\
                                    valid_instances=s_json)
        if not vca.login_to_instance(instance=instance, password=None, token=vca.vcloud_session.token,
                                     org_url=vca.vcloud_session.org_url):
            module.fail_json(msg = "Error logging into org for the instance", error=vca.response.content)
        return vca

    if service_type == 'vchs':
        if not vca.login(password=password):
            module.fail_json(msg = "Login Failed: Please check username or password", error=vca.response.content)
        if not vca.login(token=vca.token):
            module.fail_json(msg = "Failed to get the token", error=vca.response.content)
        if not vca.login_to_org(service, org):
            module.fail_json(msg = "Failed to login to org, Please check the orgname", error=vca.response.content)
        return vca

    if service_type == 'vcd':
        if not vca.login(password=password, org=org):
            module.fail_json(msg = "Login Failed: Please check username or password or host parameters")
        if not vca.login(password=password, org=org):
            module.fail_json(msg = "Failed to get the token", error=vca.response.content)
        if not vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url):
            module.fail_json(msg = "Failed to login to org", error=vca.response.content)
        return vca

def validate_nat_rules(module=None, nat_rules=None):
    for rule in nat_rules:
        if not isinstance(rule, dict):
            module.fail_json(msg="nat rules must be a list of dictionaries, Please check", valid_keys=VALID_RULE_KEYS)
        for k in rule.keys():
            if k not in VALID_RULE_KEYS:
                module.fail_json(msg="%s is not a valid key in nat rules, Please check above.." %k, valid_keys=VALID_RULE_KEYS)
        rule['original_port']   = rule.get('original_port', 'any')
        rule['original_ip']     = rule.get('original_ip', 'any')
        rule['translated_ip']   = rule.get('translated_ip', 'any')
        rule['translated_port'] = rule.get('translated_port', 'any')
        rule['protocol']        = rule.get('protocol', 'any')
        rule['rule_type']        = rule.get('rule_type', 'DNAT')
    return nat_rules


def nat_rules_to_dict(natRules):
    result = []
    for natRule in natRules:
        ruleId = natRule.get_Id()
        enable = natRule.get_IsEnabled()
        ruleType = natRule.get_RuleType()
        gatewayNatRule = natRule.get_GatewayNatRule()
        originalIp = gatewayNatRule.get_OriginalIp()
        originalPort = gatewayNatRule.get_OriginalPort()
        translatedIp = gatewayNatRule.get_TranslatedIp()
        translatedPort = gatewayNatRule.get_TranslatedPort()
        protocol = gatewayNatRule.get_Protocol()
        interface = gatewayNatRule.get_Interface().get_name()
        result.append(dict(rule_type=ruleType, original_ip=originalIp, original_port="any" if not originalPort else originalPort, translated_ip=translatedIp, translated_port="any" if not translatedPort else translatedPort,
                      protocol="any" if not protocol else protocol))
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username            = dict(default=None),
            password            = dict(default=None),
            org                 = dict(default=None),
            service_id          = dict(default=None),
            instance_id         = dict(default=None),
            host                = dict(default=None),
            api_version         = dict(default='5.7'),
            service_type        = dict(default='vca', choices=['vchs', 'vca', 'vcd']),
            state               = dict(default='present', choices = ['present', 'absent']),
            vdc_name            = dict(default=None),
            gateway_name        = dict(default='gateway'),
            nat_rules           = dict(required=True, default=None, type='list'),
            purge_rules         = dict(default=False),
        )
    )


    vdc_name        = module.params.get('vdc_name')
    org             = module.params.get('org')
    service         = module.params.get('service_id')
    state           = module.params.get('state')
    service_type    = module.params.get('service_type')
    host            = module.params.get('host')
    instance_id     = module.params.get('instance_id')
    nat_rules       = module.params.get('nat_rules')
    gateway_name    = module.params.get('gateway_name')
    purge_rules     = module.params.get('purge_rules')
    verify_certs    = dict(default=True, type='bool'),

    if not HAS_PYVCLOUD:
        module.fail_json(msg="python module pyvcloud is needed for this module")
    if service_type == 'vca':
        if not instance_id:
            module.fail_json(msg="When service type is vca the instance_id parameter is mandatory")
        if not vdc_name:
            module.fail_json(msg="When service type is vca the vdc_name parameter is mandatory")

    if service_type == 'vchs':
        if not service:
            module.fail_json(msg="When service type vchs the service_id parameter is mandatory")
        if not org:
            org = service
        if not vdc_name:
            vdc_name = service
    if service_type == 'vcd':
        if not host:
            module.fail_json(msg="When service type is vcd host parameter is mandatory")

    vca = vca_login(module)
    vdc = vca.get_vdc(vdc_name)
    if not vdc:
        module.fail_json(msg = "Error getting the vdc, Please check the vdc name")

    mod_rules = validate_nat_rules(module, nat_rules)
    gateway = vca.get_gateway(vdc_name, gateway_name)
    if not gateway:
        module.fail_json(msg="Not able to find the gateway %s, please check the gateway_name param" %gateway_name)
    rules = gateway.get_nat_rules()
    cur_rules = nat_rules_to_dict(rules)
    delete_cur_rule = []
    delete_rules = []
    for rule in cur_rules:
        match = False
        for idx, val in enumerate(mod_rules):
            match = False
            if cmp(rule, val) == 0:
                delete_cur_rule.append(val)
                mod_rules.pop(idx)
                match = True
        if not match:
            delete_rules.append(rule)
    if state == 'absent':
        if purge_rules:
            if not gateway.del_all_nat_rules():
                module.fail_json(msg="Error deleting all rules")
            module.exit_json(changed=True, msg="Removed all rules")
        if len(delete_cur_rule) < 1:
            module.exit_json(changed=False, msg="No rules to be removed", rules=cur_rules)
        else:
            for i in delete_cur_rule:
                gateway.del_nat_rule(i['rule_type'], i['original_ip'],\
                                    i['original_port'], i['translated_ip'], i['translated_port'], i['protocol'])
                task = gateway.save_services_configuration()
                if not task:
                    module.fail_json(msg="Unable to delete Rule, please check above error", error=gateway.response.content)
                if not vca.block_until_completed(task):
                    module.fail_json(msg="Failure in waiting for removing network rule", error=gateway.response.content)
            module.exit_json(changed=True, msg="The rules have been deleted", rules=delete_cur_rule)
    changed = False
    if len(mod_rules) < 1:
        if not purge_rules:
            module.exit_json(changed=False, msg="all rules are available", rules=cur_rules)
    for i in mod_rules:
        gateway.add_nat_rule(i['rule_type'], i['original_ip'], i['original_port'],\
                             i['translated_ip'], i['translated_port'], i['protocol'])
        task = gateway.save_services_configuration()
        if not task:
            module.fail_json(msg="Unable to add rule, please check above error", rules=mod_rules, error=gateway.response.content)
        if not vca.block_until_completed(task):
            module.fail_json(msg="Failure in waiting for adding network rule", error=gateway.response.content)
    if purge_rules:
        if len(delete_rules) < 1 and len(mod_rules) < 1:
            module.exit_json(changed=False, rules=cur_rules)
        for i in delete_rules:
            gateway.del_nat_rule(i['rule_type'], i['original_ip'],\
                                    i['original_port'], i['translated_ip'], i['translated_port'], i['protocol'])
            task = gateway.save_services_configuration()
            if not task:
                module.fail_json(msg="Unable to delete Rule, please check above error", error=gateway.response.content)
            if not vca.block_until_completed(task):
                module.fail_json(msg="Failure in waiting for removing network rule", error=gateway.response.content)

    module.exit_json(changed=True, rules_added=mod_rules)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
        main()
