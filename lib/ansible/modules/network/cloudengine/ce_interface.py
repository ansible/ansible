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
module: ce_interface
version_added: "2.2"
short_description: Manages physical attributes of interfaces.
description:
    - Manages physical attributes of interfaces of Huawei CloudEngine switches.
author: Pan Qijun (@CloudEngine-Ansible)
notes:
    - This module is also used to create logical interfaces such as
      vlanif and loopbacks.
options:
    interface:
        description:
            - Full name of interface, i.e. 40GE1/0/10, Tunnel1.
        required: true
        default: null
    interface_type:
        description:
            - Interface type to be configured from the device.
        required: false
        default: null
        choices: ['ge', '10ge', '25ge', '4x10ge', '40ge', '100ge', 'vlanif', 'loopback', 'meth',
                  'eth-trunk', 'nve', 'tunnel', 'ethernet', 'fcoe-port', 'fabric-port', 'stack-port', 'null']
    admin_state:
        description:
            - Administrative state of the interface.
        required: false
        default: up
        choices: ['up','down']
    description:
        description:
            - Interface description, in the range from 1 to 242.
        required: false
        default: null
    mode:
        description:
            - Manage Layer 2 or Layer 3 state of the interface.
        required: false
        default: null
        choices: ['layer2','layer3']
    state:
        description:
            - Specify desired state of the resource.
        required: true
        default: present
        choices: ['present','absent','default']
'''

EXAMPLES = '''
# Ensure an interface is a Layer 3 port and that it has the proper description
- ce_interface: interface=40GE1/0/22 description='Configured by Ansible' mode=layer3 host=68.170.147.165
# Admin down an interface
- ce_interface: interface=40GE1/0/22 host=68.170.147.165 admin_state=down
# Remove all tunnel interfaces
- ce_interface: interface_type=tunnel state=absent host=68.170.147.165
# Remove all logical interfaces
- ce_interface: interface_type={{ item }} state=absent host={{ inventory_hostname }}
  with_items:
    - loopback
    - eth-trunk
    - vlanif
    - nve
    - tunnel
# Admin up all 40GE interfaces
- ce_interface: interface_type=40GE host=68.170.147.165 admin_state=up
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"interface": "40GE1/0/10", "admin_state": "down"}
existing:
    description: k/v pairs of existing switchport
    type: dict
    sample:  {"admin_state": "up", "description": "None",
              "interface": "40GE1/0/10", "mode": "layer2"}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict or null
    sample:  {"admin_state": "down", "description": "None",
              "interface": "40GE1/0/10", "mode": "layer2"}
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: ["interface 40GE1/0/10", "shutdown"]
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


CE_NC_GET_INTFS = """
<filter type="subtree">
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName></ifName>
        <ifPhyType></ifPhyType>
        <ifNumber></ifNumber>
        <ifDescr></ifDescr>
        <ifAdminStatus></ifAdminStatus>
        <isL2SwitchPort></isL2SwitchPort>
        <ifMtu></ifMtu>
      </interface>
    </interfaces>
  </ifm>
</filter>
"""


CE_NC_GET_INTF = """
<filter type="subtree">
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <ifPhyType></ifPhyType>
        <ifNumber></ifNumber>
        <ifDescr></ifDescr>
        <ifAdminStatus></ifAdminStatus>
        <isL2SwitchPort></isL2SwitchPort>
        <ifMtu></ifMtu>
      </interface>
    </interfaces>
  </ifm>
</filter>
"""

CE_NC_XML_CREATE_INTF = """
<ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<interfaces>
  <interface operation="create">
    <ifName>%s</ifName>
    <ifDescr>%s</ifDescr>
  </interface>
</interfaces>
</ifm>
"""

CE_NC_XML_DELETE_INTF = """
<ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<interfaces>
  <interface operation="delete">
    <ifName>%s</ifName>
  </interface>
</interfaces>
</ifm>
"""


