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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ce_evpn_bgp_rr
version_added: "2.3"
short_description: Manages RR for the VXLAN Network.
extends_documentation_fragment: cloudengine
description:
    - Configure an RR in BGP-EVPN address family view.
author: Zhijin Zhou (@CloudEngine-Ansible)
notes:
    - Ensure that BGP view is existed.
    - The peer, peer_type, and reflect_client arguments must all exist or not exist.
options:
    as_number:
        description:
            - Specifies the number of the AS, in integer format.
              The value is an integer that ranges from 1 to 4294967295.
        required: true
        default: null
    bgp_instance:
        description:
            - Specifies the name of a BGP instance.
              The value of instance-name can be an integer 1 or a string of 1 to 31.
        required: false
        default: null
    bgp_evpn_enable:
        description:
            - Enable or disable the BGP-EVPN address family.
        required: false
        choices: ['true','false']
        default: true
    peer_type:
        description:
            - Specify the peer type.
        required: false
        choices: ['group_name','ipv4_address']
        default: null
    peer:
        description:
            - Specifies the IPv4 address or the group name of a peer.
        required: false
        default: null
    reflect_client:
        description:
            - Configure the local device as the route reflector and the peer or peer group as the client of the route reflector
        required: false
        choices: ['true','false']
        default: null
    policy_vpn_target:
        description:
            - Enable or disable the VPN-Target filtering.
        required: false
        choices: ['true','false']
        default: null
'''

EXAMPLES = '''
# Configure BGP-EVPN address family view and ensure that BGP view has existed.
- ce_evpn_bgp_rr:
    as_number=20
    bgp_evpn_enable=true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"

# Configure reflect client and ensure peer has existed.
- ce_evpn_bgp_rr:
    as_number=20
    peer_type=ipv4_address
    peer=192.8.3.3
    reflect_client=true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"

# Configure the VPN-Target filtering.
- ce_evpn_bgp_rr:
    as_number=20
    policy_vpn_target=true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"

# Configure an RR in BGP-EVPN address family view.
- ce_evpn_bgp_rr:
    as_number=20
    bgp_evpn_enable=true
    peer_type=ipv4_address
    peer=192.8.3.3
    reflect_client=true
    policy_vpn_target=false
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "as_number": "20",
                "bgp_evpn_enable": "true",
                "bgp_instance": null,
                "peer": "192.8.3.3",
                "peer_type": "ipv4_address",
                "policy_vpn_target": "false",
                "reflect_client": "true"
            }
existing:
    description: k/v pairs of existing attributes on the device
    type: dict
    sample: {
                "as_number": "20",
                "bgp_evpn_enable": "false",
                "bgp_instance": null,
                "peer": null,
                "peer_type": null,
                "policy_vpn_target": "false",
                "reflect_client": "false"
            }
