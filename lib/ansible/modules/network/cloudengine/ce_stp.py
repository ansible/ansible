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
module: ce_stp
version_added: "2.4"
short_description: Manages STP configuration on HUAWEI CloudEngine switches.
description:
    - Manages STP configurations on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@QijunPan)
options:
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present', 'absent']
    stp_mode:
        description:
            - Set an operation mode for the current MSTP process.
              The mode can be STP, RSTP, or MSTP.
        choices: ['stp', 'rstp', 'mstp']
    stp_enable:
        description:
            - Enable or disable STP on a switch.
        choices: ['enable', 'disable']
    stp_converge:
        description:
            - STP convergence mode.
              Fast means set STP aging mode to Fast.
              Normal means set STP aging mode to Normal.
        choices: ['fast', 'normal']
    bpdu_protection:
        description:
            - Configure BPDU protection on an edge port.
              This function prevents network flapping caused by attack packets.
        choices: ['enable', 'disable']
    tc_protection:
        description:
            - Configure the TC BPDU protection function for an MSTP process.
        choices: ['enable', 'disable']
    tc_protection_interval:
        description:
            - Set the time the MSTP device takes to handle the maximum number of TC BPDUs
              and immediately refresh forwarding entries.
              The value is an integer ranging from 1 to 600, in seconds.
    tc_protection_threshold:
        description:
            - Set the maximum number of TC BPDUs that the MSTP can handle.
              The value is an integer ranging from 1 to 255. The default value is 1 on the switch.
    interface:
        description:
            - Interface name.
              If the value is C(all), will apply configuration to all interfaces.
              if the value is a special name, only support input the full name.
    edged_port:
        description:
            - Set the current port as an edge port.
        choices: ['enable', 'disable']
    bpdu_filter:
        description:
            - Specify a port as a BPDU filter port.
        choices: ['enable', 'disable']
    cost:
        description:
            - Set the path cost of the current port.
              The default instance is 0.
    root_protection:
        description:
            - Enable root protection on the current port.
        choices: ['enable', 'disable']
    loop_protection:
        description:
            - Enable loop protection on the current port.
        choices: ['enable', 'disable']
'''

EXAMPLES = '''

- name: CloudEngine stp test
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

  - name: "Config stp mode"
    ce_stp:
      state: present
      stp_mode: stp
      provider: "{{ cli }}"

  - name: "Undo stp mode"
    ce_stp:
      state: absent
      stp_mode: stp
      provider: "{{ cli }}"

  - name: "Enable bpdu protection"
    ce_stp:
      state: present
      bpdu_protection: enable
      provider: "{{ cli }}"

  - name: "Disable bpdu protection"
    ce_stp:
      state: present
      bpdu_protection: disable
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"bpdu_protection": "enable",
             "state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"bpdu_protection": "disable"}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bpdu_protection": "enable"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["stp bpdu-protection"]
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_config, load_config, ce_argument_spec


