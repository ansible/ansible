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
module: ne_interface_action
version_added: "2.6"
short_description: Maintenance of an interface on HUAWEI netengine routers.
description:
    - Maintenance of an interface on HUAWEI netengine routers.
author: Shijiawei (@netengine-Ansible)
options:
    action_type:
        description:
            - Excute action type.
              reset_counters: Clear statistics based on the interface name.
              reset_counters_type: Clear statistics based on the interface type.
              reset_counters_all: Clear the statistics on all interfaces.
              reset_control_flap_counter: Clear the number of flapping control times.
              reset_control_flap_penalty: Clear the penalty value of an interface and remove the suppression on the interface.
              restart_interface: Restart interface.
              trunk_switch: 1:1 trunk switch.
              reset_counters_drop_mru: Clear interface Mru discard statistics.
              reset_remote_stat: Clear remote interface statistics.
              reset_fwd_stat_pkt_discard: Clear forward-statistics packet discard interface.
              subinterface_statistics_enable: The switch of sub interface statistics enable.
        required: true
        default: null
        choice: ["reset_counters", "reset_counters_type", "reset_counters_all",
                 "reset_control_flap_counter", "reset_control_flap_penalty",
                 "restart_interface", "trunk_switch", "reset_counters_drop_mru",
                 "reset_remote_stat", "reset_fwd_stat_pkt_discard",
                 "subinterface_statistics_enable"]
    name:
        description:
            - Interface name. The value is a string of 1 to 63 characters.
        required: false
        default: null
    interface_type:
        description:
            - Interface type.
        required: false
        default: null
        choice: ["gigabitethernet", "eth-trunk", "ip-trunk", "pos", "tunnel", "null", "loopback", "vlanif",
                 "100ge", "40ge", "mtunnel", "cpos", "e1", "serial", "vritual-ethernet", "ima-group", "vbridge",
                 "atm-bundle", "lmpif", "t1", "t3", "global-ve", "vbdif", "e3", "pos-trunk", "trunk-serial",
                 "global-ima-group", "global-mp-group", "wdm", "nve", "virtual-template", "atm", "xgigabitethernet",
                 "flexe", "50|100ge", "50ge", "pw-ve", "virtual-serial", "400ge"]
    stat_enable:
        description:
            - The switch of sub interface statistics enable.
        required: false
        default: null
        choices: ['true', 'false']
