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

DOCUMENTATION = """
---
module: ce_netstream_global
version_added: "2.4"
short_description: Manages global parameters of NetStream on HUAWEI CloudEngine switches.
description:
    - Manages global parameters of NetStream on HUAWEI CloudEngine switches.
author: YangYang (@QijunPan)
options:
    type:
        description:
            - Specifies the type of netstream global.
        choices: ['ip', 'vxlan']
        default: 'ip'
    state:
        description:
            - Specify desired state of the resource.
        choices: ['present', 'absent']
        default: present
    interface:
        description:
            - Netstream global interface.
        required: true
    sampler_interval:
        description:
            -  Specifies the netstream sampler interval, length is 1 - 65535.
    sampler_direction:
        description:
            -  Specifies the netstream sampler direction.
        choices: ['inbound', 'outbound']
    statistics_direction:
        description:
            -  Specifies the netstream statistic direction.
        choices: ['inbound', 'outbound']
    statistics_record:
        description:
            -  Specifies the flexible netstream statistic record, length is 1 - 32.
    index_switch:
        description:
            -  Specifies the netstream index-switch.
        choices: ['16', '32']
        default: '16'
"""

EXAMPLES = '''
- name: netstream global module test
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

  - name: Configure a netstream sampler at interface 10ge1/0/2, direction is outbound,interval is 30.
    ce_netstream_global:
      interface: 10ge1/0/2
      type: ip
      sampler_interval: 30
      sampler_direction: outbound
      state: present
      provider: "{{ cli }}"
  - name: Configure a netstream flexible statistic at interface 10ge1/0/2, record is test1, type is ip.
    ce_netstream_global:
      type: ip
      interface: 10ge1/0/2
      statistics_record: test1
      provider: "{{ cli }}"
  - name: Set the vxlan index-switch to 32.
    ce_netstream_global:
      type: vxlan
      interface: all
      index_switch: 32
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"index_switch": "16",
        "interface": "10ge1/0/2",
        "state": "present",
        "statistics_record": "test",
        "type": "vxlan"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"flexible_statistic": [
            {
                "interface": "10ge1/0/2",
                "statistics_record": [],
                "type": "ip"
            },
            {
                "interface": "10ge1/0/2",
                "statistics_record": [],
                "type": "vxlan"
            }
        ],
        "index-switch": [
            {
                "index-switch": "16",
                "type": "ip"
            },
            {
                "index-switch": "16",
                "type": "vxlan"
            }
        ],
        "ip_record": [
            "test",
            "test1"
        ],
        "sampler": [
            {
                "interface": "all",
                "sampler_direction": "null",
                "sampler_interval": "null"
            }
        ],
        "statistic": [
            {
                "interface": "10ge1/0/2",
                "statistics_direction": [],
                "type": "null"
            }
        ],
        "vxlan_record": [
            "test"
        ]}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"flexible_statistic": [
            {
                "interface": "10ge1/0/2",
                "statistics_record": [],
                "type": "ip"
            },
            {
                "interface": "10ge1/0/2",
                "statistics_record": [
                    "test"
                ],
                "type": "vxlan"
            }
        ],
        "index-switch": [
            {
                "index-switch": "16",
                "type": "ip"
            },
            {
                "index-switch": "16",
                "type": "vxlan"
            }
        ],
        "sampler": [
            {
                "interface": "all",
                "sampler_direction": "null",
                "sampler_interval": "null"
            }
        ],
        "statistic": [
            {
                "interface": "10ge1/0/2",
                "statistics_direction": [],
                "type": "null"
            }
        ]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface 10ge1/0/2",
        "netstream record test vxlan inner-ip"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_config, load_config
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec


def get_interface_type(interface):
    """Gets the type of interface, such as 10GE, ETH-TRUNK..."""

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
    elif interface.upper().startswith('ETH-TRUNK'):
        iftype = 'eth-trunk'
    elif interface.upper().startswith('ALL'):
        iftype = 'all'
    else:
        return None

    return iftype.lower()


class NetStreamGlobal(object):
    """
    Manages netstream global parameters.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.type = self.module.params['type']
        self.interface = self.module.params['interface']
        self.sampler_interval = self.module.params['sampler_interval']
        self.sampler_direction = self.module.params['sampler_direction']
        self.statistics_direction = self.module.params['statistics_direction']
        self.statistics_record = self.module.params['statistics_record']
        self.index_switch = self.module.params['index_switch']
        self.state = self.module.params['state']

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

        # local parameters
        self.existing["sampler"] = list()
        self.existing["statistic"] = list()
        self.existing["flexible_statistic"] = list()
        self.existing["index-switch"] = list()
        self.existing["ip_record"] = list()
        self.existing["vxlan_record"] = list()
        self.end_state["sampler"] = list()
        self.end_state["statistic"] = list()
        self.end_state["flexible_statistic"] = list()
        self.end_state["index-switch"] = list()
        self.sampler_changed = False
        self.statistic_changed = False
        self.flexible_changed = False
        self.index_switch_changed = False

    def init_module(self):
        """init module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def cli_add_command(self, command, undo=False):
        """add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command

        self.commands.append(cmd)
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)

    def get_exist_sampler_interval(self):
        """get exist netstream sampler interval"""

        sampler_tmp = dict()
        sampler_tmp1 = dict()
        flags = list()
        exp = " | ignore-case  include ^netstream sampler random-packets"
        flags.append(exp)
        config = get_config(self.module, flags)
        if not config:
            sampler_tmp["sampler_interval"] = "null"
            sampler_tmp["sampler_direction"] = "null"
        else:
            config_list = config.split(' ')
            config_num = len(config_list)
            sampler_tmp["sampler_direction"] = config_list[config_num - 1]
            sampler_tmp["sampler_interval"] = config_list[config_num - 2]
        sampler_tmp["interface"] = "all"
        self.existing["sampler"].append(sampler_tmp)
        if self.interface != "all":
            flags = list()
            exp = " | ignore-case  section include ^interface %s$" \
                  " | include netstream sampler random-packets" % self.interface
            flags.append(exp)
            config = get_config(self.module, flags)
            if not config:
                sampler_tmp1["sampler_interval"] = "null"
                sampler_tmp1["sampler_direction"] = "null"
            else:
                config = config.lstrip()
                config_list = config.split('\n')
                for config_mem in config_list:
                    sampler_tmp1 = dict()
                    config_mem_list = config_mem.split(' ')
                    config_num = len(config_mem_list)
                    sampler_tmp1["sampler_direction"] = config_mem_list[
                        config_num - 1]
                    sampler_tmp1["sampler_interval"] = config_mem_list[
                        config_num - 2]
                    sampler_tmp1["interface"] = self.interface
                    self.existing["sampler"].append(sampler_tmp1)

    def get_exist_statistic_record(self):
        """get exist netstream statistic record parameter"""

        if self.statistics_record and self.statistics_direction:
            self.module.fail_json(
                msg='Error: The statistic direction and record can not exist at the same time.')
        statistic_tmp = dict()
        statistic_tmp1 = dict()
        statistic_tmp["statistics_record"] = list()
        statistic_tmp["interface"] = self.interface
        statistic_tmp1["statistics_record"] = list()
        statistic_tmp1["interface"] = self.interface
        flags = list()
        exp = " | ignore-case  section include ^interface %s$" \
              " | include netstream record"\
              % (self.interface)
        flags.append(exp)
        config = get_config(self.module, flags)
        if not config:
            statistic_tmp["type"] = "ip"
            self.existing["flexible_statistic"].append(statistic_tmp)
            statistic_tmp1["type"] = "vxlan"
            self.existing["flexible_statistic"].append(statistic_tmp1)
        else:
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem = config_mem.lstrip()
                statistic_tmp["statistics_record"] = list()
                config_mem_list = config_mem.split(' ')
                if str(config_mem_list[3]) == "ip":
                    statistic_tmp["statistics_record"].append(
                        str(config_mem_list[2]))
            statistic_tmp["type"] = "ip"
            self.existing["flexible_statistic"].append(statistic_tmp)
            for config_mem in config_list:
                statistic_tmp1["statistics_record"] = list()
                config_mem = config_mem.lstrip()
                config_mem_list = config_mem.split(' ')
                if str(config_mem_list[3]) == "vxlan":
                    statistic_tmp1["statistics_record"].append(
                        str(config_mem_list[2]))
            statistic_tmp1["type"] = "vxlan"
            self.existing["flexible_statistic"].append(statistic_tmp1)

    def get_exist_interface_statistic(self):
        """get exist netstream interface statistic parameter"""

        statistic_tmp1 = dict()
        statistic_tmp1["statistics_direction"] = list()
        flags = list()
        exp = " | ignore-case  section include ^interface %s$" \
              " | include netstream inbound|outbound"\
              % self.interface
        flags.append(exp)
        config = get_config(self.module, flags)
        if not config:
            statistic_tmp1["type"] = "null"
        else:
            statistic_tmp1["type"] = "ip"
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem = config_mem.lstrip()
                config_mem_list = config_mem.split(' ')
                statistic_tmp1["statistics_direction"].append(
                    str(config_mem_list[1]))
        statistic_tmp1["interface"] = self.interface
        self.existing["statistic"].append(statistic_tmp1)

    def get_exist_index_switch(self):
        """get exist netstream index-switch"""

        index_switch_tmp = dict()
        index_switch_tmp1 = dict()
        index_switch_tmp["index-switch"] = "16"
        index_switch_tmp["type"] = "ip"
        index_switch_tmp1["index-switch"] = "16"
        index_switch_tmp1["type"] = "vxlan"
        flags = list()
        exp = " | ignore-case  include index-switch"
        flags.append(exp)
        config = get_config(self.module, flags)
        if not config:
            self.existing["index-switch"].append(index_switch_tmp)
            self.existing["index-switch"].append(index_switch_tmp1)
        else:
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem_list = config_mem.split(' ')
                if str(config_mem_list[2]) == "ip":
                    index_switch_tmp["index-switch"] = "32"
                    index_switch_tmp["type"] = "ip"
                if str(config_mem_list[2]) == "vxlan":
                    index_switch_tmp1["index-switch"] = "32"
                    index_switch_tmp1["type"] = "vxlan"
            self.existing["index-switch"].append(index_switch_tmp)
            self.existing["index-switch"].append(index_switch_tmp1)

    def get_exist_record(self):
        """get exist netstream record"""

        flags = list()
        exp = " | ignore-case include netstream record"
        flags.append(exp)
        config = get_config(self.module, flags)
        if config:
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem_list = config_mem.split(' ')
                if config_mem_list[3] == "ip":
                    self.existing["ip_record"].append(config_mem_list[2])
                if config_mem_list[3] == "vxlan":
                    self.existing["vxlan_record"].append(config_mem_list[2])

    def get_end_sampler_interval(self):
        """get end netstream sampler interval"""

        sampler_tmp = dict()
        sampler_tmp1 = dict()
        flags = list()
        exp = " | ignore-case  include ^netstream sampler random-packets"
        flags.append(exp)
        config = get_config(self.module, flags)
        if not config:
            sampler_tmp["sampler_interval"] = "null"
            sampler_tmp["sampler_direction"] = "null"
        else:
            config_list = config.split(' ')
            config_num = len(config_list)
            sampler_tmp["sampler_direction"] = config_list[config_num - 1]
            sampler_tmp["sampler_interval"] = config_list[config_num - 2]
        sampler_tmp["interface"] = "all"
        self.end_state["sampler"].append(sampler_tmp)
        if self.interface != "all":
            flags = list()
            exp = " | ignore-case  section include ^interface %s$" \
                  " | include netstream sampler random-packets" % self.interface
            flags.append(exp)
            config = get_config(self.module, flags)
            if not config:
                sampler_tmp1["sampler_interval"] = "null"
                sampler_tmp1["sampler_direction"] = "null"
            else:
                config = config.lstrip()
                config_list = config.split('\n')
                for config_mem in config_list:
                    sampler_tmp1 = dict()
                    config_mem_list = config_mem.split(' ')
                    config_num = len(config_mem_list)
                    sampler_tmp1["sampler_direction"] = config_mem_list[
                        config_num - 1]
                    sampler_tmp1["sampler_interval"] = config_mem_list[
                        config_num - 2]
                    sampler_tmp1["interface"] = self.interface
                    self.end_state["sampler"].append(sampler_tmp1)

    def get_end_statistic_record(self):
        """get end netstream statistic record parameter"""

        if self.statistics_record and self.statistics_direction:
            self.module.fail_json(
                msg='Error: The statistic direction and record can not exist at the same time.')
        statistic_tmp = dict()
        statistic_tmp1 = dict()
        statistic_tmp["statistics_record"] = list()
        statistic_tmp["interface"] = self.interface
        statistic_tmp1["statistics_record"] = list()
        statistic_tmp1["interface"] = self.interface
        flags = list()
        exp = " | ignore-case  section include ^interface %s$" \
              " | include netstream record"\
              % (self.interface)
        flags.append(exp)
        config = get_config(self.module, flags)
        if not config:
            statistic_tmp["type"] = "ip"
            self.end_state["flexible_statistic"].append(statistic_tmp)
            statistic_tmp1["type"] = "vxlan"
            self.end_state["flexible_statistic"].append(statistic_tmp1)
        else:
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem = config_mem.lstrip()
                statistic_tmp["statistics_record"] = list()
                config_mem_list = config_mem.split(' ')
                if str(config_mem_list[3]) == "ip":
                    statistic_tmp["statistics_record"].append(
                        str(config_mem_list[2]))
            statistic_tmp["type"] = "ip"
            self.end_state["flexible_statistic"].append(statistic_tmp)
            for config_mem in config_list:
                statistic_tmp1["statistics_record"] = list()
                config_mem = config_mem.lstrip()
                config_mem_list = config_mem.split(' ')
                if str(config_mem_list[3]) == "vxlan":
                    statistic_tmp1["statistics_record"].append(
                        str(config_mem_list[2]))
            statistic_tmp1["type"] = "vxlan"
            self.end_state["flexible_statistic"].append(statistic_tmp1)

    def get_end_interface_statistic(self):
        """get end netstream interface statistic parameters"""

        statistic_tmp1 = dict()
        statistic_tmp1["statistics_direction"] = list()
        flags = list()
        exp = " | ignore-case  section include ^interface %s$" \
              " | include netstream inbound|outbound"\
              % self.interface
        flags.append(exp)
        config = get_config(self.module, flags)
        if not config:
            statistic_tmp1["type"] = "null"
        else:
            statistic_tmp1["type"] = "ip"
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem = config_mem.lstrip()
                config_mem_list = config_mem.split(' ')
                statistic_tmp1["statistics_direction"].append(
                    str(config_mem_list[1]))
        statistic_tmp1["interface"] = self.interface
        self.end_state["statistic"].append(statistic_tmp1)

    def get_end_index_switch(self):
        """get end netstream index switch"""

        index_switch_tmp = dict()
        index_switch_tmp1 = dict()
        index_switch_tmp["index-switch"] = "16"
        index_switch_tmp["type"] = "ip"
        index_switch_tmp1["index-switch"] = "16"
        index_switch_tmp1["type"] = "vxlan"
        flags = list()
        exp = " | ignore-case  include index-switch"
        flags.append(exp)
        config = get_config(self.module, flags)
        if not config:
            self.end_state["index-switch"].append(index_switch_tmp)
            self.end_state["index-switch"].append(index_switch_tmp1)
        else:
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem_list = config_mem.split(' ')
                if str(config_mem_list[2]) == "ip":
                    index_switch_tmp["index-switch"] = "32"
                    index_switch_tmp["type"] = "ip"
                if str(config_mem_list[2]) == "vxlan":
                    index_switch_tmp1["index-switch"] = "32"
                    index_switch_tmp1["type"] = "vxlan"
            self.end_state["index-switch"].append(index_switch_tmp)
            self.end_state["index-switch"].append(index_switch_tmp1)

    def check_params(self):
        """check all input params"""

        # netstream parameters check
        if not get_interface_type(self.interface):
            self.module.fail_json(
                msg='Error: Interface name of %s is error.' % self.interface)
        if self.sampler_interval:
            if not str(self.sampler_interval).isdigit():
                self.module.fail_json(
                    msg='Error: Active interval should be numerical.')
            if int(self.sampler_interval) < 1 or int(self.sampler_interval) > 65535:
                self.module.fail_json(
                    msg="Error: Sampler interval should between 1 - 65535.")
        if self.statistics_record:
            if len(self.statistics_record) < 1 or len(self.statistics_record) > 32:
                self.module.fail_json(
                    msg="Error: Statistic record length should between 1 - 32.")
        if self.interface == "all":
            if self.statistics_record or self.statistics_direction:
                self.module.fail_json(
                    msg="Error: Statistic function should be used at interface.")
        if self.statistics_direction:
            if self.type == "vxlan":
                self.module.fail_json(
                    msg="Error: Vxlan do not support inbound or outbound statistic.")
        if (self.sampler_interval and not self.sampler_direction) \
                or (self.sampler_direction and not self.sampler_interval):
            self.module.fail_json(
                msg="Error: Sampler interval and direction must be set at the same time.")

        if self.statistics_record and not self.type:
            self.module.fail_json(
                msg="Error: Statistic type and record must be set at the same time.")

        self.get_exist_record()
        if self.statistics_record:
            if self.type == "ip":
                if self.statistics_record not in self.existing["ip_record"]:
                    self.module.fail_json(
                        msg="Error: The statistic record is not exist.")
            if self.type == "vxlan":
                if self.statistics_record not in self.existing["vxlan_record"]:
                    self.module.fail_json(
                        msg="Error: The statistic record is not exist.")

    def get_proposed(self):
        """get proposed info"""

        if self.type:
            self.proposed["type"] = self.type
        if self.interface:
            self.proposed["interface"] = self.interface
        if self.sampler_interval:
            self.proposed["sampler_interval"] = self.sampler_interval
        if self.sampler_direction:
            self.proposed["sampler_direction"] = self.sampler_direction
        if self.statistics_direction:
            self.proposed["statistics_direction"] = self.statistics_direction
        if self.statistics_record:
            self.proposed["statistics_record"] = self.statistics_record
        if self.index_switch:
            self.proposed["index_switch"] = self.index_switch
        if self.state:
            self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        sampler_tmp = dict()
        statistic_tmp = dict()
        statistic_tmp1 = dict()
        index_tmp = dict()
        temp = False

        self.get_exist_sampler_interval()
        self.get_exist_interface_statistic()
        self.get_exist_statistic_record()
        self.get_exist_index_switch()

        if self.state == "present":
            for sampler_tmp in self.existing["sampler"]:
                if self.interface == str(sampler_tmp["interface"]):
                    temp = True
                    if (self.sampler_interval and str(sampler_tmp["sampler_interval"]) != self.sampler_interval) \
                            or (self.sampler_direction and
                                str(sampler_tmp["sampler_direction"]) != self.sampler_direction):
                        self.sampler_changed = True
            if not temp:
                if self.sampler_direction or self.sampler_interval:
                    self.sampler_changed = True
            for statistic_tmp in self.existing["statistic"]:
                if str(statistic_tmp["interface"]) == self.interface and self.interface != "all":
                    if self.type == "vxlan":
                        if statistic_tmp["statistics_direction"] \
                                and 'outbound' in statistic_tmp["statistics_direction"]:
                            self.module.fail_json(
                                msg='Error: The NetStream record vxlan '
                                    'cannot be configured because the port has been configured NetStream outbound ip.')
                    if statistic_tmp["statistics_direction"] and self.statistics_direction:
                        if self.statistics_direction not in statistic_tmp["statistics_direction"]:
                            self.statistic_changed = True
                    else:
                        if self.statistics_direction:
                            self.statistic_changed = True
            for statistic_tmp1 in self.existing["flexible_statistic"]:
                if self.interface != "all" \
                        and self.type == str(statistic_tmp1["type"]) \
                        and self.interface == str(statistic_tmp1["interface"]):
                    if statistic_tmp1["statistics_record"] and self.statistics_record:
                        if self.statistics_record not in statistic_tmp1["statistics_record"]:
                            self.flexible_changed = True
                    else:
                        if self.statistics_record:
                            self.flexible_changed = True
            for index_tmp in self.existing["index-switch"]:
                if self.type == str(index_tmp["type"]):
                    if self.index_switch != str(index_tmp["index-switch"]):
                        self.index_switch_changed = True
        else:
            for sampler_tmp in self.existing["sampler"]:
                if self.interface == str(sampler_tmp["interface"]):
                    if (self.sampler_interval and str(sampler_tmp["sampler_interval"]) == self.sampler_interval) \
                            and (self.sampler_direction and str(sampler_tmp["sampler_direction"]) == self.sampler_direction):
                        self.sampler_changed = True
            for statistic_tmp in self.existing["statistic"]:
                if str(statistic_tmp["interface"]) == self.interface and self.interface != "all":
                    if len(statistic_tmp["statistics_direction"]) and self.statistics_direction:
                        if self.statistics_direction in statistic_tmp["statistics_direction"]:
                            self.statistic_changed = True
            for statistic_tmp1 in self.existing["flexible_statistic"]:
                if self.interface != "all" \
                        and self.type == str(statistic_tmp1["type"]) \
                        and self.interface == str(statistic_tmp1["interface"]):
                    if len(statistic_tmp1["statistics_record"]) and self.statistics_record:
                        if self.statistics_record in statistic_tmp1["statistics_record"]:
                            self.flexible_changed = True
            for index_tmp in self.existing["index-switch"]:
                if self.type == str(index_tmp["type"]):
                    if self.index_switch == str(index_tmp["index-switch"]):
                        if self.index_switch != "16":
                            self.index_switch_changed = True

    def operate_ns_gloabl(self):
        """configure netstream global parameters"""

        cmd = ""
        if not self.sampler_changed and not self.statistic_changed \
                and not self.flexible_changed and not self.index_switch_changed:
            self.changed = False
            return

        if self.sampler_changed is True:
            if self.type == "vxlan":
                self.module.fail_json(
                    msg="Error: Netstream do not support vxlan sampler.")
            if self.interface != "all":
                cmd = "interface %s" % self.interface
                self.cli_add_command(cmd)
            cmd = "netstream sampler random-packets %s %s" % (
                self.sampler_interval, self.sampler_direction)
            if self.state == "present":
                self.cli_add_command(cmd)
            else:
                self.cli_add_command(cmd, undo=True)
            if self.interface != "all":
                cmd = "quit"
                self.cli_add_command(cmd)
        if self.statistic_changed is True:
            if self.interface != "all":
                cmd = "interface %s" % self.interface
                self.cli_add_command(cmd)
            cmd = "netstream %s ip" % self.statistics_direction
            if self.state == "present":
                self.cli_add_command(cmd)
            else:
                self.cli_add_command(cmd, undo=True)
            if self.interface != "all":
                cmd = "quit"
                self.cli_add_command(cmd)
        if self.flexible_changed is True:
            if self.interface != "all":
                cmd = "interface %s" % self.interface
                self.cli_add_command(cmd)
            if self.state == "present":
                for statistic_tmp in self.existing["flexible_statistic"]:
                    tmp_list = statistic_tmp["statistics_record"]
                    if self.type == statistic_tmp["type"]:
                        if self.type == "ip":
                            if len(tmp_list):
                                cmd = "netstream record %s ip" % tmp_list[0]
                                self.cli_add_command(cmd, undo=True)
                            cmd = "netstream record %s ip" % self.statistics_record
                            self.cli_add_command(cmd)
                        if self.type == "vxlan":
                            if len(tmp_list):
                                cmd = "netstream record %s vxlan inner-ip" % tmp_list[
                                    0]
                                self.cli_add_command(cmd, undo=True)
                            cmd = "netstream record %s vxlan inner-ip" % self.statistics_record
                            self.cli_add_command(cmd)
            else:
                if self.type == "ip":
                    cmd = "netstream record %s ip" % self.statistics_record
                    self.cli_add_command(cmd, undo=True)
                if self.type == "vxlan":
                    cmd = "netstream record %s vxlan inner-ip" % self.statistics_record
                    self.cli_add_command(cmd, undo=True)
            if self.interface != "all":
                cmd = "quit"
                self.cli_add_command(cmd)
        if self.index_switch_changed is True:
            if self.interface != "all":
                self.module.fail_json(
                    msg="Error: Index-switch function should be used globally.")
            if self.type == "ip":
                cmd = "netstream export ip index-switch %s" % self.index_switch
            else:
                cmd = "netstream export vxlan inner-ip index-switch %s" % self.index_switch
            if self.state == "present":
                self.cli_add_command(cmd)
            else:
                self.cli_add_command(cmd, undo=True)

        if self.commands:
            self.cli_load_config(self.commands)
            self.changed = True

    def get_end_state(self):
        """get end state info"""

        self.get_end_sampler_interval()
        self.get_end_interface_statistic()
        self.get_end_statistic_record()
        self.get_end_index_switch()

    def work(self):
        """worker"""

        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.operate_ns_gloabl()
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
        type=dict(required=False, choices=['ip', 'vxlan'], default='ip'),
        interface=dict(required=True, type='str'),
        sampler_interval=dict(required=False, type='str'),
        sampler_direction=dict(required=False, choices=['inbound', 'outbound']),
        statistics_direction=dict(required=False, choices=['inbound', 'outbound']),
        statistics_record=dict(required=False, type='str'),
        index_switch=dict(required=False, choices=['16', '32'], default='16'),
        state=dict(required=False, choices=['present', 'absent'], default='present'),
    )
    argument_spec.update(ce_argument_spec)
    module = NetStreamGlobal(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
