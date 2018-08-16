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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ce_vxlan_vap
version_added: "2.4"
short_description: Manages VXLAN virtual access point on HUAWEI CloudEngine Devices.
description:
    - Manages VXLAN Virtual access point on HUAWEI CloudEngine Devices.
author: QijunPan (@CloudEngine-Ansible)
options:
    bridge_domain_id:
        description:
            - Specifies a bridge domain ID.
              The value is an integer ranging from 1 to 16777215.
    bind_vlan_id:
        description:
            - Specifies the VLAN binding to a BD(Bridge Domain).
              The value is an integer ranging ranging from 1 to 4094.
    l2_sub_interface:
        description:
            - Specifies an Sub-Interface full name, i.e. "10GE1/0/41.1".
              The value is a string of 1 to 63 case-insensitive characters, spaces supported.
    encapsulation:
        description:
            - Specifies an encapsulation type of packets allowed to pass through a Layer 2 sub-interface.
        choices: ['dot1q', 'default', 'untag', 'qinq', 'none']
    ce_vid:
        description:
            - When I(encapsulation) is 'dot1q', specifies a VLAN ID in the outer VLAN tag.
              When I(encapsulation) is 'qinq', specifies an outer VLAN ID for
              double-tagged packets to be received by a Layer 2 sub-interface.
              The value is an integer ranging from 1 to 4094.
    pe_vid:
        description:
            - When I(encapsulation) is 'qinq', specifies an inner VLAN ID for
              double-tagged packets to be received by a Layer 2 sub-interface.
              The value is an integer ranging from 1 to 4094.
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        default: present
        choices: ['present', 'absent']
"""

EXAMPLES = '''
- name: vxlan vap module test
  hosts: ce128
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: Create a papping between a VLAN and a BD
    ce_vxlan_vap:
      bridge_domain_id: 100
      bind_vlan_id: 99
      provider: "{{ cli }}"

  - name: Bind a Layer 2 sub-interface to a BD
    ce_vxlan_vap:
      bridge_domain_id: 100
      l2_sub_interface: 10GE2/0/20.1
      provider: "{{ cli }}"

  - name: Configure an encapsulation type on a Layer 2 sub-interface
    ce_vxlan_vap:
      l2_sub_interface: 10GE2/0/20.1
      encapsulation: dot1q
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"bridge_domain_id": "100", "bind_vlan_id": "99", state="present"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"bridge_domain_id": "100", "bind_intf_list": ["10GE2/0/20.1", "10GE2/0/20.2"],
             "bind_vlan_list": []}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"bridge_domain_id": "100", "bind_intf_list": ["110GE2/0/20.1", "10GE2/0/20.2"],
             "bind_vlan_list": ["99"]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["bridge-domain 100",
             "l2 binding vlan 99"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec

CE_NC_GET_BD_VAP = """
    <filter type="subtree">
      <evc xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bds>
          <bd>
            <bdId>%s</bdId>
            <bdBindVlan>
              <vlanList></vlanList>
            </bdBindVlan>
            <servicePoints>
              <servicePoint>
                <ifName></ifName>
              </servicePoint>
            </servicePoints>
          </bd>
        </bds>
      </evc>
    </filter>
"""

CE_NC_MERGE_BD_VLAN = """
    <config>
      <evc xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bds>
          <bd>
            <bdId>%s</bdId>
            <bdBindVlan operation="merge">
              <vlanList>%s:%s</vlanList>
            </bdBindVlan>
          </bd>
        </bds>
      </evc>
    </config>
"""

CE_NC_MERGE_BD_INTF = """
    <config>
      <evc xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bds>
          <bd>
            <bdId>%s</bdId>
            <servicePoints>
              <servicePoint operation="merge">
                <ifName>%s</ifName>
              </servicePoint>
            </servicePoints>
          </bd>
        </bds>
      </evc>
    </config>
"""

CE_NC_DELETE_BD_INTF = """
    <config>
      <evc xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bds>
          <bd>
            <bdId>%s</bdId>
            <servicePoints>
              <servicePoint operation="delete">
                <ifName>%s</ifName>
              </servicePoint>
            </servicePoints>
          </bd>
        </bds>
      </evc>
    </config>
