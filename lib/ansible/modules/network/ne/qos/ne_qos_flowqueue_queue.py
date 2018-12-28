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
module: ne_qos_flowqueue_queue
version_added: "2.6"
short_description: The queue command is used to modify the scheduling parameters of a flow queue in a flow queue profile.
description:
    - The queue command is used to modify the scheduling parameters of a flow queue in a flow queue profile.
    serviceClass:
        description:
            - Identify a flow queue.
        required: true
        default: null
        choices: ['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']

    queueScheduleMode:
        description:
            - Scheduling mode.
        required: true
        default: null
        choices: ['pq', 'wfq', 'lpq']

    weight:
        description:
            - WFQ weight.
            The value is an integer ranging from 1 to 100.
        required: true
        default: null

    shaping:
        description:
            - Shaping rate of each flow queue.
            The value is an integer ranging from 8 to 4294967294.
        required: true
        default: null

    shapingPercentage:
        description:
            - Shaping percentage, to be specific, percentage of the traffic-shaping bandwidth to the interface bandwidth.
            The value is an integer ranging from 0 to 100.
        required: true
        default: null

    car:
        description:
            - CAR for flow queue rates.
            The value is an integer ranging from 8 to 4294967294.
        required: true
        default: null

    carPercentage:
        description:
            - CAR shaping percentage.
            The value is an integer ranging from 0 to 100.
        required: true
        default: null

    pbs:
        description:
            - Buffer size, indicating the volume of the allowed peak traffic on an interface after traffic shaping is configured on the interface.
            The value is an integer ranging from 1 to 10000000.
        required: true
        default: null

    wredName:
        description:
            - WRED object used by a flow queue.
            The value is a string of characters.
        required: true
        default: null

    lowlatency:
        description:
            - Configure the low delay mode for a queue.
        required: true
        default: null
        choices=['disable', 'enable']

    lowjitter:
        description:
            - Low jitter working mode.
        required: true
        default: null
        choices=['disable', 'enable']

    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_flowqueue_queue module test
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

  - name: Config flow-queue queue
    ne_qos_flowqueue_queue:
      flowQueueName: test
      serviceClass: ef
      queueScheduleMode: wfq
      weight: 10
      shaping: 1000
      pbs: 100
      wredName: testWred
      operation: create
      provider: "{{ cli }}"

  - name: Undo flow-queue queue
    ne_qos_flowqueue_queue:
      flowQueueName: test
      serviceClass: ef
      operation: delete
      provider: "{{ cli }}"

  - name: Get flow-queue queue configurations in flow-queue template test
    ne_qos_flowqueue_queue:
      flowQueueName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "flowQueueName": "test",
        "operation": "getconfig"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: [
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "pq",
            "serviceClass": "be",
            "shaping": "100"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "af1",
            "weight": "10"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "af2",
            "weight": "10"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "af3",
            "weight": "15"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "af4",
            "weight": "15"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "pq",
            "serviceClass": "ef"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "pq",
            "serviceClass": "cs6"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "pq",
            "serviceClass": "cs7",
            "shaping": "100"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  [
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "be",
            "weight": "10"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "af1",
            "weight": "10"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "af2",
            "weight": "10"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "af3",
            "weight": "15"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "wfq",
            "serviceClass": "af4",
            "weight": "15"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "pq",
            "serviceClass": "ef"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "pq",
            "serviceClass": "cs6"
        },
        {
            "flowQueueName": "text",
            "lowlatency": "disable",
            "queueScheduleMode": "pq",
            "serviceClass": "cs7",
            "shaping": "100"
        }
    ],
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <hqos>
        <hqosFlowQueues>
            <hqosFlowQueue>
                <flowQueueName>%s</flowQueueName>
                <hqosQueues>
                    <hqosQueue>
"""

MERGE_CLASS_TAIL = """
                    </hqosQueue>
                </hqosQueues>
            </hqosFlowQueue>
        </hqosFlowQueues>
    </hqos>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <hqos>
        <hqosFlowQueues>
            <hqosFlowQueue>
                <flowQueueName>%s</flowQueueName>
                <hqosQueues>
                    <hqosQueue/>
                </hqosQueues>
            </hqosFlowQueue>
        </hqosFlowQueues>
    </hqos>
