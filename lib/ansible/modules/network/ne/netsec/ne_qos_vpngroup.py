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
module: ne_qos_vpngroup
version_added: "2.6"
short_description: Manages vrfName action of traffic behavior on HUAWEI NetEngine devices.
description:
    - Manages vrfName action of traffic behavior on HUAWEI NetEngine devices.
author:Pangaoping
options:
    vpnGroupName:
        description:
            - Name of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    description
        description:
            - Description information of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    vrfName:
        description:
            - Name of a VPN-Instance group.
              If the value is permit, allow the packets that meet the rules to pass through the device.
              If the value is deny, prohibit the packets that meet the rules from passing through the device.
        required: false
        default: null

    operation:
        description:
            - If the value is getconfig, when specify the vpnGroupName, query the configuration of the vpnGroupName, otherwise query all behavior.
        required: false
        default: create
        choices: ['create', 'merge', 'delete', 'getconfig']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_vpngroup module test
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

  - name: Create vrfName
    ne_qos_vpngroup:
      vpnGroupName: "test"
      vrfName: "pgp"
      operation: create
      provider: "{{ cli }}"

  - name: Get all traffic behavior configuration
    ne_qos_vpngroup:
      operation: getconfig
      provider: "{{ cli }}"

  - name: Get traffic behavior test configuration
    ne_qos_vpngroup:
      vpnGroupName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
existing:
    description: k/v pairs of existing traffic behavior
    returned: always
    type: dict
    sample: { "vpnGroupName": "test", "vrfName": "pgp" }
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosVpnGroups>
            <qosVpnGroup>
                <vpnGroupName>%s</vpnGroupName>
                <qosVpnInstances>
"""

MERGE_URPF = """
                <qosVpnInstance>
                    <vrfName>%s</vrfName>
                </qosVpnInstance>
"""
MERGE_CLASS_TAIL = """
                </qosVpnInstances>
            </qosVpnGroup>
        </qosVpnGroups>
    </qosCbQos>
</qos>
</config>
"""


QOS_IFCAR_CFGGET = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosVpnGroups>
            <qosVpnGroup>
                <vpnGroupName>%s</vpnGroupName>
                <qosVpnInstances>

                </qosVpnInstances>
            </qosVpnGroup>
        </qosVpnGroups>
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
        self.vpnGroupName = self.module.params['vpnGroupName']
        self.vrfName = self.module.params['vrfName']

        self.operation = self.module.params['operation']
        print('initconf_str00000000000000', self.vpnGroupName)
        # states
        self.changed = False
        self.results = dict()
        self.results["end_state"] = []
        self.proposed = dict()

    def init_module(self):
        """
        init ansilbe NetworkModule.
        """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        if not self.vpnGroupName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes vpnGroupName.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None

        conf_str = MERGE_CLASS_HEALDER % (self.vpnGroupName)
        print('self.vrfName', self.vrfName)
        str = self.vrfName
        if self.vrfName:
            str = eval(str)
            print('str', str)

        if self.vrfName:
            for i in str:
                print('fruits', i)
                conf_str += MERGE_URPF % (i)
        print('conf_str11', conf_str)

        if self.operation == 'delete':
            if self.vrfName:
                # global conf_str
                conf_str = conf_str.replace(
                    '<qosVpnInstance>', '<qosVpnInstance xc:operation="delete">')
                print('conf_str22', conf_str)
                # return err,'22222222222222'

            else:
                conf_str = conf_str.replace(
                    '<qosVpnGroup>', '<qosVpnGroup xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('conf_str88888', conf_str)
        return conf_str

    def merge_ifcar(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "MERGE_PROCESS")

        self.changed = True

    def get_ifcar(self):
        attr = dict()
        output_msg_list = list()

        if not self.vpnGroupName:
            self.vpnGroupName = ' '
        conf_str = None
        conf_str = QOS_IFCAR_CFGGET % (self.vpnGroupName)
        print('conf_str11111', conf_str)

        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str11111111111', xml_str)

        if "<data/>" in xml_str:
            return attr
        else:

            # print('66666', xml_str)
            xml_str_split = re.split('</qosVpnGroup>', xml_str)
            print('xml_str_split66666', xml_str_split)
            print('len66666', len(xml_str_split))

            for i in range(len(xml_str_split)):
                attr = dict()
                print('len1111', xml_str_split[i])

                find_vpnGroupName = re.findall(
                    r'.*<vpnGroupName>(.*)</vpnGroupName>.*\s*', xml_str_split[i])
                print('find_vpnGroupNamelen11111', find_vpnGroupName)
                find_vrfNames = re.findall(
                    r'.*<vrfName>(.*)</vrfName>.*\s*', xml_str_split[i])
                print('find_vrfNameslen11111', find_vrfNames)
                # ('find_vrfNameslen11111', ['pgp'])\n('find_vrfNameslen11111', ['vpn1', 'vpn2']
                print('find_vrfNamelen66666', len(find_vrfNames))
                if find_vpnGroupName:
                    attr['vpnGroupName'] = find_vpnGroupName[0]
                    print('9999999', find_vpnGroupName[0])
                    output_msg = list()
                    if find_vrfNames:
                        for find_vrfName in find_vrfNames:
                            output_msg.append(find_vrfName)
                            print('8888888', output_msg)

                    attr['vrfName'] = output_msg
                    # print('8888888', find_vrfName)
                    # return err,'22222222222222'
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_ifcar(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        print('recv_xml2222222222222', recv_xml)

        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

    def get_proposed(self):
        """get proposed info"""
        if self.vpnGroupName is not None:
            self.proposed["vpnGroupName"] = self.vpnGroupName
        if self.vrfName is not None:
            self.proposed["vrfName"] = self.vrfName

        self.proposed["operation"] = self.operation

    def work(self):
        """worker"""

        self.check_params()

        self.get_proposed()
        self.results['existing'] = self.get_ifcar()

        if self.operation == 'create' or self.operation == 'merge':
            self.merge_ifcar()

        if self.operation == 'delete':
            self.undo_ifcar()

        ifcarcfg_attr_exist = self.get_ifcar()
        if ifcarcfg_attr_exist:
            self.results["end_state"].append(ifcarcfg_attr_exist)

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        vpnGroupName=dict(required=False, type='str'),
        vrfName=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'merge',
                'getconfig',
                'delete'],
            default='merge'),
    )

    argument_spec.update(ne_argument_spec)
    NEWCQosIfCar = QosIfCarCfg(argument_spec)
    NEWCQosIfCar.work()


if __name__ == '__main__':
    main()