"""

CE_NC_GET_ENCAP = """
    <filter type="subtree">
      <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <servicePoints>
          <servicePoint>
            <ifName>%s</ifName>
            <flowType></flowType>
            <flowDot1qs>
              <dot1qVids></dot1qVids>
            </flowDot1qs>
            <flowQinqs>
              <flowQinq>
                <peVlanId></peVlanId>
                <ceVids></ceVids>
              </flowQinq>
            </flowQinqs>
          </servicePoint>
        </servicePoints>
      </ethernet>
    </filter>
"""

CE_NC_SET_ENCAP = """
    <config>
      <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <servicePoints>
          <servicePoint operation="merge">
            <ifName>%s</ifName>
            <flowType>%s</flowType>
          </servicePoint>
        </servicePoints>
      </ethernet>
    </config>
"""

CE_NC_UNSET_ENCAP = """
    <config>
      <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <servicePoints>
          <servicePoint operation="merge">
            <ifName>%s</ifName>
            <flowType>none</flowType>
          </servicePoint>
        </servicePoints>
      </ethernet>
    </config>
"""

CE_NC_SET_ENCAP_DOT1Q = """
    <config>
      <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <servicePoints>
          <servicePoint operation="merge">
            <ifName>%s</ifName>
            <flowType>dot1q</flowType>
            <flowDot1qs>
              <dot1qVids>%s:%s</dot1qVids>
            </flowDot1qs>
          </servicePoint>
        </servicePoints>
      </ethernet>
    </config>
"""

CE_NC_SET_ENCAP_QINQ = """
    <config>
      <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <servicePoints>
          <servicePoint>
            <ifName>%s</ifName>
            <flowType>qinq</flowType>
            <flowQinqs>
              <flowQinq operation="merge">
                <peVlanId>%s</peVlanId>
                <ceVids>%s:%s</ceVids>
              </flowQinq>
            </flowQinqs>
          </servicePoint>
        </servicePoints>
      </ethernet>
    </config>
