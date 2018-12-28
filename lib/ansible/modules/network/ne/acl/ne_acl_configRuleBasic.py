#!/usr/bin/python
# coding=utf-8


from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
DOCUMENTATION = '''
---
module: ne_acl_configRuleBasic
version_added: "2.6"
short_description: Config configuration of acl basic rules.
description:
    - Config configuration of acl basic rules.
author: Chenyang && Shaofei (@netengine-Ansible)
options:
    aclNumOrName:
        description:
            - Config the acl aclNumOrName of a acl Group.
        required: true
        default: null
    aclRuleName:
        description:
            - Config the acl aclRuleName of a acl basic rule.
        required: false
        default: null
    aclRuleID:
        description:
            - Config the acl aclRuleID of a acl basic rule.
        required: false
        default: null
    aclAction:
        description:
            - Config the acl aclAction of a acl basic rule.
        required: false
        default: null
    aclSourceIp:
        description:
            - Config the acl aclSourceIp of a acl basic rule.
        required: false
        default: null
    aclSrcWild:
        description:
            - Config the acl aclSrcWild of a acl basic rule.
        required: false
        default: null
    aclFragType:
        description:
            - Config the acl aclFragType of a acl basic rule.
        required: false
        default: null
    vrfAny:
        description:
            - Config the acl vrfAny of a acl basic rule.
        required: false
        default: null
    aclTimeName:
        description:
            - Config the acl aclTimeName of a acl basic rule.
        required: false
        default: null
    aclRuleDescription:
        description:
            - Config the acl aclRuleDescription of a acl basic rule.
        required: false
        default: null
    operation:
        description:
            - Specifies the action to be performed on the ACL basic rules.
        required: false
        default: all
        choices: ['create', 'delete', 'clear']
'''

EXAMPLES = '''
- name: Config acl basic rules configuration
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
  - name: Config acl basic rules configuration
    ne_acl_getGroup:
      aclNumOrName: sf20
      aclRuleName: rule_20
      aclAction: permit
      operation: create
      provider: "{{ cli }}"
'''

RETURN = '''
"response":
    [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
            <rpc-reply xmlns:nc-ext=\"urn:huawei:yang:huawei-ietf-netconf-ext\" nc-ext:flow-id=\"66\">
                <ok/>
            </rpc-reply>"
    ]
'''


ACLGROUP_CFG_HEAD = """
<config>
      <acl xmlns="http://www.huawei.com/netconf/vrp/huawei-acl">
        <aclGroups>
          <aclGroup>
"""

ACLRULEBASIC4_CFG_HEAD = """
<aclRuleBas4s>
  <aclRuleBas4>
"""

ACLRULEBASIC4_CFG_DELETE_HEAD = """
<aclRuleBas4s>
  <aclRuleBas4 nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

ACLRULEBASIC4_CFG_TAIL = """
  </aclRuleBas4>
</aclRuleBas4s>
"""

ACLGROUP_TAIL = """
      </aclGroup>
    </aclGroups>
  </acl>
