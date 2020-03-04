#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ce_is_is_interface
version_added: "2.10"
author: xuxiaowei0512 (@CloudEngine-Ansible)
short_description: Manages isis interface configuration on HUAWEI CloudEngine devices.
description:
  - Manages isis process id, creates a isis instance id or deletes a process id on HUAWEI CloudEngine devices.
notes:
  - Interface must already be a L3 port when using this module.
  - This module requires the netconf system service be enabled on the remote device being managed.
  - This module works with connection C(netconf).
options:
  instance_id:
    description:
      - Specifies the id of a isis process.
        The value is a number of 1 to 4294967295.
    required: true
    type: int
  ifname:
    description:
      - A L3 interface.
    required: true
    type: str
  leveltype:
    description:
      - level type for three types.
    type: str
    choices: ['level_1', 'level_2', 'level_1_2']
  level1dispriority:
    description:
      - the dispriority of the level1.
        The value is a number of 1 to 127.
    type: int
  level2dispriority:
    description:
      - the dispriority of the level1.
        The value is a number of 1 to 127.
    type: int
  silentenable:
    description:
      - enable the interface can send isis message.
        The value is a bool type.
    type: bool
  silentcost:
    description:
      - Specifies whether the routing cost of the silent interface is 0.
        The value is a bool type.
    type: bool
  typep2penable:
    description:
      - Simulate the network type of the interface as P2P.
        The value is a bool type.
    type: bool
  snpacheck:
    description:
      - Enable SNPA check for LSPs and SNPs.
        The value is a bool type.
    type: bool
  p2pnegotiationmode:
    description:
       - Set the P2P neighbor negotiation type.
    type: str
    choices: ['2_way', '3_way', '3_wayonly']
  p2ppeeripignore:
    description:
      - When the P2P hello packet is received, no IP address check is performed.
        The value is a bool type.
    type: bool
  ppposicpcheckenable:
    description:
      - Interface for setting PPP link protocol to check OSICP negotiation status.
        The value is a bool type.
    type: bool
  level1cost:
    description:
      - Specifies the link cost of the interface when performing Level-1 SPF calculation.
        The value is a number of 0 to 16777215.
    type: int
  level2cost:
    description:
      - Specifies the link cost of the interface when performing Level-2 SPF calculation.
        The value is a number of 0 to 16777215.
    type: int
  bfdstaticen:
    description:
      - Configure static BFD on a specific interface enabled with ISIS.
        The value is a bool type.
    type: bool
  bfdblocken:
    description:
      - Blocking interfaces to dynamically create BFD features.
        The value is a bool type.
    type: bool
  state:
    description:
      - Determines whether the config should be present or not on the device.
    type: str
    default: 'present'
    choices: ['present', 'absent']
"""

EXAMPLES = '''
  - name: "create vlan and config vlanif"
    ce_config:
      lines: 'vlan {{ test_vlan_id }},quit,interface {{test_intf_vlanif}},ip address {{test_vlanif_ip}} 24'
      match: none

  - name: "create eth-trunk and config eth-trunk"
    ce_config:
      lines: 'interface {{test_intf_trunk}},undo portswitch,ip address {{test_trunk_ip}} 24'
      match: none

  - name: "create vpn instance"
    ce_config:
      lines: 'ip vpn-instance {{test_vpn}},ipv4-family'
      match: none

  - name: Set isis circuit-level
    ce_is_is_interface:
      instance_id: 3
      ifname: Eth-Trunk10
      leveltype: level_1_2
      state: present

  - name: Set isis level1dispriority
    ce_is_is_interface:
      instance_id: 3
      ifname: Eth-Trunk10
      level1dispriority: 0
      state: present

  - name: Set isis level2dispriority
    ce_is_is_interface:
      instance_id: 3
      ifname: Eth-Trunk10
      level2dispriority: 0
      state: present

  - name: Set isis silentenable
    ce_is_is_interface:
      instance_id: 3
      ifname: Eth-Trunk10
      silentenable: true
      state: present

  - name: Set vpn name
    ce_is_is_instance:
      instance_id: 22
      vpn_name: vpn1
      state: present
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "addr_type": null,
        "create_type": null,
        "dest_addr": null,
        "out_if_name": "10GE1/0/1",
        "session_name": "bfd_l2link",
        "src_addr": null,
        "state": "present",
        "use_default_ip": true,
        "vrf_name": null
    }
existing:
    description: k/v pairs of existing configuration
    returned: always
    type: dict
    sample: {
        "session": {}
    }
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {
        "session": {
            "addrType": "IPV4",
            "createType": "SESS_STATIC",
            "destAddr": null,
            "outIfName": "10GE1/0/1",
            "sessName": "bfd_l2link",
            "srcAddr": null,
            "useDefaultIp": "true",
            "vrfName": null
        }
    }
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: [
        "bfd bfd_l2link bind peer-ip default-ip interface 10ge1/0/1"
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import sys
import socket
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config

CE_NC_GET_ISIS = """
    <filter type="subtree">
      <isiscomm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
      %s
      </isiscomm>
    </filter>
