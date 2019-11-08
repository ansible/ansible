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
module: ce_evpn_bgp_rr
version_added: "2.4"
short_description: Manages RR for the VXLAN Network on HUAWEI CloudEngine switches.
description:
    - Configure an RR in BGP-EVPN address family view on HUAWEI CloudEngine switches.
author: Zhijin Zhou (@QijunPan)
notes:
    - Ensure that BGP view is existed.
    - The peer, peer_type, and reflect_client arguments must all exist or not exist.
    - Recommended connection is C(network_cli).
    - This module also works with C(local) connections for legacy playbooks.
options:
    as_number:
        description:
            - Specifies the number of the AS, in integer format.
              The value is an integer that ranges from 1 to 4294967295.
        required: true
    bgp_instance:
        description:
            - Specifies the name of a BGP instance.
              The value of instance-name can be an integer 1 or a string of 1 to 31.
    bgp_evpn_enable:
        description:
            - Enable or disable the BGP-EVPN address family.
        choices: ['enable','disable']
        default: 'enable'
    peer_type:
        description:
            - Specify the peer type.
        choices: ['group_name','ipv4_address']
    peer:
        description:
            - Specifies the IPv4 address or the group name of a peer.
    reflect_client:
        description:
            - Configure the local device as the route reflector and the peer or peer group as the client of the route reflector.
        choices: ['enable','disable']
    policy_vpn_target:
        description:
            - Enable or disable the VPN-Target filtering.
        choices: ['enable','disable']
'''

EXAMPLES = '''
- name: BGP RR test
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

  - name: "Configure BGP-EVPN address family view and ensure that BGP view has existed."
    ce_evpn_bgp_rr:
      as_number: 20
      bgp_evpn_enable: enable
      provider: "{{ cli }}"

  - name: "Configure reflect client and ensure peer has existed."
    ce_evpn_bgp_rr:
      as_number: 20
      peer_type: ipv4_address
      peer: 192.8.3.3
      reflect_client: enable
      provider: "{{ cli }}"

  - name: "Configure the VPN-Target filtering."
    ce_evpn_bgp_rr:
      as_number: 20
      policy_vpn_target: enable
      provider: "{{ cli }}"

  - name: "Configure an RR in BGP-EVPN address family view."
    ce_evpn_bgp_rr:
      as_number: 20
      bgp_evpn_enable: enable
      peer_type: ipv4_address
      peer: 192.8.3.3
      reflect_client: enable
      policy_vpn_target: disable
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "as_number": "20",
                "bgp_evpn_enable": "enable",
                "bgp_instance": null,
                "peer": "192.8.3.3",
                "peer_type": "ipv4_address",
                "policy_vpn_target": "disable",
                "reflect_client": "enable"
            }
existing:
    description: k/v pairs of existing attributes on the device
    returned: always
    type: dict
    sample: {
                "as_number": "20",
                "bgp_evpn_enable": "disable",
                "bgp_instance": null,
                "peer": null,
                "peer_type": null,
                "policy_vpn_target": "disable",
                "reflect_client": "disable"
            }