CE_NC_XML_MERGE_INTF_DES = """
<ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<interfaces>
  <interface operation="merge">
    <ifName>%s</ifName>
    <ifDescr>%s</ifDescr>
  </interface>
</interfaces>
</ifm>
"""
CE_NC_XML_MERGE_INTF_STATUS = """
<ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<interfaces>
  <interface operation="merge">
    <ifName>%s</ifName>
    <ifAdminStatus>%s</ifAdminStatus>
  </interface>
</interfaces>
</ifm>
"""

CE_NC_XML_MERGE_INTF_L2ENABLE = """
<ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<ethernetIfs>
  <ethernetIf operation="merge">
    <ifName>%s</ifName>
    <l2Enable>%s</l2Enable>
  </ethernetIf>
</ethernetIfs>
</ethernet>
"""

admin_state_type = ('ge', '10ge', '25ge', '4x10ge', '40ge', '100ge',
                    'vlanif', 'meth', 'eth-trunk', 'vbdif', 'tunnel',
                    'ethernet', 'stack-port')

switch_port_type = ('ge', '10ge', '25ge',
                    '4x10ge', '40ge', '100ge', 'eth-trunk')


class CE_Interface(object):
    """CE_Interface"""

    def __init__(self, argument_spec, ):
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.spec = argument_spec
        self.module = None
        self.nc = None
        self.init_module()

        # interface info
        self.interface = self.module.params['interface']
        self.interface_type = self.module.params['interface_type']
        self.admin_state = self.module.params['admin_state']
        self.description = self.module.params['description']
        self.mode = self.module.params['mode']
        self.state = self.module.params['state']

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.password = self.module.params['password']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()
        self.intfs_info = dict()        # all type interface info
        self.intf_info = dict()         # one interface info
        self.intf_type = None           # loopback tunnel ...

        # init netconf connect
        self.init_netconf()

    def init_module(self):
        """init_module"""

        self.module = NetworkModule(
            argument_spec=self.spec, supports_check_mode=True)

    def init_netconf(self):
        """init_netconf"""

        if not HAS_NCCLIENT:
            raise Exception("the ncclient library is required")

        self.nc = get_netconf(host=self.host, port=self.port,
                              username=self.username, password=self.password)
        if not self.nc:
            self.module.fail_json(msg='Error: netconf init failed')

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def build_config_xml(self, xmlstr):
        """build_config_xml"""

        return '<config> ' + xmlstr + ' </config>'

    def get_interfaces_dict(self):
        """ get interfaces attributes dict."""

        intfs_info = dict()
        conf_str = CE_NC_GET_INTFS
        try:
            con_obj = self.nc.get_config(filter=conf_str)
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

        if "<data/>" in con_obj.xml:
            return intfs_info

        intf = re.findall(
            r'.*<ifName>(.*)</ifName>.*\s*<ifPhyType>(.*)</ifPhyType>.*\s*'
            r'<ifNumber>(.*)</ifNumber>.*\s*<ifDescr>(.*)</ifDescr>.*\s*'
            r'<isL2SwitchPort>(.*)</isL2SwitchPort>.*\s*<ifAdminStatus>'
            r'(.*)</ifAdminStatus>.*\s*<ifMtu>(.*)</ifMtu>.*', con_obj.xml)

        for i in range(len(intf)):
            if intf[i][1]:
                if not intfs_info.get(intf[i][1].lower()):
                    # new interface type list
                    intfs_info[intf[i][1].lower()] = list()
                intfs_info[intf[i][1].lower()].append\
                    (dict(ifName=intf[i][0], ifPhyType=intf[i][1],
                          ifNumber=intf[i][2], ifDescr=intf[i][3],
                          isL2SwitchPort=intf[i][4],
                          ifAdminStatus=intf[i][5],
                          ifMtu=intf[i][6]))

        return intfs_info

    def get_interface_dict(self, ifname):
        """ get one interface attributes dict."""

        intf_info = dict()
        conf_str = CE_NC_GET_INTF % ifname
        try:
            con_obj = self.nc.get_config(filter=conf_str)
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

        if "<data/>" in con_obj.xml:
            return intf_info

        intf = re.findall(
            r'.*<ifName>(.*)</ifName>.*\s*'
            r'<ifPhyType>(.*)</ifPhyType>.*\s*'
            r'<ifNumber>(.*)</ifNumber>.*\s*'
            r'<ifDescr>(.*)</ifDescr>.*\s*'
            r'<isL2SwitchPort>(.*)</isL2SwitchPort>.*\s*'
            r'<ifAdminStatus>(.*)</ifAdminStatus>.*\s*'
            r'<ifMtu>(.*)</ifMtu>.*', con_obj.xml)

        if intf:
            intf_info = dict(ifName=intf[0][0], ifPhyType=intf[0][1],
                             ifNumber=intf[0][2], ifDescr=intf[0][3],
                             isL2SwitchPort=intf[0][4],
                             ifAdminStatus=intf[0][5], ifMtu=intf[0][6])

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

    def is_admin_state_enable(self, iftype):
        """admin state disable: loopback nve"""

        if iftype in admin_state_type:
            return True
        else:
            return False

    def is_portswitch_enalbe(self, iftype):
        """"is portswitch? """

        if iftype in switch_port_type:
            return True
        else:
            return False

    def is_create_enalbe(self, iftype):
        """is_create_enalbe"""

        return True

    def is_delete_enable(self, iftype):
        """is_delete_enable"""

        return True

    def create_interface(self, ifname, descritption, admin_state, mode):
        """Create interface."""

        self.updates_cmd.append("interface %s" % ifname)
        if not descritption:
            descritption = ''
        else:
            self.updates_cmd.append("descritption %s" % descritption)

        xmlstr = CE_NC_XML_CREATE_INTF % (ifname, descritption)
        if admin_state and self.is_admin_state_enable(self.intf_type):
            xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (ifname, admin_state)
            if admin_state == 'up':
                self.updates_cmd.append("undo shutdown")
            else:
                self.updates_cmd.append("shutdown")
        if mode and self.is_portswitch_enalbe(self.intf_type):
            if mode == "layer2":
                xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (ifname, 'enable')
                self.updates_cmd.append('portswitch')
            elif mode == "layer3":
                xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (ifname, 'disable')
                self.updates_cmd.append('undo portswitch')

        conf_str = self.build_config_xml(xmlstr)
        try:
            con_obj = self.nc.set_config(config=conf_str)
            self.check_response(con_obj, "CREATE_INTF")
            self.changed = True
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def delete_interface(self, ifname):
        """ Delete interface."""

        xmlstr = CE_NC_XML_DELETE_INTF % ifname
        conf_str = self.build_config_xml(xmlstr)
        self.updates_cmd.append('undo interface %s' % ifname)

        try:
            con_obj = self.nc.set_config(config=conf_str)
            self.check_response(con_obj, "DELETE_INTF")
            self.changed = True
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def delete_interfaces(self, iftype):
        """ Delete interfaces with type."""

        xmlstr = ''
        intfs_list = self.intfs_info.get(iftype.lower())
        if not intfs_list:
            return

        for i in range(len(intfs_list)):
            xmlstr += CE_NC_XML_DELETE_INTF % intfs_list[i]['ifName']
            self.updates_cmd.append('undo interface %s' %
                                    intfs_list[i]['ifName'])

        conf_str = self.build_config_xml(xmlstr)
        try:
            con_obj = self.nc.set_config(config=conf_str)
            self.check_response(con_obj, "DELETE_INTFS")
            self.changed = True
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def merge_interface(self, ifname, descritption, admin_state, mode):
        """ Merge interface attributes."""

        xmlstr = ''
        change = False
        self.updates_cmd.append("interface %s" % ifname)
        if descritption and self.intf_info["ifDescr"] != descritption:
            xmlstr += CE_NC_XML_MERGE_INTF_DES % (ifname, descritption)
            self.updates_cmd.append("descritption %s" % descritption)
            change = True

        if admin_state and self.is_admin_state_enable(self.intf_type) \
                and self.intf_info["ifAdminStatus"] != admin_state:
            xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (ifname, admin_state)
            change = True
            if admin_state == "up":
                self.updates_cmd.append("undo shutdown")
            else:
                self.updates_cmd.append("shutdown")

        if self.is_portswitch_enalbe(self.intf_type):
            if mode == "layer2" and self.intf_info["isL2SwitchPort"] != "true":
                xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (ifname, 'enable')
                self.updates_cmd.append("portswitch")
                change = True
            elif mode == "layer3" \
                    and self.intf_info["isL2SwitchPort"] != "false":
                xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (ifname, 'disable')
                self.updates_cmd.append("undo portswitch")
                change = True

        if not change:
            return

        conf_str = self.build_config_xml(xmlstr)

        try:
            con_obj = self.nc.set_config(config=conf_str)
            self.check_response(con_obj, "MERGE_INTF_ATTR")
            self.changed = True
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def merge_interfaces(self, iftype, descritption, admin_state, mode):
        """ Merge interface attributes by type."""

        xmlstr = ''
        change = False
        intfs_list = self.intfs_info.get(iftype.lower())
        if not intfs_list:
            return

        for i in range(len(intfs_list)):
            if_change = False
            self.updates_cmd.append("interface %s" % intfs_list[i]['ifName'])
            if descritption and intfs_list[i]["ifDescr"] != descritption:
                xmlstr += CE_NC_XML_MERGE_INTF_DES % (
                    intfs_list[i]['ifName'], descritption)
                self.updates_cmd.append("descritption %s" % descritption)
                if_change = True
            if admin_state and self.is_admin_state_enable(self.intf_type)\
                    and intfs_list[i]["ifAdminStatus"] != admin_state:
                xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (
                    intfs_list[i]['ifName'], admin_state)
                if_change = True
                if admin_state == "up":
                    self.updates_cmd.append("undo shutdown")
                else:
                    self.updates_cmd.append("shutdown")

            if self.is_portswitch_enalbe(self.intf_type):
                if mode == "layer2" \
                        and intfs_list[i]["isL2SwitchPort"] != "true":
                    xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (
                        intfs_list[i]['ifName'], 'enable')
                    self.updates_cmd.append("portswitch")
                    if_change = True
                elif mode == "layer3" \
                        and intfs_list[i]["isL2SwitchPort"] != "false":
                    xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (
                        intfs_list[i]['ifName'], 'disable')
                    self.updates_cmd.append("undo portswitch")
                    if_change = True

            if if_change:
                change = True
            else:
                self.updates_cmd.pop()

        if not change:
            return

        conf_str = self.build_config_xml(xmlstr)

        try:
            con_obj = self.nc.set_config(config=conf_str)
            self.check_response(con_obj, "MERGE_INTFS_ATTR")
            self.changed = True
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def default_interface(self, ifname, default_all=False):
        """default_interface"""

        change = False
        xmlstr = ""
        self.updates_cmd.append("interface %s" % ifname)
        # set descritption default
        if self.intf_info["ifDescr"]:
            xmlstr += CE_NC_XML_MERGE_INTF_DES % (ifname, '')
            self.updates_cmd.append("undo descritption")
            change = True

        # set admin_status default
        if self.is_admin_state_enable(self.intf_type) \
                and self.intf_info["ifAdminStatus"] != 'up':
            xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (ifname, 'up')
            self.updates_cmd.append("undo shutdown")
            change = True

        # set portswitch default
        if self.is_portswitch_enalbe(self.intf_type) \
                and self.intf_info["isL2SwitchPort"] != "true":
            xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (ifname, 'enable')
            self.updates_cmd.append("portswitch")
            change = True

        if not change:
            return

        conf_str = self.build_config_xml(xmlstr)
        try:
            con_obj = self.nc.set_config(config=conf_str)
            self.check_response(con_obj, "SET_INTF_DEFAULT")
            self.changed = True
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def default_interfaces(self, iftype, default_all=False):
        """ Set interface config to default by type."""

        change = False
        xmlstr = ''
        intfs_list = self.intfs_info.get(iftype.lower())
        if not intfs_list:
            return

        for i in range(len(intfs_list)):
            if_change = False
            self.updates_cmd.append("interface %s" % intfs_list[i]['ifName'])

            # set descritption default
            if intfs_list[i]['ifDescr']:
                xmlstr += CE_NC_XML_MERGE_INTF_DES % (
                    intfs_list[i]['ifName'], '')
                self.updates_cmd.append("undo descritption")
                if_change = True

            # set admin_status default
            if self.is_admin_state_enable(self.intf_type) \
                    and intfs_list[i]["ifAdminStatus"] != 'up':
                xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (
                    intfs_list[i]['ifName'], 'up')
                self.updates_cmd.append("undo shutdown")
                if_change = True

            # set portswitch default
            if self.is_portswitch_enalbe(self.intf_type) \
                    and intfs_list[i]["isL2SwitchPort"] != "true":
                xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (
                    intfs_list[i]['ifName'], 'enable')
                self.updates_cmd.append("portswitch")
                if_change = True

            if if_change:
                change = True
            else:
                self.updates_cmd.pop()

        if not change:
            return

        conf_str = self.build_config_xml(xmlstr)
        try:
            con_obj = self.nc.set_config(config=conf_str)
            self.check_response(con_obj, "SET_INTFS_DEFAULT")
            self.changed = True
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def check_params(self):
        """Check all input params"""

        if not self.interface and not self.interface_type:
            self.module.fail_json(
                msg='Error: Interface or interface_type must be set.')
        if self.interface and self.interface_type:
            self.module.fail_json(
                msg='Error: Interface or interface_type'
                    ' can not be set at the same time.')

        # interface type check
        if self.interface:
            self.intf_type = self.get_interface_type(self.interface)
            if not self.intf_type:
                self.module.fail_json(
                    msg='Error: interface name of %s'
                        ' is error.' % self.interface)

        elif self.interface_type:
            self.intf_type = self.get_interface_type(self.interface_type)
            if not self.intf_type or self.intf_type != self.interface_type.replace(" ", "").lower():
                self.module.fail_json(
                    msg='Error: interface type of %s'
                        ' is error.' % self.interface_type)

        if not self.intf_type:
            self.module.fail_json(
                msg='Error: interface or interface type %s is error.')

        # shutdown check
        if not self.is_admin_state_enable(self.intf_type) \
                and self.state == "present" and self.admin_state == "down":
            self.module.fail_json(
                msg='Error: The %s interface can not'
                    ' be shutdown.' % self.intf_type)

        # absent check
        if not self.is_delete_enable(self.intf_type) and self.state == "absent":
            self.module.fail_json(
                msg='Error: The %s interface can not'
                    ' be delete.' % self.intf_type)

        # port switch mode check
        if not self.is_portswitch_enalbe(self.intf_type)\
                and self.mode and self.state == "present":
            self.module.fail_json(
                msg='Error: The %s interface can not manage'
                    ' Layer 2 or Layer 3 state.' % self.intf_type)

        # check description len
        if self.description:
            if len(self.description) > 242 \
                    or len(self.description.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: interface description '
                        'is not in the range from 1 to 242.')

    def get_proposed(self):
        """get_proposed"""

        self.proposed['state'] = self.state
        if self.interface:
            self.proposed["interface"] = self.interface
        if self.interface_type:
            self.proposed["interface_type"] = self.interface_type

        if self.state == 'present':
            if self.description:
                self.proposed["description"] = self.description
            if self.mode:
                self.proposed["mode"] = self.mode
            if self.admin_state:
                self.proposed["admin_state"] = self.admin_state

        elif self.state == 'default':
            if self.description:
                self.proposed["description"] = ""
            if self.is_admin_state_enable(self.intf_type) and self.admin_state:
                self.proposed["admin_state"] = self.admin_state
            if self.is_portswitch_enalbe(self.intf_type) and self.mode:
                self.proposed["mode"] = self.mode

    def get_existing(self):
        """get_existing"""

        if self.intf_info:
            self.existing["interface"] = self.intf_info["ifName"]
            if self.is_admin_state_enable(self.intf_type):
                self.existing["admin_state"] = self.intf_info["ifAdminStatus"]
            self.existing["description"] = self.intf_info["ifDescr"]
            if self.is_portswitch_enalbe(self.intf_type):
                if self.intf_info["isL2SwitchPort"] == "true":
                    self.existing["mode"] = "layer2"
                else:
                    self.existing["mode"] = "layer3"

    def get_end_state(self):
        """get_end_state"""

        if self.intf_info:
            end_info = self.get_interface_dict(self.interface)
            if end_info:
                self.end_state["interface"] = end_info["ifName"]
                if self.is_admin_state_enable(self.intf_type):
                    self.end_state["admin_state"] = end_info["ifAdminStatus"]
                self.end_state["description"] = end_info["ifDescr"]
                if self.is_portswitch_enalbe(self.intf_type):
                    if end_info["isL2SwitchPort"] == "true":
                        self.end_state["mode"] = "layer2"
                    else:
                        self.end_state["mode"] = "layer3"

    def work(self):
        """worker"""

        self.check_params()

        # single interface config
        if self.interface:
            self.intf_info = self.get_interface_dict(self.interface)
            self.get_existing()
            if self.state == 'present':
                if not self.intf_info:
                    # create interface
                    self.create_interface\
                        (self.interface,
                         self.description,
                         self.admin_state,
                         self.mode)
                else:
                    # merge interface
                    if self.description or self.admin_state or self.mode:
                        self.merge_interface\
                            (self.interface,
                             self.description,
                             self.admin_state,
                             self.mode)

            elif self.state == 'absent':
                if self.intf_info:
                    # delete interface
                    self.delete_interface(self.interface)
                else:
                    # interface does not exists
                    self.module.fail_json(
                        msg='Error: interface does not exists.')

            else:       # default
                if not self.intf_info:
                    # error, interface does not exists
                    self.module.fail_json(
                        msg='Error: interface does not exists.')
                else:
                    self.default_interface(self.interface)

        # interface type config
        else:
            self.intfs_info = self.get_interfaces_dict()
            self.get_existing()
            if self.state == 'present':
                if self.intfs_info.get(self.intf_type.lower()):
                    if self.description or self.admin_state or self.mode:
                        self.merge_interfaces\
                            (self.intf_type,
                             self.description,
                             self.admin_state,
                             self.mode)
            elif self.state == 'absent':
                # delete all interface of this type
                if self.intfs_info.get(self.intf_type.lower()):
                    self.delete_interfaces(self.intf_type)

            else:
                # set interfaces config to default
                if self.intfs_info.get(self.intf_type.lower()):
                    self.default_interfaces(self.intf_type)
                else:
                    self.module.fail_json(
                        msg='Error: no interface in this type.')

        self.get_proposed()
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
    """main"""

    argument_spec = dict(
        interface=dict(required=False, type='str'),
        admin_state=dict(choices=['up', 'down'], required=False),
        description=dict(required=False, default=None),
        mode=dict(choices=['layer2', 'layer3'], required=False),
        interface_type=dict(required=False),
        state=dict(choices=['absent', 'present', 'default'],
                   default='present', required=False),
    )

    interface = CE_Interface(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
