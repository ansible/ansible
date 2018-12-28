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
module: ne_qos_behavior_limit
version_added: "2.6"
short_description: Manages limit action of traffic behavior on Huawei NetEngine devices.
description:
    - Manages limit action of traffic behavior on Huawei NetEngine devices.
options:
    behaviorName:
        description:
            - Name of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: true
        default: null
    limitType:
        description:
            - Limit action.
              If the value is car or carpps, the parameters that can be configured include cir/pir/cbs/pbs/
              greenAction/greenServiceClass/greenColor/greenRemarkDscp/yellowAction/yellowServiceClass/yellowColor/
              yellowRemarkDscp/redAction/redServiceClass/redColor/redRemarkDscp/adjust.
              If the value is unknown-unicast-suppression or multicast-suppression or broadcast-suppression, the parameters
              that can be configured include cir/cbs/greenAction/greenServiceClass/greenColor
              redAction/redServiceClass/redColor.
              If the value is user-queue, the parameters that can be configured include
              cir/pir/flowQueueName/flowMappingName/gqName/templateName.
              If the value is flow-car, the parameters that can be configured include cir/pir/cbs/pbs/ipType.
        required: false
        default: null
        choices: ['car', 'carpps', 'unknown-unicast-suppression', 'multicast-suppression', 'broadcast-suppression', 'user-queue', 'flow-car']
    cir:
        description:
            - Committed information rate, in Kbit/s.
              The value is an integer ranging from 0 to 4294967295.
              If limitType is user-queue, the value is an integer ranging from 0, 16 to 4294967294.
        required: false
        default: null
    pir:
    pir:
        description:
            - Peak information rate, in Kbit/s.
              The value is an integer ranging from 0 to 4294967295.
              If limitType is user-queue, the value is an integer ranging from 0, 16 to 4294967294.
        required: false
        default: null
    cbs:
        description:
            - Committed burst size, in bytes.
              The value is an integer ranging from 0 to 4294967295.
        required: false
        default: null
    pbs:
        description:
            - VPeak burst size, in bytes.
              The value is an integer ranging from 0 to 4294967295.
        required: false
        default: null
    greenAction:
        description:
            - Mode in which a packet marked green is processed.
              If greenAction is discard, greenServiceClass and greenColor can not config.
        required: false
        default: pass
        choices: ['pass','discard']
    greenServiceClass:
        description:
            - Service class of a packet that is marked green.
              GreenServiceClass and greenColor must be configured at the same time.
        required: false
        default: null
        choices: ['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']
    greenColor:
        description:
            - Color of a packet that is marked green.
              GreenServiceClass and greenColor must be configured at the same time.
        required: false
        default: null
        choices: ['green','red','yellow']
    yellowAction:
        description:
            - Mode in which a packet marked yellow is processed.
              If yellowAction is discard, yellowServiceClass and yellowColor can not config.
        required: false
        default: null
        choices: ['pass','discard']
    yellowServiceClass:
        description:
            - Service class of a packet that is marked yellow.
              YellowServiceClass and yellowColor must be configured at the same time.
        required: false
        default: null
        choices: ['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']
    yellowColor:
        description:
            - Color of a packet that is marked yellow.
              YellowServiceClass and yellowColor must be configured at the same time.
        required: false
        default: null
        choices: ['green','red','yellow']
    redAction:
        description:
            - Mode in which a packet marked red is processed.
              If redAction is discard, redServiceClass and redColor can not config.
        required: false
        default: discard
        choices: ['pass','discard']
    redServiceClass:
        description:
            - Service class of a packet that is marked red.
              RedServiceClass and redColor must be configured at the same time.
        required: false
        default: null
        choices: ['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']
    redColor:
        description:
            - Color of a packet that is marked red.
              RedServiceClass and redColor must be configured at the same time.
        required: false
        default: null
        choices: ['green','red','yellow']
    colorAware:
        description:
            - When CAR is configured for a traffic behavior, the specified CAR action is sensitive to the color of packets. By default, the CAR action is \
            insensitive to the packet color.
        required: false
        default: false
        choices=['true', 'false']
    greenRemarkDscp:
        description:
            - DSCP value of a packet that is marked green.
              The value is an integer ranging from 0 to 63.
        required: false
        default: null
    yellowRemarkDscp:
        description:
            - DSCP value of a packet that is marked yellow.
              The value is an integer ranging from 0 to 63.
        required: false
        default: null
    redRemarkDscp:
        description:
            - DSCP value of a packet that is marked red.
              The value is an integer ranging from 0 to 63.
        required: false
        default: null
    flowQueueName:
        description:
            - Applied flow queue profile.
              The value is an integer ranging from 1 to 31.
        required: false
        default: null
    flowMappingName:
        description:
            - Applied flow queue mapping object.
              The value is an integer ranging from 1 to 31.
        required: false
        default: null
    gqName:
        description:
            - Name of a GQ.
              The value is an integer ranging from 1 to 31.
        required: false
        default: null
    templateName:
        description:
            - Name of the precision adjustment profile that is applied. The system defines 14 precision adjustment profiles based on services.
              The value is an integer ranging from 1 to 31.
        required: false
        default: null
    ipType:
        description:
            - Flow-CAR address type.
        required: false
        default: null
        choices=['source', 'destination']
    adjust:
        description:
            - The packet length is corrected.
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
- name: NetEngine ne_behavior_limit module test
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

  - name: Config user-queue of traffic behavior
    ne_behavior_limit:
      behaviorName: test
      limitType: user-queue
      cir: 100
      operation: create
      provider: "{{ cli }}"

  - name: Undo user-queue of traffic behavior
    ne_behavior_limit:
      behaviorName: test
      limitType: user-queue
      operation: delete
      provider: "{{ cli }}"

  - name: Get user-queue of traffic behavior configuration
    ne_behavior_limit:
      behaviorName: test
      limitType: user-queue
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "behaviorName": "test",
        "limitType": "user-queue",
        "operation": "getconfig",
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: [
        {
            "behaviorName": "test",
            "user-queue": { "cir": "100",
                            "pir": "100" }
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
            "user-queue": { "cir": "100",
                            "pir": "100" }
            "operation": "getconfig",
        }
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
    sample: { "behaviorName": "test",
              "user-queue": { "cir": "100",
                              "pir": "100" } }
'''


MERGE_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosBehaviors>
            <qosBehavior>
                <behaviorName>%s</behaviorName>
"""

MERGE_TAIL = """
            </qosBehavior>
        </qosBehaviors>
    </qosCbQos>
</qos></config>
"""

MERGE_CAR_HEAL = """
                <qosActCars>
                    <qosActCar>
                        <actionType>car</actionType>
                        <cir>%s</cir>
                        <limitType>bps</limitType>
"""
MERGE_CAR_TAIL = """
                    </qosActCar>
                </qosActCars>
"""
MERGE_CARPPS_HEAL = """
                <qosActCarPpss>
                    <qosActCarPps>
                        <actionType>car</actionType>
                        <cir>%s</cir>
"""
MERGE_CARPPS_TAIL = """
                    </qosActCarPps>
                </qosActCarPpss>
"""
MERGE_L2_HEAL = """
                <qosActL2Suppres>
                    <qosActL2Suppre>
                        <suppressType>%s</suppressType>
                        <cir>%s</cir>
"""
MERGE_L2_TAIL = """
                    </qosActL2Suppre>
                </qosActL2Suppres>
"""

MERGE_USERQUEUE_HEAL = """
                <qosActUserQueues>
                    <qosActUserQueue>
                        <cir>%s</cir>
"""
MERGE_USERQUEUE_TAIL = """
                    </qosActUserQueue>
                </qosActUserQueues>
"""
MERGE_FLOWCAR_HEAL = """
                <qosActFlowCars>
                    <qosActFlowCar>
                        <actionType>flow-car</actionType>
                        <cir>%s</cir>
                        <ipType>%s</ipType>
"""
MERGE_FLOWCAR_TAIL = """
                    </qosActFlowCar>
                </qosActFlowCars>
"""


GET_LIMIT = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosBehaviors>
            <qosBehavior>
                <behaviorName>%s</behaviorName>
               </qosBehavior>
        </qosBehaviors>
    </qosCbQos>
</qos></filter>
"""
DELETE_L2 = """
                <qosActL2Suppres>
                    <qosActL2Suppre xc:operation="delete">
                        <suppressType>%s</suppressType>
                    </qosActL2Suppre>
                </qosActL2Suppres>
"""


DELETE_CAR = """
                <qosActCars>
                    <qosActCar xc:operation="delete">
                        <actionType>car</actionType>
                    </qosActCar>
                </qosActCars>
"""
DELETE_CARPPS = """
                <qosActCarPpss>
                    <qosActCarPps xc:operation="delete">
                        <actionType>car</actionType>
                    </qosActCarPps>
                </qosActCarPpss>
"""

DELETE_USERQUEUE = """
                <qosActUserQueues>
                    <qosActUserQueue xc:operation="delete"/>
                </qosActUserQueues>
"""

DELETE_FLOWCAR = """
                <qosActFlowCars>
                    <qosActFlowCar xc:operation="delete">
                        <actionType>flow-car</actionType>
                    </qosActFlowCar>
                </qosActFlowCars>
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
        self.limitType = self.module.params['limitType']
        self.cir = self.module.params['cir']
        self.pir = self.module.params['pir']
        self.cbs = self.module.params['cbs']
        self.pbs = self.module.params['pbs']
        self.greenAction = self.module.params['greenAction']
        self.greenServiceClass = self.module.params['greenServiceClass']
        self.greenColor = self.module.params['greenColor']
        self.yellowAction = self.module.params['yellowAction']
        self.yellowServiceClass = self.module.params['yellowServiceClass']
        self.yellowColor = self.module.params['yellowColor']
        self.redAction = self.module.params['redAction']
        self.redServiceClass = self.module.params['redServiceClass']
        self.redColor = self.module.params['redColor']
        self.colorAware = self.module.params['colorAware']
        self.greenRemarkDscp = self.module.params['greenRemarkDscp']
        self.yellowRemarkDscp = self.module.params['yellowRemarkDscp']
        self.redRemarkDscp = self.module.params['redRemarkDscp']
        self.flowQueueName = self.module.params['flowQueueName']
        self.flowMappingName = self.module.params['flowMappingName']
        self.gqName = self.module.params['gqName']
        self.templateName = self.module.params['templateName']
        self.ipType = self.module.params['ipType']
        self.adjust = self.module.params['adjust']
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

    def check_car(self):
        if self.operation == 'create':
            if not self.cir and self.limitType != 'flow-car':
                self.module.fail_json(
                    msg='Error: When config ' + self.limitType + ', Please input the necessary element includes cir.')
            if (not self.cir or not self.ipType) and self.limitType == 'flow-car':
                self.module.fail_json(
                    msg='Error: When config ' + self.limitType + ', Please input the necessary element includes cir/ipType.')

        if self.cir:

            if not self.cir.isdigit() or int(self.cir) < 0 or int(self.cir) > 4294967295:
                self.module.fail_json(
                    msg='Error: Cir value is not in the range from 0 to 4294967295.')

        # check the range of pir
        if self.pir:
            if not self.pir.isdigit() or int(self.pir) < 0 or int(self.pir) > 4294967295:
                self.module.fail_json(
                    msg='Error: Pir value is not in the range from 0 to 4294967295.')
            if int(self.pir) < int(self.cir):
                self.module.fail_json(
                    msg='Error: Pir value can not be less than cir value.')
        # check para key_ref
        if self.greenAction == 'discard':
            if (self.greenServiceClass or self.greenColor):
                self.module.fail_json(
                    msg='Error: GreenServiceClass and greenColor can not be configured when greenAction is configured discard.')

        if self.redAction == 'discard':
            if (self.redServiceClass or self.redColor):
                self.module.fail_json(
                    msg='Error: RedServiceClass and redColor can not be configured when redAction is configured discard.')
        if ((self.greenServiceClass and (not self.greenColor)) or (
                self.greenColor and (not self.greenServiceClass))):
            self.module.fail_json(
                msg='Error: GreenServiceClass and greenColor must be config at the same time.')

        if ((self.redServiceClass and (not self.redColor)) or (
                self.redColor and (not self.redServiceClass))):
            self.module.fail_json(
                msg='Error: RedServiceClass and redColor must be config at the same time.')

        if self.yellowAction == 'discard':
            if (self.yellowServiceClass or self.yellowColor):
                self.module.fail_json(
                    msg='Error: yellowServiceClass and yellowColor can not be configured when yellowAction is configured discard.')

        if ((self.yellowServiceClass and (not self.yellowColor)) or (
                self.yellowColor and (not self.yellowServiceClass))):
            self.module.fail_json(
                msg='Error: YellowServiceClass and yellowColor must be config at the same time.')

    def check_userqueue(self):
        if self.operation == 'create':
            if not self.cir:
                self.module.fail_json(
                    msg='Error: When config ' + self.limitType + ', Please input the necessary element includes cir.')
        if self.cir:
            if not self.cir.isdigit() or (int(self.cir) != 0 and int(self.cir)
                                          < 16) or int(self.cir) > 4294967294:
                self.module.fail_json(
                    msg='Error: Cir value is not in the range from 0, 16 to 4294967294.')
        if self.pir:
            if not self.pir.isdigit() or (int(self.pir) != 0 and int(self.pir)
                                          < 16) or int(self.pir) > 4294967294:
                self.module.fail_json(
                    msg='Error: Pir value is not in the range from 0, 16 to 4294967294.')
            if int(self.pir) < int(self.cir):
                self.module.fail_json(
                    msg='Error: Pir value can not be less than cir value.')

    def check_params(self):
        """Check all input params"""
        if not self.behaviorName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error:  Please input the necessary element includes behaviorName.')
        if self.behaviorName and (
                len(self.behaviorName) < 1 or len(self.behaviorName) > 127):
            self.module.fail_json(
                msg='Error: The length of the behaviorName is not in the range from 1 to 127.')

        if self.limitType and self.limitType != 'user-queue':
            self.check_car()
        if self.limitType == 'user-queue':
            self.check_userqueue()

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None

        conf_str = MERGE_HEALDER % (self.behaviorName)
        if self.limitType == 'car' or self.limitType == 'carpps':

            if self.operation == 'create':
                if self.limitType == 'car':
                    conf_str += MERGE_CAR_HEAL % (self.cir)
                if self.limitType == 'carpps':
                    conf_str += MERGE_CARPPS_HEAL % self.cir
                if self.pir:
                    conf_str += '<pir>%s</pir>' % self.pir
                if self.cbs:
                    conf_str += '<cbs>%s</cbs>' % self.cbs
                if self.pbs:
                    conf_str += '<pbs>%s</pbs>' % self.pbs
                if self.greenAction:
                    conf_str += '<greenAction>%s</greenAction>' % self.greenAction
                if self.greenServiceClass:
                    conf_str += '<greenServiceClass>%s</greenServiceClass>' % self.greenServiceClass
                if self.greenColor:
                    conf_str += '<greenColor>%s</greenColor>' % self.greenColor
                if self.yellowAction:
                    conf_str += '<yellowAction>%s</yellowAction>' % self.yellowAction
                if self.yellowServiceClass:
                    conf_str += '<yellowServiceClass>%s</yellowServiceClass>' % self.yellowServiceClass
                if self.yellowColor:
                    conf_str += '<yellowColor>%s</yellowColor>' % self.yellowColor
                if self.redAction:
                    conf_str += '<redAction>%s</redAction>' % self.redAction
                if self.redServiceClass:
                    conf_str += '<redServiceClass>%s</redServiceClass>' % self.redServiceClass
                if self.redColor:
                    conf_str += '<redColor>%s</redColor>' % self.redColor
                if self.colorAware:
                    conf_str += '<colorAware>%s</colorAware>' % self.colorAware
                if self.adjust:
                    conf_str += '<adjust>%s</adjust>' % self.adjust
                if self.yellowRemarkDscp:
                    conf_str += '<yellowRemarkDscp>%s</yellowRemarkDscp>' % self.yellowRemarkDscp
                if self.greenRemarkDscp:
                    conf_str += '<greenRemarkDscp>%s</greenRemarkDscp>' % self.greenRemarkDscp
                if self.redRemarkDscp:
                    conf_str += '<redRemarkDscp>%s</redRemarkDscp>' % self.redRemarkDscp

                if self.limitType == 'car':
                    conf_str += MERGE_CAR_TAIL
                if self.limitType == 'carpps':
                    conf_str += MERGE_CARPPS_TAIL
            if self.operation == 'delete':
                if self.limitType == 'car':
                    conf_str += DELETE_CAR
                if self.limitType == 'carpps':
                    conf_str += DELETE_CARPPS

        if self.limitType == 'unknown-unicast-suppression' or self.limitType == 'multicast-suppression' or self.limitType == 'broadcast-suppression':
            if self.operation == 'create':
                conf_str += MERGE_L2_HEAL % self.limitType, self.cir
                if self.cbs:
                    conf_str += '<cbs>%s</cbs>' % self.cbs
                if self.greenAction:
                    conf_str += '<greenAction>%s</greenAction>' % self.greenAction
                if self.greenServiceClass:
                    conf_str += '<greenServiceClass>%s</greenServiceClass>' % self.greenServiceClass
                if self.greenColor:
                    conf_str += '<greenColor>%s</greenColor>' % self.greenColor
                if self.redAction:
                    conf_str += '<redAction>%s</redAction>' % self.redAction
                if self.redServiceClass:
                    conf_str += '<redServiceClass>%s</redServiceClass>' % self.redServiceClass
                if self.redColor:
                    conf_str += '<redColor>%s</redColor>' % self.redColor
                conf_str += MERGE_L2_TAIL
            if self.operation == 'delete':
                conf_str += DELETE_L2 % (self.limitType)
        if self.limitType == 'flow-car':
            if self.operation == 'create':
                conf_str += MERGE_FLOWCAR_HEAL % (self.cir, self.ipType)
                if self.pir:
                    conf_str += '<pir>%s</pir>' % self.pir
                if self.cbs:
                    conf_str += '<cbs>%s</cbs>' % self.cbs
                if self.pbs:
                    conf_str += '<pbs>%s</pbs>' % self.pbs
                conf_str += MERGE_FLOWCAR_TAIL
            if self.operation == 'delete':
                conf_str += DELETE_FLOWCAR
        if self.limitType == 'user-queue':
            if self.operation == 'create':
                conf_str += MERGE_USERQUEUE_HEAL % self.cir
                if self.pir:
                    conf_str += '<pir>%s</pir>' % self.pir
                if self.flowQueueName:
                    conf_str += '<flowQueueName>%s</flowQueueName>' % self.flowQueueName
                if self.flowMappingName:
                    conf_str += '<flowMappingName>%s</flowMappingName>' % self.flowMappingName
                if self.gqName:
                    conf_str += '<gqName>%s</gqName>' % self.gqName
                if self.templateName:
                    conf_str += '<templateName>%s</templateName>' % self.templateName
                conf_str += MERGE_USERQUEUE_TAIL
            if self.operation == 'delete':
                conf_str += DELETE_USERQUEUE

        """
        if self.operation == 'delete':
            if self.policyName :
                #global conf_str
                conf_str = conf_str.replace('<qosActRdrPolicy>', '<qosActRdrPolicy xc:operation="delete">')
            else:
                conf_str = conf_str.replace('<qosBehavior>', '<qosBehavior xc:operation="delete">')
        """
        conf_str += MERGE_TAIL
        if not self.limitType and self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qosBehavior xc:operation="merge">',
                '<qosBehavior xc:operation="delete">')
        print('99999', conf_str)
        return conf_str

    def merge_ifcar(self):
        conf_str = self.constuct_xml()
        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_userqueue(self, xml):
        data = dict()
        # str= (xml.split('<qosActUserQueues>')[-1]).split('</qosActUserQueues>')[0]
        find = re.findall(
            r'.*<qosActUserQueues>([\s\S]*)</qosActUserQueues>.*\s*', xml)
        if not find:
            return data
        str = find[0]
        print("kkkkkk", str)

        re_find = re.findall(r'.*<cir>(.*)</cir>.*\s*', str)
        if re_find:
            data['cir'] = re_find[0]
        re_find = re.findall(r'.*<pir>(.*)</pir>.*\s*', str)
        if re_find:
            data['pir'] = re_find[0]
        re_find = re.findall(
            r'.*<flowQueueName>(.*)</flowQueueName>.*\s*', str)
        if re_find:
            data['flowQueueName'] = re_find[0]
        re_find = re.findall(
            r'.*<flowMappingName>(.*)</flowMappingName>.*\s*', str)
        if re_find:
            data['flowMappingName'] = re_find[0]
        re_find = re.findall(r'.*<gqName>(.*)</gqName>.*\s*', str)
        if re_find:
            data['gqName'] = re_find[0]
        re_find = re.findall(r'.*<templateName>(.*)</templateName>.*\s*', str)
        if re_find:
            data['templateName'] = re_find[0]
        return data

    def get_car(self, xml):
        data = dict()
        find = re.findall(r'.*<qosActCars>([\s\S]*)</qosActCars>.*\s*', xml)
        if not find:
            return data
        str = find[0]
        print("kkkkkk", str)

        re_find = re.findall(r'.*<cir>(.*)</cir>.*\s*', str)
        if re_find:
            data['cir'] = re_find[0]
        re_find = re.findall(r'.*<pir>(.*)</pir>.*\s*', str)
        if re_find:
            data['pir'] = re_find[0]
        re_find = re.findall(r'.*<cbs>(.*)</cbs>.*\s*', str)
        if re_find:
            data['cbs'] = re_find[0]
        re_find = re.findall(r'.*<pbs>(.*)</pbs>.*\s*', str)
        if re_find:
            data['pbs'] = re_find[0]
        re_find = re.findall(r'.*<greenAction>(.*)</greenAction>.*\s*', str)
        if re_find:
            data['greenAction'] = re_find[0]
        re_find = re.findall(
            r'.*<greenServiceClass>(.*)</greenServiceClass>.*\s*', str)
        if re_find:
            data['greenServiceClass'] = re_find[0]
        re_find = re.findall(r'.*<greenColor>(.*)</greenColor>.*\s*', str)
        if re_find:
            data['greenColor'] = re_find[0]
        re_find = re.findall(r'.*<yellowAction>(.*)</yellowAction>.*\s*', str)
        if re_find:
            data['yellowAction'] = re_find[0]
        re_find = re.findall(
            r'.*<yellowServiceClass>(.*)</yellowServiceClass>.*\s*', str)
        if re_find:
            data['yellowServiceClass'] = re_find[0]
        re_find = re.findall(r'.*<yellowColor>(.*)</yellowColor>.*\s*', str)
        if re_find:
            data['yellowColor'] = re_find[0]
        re_find = re.findall(r'.*<redAction>(.*)</redAction>.*\s*', str)
        if re_find:
            data['redAction'] = re_find[0]

        re_find = re.findall(
            r'.*<redServiceClass>(.*)</redServiceClass>.*\s*', str)
        if re_find:
            data['redServiceClass'] = re_find[0]
        re_find = re.findall(r'.*<redColor>(.*)</redColor>.*\s*', str)
        if re_find:
            data['redColor'] = re_find[0]
        re_find = re.findall(r'.*<colorAware>(.*)</colorAware>.*\s*', str)
        if re_find:
            data['colorAware'] = re_find[0]
        re_find = re.findall(
            r'.*<greenRemarkDscp>(.*)</greenRemarkDscp>.*\s*', str)
        if re_find:
            data['greenRemarkDscp'] = re_find[0]
        re_find = re.findall(
            r'.*<yellowRemarkDscp>(.*)</yellowRemarkDscp>.*\s*', str)
        if re_find:
            data['yellowRemarkDscp'] = re_find[0]
        re_find = re.findall(
            r'.*<redRemarkDscp>(.*)</redRemarkDscp>.*\s*', str)
        if re_find:
            data['redRemarkDscp'] = re_find[0]
        re_find = re.findall(r'.*<adjust>(.*)</adjust>.*\s*', str)
        if re_find:
            data['adjust'] = re_find[0]

        return data

    def get_carpps(self, xml):
        data = dict()
        find = re.findall(
            r'.*<qosActCarPpss>([\s\S]*)</qosActCarPpss>.*\s*', xml)
        if not find:
            return data
        str = find[0]
        print("kkkkkk", str)

        re_find = re.findall(r'.*<cir>(.*)</cir>.*\s*', str)
        if re_find:
            data['cir'] = re_find[0]
        re_find = re.findall(r'.*<pir>(.*)</pir>.*\s*', str)
        if re_find:
            data['pir'] = re_find[0]
        re_find = re.findall(r'.*<cbs>(.*)</cbs>.*\s*', str)
        if re_find:
            data['cbs'] = re_find[0]
        re_find = re.findall(r'.*<pbs>(.*)</pbs>.*\s*', str)
        if re_find:
            data['pbs'] = re_find[0]
        re_find = re.findall(r'.*<greenAction>(.*)</greenAction>.*\s*', str)
        if re_find:
            data['greenAction'] = re_find[0]
        re_find = re.findall(
            r'.*<greenServiceClass>(.*)</greenServiceClass>.*\s*', str)
        if re_find:
            data['greenServiceClass'] = re_find[0]
        re_find = re.findall(r'.*<greenColor>(.*)</greenColor>.*\s*', str)
        if re_find:
            data['greenColor'] = re_find[0]
        re_find = re.findall(r'.*<yellowAction>(.*)</yellowAction>.*\s*', str)
        if re_find:
            data['yellowAction'] = re_find[0]
        re_find = re.findall(
            r'.*<yellowServiceClass>(.*)</yellowServiceClass>.*\s*', str)
        if re_find:
            data['yellowServiceClass'] = re_find[0]
        re_find = re.findall(r'.*<yellowColor>(.*)</yellowColor>.*\s*', str)
        if re_find:
            data['yellowColor'] = re_find[0]
        re_find = re.findall(r'.*<redAction>(.*)</redAction>.*\s*', str)
        if re_find:
            data['redAction'] = re_find[0]

        re_find = re.findall(
            r'.*<redServiceClass>(.*)</redServiceClass>.*\s*', str)
        if re_find:
            data['redServiceClass'] = re_find[0]
        re_find = re.findall(r'.*<redColor>(.*)</redColor>.*\s*', str)
        if re_find:
            data['redColor'] = re_find[0]
        re_find = re.findall(r'.*<colorAware>(.*)</colorAware>.*\s*', str)
        if re_find:
            data['colorAware'] = re_find[0]
        re_find = re.findall(
            r'.*<greenRemarkDscp>(.*)</greenRemarkDscp>.*\s*', str)
        if re_find:
            data['greenRemarkDscp'] = re_find[0]
        re_find = re.findall(
            r'.*<yellowRemarkDscp>(.*)</yellowRemarkDscp>.*\s*', str)
        if re_find:
            data['yellowRemarkDscp'] = re_find[0]
        re_find = re.findall(
            r'.*<redRemarkDscp>(.*)</redRemarkDscp>.*\s*', str)
        if re_find:
            data['redRemarkDscp'] = re_find[0]

        return data

    def get_flowcar(self, xml):
        data = dict()
        find = re.findall(
            r'.*<qosActFlowCars>([\s\S]*)</qosActFlowCars>.*\s*', xml)
        if not find:
            return data

        str = find[0]
        print("kkkkkk", str)

        re_find = re.findall(r'.*<cir>(.*)</cir>.*\s*', str)
        if re_find:
            data['cir'] = re_find[0]
        re_find = re.findall(r'.*<pir>(.*)</pir>.*\s*', str)
        if re_find:
            data['pir'] = re_find[0]
        re_find = re.findall(r'.*<cbs>(.*)</cbs>.*\s*', str)
        if re_find:
            data['cbs'] = re_find[0]
        re_find = re.findall(r'.*<pbs>(.*)</pbs>.*\s*', str)
        if re_find:
            data['pbs'] = re_find[0]
        re_find = re.findall(r'.*<ipType>(.*)</ipType>.*\s*', str)
        if re_find:
            data['ipType'] = re_find[0]

        return data

    def get_l2(self, xml):

        xml_str_split = list()
        re_type = list()
        output = list()
        find = re.findall(
            r'.*<qosActL2Suppres>([\s\S]*)</qosActL2Suppres>.*\s*', xml)
        if not find:
            return output, re_type
        xml_str_split = re.split('</qosActL2Suppre>', find[0])
        print('00000099999', find)
        print('666666', xml_str_split)
        re_type = re.findall(
            r'.*<suppressType>(.*)</suppressType>.*\s*', find[0])

        for i in range(len(re_type)):
            data = dict()
            re_find = re.findall(r'.*<cir>(.*)</cir>.*\s*', xml_str_split[i])
            if re_find:
                data['cir'] = re_find[0]
            re_find = re.findall(r'.*<cbs>(.*)</cbs>.*\s*', xml_str_split[i])
            if re_find:
                data['cbs'] = re_find[0]
            re_find = re.findall(
                r'.*<greenAction>(.*)</greenAction>.*\s*',
                xml_str_split[i])
            if re_find:
                data['greenAction'] = re_find[0]
            re_find = re.findall(
                r'.*<greenServiceClass>(.*)</greenServiceClass>.*\s*',
                xml_str_split[i])
            if re_find:
                data['greenServiceClass'] = re_find[0]
            re_find = re.findall(
                r'.*<redAction>(.*)</redAction>.*\s*',
                xml_str_split[i])
            if re_find:
                data['redAction'] = re_find[0]

            re_find = re.findall(
                r'.*<redServiceClass>(.*)</redServiceClass>.*\s*',
                xml_str_split[i])
            if re_find:
                data['redServiceClass'] = re_find[0]
            re_find = re.findall(
                r'.*<redColor>(.*)</redColor>.*\s*',
                xml_str_split[i])
            if re_find:
                data['redColor'] = re_find[0]
            output.append(data)
        return output, re_type

    def get_ifcar(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        if not self.behaviorName:
            self.behaviorName = ' '
        conf_str = None
        conf_str = GET_LIMIT % (self.behaviorName)
        print('conf_str', conf_str)
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

                if find_behaviorName:
                    attr['behaviorName'] = find_behaviorName[0]
                    data = self.get_userqueue(xml_str_split[j])
                    if data:
                        attr['user-queue'] = data

                    data = self.get_car(xml_str_split[j])
                    if data:
                        attr['car'] = data
                    data = self.get_carpps(xml_str_split[j])
                    if data:
                        attr['carpps'] = data
                    data = self.get_flowcar(xml_str_split[j])
                    if data:
                        attr['flow-car'] = data
                    data, type = self.get_l2(xml_str_split[j])
                    for i in range(len(type)):
                        if type[i] == 'unknown-unicast-suppression':
                            attr['unknown-unicast-suppression'] = data[i]
                        if type[i] == 'multicast-suppression':
                            attr['multicast-suppression'] = data[i]
                        if type[i] == 'broadcast-suppression':
                            attr['broadcast-suppression'] = data[i]
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
        if self.limitType:
            self.proposed["limitType"] = self.limitType
        if self.cir:
            self.proposed["cir"] = self.cir
        if self.pir:
            self.proposed["pir"] = self.pir
        if self.cbs:
            self.proposed["cbs"] = self.cbs
        if self.pbs:
            self.proposed["pbs"] = self.pbs
        if self.greenAction:
            self.proposed["greenAction"] = self.greenAction
        if self.greenServiceClass:
            self.proposed["greenServiceClass"] = self.greenServiceClass
        if self.greenColor:
            self.proposed["greenColor"] = self.greenColor
        if self.yellowAction:
            self.proposed["yellowAction"] = self.yellowAction
        if self.yellowServiceClass:
            self.proposed["yellowServiceClass"] = self.yellowServiceClass
        if self.yellowColor:
            self.proposed["yellowColor"] = self.yellowColor
        if self.redAction:
            self.proposed["redAction"] = self.redAction
        if self.redServiceClass:
            self.proposed["redServiceClass"] = self.redServiceClass
        if self.redColor:
            self.proposed["redColor"] = self.redColor
        if self.colorAware:
            self.proposed["colorAware"] = self.colorAware
        if self.greenRemarkDscp:
            self.proposed["greenRemarkDscp"] = self.greenRemarkDscp
        if self.yellowRemarkDscp:
            self.proposed["yellowRemarkDscp"] = self.yellowRemarkDscp
        if self.redRemarkDscp:
            self.proposed["redRemarkDscp"] = self.redRemarkDscp
        if self.flowQueueName:
            self.proposed["flowQueueName"] = self.flowQueueName
        if self.flowMappingName:
            self.proposed["flowMappingName"] = self.flowMappingName
        if self.gqName:
            self.proposed["gqName"] = self.gqName
        if self.templateName:
            self.proposed["templateName"] = self.templateName
        if self.ipType:
            self.proposed["ipType"] = self.ipType
        if self.adjust:
            self.proposed["adjust"] = self.adjust
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
            # self.results["existing"]=ifcarcfg_attr_exist
            self.results["existing"] = ifcarcfg_attr_exist

        if self.operation == 'create':
            self.merge_ifcar()

        if self.operation == 'delete':
            self.undo_ifcar()

        ifcarcfg_attr_end_stat = self.get_ifcar()
        if ifcarcfg_attr_end_stat:
            # self.results["end_stat"]=ifcarcfg_attr_end_stat
            self.results["end_stat"] = ifcarcfg_attr_end_stat

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        behaviorName=dict(required=False, type='str'),
        # l2Suppression
        limitType=dict(
            required=False,
            choices=[
                'car',
                'carpps',
                'unknown-unicast-suppression',
                'multicast-suppression',
                'broadcast-suppression',
                'user-queue',
                'flow-car']),
        cir=dict(required=False, type='str'),
        pir=dict(required=False, type='str'),
        cbs=dict(required=False, type='str'),
        pbs=dict(required=False, type='str'),
        adjust=dict(required=False, type='str'),
        greenAction=dict(
            required=False,
            choices=[
                'pass',
                'discard'],
            default='pass'),
        greenServiceClass=dict(
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
        greenColor=dict(required=False, choices=['green', 'yellow', 'red']),
        yellowAction=dict(required=False, choices=['pass', 'discard']),
        yellowServiceClass=dict(
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
        yellowColor=dict(required=False, choices=['green', 'yellow', 'red']),
        redAction=dict(
            required=False,
            choices=[
                'pass',
                'discard'],
            default='discard'),
        redServiceClass=dict(
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
        redColor=dict(required=False, choices=['green', 'yellow', 'red']),
        colorAware=dict(
            required=False,
            choices=[
                'true',
                'false'],
            default='false'),
        greenRemarkDscp=dict(required=False, type='str'),
        yellowRemarkDscp=dict(required=False, type='str'),
        redRemarkDscp=dict(required=False, type='str'),
        flowQueueName=dict(required=False, type='str'),
        flowMappingName=dict(required=False, type='str'),
        gqName=dict(required=False, type='str'),
        templateName=dict(required=False, type='str'),
        ipType=dict(required=False, choices=['source', 'destination']),
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
