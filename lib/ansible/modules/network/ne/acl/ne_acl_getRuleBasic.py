#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
DOCUMENTATION = '''
---
module: ne_acl_getRuleBasic
version_added: "2.6"
short_description: Get configuration of acl basic rules.
description:
    - Get configuration of acl basic rules.
author: Chenyang && Shaofei (@netengine-Ansible)
options:
    aclNumOrName:
        description:
            - Specify the acl name of a Group.
        required: true
        default: null
    aclRuleName:
        description:
            - Specify the acl rule name of a specified Group.
        required: true
        default: null
    operation:
        description:
            - Returns the specified element of specified acl basic rule.
        required: false
        default: all
        choices: ['all', 'aclRuleID', 'aclAction', 'aclActiveStatus', 'aclSourceIp',
        'aclSrcWild', 'aclFragType', 'vrfName', 'vrfAny', 'aclTimeName', 'aclRuleDescription']
'''

EXAMPLES = '''
- name: get acl basic rule configuration
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
  - name: Get acl basic rule configuration
    ne_acl_getGroup:
      aclNumOrName: sf20
      aclRuleName: rule_20
      operation: all
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
                </aclGroups>
            </acl>
        </data>"
    ]
'''


ACLGROUP_GET_HEAD = """
    <filter type="subtree">
      <acl:acl xmlns:acl="http://www.huawei.com/netconf/vrp/huawei-acl">
        <acl:aclGroups>
"""

ACLGROUP_GET_TAIL = """
        </acl:aclGroups>
      </acl:acl>
    </filter>
"""

ACLGROUP_GET_GROUP_BEGIN = """
<acl:aclGroup>"""

ACLGROUP_GET_GROUP = """
<acl:aclNumOrName>%s</acl:aclNumOrName>"""

ACLGROUP_GET_GROUP_END = """
</acl:aclGroup>"""

ACLRULEBASIC4_GET_BEGIN = """
<acl:aclRuleBas4s>
  <acl:aclRuleBas4>"""

ACLRULEBASIC4_GET_RULE = """
<acl:aclRuleName>%s</acl:aclRuleName>"""

ACLRULEBASIC4_GET_END = """
  </acl:aclRuleBas4>
</acl:aclRuleBas4s>"""

ACLRULEBASIC4_GET_ACLRULEID = """
<acl:aclRuleID/>"""

ACLRULEBASIC4_GET_ACLACTION = """
<acl:aclAction/>"""

ACLRULEBASIC4_GET_ACLACTIVESTATUS = """
<acl:aclActiveStatus/>"""

ACLRULEBASIC4_GET_ACLSOURCEIP = """
<acl:aclSourceIp/>"""

ACLRULEBASIC4_GET_ACLSRCWILD = """
<acl:aclSrcWild/>"""

ACLRULEBASIC4_GET_ACLFRAGTYPE = """
<acl:aclFragType/>"""

ACLRULEBASIC4_GET_VRFNAME = """
<acl:vrfName/>"""

ACLRULEBASIC4_GET_VRFANY = """
<acl:vrfAny/>"""

ACLRULEBASIC4_GET_ACLTIMENAME = """
<acl:aclTimeName/>"""

ACLRULEBASIC4_GET_ACLRULEDESCRIPTION = """
<acl:aclRuleDescription/>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.aclNumOrName = self.module.params['aclNumOrName']
        self.aclRuleName = self.module.params['aclRuleName']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def config_str_rule(self):
        cfg_str_rule = ''
        cfg_str_rule += ACLRULEBASIC4_GET_BEGIN
        if self.aclRuleName:
            cfg_str_rule += ACLRULEBASIC4_GET_RULE % self.aclRuleName
        if self.operation == 'aclRuleID':
            cfg_str_rule += ACLRULEBASIC4_GET_ACLRULEID
        if self.operation == 'aclAction':
            cfg_str_rule += ACLRULEBASIC4_GET_ACLACTION
        if self.operation == 'aclActiveStatus':
            cfg_str_rule += ACLRULEBASIC4_GET_ACLACTIVESTATUS
        if self.operation == 'aclSourceIp':
            cfg_str_rule += ACLRULEBASIC4_GET_ACLSOURCEIP
        if self.operation == 'aclSrcWild':
            cfg_str_rule += ACLRULEBASIC4_GET_ACLSRCWILD
        if self.operation == 'aclFragType':
            cfg_str_rule += ACLRULEBASIC4_GET_ACLFRAGTYPE
        if self.operation == 'vrfName':
            cfg_str_rule += ACLRULEBASIC4_GET_VRFNAME
        if self.operation == 'vrfAny':
            cfg_str_rule += ACLRULEBASIC4_GET_VRFANY
        if self.operation == 'aclTimeName':
            cfg_str_rule += ACLRULEBASIC4_GET_ACLTIMENAME
        if self.operation == 'aclRuleDescription':
            cfg_str_rule += ACLRULEBASIC4_GET_ACLRULEDESCRIPTION
        cfg_str_rule += ACLRULEBASIC4_GET_END
        return cfg_str_rule

    def config_str(self):
        cfg_str = ''
        cfg_str += ACLGROUP_GET_HEAD
        cfg_str += ACLGROUP_GET_GROUP_BEGIN
        if self.aclNumOrName:
            cfg_str += ACLGROUP_GET_GROUP % self.aclNumOrName
        cfg_str += self.config_str_rule()
        cfg_str += ACLGROUP_GET_GROUP_END
        cfg_str += ACLGROUP_GET_TAIL

        return cfg_str

    def run(self):
        recv_xml = get_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        aclNumOrName=dict(required=False, type='str'),
        aclRuleName=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'all',
                'aclRuleID',
                'aclAction',
                'aclActiveStatus',
                'aclSourceIp',
                'aclSrcWild',
                'aclFragType',
                'vrfName',
                'vrfAny',
                'aclTimeName',
                'aclRuleDescription'],
            default='all'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
