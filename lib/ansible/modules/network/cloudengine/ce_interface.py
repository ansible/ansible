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
module: ce_interface
version_added: "2.4"
short_description: Manages physical attributes of interfaces on HUAWEI CloudEngine switches.
description:
    - Manages physical attributes of interfaces on HUAWEI CloudEngine switches.
author: QijunPan (@QijunPan)
notes:
    - This module is also used to create logical interfaces such as
      vlanif and loopbacks.
options:
    interface:
        description:
            - Full name of interface, i.e. 40GE1/0/10, Tunnel1.
    interface_type:
        description:
            - Interface type to be configured from the device.
        choices: ['ge', '10ge', '25ge', '4x10ge', '40ge', '100ge', 'vlanif', 'loopback', 'meth',
                  'eth-trunk', 'nve', 'tunnel', 'ethernet', 'fcoe-port', 'fabric-port', 'stack-port', 'null']
    admin_state:
        description:
            - Specifies the interface management status.
              The value is an enumerated type.
              up, An interface is in the administrative Up state.
              down, An interface is in the administrative Down state.
        choices: ['up', 'down']
    description:
        description:
            - Specifies an interface description.
              The value is a string of 1 to 242 case-sensitive characters,
              spaces supported but question marks (?) not supported.
    mode:
        description:
            - Manage Layer 2 or Layer 3 state of the interface.
        choices: ['layer2', 'layer3']
    l2sub:
        description:
            - Specifies whether the interface is a Layer 2 sub-interface.
        type: bool
        default: 'no'
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present', 'absent', 'default']
'''

EXAMPLES = '''
- name: interface module test
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
  - name: Ensure an interface is a Layer 3 port and that it has the proper description
    ce_interface:
      interface: 10GE1/0/22
      description: 'Configured by Ansible'
      mode: layer3
      provider: '{{ cli }}'

  - name: Admin down an interface
    ce_interface:
      interface: 10GE1/0/22
      admin_state: down
      provider: '{{ cli }}'

  - name: Remove all tunnel interfaces
    ce_interface:
      interface_type: tunnel
      state: absent
      provider: '{{ cli }}'

  - name: Remove all logical interfaces
    ce_interface:
      interface_type: '{{ item }}'
      state: absent
      provider: '{{ cli }}'
    with_items:
      - loopback
      - eth-trunk
      - nve

  - name: Admin up all 10GE interfaces
    ce_interface:
      interface_type: 10GE
      admin_state: up
      provider: '{{ cli }}'
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"interface": "10GE1/0/10", "admin_state": "down"}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {"admin_state": "up", "description": "None",
              "interface": "10GE1/0/10", "mode": "layer2"}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  {"admin_state": "down", "description": "None",
              "interface": "10GE1/0/10", "mode": "layer2"}
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: ["interface 10GE1/0/10", "shutdown"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''


import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec


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

CE_NC_XML_CREATE_INTF_L2SUB = """
<ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
<interfaces>
  <interface operation="create">
    <ifName>%s</ifName>
    <ifDescr>%s</ifDescr>
    <l2SubIfFlag>true</l2SubIfFlag>
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

ADMIN_STATE_TYPE = ('ge', '10ge', '25ge', '4x10ge', '40ge', '100ge',
                    'vlanif', 'meth', 'eth-trunk', 'vbdif', 'tunnel',
                    'ethernet', 'stack-port')

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


def is_admin_state_enable(iftype):
    """admin state disable: loopback nve"""

    return bool(iftype in ADMIN_STATE_TYPE)


def is_portswitch_enalbe(iftype):
    """"is portswitch? """

    return bool(iftype in SWITCH_PORT_TYPE)


class Interface(object):
    """Manages physical attributes of interfaces."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # interface info
        self.interface = self.module.params['interface']
        self.interface_type = self.module.params['interface_type']
        self.admin_state = self.module.params['admin_state']
        self.description = self.module.params['description']
        self.mode = self.module.params['mode']
        self.l2sub = self.module.params['l2sub']
        self.state = self.module.params['state']

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

    def init_module(self):
        """init_module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_interfaces_dict(self):
        """ get interfaces attributes dict."""

        intfs_info = dict()
        conf_str = CE_NC_GET_INTFS
        recv_xml = get_nc_config(self.module, conf_str)

        if "<data/>" in recv_xml:
            return intfs_info

        intf = re.findall(
            r'.*<ifName>(.*)</ifName>.*\s*<ifPhyType>(.*)</ifPhyType>.*\s*'
            r'<ifNumber>(.*)</ifNumber>.*\s*<ifDescr>(.*)</ifDescr>.*\s*'
            r'<isL2SwitchPort>(.*)</isL2SwitchPort>.*\s*<ifAdminStatus>'
            r'(.*)</ifAdminStatus>.*\s*<ifMtu>(.*)</ifMtu>.*', recv_xml)

        for tmp in intf:
            if tmp[1]:
                if not intfs_info.get(tmp[1].lower()):
                    # new interface type list
                    intfs_info[tmp[1].lower()] = list()
                intfs_info[tmp[1].lower()].append(dict(ifName=tmp[0], ifPhyType=tmp[1], ifNumber=tmp[2],
                                                       ifDescr=tmp[3], isL2SwitchPort=tmp[4],
                                                       ifAdminStatus=tmp[5], ifMtu=tmp[6]))

        return intfs_info

    def get_interface_dict(self, ifname):
        """ get one interface attributes dict."""

        intf_info = dict()
        conf_str = CE_NC_GET_INTF % ifname
        recv_xml = get_nc_config(self.module, conf_str)

        if "<data/>" in recv_xml:
            return intf_info

        intf = re.findall(
            r'.*<ifName>(.*)</ifName>.*\s*'
            r'<ifPhyType>(.*)</ifPhyType>.*\s*'
            r'<ifNumber>(.*)</ifNumber>.*\s*'
            r'<ifDescr>(.*)</ifDescr>.*\s*'
            r'<isL2SwitchPort>(.*)</isL2SwitchPort>.*\s*'
            r'<ifAdminStatus>(.*)</ifAdminStatus>.*\s*'
            r'<ifMtu>(.*)</ifMtu>.*', recv_xml)

        if intf:
            intf_info = dict(ifName=intf[0][0], ifPhyType=intf[0][1],
                             ifNumber=intf[0][2], ifDescr=intf[0][3],
                             isL2SwitchPort=intf[0][4],
                             ifAdminStatus=intf[0][5], ifMtu=intf[0][6])

        return intf_info

    def create_interface(self, ifname, description, admin_state, mode, l2sub):
        """Create interface."""

        if l2sub:
            self.updates_cmd.append("interface %s mode l2" % ifname)
        else:
            self.updates_cmd.append("interface %s" % ifname)

        if not description:
            description = ''
        else:
            self.updates_cmd.append("description %s" % description)

        if l2sub:
            xmlstr = CE_NC_XML_CREATE_INTF_L2SUB % (ifname, description)
        else:
            xmlstr = CE_NC_XML_CREATE_INTF % (ifname, description)
        if admin_state and is_admin_state_enable(self.intf_type):
            xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (ifname, admin_state)
            if admin_state == 'up':
                self.updates_cmd.append("undo shutdown")
            else:
                self.updates_cmd.append("shutdown")
        if mode and is_portswitch_enalbe(self.intf_type):
            if mode == "layer2":
                xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (ifname, 'enable')
                self.updates_cmd.append('portswitch')
            elif mode == "layer3":
                xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (ifname, 'disable')
                self.updates_cmd.append('undo portswitch')

        conf_str = '<config> ' + xmlstr + ' </config>'
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CREATE_INTF")
        self.changed = True

    def delete_interface(self, ifname):
        """ Delete interface."""

        xmlstr = CE_NC_XML_DELETE_INTF % ifname
        conf_str = '<config> ' + xmlstr + ' </config>'
        self.updates_cmd.append('undo interface %s' % ifname)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "DELETE_INTF")
        self.changed = True

    def delete_interfaces(self, iftype):
        """ Delete interfaces with type."""

        xmlstr = ''
        intfs_list = self.intfs_info.get(iftype.lower())
        if not intfs_list:
            return

        for intf in intfs_list:
            xmlstr += CE_NC_XML_DELETE_INTF % intf['ifName']
            self.updates_cmd.append('undo interface %s' % intf['ifName'])

        conf_str = '<config> ' + xmlstr + ' </config>'
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "DELETE_INTFS")
        self.changed = True

    def merge_interface(self, ifname, description, admin_state, mode):
        """ Merge interface attributes."""

        xmlstr = ''
        change = False
        self.updates_cmd.append("interface %s" % ifname)
        if description and self.intf_info["ifDescr"] != description:
            xmlstr += CE_NC_XML_MERGE_INTF_DES % (ifname, description)
            self.updates_cmd.append("description %s" % description)
            change = True

        if admin_state and is_admin_state_enable(self.intf_type) \
                and self.intf_info["ifAdminStatus"] != admin_state:
            xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (ifname, admin_state)
            change = True
            if admin_state == "up":
                self.updates_cmd.append("undo shutdown")
            else:
                self.updates_cmd.append("shutdown")

        if is_portswitch_enalbe(self.intf_type):
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

        conf_str = '<config> ' + xmlstr + ' </config>'
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "MERGE_INTF_ATTR")
        self.changed = True

    def merge_interfaces(self, iftype, description, admin_state, mode):
        """ Merge interface attributes by type."""

        xmlstr = ''
        change = False
        intfs_list = self.intfs_info.get(iftype.lower())
        if not intfs_list:
            return

        for intf in intfs_list:
            if_change = False
            self.updates_cmd.append("interface %s" % intf['ifName'])
            if description and intf["ifDescr"] != description:
                xmlstr += CE_NC_XML_MERGE_INTF_DES % (
                    intf['ifName'], description)
                self.updates_cmd.append("description %s" % description)
                if_change = True
            if admin_state and is_admin_state_enable(self.intf_type)\
                    and intf["ifAdminStatus"] != admin_state:
                xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (
                    intf['ifName'], admin_state)
                if_change = True
                if admin_state == "up":
                    self.updates_cmd.append("undo shutdown")
                else:
                    self.updates_cmd.append("shutdown")

            if is_portswitch_enalbe(self.intf_type):
                if mode == "layer2" \
                        and intf["isL2SwitchPort"] != "true":
                    xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (
                        intf['ifName'], 'enable')
                    self.updates_cmd.append("portswitch")
                    if_change = True
                elif mode == "layer3" \
                        and intf["isL2SwitchPort"] != "false":
                    xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (
                        intf['ifName'], 'disable')
                    self.updates_cmd.append("undo portswitch")
                    if_change = True

            if if_change:
                change = True
            else:
                self.updates_cmd.pop()

        if not change:
            return

        conf_str = '<config> ' + xmlstr + ' </config>'
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "MERGE_INTFS_ATTR")
        self.changed = True

    def default_interface(self, ifname):
        """default_interface"""

        change = False
        xmlstr = ""
        self.updates_cmd.append("interface %s" % ifname)
        # set description default
        if self.intf_info["ifDescr"]:
            xmlstr += CE_NC_XML_MERGE_INTF_DES % (ifname, '')
            self.updates_cmd.append("undo description")
            change = True

        # set admin_status default
        if is_admin_state_enable(self.intf_type) \
                and self.intf_info["ifAdminStatus"] != 'up':
            xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (ifname, 'up')
            self.updates_cmd.append("undo shutdown")
            change = True

        # set portswitch default
        if is_portswitch_enalbe(self.intf_type) \
                and self.intf_info["isL2SwitchPort"] != "true":
            xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (ifname, 'enable')
            self.updates_cmd.append("portswitch")
            change = True

        if not change:
            return

        conf_str = '<config> ' + xmlstr + ' </config>'
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "SET_INTF_DEFAULT")
        self.changed = True

    def default_interfaces(self, iftype):
        """ Set interface config to default by type."""

        change = False
        xmlstr = ''
        intfs_list = self.intfs_info.get(iftype.lower())
        if not intfs_list:
            return

        for intf in intfs_list:
            if_change = False
            self.updates_cmd.append("interface %s" % intf['ifName'])

            # set description default
            if intf['ifDescr']:
                xmlstr += CE_NC_XML_MERGE_INTF_DES % (intf['ifName'], '')
                self.updates_cmd.append("undo description")
                if_change = True

            # set admin_status default
            if is_admin_state_enable(self.intf_type) and intf["ifAdminStatus"] != 'up':
                xmlstr += CE_NC_XML_MERGE_INTF_STATUS % (intf['ifName'], 'up')
                self.updates_cmd.append("undo shutdown")
                if_change = True

            # set portswitch default
            if is_portswitch_enalbe(self.intf_type) and intf["isL2SwitchPort"] != "true":
                xmlstr += CE_NC_XML_MERGE_INTF_L2ENABLE % (intf['ifName'], 'enable')
                self.updates_cmd.append("portswitch")
                if_change = True

            if if_change:
                change = True
            else:
                self.updates_cmd.pop()

        if not change:
            return

        conf_str = '<config> ' + xmlstr + ' </config>'
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "SET_INTFS_DEFAULT")
        self.changed = True

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
            self.intf_type = get_interface_type(self.interface)
            if not self.intf_type:
                self.module.fail_json(
                    msg='Error: interface name of %s'
                        ' is error.' % self.interface)

        elif self.interface_type:
            self.intf_type = get_interface_type(self.interface_type)
            if not self.intf_type or self.intf_type != self.interface_type.replace(" ", "").lower():
                self.module.fail_json(
                    msg='Error: interface type of %s'
                        ' is error.' % self.interface_type)

        if not self.intf_type:
            self.module.fail_json(
                msg='Error: interface or interface type %s is error.')

        # shutdown check
        if not is_admin_state_enable(self.intf_type) \
                and self.state == "present" and self.admin_state == "down":
            self.module.fail_json(
                msg='Error: The %s interface can not'
                    ' be shutdown.' % self.intf_type)

        # port switch mode check
        if not is_portswitch_enalbe(self.intf_type)\
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
        # check l2sub flag
        if self.l2sub:
            if not self.interface:
                self.module.fail_json(msg='Error: L2sub flag can not be set when there no interface set with.')
            if self.interface.count(".") != 1:
                self.module.fail_json(msg='Error: Interface name is invalid, it is not sub-interface.')

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
            self.proposed["l2sub"] = self.l2sub

        elif self.state == 'default':
            if self.description:
                self.proposed["description"] = ""
            if is_admin_state_enable(self.intf_type) and self.admin_state:
                self.proposed["admin_state"] = self.admin_state
            if is_portswitch_enalbe(self.intf_type) and self.mode:
                self.proposed["mode"] = self.mode

    def get_existing(self):
        """get_existing"""

        if self.intf_info:
            self.existing["interface"] = self.intf_info["ifName"]
            if is_admin_state_enable(self.intf_type):
                self.existing["admin_state"] = self.intf_info["ifAdminStatus"]
            self.existing["description"] = self.intf_info["ifDescr"]
            if is_portswitch_enalbe(self.intf_type):
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
                if is_admin_state_enable(self.intf_type):
                    self.end_state["admin_state"] = end_info["ifAdminStatus"]
                self.end_state["description"] = end_info["ifDescr"]
                if is_portswitch_enalbe(self.intf_type):
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
                    self.create_interface(self.interface,
                                          self.description,
                                          self.admin_state,
                                          self.mode,
                                          self.l2sub)
                else:
                    # merge interface
                    if self.description or self.admin_state or self.mode:
                        self.merge_interface(self.interface,
                                             self.description,
                                             self.admin_state,
                                             self.mode)

            elif self.state == 'absent':
                if self.intf_info:
                    # delete interface
                    self.delete_interface(self.interface)
                else:
                    # interface does not exist
                    self.module.fail_json(
                        msg='Error: interface does not exist.')

            else:       # default
                if not self.intf_info:
                    # error, interface does not exist
                    self.module.fail_json(
                        msg='Error: interface does not exist.')
                else:
                    self.default_interface(self.interface)

        # interface type config
        else:
            self.intfs_info = self.get_interfaces_dict()
            self.get_existing()
            if self.state == 'present':
                if self.intfs_info.get(self.intf_type.lower()):
                    if self.description or self.admin_state or self.mode:
                        self.merge_interfaces(self.intf_type,
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

        self.module.exit_json(**self.results)


def main():
    """main"""

    argument_spec = dict(
        interface=dict(required=False, type='str'),
        admin_state=dict(choices=['up', 'down'], required=False),
        description=dict(required=False, default=None),
        mode=dict(choices=['layer2', 'layer3'], required=False),
        interface_type=dict(required=False),
        l2sub=dict(required=False, default=False, type='bool'),
        state=dict(choices=['absent', 'present', 'default'],
                   default='present', required=False),
    )

    argument_spec.update(ce_argument_spec)
    interface = Interface(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
