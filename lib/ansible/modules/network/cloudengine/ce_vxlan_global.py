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
module: ce_vxlan_global
version_added: "2.4"
short_description: Manages global attributes of VXLAN and bridge domain on HUAWEI CloudEngine devices.
description:
    - Manages global attributes of VXLAN and bridge domain on HUAWEI CloudEngine devices.
author: QijunPan (@QijunPan)
notes:
    - Recommended connection is C(network_cli).
    - This module also works with C(local) connections for legacy playbooks.
options:
    bridge_domain_id:
        description:
            - Specifies a bridge domain ID.
              The value is an integer ranging from 1 to 16777215.
    tunnel_mode_vxlan:
        description:
            - Set the tunnel mode to VXLAN when configuring the VXLAN feature.
        choices: ['enable', 'disable']
    nvo3_prevent_loops:
        description:
            - Loop prevention of VXLAN traffic in non-enhanced mode.
              When the device works in non-enhanced mode,
              inter-card forwarding of VXLAN traffic may result in loops.
        choices: ['enable', 'disable']
    nvo3_acl_extend:
        description:
            - Enabling or disabling the VXLAN ACL extension function.
        choices: ['enable', 'disable']
    nvo3_gw_enhanced:
        description:
            - Configuring the Layer 3 VXLAN Gateway to Work in Non-loopback Mode.
        choices: ['l2', 'l3']
    nvo3_service_extend:
        description:
            - Enabling or disabling the VXLAN service extension function.
        choices: ['enable', 'disable']
    nvo3_eth_trunk_hash:
        description:
            - Eth-Trunk from load balancing VXLAN packets in optimized mode.
        choices: ['enable','disable']
    nvo3_ecmp_hash:
        description:
            - Load balancing of VXLAN packets through ECMP in optimized mode.
        choices: ['enable', 'disable']
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        default: present
        choices: ['present', 'absent']