"""


def vlan_vid_to_bitmap(vid):
    """convert VLAN list to VLAN bitmap"""

    vlan_bit = ['0'] * 1024
    int_vid = int(vid)
    j = int_vid / 4
    bit_int = 0x8 >> (int_vid % 4)
    vlan_bit[j] = str(hex(bit_int))[2]

    return ''.join(vlan_bit)


def bitmap_to_vlan_list(bitmap):
    """convert VLAN bitmap to VLAN list"""

    tmp = list()
    if not bitmap:
        return tmp

    bit_len = len(bitmap)
    for i in range(bit_len):
        if bitmap[i] == "0":
            continue
        bit = int(bitmap[i])
        if bit & 0x8:
            tmp.append(str(i * 4))
        if bit & 0x4:
            tmp.append(str(i * 4 + 1))
        if bit & 0x2:
            tmp.append(str(i * 4 + 2))
        if bit & 0x1:
            tmp.append(str(i * 4 + 3))

    return tmp


def is_vlan_bitmap_empty(bitmap):
    """check VLAN bitmap empty"""

    if not bitmap or len(bitmap) == 0:
        return True

    for bit in bitmap:
        if bit != '0':
            return False

    return True


def is_vlan_in_bitmap(vid, bitmap):
    """check is VLAN id in bitmap"""

    if is_vlan_bitmap_empty(bitmap):
        return False

    i = int(vid) / 4
    if i > len(bitmap):
        return False

    if int(bitmap[i]) & (0x8 >> (int(vid) % 4)):
        return True

    return False


def get_interface_type(interface):
    """Gets the type of interface, such as 10GE, ETH-TRUNK, VLANIF..."""

    if interface is None:
        return None

    iftype = None

    if interface.upper().startswith('GE'):
        iftype = 'ge'
    elif interface.upper().startswith('10GE'):
        iftype = '10ge'
    elif interface.upper().startswith('25GE'):
        iftype = '25ge'
    elif interface.upper().startswith('4X10GE'):
        iftype = '4x10ge'
    elif interface.upper().startswith('40GE'):
        iftype = '40ge'
    elif interface.upper().startswith('100GE'):
        iftype = '100ge'
    elif interface.upper().startswith('VLANIF'):
        iftype = 'vlanif'
    elif interface.upper().startswith('LOOPBACK'):
        iftype = 'loopback'
    elif interface.upper().startswith('METH'):
        iftype = 'meth'
    elif interface.upper().startswith('ETH-TRUNK'):
        iftype = 'eth-trunk'
    elif interface.upper().startswith('VBDIF'):
        iftype = 'vbdif'
    elif interface.upper().startswith('NVE'):
        iftype = 'nve'
    elif interface.upper().startswith('TUNNEL'):
        iftype = 'tunnel'
    elif interface.upper().startswith('ETHERNET'):
        iftype = 'ethernet'
    elif interface.upper().startswith('FCOE-PORT'):
        iftype = 'fcoe-port'
    elif interface.upper().startswith('FABRIC-PORT'):
        iftype = 'fabric-port'
    elif interface.upper().startswith('STACK-PORT'):
        iftype = 'stack-Port'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None

    return iftype.lower()


class VxlanVap(object):
    """
    Manages VXLAN virtual access point.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.bridge_domain_id = self.module.params['bridge_domain_id']
        self.bind_vlan_id = self.module.params['bind_vlan_id']
        self.l2_sub_interface = self.module.params['l2_sub_interface']
        self.ce_vid = self.module.params['ce_vid']
        self.pe_vid = self.module.params['pe_vid']
        self.encapsulation = self.module.params['encapsulation']
        self.state = self.module.params['state']

        # state
        self.vap_info = dict()
        self.l2sub_info = dict()
        self.changed = False
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """init module"""

        required_together = [()]
        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_bd_vap_dict(self):
        """get virtual access point info"""

        vap_info = dict()
        conf_str = CE_NC_GET_BD_VAP % self.bridge_domain_id
        xml_str = get_nc_config(self.module, conf_str)

        if "<data/>" in xml_str:
            return vap_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get vap: VLAN
        vap_info["bdId"] = self.bridge_domain_id
        root = ElementTree.fromstring(xml_str)
        vap_info["vlanList"] = ""
        vap_vlan = root.find("data/evc/bds/bd/bdBindVlan")
        vap_info["vlanList"] = ""
        if vap_vlan:
            for ele in vap_vlan:
                if ele.tag == "vlanList":
                    vap_info["vlanList"] = ele.text

        # get vap: l2 su-interface
        vap_ifs = root.findall(
            "data/evc/bds/bd/servicePoints/servicePoint/ifName")
        if_list = list()
        if vap_ifs:
            for vap_if in vap_ifs:
                if vap_if.tag == "ifName":
                    if_list.append(vap_if.text)
        vap_info["intfList"] = if_list

        return vap_info

    def get_l2_sub_intf_dict(self, ifname):
        """get l2 sub-interface info"""

        intf_info = dict()
        if not ifname:
            return intf_info

        conf_str = CE_NC_GET_ENCAP % ifname
        xml_str = get_nc_config(self.module, conf_str)

        if "<data/>" in xml_str:
            return intf_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get l2 sub interface encapsulation info
        root = ElementTree.fromstring(xml_str)
        bds = root.find("data/ethernet/servicePoints/servicePoint")
        if not bds:
            return intf_info

        for ele in bds:
            if ele.tag in ["ifName", "flowType"]:
                intf_info[ele.tag] = ele.text.lower()

        if intf_info.get("flowType") == "dot1q":
            ce_vid = root.find(
                "data/ethernet/servicePoints/servicePoint/flowDot1qs")
            intf_info["dot1qVids"] = ""
            if ce_vid:
                for ele in ce_vid:
                    if ele.tag == "dot1qVids":
                        intf_info["dot1qVids"] = ele.text
        elif intf_info.get("flowType") == "qinq":
            vids = root.find(
                "data/ethernet/servicePoints/servicePoint/flowQinqs/flowQinq")
            if vids:
                for ele in vids:
                    if ele.tag in ["peVlanId", "ceVids"]:
                        intf_info[ele.tag] = ele.text

        return intf_info

    def config_traffic_encap_dot1q(self):
        """configure traffic encapsulation type dot1q"""

        xml_str = ""
        self.updates_cmd.append("interface %s" % self.l2_sub_interface)
        if self.state == "present":
            if self.encapsulation != self.l2sub_info.get("flowType"):
                if self.ce_vid:
                    vlan_bitmap = vlan_vid_to_bitmap(self.ce_vid)
                    xml_str = CE_NC_SET_ENCAP_DOT1Q % (
                        self.l2_sub_interface, vlan_bitmap, vlan_bitmap)
                    self.updates_cmd.append("encapsulation %s vid %s" % (
                        self.encapsulation, self.ce_vid))
                else:
                    xml_str = CE_NC_SET_ENCAP % (
                        self.l2_sub_interface, self.encapsulation)
                    self.updates_cmd.append(
                        "encapsulation %s" % self.encapsulation)
            else:
                if self.ce_vid and not is_vlan_in_bitmap(
                        self.ce_vid, self.l2sub_info.get("dot1qVids")):
                    vlan_bitmap = vlan_vid_to_bitmap(self.ce_vid)
                    xml_str = CE_NC_SET_ENCAP_DOT1Q % (
                        self.l2_sub_interface, vlan_bitmap, vlan_bitmap)
                    self.updates_cmd.append("encapsulation %s vid %s" % (
                        self.encapsulation, self.ce_vid))
        else:
            if self.encapsulation == self.l2sub_info.get("flowType"):
                if self.ce_vid:
                    if is_vlan_in_bitmap(self.ce_vid, self.l2sub_info.get("dot1qVids")):
                        xml_str = CE_NC_UNSET_ENCAP % self.l2_sub_interface
                        self.updates_cmd.append("undo encapsulation %s vid %s" % (
                            self.encapsulation, self.ce_vid))
                else:
                    xml_str = CE_NC_UNSET_ENCAP % self.l2_sub_interface
                    self.updates_cmd.append(
                        "undo encapsulation %s" % self.encapsulation)

        if not xml_str:
            self.updates_cmd.pop()
            return
        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "CONFIG_INTF_ENCAP_DOT1Q")
        self.changed = True

    def config_traffic_encap_qinq(self):
        """configure traffic encapsulation type qinq"""

        xml_str = ""
        self.updates_cmd.append("interface %s" % self.l2_sub_interface)
        if self.state == "present":
            if self.encapsulation != self.l2sub_info.get("flowType"):
                if self.ce_vid:
                    vlan_bitmap = vlan_vid_to_bitmap(self.ce_vid)
                    xml_str = CE_NC_SET_ENCAP_QINQ % (self.l2_sub_interface,
                                                      self.pe_vid,
                                                      vlan_bitmap,
                                                      vlan_bitmap)
                    self.updates_cmd.append(
                        "encapsulation %s vid %s ce-vid %s" % (self.encapsulation,
                                                               self.pe_vid,
                                                               self.ce_vid))
                else:
                    xml_str = CE_NC_SET_ENCAP % (
                        self.l2_sub_interface, self.encapsulation)
                    self.updates_cmd.append(
                        "encapsulation %s" % self.encapsulation)
            else:
                if self.ce_vid:
                    if not is_vlan_in_bitmap(self.ce_vid, self.l2sub_info.get("ceVids")) \
                            or self.pe_vid != self.l2sub_info.get("peVlanId"):
                        vlan_bitmap = vlan_vid_to_bitmap(self.ce_vid)
                        xml_str = CE_NC_SET_ENCAP_QINQ % (self.l2_sub_interface,
                                                          self.pe_vid,
                                                          vlan_bitmap,
                                                          vlan_bitmap)
                        self.updates_cmd.append(
                            "encapsulation %s vid %s ce-vid %s" % (self.encapsulation,
                                                                   self.pe_vid,
                                                                   self.ce_vid))
        else:
            if self.encapsulation == self.l2sub_info.get("flowType"):
                if self.ce_vid:
                    if is_vlan_in_bitmap(self.ce_vid, self.l2sub_info.get("ceVids")) \
                            and self.pe_vid == self.l2sub_info.get("peVlanId"):
                        xml_str = CE_NC_UNSET_ENCAP % self.l2_sub_interface
                        self.updates_cmd.append(
                            "undo encapsulation %s vid %s ce-vid %s" % (self.encapsulation,
                                                                        self.pe_vid,
                                                                        self.ce_vid))
                else:
                    xml_str = CE_NC_UNSET_ENCAP % self.l2_sub_interface
                    self.updates_cmd.append(
                        "undo encapsulation %s" % self.encapsulation)

        if not xml_str:
            self.updates_cmd.pop()
            return
        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "CONFIG_INTF_ENCAP_QINQ")
        self.changed = True

    def config_traffic_encap(self):
        """configure traffic encapsulation types"""

        if not self.l2sub_info:
            self.module.fail_json(msg="Error: Interface %s does not exist." % self.l2_sub_interface)

        if not self.encapsulation:
            return

        xml_str = ""
        if self.encapsulation in ["default", "untag"]:
            if self.state == "present":
                if self.encapsulation != self.l2sub_info.get("flowType"):
                    xml_str = CE_NC_SET_ENCAP % (
                        self.l2_sub_interface, self.encapsulation)
                    self.updates_cmd.append(
                        "interface %s" % self.l2_sub_interface)
                    self.updates_cmd.append(
                        "encapsulation %s" % self.encapsulation)
            else:
                if self.encapsulation == self.l2sub_info.get("flowType"):
                    xml_str = CE_NC_UNSET_ENCAP % self.l2_sub_interface
                    self.updates_cmd.append(
                        "interface %s" % self.l2_sub_interface)
                    self.updates_cmd.append(
                        "undo encapsulation %s" % self.encapsulation)
        elif self.encapsulation == "none":
            if self.state == "present":
                if self.encapsulation != self.l2sub_info.get("flowType"):
                    xml_str = CE_NC_UNSET_ENCAP % self.l2_sub_interface
                    self.updates_cmd.append(
                        "interface %s" % self.l2_sub_interface)
                    self.updates_cmd.append(
                        "undo encapsulation %s" % self.l2sub_info.get("flowType"))
        elif self.encapsulation == "dot1q":
            self.config_traffic_encap_dot1q()
            return
        elif self.encapsulation == "qinq":
            self.config_traffic_encap_qinq()
            return
        else:
            pass

        if not xml_str:
            return
        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "CONFIG_INTF_ENCAP")
        self.changed = True

    def config_vap_sub_intf(self):
        """configure a Layer 2 sub-interface as a service access point"""

        if not self.vap_info:
            self.module.fail_json(msg="Error: Bridge domain %s does not exist." % self.bridge_domain_id)

        xml_str = ""
        if self.state == "present":
            if self.l2_sub_interface not in self.vap_info["intfList"]:
                self.updates_cmd.append("interface %s" % self.l2_sub_interface)
                self.updates_cmd.append("bridge-domain %s" %
                                        self.bridge_domain_id)
                xml_str = CE_NC_MERGE_BD_INTF % (
                    self.bridge_domain_id, self.l2_sub_interface)
        else:
            if self.l2_sub_interface in self.vap_info["intfList"]:
                self.updates_cmd.append("interface %s" % self.l2_sub_interface)
                self.updates_cmd.append(
                    "undo bridge-domain %s" % self.bridge_domain_id)
                xml_str = CE_NC_DELETE_BD_INTF % (
                    self.bridge_domain_id, self.l2_sub_interface)

        if not xml_str:
            return
        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "CONFIG_VAP_SUB_INTERFACE")
        self.changed = True

    def config_vap_vlan(self):
        """configure a VLAN as a service access point"""

        if not self.vap_info:
            self.module.fail_json(msg="Error: Bridge domain %s does not exist." % self.bridge_domain_id)

        xml_str = ""
        if self.state == "present":
            if not is_vlan_in_bitmap(self.bind_vlan_id, self.vap_info["vlanList"]):
                self.updates_cmd.append("bridge-domain %s" %
                                        self.bridge_domain_id)
                self.updates_cmd.append(
                    "l2 binding vlan %s" % self.bind_vlan_id)
                vlan_bitmap = vlan_vid_to_bitmap(self.bind_vlan_id)
                xml_str = CE_NC_MERGE_BD_VLAN % (
                    self.bridge_domain_id, vlan_bitmap, vlan_bitmap)
        else:
            if is_vlan_in_bitmap(self.bind_vlan_id, self.vap_info["vlanList"]):
                self.updates_cmd.append("bridge-domain %s" %
                                        self.bridge_domain_id)
                self.updates_cmd.append(
                    "undo l2 binding vlan %s" % self.bind_vlan_id)
                vlan_bitmap = vlan_vid_to_bitmap(self.bind_vlan_id)
                xml_str = CE_NC_MERGE_BD_VLAN % (
                    self.bridge_domain_id, "0" * 1024, vlan_bitmap)

        if not xml_str:
            return
        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "CONFIG_VAP_VLAN")
        self.changed = True

    def is_vlan_valid(self, vid, name):
        """check VLAN id"""

        if not vid:
            return

        if not vid.isdigit():
            self.module.fail_json(msg="Error: %s is not digit." % name)
            return

        if int(vid) < 1 or int(vid) > 4094:
            self.module.fail_json(
                msg="Error: %s is not in the range from 1 to 4094." % name)

    def is_l2_sub_intf_valid(self, ifname):
        """check l2 sub interface valid"""

        if ifname.count('.') != 1:
            return False

        if_num = ifname.split('.')[1]
        if not if_num.isdigit():
            return False

        if int(if_num) < 1 or int(if_num) > 4096:
            self.module.fail_json(
                msg="Error: Sub-interface number is not in the range from 1 to 4096.")
            return False

        if not get_interface_type(ifname):
            return False

        return True

    def check_params(self):
        """Check all input params"""

        # bridge domain id check
        if self.bridge_domain_id:
            if not self.bridge_domain_id.isdigit():
                self.module.fail_json(
                    msg="Error: Bridge domain id is not digit.")
            if int(self.bridge_domain_id) < 1 or int(self.bridge_domain_id) > 16777215:
                self.module.fail_json(
                    msg="Error: Bridge domain id is not in the range from 1 to 16777215.")

        # check bind_vlan_id
        if self.bind_vlan_id:
            self.is_vlan_valid(self.bind_vlan_id, "bind_vlan_id")

        # check l2_sub_interface
        if self.l2_sub_interface and not self.is_l2_sub_intf_valid(self.l2_sub_interface):
            self.module.fail_json(msg="Error: l2_sub_interface is invalid.")

        # check ce_vid
        if self.ce_vid:
            self.is_vlan_valid(self.ce_vid, "ce_vid")
            if not self.encapsulation or self.encapsulation not in ["dot1q", "qinq"]:
                self.module.fail_json(msg="Error: ce_vid can not be set "
                                          "when encapsulation is '%s'." % self.encapsulation)
            if self.encapsulation == "qinq" and not self.pe_vid:
                self.module.fail_json(msg="Error: ce_vid and pe_vid must be set at the same time "
                                          "when encapsulation is '%s'." % self.encapsulation)
        # check pe_vid
        if self.pe_vid:
            self.is_vlan_valid(self.pe_vid, "pe_vid")
            if not self.encapsulation or self.encapsulation != "qinq":
                self.module.fail_json(msg="Error: pe_vid can not be set "
                                          "when encapsulation is '%s'." % self.encapsulation)
            if not self.ce_vid:
                self.module.fail_json(msg="Error: ce_vid and pe_vid must be set at the same time "
                                          "when encapsulation is '%s'." % self.encapsulation)

    def get_proposed(self):
        """get proposed info"""

        if self.bridge_domain_id:
            self.proposed["bridge_domain_id"] = self.bridge_domain_id
        if self.bind_vlan_id:
            self.proposed["bind_vlan_id"] = self.bind_vlan_id
        if self.l2_sub_interface:
            self.proposed["l2_sub_interface"] = self.l2_sub_interface
        if self.encapsulation:
            self.proposed["encapsulation"] = self.encapsulation
        if self.ce_vid:
            self.proposed["ce_vid"] = self.ce_vid
        if self.pe_vid:
            self.proposed["pe_vid"] = self.pe_vid
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if self.bridge_domain_id:
            if self.bind_vlan_id or self.l2_sub_interface:
                self.existing["bridge_domain_id"] = self.bridge_domain_id
                self.existing["bind_vlan_list"] = bitmap_to_vlan_list(
                    self.vap_info.get("vlanList"))
                self.existing["bind_intf_list"] = self.vap_info.get("intfList")

        if self.encapsulation and self.l2_sub_interface:
            self.existing["l2_sub_interface"] = self.l2_sub_interface
            self.existing["encapsulation"] = self.l2sub_info.get("flowType")
            if self.existing["encapsulation"] == "dot1q":
                self.existing["ce_vid"] = bitmap_to_vlan_list(
                    self.l2sub_info.get("dot1qVids"))
            if self.existing["encapsulation"] == "qinq":
                self.existing["ce_vid"] = bitmap_to_vlan_list(
                    self.l2sub_info.get("ceVids"))
                self.existing["pe_vid"] = self.l2sub_info.get("peVlanId")

    def get_end_state(self):
        """get end state info"""

        if self.bridge_domain_id:
            if self.bind_vlan_id or self.l2_sub_interface:
                vap_info = self.get_bd_vap_dict()
                self.end_state["bridge_domain_id"] = self.bridge_domain_id
                self.end_state["bind_vlan_list"] = bitmap_to_vlan_list(
                    vap_info.get("vlanList"))
                self.end_state["bind_intf_list"] = vap_info.get("intfList")

        if self.encapsulation and self.l2_sub_interface:
            l2sub_info = self.get_l2_sub_intf_dict(self.l2_sub_interface)
            self.end_state["l2_sub_interface"] = self.l2_sub_interface
            self.end_state["encapsulation"] = l2sub_info.get("flowType")
            if self.end_state["encapsulation"] == "dot1q":
                self.end_state["ce_vid"] = bitmap_to_vlan_list(
                    l2sub_info.get("dot1qVids"))
            if self.end_state["encapsulation"] == "qinq":
                self.end_state["ce_vid"] = bitmap_to_vlan_list(
                    l2sub_info.get("ceVids"))
                self.end_state["pe_vid"] = l2sub_info.get("peVlanId")

    def data_init(self):
        """data init"""
        if self.l2_sub_interface:
            self.l2_sub_interface = self.l2_sub_interface.replace(
                " ", "").upper()
        if self.encapsulation and self.l2_sub_interface:
            self.l2sub_info = self.get_l2_sub_intf_dict(self.l2_sub_interface)
        if self.bridge_domain_id:
            if self.bind_vlan_id or self.l2_sub_interface:
                self.vap_info = self.get_bd_vap_dict()

    def work(self):
        """worker"""

        self.check_params()
        self.data_init()
        self.get_existing()
        self.get_proposed()

        # Traffic encapsulation types
        if self.encapsulation and self.l2_sub_interface:
            self.config_traffic_encap()

        # A VXLAN service access point can be a Layer 2 sub-interface or VLAN
        if self.bridge_domain_id:
            if self.l2_sub_interface:
                # configure a Layer 2 sub-interface as a service access point
                self.config_vap_sub_intf()

            if self.bind_vlan_id:
                # configure a VLAN as a service access point
                self.config_vap_vlan()
        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()
        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        bridge_domain_id=dict(required=False, type='str'),
        bind_vlan_id=dict(required=False, type='str'),
        l2_sub_interface=dict(required=False, type='str'),
        encapsulation=dict(required=False, type='str',
                           choices=['dot1q', 'default', 'untag', 'qinq', 'none']),
        ce_vid=dict(required=False, type='str'),
        pe_vid=dict(required=False, type='str'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )
    argument_spec.update(ce_argument_spec)
    module = VxlanVap(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
