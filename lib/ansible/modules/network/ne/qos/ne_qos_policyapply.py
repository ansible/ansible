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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action_yang, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import collections
import re
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ne_qos_policyapply
version_added: "2.6"
short_description: Manages traffic policy on interface on HUAWEI NetEngine devices.
description:
    - Manages traffic policy on interface on HUAWEI NetEngine devices.
options:
    ifname:
        description:
            - Name of interface.
              The value is a string of 1 to 31 characters.
        required: false
        default: null
    direction
        description:
            - Apply traffic policy to this interface direction.
        required: false
        default: null
        choices: ['inbound','outbound']
    groupId:
        description:
            - Vlan group id.
              When create with vlan, groupId is randomly assigned to uniquely identify a VLAN group,
              when delete or query_stastics or clear_stastics, groupId acts as
              an parameter to operate a VLAN group.
        required: false
        default: null
    peVlanId:
        description:
            - Specify a PE VLAN ID.
              The value is an integer ranging from 1 to 4094.
        required: false
        default: null
    vlanId:
        description:
            - Range of VLANs such as C(2-10) or C(2,5,10-15), etc.
              If specify peVlanId, vlanId specify CE VLAN ID(inner VLAN ID) range,
              otherwise vlanId specify a VLAN ID range.
        required: false
        default: null
    layer:
        description:
            - Classification based on Layer 2 information or Layer 3 information
              or MPLS packet header information.
        required: false
        default: null
        choices: ['none', 'link', 'mpls', 'all']
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete', 'query_stastics', 'clear_stastics']
'''

EXAMPLES = '''
- name: NetEngine ne_policyapply module test
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

  - name: Config traffic policy to an interface
    ne_policyapply:
      ifname: Eth-Trunk1
      policyName: 1
      direction: outbound
      groupId: 0
      vlanId: 1-3
      layer: none
      operation: create
      provider: "{{ cli }}"

  - name: Get configuration
    ne_policyapply:
      ifname: Eth-Trunk1
      operation: getconfig
      provider: "{{ cli }}"

  - name: Query traffic policy stastics
    ne_policyapply:
      ifname: Eth-Trunk1
      policyName: 1
      direction: outbound
      groupId: 0
      layer: none
      operation: query_stastics
      provider: "{{ cli }}"

  - name: Clear traffic policy stastics
    ne_policyapply:
      ifname: Eth-Trunk1
      direction: outbound
      groupId: 1
      operation: clear_stastics
      provider: "{{ cli }}"
'''

RETURN = '''
existing:
    description: k/v pairs of existing traffic policy on interface
    returned: always
    type: dict
    sample: { "direction": "outbound",
              "groupId": "1",
              "ifname": "Eth-Trunk1",
              "layer": "none",
              "policyName": "1",
              "vlanId": [ "1", "2", "3" ] }
