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
module: ne_interface_common
version_added: "2.6"
short_description: Manages common interface configuration.
description:
    - Manages configuration of an interface on HUAWEI netengine routers.
author: Shijiawei (@netengine-Ansible)
notes:
    - C(state=default) removes the configuration of the interface.
    - C(state=absent) deletes the interface.
options:
    name:
        description:
            - The textual name of the interface. The value of this object should be the name of the
              interface as assigned by the local device and should be suitable for use in commands
              entered at the device's `console'. This might be a text name, depending on the interface
              naming syntax of the device. The value is a string of 1 to 63 characters.
        required: true
        default: null
    description:
        description:
            - Description of an interface. The value is a string of 1 to 242 characters.
        required: false
        default: null
    admin_state:
        description:
            - Administrative status of an interface.
              up: Administratively Up.
              down: Administratively Down.
        required: false
        default: null
        choices: ['up', 'down']
    clear_ip_df:
        description:
            - Clear the Don't Fragment field of IP packets on an interface.
        required: false
        default: null
        choices: ['true', 'false']
    trap_enable:
        description:
            - Enable the trap function on an interface.
        required: false
        default: null
        choices: ['true', 'false']
    stat_enable:
        description:
            - Enable the statistics function on an interface.
        required: false
        default: null
        choices: ['true', 'false']
    stat_mode:
        description:
            - Mode of statistics collection.
            base_interface: statistics are collected based on interfaces.
            base_vlan_group: statistics are collected based on VLANs,
                             only L2 Sub-interface interface can be configured.
        required: false
        default: null
        choices: ['base_interface', 'base_vlan_group']
    mtu:
        description:
            - Maximum transmission unit of an interface. The value is an integer ranging from 0 to 64000, in bytes.
              The server may restrict the allowed values for this parameter, depending on the interface's type.
        required: false
        default: null
    mtu_spread:
        description:
            - Spread the MTU of main interface to subinterface.
        required: false
        default: null
        choices: ['true', 'false']
    bandwidth:
        description:
            - Specify MIB-referenced bandwidth of an interface. The value is an integer ranging from 1 to 1000000.
        required: false
        default: null
    stat_interval:
        description:
            - Interval at which flow statistics are collected on an interface.
              The value is an integer ranging from 10 to 600 and must be a multiple of 10.
        required: false
        default: null
    l2sub:
        description:
            - Identify an L2 Sub-interface.
        required: false
        default: null
        choices: ['true', 'false']
    mac_address:
        description:
            - Config MAC Address. The value is a string of 5 to 14 characters. The value is in the
              H-H-H format, where H is a 4-digit hexadecimal number, such as 00e0 and fc01. If an
              H contains less than four digits, 0s are added ahead. For example, e0 is equal to 00e0.
        required: false
        default: null
        choices: ['true', 'false']
    input_rising_rate:
        description:
            - Input bandwidth usage trap threshold. The value is an integer ranging from 1 to 100.
              If Interface input flow bandwidth usage exceeded the value, alarm will be raised.
        required: false
        default: null
    input_resume_rate:
        description:
            - Input bandwidth usage resume threshold. The value is an integer ranging from 1 to
              input_rising_rate. If Interface input flow bandwidth usage was restored to the value,
              alarm will recover.
        required: false
        default: null
    output_rising_rate:
        description:
            - Output bandwidth usage trap threshold. The value is an integer ranging from 1 to 100.
              If Interface output flow bandwidth usage exceeded the trap threshold, alarm will be raised.
        required: false
        default: null
    output_resume_rate:
        description:
            - Output bandwidth usage resume threshold. The value is an integer ranging from 1 to
              output_rising_rate. If Interface output flow bandwidth usage was restored to the
              value, alarm will recover.
        required: false
        default: null
    ip_stat_enable:
        description:
            - Enable forward statistics.
        required: false
        default: null
        choices: ['true', 'false']
    ip_stat_mode:
        description:
            - Forward statistics mode.
              forward: Forward mode statistics.
              mac: MAC mode statistics.
        required: false
        default: null
        choices: ['forward', 'mac']
    ve_group_type:
        description:
            - Virtual-Ethernet interface type.
              l2-terminate: Layer 2 Terminate Virtual-Ethernet interface.
              l3-access: Layer 3 Access Virtual-Ethernet interface.
              l3-terminate: Layer 3 Terminate Virtual-Ethernet interface.
        required: false
        default: null
        choices: ['l2-terminate', 'l3-access', 'l3-terminate']
    ve_group_id:
        description:
            - Virtual-Ethernet group ID.
        required: false
        default: null
    ve_forward_mode:
        description:
            - Virtual-Ethernet forward mode type.
              through: Software loopback.
              loopback: Hardware loopback.
              invalid: None.
        required: false
        default: null
        choices: ['through', 'loopback', 'invalid']
    unknow_unicast_alarm:
        description:
            - Unknown-unicast alarm threshold. The value is an integer ranging from 1 to 100.
        required: false
        default: null
    mru:
        description:
            - Maximum receive unit of an interface. The value is an integer ranging from 46 to 9600.
        required: false
        default: null
    mru_stat_enable:
        description:
            - Enable discard statistics of maximum receive unit of an interface.
        required: false
        default: null
        choices: ['true', 'false']
    phyif_mac_stat_enable:
        description:
            - Enable the traffic statistics function on a main interface.
        required: false
        default: null
        choices: ['true', 'false']
    vbdif_forward_loopback:
        description:
            - Set the VBDIF loopback forward mode.
        required: false
        default: null
        choices: ['true', 'false']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present', 'absent', 'default', 'query']
