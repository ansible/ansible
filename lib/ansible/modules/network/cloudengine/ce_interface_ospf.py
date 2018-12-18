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
module: ce_interface_ospf
version_added: "2.4"
short_description: Manages configuration of an OSPF interface instanceon HUAWEI CloudEngine switches.
description:
    - Manages configuration of an OSPF interface instanceon HUAWEI CloudEngine switches.
author: QijunPan (@QijunPan)
options:
    interface:
        description:
            - Full name of interface, i.e. 40GE1/0/10.
        required: true
    process_id:
        description:
            - Specifies a process ID.
              The value is an integer ranging from 1 to 4294967295.
        required: true
    area:
        description:
            - Ospf area associated with this ospf process.
              Valid values are a string, formatted as an IP address
              (i.e. "0.0.0.0") or as an integer between 1 and 4294967295.
        required: true
    cost:
        description:
            - The cost associated with this interface.
              Valid values are an integer in the range from 1 to 65535.
    hello_interval:
        description:
            - Time between sending successive hello packets.
              Valid values are an integer in the range from 1 to 65535.
    dead_interval:
        description:
            - Time interval an ospf neighbor waits for a hello
              packet before tearing down adjacencies. Valid values are an
              integer in the range from 1 to 235926000.
    silent_interface:
        description:
            - Setting to true will prevent this interface from receiving
              HELLO packets. Valid values are 'true' and 'false'.
        type: bool
        default: 'no'
    auth_mode:
        description:
            - Specifies the authentication type.
        choices: ['none', 'null', 'hmac-sha256', 'md5', 'hmac-md5', 'simple']
    auth_text_simple:
        description:
            - Specifies a password for simple authentication.
              The value is a string of 1 to 8 characters.
    auth_key_id:
        description:
            - Authentication key id when C(auth_mode) is 'hmac-sha256', 'md5' or 'hmac-md5.
              Valid value is an integer is in the range from 1 to 255.
    auth_text_md5:
        description:
            - Specifies a password for MD5, HMAC-MD5, or HMAC-SHA256 authentication.
              The value is a string of 1 to 255 case-sensitive characters, spaces not supported.
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        default: present
        choices: ['present','absent']
"""

EXAMPLES = '''
- name: eth_trunk module test
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
  - name: Enables OSPF and sets the cost on an interface
    ce_interface_ospf:
      interface: 10GE1/0/30
      process_id: 1
      area: 100
      cost: 100
      provider: '{{ cli }}'

  - name: Sets the dead interval of the OSPF neighbor
    ce_interface_ospf:
      interface: 10GE1/0/30
      process_id: 1
      area: 100
      dead_interval: 100
      provider: '{{ cli }}'

  - name: Sets the interval for sending Hello packets on an interface
    ce_interface_ospf:
      interface: 10GE1/0/30
      process_id: 1
      area: 100
      hello_interval: 2
      provider: '{{ cli }}'

  - name: Disables an interface from receiving and sending OSPF packets
    ce_interface_ospf:
      interface: 10GE1/0/30
      process_id: 1
      area: 100
      silent_interface: true
      provider: '{{ cli }}'
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"process_id": "1", "area": "0.0.0.100", "interface": "10GE1/0/30", "cost": "100"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"process_id": "1", "area": "0.0.0.100"}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"process_id": "1", "area": "0.0.0.100", "interface": "10GE1/0/30",
             "cost": "100", "dead_interval": "40", "hello_interval": "10",
             "silent_interface": "false", "auth_mode": "none"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface 10GE1/0/30",
             "ospf enable 1 area 0.0.0.100",
             "ospf cost 100"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec

CE_NC_GET_OSPF = """
    <filter type="subtree">
      <ospfv2 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <ospfv2comm>
          <ospfSites>
            <ospfSite>
              <processId>%s</processId>
              <routerId></routerId>
              <vrfName></vrfName>
              <areas>
                <area>
                  <areaId>%s</areaId>
                  <interfaces>
                    <interface>
                      <ifName>%s</ifName>
                      <networkType></networkType>
                      <helloInterval></helloInterval>
                      <deadInterval></deadInterval>
                      <silentEnable></silentEnable>
                      <configCost></configCost>
                      <authenticationMode></authenticationMode>
                      <authTextSimple></authTextSimple>
                      <keyId></keyId>
                      <authTextMd5></authTextMd5>
                    </interface>
                  </interfaces>
                </area>
              </areas>
            </ospfSite>
          </ospfSites>
        </ospfv2comm>
      </ospfv2>
    </filter>
