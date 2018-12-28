#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
DOCUMENTATION = '''
---
module: ne_acl_configRuleAdv
version_added: "2.6"
short_description: Config configuration of acl advance rules.
description:
    - Config configuration of acl advance rules.
author: Chenyang && Shaofei (@netengine-Ansible)
options:
    aclNumOrName:
        description:
            - Config the acl aclNumOrName of a acl advance Group.
        required: true
        default: null
    aclRuleName:
        description:
            - Config the acl aclRuleName of a acl advance rule.
        required: false
        default: null
    aclRuleID:
        description:
            - Config the acl aclRuleID of a acl advance rule.
        required: false
        default: null
    aclAction:
        description:
            - Config the acl aclAction of a acl advance rule.
        required: false
        default: null
    aclSourceIp:
        description:
            - Config the acl aclSourceIp of a acl advance rule.
        required: false
        default: null
    aclSrcWild:
        description:
            - Config the acl aclSrcWild of a acl advance rule.
        required: false
        default: null
    aclFragType:
        description:
            - Config the acl aclFragType of a acl advance rule.
        required: false
        default: null
    vrfAny:
        description:
            - Config the acl vrfAny of a acl advance rule.
        required: false
        default: null
    aclTimeName:
        description:
            - Config the acl aclTimeName of a acl advance rule.
        required: false
        default: null
    aclRuleDescription:
        description:
            - Config the acl aclRuleDescription of a acl advance rule.
        required: false
        default: null
    aclProtocol:
        description:
            - Config the acl aclProtocol of a acl advance rule.
        required: false
        default: null
    aclDestIp:
        description:
            - Config the acl aclDestIp of a acl advance rule.
        required: false
        default: null
    aclDestWild:
        description:
            - Config the acl aclDestWild of a acl advance rule.
        required: false
        default: null
    operation:
        description:
            - Specifies the action to be performed on the ACL advance rules.
        required: false
        default: all
        choices: ['create', 'delete', 'clear']
'''

