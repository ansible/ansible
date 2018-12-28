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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ne_qos_behavior_remark
version_added: "2.6"
short_description: Manages remark action of traffic behavior on HUAWEI NetEngine devices.
description:
    - Manages remark action of traffic behavior on HUAWEI NetEngine devices.
options:
    behaviorName:
        description:
            - Name of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    actionType:
        description:
            - Re-marking action type, which can be 8021p, mpls-exp, dscp, or ip-precedence.
              If actionType is remark8021p, specifies the 802.1p value of a VLAN packet,
              that is, the priority value of a VLAN packet.
              If actionType is remarkIpv4Dscp, specifies the remarked DSCP value of IPv4 packets.
              If actionType is remarkTos, specifies the ToS value of an IP packet.
              If actionType is remarkIpv6Dscp, specifies the remarked DSCP value of IPv6 packets.
              If actionType is remarkIpPrecedence, specifies the value of IP precedence.
              If actionType is remarkMplsExp, specifies the EXP value of MPLS packets.
              If actionType is remarkIpDf, specifies the value of the DF field in a packet,
              which indicates whether the packet is fragmentable.
              If actionType is remarkTtl, specifies the TTL value of IP packets.
              If actionType is remarkInner8021p, specifies an 802.1p value for
              inner VLAN tag of double-tagged VLAN packets.
              If actionType is remarkOuter8021p, specifies an 802.1p value for
              outer VLAN tag of double-tagged VLAN packets.
        required: false
        default: null
        choices: ['remark8021p', 'remarkIpv4Dscp', 'remarkTos', 'remarkIpv6Dscp', 'remarkIpPrecedence', 'remarkMplsExp', 'remarkIpDf', 'remarkTtl', \
        'remarkInner8021p', 'remarkOuter8021p']
    remarkValue:
        description:
            - Re-marked priority value.
              The value is an integer ranging from 0 to 255.
        required: false
        default: null
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_behavior_remark module test
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
    ne_behavior_remark:
      behaviorName: test
      operation: create
      provider: "{{ cli }}"

  - name: Config remark action
    ne_behavior_remark:
      behaviorName: test
      actionType: remark8021p
      remarkValue: 6
      operation: create
      provider: "{{ cli }}"

  - name: Undo traffic behavior
    ne_behavior_remark:
      behaviorName: test
      operation: delete
      provider: "{{ cli }}"

  - name: Undo remark action
    ne_behavior_remark:
      behaviorName: test
      actionType: remark8021p
      remarkValue: 6
      operation: delete
      provider: "{{ cli }}"

  - name: Get traffic behavior test configuration
    ne_behavior_remark:
      behaviorName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