'''


MERGE_POLICYAPPLY = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
        <qosIfQos xc:operation="merge">
            <ifName>%s</ifName>
            <qosPolicyApplys>
                <qosPolicyApply xc:operation="create">
                    <direction>%s</direction>
                    <policyName>%s</policyName>
                    <layer>%s</layer>
                    <vlanMode>%s</vlanMode>
                    <groupId>0</groupId>
                    <peVlanId>%s</peVlanId>
                    <vlanId>%s</vlanId>
                </qosPolicyApply>
            </qosPolicyApplys>
        </qosIfQos>
    </qosIfQoss>
</qos>
</config>
"""


QOS_IFCAR_CFGGET = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
        <qosIfQos>
            <ifName>%s</ifName>
            <qosPolicyApplys>
                <qosPolicyApply>
                    <direction></direction>
                    <policyName></policyName>
                    <layer></layer>
                    <vlanMode></vlanMode>
                    <groupId></groupId>
                    <peVlanId></peVlanId>
                    <vlanId></vlanId>
                </qosPolicyApply>
            </qosPolicyApplys>
        </qosIfQos>
    </qosIfQoss>
</qos>
</filter>
"""


DELETE_POLICYAPPLY = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
        <qosIfQos>
        <ifName>%s</ifName>
            <qosPolicyApplys>
                <qosPolicyApply xc:operation="delete">
                    <direction>%s</direction>
                    <policyName>%s</policyName>
                    <layer>%s</layer>
                    <vlanMode>%s</vlanMode>
                    <groupId>%s</groupId>
                </qosPolicyApply>
            </qosPolicyApplys>
        </qosIfQos>
    </qosIfQoss>
  </qos>
</config>
"""

QUERY_POLICY = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
        <qosIfQos>
            <ifName>%s</ifName>
            <qosPolicyApplys>
                <qosPolicyApply>
                    <direction>%s</direction>
                    <policyName>%s</policyName>
                    <layer>%s</layer>
                    <vlanMode>%s</vlanMode>
                    <groupId>%s</groupId>
                </qosPolicyApply>
            </qosPolicyApplys>
        </qosIfQos>
    </qosIfQoss>
</qos></filter>
"""
RESET_POLICY = """
    <qos:qosResetPolicyApply xmlns:qos="http://www.huawei.com/netconf/vrp/huawei-qos">
        <qos:direction>%s</qos:direction>
        <qos:ifName>%s</qos:ifName>
        <qos:groupId>%s</qos:groupId>
    </qos:qosResetPolicyApply>
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
        self.ifname = self.module.params['ifname']
        self.direction = self.module.params['direction']
        self.policyName = self.module.params['policyName']
        self.groupId = self.module.params['groupId']
        self.peVlanId = self.module.params['peVlanId']
        self.vlanId = self.module.params['vlanId']
        self.layer = self.module.params['layer']
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

        if (not self.ifname or not self.direction or not self.policyName or not self.groupId or
                not self.layer) and self.operation != 'getconfig' and self.operation != 'clear_stastics':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes ifname/groupId/direction/policyName/layer.')

        if (not self.ifname or not self.direction or not self.groupId) and self.operation == 'clear_stastics':
            self.module.fail_json(
                msg='Error: When clear, please input the necessary element includes ifname/groupId/direction.')

        if self.vlanId:
            vlan_list = self.vlanid_to_list(self.vlanId)
            self.vlanId = self.vlan_list_to_bitmap(vlan_list)
            self.vlanmap = self.bitmap_to_vlan_list(self.vlanId)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        self.vlanMode = 'true'
        if not self.peVlanId and not self.vlanId:
            self.vlanMode = 'false'
        if not self.vlanId:
            self.vlanId = ' '
        if not self.peVlanId:
            self.peVlanId = ' '

        conf_str = MERGE_POLICYAPPLY % (self.ifname,
                                        self.direction,
                                        self.policyName,
                                        self.layer,
                                        self.vlanMode,
                                        self.peVlanId,
                                        self.vlanId)

        if self.vlanId == ' ':
            conf_str = conf_str.replace("<vlanId> </vlanId>\n", '')
        if self.peVlanId == ' ':
            conf_str = conf_str.replace("<peVlanId> </peVlanId>\n", '')
        # if self.operation == 'delete':

        print('88888', conf_str)
        return conf_str

    def reset_policy(self):
        # get first
        conf_str = None
        conf_str = RESET_POLICY % (self.direction, self.ifname, self.groupId)
        print("233333", conf_str)
        recv_xml = execute_nc_action_yang(self.module, conf_str)
        self.check_response(recv_xml, "reset_policy")

    def vlan_series(self, vlanid_s):
        """ convert vlan range to list """

        vlan_list = []
        peerlistlen = len(vlanid_s)
        peerlistlen = len(vlanid_s)
        if peerlistlen != 2:
            self.module.fail_json(msg='Error: Format of vlanid is invalid.')
        for num in range(peerlistlen):
            if not vlanid_s[num].isdigit():
                self.module.fail_json(
                    msg='Error: Format of vlanid is invalid.')
        if int(vlanid_s[0]) > int(vlanid_s[1]):
            self.module.fail_json(msg='Error: Format of vlanid is invalid.')
        elif int(vlanid_s[0]) == int(vlanid_s[1]):
            vlan_list.append(str(vlanid_s[0]))
            return vlan_list
        for num in range(int(vlanid_s[0]), int(vlanid_s[1])):
            vlan_list.append(str(num))
        vlan_list.append(vlanid_s[1])

        return vlan_list

    def vlan_region(self, vlanid_list):
        """ convert vlan range to vlan list """

        vlan_list = []
        peerlistlen = len(vlanid_list)
        for num in range(peerlistlen):
            if vlanid_list[num].isdigit():
                vlan_list.append(vlanid_list[num])
            else:
                vlan_s = self.vlan_series(vlanid_list[num].split('-'))
                vlan_list.extend(vlan_s)

        return vlan_list

    def vlanid_to_list(self, vlanid):
        """ convert vlanid to vlan list """
        vlan_list = self.vlan_region(vlanid.split(','))

        return vlan_list

    def vlan_list_to_bitmap(self, vlanlist):
        """ convert vlan list to vlan bitmap """
        vlan_bit = ['0'] * 1024
        bit_int = [0] * 1024

        vlan_list_len = len(vlanlist)
        for num in range(vlan_list_len):
            tagged_vlans = int(vlanlist[num])
            if tagged_vlans <= 0 or tagged_vlans > 4094:
                self.module.fail_json(
                    msg='Error: Vlan id is not in the range from 1 to 4094.')
            j = tagged_vlans / 4
            bit_int[j] |= 0x8 >> (tagged_vlans % 4)
            vlan_bit[j] = hex(bit_int[j])[2].upper()

        vlan_xml = ''.join(vlan_bit)

        return vlan_xml

    def bitmap_to_vlan_list(self, bitmap):
        """convert VLAN bitmap to VLAN list"""
        tmp = list()
        if not bitmap:
            return tmp

        bit_len = len(bitmap)
        for i in range(bit_len):
            if bitmap[i] == "0":
                continue
            bit = int(bitmap[i], 16)
            if bit & 0x8:
                tmp.append(str(i * 4))
            if bit & 0x4:
                tmp.append(str(i * 4 + 1))
            if bit & 0x2:
                tmp.append(str(i * 4 + 2))
            if bit & 0x1:
                tmp.append(str(i * 4 + 3))
        # print("ggg", tmp)

        return tmp

    def get_data(self, xml_str):
        attr = dict()
        re_find = re.findall(r'.*<direction>(.*)</direction>.*\s*', xml_str)
        if re_find:
            attr['direction'] = re_find[0]
        re_find = re.findall(r'.*<policyName>(.*)</policyName>.*\s*', xml_str)
        if re_find:
            attr['policyName'] = re_find[0]
        re_find = re.findall(r'.*<layer>(.*)</layer>.*\s*', xml_str)
        if re_find:
            attr['layer'] = re_find[0]
        re_find = re.findall(r'.*<peVlanId>(.*)</peVlanId>.*\s*', xml_str)
        if re_find:
            attr['peVlanId'] = re_find[0]
        re_find = re.findall(r'.*<vlanId>(.*)</vlanId>.*\s*', xml_str)
        if re_find:
            attr['vlanId'] = self.bitmap_to_vlan_list(re_find[0])
        re_find = re.findall(r'.*<groupId>(.*)</groupId>.*\s*', xml_str)
        # if re_find and int(re_find[0])!=0 :
        if re_find:
            attr['groupId'] = re_find[0]

        return attr

    def get_query_data(self, xml_str):
        attr = dict()
        re_find = re.findall(r'.*<slotIdPath>(.*)</slotIdPath>.*\s*', xml_str)
        if re_find:
            attr['slotIdPath'] = re_find[0]
        re_find = re.findall(
            r'.*<statEnableTime>(.*)</statEnableTime>.*\s*', xml_str)
        if re_find:
            attr['statEnableTime'] = re_find[0]
        re_find = re.findall(
            r'.*<statClearTime>(.*)</statClearTime>.*\s*', xml_str)
        if re_find:
            attr['statClearTime'] = re_find[0]
        re_find = re.findall(
            r'.*<statClearFlag>(.*)</statClearFlag>.*\s*', xml_str)
        if re_find:
            attr['statClearFlag'] = re_find[0]
        re_find = re.findall(
            r'.*<matchPackets>(.*)</matchPackets>.*\s*', xml_str)
        if re_find:
            attr['matchPackets'] = re_find[0]
        re_find = re.findall(r'.*<matchBytes>(.*)</matchBytes>.*\s*', xml_str)
        # if re_find and int(re_find[0])!=0 :
        if re_find:
            attr['matchBytes'] = re_find[0]
        re_find = re.findall(
            r'.*<missPackets>(.*)</missPackets>.*\s*', xml_str)
        if re_find:
            attr['missPackets'] = re_find[0]
        re_find = re.findall(r'.*<missBytes>(.*)</missBytes>.*\s*', xml_str)
        if re_find:
            attr['missBytes'] = re_find[0]
        re_find = re.findall(
            r'.*<matchPassPkts>(.*)</matchPassPkts>.*\s*', xml_str)
        if re_find:
            attr['matchPassPkts'] = re_find[0]
        re_find = re.findall(
            r'.*<matchPassBytes>(.*)</matchPassBytes>.*\s*', xml_str)
        if re_find:
            attr['matchPassBytes'] = re_find[0]
        re_find = re.findall(
            r'.*<matchDropPkts>(.*)</matchDropPkts>.*\s*', xml_str)
        if re_find:
            attr['matchDropPkts'] = re_find[0]
        re_find = re.findall(
            r'.*<matchDropBytes>(.*)</matchDropBytes>.*\s*', xml_str)
        # if re_find and int(re_find[0])!=0 :
        if re_find:
            attr['matchDropBytes'] = re_find[0]
        re_find = re.findall(
            r'.*<missPktsRate>(.*)</missPktsRate>.*\s*', xml_str)
        if re_find:
            attr['missPktsRate'] = re_find[0]
        re_find = re.findall(
            r'.*<missBytesRate>(.*)</missBytesRate>.*\s*', xml_str)
        if re_find:
            attr['missBytesRate'] = re_find[0]
        re_find = re.findall(
            r'.*<matchPassPktsRate>(.*)</matchPassPktsRate>.*\s*', xml_str)
        if re_find:
            attr['matchPassPktsRate'] = re_find[0]
        re_find = re.findall(
            r'.*<matchPassBytesRate>(.*)</matchPassBytesRate>.*\s*', xml_str)
        if re_find:
            attr['matchPassBytesRate'] = re_find[0]
        re_find = re.findall(
            r'.*<matchDropPktsRate>(.*)</matchDropPktsRate>.*\s*', xml_str)
        if re_find:
            attr['matchDropPktsRate'] = re_find[0]
        re_find = re.findall(
            r'.*<matchDropBytesRate>(.*)</matchDropBytesRate>.*\s*', xml_str)
        # if re_find and int(re_find[0])!=0 :
        if re_find:
            attr['matchDropBytesRate'] = re_find[0]
        re_find = re.findall(
            r'.*<matchPktRate>(.*)</matchPktRate>.*\s*', xml_str)
        if re_find:
            attr['matchPktRate'] = re_find[0]
        re_find = re.findall(
            r'.*<matchByteRate>(.*)</matchByteRate>.*\s*', xml_str)
        if re_find:
            attr['matchByteRate'] = re_find[0]
        re_find = re.findall(
            r'.*<urpfPackets>(.*)</urpfPackets>.*\s*', xml_str)
        if re_find:
            attr['urpfPackets'] = re_find[0]
        re_find = re.findall(r'.*<urpfBytes>(.*)</urpfBytes>.*\s*', xml_str)
        if re_find:
            attr['urpfBytes'] = re_find[0]
        re_find = re.findall(
            r'.*<urpfPktsRate>(.*)</urpfPktsRate>.*\s*', xml_str)
        if re_find:
            attr['urpfPktsRate'] = re_find[0]
        re_find = re.findall(
            r'.*<urpfBytesRate>(.*)</urpfBytesRate>.*\s*', xml_str)
        if re_find:
            attr['urpfBytesRate'] = re_find[0]
        re_find = re.findall(r'.*<carPackets>(.*)</carPackets>.*\s*', xml_str)
        if re_find:
            attr['carPackets'] = re_find[0]
        re_find = re.findall(r'.*<carBytes>(.*)</carBytes>.*\s*', xml_str)
        if re_find:
            attr['carBytes'] = re_find[0]
        re_find = re.findall(
            r'.*<carPktsRate>(.*)</carPktsRate>.*\s*', xml_str)
        if re_find:
            attr['carPktsRate'] = re_find[0]
        re_find = re.findall(
            r'.*<carBytesRate>(.*)</carBytesRate>.*\s*', xml_str)
        if re_find:
            attr['carBytesRate'] = re_find[0]
        re_find = re.findall(
            r'.*<filterPackets>(.*)</filterPackets>.*\s*', xml_str)
        if re_find:
            attr['filterPackets'] = re_find[0]
        re_find = re.findall(
            r'.*<filterBytes>(.*)</filterBytes>.*\s*', xml_str)
        if re_find:
            attr['filterBytes'] = re_find[0]
        re_find = re.findall(
            r'.*<filterPktsRate>(.*)</filterPktsRate>.*\s*', xml_str)
        if re_find:
            attr['filterPktsRate'] = re_find[0]
        re_find = re.findall(
            r'.*<filterBytesRate>(.*)</filterBytesRate>.*\s*', xml_str)
        if re_find:
            attr['filterBytesRate'] = re_find[0]
        re_find = re.findall(r'.*<vlanId>(.*)</vlanId>.*\s*', xml_str)
        if re_find:
            attr['vlanId'] = re_find[0]
        re_find = re.findall(r'.*<peVlanId>(.*)</peVlanId>.*\s*', xml_str)
        if re_find:
            attr['peVlanId'] = re_find[0]
        re_find = re.findall(r'.*<applyTime>(.*)</applyTime>.*\s*', xml_str)
        if re_find:
            attr['applyTime'] = re_find[0]
        return attr

    def query_policy(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        if not self.ifname:
            self.ifname = ' '
        conf_str = None
        self.vlanMode = 'true'
        if self.groupId == '0':
            self.vlanMode = 'false'
        conf_str = QUERY_POLICY % (self.ifname,
                                   self.direction,
                                   self.policyName,
                                   self.layer,
                                   self.vlanMode,
                                   self.groupId)
        print('conf_str', conf_str)
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return attr
        else:
            find = re.findall(
                r'.*<qosPolicyStats>([\s\S]*)</qosPolicyStats>.*\s*', xml_str)
            print('find', find)
            if find:
                ifname = re.findall(r'.*<ifName>(.*)</ifName>.*\s*', xml_str)
                groupId = re.findall(
                    r'.*<groupId>(.*)</groupId>.*\s*', xml_str)
                direction = re.findall(
                    r'.*<direction>(.*)</direction>.*\s*', xml_str)
                re_find = re.split('</qosPolicyStat>', find[0])
                print('re_find', re_find)
                for i in range(len(re_find)):
                    str = re_find[i]
                    attr = self.get_query_data(str)
                    if attr:
                        attr['ifname'] = ifname[0]
                        attr['groupId'] = groupId[0]
                        attr['direction'] = direction[0]
                        output_msg_list.append(attr)
        return output_msg_list

    def merge_ifcar(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_ifcar(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        if not self.ifname:
            self.ifname = ' '
        conf_str = None
        conf_str = QOS_IFCAR_CFGGET % (self.ifname)
        print('conf_str', conf_str)
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return attr
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</qosIfQos>', xml_str)
            print('77777', xml_str_split)

            for j in range(len(xml_str_split)):
                find_ifname = re.findall(
                    r'.*<ifName>(.*)</ifName>.*\s*', xml_str_split[j])
                print('llll', find_ifname)

                if not find_ifname:
                    print('444444')
                    continue
                print('yyyyyy****', xml_str_split[j])
                xml_str_policy = re.split(
                    '</qosPolicyApply>', xml_str_split[j])
                print('8888****', xml_str_policy)
                for i in range(len(xml_str_policy)):
                    attr = dict()
                    attr = self.get_data(xml_str_policy[i])
                    if attr:
                        attr['ifname'] = find_ifname[0]
                        output_msg_list.append(attr)

        return output_msg_list

    def undo_ifcar(self):

        # conf_str = self.constuct_xml()
        self.vlanMode = 'true'
        if self.groupId == '0':
            self.vlanMode = 'false'

        conf_str = DELETE_POLICYAPPLY % (self.ifname,
                                         self.direction,
                                         self.policyName,
                                         self.layer,
                                         self.vlanMode,
                                         self.groupId)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")
        # self.changed = True

    def get_proposed(self):

        if self.ifname:
            self.proposed["policyName"] = self.policyName
        if self.direction:
            self.proposed["direction"] = self.direction
        if self.policyName:
            self.proposed["policyName"] = self.policyName
        if self.groupId:
            self.proposed["groupId"] = self.groupId
        if self.peVlanId:
            self.proposed["peVlanId"] = self.peVlanId
        if self.vlanId:
            self.proposed["vlanId"] = self.vlanId
        if self.layer:
            self.proposed["layer"] = self.layer
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
        if self.operation == 'create' or self.operation == 'getconfig' or self.operation == 'delete':
            ifcarcfg_attr_exist = self.get_ifcar()
            if ifcarcfg_attr_exist:
                self.results["existing"] = ifcarcfg_attr_exist

        if self.operation == 'create':
            self.merge_ifcar()

        if self.operation == 'delete':
            self.undo_ifcar()

        if self.operation == 'create' or self.operation == 'getconfig' or self.operation == 'delete':
            ifcarcfg_attr_end_stat = self.get_ifcar()
            if ifcarcfg_attr_end_stat:
                self.results["end_stat"] = ifcarcfg_attr_end_stat
                if self.operation != 'getconfig':
                    self.results["changed"] = True
                self.results["proposed"] = self.proposed

        if self.operation == 'query_stastics':
            ifcarcfg_attr_exist = self.query_policy()
            if ifcarcfg_attr_exist:
                self.ifcarcfg_exist = True
            self.results["end_stat"].append(ifcarcfg_attr_exist)
        if self.operation == 'clear_stastics':
            self.reset_policy()

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        ifname=dict(required=False, type='str'),
        direction=dict(required=False, choices=['inbound', 'outbound']),
        policyName=dict(required=False, type='str'),
        groupId=dict(required=False, type='str'),
        peVlanId=dict(required=False, type='str'),
        vlanId=dict(required=False, type='str'),
        layer=dict(required=False, choices=['none', 'link', 'mpls', 'all']),

        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete',
                'query_stastics',
                'clear_stastics'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWCQosIfCar = QosIfCarCfg(argument_spec)
    NEWCQosIfCar.work()


if __name__ == '__main__':
    main()
