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

from ansible.module_utils.network.ne.ne import constr_container_process_tail
from ansible.module_utils.network.ne.ne import constr_container_process_head
from ansible.module_utils.network.ne.ne import constr_container_tail
from ansible.module_utils.network.ne.ne import constr_container_head
from ansible.module_utils.network.ne.ne import constr_leaf_novalue
from ansible.module_utils.network.ne.ne import constr_leaf_value
from ansible.module_utils.network.ne.ne import NE_COMMON_XML_OPERATION_DELETE
from ansible.module_utils.network.ne.ne import NE_COMMON_XML_OPERATION_MERGE
from ansible.module_utils.network.ne.ne import NE_COMMON_XML_OPERATION_CREATE
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, execute_nc_action_yang, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import collections
import re
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ne_qos_ifcar
version_added: "2.6"
short_description: Manages Interface-Based Traffic Policing on HUAWEI NetEngine devices.
description:
    - Manages Interface-Based Traffic Policing on HUAWEI NetEngine devices.
options:
    ifname:
        description:
            - Name of interface.
              The value is a string of 1 to 31 characters.
        required: false
        default: null
    direction
        description:
            - Apply car to this interface direction.
        required: false
        default: null
        choices: ['inbound','outbound']
    groupId:
        description:
            - Vlan group id.
              When create car with vlan, groupId is randomly assigned to uniquely identify a VLAN group,
              when delete or query_stastics or clear_stastics, groupId acts as
              an optional parameter to operate a VLAN group.
        required: false
        default: null
    vlanid:
        description:
            - Range of VLANs such as C(2-10) or C(2,5,10-15), etc.
        required: false
        default: null
    cir:
        description:
            - Committed information rate.
              The value is an integer ranging from 0 to 4294967295.
        required: false
        default: null
    pir:
        description:
            - Peak information rate.
              The value is an integer ranging from 0 to 4294967295.
        required: false
        default: null
    cbs:
        description:
            - Value of CBS (Unit: byte): The configured value is recommended to be 187 times of the CIR value.
              The value is an integer ranging from 0 to 4294967295.
        required: false
        default: null
    pbs:
        description:
            - Value of PBS (Unit: byte): The configured value is recommended to be 187 times of the PIR value.
              The value is an integer ranging from 0 to 4294967295.
        required: false
        default: null
    greenAction:
        description:
            - Specify behavior conducted when rate no higher than CIR.
              If greenAction is discard, greenServiceClass and greenColor can not config.
        required: false
        default: pass
        choices: ['pass','discard']
    greenServiceClass:
        description:
            - Set service class.
              GreenServiceClass and greenColor must be configured at the same time.
        required: false
        default: null
        choices: ['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']
    greenColor:
        description:
            - Assign color.
              GreenServiceClass and greenColor must be configured at the same time.
        required: false
        default: null
        choices: ['green','red','yellow']
    yellowAction:
        description:
            - Specify behavior conducted when rate higher than CIR, no higher than PIR.
              If yellowAction is discard, yellowServiceClass and yellowColor can not config.
        required: false
        default: null
        choices: ['pass','discard']
    yellowServiceClass:
        description:
            - Set service class.
              YellowServiceClass and yellowColor must be configured at the same time.
        required: false
        default: null
        choices: ['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']
    yellowColor:
        description:
            - Assign color.
              YellowServiceClass and yellowColor must be configured at the same time.
        required: false
        default: null
        choices: ['green','red','yellow']
    redAction:
        description:
            - Specify behavior conducted when rate higher than PIR.
              If redAction is discard, redServiceClass and redColor can not config.
        required: false
        default: discard
        choices: ['pass','discard']
    redServiceClass:
        description:
            - Set service class.
              RedServiceClass and redColor must be configured at the same time.
        required: false
        default: null
        choices: ['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']
    redColor:
        description:
            - Assign color.
              RedServiceClass and redColor must be configured at the same time.
        required: false
        default: null
        choices: ['green','red','yellow']
    colorAware:
        description:
            - Switch car to work at color awaring mode.
        required: false
        default: false
        choices: ['true', 'false']
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete', 'query_stastics', 'clear_stastics']
'''

EXAMPLES = '''
- name: ne_ifcar module test
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

  - name: Config car
    ne_ifcar:
      ifname: "GigabitEthernet0/2/6"
      direction: outbound
      cir: 10
      greenAction: pass
      vlanid: 1-3
      operation: create
      provider: "{{ cli }}"

  - name: Get car configuration
    ne_ifcar:
      ifname: GigabitEthernet0/2/6
      operation: getconfig
      provider: "{{ cli }}"

  - name: Undo car
    ne_ifcar:
      ifname: "GigabitEthernet0/2/6"
      direction: "outbound"
      groupId: 1
      cir: 10
      greenAction: "pass"
      operation: delete
      provider: "{{ cli }}"

  - name: Query car stastics
    ne_ifcar:
      ifname: "GigabitEthernet0/2/6"
      direction: "outbound"
      groupId: 1
      operation: query_stastics
      provider: "{{ cli }}"

  - name: Clear car stastics
    ne_ifcar:
      ifname: "GigabitEthernet0/2/6"
      direction: "outbound"
      groupId: 1
      operation: clear_stastics
      provider: "{{ cli }}"