end_state:
    description: k/v pairs of end attributes on the device
    returned: always
    type: dict or null
    sample: {
                "as_number": "20",
                "bgp_evpn_enable": "true",
                "bgp_instance": null,
                "peer": "192.8.3.3",
                "peer_type": "ipv4_address",
                "policy_vpn_target": "false",
                "reflect_client": "true"
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
    type: boolean
    sample: true
'''

import re
from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.cloudengine import get_cli_exception


def is_config_exist(cmp_cfg, test_cfg):
    """is configuration exist"""

    if not cmp_cfg or not test_cfg:
        return False

    return bool(test_cfg in cmp_cfg)


class EvpnBgpRr(object):
    """Manange RR in BGP-EVPN address family view"""

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

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.password = self.module.params['password']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """init module"""

        self.module = NetworkModule(
            argument_spec=self.spec, connect_on_load=False, supports_check_mode=True)

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            try:
                self.module.config.load_config(commands)
            except NetworkError:
                err = get_cli_exception()
                self.module.fail_json(msg=err)

    def is_bgp_view_exist(self):
        """judge whether BGP view has existed"""

        if self.bgp_instance:
            view_cmd = "bgp %s instance %s" % (
                self.as_number, self.bgp_instance)
        else:
            view_cmd = "bgp %s" % self.as_number

        return is_config_exist(self.config, view_cmd)

    def is_l2vpn_family_evpn_exist(self):
        """judge whether BGP-EVPN address family view has existed"""

        view_cmd = "l2vpn-family evpn"
        return is_config_exist(self.config, view_cmd)

    def is_reflect_client_exist(self):
        """judge whether reflect client is configured"""

        view_cmd = "peer %s reflect-client" % self.peer
        return is_config_exist(self.bgp_evpn_config, view_cmd)

    def is_policy_vpn_target_exist(self):
        """judge whether the VPN-Target filtering is enabled"""

        view_cmd = "undo policy vpn-target"
        if is_config_exist(self.bgp_evpn_config, view_cmd):
            return False
        else:
            return True

    def get_config_in_bgp_view(self):
        """get configuration in BGP view"""

        exp = " | section include"
        if self.as_number:
            if self.bgp_instance:
                exp += " bgp %s instance %s" % (self.as_number,
                                                self.bgp_instance)
            else:
                exp += " bgp %s" % self.as_number

        return self.module.config.get_config(include_defaults=False, regular=exp)

    def get_config_in_bgp_evpn_view(self):
        """get configuration in BGP_EVPN view"""

        self.bgp_evpn_config = ""
        if not self.config:
            return ""

        index = self.config.find("l2vpn-family evpn")
        if index == -1:
            return ""

        return self.config[index:]

    def get_current_config(self):
        """get current configuration"""

        if not self.as_number:
            self.module.fail_json(msg='Error: The value of as-number cannot be empty.')

        self.cur_config['bgp_exist'] = False
        self.cur_config['bgp_evpn_enable'] = 'false'
        self.cur_config['reflect_client'] = 'false'
        self.cur_config['policy_vpn_target'] = 'false'
        self.cur_config['peer_type'] = None
        self.cur_config['peer'] = None

        self.config = self.get_config_in_bgp_view()

        if not self.is_bgp_view_exist():
            return
        self.cur_config['bgp_exist'] = True

        if not self.is_l2vpn_family_evpn_exist():
            return
        self.cur_config['bgp_evpn_enable'] = 'true'

        self.bgp_evpn_config = self.get_config_in_bgp_evpn_view()
        if self.is_reflect_client_exist():
            self.cur_config['reflect_client'] = 'true'
            self.cur_config['peer_type'] = self.peer_type
            self.cur_config['peer'] = self.peer

        if self.is_policy_vpn_target_exist():
            self.cur_config['policy_vpn_target'] = 'true'

    def get_existing(self):
        """get existing config"""

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
        """get proposed config"""

        self.proposed = dict(as_number=self.as_number,
                             bgp_instance=self.bgp_instance,
                             peer_type=self.peer_type,
                             peer=self.peer,
                             bgp_evpn_enable=self.bgp_evpn_enable,
                             reflect_client=self.reflect_client,
                             policy_vpn_target=self.policy_vpn_target)

    def get_end_state(self):
        """get end config"""

        self.get_current_config()
        self.end_state = dict(as_number=self.as_number,
                              bgp_instance=self.bgp_instance,
                              peer_type=self.cur_config['peer_type'],
                              peer=self.cur_config['peer'],
                              bgp_evpn_enable=self.cur_config[
                                  'bgp_evpn_enable'],
                              reflect_client=self.cur_config['reflect_client'],
                              policy_vpn_target=self.cur_config['policy_vpn_target'])

    def show_result(self):
        """ show result"""

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
        """ judge whether configuration has existed"""

        if self.bgp_evpn_enable and self.bgp_evpn_enable != self.cur_config['bgp_evpn_enable']:
            return False

        if self.bgp_evpn_enable == 'false' and self.cur_config['bgp_evpn_enable'] == 'false':
            return True

        if self.reflect_client and self.reflect_client == 'true':
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
        """add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command

        self.commands.append(cmd)          # set to device
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)   # show updates result

    def config_rr(self):
        """configure RR"""

        if self.conf_exist:
            return

        if self.bgp_instance:
            view_cmd = "bgp %s instance %s" % (
                self.as_number, self.bgp_instance)
        else:
            view_cmd = "bgp %s" % self.as_number
        self.cli_add_command(view_cmd)

        if self.bgp_evpn_enable == 'false':
            self.cli_add_command("  undo l2vpn-family evpn")
        else:
            self.cli_add_command("  l2vpn-family evpn")
            if self.reflect_client and self.reflect_client != self.cur_config['reflect_client']:
                if self.reflect_client == 'true':
                    self.cli_add_command("    peer %s enable" % self.peer)
                    self.cli_add_command(
                        "    peer %s reflect-client" % self.peer)
                else:
                    self.cli_add_command(
                        "    undo peer %s reflect-client" % self.peer)
                    self.cli_add_command("    undo peer %s enable" % self.peer)
            if self.cur_config['bgp_evpn_enable'] == 'true':
                if self.policy_vpn_target and self.policy_vpn_target != self.cur_config['policy_vpn_target']:
                    if self.policy_vpn_target == 'true':
                        self.cli_add_command("    policy vpn-target")
                    else:
                        self.cli_add_command("    undo policy vpn-target")
            else:
                if self.policy_vpn_target and self.policy_vpn_target == 'false':
                    self.cli_add_command("    undo policy vpn-target")

        if self.commands:
            self.cli_load_config(self.commands)
            self.changed = True

    def check_is_ipv4_addr(self):
        """check ipaddress validate"""

        rule1 = r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.'
        rule2 = r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])'
        ipv4_regex = '%s%s%s%s%s%s' % ('^', rule1, rule1, rule1, rule2, '$')

        return bool(re.match(ipv4_regex, self.peer))

    def check_params(self):
        """Check all input params"""

        if self.cur_config['bgp_exist'] == 'false':
            self.module.fail_json(msg="Error: BGP view doesnot exist.")

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
        """excute task"""

        self.get_current_config()
        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.conf_exist = self.judge_if_config_exist()

        self.config_rr()

        self.get_end_state()
        self.show_result()


def main():
    """main function entry"""

    argument_spec = dict(
        as_number=dict(required=True, type='str'),
        bgp_instance=dict(required=False, type='str'),
        bgp_evpn_enable=dict(required=False, type='str',
                             default='true', choices=['true', 'false']),
        peer_type=dict(required=False, type='str', choices=[
            'group_name', 'ipv4_address']),
        peer=dict(required=False, type='str'),
        reflect_client=dict(required=False, type='str',
                            choices=['true', 'false']),
        policy_vpn_target=dict(required=False, choices=['true', 'false']),
    )

    evpn_bgp_rr = EvpnBgpRr(argument_spec)
    evpn_bgp_rr.work()

if __name__ == '__main__':
    main()
