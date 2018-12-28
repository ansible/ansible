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
module: ne_interface_ipv4
version_added: "2.6"
short_description: Manages ipv4 configuration of an interface.
description:
    - Manages ipv4 configuration of an interface on HUAWEI netengine routers.
author: Shijiawei (@netengine-Ansible)
notes:
    - Interface must already be a L3 port when using this module.
    - Logical interfaces (loopback, vlanif) must be created first.
    - C(prefix_length) must be inserted in decimal format (i.e. 24) for
      both IPv6 and IPv4.
options:
    name:
        description:
            - The textual name of the interface. The value of this object should be the name of the
              interface as assigned by the local device and should be suitable for use in commands
              entered at the device's `console'. This might be a text name, depending on the interface
              naming syntax of the device. The value is a string of 1 to 63 characters.
        required: true
        default: null
    unnumbered_name:
        description:
            - Name of an unnumbered interface. The value is a string of 1 to 63 characters.
        required: true
        default: null
    address:
        description:
            - IPv4 address. The value is in dotted decimal notation.
        required: false
        default: null
    mask:
        description:
            - IPv4 address mask. The value is in dotted decimal notation.
        required: false
        default: null
    address_type:
        description:
            - IPv4 address type.
              main: Primary address of an interface.
              sub: Secondary address of an interface.
        required: false
        default: main
        choices: ['main', 'sub']
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present', 'absent', 'query']
'''

EXAMPLES = '''
- name: interface_ipv4 module test
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
  - name: Create ipv4 primary address
    ne_interface_ipv4:
      name: GigabitEthernet2/0/0
      address: 192.168.2.1
      mask: 255.255.255.0
      address_type: main
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"address": "192.168.2.1",
             "address_type": "main",
             "mask": "255.255.255.0",
             "name": "GigabitEthernet2/0/0",
             "state": "present"}
existing:
    description: k/v pairs of existing interface
    returned: always
    type: dict
    sample: {"ipv4_addr": [],
             "name": "GigabitEthernet2/0/0"}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"ipv4_addr": [
                 {
                     "address": "192.168.2.1",
                     "address_type": "main",
                     "mask": "255.255.255.0"
                 }
             ],
             "name": "GigabitEthernet2/0/0"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface GigabitEthernet2/0/0", "ip address 192.168.2.1 255.255.255.0"]
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
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_GET_IFM_HEAD
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_GET_IFM_TAIL

# Interface 模块私有接口公共函数
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_value
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_novalue

logging.basicConfig(filename='/opt/python_logger.log', level=logging.INFO)

NE_NC_ADD_IPV4 = """
  <interface>
    <ifName>%s</ifName>
    <ipv4Config>
      <am4CfgAddrs>
        <am4CfgAddr nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <ifIpAddr>%s</ifIpAddr>
          <subnetMask>%s</subnetMask>
          <addrType>%s</addrType>
        </am4CfgAddr>
      </am4CfgAddrs>
    </ipv4Config>
  </interface>
"""

NE_NC_MERGE_IPV4 = """
  <interface>
    <ifName>%s</ifName>
    <ipv4Config>
      <am4CfgAddrs>
        <am4CfgAddr nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <ifIpAddr>%s</ifIpAddr>
          <subnetMask>%s</subnetMask>
          <addrType>main</addrType>
        </am4CfgAddr>
        <am4CfgAddr nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <ifIpAddr>%s</ifIpAddr>
          <subnetMask>%s</subnetMask>
          <addrType>main</addrType>
        </am4CfgAddr>
      </am4CfgAddrs>
    </ipv4Config>
  </interface>
"""

NE_NC_DEL_IPV4 = """
  <interface>
    <ifName>%s</ifName>
    <ipv4Config>
      <am4CfgAddrs>
        <am4CfgAddr nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <ifIpAddr>%s</ifIpAddr>
          <subnetMask>%s</subnetMask>
          <addrType>%s</addrType>
        </am4CfgAddr>
      </am4CfgAddrs>
    </ipv4Config>
  </interface>
"""

NE_NC_ADD_IPV4_UNNUMBER = """
  <interface>
    <ifName>%s</ifName>
    <ipv4Config nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <unNumIfName>%s</unNumIfName>
    </ipv4Config>
  </interface>
"""

NE_NC_DEL_IPV4_UNNUMBER = """
  <interface>
    <ifName>%s</ifName>
    <ipv4Config>
      <unNumIfName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"></unNumIfName>
    </ipv4Config>
  </interface>
"""

NE_BUILD_INTERFACE_CFG = """
  <config>
    <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
      <interfaces>%s</interfaces>
    </ifm>
  </config>
"""


def is_valid_addr(addr):
    """check is ipv4 addr is valid"""

    if not addr:
        return True

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