existing:
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "behaviorName": "test",
        "operation": "getconfig",
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: [
        {
            "actionType": "remark8021p"
            "behaviorName": "test",
            "remarkValue": "6"
            "operation": "getconfig",
        }
    ]
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: [
        {
            "actionType": "remark8021p"
            "behaviorName": "test",
            "remarkValue": "6"
            "operation": "getconfig",
        }
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosBehaviors>
            <qosBehavior>
                <behaviorName>%s</behaviorName>
"""

MERGE_REMARK = """
                <qosActRemarks>
                    <qosActRemark>
                        <actionType>%s</actionType>
                        <remarkValue>%s</remarkValue>
                    </qosActRemark>
                </qosActRemarks>
"""
MERGE_CLASS_TAIL = """
            </qosBehavior>
        </qosBehaviors>
    </qosCbQos>
</qos>
</config>
"""
QOS_IFCAR_CFGGET = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosBehaviors>
            <qosBehavior>
                <behaviorName>%s</behaviorName>
                <qosActRemarks>
                    <qosActRemark>
                        <actionType></actionType>
                        <remarkValue></remarkValue>
                    </qosActRemark>
                </qosActRemarks>
            </qosBehavior>
        </qosBehaviors>
    </qosCbQos>
</qos>
</filter>
"""
DELETE_BEHAVIOR = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosBehaviors>
            <qosBehavior xc:operation="delete">
                <behaviorName>%s</behaviorName>
            </qosBehavior>
        </qosBehaviors>
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
        self.behaviorName = self.module.params['behaviorName']
        self.actionType = self.module.params['actionType']
        self.remarkValue = self.module.params['remarkValue']
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
        if not self.behaviorName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes behaviorName.')
        if not (self.actionType and self.remarkValue) and (
                self.actionType or self.remarkValue):
            self.module.fail_json(
                msg='Error: ActionType and remarkValue must be config at the same time.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % (self.behaviorName)
        print('self.actionTypeggggg', self.actionType)
        if self.actionType:
            conf_str += MERGE_REMARK % (self.actionType, self.remarkValue)
        if self.operation == 'delete':
            if self.actionType:
                # global conf_str
                conf_str = conf_str.replace(
                    '<qosActRemark>', '<qosActRemark xc:operation="delete">')
            else:
                conf_str = conf_str.replace(
                    '<qosBehavior>', '<qosBehavior xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_ifcar(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_ifcar(self):
        attr = dict()
        output_msg_list = list()
        if not self.behaviorName:
            self.behaviorName = ' '
        conf_str = None
        conf_str = QOS_IFCAR_CFGGET % (self.behaviorName)
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return attr
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</qosBehavior>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                attr = dict()
                find_behaviorName = re.findall(
                    r'.*<behaviorName>(.*)</behaviorName>.*\s*', xml_str_split[j])
                find_actionType = re.findall(
                    r'.*<actionType>(.*)</actionType>.*\s*', xml_str_split[j])
                find_remarkValue = re.findall(
                    r'.*<remarkValue>(.*)</remarkValue>.*\s*', xml_str_split[j])

                print('88888', find_behaviorName)
                if find_behaviorName:
                    attr['behaviorName'] = find_behaviorName[0]
                    # print('9999', find_classifierName[0])

                    tcplist = list()
                    for i in range(len(find_actionType)):
                        tcp = dict()
                        tcp['actionType'] = find_actionType[i]
                        tcp['remarkValue'] = find_remarkValue[i]
                        tcplist.append(tcp)
                    if tcplist:
                        attr['REMARK'] = tcplist
                        print("999999", tcplist)

                    output_msg_list.append(attr)

        return output_msg_list

    def undo_ifcar(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")
        # self.changed = True

    def get_proposed(self):

        if self.behaviorName:
            self.proposed["behaviorName"] = self.behaviorName
        if self.actionType:
            self.proposed["actionType"] = self.actionType
        if self.remarkValue:
            self.proposed["remarkValue"] = self.remarkValue
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        # check param
        self.check_params()
        self.get_proposed()
        # print("5555555", self.ifname, self.direction, self.vlanid, self.cir, self.pir, self.cbs,)
        ifcarcfg_attr_exist = self.get_ifcar()
        if ifcarcfg_attr_exist:
            self.results["existing"] = ifcarcfg_attr_exist

        if self.operation == 'create':
            self.merge_ifcar()

        if self.operation == 'delete':
            self.undo_ifcar()

        ifcarcfg_attr_end_stat = self.get_ifcar()
        if ifcarcfg_attr_end_stat:
            self.results["end_stat"] = ifcarcfg_attr_end_stat

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        behaviorName=dict(required=False, type='str'),
        actionType=dict(
            required=False,
            choices=[
                'remark8021p',
                'remarkIpv4Dscp',
                'remarkTos',
                'remarkIpv6Dscp',
                'remarkIpPrecedence',
                'remarkMplsExp',
                'remarkIpDf',
                'remarkTtl',
                'remarkInner8021p',
                'remarkOuter8021p']),
        remarkValue=dict(required=False, type='str'),
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
