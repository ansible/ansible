# -*- coding: utf-8 -*-
# !/usr/bin/python
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
module: ne_interface_ipv6
version_added: "2.6"
short_description: Manages ipv6 configuration of an interface.
description:
    - Manages ipv6 configuration of an interface on HUAWEI netengine routers.
author: Shijiawei (@netengine-Ansible)
notes:
    - Interface must already be a L3 port when using this module.
    - Logical interfaces (loopback, vlanif) must be created first.
    - C(prefix_length) must be inserted in decimal format (i.e. 24) for
      both IPv6 and IPv4.
    - A single interface can have multiple IPv6 configured.
options:
    name:
        description:
            - The textual name of the interface. The value of this object should be the name of the
              interface as assigned by the local device and should be suitable for use in commands
              entered at the device's `console'. This might be a text name, depending on the interface
              naming syntax of the device. The value is a string of 1 to 63 characters.
        required: true
        default: null
    enable:
        description:
            - It is used to control whether an interface is enabled with the IPv6 function.
        required: false
        default: null
        choices: ['true', 'false']
    mtu:
        description:
            - IPv6 maximum transmission unit of an interface.
        required: false
        default: null
    mtu_spread:
        description:
            - Spread the IPv6 MTU of main interface to subinterface.
        required: false
        default: null
        choices: ['true', 'false']
    auto_linklocal:
        description:
            - It is used to control whether an interface is enabled with the auto linklocal address function.
        required: false
        default: null
        choices: ['true', 'false']
    address:
        description:
            - IPv6 address. The total length is 128 bits, which is divided into eight groups. Each
              group contains four hexadecimal digits. The value is in the format of X:X:X:X:X:X:X:X.
              Abbreviations are supported. IPv6 addresses configured on the interfaces of the same
              device must belong to different network segments. An interface supports a maximum of 16
              global unicast addresses. A link-local address must be prefixed with FE80::/10.
        required: false
        default: null
    prefix_length:
        description:
            - Length of the IPv6 address prefix. The value is an integer ranging from 1 to 128. The
              value cannot be greater than 64 for CGA and EUI-64 addresses.
        required: false
        default: null
    address_type:
        description:
            - IPv6 address type.
              global: Global unicast address.
              link-local: Link local address.
              anycast: Anycast address.
        required: false
        default: null
        choices: ['global', 'link-local', 'anycast']
    id_gen_type:
        description:
            - Address algorithm.
              none: None.
              cga: Cryptographically generated address.
              eui64: 64-bit extended unique identifier.
        required: false
        default: null
        choices: ['none', 'cga', 'eui64']
    rsa_key_label:
        description:
            - RSA key. The value is a string of 1 to 35 case-sensitive characters, spaces not supported.
        required: false
        default: null
    sec_level:
        description:
            - Security level. The value is an integer ranging from 0 to 1. 1 represent the highest
              security level. If the security level is set to 1, the system automatically generates
              a correction value, which can be configured manually when the security level is set to 0.
        required: false
        default: null
    modifier:
        description:
            - CGA address modifier. The value is in the IPv6 address format. The total length is 128 bits,
              which is divided into eight groups. Each group contains four hexadecimal digits. The value
              is in the format of X:X:X:X:X:X:X:X. Abbreviations are supported.
        required: false
        default: null
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present', 'absent', 'query']
'''

EXAMPLES = '''
- name: interface_ipv6 module test
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
  - name: Config interface ipv6 enable and create ipv6 address
    ne_interface_ipv6:
      name: GigabitEthernet2/0/0
      enable: true
      address: 2001:db8::
      prefix_length: 32
      address_type: anycast
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"address": "2001:db8::",
             "address_type": "anycast",
             "enable": "true",
             "name": "GigabitEthernet2/0/0",
             "prefix_length": 32,
             "state": "present"}
