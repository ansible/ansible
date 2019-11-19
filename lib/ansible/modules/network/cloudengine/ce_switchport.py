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

DOCUMENTATION = '''
---
module: ce_switchport
version_added: "2.4"
short_description: Manages Layer 2 switchport interfaces on HUAWEI CloudEngine switches.
description:
    - Manages Layer 2 switchport interfaces on HUAWEI CloudEngine switches.
author: QijunPan (@QijunPan)
notes:
    - When C(state=absent), VLANs can be added/removed from trunk links and
      the existing access VLAN can be 'unconfigured' to just having VLAN 1 on that interface.
    - When working with trunks VLANs the keywords add/remove are always sent
      in the C(port trunk allow-pass vlan) command. Use verbose mode to see commands sent.
    - When C(state=unconfigured), the interface will result with having a default Layer 2 interface, i.e. vlan 1 in access mode.
    - This module requires the netconf system service be enabled on the remote device being managed.
    - Recommended connection is C(netconf).
    - This module also works with C(local) connections for legacy playbooks.
options:
    interface:
        description:
            - Full name of the interface, i.e. 40GE1/0/22.
        required: true
    mode:
        description:
            - The link type of an interface.
        choices: ['access','trunk']
    access_vlan:
        description:
            - If C(mode=access), used as the access VLAN ID, in the range from 1 to 4094.
    native_vlan:
        description:
            - If C(mode=trunk), used as the trunk native VLAN ID, in the range from 1 to 4094.
    trunk_vlans:
        description:
            - If C(mode=trunk), used as the VLAN range to ADD or REMOVE
              from the trunk, such as 2-10 or 2,5,10-15, etc.
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present', 'absent', 'unconfigured']
'''

