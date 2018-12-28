#!/usr/bin/python
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
#

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import collections
import re
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ne_qos_classifier_ipv4
version_added: "2.6"
short_description: Manages traffic classifier configurations on Huawei NetEngine devices.
description:
    - Manages traffic classifier configurations on Huawei NetEngine devices.
options:
    classifierName:
        description:
            - Name of traffic classifier.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    operator
        description:
            - Logical operator between the rules.
              If operator is or, packets are of the specified classifier when
              the packets match any one of the rules.
              If operator is and, packets are of the specified classifier only when
              the packets match all rules.
        required: false
        default: or
        choices=['and', 'or']
    description:
        description:
            - Description information of traffic classifier.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    ruleAny:
        description:
            - If ruleAny is enable, specify a matching rule for
              complex traffic classification for all IPv4 packets.
        required: false
        default: null
        choices: ['enable']
    destinationMac:
        description:
            - Specify a matching rule for complex traffic classification based on
              destination MAC addresses of packets.
              The value is in the format of H-H-H with
              each H representing four hexadecimal digits.
        required: false
        default: null
    sourceMac:
        description:
            - Specify a matching rule for complex traffic classification based on
              the source MAC addresses of packets.
              The value is in the format of H-H-H with
              each H representing four hexadecimal digits.
        required: false
        default: null
    bitMatchType:
        description:
            - Specify a matching rule for complex traffic classification based on
              the SYN Flag value in the TCP packet header.
              If bitMatchType is notConfig, bitMatchType and tcpFlag and tcpFlagMask
              must config at the same time.
              If bitMatchType is not notConfig, indicate an SYN flag in the TCP packet headers,
              tcpFlag and tcpFlagMask is not required parameters,
              device returns the default value.
        required: false
        default: present
        choices: ['notConfig', 'established', 'fin', 'syn', 'rst', 'psh', 'ack', 'urg', 'ece', 'cwr', 'ns']
    tcpFlag:
        description:
            - Specify the value of SYN Flag in the TCP packet header.
              The value is an integer ranging from 0 to 511.
        required: false
        default: null
    tcpFlagMask:
        description:
            - Specify the mask corresponding to the SYN flag value in the TCP packet headers.
              The value is an integer ranging from 0 to 511.
        required: false
        default: null
    priorityType:
        description:
            - Priority Type.
              If priorityType is 8021p, Specify a matching rule for complex
              traffic classification based on the 802.1p value of VLAN packets.
              If priorityType is ipPrecedence, Specify an IPv4-precedence-based matching rule.
              If priorityType is dscp, Specify a matching rule for complex
              traffic classification based on DSCP values
              If priorityType is mplsExp, Specify a matching rule to classify traffic
              based on the value of the MPLS EXP field.
              If priorityType is service-class, Specify a matching rule for
              MF classification based on the service class.
        required: false
        default: null
        choices: ['8021p', 'ipPrecedence', 'dscp', 'mplsExp', 'service-class']
    priorityValue:
        description:
            - Specify value for priorityType.
              If priorityValue is dscp, the value is an integer ranging from 0 to 63,
              otherwise is an integer ranging from 0 to 7.
        required: false
        default: null
    serviceClass:
        description:
            - Specify service class when priorityType is service-class.
        required: false
        default: null
        choices: ['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']
    localID:
        description:
            - Specify a matching rule to classify traffic based on the QoS policy ID.
              The value is an integer ranging from 1 to 255.
        required: false
        default: null
    aclName:
        description:
            - Specify a matching rule for complex traffic classification based on an IPv4 ACL.
              ACL number: 2000-4099; ACL Name: 64 chars string with first char a-z or A-z.
        required: false
        default: null
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices=['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_classifier_ipv4 module test
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

  - name: Config traffic behavior
    ne_classifier_ipv4:
      classifierName: test
      operation: create
      provider: "{{ cli }}"

  - name: Config tcp
    ne_classifier_ipv4:
      classifierName: test
      bitMatchType: notConfig
      tcpFlag: 6
      tcpFlagMask: 0
      operation: create
      provider: "{{ cli }}"

  - name: Undo tcp
    ne_classifier_ipv4:
      classifierName: test
      bitMatchType: notConfig
      tcpFlag: 6
      tcpFlagMask: 0
      operation: delete
      provider: "{{ cli }}"

  - name: Get all traffic classifier configuration
    ne_classifier_ipv4:
      operation: getconfig
      provider: "{{ cli }}"

  - name: Get traffic classifier test configuration
    ne_classifier_ipv4:
      classifierName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
existing:
    description: k/v pairs of traffic classifier
    returned: always
    type: dict
    sample: { "classifierName": "test",
              "if-match tcp": [ { "bitMatchType": "notConfig",
                                  "tcpFlag": "6",
                                  "tcpFlagMask": "0" } ],
              "operator": "or",
              "priority": [ { "priorityType": "service-class",
                              "serviceClass": "af3" },
                            { "priorityType": "dscp",
                              "priorityValue": "5" } ] }
'''

# from ansible.module_utils.ce import get_nc_config, set_nc_config, execute_nc_action, ce_argument_spec
# from ansible.module_utils.ce import get_nc_config

MERGE_CLASS_HEALDER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosClassifiers>
            <qosClassifier>
                <classifierName>%s</classifierName>
                <operator>%s</operator>
"""
# <description>%s</description>

MERGE_CLASS_TAIL = """
            </qosClassifier>
        </qosClassifiers>
    </qosCbQos>
</qos>
</config>
"""
Merge_ANY = """
          <qosRuleAnys>
            <qosRuleAny>
              <protoFamily>ipv4</protoFamily>
            </qosRuleAny>
          </qosRuleAnys>
"""
Merge_ANY = """
          <qosRuleAnys>
            <qosRuleAny>
              <protoFamily>ipv4</protoFamily>
            </qosRuleAny>
          </qosRuleAnys>
"""
Merge_PRI = """
          <qosRulePrioritys>
            <qosRulePriority>
              <priorityType>%s</priorityType>
              <priorityValue>%s</priorityValue>
"""
Merge_PRI_TAIL = """
            </qosRulePriority>
          </qosRulePrioritys>
"""
Merge_LOCALID = """
          <qosLocalIDs>
            <qosLocalID>
              <qosLocalId>%s</qosLocalId>
            </qosLocalID>
          </qosLocalIDs>
"""
Merge_SOURCE_MAC = """
          <qosRuleMacs>
            <qosRuleMac>
              <macType>source</macType>
              <macAddr>%s</macAddr>
            </qosRuleMac>
          </qosRuleMacs>
"""

Merge_DES_MAC = """
          <qosRuleMacs>
            <qosRuleMac>
              <macType>destination</macType>
              <macAddr>%s</macAddr>
            </qosRuleMac>
          </qosRuleMacs>
"""
Merge_TCP = """
          <qosRuleTcpFlags>
            <qosRuleTcpFlag>
              <bitMatchType>%s</bitMatchType>
              <tcpFlag>%s</tcpFlag>
              <tcpFlagMask>%s</tcpFlagMask>
            </qosRuleTcpFlag>
          </qosRuleTcpFlags>
"""
Merge_ACL = """
          <qosRuleAcls>
            <qosRuleAcl>
              <aclName>%s</aclName>
            </qosRuleAcl>
          </qosRuleAcls>
"""

QOS_IFCAR_GET = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosClassifiers>
            <qosClassifier>
                <classifierName>%s</classifierName>
         </qosClassifier>
        </qosClassifiers>
    </qosCbQos>
</qos>
</filter>
"""

DELETE_CLASS = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosClassifiers>
            <qosClassifier xc:operation="delete">
                <classifierName>%s</classifierName>
            </qosClassifier>
        </qosClassifiers>
    </qosCbQos>
</qos>
</config>
"""


class QosIfCarCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosifcar config info
        self.classifierName = self.module.params['classifierName']
        self.operator = self.module.params['operator']
        self.description = self.module.params['description']
        self.ruleAny = self.module.params['ruleAny']
        self.destinationMac = self.module.params['destinationMac']
        self.sourceMac = self.module.params['sourceMac']
        self.bitMatchType = self.module.params['bitMatchType']
        self.tcpFlag = self.module.params['tcpFlag']
        self.tcpFlagMask = self.module.params['tcpFlagMask']
        self.priorityType = self.module.params['priorityType']
        self.priorityValue = self.module.params['priorityValue']
        self.serviceClass = self.module.params['serviceClass']
        self.localID = self.module.params['localID']
        self.aclName = self.module.params['aclName']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        self.results = dict()
        self.results["existing"] = []
        self.results["end_stat"] = []
        self.results["changed"] = False

    def init_module(self):
        """
        init ansilbe NetworkModule.
        """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # check the necessary element for get/merge/query/delete

        # check the length of ifname  dengyu kong de shi hou " "
        if not self.classifierName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes classifierName.')
        if self.bitMatchType == 'fin':
            self.tcpFlag = 1
            self.tcpFlagMask = 1
        if self.bitMatchType == 'syn':
            self.tcpFlag = 2
            self.tcpFlagMask = 2
        if self.bitMatchType == 'psh':
            self.tcpFlag = 8
            self.tcpFlagMask = 8
        if self.bitMatchType == 'established':
            self.tcpFlag = 20
            self.tcpFlagMask = 20
        if self.bitMatchType == 'rst':
            self.tcpFlag = 4
            self.tcpFlagMask = 4
        if self.bitMatchType == 'ack':
            self.tcpFlag = 16
            self.tcpFlagMask = 16
        if self.bitMatchType == 'urg':
            self.tcpFlag = 32
            self.tcpFlagMask = 32
        if self.bitMatchType == 'ece':
            self.tcpFlag = 64
            self.tcpFlagMask = 64
        if self.bitMatchType == 'cwr':
            self.tcpFlag = 128
            self.tcpFlagMask = 128
        if self.bitMatchType == 'ns':
            self.tcpFlag = 256
            self.tcpFlagMask = 256
        # if self.macType:
        if not (self.bitMatchType and self.tcpFlag and self.tcpFlagMask) and (
                self.bitMatchType or self.tcpFlag or self.tcpFlagMask):
            self.module.fail_json(
                msg='Error: BitMatchType and tcpFlag and tcpFlagMask must be config at the same time.')

        if not self.priorityType and (self.priorityValue or self.serviceClass):
            self.module.fail_json(
                msg='Error: PriorityType must be config at the same time.')
        if self.priorityType and self.priorityType != 'service-class' and not self.priorityValue:
            self.module.fail_json(
                msg='Error: When priorityType is ' + self.priorityType + ', Please input the necessary element includes priorityValue.')
        if self.priorityType == 'service-class' and not self.serviceClass:
            self.module.fail_json(
                msg='Error: When priorityType is ' + self.priorityType + ', Please input the necessary element includes serviceClass.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):
        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % (self.classifierName, self.operator)

        if self.ruleAny == 'enable':
            print('9999', self.ruleAny)
            if self.operation == 'delete':
                global Merge_ANY
                Merge_ANY = Merge_ANY.replace(
                    '<qosRuleAny>', '<qosRuleAny xc:operation="delete">')
            conf_str += Merge_ANY

        if self.priorityType:
            if self.serviceClass:
                global Merge_PRI
                Merge_PRI += '<serviceClass>%s</serviceClass>' % self.serviceClass
                if self.serviceClass == 'be':
                    self.priorityValue = 0
                if self.serviceClass == 'af1':
                    self.priorityValue = 1
                if self.serviceClass == 'af2':
                    self.priorityValue = 2
                if self.serviceClass == 'af3':
                    self.priorityValue = 3
                if self.serviceClass == 'af4':
                    self.priorityValue = 4
                if self.serviceClass == 'ef':
                    self.priorityValue = 5
                if self.serviceClass == 'cs6':
                    self.priorityValue = 6
                if self.serviceClass == 'cs7':
                    self.priorityValue = 7
            conf_str += Merge_PRI % (self.priorityType, self.priorityValue)

            if self.operation == 'delete':
                conf_str = conf_str.replace(
                    '<qosRulePriority>',
                    '<qosRulePriority xc:operation="delete">')
            conf_str += Merge_PRI_TAIL
        if self.localID:
            if self.operation == 'delete':
                global Merge_LOCALID
                Merge_LOCALID = Merge_LOCALID.replace(
                    '<qosLocalID>', '<qosLocalID xc:operation="delete">')
            conf_str += Merge_LOCALID % (self.localID)

        if self.sourceMac:
            if self.operation == 'delete':
                global Merge_SOURCE_MAC
                Merge_SOURCE_MAC = Merge_SOURCE_MAC.replace(
                    '<qosRuleMac>', '<qosRuleMac xc:operation="delete">')
            conf_str += Merge_SOURCE_MAC % (self.sourceMac)

        if self.destinationMac:
            if self.operation == 'delete':
                global Merge_DES_MAC
                Merge_DES_MAC = Merge_DES_MAC.replace(
                    '<qosRuleMac>', '<qosRuleMac xc:operation="delete">')
            conf_str += Merge_DES_MAC % (self.destinationMac)

        if self.bitMatchType:
            if self.operation == 'delete':
                global Merge_TCP
                Merge_TCP = Merge_TCP.replace(
                    '<qosRuleTcpFlag>', '<qosRuleTcpFlag xc:operation="delete">')
            conf_str += Merge_TCP % (self.bitMatchType,
                                     self.tcpFlag, self.tcpFlagMask)

        if self.aclName:
            if self.operation == 'delete':
                global Merge_ACL
                Merge_ACL = Merge_ACL.replace(
                    '<qosRuleAcl>', '<qosRuleAcl xc:operation="delete">')
            conf_str += Merge_ACL % (self.aclName)

        conf_str += MERGE_CLASS_TAIL
        if not self.ruleAny and not self.priorityType and not self.localID and not self.sourceMac and not self.destinationMac and not self.bitMatchType:
            print('7777', conf_str)
            if self.operation == 'delete':
                global conf_str
                print('88888', conf_str)
                conf_str = DELETE_CLASS % self.classifierName
        print('101010', conf_str)
        return conf_str

    def merge_ifcar(self):
        if not self.classifierName:
            self.classifierName = ' '
        if not self.operator:
            self.operator = ' '
        if not self.description:
            self.description = ' '

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_ifcar(self, classifierName):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        if not self.classifierName:
            self.classifierName = ' '
        conf_str = None
        conf_str = QOS_IFCAR_GET % (self.classifierName)
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return attr
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</qosClassifier>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                attr = dict()
                find_classifierName = re.findall(
                    r'.*<classifierName>(.*)</classifierName>.*\s*', xml_str_split[j])

                print('88888', find_classifierName)
                if find_classifierName:
                    attr['classifierName'] = find_classifierName[0]
                    print('9999', find_classifierName[0])
                    find_operator = re.findall(
                        r'.*<operator>(.*)</operator>.*\s*', xml_str_split[j])
                    find_description = re.findall(
                        r'.*<description>(.*)</description>.*\s*', xml_str_split[j])
                    find_protoFamily = re.findall(
                        r'.*<protoFamily>(.*)</protoFamily>.*\s*', xml_str_split[j])
                    find_macType = re.findall(
                        r'.*<macType>(.*)</macType>.*\s*', xml_str_split[j])
                    find_macAddr = re.findall(
                        r'.*<macAddr>(.*)</macAddr>.*\s*', xml_str_split[j])
                    find_aclName = re.findall(
                        r'.*<aclName>(.*)</aclName>.*\s*', xml_str_split[j])

                    find_tcpType = re.findall(
                        r'.*<bitMatchType>(.*)</bitMatchType>.*\s*', xml_str_split[j])
                    find_tcpFlag = re.findall(
                        r'.*<tcpFlag>(.*)</tcpFlag>.*\s*', xml_str_split[j])
                    find_tcpFlagMask = re.findall(
                        r'.*<tcpFlagMask>(.*)</tcpFlagMask>.*\s*', xml_str_split[j])
                    find_local = re.findall(
                        r'.*<qosLocalId>(.*)</qosLocalId>.*\s*', xml_str_split[j])

                    if find_operator:
                        attr['operator'] = find_operator[0]
                    if find_description:
                        attr['description'] = find_description[0]
                    if find_protoFamily:
                        attr['ruleAny'] = 'enable'

                    sour_list = list()
                    des_list = list()
                    for i in range(len(find_macType)):
                        if find_macType[i] == 'source':
                            sour_list.append(find_macAddr[i])
                        if find_macType[i] == 'destination':
                            des_list.append(find_macAddr[i])
                    if sour_list:
                        attr['sourceMac'] = sour_list
                    if des_list:
                        attr['destinationMac'] = des_list
                    if find_local:
                        attr['localID'] = find_local

                    tcplist = list()
                    for i in range(len(find_tcpType)):
                        tcp = dict()
                        tcp['bitMatchType'] = find_tcpType[i]
                        tcp['tcpFlag'] = find_tcpFlag[i]
                        tcp['tcpFlagMask'] = find_tcpFlagMask[i]
                        tcplist.append(tcp)
                    if tcplist:
                        attr['if-match tcp'] = tcplist

                    tcplist = list()
                    for i in range(len(find_aclName)):
                        tcp = dict()
                        tcp['aclName'] = find_aclName[i]
                        tcplist.append(tcp)
                    if tcplist:
                        attr['if-match acl'] = tcplist
                        print("999999", tcplist)

                    tcplist = list()
                    find_priority = re.findall(
                        r'.*<priorityType>(.*)</priorityType>.*\s*', xml_str_split[j])
                    find_priorityval = re.findall(
                        r'.*<priorityValue>(.*)</priorityValue>.*\s*', xml_str_split[j])
                    xml_pri = re.split('</qosRulePriority>', xml_str_split[j])
                    for i in range(len(find_priority)):
                        tcp = dict()
                        tcp['priorityType'] = find_priority[i]
                        if find_priority[i] != 'service-class':
                            tcp['priorityValue'] = find_priorityval[i]
                        find_service = re.findall(
                            r'.*<serviceClass>(.*)</serviceClass>.*\s*', xml_pri[i])
                        if find_service:
                            tcp['serviceClass'] = find_service[0]
                        tcplist.append(tcp)
                    if tcplist:
                        attr['priority'] = tcplist

                    output_msg_list.append(attr)

        return output_msg_list

    def undo_ifcar(self):
        if not self.classifierName:
            self.classifierName = ' '
        if not self.operator:
            self.operator = ' '
        if not self.description:
            self.description = ' '

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")
        # self.changed = True

    def get_proposed(self):

        if self.classifierName:
            self.proposed["classifierName"] = self.classifierName
        if self.operator:
            self.proposed["operator"] = self.operator
        if self.description:
            self.proposed["description"] = self.description
        if self.ruleAny:
            self.proposed["ruleAny"] = self.ruleAny
        if self.destinationMac:
            self.proposed["destinationMac"] = self.destinationMac
        if self.sourceMac:
            self.proposed["sourceMac"] = self.sourceMac
        if self.bitMatchType:
            self.proposed["bitMatchType"] = self.bitMatchType
        if self.tcpFlag:
            self.proposed["tcpFlag"] = self.tcpFlag
        if self.tcpFlagMask:
            self.proposed["tcpFlagMask"] = self.tcpFlagMask
        if self.priorityType:
            self.proposed["priorityType"] = self.priorityType
        if self.priorityValue:
            self.proposed["priorityValue"] = self.priorityValue
        if self.serviceClass:
            self.proposed["serviceClass"] = self.serviceClass
        if self.localID:
            self.proposed["localID"] = self.localID
        if self.aclName:
            self.proposed["aclName"] = self.aclName
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        # check param
        self.check_params()
        self.get_proposed()

        ifcarcfg_attr_exist = self.get_ifcar(self.classifierName)
        if ifcarcfg_attr_exist:
            self.results["existing"] = ifcarcfg_attr_exist
        # print("5555555", self.ifname, self.direction, self.vlanid, self.cir, self.pir, self.cbs,)
        if self.operation == 'create':
            self.merge_ifcar()

        if self.operation == 'delete':
            self.undo_ifcar()

        ifcarcfg_attr_end_stat = self.get_ifcar(self.classifierName)
        if ifcarcfg_attr_end_stat:
            self.results["end_stat"] = ifcarcfg_attr_end_stat

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        classifierName=dict(required=False, type='str'),
        operator=dict(required=False, choices=['and', 'or'], default='or'),
        description=dict(required=False, type='str'),
        ruleAny=dict(required=False, choices=['enable']),
        # destinationMac =dict(required=False, choices=['source', 'destination']),
        destinationMac=dict(required=False, type='str'),
        sourceMac=dict(required=False, type='str'),
        bitMatchType=dict(
            required=False,
            choices=[
                'notConfig',
                'established',
                'fin',
                'syn',
                'rst',
                'psh',
                'ack',
                'urg',
                'ece',
                'cwr',
                'ns']),
        tcpFlag=dict(required=False, type='str'),
        tcpFlagMask=dict(required=False, type='str'),
        priorityType=dict(
            required=False,
            choices=[
                '8021p',
                'ipPrecedence',
                'dscp',
                'mplsExp',
                'service-class']),
        priorityValue=dict(required=False, type='str'),
        serviceClass=dict(
            required=False,
            choices=[
                'be',
                'af1',
                'af2',
                'af3',
                'af4',
                'ef',
                'cs6',
                'cs7']),
        localID=dict(required=False, type='str'),
        aclName=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )
    argument_spec.update(ne_argument_spec)
    NEWCQosIfCar = QosIfCarCfg(argument_spec)
    NEWCQosIfCar.work()


if __name__ == '__main__':
    main()