'''

EXAMPLES = '''
- name: interface_common module test
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
  - name: Create sub interface and config sub interface statistic enable
    ne_interface:
      name: Eth-Trunk100.1
      stat_enable: true
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"name": "Eth-Trunk100.1",
             "stat_enable": "true",
             "state": "present"}
existing:
    description: k/v pairs of existing interface
    returned: always
    type: dict
    sample: {}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"admin_state": "up",
             "clear_ip_df": "false",
             "l2sub": "false",
             "mtu_spread": "false",
             "name": "Eth-Trunk100.1",
             "stat_enable": "true",
             "stat_mode": "base_interface",
             "trap_enable": "true"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface Eth-Trunk100.1", "statistic enable"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import re
import logging

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

# Interface 模块私有宏定义
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_OPTYPE_CREATE
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_OPTYPE_MERGE
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_OPTYPE_DELETE
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_GET_IFM_HEAD
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_GET_IFM_TAIL
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_SET_IFM_HEAD
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_SET_IFM_TAIL

# Interface 模块私有接口公共函数
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_value
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_head
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_head_with_operation
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_tail
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_process_delete

logging.basicConfig(filename='/opt/python_logger.log', level=logging.INFO)

INTERFACE_XML2CLI = {'ifName': 'name',
                     'ifDescr': 'description',
                     'ifAdminStatus': 'admin_state',
                     'ifDf': 'clear_ip_df',
                     'ifTrapEnable': 'trap_enable',
                     'ifStatiEnable': 'stat_enable',
                     'statMode': 'stat_mode',
                     'ifMtu': 'mtu',
                     'spreadMtuFlag': 'mtu_spread',
                     'ifBandwidth': 'bandwidth',
                     'ifStatItvl': 'stat_interval',
                     'l2SubIfFlag': 'l2sub',
                     'ifCfgMac': 'mac_address'}

INTERFACE_SUBLIST_XML2CLI = {'inputRisingRate': 'input_rising_rate',
                             'inputResumeRate': 'input_resume_rate',
                             'outputRisingRate': 'output_rising_rate',
                             'outputResumeRate': 'output_resume_rate',
                             'ifIpStatiEnable': 'ip_stat_enable',
                             'ifIpStatiMode': 'ip_stat_mode',
                             'veIfType': 've_group_type',
                             'veGroupId': 've_group_id',
                             'veForwarMode': 've_forward_mode',
                             'unknownUnicastAlarm': 'unknow_unicast_alarm',
                             'mru': 'mru',
                             'mruStatEn': 'mru_stat_enable',
                             'phyIfMacStatEnable': 'phyif_mac_stat_enable',
                             'vbdIfFwdLoop': 'vbdif_forward_loopback'}

STAT_MODE_XML2CLI = {
    "baseInterface": "base_interface",
    "baseVlanGroup": "base_vlan_group"}
STAT_MODE_CLI2XML = {
    "base_interface": "baseInterface",
    "base_vlan_group": "baseVlanGroup"}

VE_GROUP_TYPE_XML2CLI = {
    "L2VE": "l2-terminate",
    "L3VE": "l3-access",
    "TerminateVE": "l3-terminate"}
