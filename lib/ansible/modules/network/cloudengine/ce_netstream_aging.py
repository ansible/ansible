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
module: ce_netstream_aging
version_added: "2.4"
short_description: Manages timeout mode of NetStream on HUAWEI CloudEngine switches.
description:
    - Manages timeout mode of NetStream on HUAWEI CloudEngine switches.
author: YangYang (@QijunPan)
notes:
    - Recommended connection is C(network_cli).
    - This module also works with C(local) connections for legacy playbooks.
options:
    timeout_interval:
        description:
            - Netstream timeout interval.
              If is active type the interval is 1-60.
              If is inactive ,the interval is 5-600.
        default: 30
    type:
        description:
            - Specifies the packet type of netstream timeout active interval.
        choices: ['ip', 'vxlan']
    state:
        description:
            - Specify desired state of the resource.
        choices: ['present', 'absent']
        default: present
    timeout_type:
        description:
            - Netstream timeout type.
        choices: ['active', 'inactive', 'tcp-session', 'manual']
    manual_slot:
        description:
            -  Specifies the slot number of netstream manual timeout.
"""

EXAMPLES = '''
- name: netstream aging module test
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

  - name: Configure netstream ip timeout active interval , the interval is 40 minutes.
    ce_netstream_aging:
      timeout_interval: 40
      type: ip
      timeout_type: active
      state: present
      provider: "{{ cli }}"

  - name: Configure netstream vxlan timeout active interval , the interval is 40 minutes.
    ce_netstream_aging:
      timeout_interval: 40
      type: vxlan
      timeout_type: active
      active_state: present
      provider: "{{ cli }}"

  - name: Delete netstream ip timeout active interval , set the ip timeout interval to 30 minutes.
    ce_netstream_aging:
      type: ip
      timeout_type: active
      state: absent
      provider: "{{ cli }}"

  - name: Delete netstream vxlan timeout active interval , set the vxlan timeout interval to 30 minutes.
    ce_netstream_aging:
      type: vxlan
      timeout_type: active
      state: absent
      provider: "{{ cli }}"

  - name: Enable netstream ip tcp session timeout.
    ce_netstream_aging:
      type: ip
      timeout_type: tcp-session
      state: present
      provider: "{{ cli }}"

  - name: Enable netstream vxlan tcp session timeout.
    ce_netstream_aging:
      type: vxlan
      timeout_type: tcp-session
      state: present
      provider: "{{ cli }}"

  - name: Disable netstream ip tcp session timeout.
    ce_netstream_aging:
      type: ip
      timeout_type: tcp-session
      state: absent
      provider: "{{ cli }}"

  - name: Disable netstream vxlan tcp session timeout.
    ce_netstream_aging:
      type: vxlan
      timeout_type: tcp-session
      state: absent
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"timeout_interval": "40",
             "type": "ip",
             "state": "absent",
             "timeout_type": active}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"active_timeout": [
            {
                "ip": "40",
                "vxlan": 30
            }
        ],
        "inactive_timeout": [
            {
                "ip": 30,
                "vxlan": 30
            }
        ],
        "tcp_timeout": [
            {
                "ip": "disable",
                "vxlan": "disable"
            }
        ]}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"active_timeout": [
            {
                "ip": 30,
                "vxlan": 30
            }
        ],
        "inactive_timeout": [
            {
                "ip": 30,
                "vxlan": 30
            }
        ],
        "tcp_timeout": [
            {
                "ip": "disable",
                "vxlan": "disable"
            }
        ]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["undo netstream timeout ip active 40"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import exec_command, load_config
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec


class NetStreamAging(object):
    """
    Manages netstream aging.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.timeout_interval = self.module.params['timeout_interval']
        self.type = self.module.params['type']
        self.state = self.module.params['state']
        self.timeout_type = self.module.params['timeout_type']
        self.manual_slot = self.module.params['manual_slot']

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
        self.existing["active_timeout"] = list()
        self.existing["inactive_timeout"] = list()
        self.existing["tcp_timeout"] = list()
        self.end_state["active_timeout"] = list()
        self.end_state["inactive_timeout"] = list()
        self.end_state["tcp_timeout"] = list()
        self.active_changed = False
        self.inactive_changed = False
        self.tcp_changed = False

    def init_module(self):
        """init module"""

        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)

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

    def get_exist_timer_out_para(self):
        """Get exist netstream timeout parameters"""

        active_tmp = dict()
        inactive_tmp = dict()
        tcp_tmp = dict()
        active_tmp["ip"] = "30"
        active_tmp["vxlan"] = "30"
        inactive_tmp["ip"] = "30"
        inactive_tmp["vxlan"] = "30"
        tcp_tmp["ip"] = "absent"
        tcp_tmp["vxlan"] = "absent"

        cmd = "display current-configuration | include ^netstream timeout"
        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            self.module.fail_json(msg=err)
        config = str(out).strip()
        if config:
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem = config_mem.lstrip()
                config_mem_list = config_mem.split(' ')
                if len(config_mem_list) > 4 and config_mem_list[2] == "ip":
                    if config_mem_list[3] == "active":
                        active_tmp["ip"] = config_mem_list[4]
                    if config_mem_list[3] == "inactive":
                        inactive_tmp["ip"] = config_mem_list[4]
                    if config_mem_list[3] == "tcp-session":
                        tcp_tmp["ip"] = "present"
                if len(config_mem_list) > 4 and config_mem_list[2] == "vxlan":
                    if config_mem_list[4] == "active":
                        active_tmp["vxlan"] = config_mem_list[5]
                    if config_mem_list[4] == "inactive":
                        inactive_tmp["vxlan"] = config_mem_list[5]
                    if config_mem_list[4] == "tcp-session":
                        tcp_tmp["vxlan"] = "present"
        self.existing["active_timeout"].append(active_tmp)
        self.existing["inactive_timeout"].append(inactive_tmp)
        self.existing["tcp_timeout"].append(tcp_tmp)

    def get_end_timer_out_para(self):
        """Get end netstream timeout parameters"""

        active_tmp = dict()
        inactive_tmp = dict()
        tcp_tmp = dict()
        active_tmp["ip"] = "30"
        active_tmp["vxlan"] = "30"
        inactive_tmp["ip"] = "30"
        inactive_tmp["vxlan"] = "30"
        tcp_tmp["ip"] = "absent"
        tcp_tmp["vxlan"] = "absent"
        cmd = "display current-configuration | include ^netstream timeout"
        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            self.module.fail_json(msg=err)
        config = str(out).strip()
        if config:
            config = config.lstrip()
            config_list = config.split('\n')
            for config_mem in config_list:
                config_mem = config_mem.lstrip()
                config_mem_list = config_mem.split(' ')
                if len(config_mem_list) > 4 and config_mem_list[2] == "ip":
                    if config_mem_list[3] == "active":
                        active_tmp["ip"] = config_mem_list[4]
                    if config_mem_list[3] == "inactive":
                        inactive_tmp["ip"] = config_mem_list[4]
                    if config_mem_list[3] == "tcp-session":
                        tcp_tmp["ip"] = "present"
                if len(config_mem_list) > 4 and config_mem_list[2] == "vxlan":
                    if config_mem_list[4] == "active":
                        active_tmp["vxlan"] = config_mem_list[5]
                    if config_mem_list[4] == "inactive":
                        inactive_tmp["vxlan"] = config_mem_list[5]
                    if config_mem_list[4] == "tcp-session":
                        tcp_tmp["vxlan"] = "present"
        self.end_state["active_timeout"].append(active_tmp)
        self.end_state["inactive_timeout"].append(inactive_tmp)
        self.end_state["tcp_timeout"].append(tcp_tmp)

    def check_params(self):
        """Check all input params"""

        # interval check
        if not str(self.timeout_interval).isdigit():
            self.module.fail_json(
                msg='Error: Timeout interval should be numerical.')
        if self.timeout_type == "active":
            if int(self.timeout_interval) < 1 or int(self.timeout_interval) > 60:
                self.module.fail_json(
                    msg="Error: Active interval should between 1 - 60 minutes.")
        if self.timeout_type == "inactive":
            if int(self.timeout_interval) < 5 or int(self.timeout_interval) > 600:
                self.module.fail_json(
                    msg="Error: Inactive interval should between 5 - 600 seconds.")
        if self.timeout_type == "manual":
            if not self.manual_slot:
                self.module.fail_json(
                    msg="Error: If use manual timeout mode,slot number is needed.")
            if re.match(r'^\d+(\/\d*)?$', self.manual_slot) is None:
                self.module.fail_json(
                    msg='Error: Slot number should be numerical.')

    def get_proposed(self):
        """get proposed info"""

        if self.timeout_interval:
            self.proposed["timeout_interval"] = self.timeout_interval
        if self.timeout_type:
            self.proposed["timeout_type"] = self.timeout_type
        if self.type:
            self.proposed["type"] = self.type
        if self.state:
            self.proposed["state"] = self.state
        if self.manual_slot:
            self.proposed["manual_slot"] = self.manual_slot

    def get_existing(self):
        """get existing info"""
        active_tmp = dict()
        inactive_tmp = dict()
        tcp_tmp = dict()

        self.get_exist_timer_out_para()

        if self.timeout_type == "active":
            for active_tmp in self.existing["active_timeout"]:
                if self.state == "present":
                    if str(active_tmp[self.type]) != self.timeout_interval:
                        self.active_changed = True
                else:
                    if self.timeout_interval != "30":
                        if str(active_tmp[self.type]) != "30":
                            if str(active_tmp[self.type]) != self.timeout_interval:
                                self.module.fail_json(
                                    msg='Error: The specified active interval do not exist.')
                    if str(active_tmp[self.type]) != "30":
                        self.timeout_interval = active_tmp[self.type]
                        self.active_changed = True
        if self.timeout_type == "inactive":
            for inactive_tmp in self.existing["inactive_timeout"]:
                if self.state == "present":
                    if str(inactive_tmp[self.type]) != self.timeout_interval:
                        self.inactive_changed = True
                else:
                    if self.timeout_interval != "30":
                        if str(inactive_tmp[self.type]) != "30":
                            if str(inactive_tmp[self.type]) != self.timeout_interval:
                                self.module.fail_json(
                                    msg='Error: The specified inactive interval do not exist.')
                    if str(inactive_tmp[self.type]) != "30":
                        self.timeout_interval = inactive_tmp[self.type]
                        self.inactive_changed = True
        if self.timeout_type == "tcp-session":
            for tcp_tmp in self.existing["tcp_timeout"]:
                if str(tcp_tmp[self.type]) != self.state:
                    self.tcp_changed = True

    def operate_time_out(self):
        """configure timeout parameters"""

        cmd = ""
        if self.timeout_type == "manual":
            if self.type == "ip":
                self.cli_add_command("quit")
                cmd = "reset netstream cache ip slot %s" % self.manual_slot
                self.cli_add_command(cmd)
            elif self.type == "vxlan":
                self.cli_add_command("quit")
                cmd = "reset netstream cache vxlan inner-ip slot %s" % self.manual_slot
                self.cli_add_command(cmd)

        if not self.active_changed and not self.inactive_changed and not self.tcp_changed:
            if self.commands:
                self.cli_load_config(self.commands)
                self.changed = True
            return

        if self.active_changed or self.inactive_changed:
            if self.type == "ip":
                cmd = "netstream timeout ip %s %s" % (self.timeout_type, self.timeout_interval)
            elif self.type == "vxlan":
                cmd = "netstream timeout vxlan inner-ip %s %s" % (self.timeout_type, self.timeout_interval)
            if self.state == "absent":
                self.cli_add_command(cmd, undo=True)
            else:
                self.cli_add_command(cmd)
        if self.timeout_type == "tcp-session" and self.tcp_changed:
            if self.type == "ip":
                if self.state == "present":
                    cmd = "netstream timeout ip tcp-session"
                else:
                    cmd = "undo netstream timeout ip tcp-session"

            elif self.type == "vxlan":
                if self.state == "present":
                    cmd = "netstream timeout vxlan inner-ip tcp-session"
                else:
                    cmd = "undo netstream timeout vxlan inner-ip tcp-session"
            self.cli_add_command(cmd)
        if self.commands:
            self.cli_load_config(self.commands)
            self.changed = True

    def get_end_state(self):
        """get end state info"""

        self.get_end_timer_out_para()

    def work(self):
        """worker"""

        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.operate_time_out()
        self.get_end_state()
        if self.existing == self.end_state:
            self.changed = False
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
        timeout_interval=dict(required=False, type='str', default='30'),
        type=dict(required=False, choices=['ip', 'vxlan']),
        state=dict(required=False, choices=['present', 'absent'], default='present'),
        timeout_type=dict(required=False, choices=['active', 'inactive', 'tcp-session', 'manual']),
        manual_slot=dict(required=False, type='str'),
    )
    argument_spec.update(ce_argument_spec)
    module = NetStreamAging(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
