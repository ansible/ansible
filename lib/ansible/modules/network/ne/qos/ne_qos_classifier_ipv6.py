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
module: ne_qos_classifier_ipv6.py
version_added: "2.6"
short_description:  IPv6 ACL rule.
description:
    - IPv6 ACL rule.
options:
    classifierName:
        description:
            - Name of a traffic classifier profile.
              The value is a string of 1 to 127 characters.
        required: true
        default: null
    aclName:
        description:
            - ID or name of an IPv6 ACL template.
              The value is a string of 1 to 64 characters.
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
- name: NetEngine ne_qos_classifier_ipv6 module test
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


  - name: Config IPv6 ACL rule.
    ne_qos_classifier_ipv6:
      classifierName: test
      aclName:3000
      operation: create
      provider: "{{ cli }}"

  - name: Undo IPv6 ACL rule.
    ne_qos_classifier_ipv6:
      classifierName: test
      aclName:3000
      provider: "{{ cli }}"


  - name: Get IPv6 ACL rules in classifier test.
    ne_qos_classifier_ipv6:
      classifierName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "classifierName": "test",
        "operation": "getconfig"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "aclName": "3000",
            "classifierName": "test"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  [
        {
            "aclName": "3000",
            "classifierName": "test"
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
    <qosCbQos>
        <qosClassifiers>
            <qosClassifier>
                <classifierName>%s</classifierName>
                <operator>%s</operator>
                <qosRuleAcl6s>
                    <qosRuleAcl6>
"""

MERGE_CLASS_TAIL = """
                    </qosRuleAcl6>
                </qosRuleAcl6s>
            </qosClassifier>
        </qosClassifiers>
    </qosCbQos>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosClassifiers>
            <qosClassifier>
                <classifierName>%s</classifierName>
                <qosRuleAcl6s>
                    <qosRuleAcl6/>
                </qosRuleAcl6s>
            </qosClassifier>
        </qosClassifiers>
    </qosCbQos>
</qos>
</filter>
"""


class QosClsIpv6Cfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.classifierName = self.module.params['classifierName']
        self.aclName = self.module.params['aclName']
        self.operation = self.module.params['operation']
        self.operator = 'or'

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
        if not self.classifierName:
            msg_para += " qosClassifier"
        if self.operation != "getconfig":
            if not self.aclName:
                msg_para += " aclName"
        if msg_para:
            self.module.fail_json(
                msg='Error: Please input the necessary element includes%s.' % msg_para)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % (self.classifierName, self.operator)
        if self.aclName:
            conf_str = constr_leaf_value(conf_str, 'aclName', self.aclName)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qosRuleAcl6>', '<qosRuleAcl6 xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_clsipv6(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        print('rrrrr', recv_xml)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_clsipv6(self):
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS % self.classifierName
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return output_msg_list
        else:

            print('66666', xml_str)
            find_operator = re.findall(
                r'.*<operator>(.*)</operator>.*\s*', xml_str)
            if find_operator:
                self.operator = find_operator[0]
            xml_str_split = re.split('</qosRuleAcl6>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):

                find_aclName = re.findall(
                    r'.*<aclName>(.*)</aclName>.*\s*', xml_str_split[j])
                if find_aclName:
                    attr = dict()
                    attr['aclName'] = find_aclName[0]
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_clsipv6(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.classifierName:
            self.proposed["classifierName"] = self.classifierName
        if self.aclName:
            self.proposed["aclName"] = self.aclName
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        clsipv6cfg_attr_exist = self.get_clsipv6()
        if clsipv6cfg_attr_exist:
            self.results["existing"] = clsipv6cfg_attr_exist

        if self.operation == 'create':
            self.merge_clsipv6()

        if self.operation == 'delete':
            self.undo_clsipv6()

        clsipv6cfg_attr_end_state = self.get_clsipv6()
        if clsipv6cfg_attr_end_state:
            self.results["end_state"] = clsipv6cfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        classifierName=dict(required=False, type='str'),
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
    NEWQosClsIpv6Cfg = QosClsIpv6Cfg(argument_spec)
    NEWQosClsIpv6Cfg.work()


if __name__ == '__main__':
    main()
