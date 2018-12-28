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
module: ne_qos_domain_trust
version_added: "2.6"
short_description:  Manages user priority of AAA domain on HUAWEI NetEngine devices.
description:
    - Manages user priority of AAA domain on HUAWEI NetEngine devices.
options:
    domainName:
        description:
            - domainName.
            The value is a string of 1 to 64 characters.
        required: true
        default: null
    direction:
        description:
            - Direction.
        required: true
        default: null
        choices=['upstream', 'downstream']
    trustType:
        description:
            - Trust type.
        required: true
        default: null
        choices=['trust-8021p-inner', 'trust-8021p-outer', 'trust-dscp-inner', 'trust-dscp-outer', 'trust-exp-inner', 'trust-exp-outer', 'unchangeable']
    priority:
        description:
            - Priority value.
            The value is an integer ranging from 0 to 7.
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
- name: NetEngine ne_qos_domain_trust module test
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


  - name: Config Domain User priority.
    ne_qos_domain_userprority:
      domainName: test
      direction: upstream
      trustType: trust-8021p-inner
      priority: 7
      operation: create
      provider: "{{ cli }}"

  - name: Undo Domain User priority.
    ne_qos_domain_userprority:
      domainName: test
      direction: upstream
      operation: delete
      provider: "{{ cli }}"

  - name: Get User priority configuration
    ne_qos_domain_userprority:
      domainName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "domainName": "test",
        "operation": "getconfig"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "direction": "upstream",
            "domainName": "test",
            "trustType": "trust-8021p-inner"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:   [
        {
            "direction": "upstream",
            "domainName": "test",
            "trustType": "trust-8021p-inner"
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
<brasqos xmlns="http://www.huawei.com/netconf/vrp/huawei-brasqos">
    <brDomainNodes>
        <brDomainNode>
            <domainName>%s</domainName>
            <qosUserPriNodes>
                <qosUserPriNode>
"""

MERGE_CLASS_TAIL = """
                </qosUserPriNode>
            </qosUserPriNodes>
        </brDomainNode>
    </brDomainNodes>
</brasqos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<brasqos xmlns="http://www.huawei.com/netconf/vrp/huawei-brasqos">
    <brDomainNodes>
        <brDomainNode>
            <domainName>%s</domainName>
            <qosUserPriNodes>
                <qosUserPriNode/>
            </qosUserPriNodes>
        </brDomainNode>
    </brDomainNodes>
</brasqos>
</filter>
"""


class QosDomainUserPriCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.domainName = self.module.params['domainName']
        self.direction = self.module.params['direction']
        self.trustType = self.module.params['trustType']
        self.priority = self.module.params['priority']

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
        if not self.domainName:
            msg_para += " domainName"
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

        conf_str = ""
        conf_str = MERGE_CLASS_HEALDER % self.domainName
        if self.direction:
            conf_str = constr_leaf_value(conf_str, 'direction', self.direction)
        if self.trustType:
            conf_str = constr_leaf_value(conf_str, 'trustType', self.trustType)
        if self.priority:
            conf_str = constr_leaf_value(conf_str, 'priority', self.priority)

        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qosUserPriNode>',
                '<qosUserPriNode xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_domainuserpri(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_domainuserpri(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS % self.domainName
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return attr
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</qosUserPriNode>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                find_direction = re.findall(
                    r'.*<direction>(.*)</direction>.*\s*', xml_str_split[j])
                find_trustType = re.findall(
                    r'.*<trustType>(.*)</trustType>.*\s*', xml_str_split[j])
                find_priority = re.findall(
                    r'.*<priority>(.*)</priority>.*\s*', xml_str_split[j])

                if find_direction:
                    attr = dict()
                    attr['direction'] = find_direction[0]
                    attr['domainName'] = self.domainName
                    if find_trustType:
                        attr['trustType'] = find_trustType[0]
                    if find_priority and find_priority[0] != '15':
                        attr['priority'] = find_priority[0]

                    output_msg_list.append(attr)

        return output_msg_list

    def undo_domainuserpri(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.domainName:
            self.proposed["domainName"] = self.domainName
        if self.direction:
            self.proposed["direction"] = self.direction
        if self.trustType:
            self.proposed["trustType"] = self.trustType
        if self.priority:
            self.proposed["priority"] = self.priority

        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        domainuserpricfg_attr_exist = self.get_domainuserpri()
        if domainuserpricfg_attr_exist:
            self.results["existing"] = domainuserpricfg_attr_exist

        if self.operation == 'create':
            self.merge_domainuserpri()

        if self.operation == 'delete':
            self.undo_domainuserpri()

        domainuserpricfg_attr_end_state = self.get_domainuserpri()
        if domainuserpricfg_attr_end_state:
            self.results["end_state"] = domainuserpricfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        domainName=dict(required=False, type='str'),
        direction=dict(required=False, choices=['upstream', 'downstream']),
        trustType=dict(
            required=False,
            choices=[
                'trust-8021p-inner',
                'trust-8021p-outer',
                'trust-dscp-inner',
                'trust-dscp-outer',
                'trust-exp-inner',
                'trust-exp-outer',
                'unchangeable']),
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
    NEWQosDomainUserPriCfg = QosDomainUserPriCfg(argument_spec)
    NEWQosDomainUserPriCfg.work()


if __name__ == '__main__':
    main()
