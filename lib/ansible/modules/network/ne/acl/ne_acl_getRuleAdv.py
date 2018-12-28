#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
DOCUMENTATION = '''
---
module: ne_acl_getRuleAdv
version_added: "2.6"
short_description: Get configuration of acl advance rules.
description:
    - Get configuration of acl advance rules.
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
            - Returns the specified element of specified acl advance rule.
        required: false
        default: all
        choices: ['all', 'aclRuleID', 'aclAction', 'aclActiveStatus', 'aclSourceIp', 'aclSrcWild',
        'aclFragType', 'vrfName', 'vrfAny', 'aclTimeName', 'aclRuleDescription', 'aclProtocol', 'aclVni',
        'aclSPoolName', 'aclDestIp', 'aclDestWild', 'aclDPoolName', 'aclSrcPortOp', 'aclSrcPortBegin', 'aclSrcPortEnd',
        'aclSPortPoolName', 'aclDestPortOp', 'aclDestPortB', 'aclDestPortE', 'aclDPortPoolName', 'aclPrecedence', 'aclTos',
        'aclDscp', 'aclIcmpName', 'aclIcmpType', 'aclIcmpTypeEnd', 'aclIcmpCode', 'aclSynFlag', 'aclTcpFlagMask',
        'aclEstablished', 'ttlOp', 'ttl', 'ttlEnd', 'aclIgmpType', 'aclPktLenOp', 'aclPktLenBegin', 'aclPktLenEnd']
'''