</qos>
</filter>
"""


class QosQueueCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.flowQueueName = self.module.params['flowQueueName']
        self.serviceClass = self.module.params['serviceClass']
        self.queueScheduleMode = self.module.params['queueScheduleMode']
        self.weight = self.module.params['weight']
        self.shaping = self.module.params['shaping']
        self.shapingPercentage = self.module.params['shapingPercentage']
        self.car = self.module.params['car']
        self.carPercentage = self.module.params['carPercentage']
        self.pbs = self.module.params['pbs']
        self.wredName = self.module.params['wredName']
        self.lowlatency = self.module.params['lowlatency']
        self.lowjitter = self.module.params['lowjitter']
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
        if not self.flowQueueName:
            msg_para += " flowQueueName"
        if self.operation != "getconfig":
            if not self.serviceClass:
                msg_para += " serviceClass"
        if msg_para:
            self.module.fail_json(
                msg='Error: Please input the necessary element includes%s.' % msg_para)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % self.flowQueueName
        conf_str = constr_leaf_value(
            conf_str, 'serviceClass', self.serviceClass)
        if self.queueScheduleMode:
            conf_str = constr_leaf_value(
                conf_str, 'queueScheduleMode', self.queueScheduleMode)
        if self.weight:
            conf_str = constr_leaf_value(conf_str, 'weight', self.weight)
        if self.shaping:
            conf_str = constr_leaf_value(conf_str, 'shaping', self.shaping)
        if self.shapingPercentage:
            conf_str = constr_leaf_value(
                conf_str, 'shapingPercentage', self.shapingPercentage)
        if self.car:
            conf_str = constr_leaf_value(conf_str, 'car', self.car)
        if self.carPercentage:
            conf_str = constr_leaf_value(
                conf_str, 'carPercentage', self.carPercentage)
        if self.pbs:
            conf_str = constr_leaf_value(conf_str, 'pbs', self.pbs)
        if self.wredName:
            conf_str = constr_leaf_value(conf_str, 'wredName', self.wredName)
        if self.lowjitter:
            conf_str = constr_leaf_value(conf_str, 'lowjitter', self.lowjitter)
        if self.lowlatency:
            conf_str = constr_leaf_value(
                conf_str, 'lowlatency', self.lowlatency)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<hqosQueue>', '<hqosQueue xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_queue(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_queue(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS % self.flowQueueName
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return None
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</hqosQueue>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                attr = dict()
                find_flowQueueName = re.findall(
                    r'.*<flowQueueName>(.*)</flowQueueName>.*\s*', xml_str_split[j])
                find_serviceClass = re.findall(
                    r'.*<serviceClass>(.*)</serviceClass>.*\s*', xml_str_split[j])
                find_queueScheduleMode = re.findall(
                    r'.*<queueScheduleMode>(.*)</queueScheduleMode>.*\s*', xml_str_split[j])
                find_weight = re.findall(
                    r'.*<weight>(.*)</weight>.*\s*', xml_str_split[j])
                find_shaping = re.findall(
                    r'.*<shaping>(.*)</shaping>.*\s*', xml_str_split[j])
                find_shapingPercentage = re.findall(
                    r'.*<shapingPercentage>(.*)</shapingPercentage>.*\s*', xml_str_split[j])
                find_car = re.findall(
                    r'.*<car>(.*)</car>.*\s*', xml_str_split[j])
                find_carPercentage = re.findall(
                    r'.*<carPercentage>(.*)</carPercentage>.*\s*', xml_str_split[j])
                find_pbs = re.findall(
                    r'.*<pbs>(.*)</pbs>.*\s*', xml_str_split[j])
                find_wredName = re.findall(
                    r'.*<wredName>(.*)</wredName>.*\s*', xml_str_split[j])
                find_lowlatency = re.findall(
                    r'.*<lowlatency>(.*)</lowlatency>.*\s*', xml_str_split[j])
                find_lowjitter = re.findall(
                    r'.*<lowjitter>(.*)</lowjitter>.*\s*', xml_str_split[j])

                if find_serviceClass:
                    attr['flowQueueName'] = self.flowQueueName
                    attr['serviceClass'] = find_serviceClass[0]
                    if find_queueScheduleMode:
                        attr['queueScheduleMode'] = find_queueScheduleMode[0]
                    if find_weight and find_queueScheduleMode and find_queueScheduleMode[
                            0] == 'wfq':
                        attr['weight'] = find_weight[0]
                    if find_shaping:
                        attr['shaping'] = find_shaping[0]
                    if find_shapingPercentage:
                        attr['shapingPercentage'] = find_shapingPercentage[0]
                    if find_car:
                        attr['car'] = find_car[0]
                    if find_carPercentage:
                        attr['carPercentage'] = find_carPercentage[0]
                    if find_pbs:
                        attr['pbs'] = find_pbs[0]
                    if find_wredName:
                        attr['wredName'] = find_wredName[0]
                    if find_lowlatency:
                        attr['lowlatency'] = find_lowlatency[0]
                    if find_lowjitter:
                        attr['lowjitter'] = find_lowjitter[0]

                    output_msg_list.append(attr)

        return output_msg_list

    def undo_queue(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.flowQueueName:
            self.proposed["flowQueueName"] = self.flowQueueName
        if self.serviceClass:
            self.proposed["serviceClass"] = self.serviceClass
        if self.queueScheduleMode:
            self.proposed["queueScheduleMode"] = self.queueScheduleMode
        if self.weight:
            self.proposed["weight"] = self.weight
        if self.shaping:
            self.proposed["shaping"] = self.shaping
        if self.shapingPercentage:
            self.proposed["shapingPercentage"] = self.shapingPercentage
        if self.car:
            self.proposed["car"] = self.car
        if self.carPercentage:
            self.proposed["carPercentage"] = self.carPercentage
        if self.pbs:
            self.proposed["pbs"] = self.pbs
        if self.wredName:
            self.proposed["wredName"] = self.wredName
        if self.lowlatency:
            self.proposed["lowlatency"] = self.lowlatency
        if self.lowjitter:
            self.proposed["lowjitter"] = self.lowjitter
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        queuecfg_attr_exist = self.get_queue()
        if queuecfg_attr_exist:
            self.results["existing"] = queuecfg_attr_exist

        if self.operation == 'create':
            self.merge_queue()

        if self.operation == 'delete':
            self.undo_queue()

        queuecfg_attr_end_state = self.get_queue()
        if queuecfg_attr_end_state:
            self.results["end_state"] = queuecfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        flowQueueName=dict(required=False, type='str'),
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
        queueScheduleMode=dict(required=False, choices=['pq', 'wfq', 'lpq']),
        weight=dict(required=False, type='str'),
        shaping=dict(required=False, type='str'),
        shapingPercentage=dict(required=False, type='str'),
        car=dict(required=False, type='str'),
        carPercentage=dict(required=False, type='str'),
        pbs=dict(required=False, type='str'),
        wredName=dict(required=False, type='str'),
        lowlatency=dict(required=False, choices=['disable', 'enable']),
        lowjitter=dict(required=False, choices=['disable', 'enable']),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosQueueCfg = QosQueueCfg(argument_spec)
    NEWQosQueueCfg.work()


if __name__ == '__main__':
    main()
