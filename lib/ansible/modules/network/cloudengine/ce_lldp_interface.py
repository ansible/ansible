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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ce_lldp_interface
version_added: "2.10"
short_description: Manages INTERFACE LLDP configuration on HUAWEI CloudEngine switches.
description:
    - Manages INTERFACE LLDP configuration on HUAWEI CloudEngine switches.
author: xuxiaowei0512 (@CloudEngine-Ansible)
notes:
    - This module requires the netconf system service be enabled on the remote device being managed.
    - Recommended connection is C(netconf).
    - This module also works with C(local) connections for legacy playbooks.
options:
  lldpenable:
    description:
      - Set global LLDP enable state.
    type: str
    choices: ['enabled', 'disabled']
  function_lldp_interface_flag:
    description:
      - Used to distinguish between command line functions.
    type: str
    choices: ['disableINTERFACE','tlvdisableINTERFACE','tlvenableINTERFACE','intervalINTERFACE']
  type_tlv_disable:
    description:
      - Used to distinguish between command line functions.
    type: str
    choices: ['basic_tlv', 'dot3_tlv']
  type_tlv_enable:
    description:
      - Used to distinguish between command line functions.
    type: str
    choices: ['dot1_tlv','dcbx']
  lldpadminstatus:
    description:
      - Set interface lldp enable state.
    type: str
    choices: ['txOnly', 'rxOnly', 'txAndRx', 'disabled']
  ifname:
    description:
      - Interface name.
    type: str
  txinterval:
    description:
      - LLDP send message interval.
    type: int
  txprotocolvlanid:
    description:
      - Set tx protocol vlan id.
    type: int
  txvlannameid:
    description:
      - Set tx vlan name id.
    type: int
  vlannametxenable:
    description:
      - Set vlan name tx enable or not.
    type: bool
  manaddrtxenable:
    description:
      - Make it able to send management address TLV.
    type: bool
  portdesctxenable:
    description:
      - Enabling the ability to send a description of TLV.
    type: bool
  syscaptxenable:
    description:
      - Enable the ability to send system capabilities TLV.
    type: bool
  sysdesctxenable:
    description:
      - Enable the ability to send system description TLV.
    type: bool
  sysnametxenable:
    description:
      - Enable the ability to send system name TLV.
    type: bool
  portvlantxenable:
    description:
      - Enable port vlan tx.
    type: bool
  protovlantxenable:
    description:
      - Enable protocol vlan tx.
    type: bool
  protoidtxenable:
     description:
       - Enable the ability to send protocol identity TLV.
     type: bool
  macphytxenable:
    description:
      - Enable MAC/PHY configuration and state TLV to be sent.
    type: bool
  linkaggretxenable:
    description:
      - Enable the ability to send link aggregation TLV.
    type: bool
  maxframetxenable:
    description:
      - Enable the ability to send maximum frame length TLV.
    type: bool
  eee:
    description:
      - Enable the ability to send EEE TLV.
    type: bool
  dcbx:
    description:
      - Enable the ability to send DCBX TLV.
    type: bool
  state:
    description:
      - Manage the state of the resource.
    type: str
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''
  - name: "Configure global LLDP enable state"
    ce_lldp_interface_interface:
      lldpenable: enabled

  - name: "Configure interface lldp enable state"
    ce_lldp_interface:
      function_lldp_interface_flag: disableINTERFACE
      ifname: 10GE1/0/1
      lldpadminstatus: rxOnly
  - name: "Configure LLDP transmit interval and ensure global LLDP state is already enabled"
    ce_lldp_interface:
      function_lldp_interface_flag: intervalINTERFACE
      ifname: 10GE1/0/1
      txinterval: 4

  - name: "Configure basic-tlv: management-address TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: basic_tlv
      ifname: 10GE1/0/1
      manaddrtxenable: true

  - name: "Configure basic-tlv: prot description TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: basic_tlv
      ifname: 10GE1/0/1
      portdesctxenable: true

  - name: "Configure basic-tlv: system capabilities TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: basic_tlv
      ifname: 10GE1/0/1
      syscaptxenable: true

  - name: "Configure basic-tlv: system description TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: basic_tlv
      ifname: 10GE1/0/1
      sysdesctxenable: true

  - name: "Configure basic-tlv: system name TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: basic_tlv
      ifname: 10GE1/0/1
      sysnametxenable: true

  - name: "TLV types that are forbidden to be published on the configuration interface, link aggregation TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: dot3_tlv
      ifname: 10GE1/0/1
      linkAggreTxEnable: true

  - name: "TLV types that are forbidden to be published on the configuration interface, MAC/PHY configuration/status TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: dot3_tlv
      ifname: 10GE1/0/1
      macPhyTxEnable: true

  - name: "TLV types that are forbidden to be published on the configuration interface, maximum frame size TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: dot3_tlv
      ifname: 10GE1/0/1
      maxFrameTxEnable: true

  - name: "TLV types that are forbidden to be published on the configuration interface, EEE TLV"
    ce_lldp_interface:
      function_lldp_interface_flag: tlvdisableINTERFACE
      type_tlv_disable: dot3_tlv
      ifname: 10GE1/0/1
      eee: true

  - name: "Configure the interface to publish an optional DCBX TLV type "
    ce_lldp_interface:
      function_lldp_interface_flag: tlvenableINTERFACE
      ifname: 10GE1/0/1
      type_tlv_enable: dcbx
'''

RETURN = '''
proposed:
  description: k/v pairs of parameters passed into module
  returned: always
  type: dict
  sample: {
          "lldpenable": "enabled",
          "lldpadminstatus": "rxOnly",
          "function_lldp_interface_flag": "tlvenableINTERFACE",
          "type_tlv_enable": "dot1_tlv",
          "ifname": "10GE1/0/1",
          "state": "present"
          }
existing:
  description: k/v pairs of existing global LLDP configration
  returned: always
  type: dict
  sample: {
           "lldpenable": "disabled",
           "ifname": "10GE1/0/1",
           "lldpadminstatus": "txAndRx"
          }
end_state:
  description: k/v pairs of global DLDP configration after module execution
  returned: always
  type: dict
  sample: {
           "lldpenable": "enabled",
           "lldpadminstatus": "rxOnly",
           "function_lldp_interface_flag": "tlvenableINTERFACE",
           "type_tlv_enable": "dot1_tlv",
           "ifname": "10GE1/0/1"
          }
updates:
  description: command sent to the device
  returned: always
  type: list
  sample: [
           "lldp enable",
           "interface 10ge 1/0/1",
           "undo lldp disable",
           "lldp tlv-enable dot1-tlv vlan-name 4",
           ]
