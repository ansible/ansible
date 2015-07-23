#!/usr/bin/python

# Copyright (c) 2015 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

DOCUMENTATION = '''
---
module: vca_fw
short_description: add remove firewall rules in a gateway  in a vca
description:
  - Adds or removes firewall rules from a gateway in a vca environment
version_added: "2.0"
options:
    username:
      version_added: "2.0"
      description:
        - The vca username or email address, if not set the environment variable VCA_USER is checked for the username.
      required: false
      default: None
    password:
      version_added: "2.0"
      description:
        - The vca password, if not set the environment variable VCA_PASS is checked for the password
      required: false
      default: None
    org:
      version_added: "2.0"
      description:
        - The org to login to for creating vapp, mostly set when the service_type is vdc.
      required: false
      default: None
    service_id:
      version_added: "2.0"
      description:
        - The service id in a vchs environment to be used for creating the vapp
      required: false
      default: None
    host:
      version_added: "2.0"
      description:
        - The authentication host to be used when service type  is vcd.
      required: false
      default: None
    api_version:
      version_added: "2.0"
      description:
        - The api version to be used with the vca
      required: false
      default: "5.7"
    service_type:
      version_added: "2.0"
      description:
        - The type of service we are authenticating against
      required: false
      default: vca
      choices: [ "vca", "vchs", "vcd" ] 
    state:
      version_added: "2.0"
      description:
        - if the object should be added or removed
      required: false
      default: present
      choices: [ "present", "absent" ]
    verify_certs:
      version_added: "2.0"
      description:
        - If the certificates of the authentication is to be verified
      required: false
      default: True
    vdc_name:
      version_added: "2.0"
      description:
        - The name of the vdc where the gateway is located.
      required: false
      default: None
    gateway_name:
      version_added: "2.0"
      description:
        - The name of the gateway of the vdc where the rule should be added
      required: false
      default: gateway
    fw_rules:
      version_added: "2.0"
      description:
        - A list of firewall rules to be added to the gateway, Please see examples on valid entries
      required: True
      default: false

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
           dest_ip: 192.168.2.11
         - description: "ben testing 2"
           source_ip: 192.168.2.100
           source_port: "Any"
           dest_port: "22"
           dest_ip: 192.168.2.13
           is_enable: "true"
           enable_logging: "false"
           protocol: "Tcp"
           policy: "allow"

'''



import time, json, xmltodict
HAS_PYVCLOUD = False
try:
    from pyvcloud.vcloudair import VCA
    from pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType import ProtocolsType 
    HAS_PYVCLOUD = True
except ImportError:
    pass

SERVICE_MAP        = {'vca': 'ondemand', 'vchs': 'subscription', 'vcd': 'vcd'}
LOGIN_HOST         = {}
LOGIN_HOST['vca']  = 'vca.vmware.com'
LOGIN_HOST['vchs'] = 'vchs.vmware.com'
VALID_RULE_KEYS    = ['policy', 'is_enable', 'enable_logging', 'description', 'dest_ip', 'dest_port', 'source_ip', 'source_port', 'protocol']

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
  
def validate_fw_rules(module=None, fw_rules=None):
    VALID_PROTO = ['Tcp', 'Udp', 'Icmp', 'Any']
    for rule in fw_rules:
        if not isinstance(rule, dict):
            module.fail_json(msg="Firewall rules must be a list of dictionaries, Please check", valid_keys=VALID_RULE_KEYS)
        for k in rule.keys():
            if k not in VALID_RULE_KEYS:
                module.fail_json(msg="%s is not a valid key in fw rules, Please check above.." %k, valid_keys=VALID_RULE_KEYS)
        rule['dest_port']       = rule.get('dest_port', 'Any')
        rule['dest_ip']         = rule.get('dest_ip', 'Any')
        rule['source_port']     = rule.get('source_port', 'Any')
        rule['source_ip']       = rule.get('source_ip', 'Any')
        rule['protocol']        = rule.get('protocol', 'Any')
        rule['policy']          = rule.get('policy', 'allow')
        rule['is_enable']       = rule.get('is_enable', 'true')
        rule['enable_logging']  = rule.get('enable_logging', 'false')
        rule['description']     = rule.get('description', 'rule added by Ansible')
        if not rule['protocol'] in VALID_PROTO:
            module.fail_json(msg="the value in protocol is not valid, valid values are as above", valid_proto=VALID_PROTO)
    return fw_rules