"""

CE_NC_XML_BUILD_PROCESS = """
    <config>
      <ospfv2 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <ospfv2comm>
          <ospfSites>
            <ospfSite>
              <processId>%s</processId>
              <areas>
                <area>
                  <areaId>%s</areaId>
                  %s
                </area>
              </areas>
            </ospfSite>
          </ospfSites>
        </ospfv2comm>
      </ospfv2>
    </config>
"""

CE_NC_XML_BUILD_MERGE_INTF = """
                  <interfaces>
                    <interface operation="merge">
                    %s
                    </interface>
                  </interfaces>
"""

CE_NC_XML_BUILD_DELETE_INTF = """
                  <interfaces>
                    <interface operation="delete">
                    %s
                    </interface>
                  </interfaces>
"""
CE_NC_XML_SET_IF_NAME = """
                      <ifName>%s</ifName>
"""

CE_NC_XML_SET_HELLO = """
                      <helloInterval>%s</helloInterval>
"""

CE_NC_XML_SET_DEAD = """
                      <deadInterval>%s</deadInterval>
"""

CE_NC_XML_SET_SILENT = """
                      <silentEnable>%s</silentEnable>
"""

CE_NC_XML_SET_COST = """
                      <configCost>%s</configCost>
"""

CE_NC_XML_SET_AUTH_MODE = """
                      <authenticationMode>%s</authenticationMode>
"""


CE_NC_XML_SET_AUTH_TEXT_SIMPLE = """
                      <authTextSimple>%s</authTextSimple>
"""

CE_NC_XML_SET_AUTH_MD5 = """
                      <keyId>%s</keyId>
                      <authTextMd5>%s</authTextMd5>