"""

CE_NC_GET_ISIS_INTERFACE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isCircuits>
              <isCircuit>
                <ifName></ifName>
                <circuitLevelType></circuitLevelType>
                <level1DisPriority></level1DisPriority>
                <level2DisPriority></level2DisPriority>
                <silentEnable></silentEnable>
                <silentCost></silentCost>
                <typeP2pEnable></typeP2pEnable>
                <snpaCheck></snpaCheck>
                <p2pNegotiationMode></p2pNegotiationMode>
                <p2pPeerIPIgnore></p2pPeerIPIgnore>
                <pPPOsicpCheckEnable></pPPOsicpCheckEnable>
                <level1Cost></level1Cost>
                <level2Cost></level2Cost>
              </isCircuit>
            </isCircuits>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_INTERFACE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isCircuits>
              <isCircuit operation="merge">
              %s
              </isCircuit>
            </isCircuits>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_INTERFACE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isCircuits>
              <isCircuit operation="delete">
              %s
              </isCircuit>
            </isCircuits>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_BFDINTERFACE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isCircMts>
                  <isCircMt>
                    <bfdStaticEn></bfdStaticEn>
                    <bfdBlockEn></bfdBlockEn>
                  </isCircMt>
                </isCircMts>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_BFDINTERFACE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isCircMts>
                  <isCircMt operation="merge">
                  %s
                  </isCircMt>
                </isCircMts>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_BFDINTERFACE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isCircMts>
                  <isCircMt operation="delete">
                  %s
                  </isCircMt>
                </isCircMts>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""


def is_valid_ip_vpn(vpname):
    """check ip vpn"""

    if not vpname:
        return False

    if vpname == "_public_":
        return False

    if len(vpname) < 1 or len(vpname) > 31:
        return False

    return True


def check_ip_addr(ipaddr):
    """check ip address, Supports IPv4 and IPv6"""

    if not ipaddr or '\x00' in ipaddr:
        return False

    try:
        res = socket.getaddrinfo(ipaddr, 0, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM,
                                 0, socket.AI_NUMERICHOST)
        return bool(res)
    except socket.gaierror:
        err = sys.exc_info()[1]
        if err.args[0] == socket.EAI_NONAME:
            return False
        raise

    return True


def check_default_ip(ipaddr):
    """check the default multicast IP address"""

    # The value ranges from 224.0.0.107 to 224.0.0.250
    if not check_ip_addr(ipaddr):
        return False

    if ipaddr.count(".") != 3:
        return False

    ips = ipaddr.split(".")
    if ips[0] != "224" or ips[1] != "0" or ips[2] != "0":
        return False

    if not ips[3].isdigit() or int(ips[3]) < 107 or int(ips[3]) > 250:
        return False

    return True


def get_interface_type(interface):
    """get the type of interface, such as 10GE, ETH-TRUNK, VLANIF..."""

    if interface.upper().startswith('GE'):
        return 'ge'
    elif interface.upper().startswith('10GE'):
        return '10ge'
    elif interface.upper().startswith('25GE'):
        return '25ge'
    elif interface.upper().startswith('4X10GE'):
        return '4x10ge'
    elif interface.upper().startswith('40GE'):
        return '40ge'
    elif interface.upper().startswith('100GE'):
        return '100ge'
    elif interface.upper().startswith('VLANIF'):
        return 'vlanif'
    elif interface.upper().startswith('LOOPBACK'):
        return 'loopback'
    elif interface.upper().startswith('METH'):
        return 'meth'
    elif interface.upper().startswith('ETH-TRUNK'):
        return 'eth-trunk'
    elif interface.upper().startswith('VBDIF'):
        return 'vbdif'
    elif interface.upper().startswith('NVE'):
        return 'nve'
    elif interface.upper().startswith('TUNNEL'):
        return 'tunnel'
    elif interface.upper().startswith('ETHERNET'):
        return 'ethernet'
    elif interface.upper().startswith('FCOE-PORT'):
        return 'fcoe-port'
    elif interface.upper().startswith('FABRIC-PORT'):
        return 'fabric-port'
    elif interface.upper().startswith('STACK-PORT'):
        return 'stack-port'
    elif interface.upper().startswith('NULL'):
        return'null'
    else:
        return None


class ISIS_Instance(object):
    """Manages ISIS Instance"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.instance_id = self.module.params['instance_id']
        self.ifname = self.module.params['ifname']
        self.leveltype = self.module.params['leveltype']
        self.level1dispriority = self.module.params['level1dispriority']
        self.level2dispriority = self.module.params['level2dispriority']
        self.silentenable = self.module.params['silentenable']
        self.silentcost = self.module.params['silentcost']
        self.typep2penable = self.module.params['typep2penable']
        self.snpacheck = self.module.params['snpacheck']
        self.p2pnegotiationmode = self.module.params['p2pnegotiationmode']
        self.p2ppeeripignore = self.module.params['p2ppeeripignore']
        self.ppposicpcheckenable = self.module.params['ppposicpcheckenable']
        self.level1cost = self.module.params['level1cost']
        self.level2cost = self.module.params['level2cost']
        self.bfdstaticen = self.module.params['bfdstaticen']
        self.bfdblocken = self.module.params['bfdblocken']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.isis_dict = dict()
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """init module"""
        mutually_exclusive = [["level1dispriority", "level2dispriority"],
                              ["level1cost", "level2cost"]]
        self.module = AnsibleModule(
            argument_spec=self.spec,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

    def get_isis_dict(self):
        """bfd config dict"""

        isis_dict = dict()
        isis_dict["instance"] = dict()
        conf_str = CE_NC_GET_ISIS % (
            (CE_NC_GET_ISIS_INTERFACE % self.instance_id))
        if self.bfdstaticen or self.bfdblocken:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_BFDINTERFACE % self.instance_id))

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return isis_dict

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)

        #
        glb = root.find("isiscomm/isSites/isSite/isCircuits/isCircuit")
        if self.bfdstaticen or self.bfdblocken:
            glb = root.find("isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isCircMts/isCircMt")
        if glb:
            for attr in glb:
                isis_dict["instance"][attr.tag] = attr.text

        return isis_dict

    def config_session(self):
        """configures bfd session"""

        xml_str = ""
        instance = self.isis_dict["instance"]
        if not self.instance_id:
            return xml_str
        if self.ifname:
            xml_str = "<ifName>%s</ifName>" % self.ifname
            self.updates_cmd.append("interface %s" % self.ifname)
        if self.state == "present":
            self.updates_cmd.append("isis enable %s" % self.instance_id)

            if self.leveltype:
                if self.leveltype == "level_1":
                    xml_str += "<circuitLevelType>level_1</circuitLevelType>"
                    self.updates_cmd.append("isis circuit-level level-1")
                elif self.leveltype == "level_2":
                    xml_str += "<circuitLevelType>level_2</circuitLevelType>"
                    self.updates_cmd.append("isis circuit-level level-2")
                elif self.leveltype == "level_1_2":
                    xml_str += "<circuitLevelType>level_1_2</circuitLevelType>"
                    self.updates_cmd.append("isis circuit-level level-1-2")
            if self.level1dispriority is not None:
                xml_str += "<level1DisPriority>%s</level1DisPriority>" % self.level1dispriority
                self.updates_cmd.append("isis dis-priority %s level-1" % self.level1dispriority)
            if self.level2dispriority is not None:
                xml_str += "<level2DisPriority>%s</level2DisPriority>" % self.level2dispriority
                self.updates_cmd.append("isis dis-priority %s level-2" % self.level2dispriority)
            if self.p2pnegotiationmode:
                if self.p2pnegotiationmode == "2_way":
                    xml_str += "<p2pNegotiationMode>2_way</p2pNegotiationMode>"
                    self.updates_cmd.append("isis ppp-negotiation 2-way")
                elif self.p2pnegotiationmode == "3_way":
                    xml_str += "<p2pNegotiationMode>3_way</p2pNegotiationMode>"
                    self.updates_cmd.append("isis ppp-negotiation 3-way")
                elif self.p2pnegotiationmode == "3_wayonly":
                    xml_str += "<p2pNegotiationMode>3_wayonly</p2pNegotiationMode>"
                    self.updates_cmd.append("isis ppp-negotiation only")
            if self.level1cost is not None:
                xml_str += "<level1Cost>%s</level1Cost>" % self.level1cost
                self.updates_cmd.append("isis cost %s level-1" % self.level1cost)
            if self.level2cost is not None:
                xml_str += "<level2Cost>%s</level2Cost>" % self.level2cost
                self.updates_cmd.append("isis cost %s level-2" % self.level2cost)

        else:
            # absent
            self.updates_cmd.append("undo isis enable")
            if self.leveltype and self.leveltype == instance.get("circuitLevelType"):
                xml_str += "<circuitLevelType>level_1_2</circuitLevelType>"
                self.updates_cmd.append("undo isis circuit-level")
            if self.level1dispriority is not None and self.level1dispriority == instance.get("level1DisPriority"):
                xml_str += "<level1DisPriority>64</level1DisPriority>"
                self.updates_cmd.append("undo isis dis-priority %s level-1" % self.level1dispriority)
            if self.level2dispriority is not None and self.level2dispriority == instance.get("level2dispriority"):
                xml_str += "<level2dispriority>64</level2dispriority>"
                self.updates_cmd.append("undo isis dis-priority %s level-2" % self.level2dispriority)
            if self.p2pnegotiationmode and self.p2pnegotiationmode == instance.get("p2pNegotiationMode"):
                xml_str += "<p2pNegotiationMode/>"
                self.updates_cmd.append("undo isis ppp-negotiation")
            if self.level1cost is not None and self.level1cost == instance.get("level1Cost"):
                xml_str += "<level1Cost/>"
                self.updates_cmd.append("undo isis cost %s level-1" % self.level1cost)
            if self.level2cost is not None and self.level2cost == instance.get("level2Cost"):
                xml_str += "<level2Cost/>"
                self.updates_cmd.append("undo isis cost %s level-2" % self.level2cost)

        if self.silentenable and instance.get("silentEnable", "false") == "false":
            xml_str += "<silentEnable>true</silentEnable>"
            self.updates_cmd.append("isis silent")
        elif not self.silentenable and instance.get("silentEnable", "false") == "true":
            xml_str += "<silentEnable>false</silentEnable>"
            self.updates_cmd.append("undo isis silent")

        if self.silentcost and instance.get("silentCost", "false") == "false":
            xml_str += "<silentCost>true</silentCost>"
            self.updates_cmd.append("isis silent advertise-zero-cost")
        elif not self.silentcost and instance.get("silentCost", "false") == "true":
            xml_str += "<silentCost>false</silentCost>"

        if self.typep2penable and instance.get("typeP2pEnable", "false") == "false":
            xml_str += "<typeP2pEnable>true</typeP2pEnable>"
            self.updates_cmd.append("isis circuit-type p2p")
        elif not self.typep2penable and instance.get("typeP2pEnable", "false") == "true":
            xml_str += "<typeP2pEnable>false</typeP2pEnable>"
            self.updates_cmd.append("undo isis circuit-type")

        if self.snpacheck and instance.get("snpaCheck", "false") == "false":
            xml_str += "<snpaCheck>true</snpaCheck>"
            self.updates_cmd.append("isis circuit-type p2p strict-snpa-check")
        elif not self.snpacheck and instance.get("snpaCheck", "false") == "true":
            xml_str += "<snpaCheck>false</snpaCheck>"

        if self.p2ppeeripignore and instance.get("p2pPeerIPIgnore", "false") == "false":
            xml_str += "<p2pPeerIPIgnore>true</p2pPeerIPIgnore>"
            self.updates_cmd.append("isis peer-ip-ignore")
        elif not self.p2ppeeripignore and instance.get("p2pPeerIPIgnore", "false") == "true":
            xml_str += "<p2pPeerIPIgnore>false</p2pPeerIPIgnore>"
            self.updates_cmd.append("undo isis peer-ip-ignore")

        if self.ppposicpcheckenable and instance.get("pPPOsicpCheckEnable", "false") == "false":
            xml_str += "<pPPOsicpCheckEnable>true</pPPOsicpCheckEnable>"
            self.updates_cmd.append("isis ppp-osicp-check")
        elif not self.ppposicpcheckenable and instance.get("pPPOsicpCheckEnable", "false") == "true":
            xml_str += "<pPPOsicpCheckEnable>false</pPPOsicpCheckEnable>"
            self.updates_cmd.append("undo isis ppp-osicp-check")
        if self.bfdstaticen and instance.get("bfdStaticEn", "false") == "false":
            xml_str += "<bfdStaticEn>true</bfdStaticEn>"
            self.updates_cmd.append("isis bfd static")
        elif not self.bfdstaticen and instance.get("bfdStaticEn", "false") == "true":
            xml_str += "<bfdStaticEn>false</bfdStaticEn>"
            self.updates_cmd.append("undo isis bfd static")
        if self.bfdblocken and instance.get("bfdBlockEn", "false") == "false":
            xml_str += "<bfdBlockEn>true</bfdBlockEn>"
            self.updates_cmd.append("isis bfd block")
        elif not self.bfdblocken and instance.get("bfdBlockEn", "false") == "true":
            xml_str += "<bfdBlockEn>false</bfdBlockEn>"
            self.updates_cmd.append("undo isis bfd block")

        if self.state == "present":
            if self.bfdstaticen is not None or self.bfdblocken is not None:
                return CE_NC_MERGE_ISIS_BFDINTERFACE % (self.instance_id, xml_str)
            return CE_NC_MERGE_ISIS_INTERFACE % (self.instance_id, xml_str)
        else:
            if self.bfdstaticen is not None or self.bfdblocken is not None:
                return CE_NC_DELETE_ISIS_BFDINTERFACE % (self.instance_id, xml_str)
            return CE_NC_DELETE_ISIS_INTERFACE % (self.instance_id, xml_str)

    def netconf_load_config(self, xml_str):
        """load bfd config by netconf"""

        if not xml_str:
            return

        xml_cfg = """
            <config>
            <isiscomm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
            %s
            </isiscomm>
            </config>""" % xml_str
        set_nc_config(self.module, xml_cfg)
        self.changed = True

    def check_params(self):
        """Check all input params"""

        # check instance id
        if not self.instance_id:
            self.module.fail_json(msg="Error: Missing required arguments: instance_id.")

        if self.instance_id:
            if self.instance_id < 1 or self.instance_id > 4294967295:
                self.module.fail_json(msg="Error: Instance id is not ranges from 1 to 4294967295.")

        # check level1dispriority
        if self.level1dispriority is not None:
            if self.level1dispriority < 0 or self.level1dispriority > 127:
                self.module.fail_json(msg="Error: level1dispriority is not ranges from 0 to 127.")

        if self.level2dispriority is not None:
            if self.level2dispriority < 0 or self.level2dispriority > 127:
                self.module.fail_json(msg="Error: level2dispriority is not ranges from 0 to 127.")

        if self.level1cost is not None:
            if self.level1cost < 0 or self.level1cost > 16777215:
                self.module.fail_json(msg="Error: level1cost is not ranges from 0 to 16777215.")

        if self.level2cost is not None:
            if self.level2cost < 0 or self.level2cost > 16777215:
                self.module.fail_json(msg="Error: level2cost is not ranges from 0 to 16777215.")

    def get_proposed(self):
        """get proposed info"""
        self.proposed["instance_id"] = self.instance_id
        self.proposed["ifname"] = self.ifname
        self.proposed["leveltype"] = self.leveltype
        self.proposed["level1dispriority"] = self.level1dispriority
        self.proposed["level2dispriority"] = self.level2dispriority
        self.proposed["silentenable"] = self.silentenable
        self.proposed["silentcost"] = self.silentcost
        self.proposed["typep2penable"] = self.typep2penable
        self.proposed["snpacheck"] = self.snpacheck
        self.proposed["p2pnegotiationmode"] = self.p2pnegotiationmode
        self.proposed["p2ppeeripignore"] = self.p2ppeeripignore
        self.proposed["ppposicpcheckenable"] = self.ppposicpcheckenable
        self.proposed["level1cost"] = self.level1cost
        self.proposed["level2cost"] = self.level2cost
        self.proposed["bfdstaticen"] = self.bfdstaticen
        self.proposed["bfdblocken"] = self.bfdblocken
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if not self.isis_dict:
            self.existing["instance"] = None
        else:
            self.existing["instance"] = self.isis_dict.get("instance")

    def get_end_state(self):
        """get end state info"""

        isis_dict = self.get_isis_dict()
        if not isis_dict:
            self.end_state["instance"] = None
        else:
            self.end_state["instance"] = isis_dict.get("instance")
        if self.existing == self.end_state:
            self.changed = False

    def work(self):
        """worker"""

        self.check_params()
        self.isis_dict = self.get_isis_dict()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        xml_str = ''
        if self.instance_id:
            xml_str += self.config_session()

        # update to device
        if xml_str:
            self.netconf_load_config(xml_str)
            self.changed = True

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
        instance_id=dict(required=True, type='int'),
        ifname=dict(required=True, type='str'),
        leveltype=dict(required=False, type='str', choices=['level_1', 'level_2', 'level_1_2']),
        level1dispriority=dict(required=False, type='int'),
        level2dispriority=dict(required=False, type='int'),
        silentenable=dict(required=False, type='bool'),
        silentcost=dict(required=False, type='bool'),
        typep2penable=dict(required=False, type='bool'),
        snpacheck=dict(required=False, type='bool'),
        p2pnegotiationmode=dict(required=False, type='str', choices=['2_way', '3_way', '3_wayonly']),
        p2ppeeripignore=dict(required=False, type='bool'),
        ppposicpcheckenable=dict(required=False, type='bool'),
        level1cost=dict(required=False, type='int'),
        level2cost=dict(required=False, type='int'),
        bfdstaticen=dict(required=False, type='bool'),
        bfdblocken=dict(required=False, type='bool'),
        state=dict(required=False, default='present', choices=['present', 'absent'])
    )

    module = ISIS_Instance(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
