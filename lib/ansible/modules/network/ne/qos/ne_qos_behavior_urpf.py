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
module: ne_qos_behavior_urpf
version_added: "2.6"
short_description:  Manages urpf of traffic behavior on HUAWEI NetEngine devices.
description:
    - Manages urpf of trafffic behavior on HUAWEI NetEngine devices.
options:
    behaviorName:
        description:
            - Name of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    checkType
        description:
            - Enable URPF check in the traffic behavior view.
        required: false
        default: null
        choices=['strict', 'loose']
    allowDefault:
        description:
            - If allowDefault is enable, indicates the packets matching the default route are forwarded.
        required: false
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
- name: NetEngine ne_behavior_urpf module test
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
    ne_behavior_urpf:
      behaviorName: test
      operation: create
      provider: "{{ cli }}"

  - name: Config urpf
    ne_behavior_urpf:
      behaviorName: test
      checkType: loose
      allowDefault: enable
      operation: create
      provider: "{{ cli }}"

  - name: Undo traffic behavior
    ne_behavior_urpf:
      behaviorName: test
      operation: delete
      provider: "{{ cli }}"

  - name: Undo urpf
    ne_behavior_urpf:
      behaviorName: test
      checkType: loose
      allowDefault: enable
      operation: delete
      provider: "{{ cli }}"

  - name: Get all traffic behavior configuration
    ne_behavior_urpf:
      operation: getconfig
      provider: "{{ cli }}"

  - name: Get traffic behavior test configuration
    ne_behavior_urpf:
      behaviorName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
existing:
    description: k/v pairs of existing urpf of traffic behavior
    returned: always
    type: dict
    sample: { "behaviorName": "test", "checkType": "loose", "allowDefault": "enable" }
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosBehaviors>
            <qosBehavior>
                <behaviorName>%s</behaviorName>
"""

MERGE_URPF = """
                <qosActUrpfs>
                    <qosActUrpf>
                        <actionType>urpf</actionType>
                        <checkType>%s</checkType>
                        <allowDefault>%s</allowDefault>
                    </qosActUrpf>
                </qosActUrpfs>
"""
MERGE_CLASS_TAIL = """
            </qosBehavior>
        </qosBehaviors>
    </qosCbQos>
</qos>
</config>
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
                <qosActUrpfs>
                    <qosActUrpf>
                        <actionType></actionType>
                        <checkType></checkType>
                        <allowDefault></allowDefault>
                    </qosActUrpf>
                </qosActUrpfs>
            </qosBehavior>
        </qosBehaviors>
    </qosCbQos>
</qos>
</filter>
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
        self.checkType = self.module.params['checkType']
        self.allowDefault = self.module.params['allowDefault']
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
        if not (self.checkType and self.allowDefault) and (
                self.checkType or self.allowDefault):
            self.module.fail_json(
                msg='Error: CheckType and allowDefault must be config at the same time.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % (self.behaviorName)
        print('self.actionTypeggggg', self.checkType)
        if self.checkType:
            conf_str += MERGE_URPF % (self.checkType, self.allowDefault)
        if self.operation == 'delete':
            if self.checkType:
                # global conf_str
                conf_str = conf_str.replace(
                    '<qosActUrpf>', '<qosActUrpf xc:operation="delete">')
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
        output_msg = list()
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
                find_checkType = re.findall(
                    r'.*<checkType>(.*)</checkType>.*\s*', xml_str_split[j])
                find_allowDefault = re.findall(
                    r'.*<allowDefault>(.*)</allowDefault>.*\s*', xml_str_split[j])

                if find_behaviorName:
                    attr['behaviorName'] = find_behaviorName[0]

                    tcplist = list()
                    for i in range(len(find_checkType)):
                        tcp = dict()
                        tcp['checkType'] = find_checkType[i]
                        tcp['allowDefault'] = find_allowDefault[i]
                        tcplist.append(tcp)
                    if tcplist:
                        attr['URPF'] = tcplist
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
        if self.checkType:
            self.proposed["checkType"] = self.checkType
        if self.allowDefault:
            self.proposed["allowDefault"] = self.allowDefault
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

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
        checkType=dict(required=False, choices=['strict', 'loose']),
        allowDefault=dict(required=False, choices=['disable', 'enable']),
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