"""


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


def is_valid_v4addr(addr):
    """check is ipv4 addr is valid"""

    if not addr:
        return False

    if addr.find('.') != -1:
        addr_list = addr.split('.')
        if len(addr_list) != 4:
            return False
        for each_num in addr_list:
            if not each_num.isdigit():
                return False
            if int(each_num) > 255:
                return False
        return True

    return False


class InterfaceOSPF(object):
    """
    Manages configuration of an OSPF interface instance.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.interface = self.module.params['interface']
        self.process_id = self.module.params['process_id']
        self.area = self.module.params['area']
        self.cost = self.module.params['cost']
        self.hello_interval = self.module.params['hello_interval']
        self.dead_interval = self.module.params['dead_interval']
        self.silent_interface = self.module.params['silent_interface']
        self.auth_mode = self.module.params['auth_mode']
        self.auth_text_simple = self.module.params['auth_text_simple']
        self.auth_key_id = self.module.params['auth_key_id']
        self.auth_text_md5 = self.module.params['auth_text_md5']
        self.state = self.module.params['state']

        # ospf info
        self.ospf_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def netconf_set_config(self, xml_str, xml_name):
        """netconf set config"""

        rcv_xml = set_nc_config(self.module, xml_str)
        if "<ok/>" not in rcv_xml:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_area_ip(self):
        """convert integer to ip address"""

        if not self.area.isdigit():
            return self.area

        addr_int = ['0'] * 4
        addr_int[0] = str(((int(self.area) & 0xFF000000) >> 24) & 0xFF)
        addr_int[1] = str(((int(self.area) & 0x00FF0000) >> 16) & 0xFF)
        addr_int[2] = str(((int(self.area) & 0x0000FF00) >> 8) & 0XFF)
        addr_int[3] = str(int(self.area) & 0xFF)

        return '.'.join(addr_int)

    def get_ospf_dict(self):
        """ get one ospf attributes dict."""

        ospf_info = dict()
        conf_str = CE_NC_GET_OSPF % (
            self.process_id, self.get_area_ip(), self.interface)
        rcv_xml = get_nc_config(self.module, conf_str)

        if "<data/>" in rcv_xml:
            return ospf_info

        xml_str = rcv_xml.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get process base info
        root = ElementTree.fromstring(xml_str)
        ospfsite = root.find("data/ospfv2/ospfv2comm/ospfSites/ospfSite")
        if not ospfsite:
            self.module.fail_json(msg="Error: ospf process does not exist.")

        for site in ospfsite:
            if site.tag in ["processId", "routerId", "vrfName"]:
                ospf_info[site.tag] = site.text

        # get areas info
        ospf_info["areaId"] = ""
        areas = root.find(
            "data/ospfv2/ospfv2comm/ospfSites/ospfSite/areas/area")
        if areas:
            for area in areas:
                if area.tag == "areaId":
                    ospf_info["areaId"] = area.text
                    break

        # get interface info
        ospf_info["interface"] = dict()
        intf = root.find(
            "data/ospfv2/ospfv2comm/ospfSites/ospfSite/areas/area/interfaces/interface")
        if intf:
            for attr in intf:
                if attr.tag in ["ifName", "networkType",
                                "helloInterval", "deadInterval",
                                "silentEnable", "configCost",
                                "authenticationMode", "authTextSimple",
                                "keyId", "authTextMd5"]:
                    ospf_info["interface"][attr.tag] = attr.text

        return ospf_info

    def set_ospf_interface(self):
        """set interface ospf enable, and set its ospf attributes"""

        xml_intf = CE_NC_XML_SET_IF_NAME % self.interface

        # ospf view
        self.updates_cmd.append("ospf %s" % self.process_id)
        self.updates_cmd.append("area %s" % self.get_area_ip())
        if self.silent_interface:
            xml_intf += CE_NC_XML_SET_SILENT % str(self.silent_interface).lower()
            if self.silent_interface:
                self.updates_cmd.append("silent-interface %s" % self.interface)
            else:
                self.updates_cmd.append("undo silent-interface %s" % self.interface)

        # interface view
        self.updates_cmd.append("interface %s" % self.interface)
        self.updates_cmd.append("ospf enable process %s area %s" % (
            self.process_id, self.get_area_ip()))
        if self.cost:
            xml_intf += CE_NC_XML_SET_COST % self.cost
            self.updates_cmd.append("ospf cost %s" % self.cost)
        if self.hello_interval:
            xml_intf += CE_NC_XML_SET_HELLO % self.hello_interval
            self.updates_cmd.append("ospf timer hello %s" %
                                    self.hello_interval)
        if self.dead_interval:
            xml_intf += CE_NC_XML_SET_DEAD % self.dead_interval
            self.updates_cmd.append("ospf timer dead %s" % self.dead_interval)
        if self.auth_mode:
            xml_intf += CE_NC_XML_SET_AUTH_MODE % self.auth_mode
            if self.auth_mode == "none":
                self.updates_cmd.append("undo ospf authentication-mode")
            else:
                self.updates_cmd.append("ospf authentication-mode %s" % self.auth_mode)
            if self.auth_mode == "simple" and self.auth_text_simple:
                xml_intf += CE_NC_XML_SET_AUTH_TEXT_SIMPLE % self.auth_text_simple
                self.updates_cmd.pop()
                self.updates_cmd.append("ospf authentication-mode %s %s"
                                        % (self.auth_mode, self.auth_text_simple))
            elif self.auth_mode in ["hmac-sha256", "md5", "hmac-md5"] and self.auth_key_id:
                xml_intf += CE_NC_XML_SET_AUTH_MD5 % (
                    self.auth_key_id, self.auth_text_md5)
                self.updates_cmd.pop()
                self.updates_cmd.append("ospf authentication-mode %s %s %s"
                                        % (self.auth_mode, self.auth_key_id, self.auth_text_md5))
            else:
                pass

        xml_str = CE_NC_XML_BUILD_PROCESS % (self.process_id,
                                             self.get_area_ip(),
                                             (CE_NC_XML_BUILD_MERGE_INTF % xml_intf))
        self.netconf_set_config(xml_str, "SET_INTERFACE_OSPF")
        self.changed = True

    def merge_ospf_interface(self):
        """merge interface ospf attributes"""

        intf_dict = self.ospf_info["interface"]

        # ospf view
        xml_ospf = ""
        if intf_dict.get("silentEnable") != str(self.silent_interface).lower():
            xml_ospf += CE_NC_XML_SET_SILENT % str(self.silent_interface).lower()
            self.updates_cmd.append("ospf %s" % self.process_id)
            self.updates_cmd.append("area %s" % self.get_area_ip())
            if self.silent_interface:
                self.updates_cmd.append("silent-interface %s" % self.interface)
            else:
                self.updates_cmd.append("undo silent-interface %s" % self.interface)

        # interface view
        xml_intf = ""
        self.updates_cmd.append("interface %s" % self.interface)
        if self.cost and intf_dict.get("configCost") != self.cost:
            xml_intf += CE_NC_XML_SET_COST % self.cost
            self.updates_cmd.append("ospf cost %s" % self.cost)
        if self.hello_interval and intf_dict.get("helloInterval") != self.hello_interval:
            xml_intf += CE_NC_XML_SET_HELLO % self.hello_interval
            self.updates_cmd.append("ospf timer hello %s" %
                                    self.hello_interval)
        if self.dead_interval and intf_dict.get("deadInterval") != self.dead_interval:
            xml_intf += CE_NC_XML_SET_DEAD % self.dead_interval
            self.updates_cmd.append("ospf timer dead %s" % self.dead_interval)
        if self.auth_mode:
            # NOTE: for security, authentication config will always be update
            xml_intf += CE_NC_XML_SET_AUTH_MODE % self.auth_mode
            if self.auth_mode == "none":
                self.updates_cmd.append("undo ospf authentication-mode")
            else:
                self.updates_cmd.append("ospf authentication-mode %s" % self.auth_mode)
            if self.auth_mode == "simple" and self.auth_text_simple:
                xml_intf += CE_NC_XML_SET_AUTH_TEXT_SIMPLE % self.auth_text_simple
                self.updates_cmd.pop()
                self.updates_cmd.append("ospf authentication-mode %s %s"
                                        % (self.auth_mode, self.auth_text_simple))
            elif self.auth_mode in ["hmac-sha256", "md5", "hmac-md5"] and self.auth_key_id:
                xml_intf += CE_NC_XML_SET_AUTH_MD5 % (
                    self.auth_key_id, self.auth_text_md5)
                self.updates_cmd.pop()
                self.updates_cmd.append("ospf authentication-mode %s %s %s"
                                        % (self.auth_mode, self.auth_key_id, self.auth_text_md5))
            else:
                pass
        if not xml_intf:
            self.updates_cmd.pop()  # remove command: interface

        if not xml_ospf and not xml_intf:
            return

        xml_sum = CE_NC_XML_SET_IF_NAME % self.interface
        xml_sum += xml_ospf + xml_intf
        xml_str = CE_NC_XML_BUILD_PROCESS % (self.process_id,
                                             self.get_area_ip(),
                                             (CE_NC_XML_BUILD_MERGE_INTF % xml_sum))
        self.netconf_set_config(xml_str, "MERGE_INTERFACE_OSPF")
        self.changed = True

    def unset_ospf_interface(self):
        """set interface ospf disable, and all its ospf attributes will be removed"""

        intf_dict = self.ospf_info["interface"]
        xml_sum = ""
        xml_intf = CE_NC_XML_SET_IF_NAME % self.interface
        if intf_dict.get("silentEnable") == "true":
            xml_sum += CE_NC_XML_BUILD_MERGE_INTF % (
                xml_intf + (CE_NC_XML_SET_SILENT % "false"))
            self.updates_cmd.append("ospf %s" % self.process_id)
            self.updates_cmd.append("area %s" % self.get_area_ip())
            self.updates_cmd.append(
                "undo silent-interface %s" % self.interface)

        xml_sum += CE_NC_XML_BUILD_DELETE_INTF % xml_intf
        xml_str = CE_NC_XML_BUILD_PROCESS % (self.process_id,
                                             self.get_area_ip(),
                                             xml_sum)
        self.netconf_set_config(xml_str, "DELETE_INTERFACE_OSPF")
        self.updates_cmd.append("undo ospf cost")
        self.updates_cmd.append("undo ospf timer hello")
        self.updates_cmd.append("undo ospf timer dead")
        self.updates_cmd.append("undo ospf authentication-mode")
        self.updates_cmd.append("undo ospf enable %s area %s" % (
            self.process_id, self.get_area_ip()))
        self.changed = True

    def check_params(self):
        """Check all input params"""

        self.interface = self.interface.replace(" ", "").upper()

        # interface check
        if not get_interface_type(self.interface):
            self.module.fail_json(msg="Error: interface is invalid.")

        # process_id check
        if not self.process_id.isdigit():
            self.module.fail_json(msg="Error: process_id is not digit.")
        if int(self.process_id) < 1 or int(self.process_id) > 4294967295:
            self.module.fail_json(msg="Error: process_id must be an integer between 1 and 4294967295.")

        # area check
        if self.area.isdigit():
            if int(self.area) < 0 or int(self.area) > 4294967295:
                self.module.fail_json(msg="Error: area id (Integer) must be between 0 and 4294967295.")
        else:
            if not is_valid_v4addr(self.area):
                self.module.fail_json(msg="Error: area id is invalid.")

        # area authentication check
        if self.state == "present":
            if self.auth_mode:
                if self.auth_mode == "simple":
                    if self.auth_text_simple and len(self.auth_text_simple) > 8:
                        self.module.fail_json(
                            msg="Error: auth_text_simple is not in the range from 1 to 8.")
                if self.auth_mode in ["hmac-sha256", "hmac-sha256", "md5"]:
                    if self.auth_key_id and not self.auth_text_md5:
                        self.module.fail_json(
                            msg='Error: auth_key_id and auth_text_md5 should be set at the same time.')
                    if not self.auth_key_id and self.auth_text_md5:
                        self.module.fail_json(
                            msg='Error: auth_key_id and auth_text_md5 should be set at the same time.')
                    if self.auth_key_id:
                        if not self.auth_key_id.isdigit():
                            self.module.fail_json(
                                msg="Error: auth_key_id is not digit.")
                        if int(self.auth_key_id) < 1 or int(self.auth_key_id) > 255:
                            self.module.fail_json(
                                msg="Error: auth_key_id is not in the range from 1 to 255.")
                    if self.auth_text_md5 and len(self.auth_text_md5) > 255:
                        self.module.fail_json(
                            msg="Error: auth_text_md5 is not in the range from 1 to 255.")
        # cost check
        if self.cost:
            if not self.cost.isdigit():
                self.module.fail_json(msg="Error: cost is not digit.")
            if int(self.cost) < 1 or int(self.cost) > 65535:
                self.module.fail_json(
                    msg="Error: cost is not in the range from 1 to 65535")

        # hello_interval check
        if self.hello_interval:
            if not self.hello_interval.isdigit():
                self.module.fail_json(
                    msg="Error: hello_interval is not digit.")
            if int(self.hello_interval) < 1 or int(self.hello_interval) > 65535:
                self.module.fail_json(
                    msg="Error: hello_interval is not in the range from 1 to 65535")

        # dead_interval check
        if self.dead_interval:
            if not self.dead_interval.isdigit():
                self.module.fail_json(msg="Error: dead_interval is not digit.")
            if int(self.dead_interval) < 1 or int(self.dead_interval) > 235926000:
                self.module.fail_json(
                    msg="Error: dead_interval is not in the range from 1 to 235926000")

    def get_proposed(self):
        """get proposed info"""

        self.proposed["interface"] = self.interface
        self.proposed["process_id"] = self.process_id
        self.proposed["area"] = self.get_area_ip()
        self.proposed["cost"] = self.cost
        self.proposed["hello_interval"] = self.hello_interval
        self.proposed["dead_interval"] = self.dead_interval
        self.proposed["silent_interface"] = self.silent_interface
        if self.auth_mode:
            self.proposed["auth_mode"] = self.auth_mode
            if self.auth_mode == "simple":
                self.proposed["auth_text_simple"] = self.auth_text_simple
            if self.auth_mode in ["hmac-sha256", "hmac-sha256", "md5"]:
                self.proposed["auth_key_id"] = self.auth_key_id
                self.proposed["auth_text_md5"] = self.auth_text_md5
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if not self.ospf_info:
            return

        if self.ospf_info["interface"]:
            self.existing["interface"] = self.interface
            self.existing["cost"] = self.ospf_info["interface"].get("configCost")
            self.existing["hello_interval"] = self.ospf_info["interface"].get("helloInterval")
            self.existing["dead_interval"] = self.ospf_info["interface"].get("deadInterval")
            self.existing["silent_interface"] = self.ospf_info["interface"].get("silentEnable")
            self.existing["auth_mode"] = self.ospf_info["interface"].get("authenticationMode")
            self.existing["auth_text_simple"] = self.ospf_info["interface"].get("authTextSimple")
            self.existing["auth_key_id"] = self.ospf_info["interface"].get("keyId")
            self.existing["auth_text_md5"] = self.ospf_info["interface"].get("authTextMd5")
        self.existing["process_id"] = self.ospf_info["processId"]
        self.existing["area"] = self.ospf_info["areaId"]

    def get_end_state(self):
        """get end state info"""

        ospf_info = self.get_ospf_dict()
        if not ospf_info:
            return

        if ospf_info["interface"]:
            self.end_state["interface"] = self.interface
            self.end_state["cost"] = ospf_info["interface"].get("configCost")
            self.end_state["hello_interval"] = ospf_info["interface"].get("helloInterval")
            self.end_state["dead_interval"] = ospf_info["interface"].get("deadInterval")
            self.end_state["silent_interface"] = ospf_info["interface"].get("silentEnable")
            self.end_state["auth_mode"] = ospf_info["interface"].get("authenticationMode")
            self.end_state["auth_text_simple"] = ospf_info["interface"].get("authTextSimple")
            self.end_state["auth_key_id"] = ospf_info["interface"].get("keyId")
            self.end_state["auth_text_md5"] = ospf_info["interface"].get("authTextMd5")
        self.end_state["process_id"] = ospf_info["processId"]
        self.end_state["area"] = ospf_info["areaId"]

    def work(self):
        """worker"""

        self.check_params()
        self.ospf_info = self.get_ospf_dict()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        if self.state == "present":
            if not self.ospf_info or not self.ospf_info["interface"]:
                # create ospf area and set interface config
                self.set_ospf_interface()
            else:
                # merge interface ospf area config
                self.merge_ospf_interface()
        else:
            if self.ospf_info and self.ospf_info["interface"]:
                # delete interface ospf area config
                self.unset_ospf_interface()

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
        process_id=dict(required=True, type='str'),
        area=dict(required=True, type='str'),
        cost=dict(required=False, type='str'),
        hello_interval=dict(required=False, type='str'),
        dead_interval=dict(required=False, type='str'),
        silent_interface=dict(required=False, default=False, type='bool'),
        auth_mode=dict(required=False,
                       choices=['none', 'null', 'hmac-sha256', 'md5', 'hmac-md5', 'simple'], type='str'),
        auth_text_simple=dict(required=False, type='str', no_log=True),
        auth_key_id=dict(required=False, type='str'),
        auth_text_md5=dict(required=False, type='str', no_log=True),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )

    argument_spec.update(ce_argument_spec)
    module = InterfaceOSPF(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