VE_GROUP_TYPE_CLI2XML = {
    "l2-terminate": "L2VE",
    "l3-access": "L3VE",
    "l3-terminate": "TerminateVE"}


class Interface(object):
    """Manages configuration of an interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.input_info = dict()
        for _, cli_key in INTERFACE_XML2CLI.items():
            self.input_info[cli_key] = self.module.params[cli_key]

        for _, cli_key in INTERFACE_SUBLIST_XML2CLI.items():
            self.input_info[cli_key] = self.module.params[cli_key]

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
        required_together = [("ve_group_type", "ve_group_id")]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
            required_together=required_together,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # check ifName
        if self.input_info.get("name") is not None:
            if len(self.input_info.get("name")) > 63 or len(
                    self.input_info.get("name").replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Interface name is not in the range from 1 to 63.')

    def netconf_set_config(self, xml_str, xml_name, check_recv=True):
        """ netconf set config """
        logging.info("netconf_set_config %s %s", xml_name, xml_str)
        recv_xml = set_nc_config(self.module, xml_str, True, check_recv)
        logging.info("netconf_set_config recv_xml: %s", recv_xml)

        if "<ok/>" not in recv_xml and check_recv:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)
        return recv_xml

    def get_interface_dict(self):
        """ get interface attributes dict."""

        interface_info = dict()
        # Head info
        conf_str = NE_NC_GET_IFM_HEAD
        # Body info
        conf_str = constr_leaf_value(
            conf_str, "ifName", self.input_info.get("name"))
        # Tail info
        conf_str += NE_NC_GET_IFM_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return interface_info

        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm"', "")

        root = ElementTree.fromstring(xml_str)
        interface = root.find("ifm/interfaces/interface")
        if interface is not None and len(interface) != 0:
            for field in interface:
                if field.tag in INTERFACE_XML2CLI.keys():
                    if field.tag == "statMode":
                        interface_info[INTERFACE_XML2CLI[field.tag]
                                       ] = STAT_MODE_XML2CLI.get(field.text)
                    else:
                        interface_info[INTERFACE_XML2CLI[field.tag]
                                       ] = field.text

        for xml_key, cli_key in INTERFACE_SUBLIST_XML2CLI.items():
            field_value = re.findall(
                r'.*<%s>(.*)</%s>.*' %
                (xml_key, xml_key), xml_str)
            if field_value:
                if "ve_group_type" == cli_key:
                    interface_info[cli_key] = VE_GROUP_TYPE_XML2CLI.get(
                        field_value[0])
                elif "ip_stat_mode" == cli_key and "invalid" == field_value[0]:
                    interface_info[cli_key] = "mac"
                else:
                    interface_info[cli_key] = field_value[0]

        return interface_info

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
            if value is not None:
                self.existing[key] = value

    def get_end_state(self):
        """get end state info"""

        interface_info = self.get_interface_dict()
        if not interface_info:
            return

        for key, value in interface_info.items():
            if value is not None:
                self.end_state[key] = value

    def create_interface(self):
        """create interface process"""
        # 生成并下发yang报文
        xml_str = NE_NC_SET_IFM_HEAD % NE_NC_OPTYPE_CREATE
        xml_str = constr_leaf_value(
            xml_str, "ifName", self.input_info.get("name"))
        if self.input_info.get("l2sub") is not None:
            xml_str = constr_leaf_value(
                xml_str, "l2SubIfFlag", self.input_info.get("l2sub"))
        xml_str += NE_NC_SET_IFM_TAIL

        self.netconf_set_config(xml_str, "CREATE_INTERFACE")
        self.changed = True

    def set_interface(self):
        """set interface process"""

        # 获取变化前的接口信息
        interface_info = self.get_interface_dict()

        # 生成并下发yang报文
        xml_str = NE_NC_SET_IFM_HEAD % NE_NC_OPTYPE_MERGE
        for xml_key, cli_key in INTERFACE_XML2CLI.items():
            if self.input_info.get(cli_key) is not None:
                if cli_key == "stat_mode":
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, STAT_MODE_CLI2XML.get(
                            self.input_info.get(cli_key)))
                else:
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, self.input_info.get(cli_key))

        # 增加属性组字段
        if self.input_info.get("input_rising_rate") is not None or self.input_info.get("input_resume_rate") is not None \
                or self.input_info.get("output_rising_rate") is not None or self.input_info.get("output_resume_rate") is not None:
            xml_str = constr_container_head(xml_str, "ifTrapThreshold")
            if self.input_info.get("input_rising_rate") is not None:
                xml_str = constr_leaf_value(
                    xml_str, "inputRisingRate", self.input_info.get("input_rising_rate"))
            if self.input_info.get("input_resume_rate") is not None:
                xml_str = constr_leaf_value(
                    xml_str, "inputResumeRate", self.input_info.get("input_resume_rate"))
            if self.input_info.get("output_rising_rate") is not None:
                xml_str = constr_leaf_value(
                    xml_str, "outputRisingRate", self.input_info.get("output_rising_rate"))
            if self.input_info.get("output_resume_rate") is not None:
                xml_str = constr_leaf_value(
                    xml_str, "outputResumeRate", self.input_info.get("output_resume_rate"))
            xml_str = constr_container_tail(xml_str, "ifTrapThreshold")

        if self.input_info.get("ip_stat_enable") is not None or self.input_info.get(
                "ip_stat_mode") is not None:
            xml_str = constr_container_head(xml_str, "ifIpStatiCfg")
            if self.input_info.get("ip_stat_enable") is not None:
                xml_str = constr_leaf_value(
                    xml_str, "ifIpStatiEnable", self.input_info.get("ip_stat_enable"))
            if self.input_info.get("ip_stat_mode") is not None:
                xml_str = constr_leaf_value(
                    xml_str, "ifIpStatiMode", self.input_info.get("ip_stat_mode"))
            xml_str = constr_container_tail(xml_str, "ifIpStatiCfg")

        if self.input_info.get("ve_group_type") is not None or self.input_info.get(
                "ve_group_id") is not None:
            xml_str = constr_container_head(xml_str, "veGroup")
            if self.input_info.get("ve_group_type") is not None:
                xml_str = constr_leaf_value(xml_str, "veIfType",
                                            VE_GROUP_TYPE_CLI2XML.get(self.input_info.get("ve_group_type")))
            if self.input_info.get("ve_group_id") is not None:
                xml_str = constr_leaf_value(
                    xml_str, "veGroupId", self.input_info.get("ve_group_id"))
            xml_str = constr_container_tail(xml_str, "veGroup")

        if self.input_info.get("ve_forward_mode") is not None:
            xml_str = constr_container_head(xml_str, "forwardMode")
            xml_str = constr_leaf_value(
                xml_str, "veForwarMode", self.input_info.get("ve_forward_mode"))
            xml_str = constr_container_tail(xml_str, "forwardMode")

        if self.input_info.get("unknow_unicast_alarm") is not None:
            xml_str = constr_container_head(xml_str, "flowAlarm")
            xml_str = constr_leaf_value(
                xml_str,
                "unknownUnicastAlarm",
                self.input_info.get("unknow_unicast_alarm"))
            xml_str = constr_container_tail(xml_str, "flowAlarm")

        if self.input_info.get("mru") is not None:
            xml_str = constr_container_head(xml_str, "ifMru")
            xml_str = constr_leaf_value(
                xml_str, "mru", self.input_info.get("mru"))
            xml_str = constr_container_tail(xml_str, "ifMru")

        if self.input_info.get("mru_stat_enable") is not None:
            xml_str = constr_container_head(xml_str, "ifMruStatEnable")
            xml_str = constr_leaf_value(
                xml_str, "mruStatEn", self.input_info.get("mru_stat_enable"))
            xml_str = constr_container_tail(xml_str, "ifMruStatEnable")

        if self.input_info.get("phyif_mac_stat_enable") is not None:
            xml_str = constr_container_head(xml_str, "phyIfMacStat")
            xml_str = constr_leaf_value(
                xml_str,
                "phyIfMacStatEnable",
                self.input_info.get("phyif_mac_stat_enable"))
            xml_str = constr_container_tail(xml_str, "phyIfMacStat")

        if self.input_info.get("vbdif_forward_loopback") is not None:
            xml_str = constr_container_head(xml_str, "vbdIfForwardMode")
            xml_str = constr_leaf_value(
                xml_str,
                "vbdIfFwdLoop",
                self.input_info.get("vbdif_forward_loopback"))
            xml_str = constr_container_tail(xml_str, "vbdIfForwardMode")

        xml_str += NE_NC_SET_IFM_TAIL

        recv_xml = self.netconf_set_config(xml_str, "SET_INTERFACE", False)

        # 接口配置失败，如果是本次创建的接口，需要回滚删除
        if "<ok/>" not in recv_xml:
            if self.changed:
                self.delete_interface()
            self.module.fail_json(msg='Error: %s.' % recv_xml)

        # 获取变化后的接口信息
        changed_interface_info = self.get_interface_dict()
        self.generate_updates_cmd(interface_info, changed_interface_info)

    def delete_interface(self):
        """Delete interface process"""
        # Head process
        xml_str = NE_NC_SET_IFM_HEAD % NE_NC_OPTYPE_DELETE
        # Body process
        xml_str = constr_leaf_value(
            xml_str, "ifName", self.input_info.get("name"))
        # Tail process
        xml_str += NE_NC_SET_IFM_TAIL

        self.netconf_set_config(xml_str, "DELETE_INTERFACE")

        self.updates_cmd.append(
            "undo interface %s" %
            self.interface_info.get("name"))
        self.changed = True

    def delete_interface_config(self):
        """Delete interface config"""
        # Head process
        xml_str = NE_NC_SET_IFM_HEAD % NE_NC_OPTYPE_MERGE
        # Body process
        xml_str = constr_leaf_value(
            xml_str, "ifName", self.input_info.get("name"))

        for xml_key, cli_key in INTERFACE_XML2CLI.items():
            if xml_key != "ifName" and xml_key != "l2SubIfFlag" and self.input_info.get(
                    cli_key) is not None:
                xml_str = constr_leaf_process_delete(xml_str, xml_key)

        # 增加属性组字段
        if self.input_info.get("input_rising_rate") is not None \
                or self.input_info.get("input_resume_rate") is not None \
                or self.input_info.get("output_rising_rate") is not None \
                or self.input_info.get("output_resume_rate") is not None:
            xml_str = constr_container_head(xml_str, "ifTrapThreshold")
            if self.input_info.get("input_rising_rate") is not None:
                xml_str = constr_leaf_process_delete(
                    xml_str, "inputRisingRate")
            if self.input_info.get("input_resume_rate") is not None:
                xml_str = constr_leaf_process_delete(
                    xml_str, "inputResumeRate")
            if self.input_info.get("output_rising_rate") is not None:
                xml_str = constr_leaf_process_delete(
                    xml_str, "outputRisingRate")
            if self.input_info.get("output_resume_rate") is not None:
                xml_str = constr_leaf_process_delete(
                    xml_str, "outputResumeRate")
            xml_str = constr_container_tail(xml_str, "ifTrapThreshold")

        if self.input_info.get("ip_stat_enable") is not None \
                or self.input_info.get("ip_stat_mode") is not None:
            xml_str = constr_container_head(xml_str, "ifIpStatiCfg")
            if self.input_info.get("ip_stat_enable") is not None:
                xml_str = constr_leaf_process_delete(
                    xml_str, "ifIpStatiEnable")
            if self.input_info.get("ip_stat_mode") is not None:
                xml_str = constr_leaf_process_delete(xml_str, "ifIpStatiMode")
            xml_str = constr_container_tail(xml_str, "ifIpStatiCfg")

        if self.input_info.get("ve_group_type") is not None \
                or self.input_info.get("ve_group_id") is not None:
            xml_str = constr_container_head_with_operation(
                xml_str, "veGroup", NE_NC_OPTYPE_DELETE)
            xml_str = constr_container_tail(xml_str, "veGroup")

        if self.input_info.get("ve_forward_mode") is not None:
            xml_str = constr_container_head_with_operation(
                xml_str, "forwardMode", NE_NC_OPTYPE_DELETE)
            xml_str = constr_leaf_value(
                xml_str, "veForwarMode", self.input_info.get("ve_forward_mode"))
            xml_str = constr_container_tail(xml_str, "forwardMode")

        if self.input_info.get("unknow_unicast_alarm") is not None:
            xml_str = constr_container_head_with_operation(
                xml_str, "flowAlarm", NE_NC_OPTYPE_DELETE)
            xml_str = constr_leaf_value(
                xml_str,
                "unknownUnicastAlarm",
                self.input_info.get("unknownUnicastAlarm"))
            xml_str = constr_container_tail(xml_str, "flowAlarm")

        if self.input_info.get("mru") is not None:
            xml_str = constr_container_head(xml_str, "ifMru")
            xml_str = constr_leaf_process_delete(xml_str, "mru")
            xml_str = constr_container_tail(xml_str, "ifMru")

        if self.input_info.get("mru_stat_enable") is not None:
            xml_str = constr_container_head(xml_str, "ifMruStatEnable")
            xml_str = constr_leaf_process_delete(xml_str, "mruStatEn")
            xml_str = constr_container_tail(xml_str, "ifMruStatEnable")

        if self.input_info.get("phyif_mac_stat_enable") is not None:
            xml_str = constr_container_head(xml_str, "phyIfMacStat")
            xml_str = constr_leaf_process_delete(xml_str, "phyIfMacStatEnable")
            xml_str = constr_container_tail(xml_str, "phyIfMacStat")

        if self.input_info.get("vbdif_forward_loopback") is not None:
            xml_str = constr_container_head(xml_str, "vbdIfForwardMode")
            xml_str = constr_leaf_process_delete(xml_str, "vbdIfFwdLoop")
            xml_str = constr_container_tail(xml_str, "vbdIfForwardMode")

        # Tail process
        xml_str += NE_NC_SET_IFM_TAIL
        self.netconf_set_config(xml_str, "DELETE_INTERFACE_CONFIG")

        changed_interface_info = self.get_interface_dict()
        self.generate_updates_cmd(self.interface_info, changed_interface_info)

    def generate_updates_cmd(self, interface_info, changed_interface_info):
        """generate updates command"""

        for key, value in self.input_info.items():
            if value is not None and changed_interface_info.get(
                    key) != interface_info.get(key):
                self.changed = True
                break

        if "true" == self.input_info.get("l2sub"):
            self.updates_cmd.append(
                "interface %s mode l2" %
                changed_interface_info.get("name"))
        else:
            self.updates_cmd.append(
                "interface %s" %
                changed_interface_info.get("name"))

        if self.input_info.get("description") is not None and \
                changed_interface_info.get("description") != interface_info.get("description"):
            if changed_interface_info.get("description"):
                self.updates_cmd.append(
                    "description %s" %
                    changed_interface_info.get("description"))
            else:
                self.updates_cmd.append("undo description")

        if self.input_info.get("admin_state") is not None and \
                changed_interface_info.get("admin_state") != interface_info.get("admin_state"):
            if "down" == changed_interface_info.get("admin_state"):
                self.updates_cmd.append("shutdown")
            else:
                self.updates_cmd.append("undo shutdown")

        if self.input_info.get("clear_ip_df") is not None and \
                changed_interface_info.get("clear_ip_df") != interface_info.get("clear_ip_df"):
            if "true" == self.input_info.get("clear_ip_df"):
                self.updates_cmd.append("clear ip df")
            else:
                self.updates_cmd.append("undo clear ip df")

        if self.input_info.get("trap_enable") is not None and \
                changed_interface_info.get("trap_enable") != interface_info.get("trap_enable"):
            if "true" == self.input_info.get("trap_enable"):
                self.updates_cmd.append("enable snmp trap updown")
            else:
                self.updates_cmd.append("undo enable snmp trap updown")

        if self.input_info.get("stat_enable") is not None or self.input_info.get(
                "stat_mode") is not None:
            if changed_interface_info.get("stat_enable") != interface_info.get("stat_enable") \
                    or changed_interface_info.get("stat_mode") != interface_info.get("stat_mode"):
                if "false" == changed_interface_info.get("stat_enable"):
                    self.updates_cmd.append("undo statistic enable")
                elif "true" == changed_interface_info.get("stat_enable"):
                    if "true" == changed_interface_info.get("l2sub"):
                        if "base_vlan_group" == self.input_info.get(
                                "stat_mode"):
                            self.updates_cmd.append(
                                "statistic enable mode multiple")
                        else:
                            self.updates_cmd.append(
                                "statistic enable mode single")
                    else:
                        self.updates_cmd.append("statistic enable")

        if self.input_info.get("mtu") is not None or self.input_info.get(
                "mtu_spread") is not None:
            if changed_interface_info.get("mtu") != interface_info.get("mtu") \
                    or changed_interface_info.get("mtu_spread") != interface_info.get("mtu_spread"):
                if changed_interface_info.get("mtu"):
                    if "true" == changed_interface_info.get("mtu_spread"):
                        self.updates_cmd.append(
                            "mtu %s spread" %
                            changed_interface_info.get("mtu"))
                    else:
                        self.updates_cmd.append(
                            "mtu %s" % changed_interface_info.get("mtu"))
                else:
                    self.updates_cmd.append("undo mtu")

        if self.input_info.get("bandwidth") is not None:
            if changed_interface_info.get(
                    "bandwidth") != interface_info.get("bandwidth"):
                if changed_interface_info.get("bandwidth"):
                    self.updates_cmd.append(
                        "bandwidth %s" %
                        changed_interface_info.get("bandwidth"))
                else:
                    self.updates_cmd.append("undo bandwidth")

        if self.input_info.get("stat_interval") is not None:
            if changed_interface_info.get(
                    "stat_interval") != interface_info.get("stat_interval"):
                if changed_interface_info.get("stat_interval"):
                    self.updates_cmd.append("set flow-stat interval %s"
                                            % changed_interface_info.get("stat_interval"))
                else:
                    self.updates_cmd.append("undo set flow-stat interval")

        if self.input_info.get("mac_address") is not None:
            if changed_interface_info.get(
                    "mac_address") != interface_info.get("mac_address"):
                if changed_interface_info.get("mac_address"):
                    self.updates_cmd.append(
                        "mac-address %s" %
                        changed_interface_info.get("mac_address"))
                else:
                    self.updates_cmd.append("undo mac-address")

        if self.input_info.get("input_rising_rate") is not None \
                or self.input_info.get("input_resume_rate") is not None:
            if changed_interface_info.get("input_rising_rate") != interface_info.get("input_rising_rate") \
                    or changed_interface_info.get("input_resume_rate") != interface_info.get("input_resume_rate"):
                if changed_interface_info.get(
                        "input_rising_rate") and changed_interface_info.get("input_resume_rate"):
                    self.updates_cmd.append("trap-threshold input-rate %s resume-rate %s"
                                            % (changed_interface_info.get("input_rising_rate"),
                                               changed_interface_info.get("input_resume_rate")))
                else:
                    self.updates_cmd.append("undo trap-threshold input-rate")

        if self.input_info.get("output_rising_rate") is not None \
                or self.input_info.get("output_resume_rate") is not None:
            if changed_interface_info.get("output_rising_rate") != interface_info.get("output_rising_rate") \
                    or changed_interface_info.get("output_resume_rate") != interface_info.get("output_resume_rate"):
                if changed_interface_info.get(
                        "output_rising_rate") and changed_interface_info.get("output_resume_rate"):
                    self.updates_cmd.append("trap-threshold output-rate %s resume-rate %s"
                                            % (changed_interface_info.get("output_rising_rate"),
                                               changed_interface_info.get("output_resume_rate")))
                else:
                    self.updates_cmd.append("undo trap-threshold output-rate")

        if self.input_info.get("ip_stat_enable") is not None:
            if changed_interface_info.get(
                    "ip_stat_enable") != interface_info.get("ip_stat_enable"):
                if "true" == changed_interface_info.get("ip_stat_enable"):
                    self.updates_cmd.append("statistic enable")
                else:
                    self.updates_cmd.append("undo statistic enable")

        if self.input_info.get("ip_stat_mode") is not None:
            if changed_interface_info.get(
                    "ip_stat_mode") != interface_info.get("ip_stat_mode"):
                if "forward" == changed_interface_info.get("ip_stat_mode"):
                    self.updates_cmd.append("statistic mode forward")
                else:
                    self.updates_cmd.append("undo statistic mode")

        if self.input_info.get("ve_group_type") is not None \
                or self.input_info.get("ve_group_id") is not None:
            if changed_interface_info.get("ve_group_type") != interface_info.get("ve_group_type") \
                    and changed_interface_info.get("ve_group_id") != interface_info.get("ve_group_id"):
                if changed_interface_info.get(
                        "ve_group_type") and changed_interface_info.get("ve_group_id"):
                    self.updates_cmd.append("ve-group %s %s" % (changed_interface_info.get("ve_group_id"),
                                                                changed_interface_info.get("ve_group_type")))
                else:
                    self.updates_cmd.append("undo ve-group")

        if self.input_info.get("ve_forward_mode") is not None:
            if changed_interface_info.get(
                    "ve_forward_mode") != interface_info.get("ve_forward_mode"):
                if changed_interface_info.get("ve_forward_mode"):
                    self.updates_cmd.append(
                        "forward-mode %s" %
                        changed_interface_info.get("ve_forward_mode"))
                else:
                    self.updates_cmd.append("undo forward-mode")

        if self.input_info.get("unknow_unicast_alarm") is not None:
            if changed_interface_info.get(
                    "unknow_unicast_alarm") != interface_info.get("unknow_unicast_alarm"):
                if changed_interface_info.get("unknow_unicast_alarm"):
                    self.updates_cmd.append("unknown-unicast alarm-threshold %s"
                                            % changed_interface_info.get("unknow_unicast_alarm"))
                else:
                    self.updates_cmd.append(
                        "undo unknown-unicast alarm-threshold")

        if self.input_info.get("mru") is not None:
            if changed_interface_info.get("mru") != interface_info.get("mru"):
                if changed_interface_info.get("mru"):
                    self.updates_cmd.append(
                        "mru %s" % changed_interface_info.get("mru"))
                else:
                    self.updates_cmd.append("undo mru")

        if self.input_info.get("mru_stat_enable") is not None:
            if changed_interface_info.get(
                    "mru_stat_enable") != interface_info.get("mru_stat_enable"):
                if "true" == changed_interface_info.get("mru_stat_enable"):
                    self.updates_cmd.append("mru statistic enable")
                else:
                    self.updates_cmd.append("undo mru statistic enable")

        if self.input_info.get("phyif_mac_stat_enable") is not None:
            if changed_interface_info.get(
                    "phyif_mac_stat_enable") != interface_info.get("phyif_mac_stat_enable"):
                if "true" == changed_interface_info.get(
                        "phyif_mac_stat_enable"):
                    self.updates_cmd.append("statistic enable mode port")
                else:
                    self.updates_cmd.append("undo statistic enable mode port")

        if self.input_info.get("vbdif_forward_loopback") is not None:
            if changed_interface_info.get(
                    "vbdif_forward_loopback") != interface_info.get("vbdif_forward_loopback"):
                if "true" == changed_interface_info.get(
                        "vbdif_forward_loopback"):
                    self.updates_cmd.append("forward-mode loopback")
                else:
                    self.updates_cmd.append("undo forward-mode")

    def work(self):
        """worker"""
        self.check_params()

        self.interface_info = self.get_interface_dict()
        self.get_proposed()
        self.get_existing()

        # 非创建流程，接口不存在报错
        if self.state != "present" and not self.interface_info:
            self.module.fail_json(
                msg='Error: Interface %s does not exist' %
                self.input_info.get("name"))

        # deal present or absent
        if self.state == "present":
            # 接口不存在，先创建接口，为了set流程获取变化的数据
            if not self.interface_info:
                self.create_interface()
            self.set_interface()
        elif self.state == "absent":
            self.delete_interface()
        elif self.state == "default":
            self.delete_interface_config()

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
    logging.info("main")
    argument_spec = dict(
        name=dict(required=True, type='str'),
        description=dict(required=False, type='str'),
        admin_state=dict(required=False, choices=['up', 'down']),
        clear_ip_df=dict(required=False, choices=['true', 'false']),
        trap_enable=dict(required=False, choices=['true', 'false']),
        stat_enable=dict(required=False, choices=['true', 'false']),
        stat_mode=dict(
            required=False,
            choices=[
                'base_interface',
                'base_vlan_group']),
        mtu=dict(required=False, type='int'),
        mtu_spread=dict(required=False, choices=['true', 'false']),
        bandwidth=dict(required=False, type='int'),
        stat_interval=dict(required=False, type='int'),
        l2sub=dict(required=False, choices=['true', 'false']),
        mac_address=dict(required=False, type='str'),
        input_rising_rate=dict(required=False, type='int'),
        input_resume_rate=dict(required=False, type='int'),
        output_rising_rate=dict(required=False, type='int'),
        output_resume_rate=dict(required=False, type='int'),
        ip_stat_enable=dict(required=False, choices=['true', 'false']),
        ip_stat_mode=dict(required=False, choices=['forward', 'mac']),
        ve_group_type=dict(
            required=False,
            choices=[
                'l2-terminate',
                'l3-access',
                'l3-terminate']),
        ve_group_id=dict(required=False, type='int'),
        ve_forward_mode=dict(
            required=False,
            choices=[
                'through',
                'loopback',
                'invalid']),
        unknow_unicast_alarm=dict(required=False, type='int'),
        mru=dict(required=False, type='int'),
        mru_stat_enable=dict(required=False, choices=['true', 'false']),
        phyif_mac_stat_enable=dict(required=False, choices=['true', 'false']),
        vbdif_forward_loopback=dict(required=False, choices=['true', 'false']),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query', 'default']))

    argument_spec.update(ne_argument_spec)
    module = Interface(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
