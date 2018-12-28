#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
DOCUMENTATION = '''
---
module: ne_acl_getall
version_added: "2.6"
short_description: Get configuration of all acl groups and rules.
description:
    - Get configuration of all acl groups and rules.
author: Chenyang && Shaofei (@netengine-Ansible)
'''

EXAMPLES = '''
- name: Get configuration of all acl groups and rules
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli

  tasks:
  - name: Get configuration of all acl groups and rules
    ne_acl_getGroup:
      provider: "{{ cli }}"
'''

RETURN = '''
"response":
    [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><data>
           <acl xmlns=\"http://www.huawei.com/netconf/vrp/huawei-acl\">
                <aclGroups>
                    <aclGroup>
                        <aclNumOrName>sf20</aclNumOrName>
                        <aclMatchOrder>Config</aclMatchOrder>
                        <aclStep>5</aclStep>
                        <aclType>Basic</aclType>
                        <aclRuleBas4s>
                            <aclRuleBas4>
                                <aclRuleName>rule_20</aclRuleName>
                                <aclRuleID>5</aclRuleID>
                                <aclAction>permit</aclAction>
                                <aclSourceIp>0.0.0.0</aclSourceIp>
                                <aclSrcWild>255.255.255.255</aclSrcWild>
                                <vrfName>_public_</vrfName>
                                <vrfAny>false</vrfAny>
                                <aclActiveStatus>active</aclActiveStatus>
                            </aclRuleBas4>
                        </aclRuleBas4s>
                    </aclGroup>
                    <aclGroup>
                        <aclNumOrName>sf10</aclNumOrName>
                        <aclMatchOrder>Config</aclMatchOrder>
                        <aclStep>5</aclStep>
                        <aclType>Advance</aclType>
                            <aclRuleAdv4s>
                                <aclRuleAdv4>
                                    <aclRuleName>rule_10</aclRuleName>
                                    <aclRuleID>5</aclRuleID>
                                    <aclAction>deny</aclAction>
                                    <aclProtocol>10</aclProtocol>
                                    <aclSourceIp>0.0.0.0</aclSourceIp>
                                    <aclSrcWild>255.255.255.255</aclSrcWild>
                                    <aclDestIp>0.0.0.0</aclDestIp>
                                    <aclDestWild>255.255.255.255</aclDestWild>
                                    <vrfName>_public_</vrfName>
                                    <vrfAny>false</vrfAny>
                                    <aclActiveStatus>active</aclActiveStatus>
                                </aclRuleAdv4>
                        </aclRuleAdv4s>
                    </aclGroup>
                </aclGroups>
            </acl>
        </data>"
    ]
'''


ALL_GETCONFIG = """
<filter type="subtree">
  <acl xmlns="http://www.huawei.com/netconf/vrp/huawei-acl">
  </acl>
</filter>
"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []

    def run(self):
        xml_str = get_nc_config(self.module, ALL_GETCONFIG)
        self.results["response"].append(xml_str)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict()
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