"""

EXAMPLES = '''
- name: vxlan global module test
  hosts: ce128
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

  - name: Create bridge domain and set tunnel mode to VXLAN
    ce_vxlan_global:
      bridge_domain_id: 100
      nvo3_acl_extend: enable
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"bridge_domain_id": "100", "nvo3_acl_extend": "enable", state="present"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"bridge_domain": {"80", "90"}, "nvo3_acl_extend": "disable"}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"bridge_domain_id": {"80", "90", "100"}, "nvo3_acl_extend": "enable"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["bridge-domain 100",
             "ip tunnel mode vxlan"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import load_config
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec
from ansible.module_utils.connection import exec_command


def is_config_exist(cmp_cfg, test_cfg):
    """is configuration exist?"""

    if not cmp_cfg or not test_cfg:
        return False

    return bool(test_cfg in cmp_cfg)


def get_nvo3_gw_enhanced(cmp_cfg):
    """get the Layer 3 VXLAN Gateway to Work in Non-loopback Mode """

    get = re.findall(
        r"assign forward nvo3-gateway enhanced (l[2|3])", cmp_cfg)
    if not get:
        return None
    else:
        return get[0]


class VxlanGlobal(object):
    """
    Manages global attributes of VXLAN and bridge domain.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.tunnel_mode_vxlan = self.module.params['tunnel_mode_vxlan']
        self.nvo3_prevent_loops = self.module.params['nvo3_prevent_loops']
        self.nvo3_acl_extend = self.module.params['nvo3_acl_extend']
        self.nvo3_gw_enhanced = self.module.params['nvo3_gw_enhanced']
        self.nvo3_service_extend = self.module.params['nvo3_service_extend']
        self.nvo3_eth_trunk_hash = self.module.params['nvo3_eth_trunk_hash']
        self.nvo3_ecmp_hash = self.module.params['nvo3_ecmp_hash']
        self.bridge_domain_id = self.module.params['bridge_domain_id']
        self.state = self.module.params['state']

        # state
        self.config = ""  # current config
        self.bd_info = list()
        self.changed = False
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def get_config(self, flags=None):
        """Retrieves the current config from the device or cache
        """
        flags = [] if flags is None else flags

        cmd = 'display current-configuration '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            self.module.fail_json(msg=err)
        cfg = str(out).strip()

        return cfg

    def get_current_config(self):
        """get current configuration"""

        flags = list()
        exp = " include-default | include vxlan|assign | exclude undo"
        flags.append(exp)
        return self.get_config(flags)

    def cli_add_command(self, command, undo=False):
        """add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command

        self.commands.append(cmd)          # set to device
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)   # show updates result

    def get_bd_list(self):
        """get bridge domain list"""
        flags = list()
        bd_info = list()
        exp = " include-default | include bridge-domain | exclude undo"
        flags.append(exp)
        bd_str = self.get_config(flags)
        if not bd_str:
            return bd_info
        bd_num = re.findall(r'bridge-domain\s*([0-9]+)', bd_str)
        bd_info.extend(bd_num)
        return bd_info

    def config_bridge_domain(self):
        """manage bridge domain"""

        if not self.bridge_domain_id:
            return

        cmd = "bridge-domain %s" % self.bridge_domain_id
        exist = self.bridge_domain_id in self.bd_info
        if self.state == "present":
            if not exist:
                self.cli_add_command(cmd)
                self.cli_add_command("quit")
        else:
            if exist:
                self.cli_add_command(cmd, undo=True)

    def config_tunnel_mode(self):
        """config tunnel mode vxlan"""

        # ip tunnel mode vxlan
        if self.tunnel_mode_vxlan:
            cmd = "ip tunnel mode vxlan"
            exist = is_config_exist(self.config, cmd)
            if self.tunnel_mode_vxlan == "enable":
                if not exist:
                    self.cli_add_command(cmd)
            else:
                if exist:
                    self.cli_add_command(cmd, undo=True)

    def config_assign_forward(self):
        """config assign forward command"""

        # [undo] assign forward nvo3-gateway enhanced {l2|l3)
        if self.nvo3_gw_enhanced:
            cmd = "assign forward nvo3-gateway enhanced %s" % self.nvo3_gw_enhanced
            exist = is_config_exist(self.config, cmd)
            if self.state == "present":
                if not exist:
                    self.cli_add_command(cmd)
            else:
                if exist:
                    self.cli_add_command(cmd, undo=True)

        # [undo] assign forward nvo3 f-linecard compatibility enable
        if self.nvo3_prevent_loops:
            cmd = "assign forward nvo3 f-linecard compatibility enable"
            exist = is_config_exist(self.config, cmd)
            if self.nvo3_prevent_loops == "enable":
                if not exist:
                    self.cli_add_command(cmd)
            else:
                if exist:
                    self.cli_add_command(cmd, undo=True)

        # [undo] assign forward nvo3 acl extend enable
        if self.nvo3_acl_extend:
            cmd = "assign forward nvo3 acl extend enable"
            exist = is_config_exist(self.config, cmd)
            if self.nvo3_acl_extend == "enable":
                if not exist:
                    self.cli_add_command(cmd)
            else:
                if exist:
                    self.cli_add_command(cmd, undo=True)

        # [undo] assign forward nvo3 service extend enable
        if self.nvo3_service_extend:
            cmd = "assign forward nvo3 service extend enable"
            exist = is_config_exist(self.config, cmd)
            if self.nvo3_service_extend == "enable":
                if not exist:
                    self.cli_add_command(cmd)
            else:
                if exist:
                    self.cli_add_command(cmd, undo=True)

        # assign forward nvo3 eth-trunk hash {enable|disable}
        if self.nvo3_eth_trunk_hash:
            cmd = "assign forward nvo3 eth-trunk hash enable"
            exist = is_config_exist(self.config, cmd)
            if self.nvo3_eth_trunk_hash == "enable":
                if not exist:
                    self.cli_add_command(cmd)
            else:
                if exist:
                    self.cli_add_command(cmd, undo=True)

        # [undo] assign forward nvo3 ecmp hash enable
        if self.nvo3_ecmp_hash:
            cmd = "assign forward nvo3 ecmp hash enable"
            exist = is_config_exist(self.config, cmd)
            if self.nvo3_ecmp_hash == "enable":
                if not exist:
                    self.cli_add_command(cmd)
            else:
                if exist:
                    self.cli_add_command(cmd, undo=True)

    def check_params(self):
        """Check all input params"""

        # bridge domain id check
        if self.bridge_domain_id:
            if not self.bridge_domain_id.isdigit():
                self.module.fail_json(
                    msg="Error: bridge domain id is not digit.")
            if int(self.bridge_domain_id) < 1 or int(self.bridge_domain_id) > 16777215:
                self.module.fail_json(
                    msg="Error: bridge domain id is not in the range from 1 to 16777215.")

    def get_proposed(self):
        """get proposed info"""

        if self.tunnel_mode_vxlan:
            self.proposed["tunnel_mode_vxlan"] = self.tunnel_mode_vxlan
        if self.nvo3_prevent_loops:
            self.proposed["nvo3_prevent_loops"] = self.nvo3_prevent_loops
        if self.nvo3_acl_extend:
            self.proposed["nvo3_acl_extend"] = self.nvo3_acl_extend
        if self.nvo3_gw_enhanced:
            self.proposed["nvo3_gw_enhanced"] = self.nvo3_gw_enhanced
        if self.nvo3_service_extend:
            self.proposed["nvo3_service_extend"] = self.nvo3_service_extend
        if self.nvo3_eth_trunk_hash:
            self.proposed["nvo3_eth_trunk_hash"] = self.nvo3_eth_trunk_hash
        if self.nvo3_ecmp_hash:
            self.proposed["nvo3_ecmp_hash"] = self.nvo3_ecmp_hash
        if self.bridge_domain_id:
            self.proposed["bridge_domain_id"] = self.bridge_domain_id
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        self.existing["bridge_domain"] = self.bd_info

        cmd = "ip tunnel mode vxlan"
        exist = is_config_exist(self.config, cmd)
        if exist:
            self.existing["tunnel_mode_vxlan"] = "enable"
        else:
            self.existing["tunnel_mode_vxlan"] = "disable"

        cmd = "assign forward nvo3 f-linecard compatibility enable"
        exist = is_config_exist(self.config, cmd)
        if exist:
            self.existing["nvo3_prevent_loops"] = "enable"
        else:
            self.existing["nvo3_prevent_loops"] = "disable"

        cmd = "assign forward nvo3 acl extend enable"
        exist = is_config_exist(self.config, cmd)
        if exist:
            self.existing["nvo3_acl_extend"] = "enable"
        else:
            self.existing["nvo3_acl_extend"] = "disable"

        self.existing["nvo3_gw_enhanced"] = get_nvo3_gw_enhanced(
            self.config)

        cmd = "assign forward nvo3 service extend enable"
        exist = is_config_exist(self.config, cmd)
        if exist:
            self.existing["nvo3_service_extend"] = "enable"
        else:
            self.existing["nvo3_service_extend"] = "disable"

        cmd = "assign forward nvo3 eth-trunk hash enable"
        exist = is_config_exist(self.config, cmd)
        if exist:
            self.existing["nvo3_eth_trunk_hash"] = "enable"
        else:
            self.existing["nvo3_eth_trunk_hash"] = "disable"

        cmd = "assign forward nvo3 ecmp hash enable"
        exist = is_config_exist(self.config, cmd)
        if exist:
            self.existing["nvo3_ecmp_hash"] = "enable"
        else:
            self.existing["nvo3_ecmp_hash"] = "disable"

    def get_end_state(self):
        """get end state info"""

        config = self.get_current_config()

        self.end_state["bridge_domain"] = self.get_bd_list()

        cmd = "ip tunnel mode vxlan"
        exist = is_config_exist(config, cmd)
        if exist:
            self.end_state["tunnel_mode_vxlan"] = "enable"
        else:
            self.end_state["tunnel_mode_vxlan"] = "disable"

        cmd = "assign forward nvo3 f-linecard compatibility enable"
        exist = is_config_exist(config, cmd)
        if exist:
            self.end_state["nvo3_prevent_loops"] = "enable"
        else:
            self.end_state["nvo3_prevent_loops"] = "disable"

        cmd = "assign forward nvo3 acl extend enable"
        exist = is_config_exist(config, cmd)
        if exist:
            self.end_state["nvo3_acl_extend"] = "enable"
        else:
            self.end_state["nvo3_acl_extend"] = "disable"

        self.end_state["nvo3_gw_enhanced"] = get_nvo3_gw_enhanced(config)

        cmd = "assign forward nvo3 service extend enable"
        exist = is_config_exist(config, cmd)
        if exist:
            self.end_state["nvo3_service_extend"] = "enable"
        else:
            self.end_state["nvo3_service_extend"] = "disable"

        cmd = "assign forward nvo3 eth-trunk hash enable"
        exist = is_config_exist(config, cmd)
        if exist:
            self.end_state["nvo3_eth_trunk_hash"] = "enable"
        else:
            self.end_state["nvo3_eth_trunk_hash"] = "disable"

        cmd = "assign forward nvo3 ecmp hash enable"
        exist = is_config_exist(config, cmd)
        if exist:
            self.end_state["nvo3_ecmp_hash"] = "enable"
        else:
            self.end_state["nvo3_ecmp_hash"] = "disable"
        if self.existing == self.end_state:
            self.changed = True

    def work(self):
        """worker"""

        self.check_params()
        self.config = self.get_current_config()
        self.bd_info = self.get_bd_list()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        self.config_bridge_domain()
        self.config_tunnel_mode()
        self.config_assign_forward()
        if self.commands:
            self.cli_load_config(self.commands)
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
        tunnel_mode_vxlan=dict(required=False, type='str',
                               choices=['enable', 'disable']),
        nvo3_prevent_loops=dict(required=False, type='str',
                                choices=['enable', 'disable']),
        nvo3_acl_extend=dict(required=False, type='str',
                             choices=['enable', 'disable']),
        nvo3_gw_enhanced=dict(required=False, type='str',
                              choices=['l2', 'l3']),
        nvo3_service_extend=dict(required=False, type='str',
                                 choices=['enable', 'disable']),
        nvo3_eth_trunk_hash=dict(required=False, type='str',
                                 choices=['enable', 'disable']),
        nvo3_ecmp_hash=dict(required=False, type='str',
                            choices=['enable', 'disable']),
        bridge_domain_id=dict(required=False, type='str'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )
    argument_spec.update(ce_argument_spec)
    module = VxlanGlobal(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
