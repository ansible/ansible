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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec, constr_leaf_value
from ansible.module_utils.basic import AnsibleModule
import collections
import re
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ne_qos_profile_car
version_added: "2.6"
short_description:  CAR rate limit in a profile.
description:
    - CAR rate limit in a profile.
options:
    carType:
        description:
            - Action type of profile CAR.
        required: true
        default: car
        choices=['car', 'broadcast', 'multicast', 'unknow_unicast', 'l2_forward', 'l3_forward', 'bum', 'bu']

    direction:
        description:
            - Direction of traffic to which profile CAR applies.
        required: true
        default: null
        choices=['inbound', 'outbound', 'all'])

    cir:
        description:
            - Committed information rate, in kbit/s.
            The value is an integer ranging from 0 to 4294967295.
        required: true
        default: null

    cirPercent:
        description:
            - Indicate the percentage of the committed rate.
            The value is an integer ranging from 0 to 100.
        required: true
        default: null

    pir:
        description:
            - Peak information rate, in kbit/s.
            The value is an integer ranging from 0 to 4294967295.
        required: true
        default: null

    pirPercent:
        description:
            - Indicate the peak rate percentage.
            The value is an integer ranging from 0 to 100.
        required: true
        default: null

    cbs:
        description:
            - Committed burst size, in bytes.
            The value is an integer ranging from 0 to 4294967295.
        required: true
        default: null

    pbs:
        description:
            - Peak burst size, in bytes.
            The value is an integer ranging from 0 to 4294967295.
        required: true
        default: null

    greenAction:
        description:
            - Mode in which a packet marked green is processed.
        required: true
        default: null
        choices=['pass', 'discard']

    greenServiceClass:
        description:
            - Service class of a packet that is marked green.
        required: true
        default: null
        choices=['green', 'yellow', 'red']

    greenColor:
        description:
            - Color of a packet that is marked green.
        required: true
        default: null
        choices=['green', 'yellow', 'red']

    yellowAction:
        description:
            - Mode in which a packet marked yellow is processed.
        required: true
        default: null
        choices=['pass', 'discard']

    yellowServiceClass:
        description:
            - Service class of a packet that is marked yellow.
        required: true
        default: null
        choices=['green', 'yellow', 'red']

    yellowColor:
        description:
            - Color of a packet that is marked yellow.
        required: true
        default: null
        choices=['green', 'yellow', 'red']


    redAction:
        description:
            - Mode in which a packet marked red is processed.
        required: true
        default: null
        choices=['pass', 'discard']

    redServiceClass:
        description:
            - Service class of a packet that is marked red.
        required: true
        default: null
        choices=['green', 'yellow', 'red']

    redColor:
        description:
            - Color of a packet that is marked red.
        required: true
        default: null
        choices=['green', 'yellow', 'red']

    colorAware:
        description:
            - Specify the color-aware mode for CAR. By default, the CAR action is insensitive to the packet color. When the packet rate is lower than the \
            CIR, the packet is considered green. When color-aware is specified in the CAR action, the current color of the packet is concerned. If the \
            current color of the packet is green, the packet is considered green when the packet rate is lower than the CIR. If the current packet is \
            yellow, the packet is considered yellow even if the packet rate is lower than the CIR.
        required: true
        default: null
        choices=['true', 'false']

    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_profile_car module test
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


  - name: Config car
    ne_qos_profile_car:
      profileName: test
      carType:car
      direction:outbound
      cir:1000
      operation: create
      provider: "{{ cli }}"

  - name: undo car
    ne_qos_profile_car:
      profileName: test
      carType:car
      direction:outbound
      operation: delete
      provider: "{{ cli }}"

  - name: Get car configuration in qos-profile
    ne_qos_profile_car:
      profileName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample:  {
        "operation": "getconfig",
        "profileName": "test"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "carType": "car",
            "cbs": "18700",
            "cir": "100",
            "colorAware": "false",
            "direction": "all",
            "greenAction": "pass",
            "profileName": "test",
            "redAction": "discard"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  [
        {
            "carType": "car",
            "cbs": "18700",
            "cir": "100",
            "colorAware": "false",
            "direction": "all",
            "greenAction": "pass",
            "profileName": "test",
            "redAction": "discard"
        }
    ],
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: false
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <hqos>
        <hqosProfiles>
            <hqosProfile>
                <profileName>%s</profileName>
                <hqosProCars>
                    <hqosProCar>
"""

MERGE_CLASS_TAIL = """
                    </hqosProCar>
                </hqosProCars>
            </hqosProfile>
        </hqosProfiles>
    </hqos>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <hqos>
        <hqosProfiles>
            <hqosProfile>
                <profileName>%s</profileName>
                <hqosProCars>
                    <hqosProCar/>
                </hqosProCars>
            </hqosProfile>
        </hqosProfiles>
    </hqos>
</qos>
</filter>
"""


class QosProfileCarCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.profileName = self.module.params['profileName']
        self.carType = self.module.params['carType']
        self.direction = self.module.params['direction']
        self.cir = self.module.params['cir']
        self.cirPercent = self.module.params['cirPercent']
        self.pir = self.module.params['pir']
        self.pirPercent = self.module.params['pirPercent']
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
        self.adjustValue = self.module.params['adjustValue']
        self.priCarTmpltName = self.module.params['priCarTmpltName']
        self.priorityAware = self.module.params['priorityAware']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        self.results = dict()
        self.results["existing"] = []
        self.results["end_state"] = []
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
        msg_para = ""
        if not self.profileName:
            msg_para += " flowQueueName"
        if self.operation != "getconfig":
            if not self.carType:
                msg_para += " carType"
            if not self.direction:
                msg_para += " direction"
        if msg_para:
            self.module.fail_json(
                msg='Error: Please input the necessary element includes%s.' % msg_para)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None

        conf_str = MERGE_CLASS_HEALDER % self.profileName
        if self.carType:
            conf_str = constr_leaf_value(conf_str, 'carType', self.carType)
        if self.direction:
            conf_str = constr_leaf_value(conf_str, 'direction', self.direction)
        if self.cir:
            conf_str = constr_leaf_value(conf_str, 'cir', self.cir)
        if self.cirPercent:
            conf_str = constr_leaf_value(
                conf_str, 'cirPercent', self.cirPercent)
        if self.pir:
            conf_str = constr_leaf_value(conf_str, 'pir', self.pir)
        if self.pirPercent:
            conf_str = constr_leaf_value(
                conf_str, 'pirPercent', self.pirPercent)
        if self.cbs:
            conf_str = constr_leaf_value(conf_str, 'cbs', self.cbs)
        if self.pbs:
            conf_str = constr_leaf_value(conf_str, 'pbs', self.pbs)
        if self.greenAction:
            conf_str = constr_leaf_value(
                conf_str, 'greenAction', self.greenAction)
        if self.greenServiceClass:
            conf_str = constr_leaf_value(
                conf_str, 'greenServiceClass', self.greenServiceClass)
        if self.greenColor:
            conf_str = constr_leaf_value(
                conf_str, 'greenColor', self.greenColor)
        if self.yellowAction:
            conf_str = constr_leaf_value(
                conf_str, 'yellowAction', self.yellowAction)
        if self.yellowServiceClass:
            conf_str = constr_leaf_value(
                conf_str, 'yellowServiceClass', self.yellowServiceClass)
        if self.yellowColor:
            conf_str = constr_leaf_value(
                conf_str, 'yellowColor', self.yellowColor)
        if self.redAction:
            conf_str = constr_leaf_value(conf_str, 'redAction', self.redAction)
        if self.redServiceClass:
            conf_str = constr_leaf_value(
                conf_str, 'redServiceClass', self.redServiceClass)
        if self.redColor:
            conf_str = constr_leaf_value(conf_str, 'redColor', self.redColor)
        if self.colorAware:
            conf_str = constr_leaf_value(
                conf_str, 'colorAware', self.colorAware)
        if self.adjustValue:
            conf_str = constr_leaf_value(
                conf_str, 'adjustValue', self.adjustValue)
        if self.priCarTmpltName:
            conf_str = constr_leaf_value(
                conf_str, 'priCarTmpltName', self.priCarTmpltName)
        if self.priorityAware:
            conf_str = constr_leaf_value(
                conf_str, 'priorityAware', self.priorityAware)

        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<hqosProCar>', '<hqosProCar xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL

        print('88888', conf_str)
        return conf_str

    def merge_profilecar(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_profilecar(self):
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS % self.profileName
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if not ("<data/>" in xml_str):
            print('66666', xml_str)
            xml_str_split = re.split('</hqosProCar>', xml_str)
            print('77777', xml_str_split)

            for j in range(len(xml_str_split)):
                find_carType = re.findall(
                    r'.*<carType>(.*)</carType>.*\s*', xml_str_split[j])
                find_direction = re.findall(
                    r'.*<direction>(.*)</direction>.*\s*', xml_str_split[j])
                find_cir = re.findall(
                    r'.*<cir>(.*)</cir>.*\s*', xml_str_split[j])
                find_cirPercent = re.findall(
                    r'.*<cirPercent>(.*)</cirPercent>.*\s*', xml_str_split[j])
                find_pir = re.findall(
                    r'.*<pir>(.*)</pir>.*\s*', xml_str_split[j])
                find_pirPercent = re.findall(
                    r'.*<pirPercent>(.*)</pirPercent>.*\s*', xml_str_split[j])
                find_cbs = re.findall(
                    r'.*<cbs>(.*)</cbs>.*\s*', xml_str_split[j])
                find_pbs = re.findall(
                    r'.*<pbs>(.*)</pbs>.*\s*', xml_str_split[j])
                find_greenAction = re.findall(
                    r'.*<greenAction>(.*)</greenAction>.*\s*', xml_str_split[j])
                find_greenServiceClass = re.findall(
                    r'.*<greenServiceClass>(.*)</greenServiceClass>.*\s*', xml_str_split[j])
                find_greenColor = re.findall(
                    r'.*<greenColor>(.*)</greenColor>.*\s*', xml_str_split[j])
                find_yellowAction = re.findall(
                    r'.*<yellowAction>(.*)</yellowAction>.*\s*', xml_str_split[j])
                find_yellowServiceClass = re.findall(
                    r'.*<yellowServiceClass>(.*)</yellowServiceClass>.*\s*', xml_str_split[j])
                find_yellowColor = re.findall(
                    r'.*<yellowColor>(.*)</yellowColor>.*\s*', xml_str_split[j])
                find_redAction = re.findall(
                    r'.*<redAction>(.*)</redAction>.*\s*', xml_str_split[j])
                find_redServiceClass = re.findall(
                    r'.*<redServiceClass>(.*)</redServiceClass>.*\s*', xml_str_split[j])
                find_redColor = re.findall(
                    r'.*<redColor>(.*)</redColor>.*\s*', xml_str_split[j])
                find_colorAware = re.findall(
                    r'.*<colorAware>(.*)</colorAware>.*\s*', xml_str_split[j])
                find_adjustValue = re.findall(
                    r'.*<adjustValue>(.*)</adjustValue>.*\s*', xml_str_split[j])
                find_priCarTmpltName = re.findall(
                    r'.*<priCarTmpltName>(.*)</priCarTmpltName>.*\s*', xml_str_split[j])
                find_priorityAware = re.findall(
                    r'.*<priorityAware>(.*)</priorityAware>.*\s*', xml_str_split[j])

                if find_carType:
                    attr = dict()
                    attr['carType'] = find_carType[0]
                    attr['profileName'] = self.profileName
                    if find_direction:
                        attr['direction'] = find_direction[0]
                    if find_cir:
                        attr['cir'] = find_cir[0]
                    if find_cirPercent:
                        attr['cirPercent'] = find_cirPercent[0]
                    if find_pir:
                        attr['pir'] = find_pir[0]
                    if find_pirPercent:
                        attr['pirPercent'] = find_pirPercent[0]
                    if find_cbs:
                        attr['cbs'] = find_cbs[0]
                    if find_pbs:
                        attr['pbs'] = find_pbs[0]
                    if find_greenAction:
                        attr['greenAction'] = find_greenAction[0]
                    if find_greenServiceClass:
                        attr['greenServiceClass'] = find_greenServiceClass[0]
                    if find_greenColor:
                        attr['greenColor'] = find_greenColor[0]
                    if find_yellowAction:
                        attr['yellowAction'] = find_yellowAction[0]
                    if find_yellowServiceClass:
                        attr['yellowServiceClass'] = find_yellowServiceClass[0]
                    if find_yellowColor:
                        attr['yellowColor'] = find_yellowColor[0]
                    if find_redAction:
                        attr['redAction'] = find_redAction[0]
                    if find_redServiceClass:
                        attr['redServiceClass'] = find_redServiceClass[0]
                    if find_redColor:
                        attr['redColor'] = find_redColor[0]
                    if find_colorAware:
                        attr['colorAware'] = find_colorAware[0]
                    if find_adjustValue:
                        attr['adjustValue'] = find_adjustValue[0]
                    if find_priCarTmpltName:
                        attr['priCarTmpltName'] = find_priCarTmpltName[0]
                    if find_priorityAware:
                        attr['priorityAware'] = find_priorityAware[0]
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_profilecar(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.profileName:
            self.proposed["profileName"] = self.profileName
        if self.carType:
            self.proposed["carType"] = self.carType
        if self.direction:
            self.proposed["direction"] = self.direction
        if self.cir:
            self.proposed["cir"] = self.cir
        if self.cirPercent:
            self.proposed["cirPercent"] = self.cirPercent
        if self.pir:
            self.proposed["pir"] = self.pir
        if self.pirPercent:
            self.proposed["pirPercent"] = self.pirPercent
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
        if self.adjustValue:
            self.proposed["adjustValue"] = self.adjustValue
        if self.priCarTmpltName:
            self.proposed["priCarTmpltName"] = self.priCarTmpltName
        if self.priorityAware:
            self.proposed["priorityAware"] = self.priorityAware
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        profilecarcfg_attr_exist = self.get_profilecar()
        if profilecarcfg_attr_exist:
            self.results["existing"] = profilecarcfg_attr_exist

        if self.operation == 'create':
            self.merge_profilecar()

        if self.operation == 'delete':
            self.undo_profilecar()

        profilecarcfg_attr_end_state = self.get_profilecar()
        if profilecarcfg_attr_end_state:
            self.results["end_state"] = profilecarcfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        profileName=dict(required=False, type='str'),
        carType=dict(
            required=False,
            choices=[
                'car',
                'broadcast',
                'multicast',
                'unknow_unicast',
                'l2_forward',
                'l3_forward',
                'bum',
                'bu'],
            default='car'),
        direction=dict(required=False, choices=['inbound', 'outbound', 'all']),
        cir=dict(required=False, type='str'),
        cirPercent=dict(required=False, type='str'),
        pir=dict(required=False, type='str'),
        pirPercent=dict(required=False, type='str'),
        cbs=dict(required=False, type='str'),
        pbs=dict(required=False, type='str'),
        greenAction=dict(required=False, choices=['pass', 'discard']),
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
        redAction=dict(required=False, choices=['pass', 'discard']),
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
        colorAware=dict(required=False, choices=['true', 'false']),
        adjustValue=dict(required=False, type='str'),
        priCarTmpltName=dict(required=False, type='str'),
        priorityAware=dict(required=False, choices=['true', 'false']),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosProfileCarCfg = QosProfileCarCfg(argument_spec)
    NEWQosProfileCarCfg.work()


if __name__ == '__main__':
    main()
