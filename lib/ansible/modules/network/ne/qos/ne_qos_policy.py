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
module: ne_qos_policy
version_added: "2.6"
short_description: Manages traffic policy on HUAWEI NetEngine devices.
description:
    - Manages traffic policy on HUAWEI NetEngine devices.
options:
    policyName:
        description:
            - Name of traffic policy.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    step:
        description:
            - Step is the difference between the numbers of sub-policies in a
              policy when the priories are assigned to sub-policies.
              The value is an integer ranging from 1 to 20.
        required: false
        default: 1
    shareMode:
        description:
            - If the value is enable, set the attribute of a policy to shared.
              If the value is disable, set the attribute of a policy to unshared.
        default: enable
        choices=['disable', 'enable']
    description:
        description:
            - Specifies the use of the traffic policy.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    statFlag:
        description:
            - If the value is enable, statistics enable .
              If the value is disable, statistics disable.
        required: false
        default: disable
        choices: ['disable', 'enable']
    classifierName:
        description:
            - Name of traffic classifier.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    behaviorName:
        description:
            - Name of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    priority:
        description:
            - Specifies the precedence of a classifier.
              The value is an integer ranging from 1 to 5119.
        required: false
        default: 1
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_policy module test
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

  - name: Config traffic policy
    ne_policy:
      policyName: test
      step: 2
      operation: create
      provider: "{{ cli }}"

  - name: Undo traffic policy
    ne_policy:
      policyName: test
      operation: delete
      provider: "{{ cli }}"

  - name: Config classifier behavior
    ne_policy:
      policyName: test
      classifierName: 1
      behaviorName: 1
      priority: 6
      operation: create
      provider: "{{ cli }}"

  - name: Undo classifier behavior
    ne_policy:
      policyName: test
      classifierName: 1
      behaviorName: 1
      priority: 6
      operation: delete
      provider: "{{ cli }}"

  - name: Get all traffic policy configuration
    ne_policy:
      operation: getconfig
      provider: "{{ cli }}"

  - name: Get traffic policy test configuration
    ne_policy:
      policyName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
existing:
    description: k/v pairs of existing traffic policy
    returned: always
    type: dict
    sample: { "CBQOS": [ { "behaviorName": "1",
                           "classifierName": "1",
                           "priority": "1" } ],
              "policyName": "test",
              "shareMode": "enable",
              "statFlag": "disable",
              "step": "1"}