def delete_zero(addr):
    """check is ipv4 addr is valid"""

    if not addr:
        return None

    if addr.find('.') != -1:
        addr_list = addr.split('.')
        if len(addr_list) != 4:
            return None
        for each_num in addr_list:
            if not each_num.isdigit():
                return None
            if int(each_num) > 255:
                return None
        new_addr = str(int(addr_list[0])) + "." + \
            str(int(addr_list[1])) + "." + \
            str(int(addr_list[2])) + "." + \
            str(int(addr_list[3]))
        return new_addr
    else:
        return None


class Interface_IPv4(object):
    """Manages configuration of an interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.input_info = dict()
        self.input_info["name"] = self.module.params["name"]
        self.input_info["unnumbered_name"] = self.module.params["unnumbered_name"]

        self.input_info["address"] = self.module.params["address"]
        self.input_info["mask"] = self.module.params["mask"]
        self.input_info["address_type"] = self.module.params["address_type"]

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
        required_together = [("address", "mask")]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
            required_together=required_together,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # 其他参数待同步增加补充
        # check interface exist
        if self.input_info.get("name") is not None:
            if len(self.input_info.get("name")) > 63 or len(
                    self.input_info.get("name").replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Interface name is not in the range from 1 to 63.')

        if self.input_info.get("unnumbered_name") is not None:
            if len(self.input_info.get("unnumbered_name")) > 63 \
                    or len(self.input_info.get("unnumbered_name").replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Unnumbered interface name is not in the range from 1 to 63.')

        if not is_valid_addr(self.input_info.get("address")):
            self.module.fail_json(
                msg='Error: The %s is not a valid address.' % self.input_info.get("address"))

        if not is_valid_addr(self.input_info.get("mask")):
            self.module.fail_json(
                msg='Error: The %s is not a valid mask.' % self.input_info.get("mask"))

        if self.state == "present" and self.input_info.get(
                "address") and self.input_info.get("unnumbered_name"):
            self.module.fail_json(
                msg='Error: Ip address and ip address unnumbered cannot be configured at the same time.')

    def get_interface_dict(self):
        """ get one interface attributes dict."""

        interface_info = dict()
        # Head info
        conf_str = NE_NC_GET_IFM_HEAD

        # Body info
        conf_str = constr_leaf_value(
            conf_str, "ifName", self.input_info.get("name"))
        conf_str = constr_container_novalue(conf_str, "ipv4Config")

        # Tail info
        conf_str += NE_NC_GET_IFM_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return interface_info

        # interface_name
        name = re.findall(r'.*<ifName>(.*)</ifName>.*', xml_str)
        if name:
            interface_info["name"] = name[0]

        # unnumber interface name
        unnumbered_name = re.findall(
            r'.*<unNumIfName>(.*)</unNumIfName>.*', xml_str)
        if unnumbered_name:
            interface_info["unnumbered_name"] = unnumbered_name[0]

        # address info
        ipv4_info = re.findall(
            r'.*<ifIpAddr>(.*)</ifIpAddr>.*\s*<subnetMask>(.*)'
            r'</subnetMask>.*\s*<addrType>(.*)</addrType>.*', xml_str)
        interface_info["ipv4_addr"] = list()
        for info in ipv4_info:
            logging.debug("ipv4_addr: %s %s %s", info[0], info[1], info[2])
            interface_info["ipv4_addr"].append(
                dict(address=info[0], mask=info[1], address_type=info[2]))

        return interface_info

    def netconf_set_config(self, xml_str, xml_name):
        """ netconf set config """
        rcv_xml = set_nc_config(self.module, xml_str)
        if "<ok/>" not in rcv_xml:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def is_ip_address_exist(self, address, mask, address_type):
        """"Check ip address exist"""
        ipv4_addrs = self.interface_info.get("ipv4_addr")
        if not ipv4_addrs:
            return False

        for ipv4_addr in ipv4_addrs:
            if ipv4_addr.get("address") == address:
                return ipv4_addr.get("mask") == mask and ipv4_addr.get(
                    "address_type") == address_type
        return False

    def get_ip_main_addr(self):
        """Get ip main address"""

        ipv4_addrs = self.interface_info.get("ipv4_addr")
        if not ipv4_addrs:
            return None

        for ipv4_addr in ipv4_addrs:
            if ipv4_addr.get("address_type") == "main":
                return ipv4_addr

        return None

    def get_unnumber_interface(self, unnum_ifname):
        """ get unnumber interface."""

        conf_str = NE_NC_GET_IFM_HEAD
        conf_str = constr_leaf_value(conf_str, "ifName", unnum_ifname)
        conf_str += NE_NC_GET_IFM_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return None

        # interface_name
        name = re.findall(r'.*<ifName>(.*)</ifName>.*', xml_str)
        if name:
            return name[0]

        return None

    def is_ip_address_unnumber_exist(self, unnum_ifname):
        """Check ip address unumber exist"""
        if unnum_ifname == self.interface_info.get("unnumbered_name"):
            return True

        return False

    def merge_ipv4_config(self, ifname, unnum_ifname,
                          address, mask, address_type):

        xml_str = ""
        self.updates_cmd.append("interface %s" % ifname)

        # 地址借用配置
        if unnum_ifname is not None:
            unnum_fullname = self.get_unnumber_interface(unnum_ifname)
            if unnum_fullname is None:
                self.module.fail_json(
                    msg='Error: Unnumbered interface %s does not exist' %
                    unnum_ifname)

            # create or set ip address unnumber
            if not self.is_ip_address_unnumber_exist(unnum_fullname):
                xml_str += NE_NC_ADD_IPV4_UNNUMBER % (ifname, unnum_fullname)
                self.updates_cmd.append(
                    "ip address unnumbered interface %s" %
                    unnum_fullname)

        # 地址配置
        if address is not None and mask is not None:
            address = delete_zero(address)
            mask = delete_zero(mask)

            if address is None:
                self.module.fail_json(
                    msg='Error: The %s is not a valid address.' %
                    self.input_info.get("address"))

            if mask is None:
                self.module.fail_json(
                    msg='Error: The %s is not a valid mask.' %
                    self.input_info.get("mask"))

            # create or set ip address
            if not self.is_ip_address_exist(address, mask, address_type):
                # primary ip address
                if address_type == "main":
                    main_addr = self.get_ip_main_addr()
                    if not main_addr:
                        # no ipv4 main address in this interface
                        xml_str += NE_NC_ADD_IPV4 % (ifname,
                                                     address, mask, address_type)
                    else:
                        # remove old address and set new
                        xml_str += NE_NC_MERGE_IPV4 % (ifname, main_addr["address"],
                                                       main_addr["mask"],
                                                       address,
                                                       mask)
                # secondary ip address
                else:
                    xml_str += NE_NC_ADD_IPV4 % (ifname,
                                                 address, mask, address_type)

                if address_type == "main":
                    self.updates_cmd.append(
                        "ip address %s %s" %
                        (address, mask))
                else:
                    self.updates_cmd.append(
                        "ip address %s %s sub" %
                        (address, mask))

        # 下发配置报文
        if xml_str:
            xml_str = NE_BUILD_INTERFACE_CFG % xml_str
            self.netconf_set_config(xml_str, "MERGE_IPV4_CONFIG")
            self.changed = True

    def delete_ipv4_config(self, ifname, unnum_ifname,
                           address, mask, address_type):
        xml_str = ""
        self.updates_cmd.append("interface %s" % ifname)

        # 地址借用配置
        if unnum_ifname is not None:
            unnum_fullname = self.get_unnumber_interface(unnum_ifname)
            if unnum_fullname is None:
                self.module.fail_json(
                    msg='Error: Unnumbered interface %s does not exist' %
                    unnum_ifname)

            # delete ip address unnumber
            if self.is_ip_address_unnumber_exist(unnum_fullname):
                xml_str += NE_NC_DEL_IPV4_UNNUMBER % (ifname)
                self.updates_cmd.append("undo ip address unnumbered")
            else:
                self.module.fail_json(
                    msg='Error: Unnumbered interface %s does not exist' %
                    unnum_ifname)

        # 地址配置
        if address is not None and mask is not None:
            address = delete_zero(address)
            mask = delete_zero(mask)

            if address is None:
                self.module.fail_json(
                    msg='Error: The %s is not a valid address.' %
                    self.input_info.get("address"))

            if mask is None:
                self.module.fail_json(
                    msg='Error: The %s is not a valid mask.' %
                    self.input_info.get("mask"))

            # delete ip address
            if self.is_ip_address_exist(address, mask, address_type):
                xml_str += NE_NC_DEL_IPV4 % (ifname,
                                             address, mask, address_type)

                if address_type == "main":
                    self.updates_cmd.append(
                        "undo ip address %s %s" %
                        (address, mask))
                else:
                    self.updates_cmd.append(
                        "undo ip address %s %s sub" %
                        (address, mask))
            else:
                self.module.fail_json(msg='Error: The address does not exist.')

        # 下发配置报文
        if xml_str:
            xml_str = NE_BUILD_INTERFACE_CFG % xml_str
            self.netconf_set_config(xml_str, "DELETE_IPV4_CONFIG")
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
            self.merge_ipv4_config(self.input_info.get("name"),
                                   self.input_info.get("unnumbered_name"),
                                   self.input_info.get("address"),
                                   self.input_info.get("mask"),
                                   self.input_info.get("address_type"))
        elif self.state == "absent":
            self.delete_ipv4_config(self.input_info.get("name"),
                                    self.input_info.get("unnumbered_name"),
                                    self.input_info.get("address"),
                                    self.input_info.get("mask"),
                                    self.input_info.get("address_type"))

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
        unnumbered_name=dict(required=False, type='str'),
        address=dict(required=False, type='str'),
        mask=dict(required=False, type='str'),
        address_type=dict(
            required=False, choices=[
                'main', 'sub'], default='main'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = Interface_IPv4(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