def create_protocol_list(protocol):
    plist = []
    plist.append(protocol.get_Tcp())
    plist.append(protocol.get_Any())
    plist.append(protocol.get_Tcp())
    plist.append(protocol.get_Udp())
    plist.append(protocol.get_Icmp())
    plist.append(protocol.get_Other())
    return plist


def create_protocols_type(protocol):
    all_protocols = {"Tcp": None, "Udp": None, "Icmp": None, "Any": None}
    all_protocols[protocol] = True
    return ProtocolsType(**all_protocols)

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
            fw_rules            = dict(required=True, default=None, type='list'),
        )
    )


    vdc_name        = module.params.get('vdc_name')
    org             = module.params.get('org')
    service         = module.params.get('service_id')
    state           = module.params.get('state')
    service_type    = module.params.get('service_type')
    host            = module.params.get('host')
    instance_id     = module.params.get('instance_id')
    fw_rules        = module.params.get('fw_rules')
    gateway_name    = module.params.get('gateway_name')
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

    mod_rules = validate_fw_rules(module, fw_rules)
    gateway = vca.get_gateway(vdc_name, gateway_name)
    if not gateway:
        module.fail_json(msg="Not able to find the gateway %s, please check the gateway_name param" %gateway_name)
    rules = gateway.get_fw_rules()
    existing_rules = []
    del_rules = []
    for rule in rules:
        current_trait = (create_protocol_list(rule.get_Protocols()),
                             rule.get_DestinationPortRange(),
                             rule.get_DestinationIp(),
                             rule.get_SourcePortRange(),
                             rule.get_SourceIp())
        for idx, val  in enumerate(mod_rules):
            trait  = (create_protocol_list(create_protocols_type(val['protocol'])),
                        val['dest_port'], val['dest_ip'], val['source_port'], val['source_ip'])
            if current_trait == trait:
                del_rules.append(mod_rules[idx])
                mod_rules.pop(idx)
        existing_rules.append(current_trait)

    if state == 'absent':
        if len(del_rules) < 1:
            module.exit_json(changed=False, msg="Nothing to delete", delete_rules=mod_rules)
        else:
            for i in del_rules:
                gateway.delete_fw_rule(i['protocol'], i['dest_port'], i['dest_ip'], i['source_port'], i['source_ip'])
            task = gateway.save_services_configuration()
            if not task:
                module.fail_json(msg="Unable to Delete  Rule, please check above error", error=gateway.response.content)
            if not vca.block_until_completed(task):
                module.fail_json(msg="Error while waiting to remove  Rule, please check above error", error=gateway.response.content)
            module.exit_json(changed=True, msg="Rules Deleted", deleted_rules=del_rules)

    if len(mod_rules) < 1:
        module.exit_json(changed=False, rules=existing_rules)
    if len(mod_rules) >= 1:
        for i in mod_rules:
            gateway.add_fw_rule(i['is_enable'], i['description'], i['policy'], i['protocol'], i['dest_port'], i['dest_ip'],
                                        i['source_port'], i['source_ip'], i['enable_logging'])
            task = gateway.save_services_configuration()
            if not task:
                module.fail_json(msg="Unable to Add Rule, please check above error", error=gateway.response.content)
            if not vca.block_until_completed(task):
                module.fail_json(msg="Failure in waiting for adding firewall  rule", error=gateway.response.content)
    module.exit_json(changed=True, rules=mod_rules)

    
# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
        main()