EXAMPLES = '''
- name: switchport module test
  hosts: cloudengine
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
  - name: Ensure 10GE1/0/22 is in its default switchport state
    ce_switchport:
      interface: 10GE1/0/22
      state: unconfigured
      provider: '{{ cli }}'

  - name: Ensure 10GE1/0/22 is configured for access vlan 20
    ce_switchport:
      interface: 10GE1/0/22
      mode: access
      access_vlan: 20
      provider: '{{ cli }}'

  - name: Ensure 10GE1/0/22 only has vlans 5-10 as trunk vlans
    ce_switchport:
      interface: 10GE1/0/22
      mode: trunk
      native_vlan: 10
      trunk_vlans: 5-10
      provider: '{{ cli }}'

  - name: Ensure 10GE1/0/22 is a trunk port and ensure 2-50 are being tagged (doesn't mean others aren't also being tagged)
    ce_switchport:
      interface: 10GE1/0/22
      mode: trunk
      native_vlan: 10
      trunk_vlans: 2-50
      provider: '{{ cli }}'

  - name: Ensure these VLANs are not being tagged on the trunk
    ce_switchport:
      interface: 10GE1/0/22
      mode: trunk
      trunk_vlans: 51-4000
      state: absent
      provider: '{{ cli }}'
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"access_vlan": "20", "interface": "10GE1/0/22", "mode": "access"}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: {"access_vlan": "10", "interface": "10GE1/0/22",
             "mode": "access", "switchport": "enable"}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: {"access_vlan": "20", "interface": "10GE1/0/22",
             "mode": "access", "switchport": "enable"}
updates:
    description: command string sent to the device
    returned: always
    type: list
    sample: ["10GE1/0/22", "port default vlan 20"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec

CE_NC_GET_INTF = """
<filter type="subtree">
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <isL2SwitchPort></isL2SwitchPort>
      </interface>
    </interfaces>
  </ifm>
</filter>
"""

CE_NC_GET_PORT_ATTR = """
<filter type="subtree">
  <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ethernetIfs>
      <ethernetIf>
        <ifName>%s</ifName>
        <l2Enable></l2Enable>
        <l2Attribute>
          <linkType></linkType>
          <pvid></pvid>
          <trunkVlans></trunkVlans>
        </l2Attribute>
      </ethernetIf>
    </ethernetIfs>
  </ethernet>
</filter>
"""

CE_NC_SET_ACCESS_PORT = """
<config>
   <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ethernetIfs>
        <ethernetIf operation="merge">
            <ifName>%s</ifName>
            <l2Attribute>
                <linkType>access</linkType>
                <pvid>%s</pvid>
                <trunkVlans></trunkVlans>
                <untagVlans></untagVlans>
            </l2Attribute>
        </ethernetIf>
    </ethernetIfs>
  </ethernet>
</config>
"""

CE_NC_SET_TRUNK_PORT_MODE = """
<ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<ethernetIfs>
    <ethernetIf operation="merge">
        <ifName>%s</ifName>
        <l2Attribute>
            <linkType>trunk</linkType>
        </l2Attribute>
    </ethernetIf>
</ethernetIfs>
</ethernet>
"""

CE_NC_SET_TRUNK_PORT_PVID = """
<ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<ethernetIfs>
    <ethernetIf operation="merge">
        <ifName>%s</ifName>
        <l2Attribute>
            <linkType>trunk</linkType>
            <pvid>%s</pvid>
            <untagVlans></untagVlans>
        </l2Attribute>
    </ethernetIf>
</ethernetIfs>
</ethernet>
"""

CE_NC_SET_TRUNK_PORT_VLANS = """
<ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<ethernetIfs>
    <ethernetIf operation="merge">
        <ifName>%s</ifName>
        <l2Attribute>
            <linkType>trunk</linkType>
            <trunkVlans>%s:%s</trunkVlans>
            <untagVlans></untagVlans>
        </l2Attribute>
    </ethernetIf>
</ethernetIfs>
</ethernet>
"""

CE_NC_SET_DEFAULT_PORT = """
<config>
   <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ethernetIfs>
        <ethernetIf operation="merge">
            <ifName>%s</ifName>
            <l2Attribute>
                <linkType>access</linkType>
                <pvid>1</pvid>
                <trunkVlans></trunkVlans>
                <untagVlans></untagVlans>
            </l2Attribute>
        </ethernetIf>
    </ethernetIfs>
  </ethernet>
</config>
"""


SWITCH_PORT_TYPE = ('ge', '10ge', '25ge',
                    '4x10ge', '40ge', '100ge', 'eth-trunk')


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
        iftype = 'stack-port'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None

    return iftype.lower()


def is_portswitch_enalbed(iftype):
    """"[undo] portswitch"""

    return bool(iftype in SWITCH_PORT_TYPE)


def vlan_bitmap_undo(bitmap):
    """convert vlan bitmap to undo bitmap"""

    vlan_bit = ['F'] * 1024

    if not bitmap or len(bitmap) == 0:
        return ''.join(vlan_bit)

    bit_len = len(bitmap)
    for num in range(bit_len):
        undo = (~int(bitmap[num], 16)) & 0xF
        vlan_bit[num] = hex(undo)[2]

    return ''.join(vlan_bit)


def is_vlan_bitmap_empty(bitmap):
    """check vlan bitmap empty"""

    if not bitmap or len(bitmap) == 0:
        return True

    bit_len = len(bitmap)
    for num in range(bit_len):
        if bitmap[num] != '0':
            return False

    return True


class SwitchPort(object):
    """
    Manages Layer 2 switchport interfaces.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # interface and vlan info
        self.interface = self.module.params['interface']
        self.mode = self.module.params['mode']
        self.state = self.module.params['state']
        self.access_vlan = self.module.params['access_vlan']
        self.native_vlan = self.module.params['native_vlan']
        self.trunk_vlans = self.module.params['trunk_vlans']

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()
        self.intf_info = dict()         # interface vlan info
        self.intf_type = None           # loopback tunnel ...

    def init_module(self):
        """ init module """

        required_if = [('state', 'absent', ['mode']), ('state', 'present', ['mode'])]
        self.module = AnsibleModule(
            argument_spec=self.spec, required_if=required_if, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_interface_dict(self, ifname):
        """ get one interface attributes dict."""

        intf_info = dict()
        conf_str = CE_NC_GET_PORT_ATTR % ifname
        rcv_xml = get_nc_config(self.module, conf_str)
        if "<data/>" in rcv_xml:
            return intf_info

        intf = re.findall(
            r'.*<ifName>(.*)</ifName>.*\s*<l2Enable>(.*)</l2Enable>.*', rcv_xml)
        if intf:
            intf_info = dict(ifName=intf[0][0],
                             l2Enable=intf[0][1],
                             linkType="",
                             pvid="",
                             trunkVlans="")
            if intf_info["l2Enable"] == "enable":
                attr = re.findall(
                    r'.*<linkType>(.*)</linkType>.*.*\s*<pvid>(.*)'
                    r'</pvid>.*\s*<trunkVlans>(.*)</trunkVlans>.*', rcv_xml)
                if attr:
                    intf_info["linkType"] = attr[0][0]
                    intf_info["pvid"] = attr[0][1]
                    intf_info["trunkVlans"] = attr[0][2]

        return intf_info

    def is_l2switchport(self):
        """Check layer2 switch port"""

        return bool(self.intf_info["l2Enable"] == "enable")

    def merge_access_vlan(self, ifname, access_vlan):
        """Merge access interface vlan"""

        change = False
        conf_str = ""
        self.updates_cmd.append("interface %s" % ifname)
        if self.state == "present":
            if self.intf_info["linkType"] == "access":
                if access_vlan and self.intf_info["pvid"] != access_vlan:
                    self.updates_cmd.append(
                        "port default vlan %s" % access_vlan)
                    conf_str = CE_NC_SET_ACCESS_PORT % (ifname, access_vlan)
                    change = True
            else:  # not access
                self.updates_cmd.append("port link-type access")
                if access_vlan:
                    self.updates_cmd.append(
                        "port default vlan %s" % access_vlan)
                    conf_str = CE_NC_SET_ACCESS_PORT % (ifname, access_vlan)
                else:
                    conf_str = CE_NC_SET_ACCESS_PORT % (ifname, "1")
                change = True
        elif self.state == "absent":
            if self.intf_info["linkType"] == "access":
                if access_vlan and self.intf_info["pvid"] == access_vlan and access_vlan != "1":
                    self.updates_cmd.append(
                        "undo port default vlan %s" % access_vlan)
                    conf_str = CE_NC_SET_ACCESS_PORT % (ifname, "1")
                    change = True
            else:  # not access
                self.updates_cmd.append("port link-type access")
                conf_str = CE_NC_SET_ACCESS_PORT % (ifname, "1")
                change = True

        if not change:
            self.updates_cmd.pop()   # remove interface
            return

        rcv_xml = set_nc_config(self.module, conf_str)
        self.check_response(rcv_xml, "MERGE_ACCESS_PORT")
        self.changed = True

    def merge_trunk_vlan(self, ifname, native_vlan, trunk_vlans):
        """Merge trunk interface vlan"""

        change = False
        xmlstr = ""
        self.updates_cmd.append("interface %s" % ifname)
        if trunk_vlans:
            vlan_list = self.vlan_range_to_list(trunk_vlans)
            vlan_map = self.vlan_list_to_bitmap(vlan_list)

        if self.state == "present":
            if self.intf_info["linkType"] == "trunk":
                if native_vlan and self.intf_info["pvid"] != native_vlan:
                    self.updates_cmd.append(
                        "port trunk pvid vlan %s" % native_vlan)
                    xmlstr += CE_NC_SET_TRUNK_PORT_PVID % (ifname, native_vlan)
                    change = True
                if trunk_vlans:
                    add_vlans = self.vlan_bitmap_add(
                        self.intf_info["trunkVlans"], vlan_map)
                    if not is_vlan_bitmap_empty(add_vlans):
                        self.updates_cmd.append(
                            "port trunk allow-pass %s"
                            % trunk_vlans.replace(',', ' ').replace('-', ' to '))
                        xmlstr += CE_NC_SET_TRUNK_PORT_VLANS % (
                            ifname, add_vlans, add_vlans)
                        change = True
            else:   # not trunk
                self.updates_cmd.append("port link-type trunk")
                change = True
                if native_vlan:
                    self.updates_cmd.append(
                        "port trunk pvid vlan %s" % native_vlan)
                    xmlstr += CE_NC_SET_TRUNK_PORT_PVID % (ifname, native_vlan)
                if trunk_vlans:
                    self.updates_cmd.append(
                        "port trunk allow-pass %s"
                        % trunk_vlans.replace(',', ' ').replace('-', ' to '))
                    xmlstr += CE_NC_SET_TRUNK_PORT_VLANS % (
                        ifname, vlan_map, vlan_map)
                if not native_vlan and not trunk_vlans:
                    xmlstr += CE_NC_SET_TRUNK_PORT_MODE % ifname
                    self.updates_cmd.append(
                        "undo port trunk allow-pass vlan 1")
        elif self.state == "absent":
            if self.intf_info["linkType"] == "trunk":
                if native_vlan and self.intf_info["pvid"] == native_vlan and native_vlan != '1':
                    self.updates_cmd.append(
                        "undo port trunk pvid vlan %s" % native_vlan)
                    xmlstr += CE_NC_SET_TRUNK_PORT_PVID % (ifname, 1)
                    change = True
                if trunk_vlans:
                    del_vlans = self.vlan_bitmap_del(
                        self.intf_info["trunkVlans"], vlan_map)
                    if not is_vlan_bitmap_empty(del_vlans):
                        self.updates_cmd.append(
                            "undo port trunk allow-pass %s"
                            % trunk_vlans.replace(',', ' ').replace('-', ' to '))
                        undo_map = vlan_bitmap_undo(del_vlans)
                        xmlstr += CE_NC_SET_TRUNK_PORT_VLANS % (
                            ifname, undo_map, del_vlans)
                        change = True
            else:   # not trunk
                self.updates_cmd.append("port link-type trunk")
                self.updates_cmd.append("undo port trunk allow-pass vlan 1")
                xmlstr += CE_NC_SET_TRUNK_PORT_MODE % ifname
                change = True

        if not change:
            self.updates_cmd.pop()
            return

        conf_str = "<config>" + xmlstr + "</config>"
        rcv_xml = set_nc_config(self.module, conf_str)
        self.check_response(rcv_xml, "MERGE_TRUNK_PORT")
        self.changed = True

    def default_switchport(self, ifname):
        """Set interface default or unconfigured"""

        change = False
        if self.intf_info["linkType"] != "access":
            self.updates_cmd.append("interface %s" % ifname)
            self.updates_cmd.append("port link-type access")
            self.updates_cmd.append("port default vlan 1")
            change = True
        else:
            if self.intf_info["pvid"] != "1":
                self.updates_cmd.append("interface %s" % ifname)
                self.updates_cmd.append("port default vlan 1")
                change = True

        if not change:
            return

        conf_str = CE_NC_SET_DEFAULT_PORT % ifname
        rcv_xml = set_nc_config(self.module, conf_str)
        self.check_response(rcv_xml, "DEFAULT_INTF_VLAN")
        self.changed = True

    def vlan_series(self, vlanid_s):
        """ convert vlan range to vlan list """

        vlan_list = []
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

    def vlan_range_to_list(self, vlan_range):
        """ convert vlan range to vlan list """

        vlan_list = self.vlan_region(vlan_range.split(','))

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
            vlan_bit[j] = hex(bit_int[j])[2]

        vlan_xml = ''.join(vlan_bit)

        return vlan_xml

    def vlan_bitmap_add(self, oldmap, newmap):
        """vlan add bitmap"""

        vlan_bit = ['0'] * 1024

        if len(newmap) != 1024:
            self.module.fail_json(msg='Error: New vlan bitmap is invalid.')

        if len(oldmap) != 1024 and len(oldmap) != 0:
            self.module.fail_json(msg='Error: old vlan bitmap is invalid.')

        if len(oldmap) == 0:
            return newmap

        for num in range(1024):
            new_tmp = int(newmap[num], 16)
            old_tmp = int(oldmap[num], 16)
            add = (~(new_tmp & old_tmp)) & new_tmp
            vlan_bit[num] = hex(add)[2]

        vlan_xml = ''.join(vlan_bit)

        return vlan_xml

    def vlan_bitmap_del(self, oldmap, delmap):
        """vlan del bitmap"""

        vlan_bit = ['0'] * 1024

        if not oldmap or len(oldmap) == 0:
            return ''.join(vlan_bit)

        if len(oldmap) != 1024 or len(delmap) != 1024:
            self.module.fail_json(msg='Error: vlan bitmap is invalid.')

        for num in range(1024):
            tmp = int(delmap[num], 16) & int(oldmap[num], 16)
            vlan_bit[num] = hex(tmp)[2]

        vlan_xml = ''.join(vlan_bit)

        return vlan_xml

    def check_params(self):
        """Check all input params"""

        # interface type check
        if self.interface:
            self.intf_type = get_interface_type(self.interface)
            if not self.intf_type:
                self.module.fail_json(
                    msg='Error: Interface name of %s is error.' % self.interface)

        if not self.intf_type or not is_portswitch_enalbed(self.intf_type):
            self.module.fail_json(msg='Error: Interface %s is error.')

        # check access_vlan
        if self.access_vlan:
            if not self.access_vlan.isdigit():
                self.module.fail_json(msg='Error: Access vlan id is invalid.')
            if int(self.access_vlan) <= 0 or int(self.access_vlan) > 4094:
                self.module.fail_json(
                    msg='Error: Access vlan id is not in the range from 1 to 4094.')

        # check native_vlan
        if self.native_vlan:
            if not self.native_vlan.isdigit():
                self.module.fail_json(msg='Error: Native vlan id is invalid.')
            if int(self.native_vlan) <= 0 or int(self.native_vlan) > 4094:
                self.module.fail_json(
                    msg='Error: Native vlan id is not in the range from 1 to 4094.')

        # get interface info
        self.intf_info = self.get_interface_dict(self.interface)
        if not self.intf_info:
            self.module.fail_json(msg='Error: Interface does not exist.')

        if not self.is_l2switchport():
            self.module.fail_json(
                msg='Error: Interface is not layer2 switch port.')

    def get_proposed(self):
        """get proposed info"""

        self.proposed['state'] = self.state
        self.proposed['interface'] = self.interface
        self.proposed['mode'] = self.mode
        self.proposed['access_vlan'] = self.access_vlan
        self.proposed['native_vlan'] = self.native_vlan
        self.proposed['trunk_vlans'] = self.trunk_vlans

    def get_existing(self):
        """get existing info"""

        if self.intf_info:
            self.existing["interface"] = self.intf_info["ifName"]
            self.existing["mode"] = self.intf_info["linkType"]
            self.existing["switchport"] = self.intf_info["l2Enable"]
            self.existing['access_vlan'] = self.intf_info["pvid"]
            self.existing['native_vlan'] = self.intf_info["pvid"]
            self.existing['trunk_vlans'] = self.intf_info["trunkVlans"]

    def get_end_state(self):
        """get end state info"""

        if self.intf_info:
            end_info = self.get_interface_dict(self.interface)
            if end_info:
                self.end_state["interface"] = end_info["ifName"]
                self.end_state["mode"] = end_info["linkType"]
                self.end_state["switchport"] = end_info["l2Enable"]
                self.end_state['access_vlan'] = end_info["pvid"]
                self.end_state['native_vlan'] = end_info["pvid"]
                self.end_state['trunk_vlans'] = end_info["trunkVlans"]

    def work(self):
        """worker"""

        self.check_params()
        if not self.intf_info:
            self.module.fail_json(msg='Error: interface does not exist.')

        self.get_existing()
        self.get_proposed()

        # present or absent
        if self.state == "present" or self.state == "absent":
            if self.mode == "access":
                self.merge_access_vlan(self.interface, self.access_vlan)
            elif self.mode == "trunk":
                self.merge_trunk_vlan(
                    self.interface, self.native_vlan, self.trunk_vlans)
        # unconfigured
        else:
            self.default_switchport(self.interface)

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
        interface=dict(required=True, type='str'),
        mode=dict(choices=['access', 'trunk'], required=False),
        access_vlan=dict(type='str', required=False),
        native_vlan=dict(type='str', required=False),
        trunk_vlans=dict(type='str', required=False),
        state=dict(choices=['absent', 'present', 'unconfigured'],
                   default='present')
    )

    argument_spec.update(ce_argument_spec)
    switchport = SwitchPort(argument_spec)
    switchport.work()


if __name__ == '__main__':
    main()