'''

EXAMPLES = '''
- name: interface_action module test
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
  - name: Reset counters by interface
    ne_interface_action:
      action_type:reset_counters
      name: GigabitEthernet2/0/0
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"action_type": "reset_counters", "name": "GigabitEthernet2/0/0"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["reset counters interface GigabitEthernet2/0/0"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import re
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import execute_nc_action_yang, ne_argument_spec

logging.basicConfig(filename='/opt/python_logger.log', level=logging.INFO)

ACTION_TYPE_LIST = ["reset_counters", "reset_counters_type", "reset_counters_all",
                    "reset_control_flap_counter", "reset_control_flap_penalty",
                    "restart_interface", "trunk_switch", "reset_counters_drop_mru",
                    "reset_remote_stat", "reset_fwd_stat_pkt_discard",
                    "subinterface_statistics_enable"]

IFTYPE_LIST = ["gigabitethernet", "eth-trunk", "ip-trunk", "pos", "tunnel", "null", "loopback", "vlanif",
               "100ge", "40ge", "mtunnel", "cpos", "e1", "serial", "vritual-ethernet", "ima-group", "vbridge",
               "atm-bundle", "lmpif", "t1", "t3", "global-ve", "vbdif", "e3", "pos-trunk", "trunk-serial",
               "global-ima-group", "global-mp-group", "wdm", "nve", "virtual-template", "atm", "xgigabitethernet",
               "flexe", "50|100ge", "50ge", "pw-ve", "virtual-serial", "400ge"]

IFTYPE_CLI2XML = {
    "gigabitethernet": "GigabitEthernet",
    "eth-trunk": "Eth-Trunk",
    "ip-trunk": "Ip-Trunk",
    "pos": "Pos",
    "tunnel": "Tunnel",
    "null": "NULL",
    "loopback": "LoopBack",
    "vlanif": "Vlanif",
    "100ge": "100GE",
    "40ge": "40GE",
    "mtunnel": "Mtunnel",
    "cpos": "Cpos",
    "e1": "E1",
    "serial": "Serial",
    "vritual-ethernet": "Virtual-Ethernet",
    "ima-group": "Ima-group",
    "vbridge": "VBridge",
    "atm-bundle": "Atm-Bundle",
    "lmpif": "Lmpif",
    "t1": "T1",
    "t3": "T3",
    "global-ve": "Global-VE",
    "vbdif": "Vbdif",
    "e3": "E3",
    "pos-trunk": "Pos-Trunk",
    "trunk-serial": "Trunk-Serial",
    "global-ima-group": "Global-Ima-Group",
    "global-mp-group": "Global-Mp-Group",
    "wdm": "Wdm",
    "nve": "Nve",
    "virtual-template": "Virtual-Template",
    "atm": "ATM",
    "xgigabitethernet": "XGigabitEthernet",
    "flexe": "FlexE",
    "50|100ge": "50|100GE",
    "50ge": "50GE",
    "pw-ve": "PW-VE",
    "virtual-serial": "Virtual-Serial",
    "400ge": "400GE"
}

NE_NC_RESET_COUNTERS_INTERFACE = """
    <ifm:rstStaByIfName xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:ifName>%s</ifm:ifName>
    </ifm:rstStaByIfName>
"""

NE_NC_RESET_COUNTERS_IFTYPE = """
    <ifm:rstStaByPhyType xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:ifPhyType>%s</ifm:ifPhyType>
    </ifm:rstStaByPhyType>
"""

NE_NC_RESET_COUNTERS_ALL = """
    <ifm:rstStaByAll xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:allIf>true</ifm:allIf>
    </ifm:rstStaByAll>
"""

NE_NC_RESET_CTRLFLAP_COUNTER = """
    <ifm:rstIfCnt xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:ifName>%s</ifm:ifName>
    </ifm:rstIfCnt>
"""

NE_NC_RESET_CTRLFLAP_PENALTY = """
    <ifm:rstIfPnlty xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:ifName>%s</ifm:ifName>
    </ifm:rstIfPnlty>
"""

NE_NC_RESTART_INTERFACE = """
    <ifm:restartInterface xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:ifName>%s</ifm:ifName>
    </ifm:restartInterface>
"""

NE_NC_SUBINTERFACE_STAT_ENABLE = """
    <ifm:SubIfStatistics xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:SubIfStatisticsEnable>%s</ifm:SubIfStatisticsEnable>
        <ifm:mainifName>%s</ifm:mainifName>
    </ifm:SubIfStatistics>
"""

NE_NC_TRUNK_SWICTH = """
    <ifmtrunk:trunkSwicth xmlns:ifmtrunk="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk">
        <ifmtrunk:ifName>%s</ifmtrunk:ifName>
    </ifmtrunk:trunkSwicth>
"""

NE_NC_RESET_FWD_STAT_PKT_DISCARD = """
    <ifm:rstIfMacMtuDisStat xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:ifName>%s</ifm:ifName>
    </ifm:rstIfMacMtuDisStat>
"""

NE_NC_RESET_COUNTERS_DROP_MRU = """
    <ifm:rstIfMruDisStat xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:ifName>%s</ifm:ifName>
    </ifm:rstIfMruDisStat>
"""

NE_NC_RESET_REMOTE_STAT = """
    <ifm:rstRemoteIfStat xmlns:ifm="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <ifm:ifName>%s</ifm:ifName>
    </ifm:rstRemoteIfStat>
"""


class Interface_Action(object):
    """ Manages interface action"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.input_info = dict()
        self.input_info["action_type"] = self.module.params["action_type"]
        self.input_info["name"] = self.module.params["name"]
        self.input_info["interface_type"] = self.module.params["interface_type"]
        self.input_info["stat_enable"] = self.module.params["stat_enable"]

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()

    def init_module(self):
        """ init module """
        required_one_of = []
        required_together = [
            ("main_interface_name",
             "subinterface_statistics_enable")]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
            required_together=required_together,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        action = self.input_info.get("action_type")
        if "reset_counters_type" == action:
            if self.input_info.get("interface_type") is None:
                self.module.fail_json(
                    msg='Error: Missing required arguments: interface_type')
            if self.input_info.get("name") is not None:
                self.module.fail_json(
                    msg='Error: The arguments: name is not supported, when action_type is %s' % action)
            if self.input_info.get("stat_enable") is not None:
                self.module.fail_json(
                    msg='Error: The arguments: stat_enable is not supported, when action_type is %s' % action)

        elif "reset_counters_all" == self.input_info.get("action_type"):
            if self.input_info.get("interface_type") is not None:
                self.module.fail_json(
                    msg='Error: The arguments: interface_type is not supported, when action_type is %s' % action)
            if self.input_info.get("name") is not None:
                self.module.fail_json(
                    msg='Error: The arguments: name is not supported, when action_type is %s' % action)
            if self.input_info.get("stat_enable") is not None:
                self.module.fail_json(
                    msg='Error: The arguments: stat_enable is not supported, when action_type is %s' % action)

        elif "subinterface_statistics_enable" == self.input_info.get("action_type"):
            if self.input_info.get("name") is None:
                self.module.fail_json(
                    msg='Error: Missing required arguments: name')
            if self.input_info.get("stat_enable") is None:
                self.module.fail_json(
                    msg='Error: Missing required arguments: stat_enable')
            if self.input_info.get("interface_type") is not None:
                self.module.fail_json(
                    msg='Error: The arguments: interface_type is not supported, when action_type is %s' % action)

        else:
            if self.input_info.get("name") is None:
                self.module.fail_json(
                    msg='Error: Missing required arguments: name')
            if self.input_info.get("interface_type") is not None:
                self.module.fail_json(
                    msg='Error: The arguments: interface_type is not supported, when action_type is %s' % action)
            if self.input_info.get("stat_enable") is not None:
                self.module.fail_json(
                    msg='Error: The arguments: stat_enable is not supported, when action_type is %s' % action)

        if self.input_info.get("name") is not None:
            if len(self.input_info.get("name")) > 63 or len(
                    self.input_info.get("name").replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Interface name is not in the range from 1 to 63.')

    def netconf_execute_action(self, xml_str, xml_name):
        """ netconf execute action"""

        logging.info("netconf_execute_action %s %s", xml_name, xml_str)
        recv_xml = execute_nc_action_yang(self.module, xml_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def reset_counters_interface(self, name):
        """reset counters interface name"""

        if not name:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_COUNTERS_INTERFACE % name
        self.netconf_execute_action(xml_str, "RESET_COUNTERS_INTERFACE")

        # 生成配置命令行
        position = re.search(r'\AE1|\AE3|\AT1|\AT3|\ACPOS|\AWDM', name.upper())
        if position:
            self.updates_cmd.append("reset counters controller %s" % name)
        else:
            self.updates_cmd.append("reset counters interface %s" % name)
        self.changed = True

    def reset_counters_interface_type(self, type):
        """reset counters interface type"""

        if not type:
            return

        # 转换输入类型为物理类型
        yang_interface_type = IFTYPE_CLI2XML.get(type)
        if not yang_interface_type:
            self.module.fail_json(
                msg='Error: interface type %s is invalid.' %
                type)

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_COUNTERS_IFTYPE % yang_interface_type
        self.netconf_execute_action(xml_str, "RESET_COUNTERS_IFTYPE")

        # 生成配置命令行
        position = re.search(
            r'E1|E3|T1|T3|CPOS|WDM',
            yang_interface_type.upper())
        if position:
            self.updates_cmd.append(
                "reset counters controller %s" %
                yang_interface_type)
        else:
            self.updates_cmd.append(
                "reset counters interface %s" %
                yang_interface_type)
        self.changed = True

    def reset_counters_all_interface(self):
        """reset counters interface"""

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_COUNTERS_ALL
        self.netconf_execute_action(xml_str, "RESET_COUNTERS")

        # 生成配置命令行
        self.updates_cmd.append("reset counters interface")
        self.changed = True

    def reset_control_flap_counter(self, name):
        """reset control-flap counter interface"""

        if not name:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_CTRLFLAP_COUNTER % name
        self.netconf_execute_action(xml_str, "RESET_CTRLFLAP_COUNTER")

        # 生成配置命令行
        self.updates_cmd.append(
            "reset control-flap counter interface %s" %
            name)
        self.changed = True

    def reset_control_flap_penalty(self, name):
        """reset control-flap counter interface"""

        if not name:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_CTRLFLAP_PENALTY % name
        self.netconf_execute_action(xml_str, "RESET_CTRLFLAP_PENALTY")

        # 生成配置命令行
        self.updates_cmd.append(
            "reset control-flap penalty interface %s" %
            name)
        self.changed = True

    def restart_interface(self, name):
        """restart interface"""

        if not name:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_CTRLFLAP_PENALTY % name
        self.netconf_execute_action(xml_str, "RESTART_INTERFACE")

        # 生成配置命令行
        self.updates_cmd.append("interface %s" % name)
        self.updates_cmd.append("restart")
        self.changed = True

    def subinterface_stat_enable(self, name, enable):
        """subinterface traffic-statistics enable"""

        if not name or not enable:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_SUBINTERFACE_STAT_ENABLE % (enable, name)
        self.netconf_execute_action(xml_str, "SUBINTERFACE_STAT_ENABLE")

        # 生成配置命令行
        self.updates_cmd.append("interface %s" % name)
        if "true" == enable:
            self.updates_cmd.append("subinterface traffic-statistics enable")
        else:
            self.updates_cmd.append(
                "undo subinterface traffic-statistics enable")
        self.changed = True

    def trunk_switch(self, name):
        """protect-switch"""

        if not name:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_TRUNK_SWICTH % (name)
        self.netconf_execute_action(xml_str, "TRUNK_SWITCH")

        # 生成配置命令行
        self.updates_cmd.append("interface %s" % name)
        self.updates_cmd.append("protect-switch")
        self.changed = True

    def reset_fwd_stat_pkt_discard(self, name):
        """reset forward-statistics packet discard"""

        if not name:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_FWD_STAT_PKT_DISCARD % (name)
        self.netconf_execute_action(xml_str, "RESET_FWD_STAT_PKT_DISCARD")

        # 生成配置命令行
        self.updates_cmd.append(
            "reset forward-statistics packet discard interface %s" %
            name)
        self.changed = True

    def reset_counters_drop_mru(self, name):
        """reset counters interface drop mru"""

        if not name:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_COUNTERS_DROP_MRU % (name)
        self.netconf_execute_action(xml_str, "RESET_COUNTERS_DROP_MRU")

        # 生成配置命令行
        self.updates_cmd.append("reset counters interface %s drop mru" % name)
        self.changed = True

    def reset_remote_stat(self, name):
        """reset remote statistics interface"""

        if not name:
            return

        # 生成并下发yang报文
        xml_str = NE_NC_RESET_REMOTE_STAT % (name)
        self.netconf_execute_action(xml_str, "RESET_REMOTE_STAT")

        # 生成配置命令行
        self.updates_cmd.append("reset remote statistics interface %s" % name)
        self.changed = True

    def get_proposed(self):
        """get proposed info"""
        for key, value in self.input_info.items():
            if value is not None:
                self.proposed[key] = value

    def work(self):
        """worker"""
        self.get_proposed()
        self.check_params()

        action_type = self.input_info.get("action_type")
        name = self.input_info.get("name")
        interface_type = self.input_info.get("interface_type")
        stat_enable = self.input_info.get("stat_enable")

        if "reset_counters" == action_type:
            self.reset_counters_interface(name)

        if "reset_counters_type" == action_type:
            self.reset_counters_interface_type(interface_type)

        if "reset_counters_all" == action_type:
            self.reset_counters_all_interface()

        if "reset_control_flap_counter" == action_type:
            self.reset_control_flap_counter(name)

        if "reset_control_flap_penalty" == action_type:
            self.reset_control_flap_penalty(name)

        if "restart_interface" == action_type:
            self.restart_interface(name)

        if "subinterface_statistics_enable" == action_type:
            self.subinterface_stat_enable(name, stat_enable)

        if "reset_counters_drop_mru" == action_type:
            self.reset_counters_drop_mru(name)

        if "reset_remote_stat" == action_type:
            self.reset_remote_stat(name)

        if "reset_fwd_stat_pkt_discard" == action_type:
            self.reset_fwd_stat_pkt_discard(name)

        if "trunk_switch" == action_type:
            self.trunk_switch(name)

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """Module main"""
    argument_spec = dict(
        action_type=dict(required=True, choices=ACTION_TYPE_LIST),
        name=dict(required=False, type='str'),
        interface_type=dict(required=False, choices=IFTYPE_LIST),
        stat_enable=dict(required=False, choices=['true', 'false'])
    )

    argument_spec.update(ne_argument_spec)
    module = Interface_Action(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
