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
module: ne_qos_behavior_sampler
version_added: "2.6"
short_description: Manages sampler of traffic behavior on Huawei NetEngine devices.
description:
    - Manages sampler of traffic behavior on Huawei NetEngine devices.
options:
    behaviorName:
        description:
            - Name of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    flowType
        description:
            - Flow type.
        required: false
        default: null
        choices: ['ipv4', 'ipv6']
    sampleType:
        description:
            - Sampling type, which can be fixed packet interval, random packet interval, or fixed time interval.
        required: false
        default: null
        choices: ['fixPackets', 'fixTime', 'randomPackets']
    sampleValue:
        description:
             - Sampling parameter value.
             - If sampleType is fixPackets, sampleValue is an integer ranging from 1 to 65535.
             - If sampleType is fixTime, sampleValue is an integer ranging from 5 to 30000.
             - If sampleType is randomPackets, sampleValue is an integer ranging from 1 to 65535.
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
- name: NetEngine ne_behavior_sampler module test
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
    ne_behavior_sampler:
      behaviorName: test
      operation: create
      provider: "{{ cli }}"

  - name: Config netstream sampler
    ne_behavior_sampler:
      behaviorName: test
      flowType: ipv4
      sampleType: fixPackets
      sampleValue: 10
      operation: create
      provider: "{{ cli }}"

  - name: Undo traffic behavior
    ne_behavior_sampler:
      behaviorName: test
      operation: delete
      provider: "{{ cli }}"

  - name: Undo netstream sampler
    ne_behavior_sampler:
      behaviorName: test
      flowType: ipv4
      sampleType: fixPackets
      sampleValue: 10
      operation: delete
      provider: "{{ cli }}"

  - name: Get traffic behavior test configuration
    ne_behavior_sampler:
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
            "behaviorName": "test",
            "flowType": "ipv4",
            "sampleType": fixPackets",
            "sampleValue": "10"
            "operation": "getconfig",
        }
    ]
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: [
        {
            "behaviorName": "test",
            "flowType": "ipv4",
            "sampleType": fixPackets",
            "sampleValue": "10"
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
          <qosActNsSamplers>
            <qosActNsSampler>
              <flowType>%s</flowType>
              <sampleType>%s</sampleType>
              <sampleValue>%s</sampleValue>
            </qosActNsSampler>
          </qosActNsSamplers>
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
          <qosActNsSamplers>
            <qosActNsSampler>
              <flowType></flowType>
              <sampleType></sampleType>
              <sampleValue></sampleValue>
            </qosActNsSampler>
          </qosActNsSamplers>
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
        self.flowType = self.module.params['flowType']
        self.sampleType = self.module.params['sampleType']
        self.sampleValue = self.module.params['sampleValue']
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
        # operation - create or delete
        if not self.behaviorName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes behaviorName.')
        if self.flowType or self.sampleType or self.sampleValue:
            if not (self.flowType and self.sampleType and self.sampleValue):
                self.module.fail_json(
                    msg='Error: FlowType and sampleType and sampleValue must be config at the same time.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % (self.behaviorName)
        if self.flowType:
            conf_str += MERGE_REMARK % (self.flowType,
                                        self.sampleType, self.sampleValue)
        if self.operation == 'delete':
            if self.flowType:
                conf_str = conf_str.replace(
                    '<qosActNsSampler>',
                    '<qosActNsSampler xc:operation="delete">')
            else:
                conf_str = conf_str.replace(
                    '<qosBehavior>', '<qosBehavior xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
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
                find_flowType = re.findall(
                    r'.*<flowType>(.*)</flowType>.*\s*', xml_str_split[j])
                find_sampleType = re.findall(
                    r'.*<sampleType>(.*)</sampleType>.*\s*', xml_str_split[j])
                find_sampleValue = re.findall(
                    r'.*<sampleValue>(.*)</sampleValue>.*\s*', xml_str_split[j])

                print('88888', find_behaviorName)
                if find_behaviorName:
                    attr['behaviorName'] = find_behaviorName[0]
                    # print('9999', find_classifierName[0])
                    if find_flowType:
                        attr['flowType'] = find_flowType[0]
                    if find_sampleType:
                        attr['sampleType'] = find_sampleType[0]
                    if find_sampleValue:
                        attr['sampleValue'] = find_sampleValue[0]

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
        if self.flowType:
            self.proposed["flowType"] = self.flowType
        if self.sampleType:
            self.proposed["sampleType"] = self.sampleType
        if self.sampleValue:
            self.proposed["sampleValue"] = self.sampleValue
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
        flowType=dict(required=False, choices=['ipv4', 'ipv6']),
        sampleType=dict(
            required=False,
            choices=[
                'fixPackets',
                'fixTime',
                'randomPackets']),
        sampleValue=dict(required=False, type='str'),
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