</config>
"""

ACLNUMORNAME = """
      <aclNumOrName>%s</aclNumOrName>"""

ACLRULENAME = """
      <aclRuleName>%s</aclRuleName>"""

ACLRULEID = """
      <aclRuleID>%s</aclRuleID>"""

ACLACTION = """
      <aclAction>%s</aclAction>"""

ACLSOURCEIP = """
      <aclSourceIp>%s</aclSourceIp>"""

ACLSRCWILD = """
      <aclSrcWild>%s</aclSrcWild>"""

ACLFRAGTYPE = """
      <aclFragType>%s</aclFragType>"""

VRFNAME = """
      <vrfName>%s</vrfName>"""

VRFANY = """
      <vrfAny>%s</vrfAny>"""

ACLTIMENAME = """
      <aclTimeName>%s</aclTimeName>"""

ACLRULEDESCRIPTION = """
      <aclRuleDescription>%s</aclRuleDescription>"""

ACLFRAGTYPE_DELETE = """
      <aclFragType nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclFragType>"""

VRFNAME_DELETE = """
      <vrfName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</vrfName>"""

ACLTIMENAME_DELETE = """
      <aclTimeName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclTimeName>"""

ACLRULEDESCRIPTION_DELETE = """
      <aclRuleDescription nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclRuleDescription>"""


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
        self.aclRuleID = self.module.params['aclRuleID']
        self.aclAction = self.module.params['aclAction']
        self.aclSourceIp = self.module.params['aclSourceIp']
        self.aclSrcWild = self.module.params['aclSrcWild']
        self.aclFragType = self.module.params['aclFragType']
        self.vrfName = self.module.params['vrfName']
        self.vrfAny = self.module.params['vrfAny']
        self.aclTimeName = self.module.params['aclTimeName']
        self.aclRuleDescription = self.module.params['aclRuleDescription']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    # def check_params(self):

    def config_str(self):
        cfg_str = ''
        cfg_str += ACLGROUP_CFG_HEAD
        cfg_str += ACLNUMORNAME % self.aclNumOrName
        if self.operation == 'create':
            cfg_str += ACLRULEBASIC4_CFG_HEAD
            if self.aclRuleName:
                cfg_str += ACLRULENAME % self.aclRuleName
            if self.aclRuleID or 0 == self.aclRuleID:
                cfg_str += ACLRULEID % self.aclRuleID
            if self.aclAction:
                cfg_str += ACLACTION % self.aclAction
            if self.aclSourceIp:
                cfg_str += ACLSOURCEIP % self.aclSourceIp
            if self.aclSrcWild:
                cfg_str += ACLSRCWILD % self.aclSrcWild
            if self.aclFragType:
                cfg_str += ACLFRAGTYPE % self.aclFragType
            if self.vrfName:
                cfg_str += VRFNAME % self.vrfName
            if self.vrfAny:
                cfg_str += VRFANY % self.vrfAny
            if self.aclTimeName:
                cfg_str += ACLTIMENAME % self.aclTimeName
            if self.aclRuleDescription:
                cfg_str += ACLRULEDESCRIPTION % self.aclRuleDescription

        if self.operation == 'clear':
            cfg_str += ACLRULEBASIC4_CFG_HEAD
            if self.aclRuleName:
                cfg_str += ACLRULENAME % self.aclRuleName
            if self.aclFragType:
                cfg_str += ACLFRAGTYPE_DELETE % self.aclFragType
            if self.vrfName:
                cfg_str += VRFNAME_DELETE % self.vrfName
            if self.aclTimeName:
                cfg_str += ACLTIMENAME_DELETE % self.aclTimeName
            if self.aclRuleDescription:
                cfg_str += ACLRULEDESCRIPTION_DELETE % self.aclRuleDescription

        if self.operation == 'delete':
            cfg_str += ACLRULEBASIC4_CFG_DELETE_HEAD
            if self.aclRuleName:
                cfg_str += ACLRULENAME % self.aclRuleName

        cfg_str += ACLRULEBASIC4_CFG_TAIL
        cfg_str += ACLGROUP_TAIL

        return cfg_str

    def run(self):
        # self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        aclNumOrName=dict(required=False, type='str'),
        aclRuleName=dict(required=False, type='str'),
        aclRuleID=dict(required=False, type='int'),
        aclAction=dict(required=False, choices=['permit', 'deny']),
        aclSourceIp=dict(required=False, type='str', default='0.0.0.0'),
        aclSrcWild=dict(required=False, type='str', default='255.255.255.255'),
        aclFragType=dict(
            required=False,
            choices=[
                'fragment_subseq',
                'fragment',
                'non_fragment',
                'non_subseq',
                'fragment_spe_first',
                'clear_fragment']),
        vrfName=dict(required=False, type='str', default='_public_'),
        vrfAny=dict(
            required=False,
            choices=[
                'true',
                'false'],
            default='false'),
        aclTimeName=dict(required=False, type='str'),
        aclRuleDescription=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'delete',
                'clear'],
            default='create'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