EXAMPLES = '''
- name: Config acl Advance rules configuration
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
  - name: Config acl Advance rules configuration
    ne_acl_getGroup:
      aclNumOrName: sf10
      aclRuleName: rule_10
      aclAction: deny
      aclProtocol: 10
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

ACLRULEADV4_CFG_HEAD = """
<aclRuleAdv4s>
  <aclRuleAdv4>
"""

ACLRULEADV4_CFG_DELETE_HEAD = """
<aclRuleAdv4s>
  <aclRuleAdv4 nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

ACLRULEADV4_CFG_TAIL = """
  </aclRuleAdv4>
</aclRuleAdv4s>
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

ACLPROTOCOL = """
      <aclProtocol>%s</aclProtocol>"""

ACLVNI = """
      <aclVni>%s</aclVni>"""

ACLSPOOLNAME = """
      <aclSPoolName>%s</aclSPoolName>"""

ACLDESTIP = """
      <aclDestIp>%s</aclDestIp>"""

ACLDESTWILD = """
      <aclDestWild>%s</aclDestWild>"""

ACLDPOOLNAME = """
      <aclDPoolName>%s</aclDPoolName>"""

ACLSRCPORTOP = """
      <aclSrcPortOp>%s</aclSrcPortOp>"""

ACLSRCPORTBEGIN = """
      <aclSrcPortBegin>%s</aclSrcPortBegin>"""

ACLSRCPORTEND = """
      <aclSrcPortEnd>%s</aclSrcPortEnd>"""

ACLSPORTPOOLNAME = """
      <aclSPortPoolName>%s</aclSPortPoolName>"""

ACLDESTPORTOP = """
      <aclDestPortOp>%s</aclDestPortOp>"""

ACLDESTPORTB = """
      <aclDestPortB>%s</aclDestPortB>"""

ACLDESTPORTE = """
      <aclDestPortE>%s</aclDestPortE>"""

ACLDPORTPOOLNAME = """
      <aclDPortPoolName>%s</aclDPortPoolName>"""

ACLPRECEDENCE = """
      <aclPrecedence>%s</aclPrecedence>"""

ACLTOS = """
      <aclTos>%s</aclTos>"""

ACLDSCP = """
      <aclDscp>%s</aclDscp>"""

ACLICMPNAME = """
      <aclIcmpName>%s</aclIcmpName>"""

ACLICMPTYPE = """
      <aclIcmpType>%s</aclIcmpType>"""

ACLICMPTYPEEND = """
      <aclIcmpTypeEnd>%s</aclIcmpTypeEnd>"""

ACLICMPCODE = """
      <aclIcmpCode>%s</aclIcmpCode>"""

ACLSYNFLAG = """
      <aclSynFlag>%s</aclSynFlag>"""

ACLTCPFLAGMASK = """
      <aclTcpFlagMask>%s</aclTcpFlagMask>"""

ACLESTABLISHED = """
      <aclEstablished>%s</aclEstablished>"""

TTLOP = """
      <ttlOp>%s</ttlOp>"""

TTL = """
      <ttl>%s</ttl>"""

TTLEND = """
      <ttlEnd>%s</ttlEnd>"""

ACLIGMPTYPE = """
      <aclIgmpType>%s</aclIgmpType>"""

ACLPKTLENOP = """
      <aclPktLenOp>%s</aclPktLenOp>"""

ACLPKTLENBEGIN = """
      <aclPktLenBegin>%s</aclPktLenBegin>"""

ACLPKTLENEND = """
      <aclPktLenEnd>%s</aclPktLenEnd>"""

ACLFRAGTYPE_DELETE = """
      <aclFragType nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclFragType>"""

VRFNAME_DELETE = """
      <vrfName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</vrfName>"""

ACLTIMENAME_DELETE = """
      <aclTimeName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclTimeName>"""

ACLRULEDESCRIPTION_DELETE = """
      <aclRuleDescription nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclRuleDescription>"""

ACLVNI_DELETE = """
      <aclVni nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclVni>"""

ACLSPOOLNAME_DELETE = """
      <aclSPoolName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclSPoolName>"""

ACLDPOOLNAME_DELETE = """
      <aclDPoolName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclDPoolName>"""

ACLSRCPORTOP_DELETE = """
      <aclSrcPortOp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclSrcPortOp>"""

ACLSRCPORTBEGIN_DELETE = """
      <aclSrcPortBegin nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclSrcPortBegin>"""

ACLSRCPORTEND_DELETE = """
      <aclSrcPortEnd nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclSrcPortEnd>"""

ACLSPORTPOOLNAME_DELETE = """
      <aclSPortPoolName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclSPortPoolName>"""

ACLDESTPORTOP_DELETE = """
      <aclDestPortOp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclDestPortOp>"""

ACLDESTPORTB_DELETE = """
      <aclDestPortB nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclDestPortB>"""

ACLDESTPORTE_DELETE = """
      <aclDestPortE nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclDestPortE>"""

ACLDPORTPOOLNAME_DELETE = """
      <aclDPortPoolName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclDPortPoolName>"""

ACLPRECEDENCE_DELETE = """
      <aclPrecedence nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclPrecedence>"""

ACLTOS_DELETE = """
      <aclTos nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclTos>"""

ACLDSCP_DELETE = """
      <aclDscp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclDscp>"""

ACLICMPTYPE_DELETE = """
      <aclIcmpType nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclIcmpType>"""

ACLICMPTYPEEND_DELETE = """
      <aclIcmpTypeEnd nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclIcmpTypeEnd>"""

ACLICMPCODE_DELETE = """
      <aclIcmpCode nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclIcmpCode>"""

ACLSYNFLAG_DELETE = """
      <aclSynFlag nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclSynFlag>"""

ACLTCPFLAGMASK_DELETE = """
      <aclTcpFlagMask nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclTcpFlagMask>"""

ACLESTABLISHED_DELETE = """
      <aclEstablished nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclEstablished>"""

TTLOP_DELETE = """
      <ttlOp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ttlOp>"""

TTL_DELETE = """
      <ttl nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ttl>"""

TTLEND_DELETE = """
      <ttlEnd nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ttlEnd>"""

ACLIGMPTYPE_DELETE = """
      <aclIgmpType nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclIgmpType>"""

ACLPKTLENOP_DELETE = """
      <aclPktLenOp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclPktLenOp>"""

ACLPKTLENBEGIN_DELETE = """
      <aclPktLenBegin nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclPktLenBegin>"""

ACLPKTLENEND_DELETE = """
      <aclPktLenEnd nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclPktLenEnd>"""


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
        self.aclProtocol = self.module.params['aclProtocol']
        self.aclVni = self.module.params['aclVni']
        self.aclSPoolName = self.module.params['aclSPoolName']
        self.aclDestIp = self.module.params['aclDestIp']
        self.aclDestWild = self.module.params['aclDestWild']
        self.aclDPoolName = self.module.params['aclDPoolName']
        self.aclSrcPortOp = self.module.params['aclSrcPortOp']
        self.aclSrcPortBegin = self.module.params['aclSrcPortBegin']
        self.aclSrcPortEnd = self.module.params['aclSrcPortEnd']
        self.aclSPortPoolName = self.module.params['aclSPortPoolName']
        self.aclDestPortOp = self.module.params['aclDestPortOp']
        self.aclDestPortB = self.module.params['aclDestPortB']
        self.aclDestPortE = self.module.params['aclDestPortE']
        self.aclDPortPoolName = self.module.params['aclDPortPoolName']
        self.aclPrecedence = self.module.params['aclPrecedence']
        self.aclTos = self.module.params['aclTos']
        self.aclDscp = self.module.params['aclDscp']
        self.aclIcmpName = self.module.params['aclIcmpName']
        self.aclIcmpType = self.module.params['aclIcmpType']
        self.aclIcmpTypeEnd = self.module.params['aclIcmpTypeEnd']
        self.aclIcmpCode = self.module.params['aclIcmpCode']
        self.aclSynFlag = self.module.params['aclSynFlag']
        self.aclTcpFlagMask = self.module.params['aclTcpFlagMask']
        self.aclEstablished = self.module.params['aclEstablished']
        self.ttlOp = self.module.params['ttlOp']
        self.ttl = self.module.params['ttl']
        self.ttlEnd = self.module.params['ttlEnd']
        self.aclIgmpType = self.module.params['aclIgmpType']
        self.aclPktLenOp = self.module.params['aclPktLenOp']
        self.aclPktLenBegin = self.module.params['aclPktLenBegin']
        self.aclPktLenEnd = self.module.params['aclPktLenEnd']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if self.aclVni:
            if int(self.aclVni) < 1 or int(self.aclVni) > 16777215:
                self.module.fail_json(
                    msg='Error: The aclVni not in the range from 1 to 16777215.')

        if self.aclSrcPortBegin:
            if int(self.aclSrcPortBegin) < 0 or int(
                    self.aclSrcPortBegin) > 65535:
                self.module.fail_json(
                    msg='Error: The aclSrcPortBegin not in the range from 0 to 65535.')

        if self.aclSrcPortEnd:
            if int(self.aclSrcPortEnd) < 0 or int(self.aclSrcPortEnd) > 65535:
                self.module.fail_json(
                    msg='Error: The aclSrcPortEnd not in the range from 0 to 65535.')

        if self.aclDestPortB:
            if int(self.aclDestPortB) < 0 or int(self.aclDestPortB) > 65535:
                self.module.fail_json(
                    msg='Error: The aclDestPortB not in the range from 0 to 65535.')

        if self.aclDestPortE:
            if int(self.aclDestPortE) < 0 or int(self.aclDestPortE) > 65535:
                self.module.fail_json(
                    msg='Error: The aclDestPortE not in the range from 0 to 65535.')

        if self.aclPrecedence:
            if int(self.aclPrecedence) < 0 or int(self.aclPrecedence) > 7:
                self.module.fail_json(
                    msg='Error: The aclPrecedence not in the range from 0 to 7.')

        if self.aclTos:
            if int(self.aclTos) < 0 or int(self.aclTos) > 15:
                self.module.fail_json(
                    msg='Error: The aclTos not in the range from 0 to 15.')

        if self.aclDscp:
            if int(self.aclDscp) < 0 or int(self.aclDscp) > 63:
                self.module.fail_json(
                    msg='Error: The fastMessageCount not in the range from 0 to 63.')

        if self.aclIcmpType:
            if int(self.aclIcmpType) < 0 or int(self.aclIcmpType) > 255:
                self.module.fail_json(
                    msg='Error: The aclIcmpType not in the range from 0 to 255.')

        if self.aclIcmpTypeEnd:
            if int(self.aclIcmpTypeEnd) < 0 or int(self.aclIcmpTypeEnd) > 255:
                self.module.fail_json(
                    msg='Error: The aclIcmpTypeEnd not in the range from 0 to 255.')

        if self.aclIcmpCode:
            if int(self.aclIcmpCode) < 0 or int(self.aclIcmpCode) > 255:
                self.module.fail_json(
                    msg='Error: The aclIcmpCode not in the range from 0 to 255.')

        if self.aclSynFlag:
            if int(self.aclSynFlag) < 0 or int(self.aclSynFlag) > 63:
                self.module.fail_json(
                    msg='Error: The aclSynFlag not in the range from 0 to 63.')

        if self.aclTcpFlagMask:
            if int(self.aclTcpFlagMask) < 0 or int(self.aclTcpFlagMask) > 63:
                self.module.fail_json(
                    msg='Error: The aclTcpFlagMask not in the range from 0 to 63.')

        if self.ttl:
            if int(self.ttl) < 1 or int(self.ttl) > 255:
                self.module.fail_json(
                    msg='Error: The ttl not in the range from 1 to 255.')

        if self.ttlEnd:
            if int(self.ttlEnd) < 1 or int(self.ttlEnd) > 255:
                self.module.fail_json(
                    msg='Error: The ttlEnd not in the range from 1 to 255.')

        if self.aclPktLenBegin:
            if int(self.aclPktLenBegin) < 0 or int(
                    self.aclPktLenBegin) > 65535:
                self.module.fail_json(
                    msg='Error: The aclPktLenBegin not in the range from 0 to 65535.')

        if self.aclPktLenEnd:
            if int(self.aclPktLenEnd) < 0 or int(self.aclPktLenEnd) > 65535:
                self.module.fail_json(
                    msg='Error: The aclPktLenEnd not in the range from 0 to 65535.')

    def config_str(self):
        cfg_str = ''
        cfg_str += ACLGROUP_CFG_HEAD
        cfg_str += ACLNUMORNAME % self.aclNumOrName
        if self.operation == 'create':
            cfg_str += ACLRULEADV4_CFG_HEAD
            if self.aclRuleName:
                cfg_str += ACLRULENAME % self.aclRuleName
            if self.aclRuleID or 0 == self.aclRuleID:
                cfg_str += ACLRULEID % self.aclRuleID
            if self.aclAction:
                cfg_str += ACLACTION % self.aclAction
            if self.aclProtocol or 0 == self.aclProtocol:
                cfg_str += ACLPROTOCOL % self.aclProtocol
            if self.aclVni:
                cfg_str += ACLVNI % self.aclVni
            if self.aclSourceIp:
                cfg_str += ACLSOURCEIP % self.aclSourceIp
            if self.aclSrcWild:
                cfg_str += ACLSRCWILD % self.aclSrcWild
            if self.aclSPoolName:
                cfg_str += ACLSPOOLNAME % self.aclSPoolName
            if self.aclDestIp:
                cfg_str += ACLDESTIP % self.aclDestIp
            if self.aclDestWild:
                cfg_str += ACLDESTWILD % self.aclDestWild
            if self.aclDPoolName:
                cfg_str += ACLDPOOLNAME % self.aclDPoolName
            if self.aclSrcPortOp:
                cfg_str += ACLSRCPORTOP % self.aclSrcPortOp
            if self.aclSrcPortBegin or 0 == self.aclSrcPortBegin:
                cfg_str += ACLSRCPORTBEGIN % self.aclSrcPortBegin
            if self.aclSrcPortEnd or 0 == self.aclSrcPortEnd:
                cfg_str += ACLSRCPORTEND % self.aclSrcPortEnd
            if self.aclSPortPoolName:
                cfg_str += ACLSPORTPOOLNAME % self.aclSPortPoolName
            if self.aclDestPortOp:
                cfg_str += ACLDESTPORTOP % self.aclDestPortOp
            if self.aclDestPortB or 0 == self.aclDestPortB:
                cfg_str += ACLDESTPORTB % self.aclDestPortB
            if self.aclDestPortE or 0 == self.aclDestPortE:
                cfg_str += ACLDESTPORTE % self.aclDestPortE
            if self.aclDPortPoolName:
                cfg_str += ACLDPORTPOOLNAME % self.aclDPortPoolName
            if self.aclFragType:
                cfg_str += ACLFRAGTYPE % self.aclFragType
            if self.aclPrecedence or 0 == self.aclPrecedence:
                cfg_str += ACLPRECEDENCE % self.aclPrecedence
            if self.aclTos or 0 == self.aclTos:
                cfg_str += ACLTOS % self.aclTos
            if self.aclDscp or 0 == self.aclDscp:
                cfg_str += ACLDSCP % self.aclDscp
            if self.aclIcmpName:
                cfg_str += ACLICMPNAME % self.aclIcmpName
            if self.aclIcmpType or 0 == self.aclIcmpType:
                cfg_str += ACLICMPTYPE % self.aclIcmpType
            if self.aclIcmpTypeEnd or 0 == self.aclIcmpTypeEnd:
                cfg_str += ACLICMPTYPEEND % self.aclIcmpTypeEnd
            if self.aclIcmpCode or 0 == self.aclIcmpCode:
                cfg_str += ACLICMPCODE % self.aclIcmpCode
            if self.vrfName:
                cfg_str += VRFNAME % self.vrfName
            if self.vrfAny:
                cfg_str += VRFANY % self.vrfAny
            if self.aclSynFlag or 0 == self.aclSynFlag:
                cfg_str += ACLSYNFLAG % self.aclSynFlag
            if self.aclTcpFlagMask or 0 == self.aclTcpFlagMask:
                cfg_str += ACLTCPFLAGMASK % self.aclTcpFlagMask
            if self.aclEstablished:
                cfg_str += ACLESTABLISHED % self.aclEstablished
            if self.aclTimeName:
                cfg_str += ACLTIMENAME % self.aclTimeName
            if self.ttlOp:
                cfg_str += TTLOP % self.ttlOp
            if self.ttl:
                cfg_str += TTL % self.ttl
            if self.ttlEnd:
                cfg_str += TTLEND % self.ttlEnd
            if self.aclRuleDescription:
                cfg_str += ACLRULEDESCRIPTION % self.aclRuleDescription
            if self.aclIgmpType or 0 == self.aclIgmpType:
                cfg_str += ACLIGMPTYPE % self.aclIgmpType
            if self.aclPktLenOp:
                cfg_str += ACLPKTLENOP % self.aclPktLenOp
            if self.aclPktLenBegin or 0 == self.aclPktLenBegin:
                cfg_str += ACLPKTLENBEGIN % self.aclPktLenBegin
            if self.aclPktLenEnd or 0 == self.aclPktLenEnd:
                cfg_str += ACLPKTLENEND % self.aclPktLenEnd

        if self.operation == 'clear':
            cfg_str += ACLRULEADV4_CFG_HEAD
            if self.aclRuleName:
                cfg_str += ACLRULENAME % self.aclRuleName
            if self.aclVni:
                cfg_str += ACLVNI_DELETE % self.aclVni
            if self.aclSPoolName:
                cfg_str += ACLSPOOLNAME_DELETE % self.aclSPoolName
            if self.aclDPoolName:
                cfg_str += ACLDPOOLNAME_DELETE % self.aclDPoolName
            if self.aclSrcPortOp:
                cfg_str += ACLSRCPORTOP_DELETE % self.aclSrcPortOp
            if self.aclSrcPortBegin or 0 == self.aclSrcPortBegin:
                cfg_str += ACLSRCPORTBEGIN_DELETE % self.aclSrcPortBegin
            if self.aclSrcPortEnd or 0 == self.aclSrcPortEnd:
                cfg_str += ACLSRCPORTEND_DELETE % self.aclSrcPortEnd
            if self.aclSPortPoolName:
                cfg_str += ACLSPORTPOOLNAME_DELETE % self.aclSPortPoolName
            if self.aclDestPortOp:
                cfg_str += ACLDESTPORTOP_DELETE % self.aclDestPortOp
            if self.aclDestPortB or 0 == self.aclDestPortB:
                cfg_str += ACLDESTPORTB_DELETE % self.aclDestPortB
            if self.aclDestPortE or 0 == self.aclDestPortE:
                cfg_str += ACLDESTPORTE_DELETE % self.aclDestPortE
            if self.aclDPortPoolName:
                cfg_str += ACLDPORTPOOLNAME_DELETE % self.aclDPortPoolName
            if self.aclFragType:
                cfg_str += ACLFRAGTYPE_DELETE % self.aclFragType
            if self.aclPrecedence or 0 == self.aclPrecedence:
                cfg_str += ACLPRECEDENCE_DELETE % self.aclPrecedence
            if self.aclTos or 0 == self.aclTos:
                cfg_str += ACLTOS_DELETE % self.aclTos
            if self.aclDscp or 0 == self.aclDscp:
                cfg_str += ACLDSCP_DELETE % self.aclDscp
            if self.aclIcmpType or 0 == self.aclIcmpType:
                cfg_str += ACLICMPTYPE_DELETE % self.aclIcmpType
            if self.aclIcmpTypeEnd or 0 == self.aclIcmpTypeEnd:
                cfg_str += ACLICMPTYPEEND_DELETE % self.aclIcmpTypeEnd
            if self.aclIcmpCode or 0 == self.aclIcmpCode:
                cfg_str += ACLICMPCODE_DELETE % self.aclIcmpCode
            if self.vrfName:
                cfg_str += VRFNAME_DELETE % self.vrfName
            if self.aclSynFlag or 0 == self.aclSynFlag:
                cfg_str += ACLSYNFLAG_DELETE % self.aclSynFlag
            if self.aclTcpFlagMask or 0 == self.aclTcpFlagMask:
                cfg_str += ACLTCPFLAGMASK_DELETE % self.aclTcpFlagMask
            if self.aclEstablished:
                cfg_str += ACLESTABLISHED_DELETE % self.aclEstablished
            if self.aclTimeName:
                cfg_str += ACLTIMENAME_DELETE % self.aclTimeName
            if self.ttlOp:
                cfg_str += TTLOP_DELETE % self.ttlOp
            if self.ttl:
                cfg_str += TTL_DELETE % self.ttl
            if self.ttlEnd:
                cfg_str += TTLEND_DELETE % self.ttlEnd
            if self.aclRuleDescription:
                cfg_str += ACLRULEDESCRIPTION_DELETE % self.aclRuleDescription
            if self.aclIgmpType or 0 == self.aclIgmpType:
                cfg_str += ACLIGMPTYPE_DELETE % self.aclIgmpType
            if self.aclPktLenOp:
                cfg_str += ACLPKTLENOP_DELETE % self.aclPktLenOp
            if self.aclPktLenBegin or 0 == self.aclPktLenBegin:
                cfg_str += ACLPKTLENBEGIN_DELETE % self.aclPktLenBegin
            if self.aclPktLenEnd or 0 == self.aclPktLenEnd:
                cfg_str += ACLPKTLENEND_DELETE % self.aclPktLenEnd

        if self.operation == 'delete':
            cfg_str += ACLRULEADV4_CFG_DELETE_HEAD
            if self.aclRuleName:
                cfg_str += ACLRULENAME % self.aclRuleName

        cfg_str += ACLRULEADV4_CFG_TAIL
        cfg_str += ACLGROUP_TAIL

        return cfg_str

    def run(self):
        self.check_params()
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
        aclSourceIp=dict(required=False, type='str'),
        aclSrcWild=dict(required=False, type='str'),
        aclFragType=dict(
            required=False,
            choices=[
                'fragment_subseq',
                'fragment',
                'non_fragment',
                'non_subseq',
                'fragment_spe_first',
                'clear_fragment']),
        vrfName=dict(required=False, type='str'),
        vrfAny=dict(
            required=False,
            choices=[
                'true',
                'false'],
            default='false'),
        aclTimeName=dict(required=False, type='str'),
        aclRuleDescription=dict(required=False, type='str'),
        aclProtocol=dict(required=False, type='int'),
        aclVni=dict(required=False, type='int'),
        aclSPoolName=dict(required=False, type='str'),
        aclDestIp=dict(required=False, type='str'),
        aclDestWild=dict(required=False, type='str'),
        aclDPoolName=dict(required=False, type='str'),
        aclSrcPortOp=dict(
            required=False,
            choices=[
                'lt',
                'eq',
                'gt',
                'neq',
                'range']),
        aclSrcPortBegin=dict(required=False, type='int'),
        aclSrcPortEnd=dict(required=False, type='int'),
        aclSPortPoolName=dict(required=False, type='str'),
        aclDestPortOp=dict(
            required=False, choices=[
                'lt', 'eq', 'gt', 'neq', 'range']),
        aclDestPortB=dict(required=False, type='int'),
        aclDestPortE=dict(required=False, type='int'),
        aclDPortPoolName=dict(required=False, type='str'),
        aclPrecedence=dict(required=False, type='int'),
        aclTos=dict(required=False, type='int'),
        aclDscp=dict(required=False, type='int'),
        aclIcmpName=dict(
            required=False,
            choices=[
                'unconfigured',
                'echo',
                'fragmentneed-DFset',
                'host-redirect',
                'host-tos-redirect',
                'host-unreachable',
                'information-reply',
                'information-request',
                'net-redirect',
                'net-tos-redirect',
                'net-unreachable',
                'parameter-problem',
                'port-unreachable',
                'protocol-unreachable',
                'reassembly-timeout',
                'source-quench',
                'source-route-failed',
                'timestamp-reply',
                'timestamp-request',
                'ttl-exceeded',
                'address-mask-reply',
                'address-mask-request',
                'custom']),
        aclIcmpType=dict(required=False, type='int'),
        aclIcmpTypeEnd=dict(required=False, type='int'),
        aclIcmpCode=dict(required=False, type='int'),
        aclSynFlag=dict(required=False, type='int'),
        aclTcpFlagMask=dict(required=False, type='int'),
        aclEstablished=dict(required=False, choices=['true', 'false']),
        ttlOp=dict(required=False, choices=['lt', 'eq', 'gt', 'neq', 'range']),
        ttl=dict(required=False, type='int'),
        ttlEnd=dict(required=False, type='int'),
        aclIgmpType=dict(required=False, type='int'),
        aclPktLenOp=dict(
            required=False,
            choices=[
                'lt',
                'eq',
                'gt',
                'neq',
                'range']),
        aclPktLenBegin=dict(required=False, type='int'),
        aclPktLenEnd=dict(required=False, type='int'),
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
