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
module: ne_qos_globlepolicy
version_added: "2.6"
short_description:  The traffic policy is applied to the system view.
description:
    - The traffic policy is applied to the system view.
options:
    direction:
        description:
            - Incoming or outgoing traffic.
        required: true
        default: null
        choices=['inbound', 'outbound']
    policyName:
        description:
            - Name of a traffic policy.
        required: true
        default: null
    uclType:
        description:
            - Type of the traffic policy applied in the system view. The value can be UCL or DAA.
        required: true
        default: null
        choices=['UCL', 'ACL']
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_globlepolicy module test
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


  - name: Config global traffic policy
    ne_qos_globlepolicy:
      policyName: test
      direction: outbound
      uclType: UCL
      operation: create
      provider: "{{ cli }}"

  - name: Undo global traffic policy
    ne_qos_globlepolicy:
      policyName: test
      direction: outbound
      uclType: UCL
      operation: delete
      provider: "{{ cli }}"


  - name: Get all global traffic policy configuration
    ne_qos_globlepolicy:
      operation: getconfig
      provider: "{{ cli }}"

'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "operation": "getconfig"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "direction": "outbound",
            "policyName": "test",
            "uclType": "UCL"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:   [
        {
            "direction": "outbound",
            "policyName": "test",
            "uclType": "UCL"
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
    <qosGlobalPolicys>
        <qosGlobalPolicy>
"""

MERGE_CLASS_TAIL = """
        </qosGlobalPolicy>
    </qosGlobalPolicys>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosGlobalPolicys>
        <qosGlobalPolicy/>
    </qosGlobalPolicys>
</qos>
</filter>
"""


class QosGloblePolicy(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.direction = self.module.params['direction']
        self.policyName = self.module.params['policyName']
        self.uclType = self.module.params['uclType']
        self.upId = self.module.params['upId']

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
        if self.operation != "getconfig":
            if not self.direction:
                msg_para += " direction"
            if not self.policyName:
                msg_para += " policyName"
            if not self.uclType:
                msg_para += " uclType"
        if msg_para:
            self.module.fail_json(
                msg='Error: Please input the necessary element includes%s.' % msg_para)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER
        conf_str = constr_leaf_value(conf_str, 'direction', self.direction)
        conf_str = constr_leaf_value(conf_str, 'policyName', self.policyName)
        conf_str = constr_leaf_value(conf_str, 'uclType', self.uclType)
        if self.upId:
            conf_str = constr_leaf_value(conf_str, 'upId', self.upId)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qosGlobalPolicy>',
                '<qosGlobalPolicy xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_globlepolicy(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_globlepolicy(self):
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return output_msg_list
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</qosGlobalPolicy>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):

                find_direction = re.findall(
                    r'.*<direction>(.*)</direction>.*\s*', xml_str_split[j])
                find_policyName = re.findall(
                    r'.*<policyName>(.*)</policyName>.*\s*', xml_str_split[j])
                find_uclType = re.findall(
                    r'.*<uclType>(.*)</uclType>.*\s*', xml_str_split[j])
                find_upId = re.findall(
                    r'.*<upId>(.*)</upId>.*\s*', xml_str_split[j])

                if find_policyName:
                    attr = dict()
                    attr['direction'] = find_direction[0]
                    attr['policyName'] = find_policyName[0]
                    attr['uclType'] = find_uclType[0]
                    if find_upId:
                        attr['upId'] = find_upId[0]

                    output_msg_list.append(attr)

        return output_msg_list

    def undo_globlepolicy(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.direction:
            self.proposed["direction"] = self.direction
        if self.policyName:
            self.proposed["policyName"] = self.policyName
        if self.uclType:
            self.proposed["uclType"] = self.uclType
        if self.upId:
            self.proposed["upId"] = self.upId
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        globlepolicycfg_attr_exist = self.get_globlepolicy()
        if globlepolicycfg_attr_exist:
            self.results["existing"] = globlepolicycfg_attr_exist

        if self.operation == 'create':
            self.merge_globlepolicy()

        if self.operation == 'delete':
            self.undo_globlepolicy()

        globlepolicycfg_attr_end_state = self.get_globlepolicy()
        if globlepolicycfg_attr_end_state:
            self.results["end_state"] = globlepolicycfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        direction=dict(required=False, choices=['inbound', 'outbound']),
        policyName=dict(required=False, type='str'),
        uclType=dict(required=False, choices=['UCL', 'ACL']),
        upId=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosGloblePolicy = QosGloblePolicy(argument_spec)
    NEWQosGloblePolicy.work()


if __name__ == '__main__':
    main()
