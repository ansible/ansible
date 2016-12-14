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

DOCUMENTATION = '''
---
module: ce_ip_interface
version_added: "2.2"
short_description: Manages L3 attributes for IPv4 and IPv6 interfaces.
description:
    - Manages Layer 3 attributes for IPv4 and IPv6 interfaces.
extends_documentation_fragment: CloudEngine
author:
    - Pan Qijun (@CloudEngine-Ansible)
notes:
    - Interface must already be a L3 port when using this module.
    - Logical interfaces (loopback, vlanif) must be created first.
    - C(mask) must be inserted in decimal format (i.e. 24) for
      both IPv6 and IPv4.
    - A single interface can have multiple IPv6 configured.
options:
    interface:
        description:
            - Full name of interface, i.e. 40GE1/0/22, vlanif10.
        required: true
    addr:
        description:
            - IPv4 or IPv6 Address.
        required: false
        default: null
    mask:
        description:
            - Subnet mask for IPv4 or IPv6 Address in decimal format.
        required: false
        default: null
    version:
        description:
            - IP address version.
        required: false
        default: v4
        choices: ['v4','v6']
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ensure ipv4 address is configured on 40GE1/0/22
- ce_ip_interface: interface=40GE1/0/22 version=v4 state=present addr=20.20.20.20 mask=24
# ensure ipv6 is enabled on 40GE1/0/22
- ce_ip_interface: interface=40GE1/0/22 version=v6 state=present
# ensure ipv6 address is configured on 40GE1/0/22
- ce_ip_interface: interface=40GE1/0/22 version=v6 state=present addr=2001::db8:800:200c:cccb mask=64
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"addr": "20.20.20.20", "interface": "40GE1/0/22", "mask": "24"}
existing:
    description: k/v pairs of existing IP attributes on the interface
    type: dict
    sample: {"ipv4": [{"ifIpAddr": "11.11.11.11", "subnetMask": "255.255.0.0", "addrType": "main"}],
            "interface": "40GE1/0/22"}
end_state:
    description: k/v pairs of IP attributes after module execution
    returned: always
    type: dict
    sample: {"ipv4": [{"ifIpAddr": "20.20.20.20", "subnetMask": "255.255.255.0", "addrType": "main"}],
            "interface": "40GE1/0/22""}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface 40GE1/0/22", "ip address 20.20.20.20 24"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import re
import datetime
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False
    pass

CE_NC_GET_INTF = """
<filter type="subtree">
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <isL2SwitchPort></isL2SwitchPort>
        <ifmAm4>
        </ifmAm4>
        <ifmAm6>
        </ifmAm6>
      </interface>
    </interfaces>
  </ifm>
</filter>
"""

CE_NC_ADD_IPV4 = """
<config>
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <ifmAm4>
          <am4CfgAddrs>
            <am4CfgAddr operation="merge">
              <ifIpAddr>%s</ifIpAddr>
              <subnetMask>%s</subnetMask>
              <addrType>main</addrType>
            </am4CfgAddr>
          </am4CfgAddrs>
        </ifmAm4>
      </interface>
    </interfaces>
  </ifm>
</config>
"""

CE_NC_MERGE_IPV4 = """
<config>
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <ifmAm4>
          <am4CfgAddrs>
            <am4CfgAddr operation="delete">
              <ifIpAddr>%s</ifIpAddr>
              <subnetMask>%s</subnetMask>
              <addrType>main</addrType>
            </am4CfgAddr>
            <am4CfgAddr operation="merge">
              <ifIpAddr>%s</ifIpAddr>
              <subnetMask>%s</subnetMask>
              <addrType>main</addrType>
            </am4CfgAddr>
          </am4CfgAddrs>
        </ifmAm4>
      </interface>
    </interfaces>
  </ifm>
</config>
"""


CE_NC_DEL_IPV4 = """
<config>
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <ifmAm4>
          <am4CfgAddrs>
            <am4CfgAddr operation="delete">
              <ifIpAddr>%s</ifIpAddr>
              <subnetMask>%s</subnetMask>
              <addrType>main</addrType>
            </am4CfgAddr>
          </am4CfgAddrs>
        </ifmAm4>
      </interface>
    </interfaces>
  </ifm>
</config>
"""

CE_NC_ADD_IPV6 = """
<config>
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <ifmAm6>
          <am6CfgAddrs>
            <am6CfgAddr operation="merge">
              <ifIp6Addr>%s</ifIp6Addr>
              <addrPrefixLen>%s</addrPrefixLen>
              <addrType6>global</addrType6>
            </am6CfgAddr>
          </am6CfgAddrs>
        </ifmAm6>
      </interface>
    </interfaces>
  </ifm>
</config>
"""

CE_NC_DEL_IPV6 = """
    <config>
      <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <interfaces>
          <interface>
            <ifName>%s</ifName>
            <ifmAm6>
              <am6CfgAddrs>
                <am6CfgAddr operation="delete">
                  <ifIp6Addr>%s</ifIp6Addr>
                  <addrPrefixLen>%s</addrPrefixLen>
                  <addrType6>global</addrType6>
                </am6CfgAddr>
              </am6CfgAddrs>
            </ifmAm6>
          </interface>
        </interfaces>
      </ifm>
    </config>
"""

CE_NC_MERGE_IPV6_ENABLE = """
<config>
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <ifmAm6 operation="merge">
          <enableFlag>%s</enableFlag>
        </ifmAm6>
      </interface>
    </interfaces>
  </ifm>
</config>
"""


class IpInterface(object):
    """
    Manages L3 attributes for IPv4 and IPv6 interfaces.
    """

    def __init__(self, argument_spec, ):
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.spec = argument_spec
        self.module = None
        self.netconf = None
        self.init_module()

        # module input info]
        self.interface = self.module.params['interface']
        self.addr = self.module.params['addr']
        self.mask = self.module.params['mask']
        self.version = self.module.params['version']
        self.state = self.module.params['state']

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
        # interface info
        self.intf_info = dict()
        self.intf_type = None

        # init netconf connect
        self.init_netconf()

    def init_module(self):
        """" init module """

        self.module = NetworkModule(
            argument_spec=self.spec, supports_check_mode=True)

    def init_netconf(self):
        """ init netconf """

        if not HAS_NCCLIENT:
            raise Exception("the ncclient library is required")

        self.netconf = get_netconf(host=self.host,
                                   port=self.port,
                                   username=self.username,
                                   password=self.module.params['password'])
        if not self.netconf:
            self.module.fail_json(msg='Error: netconf init failed')

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def netconf_get_config(self, xml_str):
        """ netconf get config """

        try:
            con_obj = self.netconf.get_config(filter=xml_str)
        except RPCError as err:
            self.module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def netconf_set_config(self, xml_str, xml_name):
        """ netconf set config """

        try:
            con_obj = self.netconf.set_config(config=xml_str)
            self.check_response(con_obj, xml_name)
        except RPCError as err:
            self.module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def netconf_set_action(self, xml_str, xml_name):
        """ netconf set config """

        try:
            con_obj = self.netconf.execute_action(action=xml_str)
            self.check_response(con_obj, xml_name)
        except RPCError as err:
            self.module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def get_interface_dict(self, ifname):
        """ get one interface attributes dict."""

        intf_info = dict()
        conf_str = CE_NC_GET_INTF % ifname
        con_obj = self.netconf_get_config(conf_str)

        if "<data/>" in con_obj.xml:
            return intf_info

        # get interface base info
        intf = re.findall(
            r'.*<ifName>(.*)</ifName>.*\s*'
            r'<isL2SwitchPort>(.*)</isL2SwitchPort>.*', con_obj.xml)

        if intf:
            intf_info = dict(ifName=intf[0][0],
                             isL2SwitchPort=intf[0][1])

        # get interface ipv4 address info
        ipv4_info = re.findall(
            r'.*<ifIpAddr>(.*)</ifIpAddr>.*\s*<subnetMask>(.*)'
            r'</subnetMask>.*\s*<addrType>(.*)</addrType>.*', con_obj.xml)
        intf_info["am4CfgAddr"] = list()
        for info in ipv4_info:
            intf_info["am4CfgAddr"].append(
                dict(ifIpAddr=info[0], subnetMask=info[1], addrType=info[2]))

        # get interface ipv6 address info
        ipv6_info = re.findall(
            r'.*<ifmAm6>.*\s*<enableFlag>(.*)</enableFlag>.*', con_obj.xml)
        if not ipv6_info:
            self.module.fail_json(msg='Fail to get interface IPv6 state')
        else:
            intf_info["enableFlag"] = ipv6_info[0]

        # get interface ipv6 enable info
        ipv6_info = re.findall(
            r'.*<ifIp6Addr>(.*)</ifIp6Addr>.*\s*<addrPrefixLen>(.*)'
            r'</addrPrefixLen>.*\s*<addrType6>(.*)</addrType6>.*', con_obj.xml)

        intf_info["am6CfgAddr"] = list()
        for info in ipv6_info:
            intf_info["am6CfgAddr"].append(
                dict(ifIp6Addr=info[0], addrPrefixLen=info[1], addrType6=info[2]))

        return intf_info

    def get_interface_type(self, interface):
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

    def convert_len_to_mask(self, masklen):
        """convert mask length to ip address mask, i.e. 24 to 255.255.255.0"""

        mask_int = ["0"] * 4
        length = int(masklen)

        if length > 32:
            self.module.fail_json(msg='IPv4 ipaddress mask length is invalid')
        if length < 8:
            mask_int[0] = str(int((0xFF << (8 - length % 8)) & 0xFF))
        if length >= 8:
            mask_int[0] = '255'
            mask_int[1] = str(int((0xFF << (16 - (length % 16))) & 0xFF))
        if length >= 16:
            mask_int[1] = '255'
            mask_int[2] = str(int((0xFF << (24 - (length % 24))) & 0xFF))
        if length >= 24:
            mask_int[2] = '255'
            mask_int[3] = str(int((0xFF << (32 - (length % 32))) & 0xFF))
        if length == 32:
            mask_int[3] = '255'

        return '.'.join(mask_int)

    def is_ipv4_exist(self, addr, maskstr):
        """"Check IPv4 address exist"""

        addrs = self.intf_info["am4CfgAddr"]
        if not addrs:
            return False

        for address in addrs:
            if address["ifIpAddr"] == addr:
                return address["subnetMask"] == maskstr and address["addrType"] == "main"
        return False

    def get_ipv4_main_addr(self):
        """get IPv4 main address"""

        addrs = self.intf_info["am4CfgAddr"]
        if not addrs:
            return None

        for address in addrs:
            if address["addrType"] == "main":
                return address

        return None

    def is_ipv6_exist(self, addr, masklen):
        """Check IPv6 address exist"""

        addrs = self.intf_info["am6CfgAddr"]
        if not addrs:
            return False

        for address in addrs:
            if address["ifIp6Addr"] == addr.upper():
                if address["addrPrefixLen"] == masklen and address["addrType6"] == "global":
                    return True
                else:
                    self.module.fail_json(
                        msg="Input IPv6 address or mask is invalid")

        return False

    def set_ipv4_addr(self, ifname, addr, mask):
        """Set interface IPv4 address"""

        if not addr or not mask:
            return

        maskstr = self.convert_len_to_mask(mask)
        if self.state == "present":
            if not self.is_ipv4_exist(addr, maskstr):
                main_addr = self.get_ipv4_main_addr()
                if not main_addr:
                    # no ipv4 main address in this interface
                    xml_str = CE_NC_ADD_IPV4 % (ifname, addr, maskstr)
                    self.netconf_set_config(xml_str, "ADD_IPV4_ADDR")
                else:
                    # remove old address and set new
                    xml_str = CE_NC_MERGE_IPV4 % (ifname, main_addr["ifIpAddr"],
                                                  main_addr["subnetMask"],
                                                  addr, maskstr)
                    self.netconf_set_config(xml_str, "MERGE_IPV4_ADDR")
                self.updates_cmd.append("interface %s" % ifname)
                self.updates_cmd.append("ip address %s %s" % (addr, maskstr))
                self.changed = True
        else:
            if self.is_ipv4_exist(addr, maskstr):
                xml_str = CE_NC_DEL_IPV4 % (ifname, addr, maskstr)
                self.netconf_set_config(xml_str, "DEL_IPV4_ADDR")
                self.updates_cmd.append("interface %s" % ifname)
                self.updates_cmd.append(
                    "undo ip address %s %s" % (addr, maskstr))
                self.changed = True

    def set_ipv6_addr(self, ifname, addr, mask):
        """Set interface IPv6 address"""

        if not addr or not mask:
            return

        if self.state == "present":
            self.updates_cmd.append("interface %s" % ifname)
            if self.intf_info["enableFlag"] == "false":
                xml_str = CE_NC_MERGE_IPV6_ENABLE % (ifname, "true")
                self.netconf_set_config(xml_str, "SET_IPV6_ENABLE")
                self.updates_cmd.append("ipv6 enable")
                self.changed = True

            if not self.is_ipv6_exist(addr, mask):
                xml_str = CE_NC_ADD_IPV6 % (ifname, addr, mask)
                self.netconf_set_config(xml_str, "ADD_IPV6_ADDR")

                self.updates_cmd.append("ipv6 address %s %s" % (addr, mask))
                self.changed = True

            if not self.changed:
                self.updates_cmd.pop()
        else:
            if self.is_ipv6_exist(addr, mask):
                xml_str = CE_NC_DEL_IPV6 % (ifname, addr, mask)
                self.netconf_set_config(xml_str, "DEL_IPV6_ADDR")
                self.updates_cmd.append("interface %s" % ifname)
                self.updates_cmd.append(
                    "undo ipv6 address %s %s" % (addr, mask))
                self.changed = True

    def set_ipv6_enable(self, ifname):
        """Set interface IPv6 enable"""

        if self.state == "present":
            if self.intf_info["enableFlag"] == "false":
                xml_str = CE_NC_MERGE_IPV6_ENABLE % (ifname, "true")
                self.netconf_set_config(xml_str, "SET_IPV6_ENABLE")
                self.updates_cmd.append("interface %s" % ifname)
                self.updates_cmd.append("ipv6 enable")
                self.changed = True
        else:
            if self.intf_info["enableFlag"] == "true":
                xml_str = CE_NC_MERGE_IPV6_ENABLE % (ifname, "false")
                self.netconf_set_config(xml_str, "SET_IPV6_DISABLE")
                self.updates_cmd.append("interface %s" % ifname)
                self.updates_cmd.append("undo ipv6 enable")
                self.changed = True

    def is_valid_v4addr(self, addr):
        """check is ipv4 addr is valid"""

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

    def check_params(self):
        """Check all input params"""

        # check interface type
        if self.interface:
            self.intf_type = self.get_interface_type(self.interface)
            if not self.intf_type:
                self.module.fail_json(
                    msg='Error: Interface name of %s '
                        'is error.' % self.interface)

        # ipv4 addr and mask check
        if self.version == "v4":
            if not self.addr or not self.mask:
                self.module.fail_json(msg='Error: addr and mask must be set.')
            if not self.is_valid_v4addr(self.addr):
                self.module.fail_json(
                    msg='Error: The %s is not a valid address' % self.addr)
            if not self.mask.isdigit():
                self.module.fail_json(msg='Error: mask is invalid.')
            if int(self.mask) > 32 or int(self.mask) < 1:
                self.module.fail_json(
                    msg='Error: mask must be an integer between 1 and 32.')

        # ipv6 mask check
        if self.version == "v6":
            if self.addr:
                if not self.mask:
                    self.module.fail_json(msg='Error: mask must be set.')
                if not self.mask.isdigit():
                    self.module.fail_json(msg='Error: mask is invalid.')
                if int(self.mask) > 128 or int(self.mask) < 1:
                    self.module.fail_json(
                        msg='Error: mask must be an integer between 1 and 128.')

        # interface and layer3 check
        self.intf_info = self.get_interface_dict(self.interface)
        if not self.intf_info:
            self.module.fail_json(msg='Error: interface does not exist.')

        if self.intf_info["isL2SwitchPort"] == "true":
            self.module.fail_json(msg='Error: interface is layer2.')

    def get_proposed(self):
        """get proposed info"""

        self.proposed["state"] = self.state
        self.proposed["addr"] = self.addr
        self.proposed["mask"] = self.mask
        self.proposed["version"] = self.version
        self.proposed["interface"] = self.interface

    def get_existing(self):
        """get existing info"""

        self.existing["interface"] = self.interface
        self.existing["ipv4addr"] = self.intf_info["am4CfgAddr"]
        self.existing["ipv6addr"] = self.intf_info["am6CfgAddr"]
        self.existing["ipv6enalbe"] = self.intf_info["enableFlag"]

    def get_end_state(self):
        """get end state info"""

        intf_info = self.get_interface_dict(self.interface)
        self.end_state["interface"] = self.interface
        self.end_state["ipv4addr"] = intf_info["am4CfgAddr"]
        self.end_state["ipv6addr"] = intf_info["am6CfgAddr"]
        self.end_state["ipv6enalbe"] = intf_info["enableFlag"]

    def work(self):
        """worker"""

        self.check_params()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        if self.version == "v4":
            self.set_ipv4_addr(self.interface, self.addr, self.mask)
        else:
            if not self.addr and not self.mask:
                self.set_ipv6_enable(self.interface)
            else:
                self.set_ipv6_addr(self.interface, self.addr, self.mask)

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.end_time = datetime.datetime.now()
        self.results['execute_time'] = str(self.end_time - self.start_time)

        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        interface=dict(required=True),
        addr=dict(required=False),
        version=dict(required=False, choices=['v4', 'v6'],
                     default='v4'),
        mask=dict(type='str', required=False),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )

    module = IpInterface(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