end_state:
    description: k/v pairs of end attributes on the device
    returned: always
    type: dict
    sample: {
                "as_number": "20",
                "bgp_evpn_enable": "enable",
                "bgp_instance": null,
                "peer": "192.8.3.3",
                "peer_type": "ipv4_address",
                "policy_vpn_target": "disable",
                "reflect_client": "enable"
            }
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: [
                "bgp 20",
                "  l2vpn-family evpn",
                "    peer 192.8.3.3 enable",
                "    peer 192.8.3.3 reflect-client",
                "    undo policy vpn-target"
            ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import exec_command, load_config, ce_argument_spec


def is_config_exist(cmp_cfg, test_cfg):
    """is configuration exist"""

    if not cmp_cfg or not test_cfg:
        return False

    return bool(test_cfg in cmp_cfg)


class EvpnBgpRr(object):
    """Manage RR in BGP-EVPN address family view"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # RR configuration parameters
        self.as_number = self.module.params['as_number']
        self.bgp_instance = self.module.params['bgp_instance']
        self.peer_type = self.module.params['peer_type']
        self.peer = self.module.params['peer']
        self.bgp_evpn_enable = self.module.params['bgp_evpn_enable']
        self.reflect_client = self.module.params['reflect_client']
        self.policy_vpn_target = self.module.params['policy_vpn_target']

        self.commands = list()
        self.config = None
        self.bgp_evpn_config = ""
        self.cur_config = dict()
        self.conf_exist = False

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """Init module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def cli_load_config(self, commands):
        """Load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def is_bgp_view_exist(self):
        """Judge whether BGP view has existed"""

        if self.bgp_instance:
            view_cmd = "bgp %s instance %s" % (
                self.as_number, self.bgp_instance)
        else:
            view_cmd = "bgp %s" % self.as_number

        return is_config_exist(self.config, view_cmd)

    def is_l2vpn_family_evpn_exist(self):
        """Judge whether BGP-EVPN address family view has existed"""

        view_cmd = "l2vpn-family evpn"
        return is_config_exist(self.config, view_cmd)

    def is_reflect_client_exist(self):
        """Judge whether reflect client is configured"""

        view_cmd = "peer %s reflect-client" % self.peer
        return is_config_exist(self.bgp_evpn_config, view_cmd)

    def is_policy_vpn_target_exist(self):
        """Judge whether the VPN-Target filtering is enabled"""

        view_cmd = "undo policy vpn-target"
        if is_config_exist(self.bgp_evpn_config, view_cmd):
            return False
        else:
            return True

    def get_config_in_bgp_view(self):
        """Get configuration in BGP view"""

        cmd = "display current-configuration | section include"
        if self.as_number:
            if self.bgp_instance:
                cmd += " bgp %s instance %s" % (self.as_number,
                                                self.bgp_instance)
            else:
                cmd += " bgp %s" % self.as_number
        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            self.module.fail_json(msg=err)
        config = out.strip() if out else ""
        if cmd == config:
            return ''

        return config

    def get_config_in_bgp_evpn_view(self):
        """Get configuration in BGP_EVPN view"""

        self.bgp_evpn_config = ""
        if not self.config:
            return ""

        index = self.config.find("l2vpn-family evpn")
        if index == -1:
            return ""

        return self.config[index:]

    def get_current_config(self):
        """Get current configuration"""

        if not self.as_number:
            self.module.fail_json(msg='Error: The value of as-number cannot be empty.')

        self.cur_config['bgp_exist'] = False
        self.cur_config['bgp_evpn_enable'] = 'disable'
        self.cur_config['reflect_client'] = 'disable'
        self.cur_config['policy_vpn_target'] = 'disable'
        self.cur_config['peer_type'] = None
        self.cur_config['peer'] = None

        self.config = self.get_config_in_bgp_view()

        if not self.is_bgp_view_exist():
            return
        self.cur_config['bgp_exist'] = True

        if not self.is_l2vpn_family_evpn_exist():
            return
        self.cur_config['bgp_evpn_enable'] = 'enable'

        self.bgp_evpn_config = self.get_config_in_bgp_evpn_view()
        if self.is_reflect_client_exist():
            self.cur_config['reflect_client'] = 'enable'
            self.cur_config['peer_type'] = self.peer_type
            self.cur_config['peer'] = self.peer

        if self.is_policy_vpn_target_exist():
            self.cur_config['policy_vpn_target'] = 'enable'

    def get_existing(self):
        """Get existing config"""

        self.existing = dict(as_number=self.as_number,
                             bgp_instance=self.bgp_instance,
                             peer_type=self.cur_config['peer_type'],
                             peer=self.cur_config['peer'],
                             bgp_evpn_enable=self.cur_config[
                                 'bgp_evpn_enable'],
                             reflect_client=self.cur_config['reflect_client'],
                             policy_vpn_target=self.cur_config[
                                 'policy_vpn_target'])

    def get_proposed(self):
        """Get proposed config"""

        self.proposed = dict(as_number=self.as_number,
                             bgp_instance=self.bgp_instance,
                             peer_type=self.peer_type,
                             peer=self.peer,
                             bgp_evpn_enable=self.bgp_evpn_enable,
                             reflect_client=self.reflect_client,
                             policy_vpn_target=self.policy_vpn_target)

    def get_end_state(self):
        """Get end config"""

        self.get_current_config()
        self.end_state = dict(as_number=self.as_number,
                              bgp_instance=self.bgp_instance,
                              peer_type=self.cur_config['peer_type'],
                              peer=self.cur_config['peer'],
                              bgp_evpn_enable=self.cur_config[
                                  'bgp_evpn_enable'],
                              reflect_client=self.cur_config['reflect_client'],
                              policy_vpn_target=self.cur_config['policy_vpn_target'])
        if self.end_state == self.existing:
            self.changed = False

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

    def judge_if_config_exist(self):
        """Judge whether configuration has existed"""

        if self.bgp_evpn_enable and self.bgp_evpn_enable != self.cur_config['bgp_evpn_enable']:
            return False

        if self.bgp_evpn_enable == 'disable' and self.cur_config['bgp_evpn_enable'] == 'disable':
            return True

        if self.reflect_client and self.reflect_client == 'enable':
            if self.peer_type and self.peer_type != self.cur_config['peer_type']:
                return False
            if self.peer and self.peer != self.cur_config['peer']:
                return False
        if self.reflect_client and self.reflect_client != self.cur_config['reflect_client']:
            return False

        if self.policy_vpn_target and self.policy_vpn_target != self.cur_config['policy_vpn_target']:
            return False

        return True

    def cli_add_command(self, command, undo=False):
        """Add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command

        self.commands.append(cmd)          # set to device
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)   # show updates result

    def config_rr(self):
        """Configure RR"""

        if self.conf_exist:
            return

        if self.bgp_instance:
            view_cmd = "bgp %s instance %s" % (
                self.as_number, self.bgp_instance)
        else:
            view_cmd = "bgp %s" % self.as_number
        self.cli_add_command(view_cmd)

        if self.bgp_evpn_enable == 'disable':
            self.cli_add_command("undo l2vpn-family evpn")
        else:
            self.cli_add_command("l2vpn-family evpn")
            if self.reflect_client and self.reflect_client != self.cur_config['reflect_client']:
                if self.reflect_client == 'enable':
                    self.cli_add_command("peer %s enable" % self.peer)
                    self.cli_add_command(
                        "peer %s reflect-client" % self.peer)
                else:
                    self.cli_add_command(
                        "undo peer %s reflect-client" % self.peer)
                    self.cli_add_command("undo peer %s enable" % self.peer)
            if self.cur_config['bgp_evpn_enable'] == 'enable':
                if self.policy_vpn_target and self.policy_vpn_target != self.cur_config['policy_vpn_target']:
                    if self.policy_vpn_target == 'enable':
                        self.cli_add_command("policy vpn-target")
                    else:
                        self.cli_add_command("undo policy vpn-target")
            else:
                if self.policy_vpn_target and self.policy_vpn_target == 'disable':
                    self.cli_add_command("undo policy vpn-target")

        if self.commands:
            self.cli_load_config(self.commands)
            self.changed = True

    def check_is_ipv4_addr(self):
        """Check ipaddress validate"""

        rule1 = r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.'
        rule2 = r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])'
        ipv4_regex = '%s%s%s%s%s%s' % ('^', rule1, rule1, rule1, rule2, '$')

        return bool(re.match(ipv4_regex, self.peer))

    def check_params(self):
        """Check all input params"""

        if self.cur_config['bgp_exist'] == 'false':
            self.module.fail_json(msg="Error: BGP view does not exist.")

        if self.bgp_instance:
            if len(self.bgp_instance) < 1 or len(self.bgp_instance) > 31:
                self.module.fail_json(
                    msg="Error: The length of BGP instance-name must be between 1 or a string of 1 to and 31.")

        if self.as_number:
            if len(self.as_number) > 11 or len(self.as_number) == 0:
                self.module.fail_json(
                    msg='Error: The len of as_number %s is out of [1 - 11].' % self.as_number)

        tmp_dict1 = dict(peer_type=self.peer_type,
                         peer=self.peer,
                         reflect_client=self.reflect_client)
        tmp_dict2 = dict((k, v)
                         for k, v in tmp_dict1.items() if v is not None)
        if len(tmp_dict2) != 0 and len(tmp_dict2) != 3:
            self.module.fail_json(
                msg='Error: The peer, peer_type, and reflect_client arguments must all exist or not exist.')

        if self.peer_type:
            if self.peer_type == 'ipv4_address' and not self.check_is_ipv4_addr():
                self.module.fail_json(msg='Error: Illegal IPv4 address.')
            elif self.peer_type == 'group_name' and self.check_is_ipv4_addr():
                self.module.fail_json(
                    msg='Error: Ip address cannot be configured as group-name.')

    def work(self):
        """Execute task"""

        self.get_current_config()
        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.conf_exist = self.judge_if_config_exist()

        self.config_rr()

        self.get_end_state()
        self.show_result()


def main():
    """Main function entry"""

    argument_spec = dict(
        as_number=dict(required=True, type='str'),
        bgp_instance=dict(required=False, type='str'),
        bgp_evpn_enable=dict(required=False, type='str',
                             default='enable', choices=['enable', 'disable']),
        peer_type=dict(required=False, type='str', choices=[
            'group_name', 'ipv4_address']),
        peer=dict(required=False, type='str'),
        reflect_client=dict(required=False, type='str',
                            choices=['enable', 'disable']),
        policy_vpn_target=dict(required=False, choices=['enable', 'disable']),
    )
    argument_spec.update(ce_argument_spec)
    evpn_bgp_rr = EvpnBgpRr(argument_spec)
    evpn_bgp_rr.work()


if __name__ == '__main__':
    main()