'''

RETURN = '''
existing:
    description: k/v pairs of existing car
    returned: always
    type: dict
    sample: {"cbs": "1870",
             "cir": "10",
             "colorAware": "false",
             "direction": "outbound",
             "greenAction": "pass",
             "groupId": "1",
             "ifname": "Eth-Trunk1",
             "pbs": "0",
             "redAction": "discard",
             "vlanId": ["1", "2", "3"] }
'''


PRODUCT_SYSTERM = """
<filter type="subtree">
<system xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0"></system>
</filter>
"""

QOS_IFCAR_HEALDER = """
  <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
      <qosIfQos>
        <ifName>%s</ifName>
        <qosIfCars>
          <qosIfCar xc:operation="%s">
"""

QOS_IFCAR_TAIL = """
          </qosIfCar>
        </qosIfCars>
      </qosIfQos>
    </qosIfQoss>
  </qos>
</config>
"""

QOS_IFCAR_GET_HEALDER = """
<filter type="subtree">
  <qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
      <qosIfQos>
"""

QOS_IFCAR_GET_TAIL = """
      </qosIfQos>
    </qosIfQoss>
  </qos>
</filter>
"""


QOS_IFCAR_MERGE = """
  <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
      <qosIfQos xc:operation="merge">
        <ifName>%s</ifName>
        <qosIfCars>
          <qosIfCar xc:operation="merge">
            <direction>%s</direction>
            <vlanMode>%s</vlanMode>
            <groupId>0</groupId>
            <identifier>no</identifier>
            <cir>%s</cir>
            <pir>%s</pir>
            <cbs>%s</cbs>
            <pbs>%s</pbs>
            <greenAction>%s</greenAction>
            <greenServiceClass>%s</greenServiceClass>
            <greenColor>%s</greenColor>
            <yellowAction>%s</yellowAction>
            <yellowServiceClass>%s</yellowServiceClass>
            <yellowColor>%s</yellowColor>
            <redAction>%s</redAction>
            <redServiceClass>%s</redServiceClass>
            <redColor>%s</redColor>
            <vlanId>%s</vlanId>
            <colorAware>%s</colorAware>
            <rateMode>value</rateMode>
          </qosIfCar>
        </qosIfCars>
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
        <qosIfCars>
          <qosIfCar>
            <direction>%s</direction>
            <vlanMode>%s</vlanMode>
            <groupId>%s</groupId>
            <identifier/>
            <cir/>
            <pir/>
            <cirPercent/>
            <pirPercent/>
            <cbs/>
            <pbs/>
            <greenAction/>
            <greenServiceClass/>
            <greenColor/>
            <yellowAction/>
            <yellowServiceClass/>
            <yellowColor/>
            <redAction/>
            <redServiceClass/>
            <redColor/>
            <vlanId/>
            <colorAware/>
            <rateMode/>
          </qosIfCar>
        </qosIfCars>
      </qosIfQos>
    </qosIfQoss>
  </qos>
</filter>
"""
QOS_IFCAR_CFGUNDO = """
<config>
  <qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
      <qosIfQos>
        <ifName>%s</ifName>
        <qosIfCars>
            <qosIfCar operation="delete">
            <direction>%s</direction>
            <vlanMode>%s</vlanMode>
            <groupId>%d</groupId>
          </qosIfCar>
        </qosIfCars>
      </qosIfQos>
    </qosIfQoss>
  </qos>
</config>
"""


QOS_IFCAR_QUERY = """
<filter type="subtree">
  <qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosIfQoss>
      <qosIfQos>
        <ifName>%s</ifName>
        <qosIfCars>
          <qosIfCar>
            <direction>%s</direction>
            <vlanMode>%s</vlanMode>
            <groupId>%s</groupId>
            <qosIfCarStats>
              <qosIfCarStat>
                <slotIdPath/>
                <passPackets/>
                <passBytes/>
                <dropPackets/>
                <dropBytes/>
                <passPktsRate/>
                <passBytesRate/>
                <dropPktsRate/>
                <dropBytesRate/>
                <vlanId/>
                </qosIfCarStat>
            </qosIfCarStats>
          </qosIfCar>
        </qosIfCars>
      </qosIfQos>
    </qosIfQoss>
  </qos>
</filter>
"""
QOS_IFCAR_RESET = """
    <qos:qosResetIfCar xmlns:qos="http://www.huawei.com/netconf/vrp/huawei-qos">
      <qos:ifName>%s</qos:ifName>
      <qos:direction>%s</qos:direction>
      <qos:groupId>%d</qos:groupId>
    </qos:qosResetIfCar>

"""


class QosIfCarCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        self.ifname = self.module.params['ifname']
        self.direction = self.module.params['direction']
        self.vlanid = self.module.params['vlanid']
        self.groupId = self.module.params['groupId']
        self.cir = self.module.params['cir']
        self.pir = self.module.params['pir']
        self.cbs = self.module.params['cbs']
        self.pbs = self.module.params['pbs']
        self.greenAction = self.module.params['greenAction']
        self.greenServiceClass = self.module.params['greenServiceClass']
        self.greenColor = self.module.params['greenColor']
        self.yellowAction = self.module.params['yellowAction']
        self.yellowServiceClass = self.module.params['yellowServiceClass']
        self.yellowColor = self.module.params['yellowColor']
        self.redAction = self.module.params['redAction']
        self.redServiceClass = self.module.params['redServiceClass']
        self.redColor = self.module.params['redColor']
        self.colorAware = self.module.params['colorAware']
        self.operation = self.module.params['operation']
        self.existing = dict()
        self.results = dict()
        self.ifcarcfg_exist = False
        self.ifcarcfg_attr_exist = None
        self.results["existing"] = []

    def init_module(self):
        """
        init ansilbe NetworkModule.
        """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_product_name(self):
        """Check all input params"""

        conf_str = None
        conf_str = PRODUCT_SYSTERM
        xml_str = get_nc_config(self.module, PRODUCT_SYSTERM)
        # print('xml_str', xml_str)
        attr = dict()
        if "<data/>" in xml_str:
            return attr
        else:
            attr_total = list()
            re_find_product_name = re.findall(
                r'.*<productName>(.*)</productName>.*\s*', xml_str)
            print("yyyyy", re_find_product_name, re_find_product_name[0])
        if re_find_product_name:
            if (re_find_product_name[0] == 'ATN 950B') or (
                    re_find_product_name[0] == 'ATN 910B'):
                self.module.fail_json(
                    msg='Error: ATN 950B and ATN 910B does not support this modules.')
        return None

    def check_params(self):
        """Check all input params"""
        # check the necessary element for get/merge/query/delete
        if self.operation == 'create':
            # create necessary element
            if not self.ifname or not self.direction or (self.groupId is None):
                self.module.fail_json(
                    msg='Error: Please input the necessary element includes ifname/direction/groupId.')

        if self.operation == 'delete':
            if not self.ifname or not self.direction:
                self.module.fail_json(
                    msg='Error: Please input the necessary element includes ifname/direction/groupId.')

        # check the length of ifname
        if self.ifname:
            if len(self.ifname) > 32:
                self.module.fail_json(
                    msg='Error: The length of the interface name is not in the range from 1 to 32.')
        # check the vlanid
        if self.vlanid:
            vlan_list = self.vlanid_to_list(self.vlanid)
            self.vlanid = self.vlan_list_to_bitmap(vlan_list)
            self.vlanmap = self.bitmap_to_vlan_list(self.vlanid)
            # print("9999", self.vlanmap)
        print("33333333", self.groupId)

        if self.groupId:
            if not self.groupId.isdigit():
                self.module.fail_json(
                    msg="Error: GroupId value is not digit.")
        """

            if int(self.groupId) < 1 or int(self.groupId) > 4294967295:
                self.module.fail_json(
                    msg='Error: GroupId value is not in the range from 1 to 4294967295.')
        """
        # check the range of cir
        if self.cir:
            if not self.cir.isdigit():
                self.module.fail_json(
                    msg="Error: Cir value is not digit.")
            print("44444", self.cir, int(self.cir))
            if int(self.cir) < 0 or int(self.cir) > 4294967295:
                self.module.fail_json(
                    msg='Error: Cir value is not in the range from 0 to 4294967295.')
        # check the range of pir
        if self.pir:
            if not self.pir.isdigit():
                self.module.fail_json(
                    msg="Error: Pir value is not digit.")
            if int(self.pir) < 0 or int(self.pir) > 4294967295:
                self.module.fail_json(
                    msg='Error: Pir value is not in the range from 0 to 4294967295.')
            if self.pir < self.cir:
                self.module.fail_json(
                    msg='Error: Pir value can not be less than cir value.')

        # check the range of cbs
        if self.cbs:
            if not self.cbs.isdigit():
                self.module.fail_json(
                    msg="Error: Cbs value is not digit.")

            if int(self.cbs) < 0 or int(self.cbs) > 4294967295:
                self.module.fail_json(
                    msg='Error: Cbs value is not in the range from 0 to 4294967295.')
        # check the range of pbs
        if self.pbs:
            if not self.pbs.isdigit():
                self.module.fail_json(
                    msg="Error: Pbs value is not digit.")

            if not self.cbs:
                self.module.fail_json(
                    msg='Error: Pbs can not be configured when cbs is not configured.')
            if int(self.pbs) < 0 or int(self.pbs) > 4294967295:
                self.module.fail_json(
                    msg='Error: Pbs value is not in the range from 0 to 4294967295.')

        if self.greenAction == 'discard':
            if (self.greenServiceClass or self.greenColor):
                self.module.fail_json(
                    msg='Error: GreenServiceClass and greenColor can not be configured when greenAction is configured discard.')

        if self.yellowAction == 'discard':

            if (self.yellowServiceClass or self.yellowColor):
                self.module.fail_json(
                    msg='Error: yellowServiceClass and yellowColor can not be configured when yellowAction is configured discard.')

        if self.redAction == 'discard':
            if (self.redServiceClass or self.redColor):
                self.module.fail_json(
                    msg='Error: RedServiceClass and redColor can not be configured when redAction is configured discard.')
        if ((self.greenServiceClass and (not self.greenColor)) or (
                self.greenColor and (not self.greenServiceClass))):
            self.module.fail_json(
                msg='Error: GreenServiceClass and greenColor must be config at the same time.')

        if ((self.redServiceClass and (not self.redColor)) or (
                self.redColor and (not self.redServiceClass))):
            self.module.fail_json(
                msg='Error: RedServiceClass and redColor must be config at the same time.')

        if ((self.yellowServiceClass and (not self.yellowColor)) or (
                self.yellowColor and (not self.yellowServiceClass))):
            self.module.fail_json(
                msg='Error: YellowServiceClass and yellowColor must be config at the same time.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

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

        return tmp

    """
    def config_ifcar(self, ifname, direction, vlanid, identifier, cir, pir, cbs, pbs, greenAction, greenServiceClass, greenColor, yellowAction, \
    yellowServiceClass, yellowColor, redAction, redServiceClass, redColor, colorAware):
        if not self.vlanid:
            vlanmode='false'
        else:
            vlanmode='true'
        if cir is None:
            cir=' '
        if pir is None:
            pir=' '
        if cbs is None:
            cbs=' '
        if pbs is None:
            pbs=' '
        if not greenServiceClass:
            greenServiceClass=' '
        if not greenColor:
            greenColor=' '
        if not yellowAction:
            yellowAction=' '
        if not yellowServiceClass:
            yellowServiceClass=' '
        if not yellowColor:
            yellowColor=' '
        if not redServiceClass:
            redServiceClass=' '
        if not redColor:
            redColor=' '
        conf_str = None
        conf_str = QOS_IFCAR_CFG % (ifname, direction, vlanmode, identifier, str(cir), str(pir), str(cbs), str(pbs), greenAction, greenServiceClass, \
        greenColor, yellowAction, yellowServiceClass, yellowColor, redAction, redServiceClass, redColor, vlanid, colorAware)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")
        #self.changed = True
        """

    def merge_ifcar(self, ifname):

        if not self.vlanid:
            vlanmode = 'false'
        else:
            vlanmode = 'true'

        xml_str = QOS_IFCAR_HEALDER % (ifname, NE_COMMON_XML_OPERATION_MERGE)
        xml_str = constr_leaf_value(xml_str, "direction", self.direction)
        xml_str = constr_leaf_value(xml_str, "vlanMode", vlanmode)
        xml_str = constr_leaf_value(xml_str, "groupId", self.groupId)
        xml_str = constr_leaf_value(xml_str, "cir", self.cir)
        xml_str = constr_leaf_value(xml_str, "pir", self.pir)
        xml_str = constr_leaf_value(xml_str, "cbs", self.cbs)
        xml_str = constr_leaf_value(xml_str, "pbs", self.pbs)
        xml_str = constr_leaf_value(xml_str, "greenAction", self.greenAction)
        xml_str = constr_leaf_value(
            xml_str,
            "greenServiceClass",
            self.greenServiceClass)
        xml_str = constr_leaf_value(xml_str, "greenColor", self.greenColor)
        xml_str = constr_leaf_value(xml_str, "yellowAction", self.yellowAction)
        xml_str = constr_leaf_value(
            xml_str,
            "yellowServiceClass",
            self.yellowServiceClass)
        xml_str = constr_leaf_value(xml_str, "yellowColor", self.yellowColor)
        xml_str = constr_leaf_value(xml_str, "redAction", self.redAction)
        xml_str = constr_leaf_value(
            xml_str,
            "redServiceClass",
            self.yellowServiceClass)
        xml_str = constr_leaf_value(xml_str, "redColor", self.redColor)
        xml_str = constr_leaf_value(xml_str, "vlanId", self.vlanid)
        xml_str = constr_leaf_value(xml_str, "colorAware", self.colorAware)

        xml_str += "<rateMode>value</rateMode>"
        xml_str += QOS_IFCAR_TAIL

        # conf_str = QOS_IFCAR_MERGE % (ifname, direction, vlanmode, str(cir), str(pir), str(cbs), str(pbs), greenAction, greenServiceClass, greenColor, \
        # yellowAction, yellowServiceClass, yellowColor, redAction, redServiceClass, redColor, vlanid, colorAware)
        print('xml_str', xml_str)
        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "CFG_IFCAR")
        # self.changed = False

    def get_data(self, ifname, xml_str):
        attr = dict()
        attr['ifname'] = ifname
        re_find = re.findall(r'.*<direction>(.*)</direction>.*\s*', xml_str)
        if re_find:
            attr['direction'] = re_find[0]
        re_find = re.findall(r'.*<cir>(.*)</cir>.*\s*', xml_str)
        if re_find:
            attr['cir'] = re_find[0]
        re_find = re.findall(r'.*<pir>(.*)</pir>.*\s*', xml_str)
        if re_find:
            attr['pir'] = re_find[0]
        re_find = re.findall(r'.*<cbs>(.*)</cbs>.*\s*', xml_str)
        if re_find:
            attr['cbs'] = re_find[0]
        re_find = re.findall(r'.*<pbs>(.*)</pbs>.*\s*', xml_str)
        if re_find:
            attr['pbs'] = re_find[0]
        re_find = re.findall(
            r'.*<greenAction>(.*)</greenAction>.*\s*', xml_str)
        if re_find:
            attr['greenAction'] = re_find[0]
        re_find = re.findall(
            r'.*<greenServiceClass>(.*)</greenServiceClass>.*\s*', xml_str)
        if re_find:
            attr['greenServiceClass'] = re_find[0]
        re_find = re.findall(r'.*<greenColor>(.*)</greenColor>.*\s*', xml_str)
        if re_find:
            attr['greenColor'] = re_find[0]
        re_find = re.findall(
            r'.*<yellowAction>(.*)</yellowAction>.*\s*', xml_str)
        if re_find:
            attr['yellowAction'] = re_find[0]
        re_find = re.findall(
            r'.*<yellowServiceClass>(.*)</yellowServiceClass>.*\s*', xml_str)
        if re_find:
            attr['yellowServiceClass'] = re_find[0]
        re_find = re.findall(
            r'.*<yellowColor>(.*)</yellowColor>.*\s*', xml_str)
        if re_find:
            attr['yellowColor'] = re_find[0]
        re_find = re.findall(r'.*<redAction>(.*)</redAction>.*\s*', xml_str)
        if re_find:
            attr['redAction'] = re_find[0]

        re_find = re.findall(
            r'.*<redServiceClass>(.*)</redServiceClass>.*\s*', xml_str)
        if re_find:
            attr['redServiceClass'] = re_find[0]
        re_find = re.findall(r'.*<redColor>(.*)</redColor>.*\s*', xml_str)
        if re_find:
            attr['redColor'] = re_find[0]
        re_find = re.findall(r'.*<vlanId>(.*)</vlanId>.*\s*', xml_str)
        if re_find:
            attr['vlanId'] = self.bitmap_to_vlan_list(re_find[0])
        re_find = re.findall(r'.*<colorAware>(.*)</colorAware>.*\s*', xml_str)
        if re_find:
            attr['colorAware'] = re_find[0]
        re_find = re.findall(r'.*<groupId>(.*)</groupId>.*\s*', xml_str)
        if re_find and int(re_find[0]) != 0:
            attr['groupId'] = re_find[0]

        return attr

    def get_ifcar(self, ifname, direction, groupId):
        """
        vlanmode='false'
        #or self.operation== 'create' or self.operation== 'merge' or self.operation == 'delete'
        if not ifname :
           ifname = ' '
        if not self.direction :
           direction = ' '
        if not self.groupId  :
        #if 0 == groupId :
            groupId = ' '
        if  self.operation == 'create' or self.operation == 'delete' :
            direction = ' '
            groupId = ' '
        conf_str = None
        conf_str = QOS_IFCAR_CFGGET % (ifname, direction, ' ', groupId)
        print('conf_str', conf_str)
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        """
        conf_str = QOS_IFCAR_GET_HEALDER
        conf_str = constr_leaf_value(conf_str, "ifName", self.ifname)

        conf_str = constr_container_head(conf_str, "qosIfCars")
        conf_str = constr_container_head(conf_str, "qosIfCar")
        conf_str = constr_leaf_value(conf_str, "direction", self.direction)
        # conf_str = constr_leaf_value(conf_str, "groupId", self.groupId)

        conf_str = constr_leaf_novalue(conf_str, "cir")
        conf_str = constr_leaf_novalue(conf_str, "pir")
        conf_str = constr_leaf_novalue(conf_str, "cbs")
        conf_str = constr_leaf_novalue(conf_str, "pbs")
        conf_str = constr_leaf_novalue(conf_str, "greenAction")
        conf_str = constr_leaf_novalue(conf_str, "greenServiceClass")
        conf_str = constr_leaf_novalue(conf_str, "greenColor")
        conf_str = constr_leaf_novalue(conf_str, "yellowAction")
        conf_str = constr_leaf_novalue(conf_str, "yellowServiceClass")
        conf_str = constr_leaf_novalue(conf_str, "yellowColor")
        conf_str = constr_leaf_novalue(conf_str, "redAction")
        conf_str = constr_leaf_novalue(conf_str, "redServiceClass")
        conf_str = constr_leaf_novalue(conf_str, "redColor")
        conf_str = constr_leaf_novalue(conf_str, "vlanId")
        conf_str = constr_leaf_novalue(conf_str, "colorAware")

        conf_str = constr_container_tail(conf_str, "qosIfCar")
        conf_str = constr_container_tail(conf_str, "qosIfCars")
        conf_str += QOS_IFCAR_GET_TAIL
        print('conf_str', conf_str)
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)

        attr = dict()
        if "<data/>" in xml_str:
            return attr
        else:

            attr_total = list()

            vlan_list = list()

            xml_str_cars = re.split('</qosIfCars>', xml_str)

            for j in range(len(xml_str_cars)):
                re_find_ifname = re.findall(
                    r'.*<ifName>(.*)</ifName>.*\s*', xml_str_cars[j])
                print("333333", re_find_ifname)
                if not re_find_ifname:
                    break
                ifname = re_find_ifname[-1]
                re_find_direction = re.findall(
                    r'.*<direction>(.*)</direction>.*\s*', xml_str_cars[j])

                xml_str_car = re.split('</qosIfCar>', xml_str_cars[j])

                for i in range(len(re_find_direction)):

                    attr = self.get_data(ifname, xml_str_car[i])
                    attr_total.append(attr)
                    attr = dict()
            return attr_total

    def undo_ifcar(self, ifname, direction, groupId):
        """

        if not self.groupId  :
            groupId = ' '
        conf_get_str = None
        conf_get_str = QOS_IFCAR_CFGGET % (ifname, direction, 'false', groupId)
        xml_get_str = get_nc_config(self.module, conf_get_str)
        print('xml_get_str', xml_get_str)
        """
        xml_str = QOS_IFCAR_HEALDER % (ifname, NE_COMMON_XML_OPERATION_DELETE)
        xml_str = constr_leaf_value(xml_str, "direction", self.direction)
        xml_str = constr_leaf_value(xml_str, "groupId", self.groupId)
        xml_str = constr_leaf_value(xml_str, "vlanMode", "false")
        xml_str += QOS_IFCAR_TAIL
        print('xml_str', xml_str)
        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "DELETE_IFCAR")

    def query_ifcar(self, ifname, direction, vlanid, groupId):
        if not ifname:
            ifname = ' '
        if not self.groupId:
            vlanmode = 'false'
        else:
            vlanmode = 'true'
        if not self.groupId:
            groupId = ' '
        if not self.direction:
            direction = ' '
        conf_str = None
        conf_str = QOS_IFCAR_QUERY % (ifname, direction, vlanmode, groupId)
        xml_str = get_nc_config(self.module, conf_str)
        attr = collections.OrderedDict()
        output_msg_list = list()
        output_msg = list()

        if "<data/>" in xml_str:
            return output_msg
        else:

            xml_str_split = re.split('</qosIfQos>', xml_str)
            for j in range(len(xml_str_split)):

                re_find = re.findall(r'.*<passBytes>(.*)</passBytes>.*\s*'
                                     r'<passPackets>(.*)</passPackets>.*\s*'
                                     r'<dropBytes>(.*)</dropBytes>.*\s*'
                                     r'<dropPackets>(.*)</dropPackets>.*\s*'
                                     r'<passPktsRate>(.*)</passPktsRate>.*\s*'
                                     r'<passBytesRate>(.*)</passBytesRate>.*\s*'
                                     r'<dropPktsRate>(.*)</dropPktsRate>.*\s*'
                                     r'<dropBytesRate>(.*)</dropBytesRate>.*\s*'
                                     r'<vlanId>(.*)</vlanId>.*\s',
                                     # r'<vid>(.*)</vid>.*\s',
                                     xml_str_split[j])

                print('re_find', re_find)
                if re_find:
                    ifname = re.findall(
                        r'.*<ifName>(.*)</ifName>.*\s*', xml_str_split[j])
                    groupId = re.findall(
                        r'.*<groupId>(.*)</groupId>.*\s*', xml_str_split[j])
                    direction = re.findall(
                        r'.*<direction>(.*)</direction>.*\s*', xml_str_split[j])

                    for i in range(len(re_find)):
                        attr = collections.OrderedDict()
                        attr['ifName'] = ifname[0]
                        if int(groupId[0]) != 0:
                            attr['groupId'] = groupId[0]
                        attr['direction'] = direction[0]
                        attr['passBytes'] = re_find[i][0]
                        attr['passPackets'] = re_find[i][1]
                        attr['dropBytes'] = re_find[i][2]
                        attr['dropPackets'] = re_find[i][3]
                        attr['passPktsRate'] = re_find[i][4]
                        attr['passBytesRate'] = re_find[i][5]
                        attr['dropPktsRate'] = re_find[i][6]
                        attr['dropBytesRate'] = re_find[i][7]
                        attr['vlanId'] = re_find[i][8]
                        output_msg_list.append(attr)

        return output_msg_list

    def reset_ifcar(self, ifname, direction, groupId):
        # get first
        if not self.groupId:
            groupId = ' '
        conf_get_str = None
        conf_get_str = QOS_IFCAR_CFGGET % (ifname, direction, 'false', groupId)
        xml_get_str = get_nc_config(self.module, conf_get_str)
        print('xml_get_str', xml_get_str)
        attr = dict()
        if "<data/>" in xml_get_str:
            return attr
        else:
            attr_total = list()
            re_find_groupid = re.findall(
                r'.*<groupId>(.*)</groupId>.*\s*', xml_get_str)
            for i in range(len(re_find_groupid)):
                conf_str = None
                conf_str = QOS_IFCAR_RESET % (
                    ifname, direction, int(re_find_groupid[i]))
                recv_xml = execute_nc_action_yang(self.module, conf_str)
                self.check_response(recv_xml, "RESET_IFCAR")
        return None

    def work(self):
        """
        worker.
        """
        # modify
        # self.check_product_name()
        self.check_params()
        if self.operation == 'create':
            self.merge_ifcar(self.ifname)

        elif self.operation == 'delete':
            self.undo_ifcar(self.ifname, self.direction, self.groupId)
        if self.operation == 'create' or self.operation == 'getconfig' or self.operation == 'delete':

            ifcarcfg_attr_exist = self.get_ifcar(
                self.ifname, self.direction, self.groupId)
            if ifcarcfg_attr_exist:
                self.ifcarcfg_exist = True
            self.results["existing"] = ifcarcfg_attr_exist

        if self.operation == 'query_stastics':
            ifcarcfg_attr_exist = self.query_ifcar(
                self.ifname, self.direction, self.vlanid, self.groupId)
            if ifcarcfg_attr_exist:
                self.ifcarcfg_exist = True
            self.results["existing"] = ifcarcfg_attr_exist
        elif self.operation == 'clear_stastics':
            self.reset_ifcar(self.ifname, self.direction, self.groupId)

        self.module.exit_json(**self.results)


def main():
    """ module main """
    argument_spec = dict(
        ifname=dict(required=False, type='str'),
        direction=dict(required=False, choices=['inbound', 'outbound']),
        vlanid=dict(required=False, type='str'),
        groupId=dict(required=False, type='str'),
        cir=dict(required=False, type='str'),
        pir=dict(required=False, type='str'),
        cbs=dict(required=False, type='str'),
        pbs=dict(required=False, type='str'),
        greenAction=dict(
            required=False,
            choices=[
                'pass',
                'discard'],
            default='pass'),
        greenServiceClass=dict(
            required=False,
            choices=[
                'be',
                'af1',
                'af2',
                'af3',
                'af4',
                'ef',
                'cs6',
                'cs7']),
        greenColor=dict(required=False, choices=['green', 'yellow', 'red']),
        yellowAction=dict(required=False, choices=['pass', 'discard']),
        yellowServiceClass=dict(
            required=False,
            choices=[
                'be',
                'af1',
                'af2',
                'af3',
                'af4',
                'ef',
                'cs6',
                'cs7']),
        yellowColor=dict(required=False, choices=['green', 'yellow', 'red']),
        redAction=dict(
            required=False,
            choices=[
                'pass',
                'discard'],
            default='discard'),
        redServiceClass=dict(
            required=False,
            choices=[
                'be',
                'af1',
                'af2',
                'af3',
                'af4',
                'ef',
                'cs6',
                'cs7']),
        redColor=dict(required=False, choices=['green', 'yellow', 'red']),
        colorAware=dict(
            required=False,
            choices=[
                'true',
                'false'],
            default='false'),
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