EXAMPLES = '''
- name: get acl advance rule configuration
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
  - name: Get acl advance rule configuration
    ne_acl_getGroup:
      aclNumOrName: sf10
      aclRuleName: rule_10
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

ACLRULEADV4_GET_BEGIN = """
<acl:aclRuleAdv4s>
  <acl:aclRuleAdv4>"""

ACLRULEADV4_GET_RULE = """
<acl:aclRuleName>%s</acl:aclRuleName>"""

ACLRULEADV4_GET_END = """
  </acl:aclRuleAdv4>
</acl:aclRuleAdv4s>"""

ACLRULEADV4_GET_ACLRULEID = """
<acl:aclRuleID/>"""

ACLRULEADV4_GET_ACLACTION = """
<acl:aclAction/>"""

ACLRULEADV4_GET_ACLACTIVESTATUS = """
<acl:aclActiveStatus/>"""

ACLRULEADV4_GET_ACLSOURCEIP = """
<acl:aclSourceIp/>"""

ACLRULEADV4_GET_ACLSRCWILD = """
<acl:aclSrcWild/>"""

ACLRULEADV4_GET_ACLFRAGTYPE = """
<acl:aclFragType/>"""

ACLRULEADV4_GET_VRFNAME = """
<acl:vrfName/>"""

ACLRULEADV4_GET_VRFANY = """
<acl:vrfAny/>"""

ACLRULEADV4_GET_ACLTIMENAME = """
<acl:aclTimeName/>"""

ACLRULEADV4_GET_ACLRULEDESCRIPTION = """
<acl:aclRuleDescription/>"""

ACLRULEADV4_GET_ACLPROTOCOL = """
<acl:aclProtocol/>"""

ACLRULEADV4_GET_ACLVNI = """
<acl:aclVni/>"""

ACLRULEADV4_GET_ACLSPOOLNAME = """
<acl:aclSPoolName/>"""

ACLRULEADV4_GET_ACLDESTIP = """
<acl:aclDestIp/>"""

ACLRULEADV4_GET_ACLDESTWILD = """
<acl:aclDestWild/>"""

ACLRULEADV4_GET_ACLDPOOLNAME = """
<acl:aclDPoolName/>"""

ACLRULEADV4_GET_ACLSRCPORTOP = """
<acl:aclSrcPortOp/>"""

ACLRULEADV4_GET_ACLSRCPORTBEGIN = """
<acl:aclSrcPortBegin/>"""

ACLRULEADV4_GET_ACLSRCPORTEND = """
<acl:aclSrcPortEnd/>"""

ACLRULEADV4_GET_ACLSPORTPOOLNAME = """
<acl:aclSPortPoolName/>"""

ACLRULEADV4_GET_ACLDESTPORTOP = """
<acl:aclDestPortOp/>"""

ACLRULEADV4_GET_ACLDESTPORTB = """
<acl:aclDestPortB/>"""

ACLRULEADV4_GET_ACLDESTPORTE = """
<acl:aclDestPortE/>"""

ACLRULEADV4_GET_ACLDPORTPOOLNAME = """
<acl:aclDPortPoolName/>"""

ACLRULEADV4_GET_ACLPRECEDENCE = """
<acl:aclPrecedence/>"""

ACLRULEADV4_GET_ACLTOS = """
<acl:aclTos/>"""

ACLRULEADV4_GET_ACLDSCP = """
<acl:aclDscp/>"""

ACLRULEADV4_GET_ACLICMPNAME = """
<acl:aclIcmpName/>"""

ACLRULEADV4_GET_ACLICMPTYPE = """
<acl:aclIcmpType/>"""

ACLRULEADV4_GET_ACLICMPTYPEEND = """
<acl:aclIcmpTypeEnd/>"""

ACLRULEADV4_GET_ACLICMPCODE = """
<acl:aclIcmpCode/>"""

ACLRULEADV4_GET_ACLSYNFLAG = """
<acl:aclSynFlag/>"""

ACLRULEADV4_GET_ACLTCPFLAGMASK = """
<acl:aclTcpFlagMask/>"""

ACLRULEADV4_GET_ACLESTABLISHED = """
<acl:aclEstablished/>"""

ACLRULEADV4_GET_TTLOP = """
<acl:ttlOp/>"""

ACLRULEADV4_GET_TTL = """
<acl:ttl/>"""

ACLRULEADV4_GET_TTLEND = """
<acl:ttlEnd/>"""

ACLRULEADV4_GET_ACLIGMPTYPE = """
<acl:aclIgmpType/>"""

ACLRULEADV4_GET_ACLPKTLENOP = """
<acl:aclPktLenOp/>"""

ACLRULEADV4_GET_ACLPKTLENBEGIN = """
<acl:aclPktLenBegin/>"""

ACLRULEADV4_GET_ACLPKTLENEND = """
<acl:aclPktLenEnd/>"""


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
        cfg_str_rule += ACLRULEADV4_GET_BEGIN
        if self.aclRuleName:
            cfg_str_rule += ACLRULEADV4_GET_RULE % self.aclRuleName
        if self.operation == 'aclRuleID':
            cfg_str_rule += ACLRULEADV4_GET_ACLRULEID
        if self.operation == 'aclAction':
            cfg_str_rule += ACLRULEADV4_GET_ACLACTION
        if self.operation == 'aclActiveStatus':
            cfg_str_rule += ACLRULEADV4_GET_ACLACTIVESTATUS
        if self.operation == 'aclSourceIp':
            cfg_str_rule += ACLRULEADV4_GET_ACLSOURCEIP
        if self.operation == 'aclSrcWild':
            cfg_str_rule += ACLRULEADV4_GET_ACLSRCWILD
        if self.operation == 'aclFragType':
            cfg_str_rule += ACLRULEADV4_GET_ACLFRAGTYPE
        if self.operation == 'vrfName':
            cfg_str_rule += ACLRULEADV4_GET_VRFNAME
        if self.operation == 'vrfAny':
            cfg_str_rule += ACLRULEADV4_GET_VRFANY
        if self.operation == 'aclTimeName':
            cfg_str_rule += ACLRULEADV4_GET_ACLTIMENAME
        if self.operation == 'aclProtocol':
            cfg_str_rule += ACLRULEADV4_GET_ACLPROTOCOL
        if self.operation == 'aclVni':
            cfg_str_rule += ACLRULEADV4_GET_ACLVNI
        if self.operation == 'aclSPoolName':
            cfg_str_rule += ACLRULEADV4_GET_ACLSPOOLNAME
        if self.operation == 'aclDestIp':
            cfg_str_rule += ACLRULEADV4_GET_ACLDESTIP
        if self.operation == 'aclDestWild':
            cfg_str_rule += ACLRULEADV4_GET_ACLDESTWILD
        if self.operation == 'aclDPoolName':
            cfg_str_rule += ACLRULEADV4_GET_ACLDPOOLNAME
        if self.operation == 'aclSrcPortOp':
            cfg_str_rule += ACLRULEADV4_GET_ACLSRCPORTOP
        if self.operation == 'aclSrcPortBegin':
            cfg_str_rule += ACLRULEADV4_GET_ACLSRCPORTBEGIN
        if self.operation == 'aclSrcPortEnd':
            cfg_str_rule += ACLRULEADV4_GET_ACLSRCPORTEND
        if self.operation == 'aclSPortPoolName':
            cfg_str_rule += ACLRULEADV4_GET_ACLSPORTPOOLNAME
        if self.operation == 'aclDestPortOp':
            cfg_str_rule += ACLRULEADV4_GET_ACLDESTPORTOP
        if self.operation == 'aclDestPortB':
            cfg_str_rule += ACLRULEADV4_GET_ACLDESTPORTB
        if self.operation == 'aclDestPortE':
            cfg_str_rule += ACLRULEADV4_GET_ACLDESTPORTE
        if self.operation == 'aclDPortPoolName':
            cfg_str_rule += ACLRULEADV4_GET_ACLDPORTPOOLNAME
        if self.operation == 'aclPrecedence':
            cfg_str_rule += ACLRULEADV4_GET_ACLPRECEDENCE
        if self.operation == 'aclTos':
            cfg_str_rule += ACLRULEADV4_GET_ACLTOS
        if self.operation == 'aclDscp':
            cfg_str_rule += ACLRULEADV4_GET_ACLDSCP
        if self.operation == 'aclIcmpName':
            cfg_str_rule += ACLRULEADV4_GET_ACLICMPNAME
        if self.operation == 'aclIcmpType':
            cfg_str_rule += ACLRULEADV4_GET_ACLICMPTYPE
        if self.operation == 'aclIcmpTypeEnd':
            cfg_str_rule += ACLRULEADV4_GET_ACLICMPTYPEEND
        if self.operation == 'aclIcmpCode':
            cfg_str_rule += ACLRULEADV4_GET_ACLICMPCODE
        if self.operation == 'aclSynFlag':
            cfg_str_rule += ACLRULEADV4_GET_ACLSYNFLAG
        if self.operation == 'aclTcpFlagMask':
            cfg_str_rule += ACLRULEADV4_GET_ACLTCPFLAGMASK
        if self.operation == 'aclEstablished':
            cfg_str_rule += ACLRULEADV4_GET_ACLESTABLISHED
        if self.operation == 'ttlOp':
            cfg_str_rule += ACLRULEADV4_GET_TTLOP
        if self.operation == 'ttl':
            cfg_str_rule += ACLRULEADV4_GET_TTL
        if self.operation == 'ttlEnd':
            cfg_str_rule += ACLRULEADV4_GET_TTLEND
        if self.operation == 'aclIgmpType':
            cfg_str_rule += ACLRULEADV4_GET_ACLIGMPTYPE
        if self.operation == 'aclPktLenOp':
            cfg_str_rule += ACLRULEADV4_GET_ACLPKTLENOP
        if self.operation == 'aclPktLenBegin':
            cfg_str_rule += ACLRULEADV4_GET_ACLPKTLENBEGIN
        if self.operation == 'aclPktLenEnd':
            cfg_str_rule += ACLRULEADV4_GET_ACLPKTLENEND
        cfg_str_rule += ACLRULEADV4_GET_END
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
                'aclRuleDescription',
                'aclProtocol',
                'aclVni',
                'aclSPoolName',
                'aclDestIp',
                'aclDestWild',
                'aclDPoolName',
                'aclSrcPortOp',
                'aclSrcPortBegin',
                'aclSrcPortEnd',
                'aclSPortPoolName',
                'aclDestPortOp',
                'aclDestPortB',
                'aclDestPortE',
                'aclDPortPoolName',
                'aclPrecedence',
                'aclTos',
                'aclDscp',
                'aclIcmpName',
                'aclIcmpType',
                'aclIcmpTypeEnd',
                'aclIcmpCode',
                'aclSynFlag',
                'aclTcpFlagMask',
                'aclEstablished',
                'ttlOp',
                'ttl',
                'ttlEnd',
                'aclIgmpType',
                'aclPktLenOp',
                'aclPktLenBegin',
                'aclPktLenEnd'],
            default='all'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
