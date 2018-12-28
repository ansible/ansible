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
module: ne_interface
version_added: "2.6"
short_description: Manages configuration of an eth-trunk or ip-trunk interface.
description:
    - Manages configuration of an eth-trunk or ip-trunk interface on HUAWEI netengine routers.
author: Shijiawei (@netengine-Ansible)
notes:
     - C(state=default) removes the configuration of the trunk interface, removes the configuration of
       the trunk member.
     - C(state=absent) deletes the trunk interface or removes trunk member from trunk.
options:
    name:
        description:
            - Specify the name of a trunk interface. The value is a string of 1 to 63 characters.
        required: true
        default: null
    mode:
        description:
            - Configure the working mode for a trunk interface.
              manual: Specify the manual load balancing mode. It is a basic link aggregation mode.
                      In this mode, you must manually create a trunk interface, add interfaces to the
                      trunk interface, and specify active member interfaces. LACP is not involved.
              backup: Specify the 1:1 active/standby load balancing mode. In this mode, an Eth-Trunk
                      interface contains only two member interfaces (one active interface and one
                      standby interface).
              lacp-static: Specify the static LACP mode. In this mode, you must manually add interfaces
                           to the Eth-Trunk interface. Different from link aggregation in manual load
                           balancing mode, active member interfaces are selected based on LACP packets.
        required: false
        default: null
        choices: ['manual', 'backup', 'lacp-static']
    min_links:
        description:
            - Specify the minimum number of Up member links of a trunk interface.
              The value is an integer ranging from 1 to 64.
        required: false
        default: null
    min_bandwidth:
        description:
            - Specify the minimum bandwidth of Up member links of a trunk interface.
              The value is an integer ranging from 1 to 4294967295.
        required: false
        default: null
    max_links:
        description:
            - Maximum number of links that affect the actual bandwidth of the Layer 2 Eth-Trunk interface.
              The value is an integer ranging from 1 to 64.
        required: false
        default: null
    remote:
        description:
            - To identify remote Eth-Trunk interface.
        required: false
        default: null
        choices: ['true', 'false']
    hash_type:
        description:
            - Configure the hash algorithm for a forwarding table.
              src-dst-ip: Specify the IP-address-based per-destination load balancing mode. In this mode,
                          data flows are differentiated based on IP addresses of packets to ensure that
                          the packets of the same data flow are transmitted over the same member link.
              src-dst-mac: Specify the MAC-address-based per-destination load balancing mode. In this mode,
                           data flows are differentiated based on MAC addresses of packets to ensure that
                           the packets of the same data flow are transmitted over the same member link.
              packet-all: Specifies the per-packet load balancing mode. In this mode, one packet
                          (not a data flow) is regarded as a unit, and packets are dispersed and
                          transmitted among different member links.
              l4: According to source/destination IP, source/destination port and protocol hash arithmetic.
              symmetric-hash: Symmetric hash arithmetic.
              symmetric-hash-complement: Symmetric complement hash arithmetic.
        required: false
        default: null
        choices: ['src-dst-ip', 'src-dst-mac', 'packet-all',
                 'l4', 'symmetric-hash', 'symmetric-hash-complement']
    smart_link_flush_vlan_id:
        description:
            - Specify the ID of the VLAN to which Smart-link flush packets are sent.
              The value is an integer ranging from 1 to 4094.
        required: false
        default: null
    inactive_port_shutdown:
        description:
            - Enable the laser auto shutdown function on the backup interface of the Eth-Trunk interface
              working in 1:1 master/backup mode. After this function is enabled, the backup interface
              will be shut down. By default, the laser auto shutdown function is disabled.
        required: false
        default: null
        choices: ['true', 'false']
    preempt_enable:
        description:
            - Enable delay switchback for the master member interface of an Eth-Trunk interface working
              in 1:1 master/backup mode. By default, this function is disabled. This function works
              together with revert delay time that can be configured only after this function is enabled.
              After this function is enabled, the restored master interface automatically takes over
              traffic of the backup interface when the revert delay time expires.
        required: false
        default: null
        choices: ['true', 'false']
    preempt_delay_minutes:
        description:
            - Specify the delay interval (in minutes) at which the master interface of an Eth-Trunk
              interface working 1:1 master/backup mode switches back to the master state. Value 0
              indicates that a master interface immediately switches back to the master state once it
              is restored. This time can be configured only after delay switchback is enabled. After
              this time is configured, the restored master interface switches back to the master state
              only after the time expires, preventing frequent interface flappings and traffic loss.
              The value is an integer ranging from 0 to 30.
        required: false
        default: null
    preempt_delay_seconds:
        description:
            - Specify the delay interval (in seconds) at which the master interface of an Eth-Trunk
              interface working 1:1 master/backup mode switches back to the master state. Value 0
              indicates that a master interface immediately switches back to the master state once it
              is restored. This time can be configured only after delay switchback is enabled. After
              this time is configured, the restored master interface switches back to the master state
              only after the time expires, preventing frequent interface flappings and traffic loss.
              The value is an integer ranging from 0 to 59.
        required: false
        default: null
    preempt_delay_million_seconds:
        description:
            - Specify the delay interval (in million-seconds) at which the master interface of an
              Eth-Trunk interface working 1:1 master/backup mode switches back to the master state.
              Value 0 indicates that a master interface immediately switches back to the master state
              once it is restored. This time can be configured only after delay switchback is enabled.
              After this time is configured, the restored master interface switches back to the master
              state only after the time expires, preventing frequent interface flappings and traffic loss.
              The value is an integer ranging from 0 to 999.
        required: false
        default: null
    locality:
        description:
            - Enable or disable virtual-cluster trunk localization.
        required: false
        default: null
        choices: ['true', 'false']
    hash_arith_type:
        description:
            - Configure the hash arithmetic type for a trunk interface.
              crc32_1: CRC32-1
              crc32_2: CRC32-2
              xor_16bit: 16bit XOR
              xor_8bit: 8bit XOR
        required: false
        default: null
        choices: ['crc32_1', 'crc32_2', 'xor_16bit', 'xor_8bit']
    dual_receive_enable:
        description:
            - Enable the backup-dual-receiving function of the eth-trunk interface.
        required: false
        default: null
        choices: ['true', 'false']
    member_name:
        description:
            - Configure the name of a trunk member interface. The value is a string of 1 to 63 characters.
        required: false
        default: null
    member_weight:
        description:
            - Set the weight for a trunk member interface. The value is an integer ranging from 1 to 64.
        required: false
        default: null
    member_port_master:
        description:
            - Configure a trunk member interface as the master interface.
        required: false
        default: null
        choices: ['true', 'false']
    member_hash_index:
        description:
            - Set Hash index of eth-trunk member. The value is an integer ranging from 1 to 64.
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present', 'absent', 'default', 'query']
'''

EXAMPLES = '''
- name: interface_trunk module test
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
  - name: Create eth-trunk interface and config trunk mode
    ne_interface_trunk:
      name: Eth-Trunk100
      mode: lacp-static
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"mode": "lacp-static",
             "name": "Eth-Trunk100",
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
    sample: {"hash_type": "src-dst-ip",
             "inactive_port_shutdown": "false",
             "max_links": "64",
             "min_links": "1",
             "mode": "lacp-static",
             "name": "Eth-Trunk100",
             "preempt_delay_million_seconds": "0",
             "preempt_delay_minutes": "0",
             "preempt_delay_seconds": "0",
             "preempt_enable": "false",
             "remote": "false"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface Eth-Trunk100", "mode lacp-static"]
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

# Interface 模块私有接口公共函数
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_value
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_head
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_tail
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_process_delete

logging.basicConfig(filename='/opt/python_logger.log', level=logging.INFO)

NE_NC_GET_TRUNK = """
<filter type="subtree">
  <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk">
    <TrunkIfs>
      <TrunkIf>
        <ifName>%s</ifName>
      </TrunkIf>
    </TrunkIfs>
  </ifmtrunk>
</filter>
"""

NE_NC_GET_TRUNK_MEMBER = """
<filter type="subtree">
  <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk">
    <TrunkIfs>
      <TrunkIf>
        <ifName>%s</ifName>
        <TrunkMemberIfs>
          <TrunkMemberIf>
            <memberIfName>%s</memberIfName>
          </TrunkMemberIf>
        </TrunkMemberIfs>
      </TrunkIf>
    </TrunkIfs>
  </ifmtrunk>
</filter>
"""

NE_NC_SET_TRUNK_HEAD = """
<config>
  <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk">
    <TrunkIfs>
      <TrunkIf nc:operation="%s" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

NE_NC_SET_TRUNK_TAIL = """
      </TrunkIf>
    </TrunkIfs>
  </ifmtrunk>
</config>
"""

NE_NC_SET_TRUNK_MEM_HEAD = """
<config>
  <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk">
    <TrunkIfs>
      <TrunkIf>
        <ifName>%s</ifName>
        <TrunkMemberIfs>
          <TrunkMemberIf nc:operation="%s" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

NE_NC_SET_TRUNK_MEM_TAIL = """
          </TrunkMemberIf>
        </TrunkMemberIfs>
      </TrunkIf>
    </TrunkIfs>
  </ifmtrunk>
</config>
"""

MODE_XML2CLI = {
    "Manual": "manual",
    "Backup": "backup",
    "Static": "lacp-static"}
MODE_CLI2XML = {
    "manual": "Manual",
    "backup": "Backup",
    "lacp-static": "Static"}
HASH_TYPE_XML2CLI = {"IP": "src-dst-ip", "MAC": "src-dst-mac", "PacketAll": "packet-all",
                     "L4": "l4", "Symmetric": "symmetric-hash",
                     "SymmetricComplement": "symmetric-hash-complement"}
HASH_TYPE_CLI2XML = {"src-dst-ip": "IP", "src-dst-mac": "MAC", "packet-all": "PacketAll",
                     "l4": "L4", "symmetric-hash": "Symmetric",
                     "symmetric-hash-complement": "SymmetricComplement"}
HASH_ARITH_TYPE_XML2CLI = {
    "CRC32_1": "crc32_1",
    "CRC32_2": "crc32_2",
    "XOR_16BIT": "xor_16bit",
    "XOR_8BIT": "xor_8bit"}
HASH_ARITH_TYPE_CLI2XML = {
    "crc32_1": "CRC32_1",
    "crc32_2": "CRC32_2",
    "xor_16bit": "XOR_16BIT",
    "xor_8bit": "XOR_8BIT"}
TRUNKIF_XML2CLI = {'ifName': 'name',
                   'minUpNum': 'min_links',
                   'minUpBand': 'min_bandwidth',
                   'maxUpNum': 'max_links',
                   'remoteEthTrunk': 'remote',
                   'hashType': 'hash_type',
                   'workMode': 'mode',
                   'smlkFlushVlanId': 'smart_link_flush_vlan_id',
                   'inactivePortShutdown': 'inactive_port_shutdown',
                   'preemptEnable': 'preempt_enable',
                   'preemptDelayTime': 'preempt_delay_minutes',
                   'preemptDelaySec': 'preempt_delay_seconds',
                   'preemptDelayMS': 'preempt_delay_million_seconds'}
TRUNKMEM_XML2CLI = {'memberIfName': 'member_name',
                    'weight': 'member_weight',
                    'isMasterMember': 'member_port_master'}


class Interface_Trunk(object):
    """ Manages Eth-Trunk and IP-Trunk interfaces."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.input_info = dict()
        self.input_info["name"] = self.module.params["name"]
        self.input_info["mode"] = self.module.params["mode"]
        self.input_info["min_links"] = self.module.params["min_links"]
        self.input_info["min_bandwidth"] = self.module.params["min_bandwidth"]
        self.input_info["max_links"] = self.module.params["max_links"]
        self.input_info["remote"] = self.module.params["remote"]
        self.input_info["hash_type"] = self.module.params["hash_type"]
        self.input_info["smart_link_flush_vlan_id"] = self.module.params["smart_link_flush_vlan_id"]
        self.input_info["inactive_port_shutdown"] = self.module.params["inactive_port_shutdown"]
        self.input_info["preempt_enable"] = self.module.params["preempt_enable"]
        self.input_info["preempt_delay_minutes"] = self.module.params["preempt_delay_minutes"]
        self.input_info["preempt_delay_seconds"] = self.module.params["preempt_delay_seconds"]
        self.input_info["preempt_delay_million_seconds"] = self.module.params["preempt_delay_million_seconds"]

        self.input_info["locality"] = self.module.params["locality"]
        self.input_info["hash_arith_type"] = self.module.params["hash_arith_type"]
        self.input_info["dual_receive_enable"] = self.module.params["dual_receive_enable"]

        self.input_info["member_name"] = self.module.params["member_name"]
        self.input_info["member_weight"] = self.module.params["member_weight"]
        self.input_info["member_port_master"] = self.module.params["member_port_master"]

        self.input_info["member_hash_index"] = self.module.params["member_hash_index"]

        self.state = self.module.params['state']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

        # interface info
        self.trunk_info = dict()

    def __init_module__(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def netconf_set_config(self, xml_str, xml_name, check_recv=True):
        """ netconf set config """
        logging.info("netconf_set_config %s %s", xml_name, xml_str)
        recv_xml = set_nc_config(self.module, xml_str, True, check_recv)
        logging.info("netconf_set_config recv_xml: %s", recv_xml)

        if "<ok/>" not in recv_xml and check_recv:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)
        return recv_xml

    def get_trunk_dict(self):
        """ get one interface attributes dict."""

        trunk_info = dict()
        conf_str = NE_NC_GET_TRUNK % self.input_info["name"]
        xml_str = get_nc_config(self.module, conf_str, True)

        if "<data/>" in xml_str:
            return trunk_info

        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', ""). \
            replace(
            'xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk"', "")

        # 获取Trunk信息
        root = ElementTree.fromstring(xml_str)
        trunk_if = root.find("ifmtrunk/TrunkIfs/TrunkIf")
        if trunk_if is not None and len(trunk_if) != 0:
            for field in trunk_if:
                if field.tag in TRUNKIF_XML2CLI.keys():
                    if field.tag == "hashType":
                        trunk_info[TRUNKIF_XML2CLI[field.tag]
                                   ] = HASH_TYPE_XML2CLI.get(field.text)
                    elif field.tag == "workMode":
                        trunk_info[TRUNKIF_XML2CLI[field.tag]
                                   ] = MODE_XML2CLI.get(field.text)
                    else:
                        trunk_info[TRUNKIF_XML2CLI[field.tag]] = field.text

        locality = re.findall(r'.*<locality>(.*)</locality>.*', xml_str)
        if locality:
            trunk_info["locality"] = locality[0]

        hash_arith_type = re.findall(
            r'.*<hashArithType>(.*)</hashArithType>.*', xml_str)
        if hash_arith_type:
            trunk_info["hash_arith_type"] = HASH_ARITH_TYPE_XML2CLI.get(
                hash_arith_type[0])

        dual_receive_enable = re.findall(
            r'.*<trunkDualRcvEnable>(.*)</trunkDualRcvEnable>.*', xml_str)
        if dual_receive_enable:
            trunk_info["dual_receive_enable"] = dual_receive_enable[0]

        # 获取Trunk成员信息
        trunk_members = root.find("ifmtrunk/TrunkIfs/TrunkIf/TrunkMemberIfs")
        if trunk_members is not None and len(trunk_members) != 0:
            trunk_info["members"] = list()
            for trunk_member in trunk_members:
                trunk_member_info = dict()
                for field in trunk_member:
                    if field.tag in TRUNKMEM_XML2CLI.keys():
                        trunk_member_info[TRUNKMEM_XML2CLI[field.tag]
                                          ] = field.text
                    if field.tag == "fimHashIndex":
                        for hash_index in field.iter(tag='hashIndex'):
                            trunk_member_info["member_hash_index"] = hash_index.text
                trunk_info["members"].append(trunk_member_info)

        return trunk_info

    def get_trunk_member(self, trunk_name, member_name):
        """Get trunk member info by trunk_name and member_name"""
        if trunk_name is None or member_name is None:
            return None

        conf_str = NE_NC_GET_TRUNK_MEMBER % (trunk_name, member_name)
        xml_str = get_nc_config(self.module, conf_str, True)

        if "<data/>" in xml_str:
            return None

        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', ""). \
            replace(
            'xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk"', "")

        root = ElementTree.fromstring(xml_str)
        trunk_members = root.find("ifmtrunk/TrunkIfs/TrunkIf/TrunkMemberIfs")
        if trunk_members is not None and len(trunk_members) != 0:
            trunk_member = trunk_members[0]
            trunk_member_info = dict()
            for field in trunk_member:
                if field.tag in TRUNKMEM_XML2CLI.keys():
                    trunk_member_info[TRUNKMEM_XML2CLI[field.tag]] = field.text
                if field.tag == "fimHashIndex":
                    for hash_index in field.iter(tag='hashIndex'):
                        trunk_member_info["member_hash_index"] = hash_index.text

            trunk_name = re.findall(r'.*<ifName>(.*)</ifName>.*', xml_str)
            if trunk_name:
                trunk_member_info["trunk_name"] = trunk_name[0]
            return trunk_member_info

        return None

    def create_trunk_if(self):
        """Create Eth-Trunk interface"""

        # 生成并下发yang报文
        xml_str = NE_NC_SET_TRUNK_HEAD % NE_NC_OPTYPE_CREATE
        xml_str = constr_leaf_value(
            xml_str, "ifName", self.input_info.get("name"))
        if self.input_info.get("remote") is not None:
            xml_str = constr_leaf_value(
                xml_str, "remoteEthTrunk", self.input_info.get("remote"))
        xml_str += NE_NC_SET_TRUNK_TAIL

        self.netconf_set_config(xml_str, "CREATE_TRUNK")
        self.changed = True

    def set_trunk_config(self):
        """Merge trunk configuration or add trunk member"""

        # 获取变更前的数据
        trunk_info = self.get_trunk_dict()
        trunk_member = None

        # 生成并下发yang报文
        xml_str = NE_NC_SET_TRUNK_HEAD % NE_NC_OPTYPE_MERGE
        for xml_key, cli_key in TRUNKIF_XML2CLI.items():
            if self.input_info.get(cli_key) is not None:
                if xml_key == "hashType":
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, HASH_TYPE_CLI2XML.get(
                            self.input_info.get(cli_key)))
                elif xml_key == "workMode":
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, MODE_CLI2XML.get(
                            self.input_info.get(cli_key)))
                else:
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, self.input_info.get(cli_key))

        if self.input_info.get("locality") is not None:
            xml_str = constr_container_head(xml_str, "trunkLocality")
            xml_str = constr_leaf_value(
                xml_str, "locality", self.input_info.get("locality"))
            xml_str = constr_container_tail(xml_str, "trunkLocality")

        if self.input_info.get("hash_arith_type") is not None:
            xml_str = constr_container_head(xml_str, "trunkHashArith")
            xml_str = constr_leaf_value(xml_str, "hashArithType",
                                        HASH_ARITH_TYPE_CLI2XML.get(self.input_info.get("hash_arith_type")))
            xml_str = constr_container_tail(xml_str, "trunkHashArith")

        if self.input_info.get("dual_receive_enable") is not None:
            xml_str = constr_container_head(xml_str, "trunkDualRcv")
            xml_str = constr_leaf_value(
                xml_str,
                "trunkDualRcvEnable",
                self.input_info.get("dual_receive_enable"))
            xml_str = constr_container_tail(xml_str, "trunkDualRcv")

        if self.input_info.get("member_name") is not None:
            # 获取变更前的数据
            trunk_member = self.get_trunk_member(
                self.input_info.get("name"),
                self.input_info.get("member_name"))

            # 生成并下发yang报文
            xml_str = constr_container_head(xml_str, "TrunkMemberIfs")
            xml_str = constr_container_head(xml_str, "TrunkMemberIf")

            for xml_key, cli_key in TRUNKMEM_XML2CLI.items():
                if self.input_info.get(cli_key) is not None:
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, self.input_info.get(cli_key))

            if self.input_info.get("member_hash_index") is not None:
                xml_str = constr_container_head(xml_str, "fimHashIndex")
                xml_str = constr_leaf_value(
                    xml_str, "hashIndex", self.input_info.get("member_hash_index"))
                xml_str = constr_container_tail(xml_str, "fimHashIndex")

            xml_str = constr_container_tail(xml_str, "TrunkMemberIf")
            xml_str = constr_container_tail(xml_str, "TrunkMemberIfs")

        xml_str += NE_NC_SET_TRUNK_TAIL

        recv_xml = self.netconf_set_config(xml_str, "SET_TRUNK", False)

        # 接口配置失败，如果是本次创建的trunk接口，需要回滚删除
        if "<ok/>" not in recv_xml:
            if self.changed:
                self.delete_trunk_if()
            self.module.fail_json(msg='Error: %s.' % recv_xml)

        # 获取变更后的数据
        changed_trunk_info = self.get_trunk_dict()
        changed_trunk_member = self.get_trunk_member(
            self.input_info.get("name"), self.input_info.get("member_name"))

        # 生成配置命令行
        self.generate_set_trunk_if_config_updates_cmd(
            trunk_info, changed_trunk_info)
        self.generate_set_trunk_mem_config_updates_cmd(
            trunk_member, changed_trunk_member)

    def generate_set_trunk_if_config_updates_cmd(
            self, trunk_info, changed_trunk_info):
        """generate updates command for set trunk interafce"""

        if trunk_info is None or changed_trunk_info is None:
            return

        # 比较非member字段是否变更
        for key, value in self.input_info.items():
            if re.match(r'^member_', key) is None \
                    and value is not None and changed_trunk_info.get(key) != trunk_info.get(key):
                self.changed = True
                break

        # 无配置变更，直接返回
        if not self.changed:
            return

        # 生成配置命令行
        if "true" == self.input_info.get("remote"):
            self.updates_cmd.append(
                "interface %s remote" %
                changed_trunk_info.get("name"))
        else:
            self.updates_cmd.append(
                "interface %s" %
                changed_trunk_info.get("name"))

        if self.input_info.get("mode") is not None:
            if trunk_info.get("mode") != changed_trunk_info.get("mode"):
                if "manual" == self.input_info.get("mode"):
                    self.updates_cmd.append("mode manual load-balance")
                elif "backup" == self.input_info.get("mode"):
                    self.updates_cmd.append("mode backup manual backup")
                elif "lacp-static" == self.input_info.get("mode"):
                    self.updates_cmd.append("mode lacp-static")

        if self.input_info.get("min_links") is not None:
            if trunk_info.get(
                    "min_links") != changed_trunk_info.get("min_links"):
                self.updates_cmd.append(
                    "least active-linknumber %s" %
                    self.input_info.get("min_links"))

        if self.input_info.get("min_bandwidth") is not None:
            if trunk_info.get("min_bandwidth") != changed_trunk_info.get(
                    "min_bandwidth"):
                self.updates_cmd.append(
                    "least active-bandwidth %s" %
                    self.input_info.get("min_bandwidth"))

        if self.input_info.get("max_links") is not None:
            if trunk_info.get(
                    "max_links") != changed_trunk_info.get("max_links"):
                self.updates_cmd.append(
                    "max bandwidth-affected-linknumber %s" %
                    self.input_info.get("max_links"))

        if self.input_info.get("hash_type") is not None:
            if trunk_info.get(
                    "hash_type") != changed_trunk_info.get("hash_type"):
                if "symmetric-hash-complement" == self.input_info.get(
                        "hash_type"):
                    self.updates_cmd.append(
                        "load-balance symmetric-hash complement")
                else:
                    self.updates_cmd.append(
                        "load-balance %s" %
                        self.input_info.get("hash_type"))

        if self.input_info.get("smart_link_flush_vlan_id") is not None:
            if trunk_info.get("smart_link_flush_vlan_id") != changed_trunk_info.get(
                    "smart_link_flush_vlan_id"):
                self.updates_cmd.append("smart-link flush send vlan %s" %
                                        self.input_info.get("smart_link_flush_vlan_id"))

        if self.input_info.get("inactive_port_shutdown") is not None:
            if trunk_info.get("inactive_port_shutdown") != changed_trunk_info.get(
                    "inactive_port_shutdown"):
                if "true" == self.input_info.get("inactive_port_shutdown"):
                    self.updates_cmd.append("inactive-port shutdown enable")
                else:
                    self.updates_cmd.append(
                        "undo inactive-port shutdown enable")

        if self.input_info.get("preempt_enable") is not None \
                or self.input_info.get("preempt_delay_minutes") is not None \
                or self.input_info.get("preempt_delay_seconds") is not None \
                or self.input_info.get("preempt_delay_million_seconds") is not None:

            if trunk_info.get("preempt_enable") != changed_trunk_info.get("preempt_enable") \
                    or trunk_info.get("preempt_delay_minutes") != changed_trunk_info.get("preempt_delay_minutes") \
                    or trunk_info.get("preempt_delay_seconds") != changed_trunk_info.get("preempt_delay_seconds") \
                    or trunk_info.get("preempt_delay_million_seconds") != changed_trunk_info.get(
                        "preempt_delay_million_seconds"):
                if "true" == changed_trunk_info.get("preempt_enable"):
                    self.updates_cmd.append("preempt enable delay %s %s %s"
                                            % (changed_trunk_info.get("preempt_delay_minutes"),
                                               changed_trunk_info.get(
                                                   "preempt_delay_seconds"),
                                               changed_trunk_info.get("preempt_delay_million_seconds")))
                else:
                    self.updates_cmd.append("undo preempt enable")

        if self.input_info.get("locality") is not None:
            if trunk_info.get(
                    "locality") != changed_trunk_info.get("locality"):
                if "true" == self.input_info.get("locality"):
                    self.updates_cmd.append("virtual-cluster-chassis locality")
                else:
                    self.updates_cmd.append(
                        "undo virtual-cluster-chassis locality")

        if self.input_info.get("hash_arith_type") is not None:
            if trunk_info.get("hash_arith_type") != changed_trunk_info.get(
                    "hash_arith_type"):
                self.updates_cmd.append(
                    "load-balance hash-arithmetic %s" %
                    self.input_info.get("hash_arith_type"))

        if self.input_info.get("dual_receive_enable") is not None:
            if trunk_info.get("dual_receive_enable") != changed_trunk_info.get(
                    "dual_receive_enable"):
                if "true" == self.input_info.get("dual_receive_enable"):
                    self.updates_cmd.append("backup-dual-receiving enable")
                else:
                    self.updates_cmd.append(
                        "undo backup-dual-receiving enable")

    def generate_set_trunk_mem_config_updates_cmd(
            self, trunk_member, changed_trunk_member):
        """generate updates command for set trunk member"""

        if self.input_info.get(
                "member_name") and changed_trunk_member is not None:
            member_changed = False
            self.updates_cmd.append(
                "interface %s" %
                changed_trunk_member.get("member_name"))

            if trunk_member is None and changed_trunk_member.get(
                    "trunk_name") is not None:
                trunk_name = changed_trunk_member.get("trunk_name")
                trunk_id = re.search(r"\d", trunk_name)
                if trunk_id is not None:
                    # eth-trunk1中插入空格
                    pos = trunk_id.span()[0]
                    add_trunk_member_cmd = trunk_name[:pos].lower(
                    ) + " " + trunk_name[pos:]
                    self.updates_cmd.append(add_trunk_member_cmd)
                    member_changed = True

            if self.input_info.get("member_weight") is not None:
                if trunk_member is None \
                        or trunk_member.get("member_weight") != changed_trunk_member.get("member_weight"):
                    self.updates_cmd.append(
                        "distribute-weight %s" %
                        self.input_info.get("member_weight"))
                    member_changed = True

            if self.input_info.get("member_port_master") is not None:
                if trunk_member is None \
                        or trunk_member.get("member_port_master") != changed_trunk_member.get("member_port_master"):
                    if "true" == self.input_info.get("member_port_master"):
                        self.updates_cmd.append("port-master")
                    else:
                        self.updates_cmd.append("undo port-master")
                    member_changed = True

            if self.input_info.get("member_hash_index") is not None:
                if trunk_member is None \
                        or trunk_member.get("member_hash_index") != changed_trunk_member.get("member_hash_index"):
                    self.updates_cmd.append(
                        "hash index %s" %
                        self.input_info.get("member_hash_index"))
                    member_changed = True

            if not member_changed:
                # 如果没有配置变更，去除interface <member_name>命令
                self.updates_cmd.pop()
            else:
                self.changed = member_changed

    def delete_trunk_config(self):
        """Delete Trunk interface config"""

        # 获取变更前的数据
        trunk_info = self.get_trunk_dict()
        trunk_member = None

        # 生成并下发yang报文
        xml_str = NE_NC_SET_TRUNK_HEAD % NE_NC_OPTYPE_MERGE
        for xml_key, cli_key in TRUNKIF_XML2CLI.items():
            if self.input_info.get(cli_key) is not None:
                if cli_key == "name":
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, self.input_info.get(cli_key))
                else:
                    xml_str = constr_leaf_process_delete(xml_str, xml_key)

        if self.input_info.get("locality") is not None:
            xml_str = constr_container_head(xml_str, "trunkLocality")
            xml_str = constr_leaf_process_delete(xml_str, "locality")
            xml_str = constr_container_tail(xml_str, "trunkLocality")

        if self.input_info.get("hash_arith_type") is not None:
            xml_str = constr_container_head(xml_str, "trunkHashArith")
            xml_str = constr_leaf_process_delete(xml_str, "hashArithType")
            xml_str = constr_container_tail(xml_str, "trunkHashArith")

        if self.input_info.get("dual_receive_enable") is not None:
            xml_str = constr_container_head(xml_str, "trunkDualRcv")
            xml_str = constr_leaf_process_delete(xml_str, "trunkDualRcvEnable")
            xml_str = constr_container_tail(xml_str, "trunkDualRcv")

        if self.input_info.get("member_name") is not None:
            # 获取变更前的数据
            trunk_member = self.get_trunk_member(
                self.input_info.get("name"),
                self.input_info.get("member_name"))
            if trunk_member is None:
                self.module.fail_json(
                    msg='Error: Trunk member interface does not exist in the trunk.')

            # 生成并下发yang报文
            xml_str = constr_container_head(xml_str, "TrunkMemberIfs")
            xml_str = constr_container_head(xml_str, "TrunkMemberIf")

            for xml_key, cli_key in TRUNKMEM_XML2CLI.items():
                if self.input_info.get(cli_key) is not None:
                    if cli_key == "member_name":
                        xml_str = constr_leaf_value(
                            xml_str, xml_key, self.input_info.get(cli_key))
                    else:
                        xml_str = constr_leaf_process_delete(xml_str, xml_key)

            if self.input_info.get("member_hash_index") is not None:
                xml_str = constr_container_head(xml_str, "fimHashIndex")
                xml_str = constr_leaf_process_delete(xml_str, "hashIndex")
                xml_str = constr_container_tail(xml_str, "fimHashIndex")

            xml_str = constr_container_tail(xml_str, "TrunkMemberIf")
            xml_str = constr_container_tail(xml_str, "TrunkMemberIfs")

        xml_str += NE_NC_SET_TRUNK_TAIL

        self.netconf_set_config(xml_str, "REMOVE_CONFIG_ON_TRUNK")

        # 获取变更后的数据
        changed_trunk_info = self.get_trunk_dict()
        changed_trunk_member = self.get_trunk_member(
            self.input_info.get("name"), self.input_info.get("member_name"))

        # 生成配置变更命令行
        self.generate_delete_trunk_if_config_updates_cmd(
            trunk_info, changed_trunk_info)
        self.generate_delete_trunk_mem_config_updates_cmd(
            trunk_member, changed_trunk_member)

    def generate_delete_trunk_if_config_updates_cmd(
            self, trunk_info, changed_trunk_info):
        """generate updates command for set trunk interafce"""

        # 比较非member字段是否变更
        for key, value in self.input_info.items():
            if re.match(r'^member_', key) is None \
                    and value is not None and changed_trunk_info.get(key) != trunk_info.get(key):
                self.changed = True
                break

        # 无配置变更，直接返回
        if not self.changed:
            return

        # 生成配置命令行
        if "true" == self.input_info.get("remote"):
            self.updates_cmd.append(
                "interface %s remote" %
                changed_trunk_info.get("name"))
        else:
            self.updates_cmd.append(
                "interface %s" %
                changed_trunk_info.get("name"))

        if self.input_info.get("mode") is not None:
            if trunk_info.get("mode") != changed_trunk_info.get("mode"):
                self.updates_cmd.append("undo mode")

        if self.input_info.get("min_links") is not None:
            if trunk_info.get(
                    "min_links") != changed_trunk_info.get("min_links"):
                self.updates_cmd.append("undo least active-linknumber")

        if self.input_info.get("min_bandwidth") is not None:
            if trunk_info.get("min_bandwidth") != changed_trunk_info.get(
                    "min_bandwidth"):
                self.updates_cmd.append("undo least active-bandwidth")

        if self.input_info.get("max_links") is not None:
            if trunk_info.get(
                    "max_links") != changed_trunk_info.get("max_links"):
                self.updates_cmd.append(
                    "undo max bandwidth-affected-linknumber")

        if self.input_info.get("hash_type") is not None:
            if trunk_info.get(
                    "hash_type") != changed_trunk_info.get("hash_type"):
                self.updates_cmd.append("undo load-balance")

        if self.input_info.get("smart_link_flush_vlan_id") is not None:
            if trunk_info.get("smart_link_flush_vlan_id") != changed_trunk_info.get(
                    "smart_link_flush_vlan_id"):
                self.updates_cmd.append("undo smart-link flush send")

        if self.input_info.get("inactive_port_shutdown") is not None:
            if trunk_info.get("inactive_port_shutdown") != changed_trunk_info.get(
                    "inactive_port_shutdown"):
                self.updates_cmd.append("undo inactive-port shutdown enable")

        if self.input_info.get("preempt_enable") is not None \
                or self.input_info.get("preempt_delay_minutes") is not None \
                or self.input_info.get("preempt_delay_seconds") is not None \
                or self.input_info.get("preempt_delay_million_seconds") is not None:

            if trunk_info.get("preempt_enable") != changed_trunk_info.get("preempt_enable") \
                    or trunk_info.get("preempt_delay_minutes") != changed_trunk_info.get("preempt_delay_minutes") \
                    or trunk_info.get("preempt_delay_seconds") != changed_trunk_info.get("preempt_delay_seconds") \
                    or trunk_info.get("preempt_delay_million_seconds") != changed_trunk_info.get(
                        "preempt_delay_million_seconds"):
                if "true" == changed_trunk_info.get("preempt_enable"):
                    self.updates_cmd.append("preempt enable delay %s %s %s"
                                            % (changed_trunk_info.get("preempt_delay_minutes"),
                                               changed_trunk_info.get(
                                                   "preempt_delay_seconds"),
                                               changed_trunk_info.get("preempt_delay_million_seconds")))
                else:
                    self.updates_cmd.append("undo preempt enable")

        if self.input_info.get("locality") is not None:
            if trunk_info.get(
                    "locality") != changed_trunk_info.get("locality"):
                self.updates_cmd.append(
                    "undo virtual-cluster-chassis locality")

        if self.input_info.get("hash_arith_type") is not None:
            if trunk_info.get("hash_arith_type") != changed_trunk_info.get(
                    "hash_arith_type"):
                self.updates_cmd.append("undo load-balance hash-arithmetic")

        if self.input_info.get("dual_receive_enable") is not None:
            if trunk_info.get("dual_receive_enable") != changed_trunk_info.get(
                    "dual_receive_enable"):
                self.updates_cmd.append("undo backup-dual-receiving enable")

    def generate_delete_trunk_mem_config_updates_cmd(
            self, trunk_member, changed_trunk_member):

        if self.input_info.get(
                "member_name") and changed_trunk_member is not None:
            member_changed = False
            self.updates_cmd.append(
                "interface %s" %
                changed_trunk_member.get("member_name"))

            if self.input_info.get("member_weight") is not None:
                if trunk_member.get("member_weight") != changed_trunk_member.get(
                        "member_weight"):
                    self.updates_cmd.append("undo distribute-weight")
                    member_changed = True

            if self.input_info.get("member_port_master") is not None:
                if trunk_member.get("member_port_master") != changed_trunk_member.get(
                        "member_port_master"):
                    self.updates_cmd.append("undo port-master")
                    member_changed = True

            if self.input_info.get("member_hash_index") is not None:
                if trunk_member.get("member_hash_index") != changed_trunk_member.get(
                        "member_hash_index"):
                    self.updates_cmd.append("undo hash index")
                    member_changed = True

            if not member_changed:
                # 如果没有配置变更，去除interface <member_name>命令
                self.updates_cmd.pop()
            else:
                self.changed = member_changed

    def delete_trunk_if(self):
        """Delete Eth-Trunk interface and remove all member"""
        if not self.trunk_info:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_SET_TRUNK_HEAD % NE_NC_OPTYPE_DELETE
        xml_str = constr_leaf_value(
            xml_str, "ifName", self.input_info.get("name"))
        xml_str += NE_NC_SET_TRUNK_TAIL

        self.netconf_set_config(xml_str, "DELETE_TRUNK")

        # 生成配置命令行
        self.updates_cmd.append(
            "undo interface %s" %
            self.trunk_info.get("name"))
        self.changed = True

    def delete_trunk_member(self):
        """Delete trunk member"""

        if self.input_info.get("member_name") is None:
            return

        trunk_member = self.get_trunk_member(
            self.input_info.get("name"),
            self.input_info.get("member_name"))
        if trunk_member is not None:
            xml_str = NE_NC_SET_TRUNK_MEM_HEAD % (
                self.input_info.get("name"), NE_NC_OPTYPE_DELETE)
            xml_str = constr_leaf_value(
                xml_str, "memberIfName", trunk_member.get("member_name"))
            xml_str += NE_NC_SET_TRUNK_MEM_TAIL
            self.netconf_set_config(xml_str, "DELETE_TRUNK_MEMBER")
            self.updates_cmd.append(
                "interface %s" %
                trunk_member.get("member_name"))

            if trunk_member.get("trunk_name") is not None:
                trunk_name = trunk_member.get("trunk_name")
                trunk_id = re.search(r"\d", trunk_name)
                if trunk_id is not None:
                    # eth-trunk1中插入空格
                    pos = trunk_id.span()[0]
                    delete_trunk_member_cmd = "undo " + \
                        trunk_name[:pos].lower()
                    self.updates_cmd.append(delete_trunk_member_cmd)
                    self.changed = True
        else:
            self.module.fail_json(
                msg='Error: Trunk member interface does not exist in the trunk.')

    def check_params(self):
        """Check all input params"""

        if self.input_info.get("name") is not None:
            if len(self.input_info.get("name")) > 63 or len(
                    self.input_info.get("name").replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Trunk interface name is not in the range from 1 to 63.')

        if self.input_info.get("member_name") is not None:
            if len(self.input_info.get("member_name")) > 63 or len(
                    self.input_info.get("member_name").replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Trunk member interface name is not in the range from 1 to 63.')

        if self.input_info.get("member_weight") is not None or self.input_info.get("member_port_master") is not None \
                or self.input_info.get("member_hash_index"):
            if self.input_info.get("member_name") is None:
                self.module.fail_json(
                    msg='Error: Trunk member interface name has no value')

    def get_proposed(self):
        """Get proposed info"""
        for key, value in self.input_info.items():
            if value is not None:
                self.proposed[key] = value

        self.proposed["state"] = self.state

    def get_existing(self):
        """Get existing info"""
        if not self.trunk_info:
            return

        for key, value in self.trunk_info.items():
            self.existing[key] = value

    def get_end_state(self):
        """Get end state info"""

        trunk_info = self.get_trunk_dict()
        if not trunk_info:
            return

        for key, value in trunk_info.items():
            self.end_state[key] = value

    def work(self):
        """worker"""

        self.check_params()
        self.trunk_info = self.get_trunk_dict()
        self.get_existing()
        self.get_proposed()

        if self.state != "present" and not self.trunk_info:
            self.module.fail_json(
                msg='Error: Interface %s does not exist' %
                self.input_info.get("name"))

        if self.state == "present":
            if not self.trunk_info:
                self.create_trunk_if()
            self.set_trunk_config()
        elif self.state == "absent":
            if not self.input_info.get("member_name"):
                self.delete_trunk_if()
            else:
                self.delete_trunk_member()
        elif self.state == "default":
            self.delete_trunk_config()

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
        mode=dict(required=False, choices=['manual', 'backup', 'lacp-static']),
        min_links=dict(required=False, type='int'),
        min_bandwidth=dict(required=False, type='int'),
        max_links=dict(required=False, type='int'),
        remote=dict(required=False, choices=['true', 'false']),
        hash_type=dict(required=False, choices=['src-dst-ip', 'src-dst-mac', 'packet-all',
                                                'l4', 'symmetric-hash', 'symmetric-hash-complement']),
        smart_link_flush_vlan_id=dict(required=False, type='int'),
        inactive_port_shutdown=dict(required=False, choices=['true', 'false']),
        preempt_enable=dict(required=False, choices=['true', 'false']),
        preempt_delay_minutes=dict(required=False, type='int'),
        preempt_delay_seconds=dict(required=False, type='int'),
        preempt_delay_million_seconds=dict(required=False, type='int'),

        locality=dict(required=False, choices=['true', 'false']),
        hash_arith_type=dict(
            required=False,
            choices=[
                'crc32_1',
                'crc32_2',
                'xor_16bit',
                'xor_8bit']),
        dual_receive_enable=dict(required=False, choices=['true', 'false']),

        member_name=dict(required=False, type='str'),
        member_weight=dict(required=False, type='str'),
        member_port_master=dict(required=False, choices=['true', 'false']),
        member_hash_index=dict(required=False, type='int'),

        state=dict(
            required=False,
            default='present',
            choices=[
                'present',
                'absent',
                'query',
                'default'])
    )

    argument_spec.update(ne_argument_spec)
    module = Interface_Trunk(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