class Stp(object):
    """ Manages stp/rstp/mstp configuration """

    def __init__(self, **kwargs):
        """ Stp module init """

        # module
        argument_spec = kwargs["argument_spec"]
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)

        # config
        self.cur_cfg = dict()
        self.stp_cfg = None
        self.interface_stp_cfg = None

        # module args
        self.state = self.module.params['state'] or None
        self.stp_mode = self.module.params['stp_mode'] or None
        self.stp_enable = self.module.params['stp_enable'] or None
        self.stp_converge = self.module.params['stp_converge'] or None
        self.interface = self.module.params['interface'] or None
        self.edged_port = self.module.params['edged_port'] or None
        self.bpdu_filter = self.module.params['bpdu_filter'] or None
        self.cost = self.module.params['cost'] or None
        self.bpdu_protection = self.module.params['bpdu_protection'] or None
        self.tc_protection = self.module.params['tc_protection'] or None
        self.tc_protection_interval = self.module.params['tc_protection_interval'] or None
        self.tc_protection_threshold = self.module.params['tc_protection_threshold'] or None
        self.root_protection = self.module.params['root_protection'] or None
        self.loop_protection = self.module.params['loop_protection'] or None

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def cli_load_config(self, commands):
        """ Cli load configuration """

        if not self.module.check_mode:
            load_config(self.module, commands)

    def cli_get_stp_config(self):
        """ Cli get stp configuration """

        regular = "| include stp"

        flags = list()
        flags.append(regular)
        self.stp_cfg = get_config(self.module, flags)

    def cli_get_interface_stp_config(self):
        """ Cli get interface's stp configuration """

        if self.interface:
            regular = "| ignore-case section include ^interface %s$" % self.interface
            flags = list()
            flags.append(regular)
            tmp_cfg = get_config(self.module, flags)

            if not tmp_cfg:
                self.module.fail_json(
                    msg='Error: The interface %s is not exist.' % self.interface)

            if "undo portswitch" in tmp_cfg:
                self.module.fail_json(
                    msg='Error: The interface %s is not switch mode.' % self.interface)

            self.interface_stp_cfg = tmp_cfg

    def check_params(self):
        """ Check module params """

        if self.cost:
            if self.cost.isdigit():
                if int(self.cost) < 1 or int(self.cost) > 200000000:
                    self.module.fail_json(
                        msg='Error: The value of cost is out of [1 - 200000000].')
            else:
                self.module.fail_json(
                    msg='Error: The cost is not digit.')

        if self.tc_protection_interval:
            if self.tc_protection_interval.isdigit():
                if int(self.tc_protection_interval) < 1 or int(self.tc_protection_interval) > 600:
                    self.module.fail_json(
                        msg='Error: The value of tc_protection_interval is out of [1 - 600].')
            else:
                self.module.fail_json(
                    msg='Error: The tc_protection_interval is not digit.')

        if self.tc_protection_threshold:
            if self.tc_protection_threshold.isdigit():
                if int(self.tc_protection_threshold) < 1 or int(self.tc_protection_threshold) > 255:
                    self.module.fail_json(
                        msg='Error: The value of tc_protection_threshold is out of [1 - 255].')
            else:
                self.module.fail_json(
                    msg='Error: The tc_protection_threshold is not digit.')

        if self.root_protection or self.loop_protection or self.cost:
            if not self.interface:
                self.module.fail_json(
                    msg='Error: Please input interface.')
            elif self.interface == "all":
                self.module.fail_json(
                    msg='Error: Interface can not be all when config root_protection or loop_protection or cost.')

        if self.root_protection and self.root_protection == "enable":
            if self.loop_protection and self.loop_protection == "enable":
                self.module.fail_json(
                    msg='Error: Can not enable root_protection and loop_protection at the same interface.')

        if self.edged_port or self.bpdu_filter:
            if not self.interface:
                self.module.fail_json(
                    msg='Error: Please input interface.')

    def get_proposed(self):
        """ Get module proposed """

        self.proposed["state"] = self.state

        if self.stp_mode:
            self.proposed["stp_mode"] = self.stp_mode
        if self.stp_enable:
            self.proposed["stp_enable"] = self.stp_enable
        if self.stp_converge:
            self.proposed["stp_converge"] = self.stp_converge
        if self.interface:
            self.proposed["interface"] = self.interface
        if self.edged_port:
            self.proposed["edged_port"] = self.edged_port
        if self.bpdu_filter:
            self.proposed["bpdu_filter"] = self.bpdu_filter
        if self.cost:
            self.proposed["cost"] = self.cost
        if self.bpdu_protection:
            self.proposed["bpdu_protection"] = self.bpdu_protection
        if self.tc_protection:
            self.proposed["tc_protection"] = self.tc_protection
        if self.tc_protection_interval:
            self.proposed["tc_protection_interval"] = self.tc_protection_interval
        if self.tc_protection_threshold:
            self.proposed["tc_protection_threshold"] = self.tc_protection_threshold
        if self.root_protection:
            self.proposed["root_protection"] = self.root_protection
        if self.loop_protection:
            self.proposed["loop_protection"] = self.loop_protection

    def get_existing(self):
        """ Get existing configuration """

        self.cli_get_stp_config()
        if self.interface and self.interface != "all":
            self.cli_get_interface_stp_config()

        if self.stp_mode:
            if "stp mode stp" in self.stp_cfg:
                self.cur_cfg["stp_mode"] = "stp"
                self.existing["stp_mode"] = "stp"
            elif "stp mode rstp" in self.stp_cfg:
                self.cur_cfg["stp_mode"] = "rstp"
                self.existing["stp_mode"] = "rstp"
            else:
                self.cur_cfg["stp_mode"] = "mstp"
                self.existing["stp_mode"] = "mstp"

        if self.stp_enable:
            if "stp disable" in self.stp_cfg:
                self.cur_cfg["stp_enable"] = "disable"
                self.existing["stp_enable"] = "disable"
            else:
                self.cur_cfg["stp_enable"] = "enable"
                self.existing["stp_enable"] = "enable"

        if self.stp_converge:
            if "stp converge fast" in self.stp_cfg:
                self.cur_cfg["stp_converge"] = "fast"
                self.existing["stp_converge"] = "fast"
            else:
                self.cur_cfg["stp_converge"] = "normal"
                self.existing["stp_converge"] = "normal"

        if self.edged_port:
            if self.interface == "all":
                if "stp edged-port default" in self.stp_cfg:
                    self.cur_cfg["edged_port"] = "enable"
                    self.existing["edged_port"] = "enable"
                else:
                    self.cur_cfg["edged_port"] = "disable"
                    self.existing["edged_port"] = "disable"
            else:
                if "stp edged-port enable" in self.interface_stp_cfg:
                    self.cur_cfg["edged_port"] = "enable"
                    self.existing["edged_port"] = "enable"
                else:
                    self.cur_cfg["edged_port"] = "disable"
                    self.existing["edged_port"] = "disable"

        if self.bpdu_filter:
            if self.interface == "all":
                if "stp bpdu-filter default" in self.stp_cfg:
                    self.cur_cfg["bpdu_filter"] = "enable"
                    self.existing["bpdu_filter"] = "enable"
                else:
                    self.cur_cfg["bpdu_filter"] = "disable"
                    self.existing["bpdu_filter"] = "disable"
            else:
                if "stp bpdu-filter enable" in self.interface_stp_cfg:
                    self.cur_cfg["bpdu_filter"] = "enable"
                    self.existing["bpdu_filter"] = "enable"
                else:
                    self.cur_cfg["bpdu_filter"] = "disable"
                    self.existing["bpdu_filter"] = "disable"

        if self.bpdu_protection:
            if "stp bpdu-protection" in self.stp_cfg:
                self.cur_cfg["bpdu_protection"] = "enable"
                self.existing["bpdu_protection"] = "enable"
            else:
                self.cur_cfg["bpdu_protection"] = "disable"
                self.existing["bpdu_protection"] = "disable"

        if self.tc_protection:
            if "stp tc-protection" in self.stp_cfg:
                self.cur_cfg["tc_protection"] = "enable"
                self.existing["tc_protection"] = "enable"
            else:
                self.cur_cfg["tc_protection"] = "disable"
                self.existing["tc_protection"] = "disable"

        if self.tc_protection_interval:
            if "stp tc-protection interval" in self.stp_cfg:
                tmp_value = re.findall(r'stp tc-protection interval (.*)', self.stp_cfg)
                if not tmp_value:
                    self.module.fail_json(
                        msg='Error: Can not find tc-protection interval on the device.')
                self.cur_cfg["tc_protection_interval"] = tmp_value[0]
                self.existing["tc_protection_interval"] = tmp_value[0]
            else:
                self.cur_cfg["tc_protection_interval"] = "null"
                self.existing["tc_protection_interval"] = "null"

        if self.tc_protection_threshold:
            if "stp tc-protection threshold" in self.stp_cfg:
                tmp_value = re.findall(r'stp tc-protection threshold (.*)', self.stp_cfg)
                if not tmp_value:
                    self.module.fail_json(
                        msg='Error: Can not find tc-protection threshold on the device.')
                self.cur_cfg["tc_protection_threshold"] = tmp_value[0]
                self.existing["tc_protection_threshold"] = tmp_value[0]
            else:
                self.cur_cfg["tc_protection_threshold"] = "1"
                self.existing["tc_protection_threshold"] = "1"

        if self.cost:
            tmp_value = re.findall(r'stp instance (.*) cost (.*)', self.interface_stp_cfg)
            if not tmp_value:
                self.cur_cfg["cost"] = "null"
                self.existing["cost"] = "null"
            else:
                self.cur_cfg["cost"] = tmp_value[0][1]
                self.existing["cost"] = tmp_value[0][1]

        # root_protection and loop_protection should get configuration at the same time
        if self.root_protection or self.loop_protection:
            if "stp root-protection" in self.interface_stp_cfg:
                self.cur_cfg["root_protection"] = "enable"
                self.existing["root_protection"] = "enable"
            else:
                self.cur_cfg["root_protection"] = "disable"
                self.existing["root_protection"] = "disable"

            if "stp loop-protection" in self.interface_stp_cfg:
                self.cur_cfg["loop_protection"] = "enable"
                self.existing["loop_protection"] = "enable"
            else:
                self.cur_cfg["loop_protection"] = "disable"
                self.existing["loop_protection"] = "disable"

    def get_end_state(self):
        """ Get end state """

        self.cli_get_stp_config()
        if self.interface and self.interface != "all":
            self.cli_get_interface_stp_config()

        if self.stp_mode:
            if "stp mode stp" in self.stp_cfg:
                self.end_state["stp_mode"] = "stp"
            elif "stp mode rstp" in self.stp_cfg:
                self.end_state["stp_mode"] = "rstp"
            else:
                self.end_state["stp_mode"] = "mstp"

        if self.stp_enable:
            if "stp disable" in self.stp_cfg:
                self.end_state["stp_enable"] = "disable"
            else:
                self.end_state["stp_enable"] = "enable"

        if self.stp_converge:
            if "stp converge fast" in self.stp_cfg:
                self.end_state["stp_converge"] = "fast"
            else:
                self.end_state["stp_converge"] = "normal"

        if self.edged_port:
            if self.interface == "all":
                if "stp edged-port default" in self.stp_cfg:
                    self.end_state["edged_port"] = "enable"
                else:
                    self.end_state["edged_port"] = "disable"
            else:
                if "stp edged-port enable" in self.interface_stp_cfg:
                    self.end_state["edged_port"] = "enable"
                else:
                    self.end_state["edged_port"] = "disable"

        if self.bpdu_filter:
            if self.interface == "all":
                if "stp bpdu-filter default" in self.stp_cfg:
                    self.end_state["bpdu_filter"] = "enable"
                else:
                    self.end_state["bpdu_filter"] = "disable"
            else:
                if "stp bpdu-filter enable" in self.interface_stp_cfg:
                    self.end_state["bpdu_filter"] = "enable"
                else:
                    self.end_state["bpdu_filter"] = "disable"

        if self.bpdu_protection:
            if "stp bpdu-protection" in self.stp_cfg:
                self.end_state["bpdu_protection"] = "enable"
            else:
                self.end_state["bpdu_protection"] = "disable"

        if self.tc_protection:
            if "stp tc-protection" in self.stp_cfg:
                self.end_state["tc_protection"] = "enable"
            else:
                self.end_state["tc_protection"] = "disable"

        if self.tc_protection_interval:
            if "stp tc-protection interval" in self.stp_cfg:
                tmp_value = re.findall(r'stp tc-protection interval (.*)', self.stp_cfg)
                if not tmp_value:
                    self.module.fail_json(
                        msg='Error: Can not find tc-protection interval on the device.')
                self.end_state["tc_protection_interval"] = tmp_value[0]
            else:
                self.end_state["tc_protection_interval"] = "null"

        if self.tc_protection_threshold:
            if "stp tc-protection threshold" in self.stp_cfg:
                tmp_value = re.findall(r'stp tc-protection threshold (.*)', self.stp_cfg)
                if not tmp_value:
                    self.module.fail_json(
                        msg='Error: Can not find tc-protection threshold on the device.')
                self.end_state["tc_protection_threshold"] = tmp_value[0]
            else:
                self.end_state["tc_protection_threshold"] = "1"

        if self.cost:
            tmp_value = re.findall(r'stp instance (.*) cost (.*)', self.interface_stp_cfg)
            if not tmp_value:
                self.end_state["cost"] = "null"
            else:
                self.end_state["cost"] = tmp_value[0][1]

        if self.root_protection:
            if "stp root-protection" in self.interface_stp_cfg:
                self.end_state["root_protection"] = "enable"
            else:
                self.end_state["root_protection"] = "disable"

        if self.loop_protection:
            if "stp loop-protection" in self.interface_stp_cfg:
                self.end_state["loop_protection"] = "enable"
            else:
                self.end_state["loop_protection"] = "disable"

    def present_stp(self):
        """ Present stp configuration """

        cmds = list()

        # cofig stp global
        if self.stp_mode:
            if self.stp_mode != self.cur_cfg["stp_mode"]:
                cmd = "stp mode %s" % self.stp_mode
                cmds.append(cmd)
                self.updates_cmd.append(cmd)

        if self.stp_enable:
            if self.stp_enable != self.cur_cfg["stp_enable"]:
                cmd = "stp %s" % self.stp_enable
                cmds.append(cmd)
                self.updates_cmd.append(cmd)

        if self.stp_converge:
            if self.stp_converge != self.cur_cfg["stp_converge"]:
                cmd = "stp converge %s" % self.stp_converge
                cmds.append(cmd)
                self.updates_cmd.append(cmd)

        if self.edged_port:
            if self.interface == "all":
                if self.edged_port != self.cur_cfg["edged_port"]:
                    if self.edged_port == "enable":
                        cmd = "stp edged-port default"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                    else:
                        cmd = "undo stp edged-port default"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)

        if self.bpdu_filter:
            if self.interface == "all":
                if self.bpdu_filter != self.cur_cfg["bpdu_filter"]:
                    if self.bpdu_filter == "enable":
                        cmd = "stp bpdu-filter default"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                    else:
                        cmd = "undo stp bpdu-filter default"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)

        if self.bpdu_protection:
            if self.bpdu_protection != self.cur_cfg["bpdu_protection"]:
                if self.bpdu_protection == "enable":
                    cmd = "stp bpdu-protection"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)
                else:
                    cmd = "undo stp bpdu-protection"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)

        if self.tc_protection:
            if self.tc_protection != self.cur_cfg["tc_protection"]:
                if self.tc_protection == "enable":
                    cmd = "stp tc-protection"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)
                else:
                    cmd = "undo stp tc-protection"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)

        if self.tc_protection_interval:
            if self.tc_protection_interval != self.cur_cfg["tc_protection_interval"]:
                cmd = "stp tc-protection interval %s" % self.tc_protection_interval
                cmds.append(cmd)
                self.updates_cmd.append(cmd)

        if self.tc_protection_threshold:
            if self.tc_protection_threshold != self.cur_cfg["tc_protection_threshold"]:
                cmd = "stp tc-protection threshold %s" % self.tc_protection_threshold
                cmds.append(cmd)
                self.updates_cmd.append(cmd)

        # config interface stp
        if self.interface and self.interface != "all":
            tmp_changed = False

            cmd = "interface %s" % self.interface
            cmds.append(cmd)
            self.updates_cmd.append(cmd)

            if self.edged_port:
                if self.edged_port != self.cur_cfg["edged_port"]:
                    if self.edged_port == "enable":
                        cmd = "stp edged-port enable"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True
                    else:
                        cmd = "undo stp edged-port"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True

            if self.bpdu_filter:
                if self.bpdu_filter != self.cur_cfg["bpdu_filter"]:
                    if self.bpdu_filter == "enable":
                        cmd = "stp bpdu-filter enable"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True
                    else:
                        cmd = "undo stp bpdu-filter"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True

            if self.root_protection:
                if self.root_protection == "enable" and self.cur_cfg["loop_protection"] == "enable":
                    self.module.fail_json(
                        msg='Error: The interface has enable loop_protection, can not enable root_protection.')
                if self.root_protection != self.cur_cfg["root_protection"]:
                    if self.root_protection == "enable":
                        cmd = "stp root-protection"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True
                    else:
                        cmd = "undo stp root-protection"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True

            if self.loop_protection:
                if self.loop_protection == "enable" and self.cur_cfg["root_protection"] == "enable":
                    self.module.fail_json(
                        msg='Error: The interface has enable root_protection, can not enable loop_protection.')
                if self.loop_protection != self.cur_cfg["loop_protection"]:
                    if self.loop_protection == "enable":
                        cmd = "stp loop-protection"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True
                    else:
                        cmd = "undo stp loop-protection"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True

            if self.cost:
                if self.cost != self.cur_cfg["cost"]:
                    cmd = "stp cost %s" % self.cost
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)
                    tmp_changed = True

            if not tmp_changed:
                cmd = "interface %s" % self.interface
                self.updates_cmd.remove(cmd)
                cmds.remove(cmd)

        if cmds:
            self.cli_load_config(cmds)
            self.changed = True

    def absent_stp(self):
        """ Absent stp configuration """

        cmds = list()

        if self.stp_mode:
            if self.stp_mode == self.cur_cfg["stp_mode"]:
                if self.stp_mode != "mstp":
                    cmd = "undo stp mode"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)
                    self.changed = True

        if self.stp_enable:
            if self.stp_enable != self.cur_cfg["stp_enable"]:
                cmd = "stp %s" % self.stp_enable
                cmds.append(cmd)
                self.updates_cmd.append(cmd)

        if self.stp_converge:
            if self.stp_converge == self.cur_cfg["stp_converge"]:
                cmd = "undo stp converge"
                cmds.append(cmd)
                self.updates_cmd.append(cmd)
                self.changed = True

        if self.edged_port:
            if self.interface == "all":
                if self.edged_port != self.cur_cfg["edged_port"]:
                    if self.edged_port == "enable":
                        cmd = "stp edged-port default"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                    else:
                        cmd = "undo stp edged-port default"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)

        if self.bpdu_filter:
            if self.interface == "all":
                if self.bpdu_filter != self.cur_cfg["bpdu_filter"]:
                    if self.bpdu_filter == "enable":
                        cmd = "stp bpdu-filter default"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                    else:
                        cmd = "undo stp bpdu-filter default"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)

        if self.bpdu_protection:
            if self.bpdu_protection != self.cur_cfg["bpdu_protection"]:
                if self.bpdu_protection == "enable":
                    cmd = "stp bpdu-protection"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)
                else:
                    cmd = "undo stp bpdu-protection"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)

        if self.tc_protection:
            if self.tc_protection != self.cur_cfg["tc_protection"]:
                if self.tc_protection == "enable":
                    cmd = "stp tc-protection"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)
                else:
                    cmd = "undo stp tc-protection"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)

        if self.tc_protection_interval:
            if self.tc_protection_interval == self.cur_cfg["tc_protection_interval"]:
                cmd = "undo stp tc-protection interval"
                cmds.append(cmd)
                self.updates_cmd.append(cmd)
                self.changed = True

        if self.tc_protection_threshold:
            if self.tc_protection_threshold == self.cur_cfg["tc_protection_threshold"]:
                if self.tc_protection_threshold != "1":
                    cmd = "undo stp tc-protection threshold"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)
                    self.changed = True

        # undo interface stp
        if self.interface and self.interface != "all":
            tmp_changed = False

            cmd = "interface %s" % self.interface
            cmds.append(cmd)
            self.updates_cmd.append(cmd)

            if self.edged_port:
                if self.edged_port != self.cur_cfg["edged_port"]:
                    if self.edged_port == "enable":
                        cmd = "stp edged-port enable"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True
                    else:
                        cmd = "undo stp edged-port"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True

            if self.bpdu_filter:
                if self.bpdu_filter != self.cur_cfg["bpdu_filter"]:
                    if self.bpdu_filter == "enable":
                        cmd = "stp bpdu-filter enable"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True
                    else:
                        cmd = "undo stp bpdu-filter"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True

            if self.root_protection:
                if self.root_protection == "enable" and self.cur_cfg["loop_protection"] == "enable":
                    self.module.fail_json(
                        msg='Error: The interface has enable loop_protection, can not enable root_protection.')
                if self.root_protection != self.cur_cfg["root_protection"]:
                    if self.root_protection == "enable":
                        cmd = "stp root-protection"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True
                    else:
                        cmd = "undo stp root-protection"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True

            if self.loop_protection:
                if self.loop_protection == "enable" and self.cur_cfg["root_protection"] == "enable":
                    self.module.fail_json(
                        msg='Error: The interface has enable root_protection, can not enable loop_protection.')
                if self.loop_protection != self.cur_cfg["loop_protection"]:
                    if self.loop_protection == "enable":
                        cmd = "stp loop-protection"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True
                    else:
                        cmd = "undo stp loop-protection"
                        cmds.append(cmd)
                        self.updates_cmd.append(cmd)
                        tmp_changed = True

            if self.cost:
                if self.cost == self.cur_cfg["cost"]:
                    cmd = "undo stp cost"
                    cmds.append(cmd)
                    self.updates_cmd.append(cmd)
                    tmp_changed = True

            if not tmp_changed:
                cmd = "interface %s" % self.interface
                self.updates_cmd.remove(cmd)
                cmds.remove(cmd)

        if cmds:
            self.cli_load_config(cmds)
            self.changed = True

    def work(self):
        """ Work function """

        self.check_params()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            self.present_stp()
        else:
            self.absent_stp()

        self.get_end_state()

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        self.results['updates'] = self.updates_cmd

        self.module.exit_json(**self.results)


def main():
    """ Module main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        stp_mode=dict(choices=['stp', 'rstp', 'mstp']),
        stp_enable=dict(choices=['enable', 'disable']),
        stp_converge=dict(choices=['fast', 'normal']),
        bpdu_protection=dict(choices=['enable', 'disable']),
        tc_protection=dict(choices=['enable', 'disable']),
        tc_protection_interval=dict(type='str'),
        tc_protection_threshold=dict(type='str'),
        interface=dict(type='str'),
        edged_port=dict(choices=['enable', 'disable']),
        bpdu_filter=dict(choices=['enable', 'disable']),
        cost=dict(type='str'),
        root_protection=dict(choices=['enable', 'disable']),
        loop_protection=dict(choices=['enable', 'disable'])
    )

    argument_spec.update(ce_argument_spec)
    module = Stp(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
