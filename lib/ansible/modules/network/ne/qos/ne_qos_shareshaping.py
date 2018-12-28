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
module: ne_qos_shareshaping
version_added: "2.6"
short_description: Configure shared shaping for multiple FQs in a FQ profile.
description:
    - Configure shared shaping for multiple FQs in a FQ profile.
    be:
        description:
            - Best effort (BE), which focuses only on whether packets can reach the destination, regardless of the transmission performance.
        required: true
        default: null
        choices: ['true', 'false']

    af1:
        description:
            - One of the four standard PHB behaviors defined by the Internet Engineering Task Force (IETF). The AF1 service level is higher than the BE \
            service level and can be used for services that do not require high real-time performance.
        required: true
        default: null
        choices: ['true', 'false']

    af2:
        description:
            - One of the four standard PHB behaviors defined by the Internet Engineering Task Force (IETF). The AF2 service level is higher than that of \
            BE and AF1 and can be used for services with high real-time requirements.
        required: true
        default: null
        choices: ['true', 'false']

    af3:
        description:
            - One of the four standard PHB behaviors defined by the Internet Engineering Task Force (IETF). The AF3 service level is higher than that of \
            BE, AF1, and AF2, and can be used for services with high real-time requirements, such as voice and video services.
        required: true
        default: null
        choices: ['true', 'false']

    af4:
        description:
            - One of the four standard PHB behaviors defined by the Internet Engineering Task Force (IETF). The AF4 service level is higher than that of \
            BE, AF1, AF2, and AF3, and applies to key data services requiring guaranteed bandwidth and low delay.
        required: true
        default: null
        choices: ['true', 'false']

    ef:
        description:
            - A type of QoS class. The EF service provides absolute high-priority queue scheduling to ensure that the delay of real-time data meets the \
            requirements. In addition, by restricting the data traffic of high priority, you can prevent low-priority PQs from starving.
        required: true
        default: null
        choices: ['true', 'false']

    cs6:
        description:
            - A QoS class that provides a service level lower only than CS7 and is used to ensure the forwarding of protocol packets.
        required: true
        default: null
        choices: ['true', 'false']

    cs7:
        description:
            - A type of QoS class that represents the highest service level.
        required: true
        default: null
        choices: ['true', 'false']

    queueScheduleMode:
        description:
            - Scheduling mode.
        required: true
        default: null
        choices=['notConfig', 'pq', 'wfq', 'lpq']

    shapId:
        description:
            - ID of a traffic shaping profile.
            The data type is 1.
        required: true
        default: null

    weight:
        description:
            - WFQ weight.
            The value is an integer ranging from 1 to 100.
        required: true
        default: null


    shareShapingPir:
        description:
            - Shared shaping rate of multiple FQs.
            The value is an integer ranging from 1 to 4294967294.
        required: true
        default: null

    pbs:
        description:
            - Peak burst size.
            The value is an integer ranging from 1 to 4194304.
        required: true
        default: null

    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_shareshaping module test
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

  - name: Config share-shaping be af1
    ne_qos_shareshaping:
      flowQueueName: test
      be: true
      ef:false
      queueScheduleMode: pq
      shareShapingPir:1000
      pbs: 100
      operation: create
      provider: "{{ cli }}"

  - name: Undo share-shaping be af1
    ne_qos_shareshaping:
      flowQueueName: test
      be: true
      ef:false
      queueScheduleMode: pq
      shareShapingPir:1000
      operation: delete
      provider: "{{ cli }}"

  - name: Get flow-queue queue configurations in flow-queue template test
    ne_qos_shareshaping:
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
        "af1": "true",
        "af4": "false",
        "be": "true",
        "flowQueueName": "test",
        "operation": "create",
        "shareShapingPir": "1000"
    }
}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "af1": "true",
            "af2": "false",
            "af3": "false",
            "af4": "true",
            "be": "false",
            "cs6": "false",
            "cs7": "false",
            "ef": "false",
            "flowQueueName": "test",
            "queueScheduleMode": "notConfig",
            "shareShapingPir": "1000"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:   [
        {
            "af1": "true",
            "af2": "false",
            "af3": "false",
            "af4": "false",
            "be": "true",
            "cs6": "false",
            "cs7": "false",
            "ef": "false",
            "flowQueueName": "test",
            "queueScheduleMode": "notConfig",
            "shareShapingPir": "1000"
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
                <hqosShareShapes>
                    <hqosShareShape>
"""

MERGE_CLASS_TAIL = """
                    </hqosShareShape>
                </hqosShareShapes>
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
                <hqosShareShapes>
                    <hqosShareShape/>
                </hqosShareShapes>
            </hqosFlowQueue>
        </hqosFlowQueues>
    </hqos>
</qos>
</filter>
"""


class QosShareShapingCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.flowQueueName = self.module.params['flowQueueName']
        self.shapId = self.module.params['shapId']
        self.be = self.module.params['be']
        self.af1 = self.module.params['af1']
        self.af2 = self.module.params['af2']
        self.af3 = self.module.params['af3']
        self.af4 = self.module.params['af4']
        self.ef = self.module.params['ef']
        self.cs6 = self.module.params['cs6']
        self.cs7 = self.module.params['cs7']
        self.queueScheduleMode = self.module.params['queueScheduleMode']
        self.weight = self.module.params['weight']
        self.shareShapingPir = self.module.params['shareShapingPir']
        self.pbs = self.module.params['pbs']
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
            if not self.shareShapingPir:
                msg_para += " shareShapingPir"
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
        if self.shapId:
            conf_str = constr_leaf_value(conf_str, 'shapId', self.shapId)
        if self.be:
            conf_str = constr_leaf_value(conf_str, 'be', self.be)
        if self.af1:
            conf_str = constr_leaf_value(conf_str, 'af1', self.af1)
        if self.af2:
            conf_str = constr_leaf_value(conf_str, 'af2', self.af2)
        if self.af3:
            conf_str = constr_leaf_value(conf_str, 'af3', self.af3)
        if self.af4:
            conf_str = constr_leaf_value(conf_str, 'af4', self.af4)
        if self.ef:
            conf_str = constr_leaf_value(conf_str, 'ef', self.ef)
        if self.cs6:
            conf_str = constr_leaf_value(conf_str, 'cs6', self.cs6)
        if self.cs7:
            conf_str = constr_leaf_value(conf_str, 'cs7', self.cs6)
        if self.queueScheduleMode:
            conf_str = constr_leaf_value(
                conf_str, 'queueScheduleMode', self.queueScheduleMode)
        if self.weight:
            conf_str = constr_leaf_value(conf_str, 'weight', self.weight)
        if self.shareShapingPir:
            conf_str = constr_leaf_value(
                conf_str, 'shareShapingPir', self.shareShapingPir)
        if self.pbs:
            conf_str = constr_leaf_value(conf_str, 'pbs', self.pbs)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<hqosShareShape>',
                '<hqosShareShape xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        if self.shapId:
            conf_str = conf_str.replace('hqosShareShape', 'hqosShareShapeID')
        print('88888', conf_str)
        return conf_str

    def merge_shareshaping(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_shareshaping(self):
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS % self.flowQueueName
        flag_show = 0
        xml_str = ""
        xml_str_para0 = get_nc_config(self.module, conf_str)
        print('xml_str0', xml_str)
        if not ("<data/>" in xml_str_para0):
            xml_str += xml_str_para0
        xml_str_para1 = get_nc_config(
            self.module, conf_str.replace(
                'hqosShareShape', 'hqosShareShapeID'))
        print('xml_str0', xml_str_para1)
        if not ("<data/>" in xml_str_para1):
            xml_str += xml_str_para1
        if xml_str:

            print('66666', xml_str)
            find_flowQueueName = re.findall(
                r'.*<flowQueueName>(.*)</flowQueueName>.*\s*', xml_str)

            xml_str_split = re.split('</hqosShareShape', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                attr = dict()
                find_shapId = re.findall(
                    r'.*<shapId>(.*)</shapId>.*\s*', xml_str_split[j])
                find_be = re.findall(r'.*<be>(.*)</be>.*\s*', xml_str_split[j])
                find_af1 = re.findall(
                    r'.*<af1>(.*)</af1>.*\s*', xml_str_split[j])
                find_af2 = re.findall(
                    r'.*<af2>(.*)</af2>.*\s*', xml_str_split[j])
                find_af3 = re.findall(
                    r'.*<af3>(.*)</af3>.*\s*', xml_str_split[j])
                find_af4 = re.findall(
                    r'.*<af4>(.*)</af4>.*\s*', xml_str_split[j])
                find_ef = re.findall(r'.*<ef>(.*)</ef>.*\s*', xml_str_split[j])
                find_cs6 = re.findall(
                    r'.*<cs6>(.*)</cs6>.*\s*', xml_str_split[j])
                find_cs7 = re.findall(
                    r'.*<cs7>(.*)</cs7>.*\s*', xml_str_split[j])
                find_queueScheduleMode = re.findall(
                    r'.*<queueScheduleMode>(.*)</queueScheduleMode>.*\s*', xml_str_split[j])
                find_weight = re.findall(
                    r'.*<weight>(.*)</weight>.*\s*', xml_str_split[j])
                find_shareShapingPir = re.findall(
                    r'.*<shareShapingPir>(.*)</shareShapingPir>.*\s*', xml_str_split[j])
                find_pbs = re.findall(
                    r'.*<pbs>(.*)</pbs>.*\s*', xml_str_split[j])

                if find_shareShapingPir:
                    attr['shareShapingPir'] = find_shareShapingPir[0]
                    attr['flowQueueName'] = self.flowQueueName
                    if find_shapId:
                        attr['shapId'] = find_shapId[0]
                    if find_be:
                        attr['be'] = find_be[0]
                    if find_af1:
                        attr['af1'] = find_af1[0]
                    if find_af2:
                        attr['af2'] = find_af2[0]
                    if find_af3:
                        attr['af3'] = find_af3[0]
                    if find_af4:
                        attr['af4'] = find_af4[0]
                    if find_ef:
                        attr['ef'] = find_ef[0]
                    if find_cs6:
                        attr['cs6'] = find_cs6[0]
                    if find_cs7:
                        attr['cs7'] = find_cs7[0]
                    if find_queueScheduleMode:
                        attr['queueScheduleMode'] = find_queueScheduleMode[0]
                    if find_weight:
                        attr['weight'] = find_weight[0]

                    if find_pbs:
                        attr['pbs'] = find_pbs[0]
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_shareshaping(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_SHARESHAP")
        # self.changed = True

    def get_proposed(self):

        if self.flowQueueName:
            self.proposed["flowQueueName"] = self.flowQueueName
        if self.shapId:
            self.proposed["shapId"] = self.shapId
        if self.be:
            self.proposed["be"] = self.be
        if self.af1:
            self.proposed["af1"] = self.af1
        if self.af2:
            self.proposed["af2"] = self.af2
        if self.af3:
            self.proposed["af3"] = self.af3
        if self.af4:
            self.proposed["af4"] = self.af4
        if self.ef:
            self.proposed["ef"] = self.ef
        if self.cs6:
            self.proposed["cs6"] = self.cs6
        if self.cs7:
            self.proposed["cs7"] = self.cs7
        if self.queueScheduleMode:
            self.proposed["queueScheduleMode"] = self.queueScheduleMode
        if self.weight:
            self.proposed["weight"] = self.weight
        if self.shareShapingPir:
            self.proposed["shareShapingPir"] = self.shareShapingPir
        if self.pbs:
            self.proposed["pbs"] = self.pbs
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        shareshapingcfg_attr_exist = self.get_shareshaping()
        if shareshapingcfg_attr_exist:
            self.results["existing"] = shareshapingcfg_attr_exist

        if self.operation == 'create':
            self.merge_shareshaping()

        if self.operation == 'delete':
            self.undo_shareshaping()

        shareshapingcfg_attr_end_state = self.get_shareshaping()
        if shareshapingcfg_attr_end_state:
            self.results["end_state"] = shareshapingcfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        flowQueueName=dict(required=False, type='str'),
        shapId=dict(required=False, type='str'),
        be=dict(required=False, choices=['true', 'false']),
        af1=dict(required=False, choices=['true', 'false']),
        af2=dict(required=False, choices=['true', 'false']),
        af3=dict(required=False, choices=['true', 'false']),
        af4=dict(required=False, choices=['true', 'false']),
        ef=dict(required=False, choices=['true', 'false']),
        cs6=dict(required=False, choices=['true', 'false']),
        cs7=dict(required=False, choices=['true', 'false']),
        queueScheduleMode=dict(
            required=False, choices=[
                'notConfig', 'pq', 'wfq', 'lpq']),
        weight=dict(required=False, type='str'),
        shareShapingPir=dict(required=False, type='str'),
        pbs=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosShareShapingCfg = QosShareShapingCfg(argument_spec)
    NEWQosShareShapingCfg.work()


if __name__ == '__main__':
    main()