existing:
    description: k/v pairs of existing interface
    returned: always
    type: dict
    sample: {"auto_linklocal": "false",
             "enable": "false",
             "ipv6_addr": [],
             "mtu_spread": "false",
             "name": "GigabitEthernet2/0/0"}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"auto_linklocal": "false",
             "enable": "true",
             "ipv6_addr": [
                 {
                     "address": "2001:DB8::",
                     "address_type": "anycast",
                     "id_gen_type": "none",
                     "prefix_length": "32"
                 }
             ],
             "mtu": "1500",
             "mtu_spread": "false",
             "name": "GigabitEthernet2/0/0"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface GigabitEthernet2/0/0", "ipv6 enable", "ipv6 address 2001:db8:: 32 anycast"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import re
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
# Interface 模块私有宏定义
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_OPTYPE_MERGE
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_OPTYPE_DELETE
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_GET_IFM_HEAD
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_GET_IFM_TAIL

# Interface 模块私有接口公共函数
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_value
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_novalue
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_process_delete

logging.basicConfig(filename='/opt/python_logger.log', level=logging.INFO)

NE_NC_IPV6_CONFIG_HEAD = """
  <interface>
    <ifName>%s</ifName>
    <ipv6Config nc:operation="%s" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

NE_NC_IPV6_CONFIG_TAIL = """
    </ipv6Config>
  </interface>
"""

NE_NC_GET_IPV6_ADDRESS = """
<filter type="subtree">
  <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <ipv6Config>
          <am6CfgAddrs>
            <am6CfgAddr>
              <ifIp6Addr>%s</ifIp6Addr>
            </am6CfgAddr>
          </am6CfgAddrs>
        </ipv6Config>
      </interface>
    </interfaces>
  </ifm>
</filter>
"""

NE_NC_IPV6_ADDRESS_HEAD = """
  <interface>
    <ifName>%s</ifName>
    <ipv6Config>
      <am6CfgAddrs>
        <am6CfgAddr nc:operation="%s" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

NE_NC_IPV6_ADDRESS_TAIL = """
        </am6CfgAddr>
      </am6CfgAddrs>
    </ipv6Config>
  </interface>
"""

NE_NC_IPV6_CGA_HEAD = """
  <interface>
    <ifName>%s</ifName>
    <ipv6Config>
      <am6CgaInfos>
        <am6CgaInfo nc:operation="%s" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

NE_NC_IPV6_CGA_TAIL = """
        </am6CgaInfo>
      </am6CgaInfos>
    </ipv6Config>
  </interface>
"""

NE_BUILD_INTERFACE_CFG = """
  <config>
    <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
      <interfaces>%s</interfaces>
    </ifm>
  </config>
