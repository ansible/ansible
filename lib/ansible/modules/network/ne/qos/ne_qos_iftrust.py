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
module: ne_qos_iftrust
version_added: "2.6"
short_description: Trusted DS domain or 802.1p.
description:
    - Trusted DS domain or 802.1p.
options:
    ifName:
        description:
            - Name of the interface on which the QoS service is configured.
            The value is a string of characters.
        required: true
        default: null
    trustType:
        description:
            - Trust DS domain, 8021p, or full trust.
        required: true
        default: null
        choices=['8021p', 'ds', 'inner-8021p', 'outer-8021p']
    directType:
        description:
            - Incoming or outgoing traffic.
        required: true
        default: null
        choices=['inbound', 'outbound', 'in-outbound']
    vlanMode:
        description:
            - Specify a VLAN ID for BA classification. BA classification takes effect only on the specified VLAN.
        required: false
        default: null
        choices=['true', 'false']
    groupId:
        description:
            - Specify a VLAN ID for BA classification. BA classification takes effect only on the specified VLAN.
            The value is an integer ranging from 0 to 4294967295.
        required: false
        default: null
    dsName:
        description:
            - DS domain name when the trusted DS domain is selected.
        required: true
        default: null
    vlanId:
        description:
            - VLAN ID specified when behavior aggregate (BA) classification is configured.
            Range of VLANs such as C(2-10) or C(2,5,10-15), etc.
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
- name: NetEngine ne_qos_iftrust module test
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

  - name: Config trust
    ne_qos_iftrust:
      ifName: GigabitEthernet1/0/0
      trustType: ds
      dsName: default
      directionType: in-outbound
      operation: create
      provider: "{{ cli }}"

  - name: Undo trust
    ne_qos_iftrust:
      ifName: GigabitEthernet1/0/0
      trustType: ds
      dsName: default
      directionType: in-outbound
      operation: delete
      provider: "{{ cli }}"

  - name: Get get trust configurations in interface 1/0/0
    ne_qos_iftrust:
      ifName: GigabitEthernet1/0/0
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "ifName": "GigabitEthernet1/0/0",
        "operation": "getconfig"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: [
        {
            "directType": "in-outbound",
            "dsName": "default",
            "groupId": "0",
            "ifName": "GigabitEthernet1/0/0",
            "trustType": "ds",
            "vlanMode": "false"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: [
        {
            "directType": "in-outbound",
            "dsName": "default",
            "groupId": "0",
            "ifName": "GigabitEthernet1/0/0",
            "trustType": "ds",
            "vlanMode": "false"
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
    <qosIfQoss>
        <qosIfQos>
            <ifName>%s</ifName>
            <qosIfTrusts>
                <qosIfTrust>
"""

MERGE_CLASS_TAIL = """
                </qosIfTrust>
            </qosIfTrusts>
        </qosIfQos>
    </qosIfQoss>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
        <qosIfQos>
            <ifName>%s</ifName>
            <qosIfTrusts>
                <qosIfTrust/>
            </qosIfTrusts>
        </qosIfQos>
    </qosIfQoss>
</qos>
</filter>
"""


class QosIfTrustCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.ifName = self.module.params['ifName']
        self.trustType = self.module.params['trustType']
        self.directType = self.module.params['directType']
        self.vlanMode = self.module.params['vlanMode']
        self.groupId = self.module.params['groupId']
        self.dsName = self.module.params['dsName']
        self.vpnMode = self.module.params['vpnMode']
        self.vlanId = self.module.params['vlanId']
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
        if not self.ifName:
            msg_para += " ifName"
        if self.operation != "getconfig":
            if not self.trustType:
                msg_para += " trustType"
            if not self.directType:
                msg_para += " directType"
        if msg_para:
            self.module.fail_json(
                msg='Error: Please input the necessary element includes%s.' % msg_para)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None

        conf_str = MERGE_CLASS_HEALDER % self.ifName
        if self.trustType:
            conf_str = constr_leaf_value(conf_str, 'trustType', self.trustType)
        if self.directType:
            conf_str = constr_leaf_value(
                conf_str, 'directType', self.directType)
        if self.vlanId:
            conf_str = constr_leaf_value(conf_str, 'vlanId', self.vlanId)
            self.vlanMode = 'true'
        else:
            self.vlanMode = 'false'
        conf_str = constr_leaf_value(conf_str, 'vlanMode', self.vlanMode)
        conf_str = constr_leaf_value(conf_str, 'groupId', self.groupId or '0')
        if self.dsName:
            conf_str = constr_leaf_value(conf_str, 'dsName', self.dsName)
        if self.vpnMode:
            conf_str = constr_leaf_value(conf_str, 'vpnMode', self.vpnMode)

        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qosIfTrust>', '<qosIfTrust xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_iftrust(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_iftrust(self):

        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS % self.ifName
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return output_msg_list
        else:
            print('66666', xml_str)
            xml_str_split = re.split('</hqosUserQueue>', xml_str)
            print('77777', xml_str_split)

            for j in range(len(xml_str_split)):
                find_trustType = re.findall(
                    r'.*<trustType>(.*)</trustType>.*\s*', xml_str_split[j])
                find_directType = re.findall(
                    r'.*<directType>(.*)</directType>.*\s*', xml_str_split[j])
                find_vlanMode = re.findall(
                    r'.*<vlanMode>(.*)</vlanMode>.*\s*', xml_str_split[j])
                find_groupId = re.findall(
                    r'.*<groupId>(.*)</groupId>.*\s*', xml_str_split[j])
                find_dsName = re.findall(
                    r'.*<dsName>(.*)</dsName>.*\s*', xml_str_split[j])
                find_vpnMode = re.findall(
                    r'.*<vpnMode>(.*)</vpnMode>.*\s*', xml_str_split[j])
                find_vlanId = re.findall(
                    r'.*<vlanId>(.*)</vlanId>.*\s*', xml_str_split[j])

                if find_trustType:
                    attr = dict()
                    attr['trustType'] = find_trustType[0]
                    attr['ifName'] = self.ifName
                    if find_trustType:
                        attr['trustType'] = find_trustType[0]
                    if find_directType:
                        attr['directType'] = find_directType[0]
                    if find_vlanMode:
                        attr['vlanMode'] = find_vlanMode[0]
                    if find_groupId:
                        attr['groupId'] = find_groupId[0]
                        self.groupId = find_groupId[0]
                    if find_dsName:
                        attr['dsName'] = find_dsName[0]
                    if find_vpnMode:
                        attr['vpnMode'] = find_vpnMode[0]
                    if find_vlanId:
                        attr['vlanId'] = find_vlanId[0]

                    output_msg_list.append(attr)

        return output_msg_list

    def undo_iftrust(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.ifName:
            self.proposed["ifName"] = self.ifName
        if self.trustType:
            self.proposed["trustType"] = self.trustType
        if self.directType:
            self.proposed["directType"] = self.directType
        if self.dsName:
            self.proposed["dsName"] = self.dsName
        if self.vpnMode:
            self.proposed["vpnMode"] = self.vpnMode
        if self.vlanId:
            self.proposed["vlanId"] = self.vlanId

        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        iftrustcfg_attr_exist = self.get_iftrust()
        if iftrustcfg_attr_exist:
            self.results["existing"] = iftrustcfg_attr_exist

        if self.operation == 'create':
            self.merge_iftrust()

        if self.operation == 'delete':
            self.undo_iftrust()

        iftrustcfg_attr_end_state = self.get_iftrust()
        if iftrustcfg_attr_end_state:
            self.results["end_state"] = iftrustcfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        ifName=dict(required=False, type='str'),
        trustType=dict(
            required=False,
            choices=[
                '8021p',
                'ds',
                'inner-8021p',
                'outer-8021p']),
        directType=dict(
            required=False,
            choices=[
                'inbound',
                'outbound',
                'in-outbound']),
        dsName=dict(required=False, type='str'),
        groupId=dict(required=False, type='str'),
        vlanMode=dict(required=False, choices=['true', 'false']),
        vpnMode=dict(required=False, choices=['true', 'false']),
        vlanId=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosIfTrustCfg = QosIfTrustCfg(argument_spec)
    NEWQosIfTrustCfg.work()


if __name__ == '__main__':
    main()