changed:
  description: check to see if a change was made on the device
  returned: always
  type: bool
  sample: true
'''

import copy
import re
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import set_nc_config, get_nc_config

CE_NC_GET_GLOBAL_LLDPENABLE_CONFIG = """
<filter type="subtree">
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpSys>
      <lldpEnable></lldpEnable>
    </lldpSys>
  </lldp>
</filter>
"""

CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG = """
<config>
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpSys operation="merge">
      <lldpEnable>%s</lldpEnable>
    </lldpSys>
  </lldp>
</config>
"""

CE_NC_GET_INTERFACE_LLDP_CONFIG = """
<filter type="subtree">
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpInterfaces>
      <lldpInterface>
        <ifName></ifName>
        <lldpAdminStatus></lldpAdminStatus>
      </lldpInterface>
    </lldpInterfaces>
  </lldp>
</filter>
"""

CE_NC_MERGE_INTERFACE_LLDP_CONFIG = """
<config>
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpInterfaces>
      <lldpInterface operation="merge">
        <ifName>%s</ifName>
        <lldpAdminStatus>%s</lldpAdminStatus>
      </lldpInterface>
    </lldpInterfaces>
  </lldp>
</config>
"""

CE_NC_GET_INTERFACE_INTERVAl_CONFIG = """
<filter type="subtree">
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpInterfaces>
      <lldpInterface>
        <ifName></ifName>
        <msgInterval>
          <txInterval></txInterval>
        </msgInterval>
      </lldpInterface>
    </lldpInterfaces>
  </lldp>
</filter>
"""

CE_NC_MERGE_INTERFACE_INTERVAl_CONFIG = """
<config>
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpInterfaces>
      <lldpInterface>
        <ifName>%s</ifName>
        <msgInterval operation="merge">
          <txInterval>%s</txInterval>
        </msgInterval>
      </lldpInterface>
    </lldpInterfaces>
  </lldp>
</config>
"""

CE_NC_GET_INTERFACE_TLV_ENABLE_CONFIG = """
<filter type="subtree">
    <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lldpInterfaces>
            <lldpInterface>
                <ifName></ifName>
                <tlvTxEnable>
                    <dcbx></dcbx>
                    <protoIdTxEnable></protoIdTxEnable>
                </tlvTxEnable>
            </lldpInterface>
        </lldpInterfaces>
    </lldp>
</filter>
"""

CE_NC_GET_INTERFACE_TLV_DISABLE_CONFIG = """
<filter type="subtree">
    <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lldpInterfaces>
            <lldpInterface>
                <ifName></ifName>
                <tlvTxEnable>
                    <manAddrTxEnable></manAddrTxEnable>
                    <portDescTxEnable></portDescTxEnable>
                    <sysCapTxEnable></sysCapTxEnable>
                    <sysDescTxEnable></sysDescTxEnable>
                    <sysNameTxEnable></sysNameTxEnable>
                    <linkAggreTxEnable></linkAggreTxEnable>
                    <macPhyTxEnable></macPhyTxEnable>
                    <maxFrameTxEnable></maxFrameTxEnable>
                    <eee></eee>
                </tlvTxEnable>
            </lldpInterface>
        </lldpInterfaces>
    </lldp>
</filter>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER = """
<config>
    <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lldpInterfaces>
            <lldpInterface>
                <ifName>%s</ifName>
                <tlvTxEnable operation="merge">
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_ENABLE_PROTOIDTXENABLE = """
                    <protoIdTxEnable>%s</protoIdTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_ENABLE_DCBX = """
                    <dcbx>%s</dcbx>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_MANADDRTXENABLE = """
                    <manAddrTxEnable>%s</manAddrTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_PORTDESCTXENABLE = """
                    <portDescTxEnable>%s</portDescTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_SYSCAPTXENABLE = """
                    <sysCapTxEnable>%s</sysCapTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_SYSDESCTXENABLE = """
                    <sysDescTxEnable>%s</sysDescTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_SYSNAMETXENABLE = """
                    <sysNameTxEnable>%s</sysNameTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_LINKAGGRETXENABLE = """
                    <linkAggreTxEnable>%s</linkAggreTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_MACPHYTXENABLE = """
                    <macPhyTxEnable>%s</macPhyTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_MAXFRAMETXENABLE = """
                    <maxFrameTxEnable>%s</maxFrameTxEnable>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_EEE = """
                    <eee>%s</eee>
"""

CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL = """
                </tlvTxEnable>
            </lldpInterface>
        </lldpInterfaces>
    </lldp>
</config>
"""

CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG = """
<config>
    <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lldpSys operation="merge">
            <lldpEnable>%s</lldpEnable>
        </lldpSys>
    </lldp>
</config>
"""


def get_interface_type(interface):
    """Gets the type of interface, such as 10GE"""

    if interface is None:
        return None

    iftype = None

    if interface.upper().startswith('GE'):
        iftype = 'ge'
    elif interface.upper().startswith('10GE'):
        iftype = '10ge'
    elif interface.upper().startswith('25GE'):
        iftype = '25ge'
    elif interface.upper().startswith('40GE'):
        iftype = '40ge'
    elif interface.upper().startswith('100GE'):
        iftype = '100ge'
    elif interface.upper().startswith('PORT-GROUP'):
        iftype = 'stack-Port'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None
    return iftype.lower()


class Lldp_interface(object):
    """Manage global lldp enable configuration"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)

        self.lldpenable = self.module.params['lldpenable'] or None
        self.function_lldp_interface_flag = self.module.params['function_lldp_interface_flag']
        self.type_tlv_disable = self.module.params['type_tlv_disable']
        self.type_tlv_enable = self.module.params['type_tlv_enable']
        self.ifname = self.module.params['ifname']
        if self.function_lldp_interface_flag == 'disableINTERFACE':
            self.ifname = self.module.params['ifname']
            self.lldpadminstatus = self.module.params['lldpadminstatus']
        elif self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
            if self.type_tlv_disable == 'basic_tlv':
                self.ifname = self.module.params['ifname']
                self.manaddrtxenable = self.module.params['manaddrtxenable']
                self.portdesctxenable = self.module.params['portdesctxenable']
                self.syscaptxenable = self.module.params['syscaptxenable']
                self.sysdesctxenable = self.module.params['sysdesctxenable']
                self.sysnametxenable = self.module.params['sysnametxenable']
            if self.type_tlv_disable == 'dot3_tlv':
                self.ifname = self.module.params['ifname']
                self.macphytxenable = self.module.params['macphytxenable']
                self.linkaggretxenable = self.module.params['linkaggretxenable']
                self.maxframetxenable = self.module.params['maxframetxenable']
                self.eee = self.module.params['eee']
        elif self.function_lldp_interface_flag == 'tlvenableINTERFACE':
            if self.type_tlv_enable == 'dot1_tlv':
                self.ifname = self.module.params['ifname']
                self.protoidtxenable = self.module.params['protoidtxenable']
            if self.type_tlv_enable == 'dcbx':
                self.ifname = self.module.params['ifname']
                self.dcbx = self.module.params['dcbx']
        elif self.function_lldp_interface_flag == 'intervalINTERFACE':
            self.ifname = self.module.params['ifname']
            self.txinterval = self.module.params['txinterval']
        self.state = self.module.params['state']

        self.lldp_conf = dict()
        self.conf_disable_exsit = False
        self.conf_interface_lldp_disable_exsit = False
        self.conf_interval_exsit = False
        self.conf_tlv_disable_exsit = False
        self.conf_tlv_enable_exsit = False
        self.enable_flag = 0
        self.check_params()
        self.existing_state_value = dict()
        self.existing_end_state_value = dict()
        self.interface_lldp_info = list()

        # state
        self.changed = False
        self.proposed_changed = dict()
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def check_params(self):
        """Check all input params"""

        if self.ifname:
            intf_type = get_interface_type(self.ifname)
            if not intf_type:
                self.module.fail_json(msg='Error: ifname name of %s is error.' % self.ifname)
            if (len(self.ifname) < 1) or (len(self.ifname) > 63):
                self.module.fail_json(msg='Error: Ifname length is beetween 1 and 63.')

        if self.function_lldp_interface_flag == 'intervalINTERFACE':
            if self.txinterval:
                if int(self.txinterval) < 1 or int(self.txinterval) > 32768:
                    self.module.fail_json(
                        msg='Error: The value of txinterval is out of [1 - 32768].')
                if self.ifname:
                    intf_type = get_interface_type(self.ifname)
                    if not intf_type:
                        self.module.fail_json(
                            msg='Error: ifname name of %s '
                                'is error.' % self.ifname)
                    if (len(self.ifname) < 1) or (len(self.ifname) > 63):
                        self.module.fail_json(
                            msg='Error: Ifname length is beetween 1 and 63.')

        if self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
            if self.type_tlv_disable == 'dot1_tlv':
                if self.ifname:
                    intf_type = get_interface_type(self.ifname)
                    if not intf_type:
                        self.module.fail_json(
                            msg='Error: ifname name of %s '
                                'is error.' % self.ifname)
                    if (len(self.ifname) < 1) or (len(self.ifname) > 63):
                        self.module.fail_json(
                            msg='Error: Ifname length is beetween 1 and 63.')

        if self.function_lldp_interface_flag == 'tlvenableINTERFACE':
            if self.type_tlv_enable == 'dot1_tlv':
                if self.ifname:
                    intf_type = get_interface_type(self.ifname)
                    if not intf_type:
                        self.module.fail_json(
                            msg='Error: ifname name of %s '
                                'is error.' % self.ifname)
                    if (len(self.ifname) < 1) or (len(self.ifname) > 63):
                        self.module.fail_json(
                            msg='Error: Ifname length is beetween 1 and 63.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already OK"""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def show_result(self):
        """Show result"""

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)

    def get_lldp_enable_pre_config(self):
        """Get lldp enable configure"""

        lldp_dict = dict()
        lldp_config = list()
        conf_enable_str = CE_NC_GET_GLOBAL_LLDPENABLE_CONFIG
        conf_enable_obj = get_nc_config(self.module, conf_enable_str)
        xml_enable_str = conf_enable_obj.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get lldp enable config info
        root_enable = ElementTree.fromstring(xml_enable_str)
        ntpsite_enable = root_enable.findall("lldp/lldpSys")
        for nexthop_enable in ntpsite_enable:
            for ele_enable in nexthop_enable:
                if ele_enable.tag in ["lldpEnable"]:
                    lldp_dict[ele_enable.tag] = ele_enable.text
                    if lldp_dict['lldpEnable'] == 'enabled':
                        self.enable_flag = 1
            lldp_config.append(dict(lldpenable=lldp_dict['lldpEnable']))
        return lldp_config

    def get_interface_lldp_disable_pre_config(self):
        """Get interface undo lldp disable configure"""
        lldp_dict = dict()
        interface_lldp_disable_dict = dict()
        if self.enable_flag == 1:
            conf_enable_str = CE_NC_GET_INTERFACE_LLDP_CONFIG
            conf_enable_obj = get_nc_config(self.module, conf_enable_str)
            if "<data/>" in conf_enable_obj:
                return
            xml_enable_str = conf_enable_obj.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
            root = ElementTree.fromstring(xml_enable_str)
            lldp_disable_enable = root.findall("lldp/lldpInterfaces/lldpInterface")
            for nexthop_enable in lldp_disable_enable:
                name = nexthop_enable.find("ifName")
                status = nexthop_enable.find("lldpAdminStatus")
                if name is not None and status is not None:
                    interface_lldp_disable_dict[name.text] = status.text
        return interface_lldp_disable_dict

    def get_interface_lldp_disable_config(self):
        lldp_config = list()
        interface_lldp_disable_dict_tmp = dict()
        if self.state == "present":
            if self.ifname:
                interface_lldp_disable_dict_tmp = self.get_interface_lldp_disable_pre_config()
                key_list = interface_lldp_disable_dict_tmp.keys()
                if len(key_list) != 0:
                    for key in key_list:
                        if key == self.ifname:
                            if interface_lldp_disable_dict_tmp[key] != self.lldpadminstatus:
                                self.conf_interface_lldp_disable_exsit = True
                            else:
                                self.conf_interface_lldp_disable_exsit = False
                elif self.ifname not in key_list:
                    self.conf_interface_lldp_disable_exsit = True
                elif (len(key_list) == 0) and self.ifname and self.lldpadminstatus:
                    self.conf_interface_lldp_disable_exsit = True
                lldp_config.append(interface_lldp_disable_dict_tmp)
        return lldp_config

    def get_interface_tlv_disable_config(self):
        lldp_config = list()
        lldp_dict = dict()
        cur_interface_mdn_cfg = dict()
        exp_interface_mdn_cfg = dict()

        if self.enable_flag == 1:
            conf_str = CE_NC_GET_INTERFACE_TLV_DISABLE_CONFIG
            conf_obj = get_nc_config(self.module, conf_str)
            if "<data/>" in conf_obj:
                return lldp_config
            xml_str = conf_obj.replace('\r', '').replace('\n', '')
            xml_str = xml_str.replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "")
            xml_str = xml_str.replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
            root = ElementTree.fromstring(xml_str)
            lldp_tlvdisable_ifname = root.findall("lldp/lldpInterfaces/lldpInterface")
            for ele in lldp_tlvdisable_ifname:
                ifname_tmp = ele.find("ifName")
                manaddrtxenable_tmp = ele.find("tlvTxEnable/manAddrTxEnable")
                portdesctxenable_tmp = ele.find("tlvTxEnable/portDescTxEnable")
                syscaptxenable_tmp = ele.find("tlvTxEnable/sysCapTxEnable")
                sysdesctxenable_tmp = ele.find("tlvTxEnable/sysDescTxEnable")
                sysnametxenable_tmp = ele.find("tlvTxEnable/sysNameTxEnable")
                linkaggretxenable_tmp = ele.find("tlvTxEnable/linkAggreTxEnable")
                macphytxenable_tmp = ele.find("tlvTxEnable/macPhyTxEnable")
                maxframetxenable_tmp = ele.find("tlvTxEnable/maxFrameTxEnable")
                eee_tmp = ele.find("tlvTxEnable/eee")
                if ifname_tmp is not None:
                    if ifname_tmp.text is not None:
                        cur_interface_mdn_cfg["ifname"] = ifname_tmp.text
                if ifname_tmp is not None and manaddrtxenable_tmp is not None:
                    if manaddrtxenable_tmp.text is not None:
                        cur_interface_mdn_cfg["manaddrtxenable"] = manaddrtxenable_tmp.text
                if ifname_tmp is not None and portdesctxenable_tmp is not None:
                    if portdesctxenable_tmp.text is not None:
                        cur_interface_mdn_cfg['portdesctxenable'] = portdesctxenable_tmp.text
                if ifname_tmp is not None and syscaptxenable_tmp is not None:
                    if syscaptxenable_tmp.text is not None:
                        cur_interface_mdn_cfg['syscaptxenable'] = syscaptxenable_tmp.text
                if ifname_tmp is not None and sysdesctxenable_tmp is not None:
                    if sysdesctxenable_tmp.text is not None:
                        cur_interface_mdn_cfg['sysdesctxenable'] = sysdesctxenable_tmp.text
                if ifname_tmp is not None and sysnametxenable_tmp is not None:
                    if sysnametxenable_tmp.text is not None:
                        cur_interface_mdn_cfg['sysnametxenable'] = sysnametxenable_tmp.text
                if ifname_tmp is not None and linkaggretxenable_tmp is not None:
                    if linkaggretxenable_tmp.text is not None:
                        cur_interface_mdn_cfg['linkaggretxenable'] = linkaggretxenable_tmp.text
                if ifname_tmp is not None and macphytxenable_tmp is not None:
                    if macphytxenable_tmp.text is not None:
                        cur_interface_mdn_cfg['macphytxenable'] = macphytxenable_tmp.text
                if ifname_tmp is not None and maxframetxenable_tmp is not None:
                    if maxframetxenable_tmp.text is not None:
                        cur_interface_mdn_cfg['maxframetxenable'] = maxframetxenable_tmp.text
                if ifname_tmp is not None and eee_tmp is not None:
                    if eee_tmp.text is not None:
                        cur_interface_mdn_cfg['eee'] = eee_tmp.text
                if self.state == "present":
                    if self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
                        if self.type_tlv_disable == 'basic_tlv':
                            if self.ifname:
                                exp_interface_mdn_cfg['ifname'] = self.ifname
                                if self.manaddrtxenable:
                                    exp_interface_mdn_cfg['manaddrtxenable'] = self.manaddrtxenable
                                if self.portdesctxenable:
                                    exp_interface_mdn_cfg['portdesctxenable'] = self.portdesctxenable
                                if self.syscaptxenable:
                                    exp_interface_mdn_cfg['syscaptxenable'] = self.syscaptxenable
                                if self.sysdesctxenable:
                                    exp_interface_mdn_cfg['sysdesctxenable'] = self.sysdesctxenable
                                if self.sysnametxenable:
                                    exp_interface_mdn_cfg['sysnametxenable'] = self.sysnametxenable
                                if self.ifname == ifname_tmp.text:
                                    key_list = exp_interface_mdn_cfg.keys()
                                    key_list_cur = cur_interface_mdn_cfg.keys()
                                    if len(key_list) != 0:
                                        for key in key_list:
                                            if key == "ifname" and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(ifname=cur_interface_mdn_cfg['ifname']))
                                            if "manaddrtxenable" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(manaddrtxenable=cur_interface_mdn_cfg['manaddrtxenable']))
                                            if "portdesctxenable" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(portdesctxenable=cur_interface_mdn_cfg['portdesctxenable']))
                                            if "syscaptxenable" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(syscaptxenable=cur_interface_mdn_cfg['syscaptxenable']))
                                            if "sysdesctxenable" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(sysdesctxenable=cur_interface_mdn_cfg['sysdesctxenable']))
                                            if "sysnametxenable" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(sysnametxenable=cur_interface_mdn_cfg['sysnametxenable']))
                                            if key in key_list_cur:
                                                if str(exp_interface_mdn_cfg[key]) != str(cur_interface_mdn_cfg[key]):
                                                    self.conf_tlv_disable_exsit = True
                                                    self.changed = True
                                                    return lldp_config
                                            else:
                                                self.conf_tlv_disable_exsit = True
                                                return lldp_config

                        if self.type_tlv_disable == 'dot3_tlv':
                            if self.ifname:
                                exp_interface_mdn_cfg['ifname'] = self.ifname
                                if self.linkaggretxenable:
                                    exp_interface_mdn_cfg['linkaggretxenable'] = self.linkaggretxenable
                                if self.macphytxenable:
                                    exp_interface_mdn_cfg['macphytxenable'] = self.macphytxenable
                                if self.maxframetxenable:
                                    exp_interface_mdn_cfg['maxframetxenable'] = self.maxframetxenable
                                if self.eee:
                                    exp_interface_mdn_cfg['eee'] = self.eee
                                if self.ifname == ifname_tmp.text:
                                    key_list = exp_interface_mdn_cfg.keys()
                                    key_list_cur = cur_interface_mdn_cfg.keys()
                                    if len(key_list) != 0:
                                        for key in key_list:
                                            if key == "ifname" and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(ifname=cur_interface_mdn_cfg['ifname']))
                                            if "linkaggretxenable" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(linkaggretxenable=cur_interface_mdn_cfg['linkaggretxenable']))
                                            if "macphytxenable" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(macphytxenable=cur_interface_mdn_cfg['macphytxenable']))
                                            if "maxframetxenable" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(maxframetxenable=cur_interface_mdn_cfg['maxframetxenable']))
                                            if "eee" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(eee=cur_interface_mdn_cfg['eee']))
                                            if key in key_list_cur:
                                                if str(exp_interface_mdn_cfg[key]) != str(cur_interface_mdn_cfg[key]):
                                                    self.conf_tlv_disable_exsit = True
                                                    self.changed = True
                                                    return lldp_config
                                            else:
                                                self.conf_tlv_disable_exsit = True
                                                return lldp_config
        return lldp_config

    def get_interface_tlv_enable_config(self):
        lldp_config = list()
        lldp_dict = dict()
        cur_interface_mdn_cfg = dict()
        exp_interface_mdn_cfg = dict()
        if self.enable_flag == 1:
            conf_str = CE_NC_GET_INTERFACE_TLV_ENABLE_CONFIG
            conf_obj = get_nc_config(self.module, conf_str)
            if "<data/>" in conf_obj:
                return lldp_config
            xml_str = conf_obj.replace('\r', '').replace('\n', '')
            xml_str = xml_str.replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "")
            xml_str = xml_str.replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
            root = ElementTree.fromstring(xml_str)
            lldpenablesite = root.findall("lldp/lldpInterfaces/lldpInterface")
            for ele in lldpenablesite:
                ifname_tmp = ele.find("ifName")
                protoidtxenable_tmp = ele.find("tlvTxEnable/protoIdTxEnable")
                dcbx_tmp = ele.find("tlvTxEnable/dcbx")
                if ifname_tmp is not None:
                    if ifname_tmp.text is not None:
                        cur_interface_mdn_cfg["ifname"] = ifname_tmp.text
                if ifname_tmp is not None and protoidtxenable_tmp is not None:
                    if protoidtxenable_tmp.text is not None:
                        cur_interface_mdn_cfg["protoidtxenable"] = protoidtxenable_tmp.text
                if ifname_tmp is not None and dcbx_tmp is not None:
                    if dcbx_tmp.text is not None:
                        cur_interface_mdn_cfg['dcbx'] = dcbx_tmp.text
                if self.state == "present":
                    if self.function_lldp_interface_flag == 'tlvenableINTERFACE':
                        if self.type_tlv_enable == 'dot1_tlv':
                            if self.ifname:
                                exp_interface_mdn_cfg['ifname'] = self.ifname
                                if self.protoidtxenable:
                                    exp_interface_mdn_cfg['protoidtxenable'] = self.protoidtxenable
                                if self.ifname == ifname_tmp.text:
                                    key_list = exp_interface_mdn_cfg.keys()
                                    key_list_cur = cur_interface_mdn_cfg.keys()
                                    if len(key_list) != 0:
                                        for key in key_list:
                                            if "protoidtxenable" == str(key) and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(protoidtxenable=cur_interface_mdn_cfg['protoidtxenable']))
                                            if key in key_list_cur:
                                                if str(exp_interface_mdn_cfg[key]) != str(cur_interface_mdn_cfg[key]):
                                                    self.conf_tlv_enable_exsit = True
                                                    self.changed = True
                                                    return lldp_config
                                            else:
                                                self.conf_tlv_enable_exsit = True
                                                return lldp_config
                        if self.type_tlv_enable == 'dcbx':
                            if self.ifname:
                                exp_interface_mdn_cfg['ifname'] = self.ifname
                                if self.dcbx:
                                    exp_interface_mdn_cfg['dcbx'] = self.dcbx
                                if self.ifname == ifname_tmp.text:
                                    key_list = exp_interface_mdn_cfg.keys()
                                    key_list_cur = cur_interface_mdn_cfg.keys()
                                    if len(key_list) != 0:
                                        for key in key_list:
                                            if "dcbx" == key and self.ifname == cur_interface_mdn_cfg['ifname']:
                                                lldp_config.append(dict(dcbx=cur_interface_mdn_cfg['dcbx']))
                                            if key in key_list_cur:
                                                if str(exp_interface_mdn_cfg[key]) != str(cur_interface_mdn_cfg[key]):
                                                    self.conf_tlv_enable_exsit = True
                                                    self.changed = True
                                                    return lldp_config
                                            else:
                                                self.conf_tlv_enable_exsit = True
                                                return lldp_config
        return lldp_config

    def get_interface_interval_config(self):
        lldp_config = list()
        lldp_dict = dict()
        cur_interface_mdn_cfg = dict()
        exp_interface_mdn_cfg = dict()
        interface_lldp_disable_dict_tmp2 = self.get_interface_lldp_disable_pre_config()
        if self.enable_flag == 1:
            if interface_lldp_disable_dict_tmp2[self.ifname] != 'disabled':
                conf_str = CE_NC_GET_INTERFACE_INTERVAl_CONFIG
                conf_obj = get_nc_config(self.module, conf_str)
                if "<data/>" in conf_obj:
                    return lldp_config
                xml_str = conf_obj.replace('\r', '').replace('\n', '')
                xml_str = xml_str.replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "")
                xml_str = xml_str.replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
                root = ElementTree.fromstring(xml_str)
                txintervalsite = root.findall("lldp/lldpInterfaces/lldpInterface")
                for ele in txintervalsite:
                    ifname_tmp = ele.find("ifName")
                    txinterval_tmp = ele.find("msgInterval/txInterval")
                    if ifname_tmp is not None:
                        if ifname_tmp.text is not None:
                            cur_interface_mdn_cfg["ifname"] = ifname_tmp.text
                    if txinterval_tmp is not None:
                        if txinterval_tmp.text is not None:
                            cur_interface_mdn_cfg["txinterval"] = txinterval_tmp.text
                    if self.state == "present":
                        if self.ifname:
                            exp_interface_mdn_cfg["ifname"] = self.ifname
                            if self.txinterval:
                                exp_interface_mdn_cfg["txinterval"] = self.txinterval
                            if self.ifname == ifname_tmp.text:
                                key_list = exp_interface_mdn_cfg.keys()
                                key_list_cur = cur_interface_mdn_cfg.keys()
                                if len(key_list) != 0:
                                    for key in key_list:
                                        if "txinterval" == str(key) and self.ifname == cur_interface_mdn_cfg['ifname']:
                                            lldp_config.append(dict(ifname=cur_interface_mdn_cfg['ifname'], txinterval=exp_interface_mdn_cfg['txinterval']))
                                        if key in key_list_cur:
                                            if str(exp_interface_mdn_cfg[key]) != str(cur_interface_mdn_cfg[key]):
                                                self.conf_interval_exsit = True
                                                lldp_config.append(cur_interface_mdn_cfg)
                                                return lldp_config
                                        else:
                                            self.conf_interval_exsit = True
                                            return lldp_config
        return lldp_config

    def config_global_lldp_enable(self):
        if self.state == 'present':
            if self.enable_flag == 0 and self.lldpenable == 'enabled':
                xml_str = CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG % self.lldpenable
                ret_xml = set_nc_config(self.module, xml_str)
                self.check_response(ret_xml, "LLDP_ENABLE_CONFIG")
                self.changed = True
            elif self.enable_flag == 1 and self.lldpenable == 'disabled':
                xml_str = CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG % self.lldpenable
                ret_xml = set_nc_config(self.module, xml_str)
                self.check_response(ret_xml, "LLDP_ENABLE_CONFIG")
                self.changed = True

    def config_interface_lldp_disable_config(self):
        if self.function_lldp_interface_flag == 'disableINTERFACE':
            if self.enable_flag == 1 and self.conf_interface_lldp_disable_exsit:
                if self.ifname:
                    xml_str = CE_NC_MERGE_INTERFACE_LLDP_CONFIG % (self.ifname, self.lldpadminstatus)
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "INTERFACE_LLDP_DISABLE_CONFIG")
                    self.changed = True

    def config_interface_tlv_disable_config(self):
        if self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
            if self.enable_flag == 1 and self.conf_tlv_disable_exsit:
                if self.type_tlv_disable == 'basic_tlv':
                    if self.ifname:
                        if self.portdesctxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_PORTDESCTXENABLE % self.portdesctxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_PORTDESCTXENABLE")
                            self.changed = True
                        if self.manaddrtxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_MANADDRTXENABLE % self.manaddrtxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_MANADDRTXENABLE")
                            self.changed = True
                        if self.syscaptxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_SYSCAPTXENABLE % self.syscaptxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_SYSCAPTXENABLE")
                            self.changed = True
                        if self.sysdesctxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_SYSDESCTXENABLE % self.sysdesctxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_SYSDESCTXENABLE")
                            self.changed = True
                        if self.sysnametxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_SYSNAMETXENABLE % self.sysnametxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_SYSNAMETXENABLE")
                            self.changed = True
                if self.type_tlv_disable == 'dot3_tlv':
                    if self.ifname:
                        if self.linkaggretxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_LINKAGGRETXENABLE % self.linkaggretxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_LINKAGGRETXENABLE")
                            self.changed = True
                        if self.macphytxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_MACPHYTXENABLE % self.macphytxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_MACPHYTXENABLE")
                            self.changed = True
                        if self.maxframetxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_MAXFRAMETXENABLE % self.maxframetxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_MAXFRAMETXENABLE")
                            self.changed = True
                        if self.eee:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_DISABLE_EEE % self.eee) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_DISABLE_EEE")
                            self.changed = True

    def config_interface_tlv_enable_config(self):
        if self.function_lldp_interface_flag == 'tlvenableINTERFACE':
            if self.enable_flag == 1 and self.conf_tlv_enable_exsit:
                if self.type_tlv_enable == 'dot1_tlv':
                    if self.ifname:
                        if self.protoidtxenable:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_ENABLE_PROTOIDTXENABLE % self.protoidtxenable) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_ENABLE_DOT1_PORT_VLAN")
                            self.changed = True
                if self.type_tlv_enable == 'dcbx':
                    if self.ifname:
                        if self.dcbx:
                            xml_str = (CE_NC_MERGE_INTERFACE_TLV_CONFIG_HEADER % self.ifname) + \
                                (CE_NC_MERGE_INTERFACE_TLV_CONFIG_ENABLE_DCBX % self.dcbx) + \
                                CE_NC_MERGE_INTERFACE_TLV_CONFIG_TAIL
                            ret_xml = set_nc_config(self.module, xml_str)
                            self.check_response(ret_xml, "TLV_ENABLE_DCBX_VLAN")
                            self.changed = True

    def config_interface_interval_config(self):
        if self.function_lldp_interface_flag == 'intervalINTERFACE':
            tmp = self.get_interface_lldp_disable_pre_config()
            if self.enable_flag == 1 and self.conf_interval_exsit and tmp[self.ifname] != 'disabled':
                if self.ifname:
                    if self.txinterval:
                        xml_str = CE_NC_MERGE_INTERFACE_INTERVAl_CONFIG % (self.ifname, self.txinterval)
                        ret_xml = set_nc_config(self.module, xml_str)
                        self.check_response(ret_xml, "INTERFACE_INTERVAL_CONFIG")
                        self.changed = True

    def get_existing(self):
        """get existing information"""
        self.get_lldp_enable_pre_config()
        if self.lldpenable:
            self.existing['globalLLDPENABLE'] = self.get_lldp_enable_pre_config()
        if self.function_lldp_interface_flag == 'disableINTERFACE':
            self.existing['disableINTERFACE'] = self.get_interface_lldp_disable_config()
        if self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
            self.existing['tlvdisableINTERFACE'] = self.get_interface_tlv_disable_config()
        if self.function_lldp_interface_flag == 'tlvenableINTERFACE':
            self.existing['tlvenableINTERFACE'] = self.get_interface_tlv_enable_config()
        if self.function_lldp_interface_flag == 'intervalINTERFACE':
            self.existing['intervalINTERFACE'] = self.get_interface_interval_config()

    def get_proposed(self):
        """get proposed"""
        if self.lldpenable:
            self.proposed = dict(lldpenable=self.lldpenable)
        if self.function_lldp_interface_flag == 'disableINTERFACE':
            if self.enable_flag == 1:
                self.proposed = dict(ifname=self.ifname, lldpadminstatus=self.lldpadminstatus)
        if self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
            if self.enable_flag == 1:
                if self.type_tlv_disable == 'basic_tlv':
                    if self.ifname:
                        if self.manaddrtxenable:
                            self.proposed = dict(ifname=self.ifname, manaddrtxenable=self.manaddrtxenable)
                        if self.portdesctxenable:
                            self.proposed = dict(ifname=self.ifname, portdesctxenable=self.portdesctxenable)
                        if self.syscaptxenable:
                            self.proposed = dict(ifname=self.ifname, syscaptxenable=self.syscaptxenable)
                        if self.sysdesctxenable:
                            self.proposed = dict(ifname=self.ifname, sysdesctxenable=self.sysdesctxenable)
                        if self.sysnametxenable:
                            self.proposed = dict(ifname=self.ifname, sysnametxenable=self.sysnametxenable)
                if self.type_tlv_disable == 'dot3_tlv':
                    if self.ifname:
                        if self.linkaggretxenable:
                            self.proposed = dict(ifname=self.ifname, linkaggretxenable=self.linkaggretxenable)
                        if self.macphytxenable:
                            self.proposed = dict(ifname=self.ifname, macphytxenable=self.macphytxenable)
                        if self.maxframetxenable:
                            self.proposed = dict(ifname=self.ifname, maxframetxenable=self.maxframetxenable)
                        if self.eee:
                            self.proposed = dict(ifname=self.ifname, eee=self.eee)
        if self.function_lldp_interface_flag == 'tlvenableINTERFACE':
            if self.enable_flag == 1:
                if self.type_tlv_enable == 'dot1_tlv':
                    if self.ifname:
                        if self.protoidtxenable:
                            self.proposed = dict(ifname=self.ifname, protoidtxenable=self.protoidtxenable)
                if self.type_tlv_enable == 'dcbx':
                    if self.ifname:
                        if self.dcbx:
                            self.proposed = dict(ifname=self.ifname, dcbx=self.dcbx)
        if self.function_lldp_interface_flag == 'intervalINTERFACE':
            tmp1 = self.get_interface_lldp_disable_pre_config()
            if self.enable_flag == 1 and tmp1[self.ifname] != 'disabled':
                self.proposed = dict(ifname=self.ifname, txinterval=self.txinterval)

    def config_lldp_interface(self):
        """config lldp interface"""
        if self.lldpenable:
            self.config_global_lldp_enable()
        if self.function_lldp_interface_flag == 'disableINTERFACE':
            self.config_interface_lldp_disable_config()
        elif self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
            self.config_interface_tlv_disable_config()
        elif self.function_lldp_interface_flag == 'tlvenableINTERFACE':
            self.config_interface_tlv_enable_config()
        elif self.function_lldp_interface_flag == 'intervalINTERFACE':
            self.config_interface_interval_config()

    def get_end_state(self):
        """get end_state information"""
        self.get_lldp_enable_pre_config()
        if self.lldpenable:
            self.end_state['globalLLDPENABLE'] = self.get_lldp_enable_pre_config()
        if self.function_lldp_interface_flag == 'disableINTERFACE':
            self.end_state['disableINTERFACE'] = self.get_interface_lldp_disable_config()
        if self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
            self.end_state['tlvdisableINTERFACE'] = self.get_interface_tlv_disable_config()
        if self.function_lldp_interface_flag == 'tlvenableINTERFACE':
            self.end_state['tlvenableINTERFACE'] = self.get_interface_tlv_enable_config()
        if self.function_lldp_interface_flag == 'intervalINTERFACE':
            self.end_state['intervalINTERFACE'] = self.get_interface_interval_config()

    def get_update_cmd(self):
        """Get updated commands"""

        cmds = []
        if self.state == "present":
            if self.lldpenable == "enabled":
                cmds.append("lldp enable")
                if self.function_lldp_interface_flag == 'disableINTERFACE':
                    if self.ifname:
                        cmds.append("%s %s" % ("interface", self.ifname))
                        if self.lldpadminstatus == 'disabled':
                            cmds.append("lldp disable")
                        else:
                            cmds.append("undo lldp disable")
                elif self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
                    if self.type_tlv_disable == 'basic_tlv':
                        if self.ifname:
                            cmds.append("%s %s" % ("interface", self.ifname))
                            if self.manaddrtxenable:
                                if self.manaddrtxenable == "false":
                                    cmds.append("lldp tlv-disable basic-tlv management-address")
                                if self.manaddrtxenable == "true":
                                    cmds.append("undo lldp tlv-disable basic-tlv management-address")
                            if self.portdesctxenable:
                                if self.portdesctxenable == "false":
                                    cmds.append("lldp tlv-disable basic-tlv port-description")
                                if self.portdesctxenable == "true":
                                    cmds.append("undo lldp tlv-disable basic-tlv port-description")
                            if self.syscaptxenable:
                                if self.syscaptxenable == "false":
                                    cmds.append("lldp tlv-disable basic-tlv system-capability")
                                if self.syscaptxenable == "true":
                                    cmds.append("undo lldp tlv-disable basic-tlv system-capability")
                            if self.sysdesctxenable:
                                if self.sysdesctxenable == "false":
                                    cmds.append("lldp tlv-disable basic-tlv system-description")
                                if self.sysdesctxenable == "true":
                                    cmds.append("undo lldp tlv-disable basic-tlv system-description")
                            if self.sysnametxenable:
                                if self.sysnametxenable == "false":
                                    cmds.append("lldp tlv-disable basic-tlv system-name")
                                if self.sysnametxenable == "true":
                                    cmds.append("undo lldp tlv-disable basic-tlv system-name")
                    if self.type_tlv_disable == 'dot3_tlv':
                        if self.ifname:
                            cmds.append("%s %s" % ("interface", self.ifname))
                            if self.linkaggretxenable:
                                if self.linkaggretxenable == "false":
                                    cmds.append("lldp tlv-disable dot3-tlv link-aggregation")
                                if self.linkaggretxenable == "true":
                                    cmds.append("undo lldp tlv-disable dot3-tlv link-aggregation")
                            if self.macphytxenable:
                                if self.macphytxenable == "false":
                                    cmds.append("lldp tlv-disable dot3-tlv mac-physic")
                                if self.macphytxenable == "true":
                                    cmds.append("undo lldp tlv-disable dot3-tlv mac-physic")
                            if self.maxframetxenable:
                                if self.maxframetxenable == "false":
                                    cmds.append("lldp tlv-disable dot3-tlv max-frame-size")
                                if self.maxframetxenable == "true":
                                    cmds.append("undo lldp tlv-disable dot3-tlv max-frame-size")
                            if self.eee:
                                if self.eee == "false":
                                    cmds.append("lldp tlv-disable dot3-tlv eee")
                                if self.eee == "true":
                                    cmds.append("undo lldp tlv-disable dot3-tlv eee")
                elif self.function_lldp_interface_flag == 'tlvenableINTERFACE':
                    if self.type_tlv_enable == 'dot1_tlv':
                        if self.ifname:
                            cmds.append("%s %s" % ("interface", self.ifname))
                            if self.protoidtxenable:
                                if self.protoidtxenable == "false":
                                    cmds.append("undo lldp tlv-enable dot1-tlv protocol-identity")
                                if self.protoidtxenable == "true":
                                    cmds.append("lldp tlv-enable dot1-tlv protocol-identity")
                    if self.type_tlv_enable == 'dcbx':
                        if self.ifname:
                            cmds.append("%s %s" % ("interface", self.ifname))
                            if self.dcbx:
                                if self.dcbx == "false":
                                    cmds.append("undo lldp tlv-enable dcbx")
                                if self.dcbx == "true":
                                    cmds.append("lldp tlv-enable dcbx")
                elif self.function_lldp_interface_flag == 'intervalINTERFACE':
                    if self.ifname:
                        cmds.append("%s %s" % ("interface", self.ifname))
                        if self.txinterval:
                            cmds.append("lldp transmit fast-mode interval %s" % self.txinterval)
            elif self.lldpenable == "disabled":
                cmds.append("undo lldp enable")
            else:
                if self.enable_flag == 1:
                    if self.function_lldp_interface_flag == 'disableINTERFACE':
                        if self.ifname:
                            cmds.append("interface %s" % self.ifname)
                            if self.lldpadminstatus == 'disabled':
                                cmds.append("lldp disable")
                            else:
                                cmds.append("undo lldp disable")
                    elif self.function_lldp_interface_flag == 'tlvdisableINTERFACE':
                        if self.type_tlv_disable == 'basic_tlv':
                            if self.ifname:
                                cmds.append("interface %s" % self.ifname)
                                if self.manaddrtxenable:
                                    if self.manaddrtxenable == "false":
                                        cmds.append("lldp tlv-disable basic-tlv management-address")
                                    if self.manaddrtxenable == "true":
                                        cmds.append("undo lldp tlv-disable basic-tlv management-address")
                                if self.portdesctxenable:
                                    if self.portdesctxenable == "false":
                                        cmds.append("lldp tlv-disable basic-tlv port-description")
                                    if self.portdesctxenable == "true":
                                        cmds.append("undo lldp tlv-disable basic-tlv port-description")
                                if self.syscaptxenable:
                                    if self.syscaptxenable == "false":
                                        cmds.append("lldp tlv-disable basic-tlv system-capability")
                                    if self.syscaptxenable == "true":
                                        cmds.append("undo lldp tlv-disable basic-tlv system-capability")
                                if self.sysdesctxenable:
                                    if self.sysdesctxenable == "false":
                                        cmds.append("lldp tlv-disable basic-tlv system-description")
                                    if self.sysdesctxenable == "true":
                                        cli_str = "%s %s\n" % (cli_str, "undo lldp tlv-disable basic-tlv system-description")
                                if self.sysnametxenable:
                                    if self.sysnametxenable == "false":
                                        cmds.append("lldp tlv-disable basic-tlv system-name")
                                    if self.sysnametxenable == "true":
                                        cmds.append("undo lldp tlv-disable basic-tlv system-name")
                        if self.type_tlv_disable == 'dot3_tlv':
                            if self.ifname:
                                cmds.append("interface %s" % self.ifname)
                                if self.linkaggretxenable:
                                    if self.linkaggretxenable == "false":
                                        cmds.append("lldp tlv-disable dot3-tlv link-aggregation")
                                    if self.linkaggretxenable == "true":
                                        cmds.append("undo lldp tlv-disable dot3-tlv link-aggregation")
                                if self.macphytxenable:
                                    if self.macphytxenable == "false":
                                        cmds.append("lldp tlv-disable dot3-tlv mac-physic")
                                    if self.macphytxenable == "true":
                                        cli_str = "%s %s\n" % (cli_str, "undo lldp tlv-disable dot3-tlv mac-physic")
                                if self.maxframetxenable:
                                    if self.maxframetxenable == "false":
                                        cmds.append("lldp tlv-disable dot3-tlv max-frame-size")
                                    if self.maxframetxenable == "true":
                                        cmds.append("undo lldp tlv-disable dot3-tlv max-frame-size")
                                if self.eee:
                                    if self.eee == "false":
                                        cmds.append("lldp tlv-disable dot3-tlv eee")
                                    if self.eee == "true":
                                        cmds.append("undo lldp tlv-disable dot3-tlv eee")
                    elif self.function_lldp_interface_flag == 'tlvenableINTERFACE':
                        if self.type_tlv_enable == 'dot1_tlv':
                            if self.ifname:
                                cmds.append("interface %s" % self.ifname)
                                if self.protoidtxenable:
                                    if self.protoidtxenable == "false":
                                        cmds.append("undo lldp tlv-enable dot1-tlv protocol-identity")
                                    if self.protoidtxenable == "true":
                                        cmds.append("lldp tlv-enable dot1-tlv protocol-identity")
                        if self.type_tlv_enable == 'dcbx':
                            if self.ifname:
                                cmds.append("interface %s" % self.ifname)
                                if self.dcbx:
                                    if self.dcbx == "false":
                                        cmds.append("undo lldp tlv-enable dcbx")
                                    if self.dcbx == "true":
                                        cmds.append("lldp tlv-enable dcbx")
                    elif self.function_lldp_interface_flag == 'intervalINTERFACE':
                        if self.ifname:
                            cmds.append("interface %s" % self.ifname)
                            if self.txinterval:
                                cmds.append("lldp transmit fast-mode interval %s" % self.txinterval)
        self.updates_cmd = cmds

    def work(self):
        """Execute task"""
        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.config_lldp_interface()
        self.get_update_cmd()
        self.get_end_state()
        self.show_result()


def main():
    """Main function"""

    argument_spec = dict(
        lldpenable=dict(choices=['enabled', 'disabled']),
        function_lldp_interface_flag=dict(choices=['disableINTERFACE', 'tlvdisableINTERFACE', 'tlvenableINTERFACE', 'intervalINTERFACE'], type='str'),
        type_tlv_disable=dict(choices=['basic_tlv', 'dot3_tlv'], type='str'),
        type_tlv_enable=dict(choices=['dot1_tlv', 'dcbx'], type='str'),
        ifname=dict(type='str'),
        lldpadminstatus=dict(choices=['txOnly', 'rxOnly', 'txAndRx', 'disabled'], type='str'),
        manaddrtxenable=dict(type='bool'),
        portdesctxenable=dict(type='bool'),
        syscaptxenable=dict(type='bool'),
        sysdesctxenable=dict(type='bool'),
        sysnametxenable=dict(type='bool'),
        portvlantxenable=dict(type='bool'),
        protovlantxenable=dict(type='bool'),
        txprotocolvlanid=dict(type='int'),
        vlannametxenable=dict(type='bool'),
        txvlannameid=dict(type='int'),
        txinterval=dict(type='int'),
        protoidtxenable=dict(type='bool'),
        macphytxenable=dict(type='bool'),
        linkaggretxenable=dict(type='bool'),
        maxframetxenable=dict(type='bool'),
        eee=dict(type='bool'),
        dcbx=dict(type='bool'),
        state=dict(type='str', choices=['absent', 'present'], default='present'),
    )

    lldp_interface_obj = Lldp_interface(argument_spec)
    lldp_interface_obj.work()


if __name__ == '__main__':
    main()