"""

ADDRESS_TYPE_XML2CLI = {
    "global": "global",
    "linkLocal": "link-local",
    "anycast": "anycast"}
ADDRESS_TYPE_CLI2XML = {
    "global": "global",
    "link-local": "linkLocal",
    "anycast": "anycast"}


class Interface_IPv6(object):
    """Manages configuration of an interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.input_info = dict()
        self.input_info["name"] = self.module.params["name"]
        self.input_info["enable"] = self.module.params["enable"]
        self.input_info["mtu"] = self.module.params["mtu"]
        self.input_info["mtu_spread"] = self.module.params["mtu_spread"]
        self.input_info["auto_linklocal"] = self.module.params["auto_linklocal"]

        self.input_info["address"] = self.module.params["address"]
        self.input_info["prefix_length"] = self.module.params["prefix_length"]
        self.input_info["address_type"] = self.module.params["address_type"]
        self.input_info["id_gen_type"] = self.module.params["id_gen_type"]

        self.input_info["rsa_key_label"] = self.module.params["rsa_key_label"]
        self.input_info["sec_level"] = self.module.params["sec_level"]
        self.input_info["modifier"] = self.module.params["modifier"]

        self.state = self.module.params['state']

        # interface info
        self.interface_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """
        required_one_of = [["name"]]
        required_together = [("address", "prefix_length")]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
            required_together=required_together,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # check interface name
        if self.input_info.get("name") is not None:
            if len(self.input_info.get("name")) > 63 or len(
                    self.input_info.get("name").replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Interface name is not in the range from 1 to 63.')

        if self.input_info.get("sec_level") is not None or self.input_info.get(
                "modifier") is not None:
            if self.input_info.get("rsa_key_label") is None:
                self.module.fail_json(
                    msg='Error: Rsa key-pair label has no value.')

        prefixlen = self.input_info.get("prefix_length")
        address_type = self.input_info.get("address_type")
        id_gen_type = self.input_info.get("id_gen_type")
        if address_type == "link-local" and prefixlen != 10:
            self.module.fail_json(
                msg='Error:The prefixlen of link-local address is not 10')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_interface_dict(self):
        """ get one interface attributes dict."""

        interface_info = dict()
        # Head info
        conf_str = NE_NC_GET_IFM_HEAD

        # Body info
        conf_str = constr_leaf_value(
            conf_str, "ifName", self.input_info["name"])
        conf_str = constr_container_novalue(conf_str, "ipv6Config")

        # Tail info
        conf_str += NE_NC_GET_IFM_TAIL
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return interface_info

        # interface_name
        name = re.findall(r'.*<ifName>(.*)</ifName>.*', xml_str)
        if name:
            interface_info["name"] = name[0]

        ipv6_enable = re.findall(r'.*<enableFlag>(.*)</enableFlag>.*', xml_str)
        if ipv6_enable:
            interface_info["enable"] = ipv6_enable[0]

        ipv6_mtu = re.findall(r'.*<ifMtu6>(.*)</ifMtu6>.*', xml_str)
        if ipv6_mtu:
            interface_info["mtu"] = ipv6_mtu[0]

        ipv6_mtu_spread = re.findall(
            r'.*<spreadMtu6Flag>(.*)</spreadMtu6Flag>.*', xml_str)
        if ipv6_mtu_spread:
            interface_info["mtu_spread"] = ipv6_mtu_spread[0]

        auto_linklocal = re.findall(
            r'.*<autoLinkLocal>(.*)</autoLinkLocal>.*', xml_str)
        if auto_linklocal:
            interface_info["auto_linklocal"] = auto_linklocal[0]

        # address info
        ipv6_info = re.findall(
            r'.*<ifIp6Addr>(.*)</ifIp6Addr>.*\s*<addrPrefixLen>(.*)</addrPrefixLen>.*\s*'
            r'<addrType6>(.*)</addrType6>.*\s*<ifIDGenType>(.*)</ifIDGenType>.*', xml_str)
        interface_info["ipv6_addr"] = list()
        for info in ipv6_info:
            interface_info["ipv6_addr"].append(
                dict(address=info[0], prefix_length=info[1],
                     address_type=ADDRESS_TYPE_XML2CLI.get(info[2]), id_gen_type=info[3]))

        rsa_key_label = re.findall(
            r'.*<rsaKeyLabel>(.*)</rsaKeyLabel>.*', xml_str)
        if rsa_key_label:
            interface_info["rsa_key_label"] = rsa_key_label[0]

        sec_level = re.findall(r'.*<secLevel>(.*)</secLevel>.*', xml_str)
        if sec_level:
            interface_info["sec_level"] = sec_level[0]

        modifier = re.findall(r'.*<modifier>(.*)</modifier>.*', xml_str)
        if modifier:
            interface_info["modifier"] = modifier[0]

        return interface_info

    def netconf_set_config(self, xml_str, xml_name):
        """ netconf set config """

        logging.info("netconf_set_config %s %s", xml_name, xml_str)
        rcv_xml = set_nc_config(self.module, xml_str)
        if "<ok/>" not in rcv_xml:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ipv6_address(self, ifname, address,
                         prefix_length, address_type, id_gen_type):
        """get ipv6 address"""
        logging.info(
            "get_ipv6_address %s %s %s %s %s",
            ifname,
            address,
            prefix_length,
            address_type,
            id_gen_type)
        conf_str = NE_NC_GET_IPV6_ADDRESS % (ifname, address)
        xml_str = get_nc_config(self.module, conf_str, True)

        # address info
        ipv6_info = re.findall(
            r'.*<ifIp6Addr>(.*)</ifIp6Addr>.*\s*<addrPrefixLen>(.*)</addrPrefixLen>.*\s*'
            r'<addrType6>(.*)</addrType6>.*\s*<ifIDGenType>(.*)</ifIDGenType>.*', xml_str)
        logging.info("ipv6_info %s", ipv6_info)
        if ipv6_info:
            ipv6_address = dict(address=ipv6_info[0][0], prefix_length=ipv6_info[0][1],
                                address_type=ADDRESS_TYPE_XML2CLI.get(ipv6_info[0][2]), id_gen_type=ipv6_info[0][3])
            if (prefix_length and str(prefix_length) != ipv6_address.get("prefix_length")) \
                    or (address_type and address_type != ipv6_address.get("address_type")) \
                    or (id_gen_type and id_gen_type != ipv6_address.get("id_gen_type")):
                return None
            else:
                return ipv6_address
        else:
            return None

    def merge_ipv6_config(self):
        """Merge ipv6 configuration"""

        xml_str = ""
        ifname = self.input_info.get("name")
        enable = self.input_info.get("enable")
        mtu = self.input_info.get("mtu")
        mtu_spread = self.input_info.get("mtu_spread")
        auto_linklocal = self.input_info.get("auto_linklocal")
        rsa_key_label = self.input_info.get("rsa_key_label")
        sec_level = self.input_info.get("sec_level")
        modifier = self.input_info.get("modifier")
        address = self.input_info.get("address")
        prefixlen = self.input_info.get("prefix_length")
        address_type = self.input_info.get("address_type")
        id_gen_type = self.input_info.get("id_gen_type")
        ipv6_addr = None

        # 构造下发报文，创建时，先配使能，再配CGA, 最后配地址
        if enable is not None or mtu is not None or mtu_spread is not None or auto_linklocal is not None:
            xml_str += NE_NC_IPV6_CONFIG_HEAD % (ifname, NE_NC_OPTYPE_MERGE)
            xml_str = constr_leaf_value(xml_str, "enableFlag", enable)
            xml_str = constr_leaf_value(xml_str, "ifMtu6", mtu)
            xml_str = constr_leaf_value(xml_str, "spreadMtu6Flag", mtu_spread)
            xml_str = constr_leaf_value(
                xml_str, "autoLinkLocal", auto_linklocal)
            xml_str += NE_NC_IPV6_CONFIG_TAIL

        if rsa_key_label is not None or sec_level is not None or modifier is not None:
            xml_str += NE_NC_IPV6_CGA_HEAD % (
                self.input_info.get("name"), NE_NC_OPTYPE_MERGE)
            xml_str = constr_leaf_value(xml_str, "rsaKeyLabel", rsa_key_label)
            xml_str = constr_leaf_value(xml_str, "secLevel", sec_level)
            xml_str = constr_leaf_value(xml_str, "modifier", modifier)
            xml_str += NE_NC_IPV6_CGA_TAIL

        if address is not None and prefixlen is not None:
            ipv6_addr = self.get_ipv6_address(
                ifname, address, prefixlen, address_type, id_gen_type)
            if not ipv6_addr:
                xml_str += NE_NC_IPV6_ADDRESS_HEAD % (
                    ifname, NE_NC_OPTYPE_MERGE)
                xml_str = constr_leaf_value(xml_str, "ifIp6Addr", address)
                xml_str = constr_leaf_value(
                    xml_str, "addrPrefixLen", prefixlen)
                if address_type is not None:
                    xml_str = constr_leaf_value(
                        xml_str, "addrType6", ADDRESS_TYPE_CLI2XML.get(address_type))
                xml_str = constr_leaf_value(
                    xml_str, "ifIDGenType", id_gen_type)
                xml_str += NE_NC_IPV6_ADDRESS_TAIL

        # 下发配置报文
        if xml_str:
            xml_str = NE_BUILD_INTERFACE_CFG % xml_str
            self.netconf_set_config(xml_str, "MERGE_IPV6_CONFIG")
        else:
            return

        # 获取变更后的配置
        changed_interface_info = self.get_interface_dict()

        # 生成配置变更命令行
        self.updates_cmd.append("interface %s" % self.input_info.get("name"))
        if enable is not None or mtu is not None or mtu_spread is not None or auto_linklocal is not None:
            if enable == "true":
                if self.interface_info.get(
                        "enable") != changed_interface_info.get("enable"):
                    self.updates_cmd.append("ipv6 enable")
                    self.changed = True

            if auto_linklocal is not None:
                if self.interface_info.get(
                        "auto_linklocal") != changed_interface_info.get("auto_linklocal"):
                    if auto_linklocal == "true":
                        self.updates_cmd.append("ipv6 address auto link-local")
                    else:
                        self.updates_cmd.append(
                            "undo ipv6 address auto link-local")
                    self.changed = True

            if mtu is not None or mtu_spread is not None:
                if changed_interface_info.get("mtu") != self.interface_info.get("mtu") \
                        or changed_interface_info.get("mtu_spread") != self.interface_info.get("mtu_spread"):
                    if changed_interface_info.get("mtu"):
                        if "true" == changed_interface_info.get("mtu_spread"):
                            self.updates_cmd.append(
                                "ipv6 mtu %s spread" %
                                changed_interface_info.get("mtu"))
                        else:
                            self.updates_cmd.append(
                                "ipv6 mtu %s" % changed_interface_info.get("mtu"))
                    else:
                        self.updates_cmd.append("undo ipv6 mtu")
                    self.changed = True

            if enable == "false":
                if self.interface_info.get(
                        "enable") != changed_interface_info.get("enable"):
                    self.updates_cmd.append("undo ipv6 enable")
                    self.changed = True

        if rsa_key_label is not None or sec_level is not None or modifier is not None:
            if rsa_key_label is not None:
                if changed_interface_info.get("rsa_key_label") is not None and \
                        self.interface_info.get("rsa_key_label") != changed_interface_info.get("rsa_key_label"):
                    self.updates_cmd.append("ipv6 security rsakey-pair %s"
                                            % changed_interface_info.get("rsa_key_label"))
                    self.changed = True

            if modifier is not None or sec_level is not None:
                if self.interface_info.get("sec_level") != changed_interface_info.get("sec_level") \
                        or self.interface_info.get("modifier") != changed_interface_info.get("modifier"):
                    logging.info("sec_level: %s %s", self.interface_info.get("sec_level"),
                                 changed_interface_info.get("sec_level"))
                    logging.info("modifier: %s %s", self.interface_info.get("modifier"),
                                 changed_interface_info.get("modifier"))
                    if changed_interface_info.get("modifier") is not None \
                            and changed_interface_info.get("sec_level") is not None:
                        self.updates_cmd.append("ipv6 security modifier sec-level %s %s"
                                                % (changed_interface_info.get("sec_level"),
                                                   changed_interface_info.get("modifier")))
                    elif changed_interface_info.get("sec_level") is not None:
                        self.updates_cmd.append("ipv6 security modifier sec-level %s"
                                                % changed_interface_info.get("sec_level"))
                    self.changed = True

        if address is not None and prefixlen is not None:
            if not ipv6_addr:
                if address_type == "link-local":
                    if id_gen_type == "cga":
                        self.updates_cmd.append(
                            "ipv6 address %s link-local cga" % address)
                    else:
                        self.updates_cmd.append(
                            "ipv6 address %s link-local" % address)
                elif address_type == "anycast":
                    self.updates_cmd.append(
                        "ipv6 address %s %s anycast" %
                        (address, prefixlen))
                else:
                    if id_gen_type == "cga":
                        self.updates_cmd.append(
                            "ipv6 address %s %s cga" %
                            (address, prefixlen))
                    elif id_gen_type == "eui64":
                        self.updates_cmd.append(
                            "ipv6 address %s %s eui-64" %
                            (address, prefixlen))
                    else:
                        self.updates_cmd.append(
                            "ipv6 address %s %s" %
                            (address, prefixlen))

                self.changed = True

    def delete_ipv6_config(self):
        """Delete ipv6 configuration"""

        xml_str = ""
        ifname = self.input_info.get("name")
        enable = self.input_info.get("enable")
        mtu = self.input_info.get("mtu")
        mtu_spread = self.input_info.get("mtu_spread")
        auto_linklocal = self.input_info.get("auto_linklocal")
        rsa_key_label = self.input_info.get("rsa_key_label")
        sec_level = self.input_info.get("sec_level")
        modifier = self.input_info.get("modifier")
        address = self.input_info.get("address")
        prefixlen = self.input_info.get("prefix_length")
        address_type = self.input_info.get("address_type")
        id_gen_type = self.input_info.get("id_gen_type")
        ipv6_addr = None

        # 构造下发报文，删除时，先删地址，再删CGA，最后删使能
        if address is not None and prefixlen is not None:
            ipv6_addr = self.get_ipv6_address(
                ifname, address, prefixlen, address_type, id_gen_type)
            if ipv6_addr:
                xml_str += NE_NC_IPV6_ADDRESS_HEAD % (
                    ifname, NE_NC_OPTYPE_DELETE)
                xml_str = constr_leaf_value(xml_str, "ifIp6Addr", address)
                xml_str = constr_leaf_value(
                    xml_str, "addrPrefixLen", prefixlen)
                if address_type is not None:
                    xml_str = constr_leaf_value(
                        xml_str, "addrType6", ADDRESS_TYPE_CLI2XML.get(address_type))
                xml_str = constr_leaf_value(
                    xml_str, "ifIDGenType", id_gen_type)
                xml_str += NE_NC_IPV6_ADDRESS_TAIL
            else:
                self.module.fail_json(msg='Error: The address does not exist.')

        if rsa_key_label is not None or sec_level is not None or modifier is not None:
            if "true" == self.interface_info.get("enable"):
                xml_str += NE_NC_IPV6_CGA_HEAD % (ifname, NE_NC_OPTYPE_DELETE)
                xml_str = constr_leaf_value(
                    xml_str, "rsaKeyLabel", rsa_key_label)
                xml_str = constr_leaf_value(xml_str, "secLevel", sec_level)
                xml_str = constr_leaf_value(xml_str, "modifier", modifier)
                xml_str += NE_NC_IPV6_CGA_TAIL

        if enable is not None or mtu is not None or mtu_spread is not None or auto_linklocal is not None:
            if "true" == self.interface_info.get("enable"):
                xml_str += NE_NC_IPV6_CONFIG_HEAD % (ifname,
                                                     NE_NC_OPTYPE_MERGE)
                if enable is not None:
                    xml_str = constr_leaf_process_delete(xml_str, "enableFlag")
                if mtu is not None:
                    xml_str = constr_leaf_process_delete(xml_str, "ifMtu6")
                if mtu_spread is not None:
                    xml_str = constr_leaf_process_delete(
                        xml_str, "spreadMtu6Flag")
                if auto_linklocal is not None:
                    xml_str = constr_leaf_process_delete(
                        xml_str, "autoLinkLocal")
                xml_str += NE_NC_IPV6_CONFIG_TAIL

        # 下发配置报文
        if xml_str:
            xml_str = NE_BUILD_INTERFACE_CFG % xml_str
            self.netconf_set_config(xml_str, "DELETE_IPV6_CONFIG")
        else:
            return

        # 获取变更后的配置
        changed_interface_info = self.get_interface_dict()

        # 生成配置变更命令行
        self.updates_cmd.append("interface %s" % self.input_info.get("name"))
        if address is not None and prefixlen is not None:
            if ipv6_addr:
                if address_type == "link-local":
                    if ipv6_addr.get("id_gen_type") == "cga":
                        self.updates_cmd.append(
                            "undo ipv6 address %s link-local cga" % address)
                    else:
                        self.updates_cmd.append(
                            "undo ipv6 address %s link-local" % address)
                elif ipv6_addr.get("address_type") == "anycast":
                    self.updates_cmd.append(
                        "undo ipv6 address %s %s anycast" %
                        (address, prefixlen))
                else:
                    if ipv6_addr.get("id_gen_type") == "cga":
                        self.updates_cmd.append(
                            "undo ipv6 address %s %s cga" %
                            (address, prefixlen))
                    elif ipv6_addr.get("id_gen_type") == "eui64":
                        self.updates_cmd.append(
                            "undo ipv6 address %s %s eui-64" %
                            (address, prefixlen))
                    else:
                        self.updates_cmd.append(
                            "undo ipv6 address %s %s" %
                            (address, prefixlen))

                self.changed = True

        if rsa_key_label is not None or sec_level is not None or modifier is not None:
            if modifier is not None or sec_level is not None:
                if self.interface_info.get("sec_level") != changed_interface_info.get("sec_level") \
                        or self.interface_info.get("modifier") != changed_interface_info.get("modifier"):
                    self.updates_cmd.append("undo ipv6 security modifier")
                    self.changed = True

            if rsa_key_label is not None:
                if self.interface_info.get(
                        "rsa_key_label") != changed_interface_info.get("rsa_key_label"):
                    self.updates_cmd.append(
                        "undo ipv6 security rsakey-pair %s" %
                        rsa_key_label)
                    self.changed = True

        if enable is not None or mtu is not None or mtu_spread is not None or auto_linklocal is not None:
            if auto_linklocal is not None:
                if self.interface_info.get(
                        "auto_linklocal") != changed_interface_info.get("auto_linklocal"):
                    self.updates_cmd.append(
                        "undo ipv6 address auto link-local")
                    self.changed = True

            if mtu is not None or mtu_spread is not None:
                if changed_interface_info.get("mtu") != self.interface_info.get("mtu") \
                        or changed_interface_info.get("mtu_spread") != self.interface_info.get("mtu_spread"):
                    if changed_interface_info.get("mtu"):
                        if "true" == changed_interface_info.get("mtu_spread"):
                            self.updates_cmd.append(
                                "ipv6 mtu %s spread" %
                                changed_interface_info.get("mtu"))
                        else:
                            self.updates_cmd.append(
                                "ipv6 mtu %s" % changed_interface_info.get("mtu"))
                    else:
                        self.updates_cmd.append("undo ipv6 mtu")
                    self.changed = True

            if enable is not None:
                if self.interface_info.get(
                        "enable") != changed_interface_info.get("enable"):
                    self.updates_cmd.append("undo ipv6 enable")
                    self.changed = True

    def get_proposed(self):
        """get proposed info"""
        self.proposed["state"] = self.state

        for key, value in self.input_info.items():
            if value is not None:
                self.proposed[key] = value

    def get_existing(self):
        """get existing info"""
        if not self.interface_info:
            return

        for key, value in self.interface_info.items():
            self.existing[key] = value

    def get_end_state(self):
        """get end state info"""

        interface_info = self.get_interface_dict()
        if not interface_info:
            return

        for key, value in interface_info.items():
            self.end_state[key] = value

    def work(self):
        """worker"""
        self.check_params()

        self.interface_info = self.get_interface_dict()
        self.get_proposed()
        self.get_existing()

        if not self.interface_info:
            self.module.fail_json(
                msg='Error: Interface %s does not exist.' %
                self.input_info.get("name"))

        if self.state == "present":
            self.merge_ipv6_config()
        elif self.state == "absent":
            self.delete_ipv6_config()

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
        name=dict(required=True, type='str'),
        enable=dict(required=False, choices=['true', 'false']),
        mtu=dict(required=False, type='int'),
        mtu_spread=dict(required=False, choices=['true', 'false']),
        auto_linklocal=dict(required=False, choices=['true', 'false']),

        address=dict(required=False, type='str'),
        prefix_length=dict(required=False, type='int'),
        address_type=dict(
            required=False,
            choices=[
                'global',
                'link-local',
                'anycast']),
        id_gen_type=dict(required=False, choices=['none', 'cga', 'eui64']),

        rsa_key_label=dict(required=False, type='str'),
        sec_level=dict(required=False, type='int'),
        modifier=dict(required=False, type='str'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = Interface_IPv6(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