'''


MERGE_POLICY_HEALDER = """
  <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
        <qosCbQos>
          <qosPolicys>
            <qosPolicy>
              <policyName>%s</policyName>
"""
MERGE_DES = """
              <description>%s</description>
"""
MERGE_STEP = """
              <step>%s</step>
"""
MERGE_SHARE = """
              <shareMode>%s</shareMode>
"""
MERGE_STAT = """
              <statFlag>%s</statFlag>
"""

MERGE_POLICY_TAIL = """
            </qosPolicy>
          </qosPolicys>
        </qosCbQos>
      </qos>
    </config>
"""
Merge_CB = """
              <qosPolicyNodes>
                <qosPolicyNode>
                  <classifierName>%s</classifierName>
                  <behaviorName>%s</behaviorName>
                  <priority>%s</priority>
                </qosPolicyNode>
              </qosPolicyNodes>
"""

QOS_IFCAR_CFGGET = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosPolicys>
            <qosPolicy>
                <policyName>%s</policyName>
                <description></description>
                <step></step>
                <shareMode></shareMode>
                <statFlag></statFlag>
              <qosPolicyNodes>
                <qosPolicyNode>
                  <classifierName></classifierName>
                  <behaviorName></behaviorName>
                  <priority></priority>
                </qosPolicyNode>
              </qosPolicyNodes>
            </qosPolicy>
        </qosPolicys>
    </qosCbQos>
</qos>
</filter>
"""
DELETE_POLICY = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosPolicys>
            <qosPolicy xc:operation="delete">
                <policyName>%s</policyName>
            </qosPolicy>
        </qosPolicys>
    </qosCbQos>
</qos>
  </config>
"""

DELETE_CB = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosPolicys>
            <qosPolicy>
                <policyName>%s</policyName>
                <qosPolicyNodes>
                    <qosPolicyNode xc:operation="delete">
                        <classifierName>%s</classifierName>
                        <behaviorName>%s</behaviorName>
                    </qosPolicyNode>
                </qosPolicyNodes>
            </qosPolicy>
        </qosPolicys>
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
        self.policyName = self.module.params['policyName']
        self.step = self.module.params['step']
        self.shareMode = self.module.params['shareMode']
        self.description = self.module.params['description']
        self.statFlag = self.module.params['statFlag']
        self.classifierName = self.module.params['classifierName']
        self.behaviorName = self.module.params['behaviorName']
        self.priority = self.module.params['priority']
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

    def isint(self, x):
        try:
            x = int(x)
            return isinstance(x, int)
        except ValueError:
            return False

    def check_params(self):
        """Check all input params"""
        # check the necessary element for get/merge/query/delete

        # check the length of ifname  dengyu kong de shi hou " "
        if not self.policyName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes policyName.')
        if self.policyName:
            if len(self.policyName) > 127 or len(self.policyName) < 1:
                self.module.fail_json(
                    msg='Error: The length of the policyName is not in the range from 1 to 127.')
        if self.classifierName:
            if len(self.classifierName) > 127:
                self.module.fail_json(
                    msg='Error: The length of the classifierName is not in the range from 1 to 127.')
        if self.behaviorName:
            if len(self.behaviorName) > 127:
                self.module.fail_json(
                    msg='Error: The length of the behaviorName is not in the range from 1 to 127.')
        if self.description:
            if len(self.description) > 127:
                self.module.fail_json(
                    msg='Error: The length of the description is not in the range from 1 to 127.')
        if self.step:
            if not self.isint(self.step):
                self.module.fail_json(
                    msg="Error: Step value is not digit.")

            if int(self.step) < 1 or int(self.step) > 20:
                self.module.fail_json(
                    msg='Error: Step value is not in the range from 1 to 20.')
        if self.priority:
            if not self.isint(self.priority):
                self.module.fail_json(
                    msg="Error: Priority value is not digit.")

            if int(self.priority) < 1 or int(self.priority) > 5119:
                self.module.fail_json(
                    msg='Error: Priority value is not in the range from 1 to 5119.')

        if ((self.classifierName and (not self.behaviorName)) or (self.behaviorName and (
                not self.classifierName))) and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: ClassifierName and behaviorName must be config at the same time.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def merge_ifcar(self):
        if not self.policyName:
            self.policyName = ' '
        if not self.priority:
            self.priority = ' '

        conf_str = None
        conf_str = MERGE_POLICY_HEALDER % (self.policyName)
        if self.description:
            conf_str += MERGE_DES % self.description
        if self.step:
            conf_str += MERGE_STEP % self.step
        if self.shareMode:
            conf_str += MERGE_SHARE % self.shareMode
        if self.statFlag:
            conf_str += MERGE_STAT % self.statFlag
        if self.classifierName:
            print('9999', self.classifierName)
            conf_str += Merge_CB % (self.classifierName,
                                    self.behaviorName, self.priority)
            if self.priority == ' ':
                print('23333', self.priority)
                conf_str = conf_str.replace('<priority> </priority>\n', '')
        conf_str += MERGE_POLICY_TAIL
        print('888888', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_ifcar(self, policyName):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        if not self.policyName:
            self.policyName = ' '
        conf_str = None
        conf_str = QOS_IFCAR_CFGGET % (self.policyName)
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return attr
        else:

            xml_str_split = re.split('</qosPolicy>', xml_str)
            print('66666', xml_str_split)
            for j in range(len(xml_str_split)):
                attr = dict()
                find_policyName = re.findall(
                    r'.*<policyName>(.*)</policyName>.*\s*', xml_str_split[j])
                find_step = re.findall(
                    r'.*<step>(.*)</step>.*\s*', xml_str_split[j])
                find_shareMode = re.findall(
                    r'.*<shareMode>(.*)</shareMode>.*\s*', xml_str_split[j])
                find_description = re.findall(
                    r'.*<description>(.*)</description>.*\s*', xml_str_split[j])
                find_statFlag = re.findall(
                    r'.*<statFlag>(.*)</statFlag>.*\s*', xml_str_split[j])
                find_classifierName = re.findall(
                    r'.*<classifierName>(.*)</classifierName>.*\s*', xml_str_split[j])
                find_behaviorName = re.findall(
                    r'.*<behaviorName>(.*)</behaviorName>.*\s*', xml_str_split[j])
                find_priority = re.findall(
                    r'.*<priority>(.*)</priority>.*\s*', xml_str_split[j])
                if find_policyName:
                    attr['policyName'] = find_policyName[0]
                    if find_step:
                        attr['step'] = find_step[0]
                    if find_shareMode:
                        attr['shareMode'] = find_shareMode[0]
                    if find_description:
                        attr['description'] = find_description[0]
                    if find_statFlag:
                        attr['statFlag'] = find_statFlag[0]

                    tcplist = list()
                    for i in range(len(find_classifierName)):
                        tcp = dict()
                        tcp['classifierName'] = find_classifierName[i]
                        tcp['behaviorName'] = find_behaviorName[i]
                        if find_priority:
                            tcp['priority'] = find_priority[i]

                        tcplist.append(tcp)
                    if tcplist:
                        attr['CBQOS'] = tcplist
                        print("999999", tcplist)

                    output_msg_list.append(attr)

        return output_msg_list

    def undo_ifcar(self):

        conf_str = None
        if self.classifierName:
            conf_str = DELETE_CB % (
                self.policyName, self.classifierName, self.behaviorName)

            recv_xml = set_nc_config(self.module, conf_str)
            self.check_response(recv_xml, "CFG_IFCAR")
        else:
            conf_str = DELETE_POLICY % (self.policyName)

            recv_xml = set_nc_config(self.module, conf_str)
            self.check_response(recv_xml, "CFG_IFCAR")
        # self.changed = True

    def get_proposed(self):

        if self.policyName:
            self.proposed["policyName"] = self.policyName
        if self.step:
            self.proposed["step"] = self.step
        if self.shareMode:
            self.proposed["shareMode"] = self.shareMode
        if self.description:
            self.proposed["description"] = self.description
        if self.statFlag:
            self.proposed["statFlag"] = self.statFlag
        if self.classifierName:
            self.proposed["classifierName"] = self.classifierName
        if self.behaviorName:
            self.proposed["behaviorName"] = self.behaviorName
        if self.priority:
            self.proposed["priority"] = self.priority
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
        ifcarcfg_attr_exist = self.get_ifcar(self.policyName)
        if ifcarcfg_attr_exist:
            self.results["existing"] = ifcarcfg_attr_exist

        if self.operation == 'create':
            self.merge_ifcar()

        if self.operation == 'delete':
            self.undo_ifcar()

        ifcarcfg_attr_end_stat = self.get_ifcar(self.policyName)
        if ifcarcfg_attr_end_stat:
            self.results["end_stat"] = ifcarcfg_attr_end_stat

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        policyName=dict(required=False, type='str'),
        step=dict(required=False, type='str'),
        shareMode=dict(required=False, choices=['disable', 'enable']),
        description=dict(required=False, type='str'),
        statFlag=dict(required=False, choices=['disable', 'enable']),
        classifierName=dict(required=False, type='str'),
        behaviorName=dict(required=False, type='str'),
        priority=dict(required=False, type='str'),
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
