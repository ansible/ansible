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
module: ne_qos_profile_userqueue
version_added: "2.6"
short_description: Subscriber queue
description:
    - Subscriber queue (SQ) is a virtual queue. There is no actual cache unit in the queue, and therefore no data packets can be temporarily stored in the \
    queue. There is no delay when a packet enters or leaves the queue. This queue participates in outbound scheduling as a level-1 queue.
    direction:
        description:
            - Direction of a virtual queue. The value can be inbound or outbound.
        required: true
        default: null
        choices=['inbound', 'outbound', 'all']

    cir:
        description:
            - CIR. It must be smaller than the interface bandwidth.
            The value is an integer ranging from 0 to 4294967294.
        required: true
        default: null

    cirPercent:
        description:
            - CIR percentage of an SQ.
            The value is an integer ranging from 0 to 100.
        required: true
        default: null

    cbs:
        description:
            - Committed burst size.
            The value is an integer ranging from 1 to 4194304.
        required: true
        default: null

    pir:
        description:
            - PIR. It must be smaller than the interface bandwidth.
            The value is an integer ranging from 0 to 4294967294.
        required: true
        default: null

    pirPercent:
        description:
            - PIR percentage of an SQ.
            The value is an integer ranging from 0 to 100.
        required: true
        default: null

    priorityLevelID:
        description:
            - Set the PIR priority of the user-queue to high.
        required: true
        default: null
        choices=['low', 'high']

    pbs:
        description:
            - Peak burst size.
            The value is an integer ranging from 1 to 4194304.
        required: true
        default: null

    flowQueueName:
        description:
            - Flow queue profile, which supports the eight-flow-queue mapping (BE/AF1/AF2/AF3/AF4/EF/CS6/CS7) profile, four-flow-queue mapping \
            (cos0/cos1/cos2/cos3) profile, and priority-mode flow queue profile.
        required: true
        default: null

    adjustOnCard:
        description:
            - Enable precise compensation on a subcard.
        required: true
        default: null
        choices=['enable', 'disable']

    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_profile_userqueue module test
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

  - name: Config user-queue cir 100 pir 200
    ne_qos_profile_userqueue:
      profileName: test
      cir: 100
      pir: 200
      direction: all
      operation: create
      provider: "{{ cli }}"

  - name: Undo user-queue cir 100 pir 200
    ne_qos_profile_userqueue:
      profileName: test
      cir: 100
      pir: 200
      direction: all
      operation: delete
      provider: "{{ cli }}"

  - name: Get user-queue queue configurations in qos-profile template test
    ne_qos_profile_userqueue:
      profileName: test
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
    sample: [
        {
            "cir": "1000",
            "direction": "outbound",
            "pir": "2000",
            "profileName": "test"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  [
        {
            "cir": "1000",
            "direction": "outbound",
            "pir": "2000",
            "profileName": "test"
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
        <hqosProfiles>
            <hqosProfile>
                <profileName>%s</profileName>
                <hqosUserQueues>
                    <hqosUserQueue>
"""

MERGE_CLASS_TAIL = """
                    </hqosUserQueue>
                </hqosUserQueues>
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
                <hqosUserQueues>
                    <hqosUserQueue/>
                </hqosUserQueues>
            </hqosProfile>
        </hqosProfiles>
    </hqos>
</qos>
</filter>
"""


class QosProfileSQCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.profileName = self.module.params['profileName']
        self.direction = self.module.params['direction']
        self.cir = self.module.params['cir']
        self.cirPercent = self.module.params['cirPercent']
        self.cbs = self.module.params['cbs']
        self.pir = self.module.params['pir']
        self.pirPercent = self.module.params['pirPercent']
        self.priorityLevelID = self.module.params['priorityLevelID']
        self.pbs = self.module.params['pbs']
        self.flowQueueName = self.module.params['flowQueueName']
        self.adjustOnCard = self.module.params['adjustOnCard']
        self.carMode = self.module.params['carMode']
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
            msg_para += " profileName"
        if self.operation != "getconfig":
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
        if self.direction:
            conf_str = constr_leaf_value(conf_str, 'direction', self.direction)
        if self.cir:
            conf_str = constr_leaf_value(conf_str, 'cir', self.cir)
        if self.cirPercent:
            conf_str = constr_leaf_value(
                conf_str, 'cirPercent', self.cirPercent)
        if self.cbs:
            conf_str = constr_leaf_value(conf_str, 'cbs', self.cbs)
        if self.pir:
            conf_str = constr_leaf_value(conf_str, 'pir', self.pir)
        if self.pirPercent:
            conf_str = constr_leaf_value(
                conf_str, 'pirPercent', self.pirPercent)
        if self.priorityLevelID:
            conf_str = constr_leaf_value(
                conf_str, 'priorityLevelID', self.priorityLevelID)
        if self.pbs:
            conf_str = constr_leaf_value(conf_str, 'pbs', self.pbs)
        if self.flowQueueName:
            conf_str = constr_leaf_value(
                conf_str, 'flowQueueName', self.flowQueueName)
        if self.adjustOnCard:
            conf_str = constr_leaf_value(
                conf_str, 'adjustOnCard', self.adjustOnCard)
        if self.carMode:
            conf_str = constr_leaf_value(conf_str, 'carMode', self.carMode)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<hqosUserQueue>',
                '<hqosUserQueue xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_profilesq(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_profilesq(self):

        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS % self.profileName
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return output_msg_list
        else:
            print('66666', xml_str)
            xml_str_split = re.split('</hqosUserQueue>', xml_str)
            print('77777', xml_str_split)

            for j in range(len(xml_str_split)):
                find_direction = re.findall(
                    r'.*<direction>(.*)</direction>.*\s*', xml_str_split[j])
                find_cir = re.findall(
                    r'.*<cir>(.*)</cir>.*\s*', xml_str_split[j])
                find_cirPercent = re.findall(
                    r'.*<cirPercent>(.*)</cirPercent>.*\s*', xml_str_split[j])
                find_cbs = re.findall(
                    r'.*<cbs>(.*)</cbs>.*\s*', xml_str_split[j])
                find_pir = re.findall(
                    r'.*<pir>(.*)</pir>.*\s*', xml_str_split[j])
                find_pirPercent = re.findall(
                    r'.*<pirPercent>(.*)</pirPercent>.*\s*', xml_str_split[j])
                find_priorityLevelID = re.findall(
                    r'.*<priorityLevelID>(.*)</priorityLevelID>.*\s*', xml_str_split[j])
                find_pbs = re.findall(
                    r'.*<pbs>(.*)</pbs>.*\s*', xml_str_split[j])
                find_flowQueueName = re.findall(
                    r'.*<flowQueueName>(.*)</flowQueueName>.*\s*', xml_str_split[j])
                find_adjustOnCard = re.findall(
                    r'.*<adjustOnCard>(.*)</adjustOnCard>.*\s*', xml_str_split[j])
                find_carMode = re.findall(
                    r'.*<carMode>(.*)</carMode>.*\s*', xml_str_split[j])

                if find_direction:
                    attr = dict()
                    attr['direction'] = find_direction[0]
                    attr['profileName'] = self.profileName
                    if find_cir:
                        attr['cir'] = find_cir[0]
                    if find_cirPercent:
                        attr['cirPercent'] = find_cirPercent[0]
                    if find_cbs:
                        attr['cbs'] = find_cbs[0]
                    if find_pir:
                        attr['pir'] = find_pir[0]
                    if find_pirPercent:
                        attr['pirPercent'] = find_pirPercent[0]
                    if find_priorityLevelID:
                        attr['priorityLevelID'] = find_priorityLevelID[0]
                    if find_pbs:
                        attr['pbs'] = find_pbs[0]
                    if find_flowQueueName:
                        attr['flowQueueName'] = find_flowQueueName[0]
                    if find_adjustOnCard:
                        attr['adjustOnCard'] = find_adjustOnCard[0]
                    if find_carMode:
                        attr['carMode'] = find_carMode[0]
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_profilesq(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.profileName:
            self.proposed["profileName"] = self.profileName
        if self.direction:
            self.proposed["direction"] = self.direction
        if self.cir:
            self.proposed["cir"] = self.cir
        if self.cirPercent:
            self.proposed["cirPercent"] = self.cirPercent
        if self.cbs:
            self.proposed["cbs"] = self.cbs
        if self.pir:
            self.proposed["pir"] = self.pir
        if self.pirPercent:
            self.proposed["pirPercent"] = self.pirPercent
        if self.priorityLevelID:
            self.proposed["priorityLevelID"] = self.priorityLevelID
        if self.pbs:
            self.proposed["pbs"] = self.pbs
        if self.flowQueueName:
            self.proposed["flowQueueName"] = self.flowQueueName
        if self.adjustOnCard:
            self.proposed["adjustOnCard"] = self.adjustOnCard
        if self.carMode:
            self.proposed["carMode"] = self.carMode
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        profilesqcfg_attr_exist = self.get_profilesq()
        if profilesqcfg_attr_exist:
            self.results["existing"] = profilesqcfg_attr_exist

        if self.operation == 'create':
            self.merge_profilesq()

        if self.operation == 'delete':
            self.undo_profilesq()

        profilesqcfg_attr_end_state = self.get_profilesq()
        if profilesqcfg_attr_end_state:
            self.results["end_state"] = profilesqcfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        profileName=dict(required=False, type='str'),
        direction=dict(required=False, choices=['inbound', 'outbound', 'all']),
        cir=dict(required=False, type='str'),
        cirPercent=dict(required=False, type='str'),
        cbs=dict(required=False, type='str'),
        pir=dict(required=False, type='str'),
        pirPercent=dict(required=False, type='str'),
        priorityLevelID=dict(required=False, choices=['low', 'high']),
        pbs=dict(required=False, type='str'),
        flowQueueName=dict(required=False, type='str'),
        adjustOnCard=dict(required=False, choices=['enable', 'disable']),
        carMode=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosProfileSQCfg = QosProfileSQCfg(argument_spec)
    NEWQosProfileSQCfg.work()


if __name__ == '__main__':
    main()
