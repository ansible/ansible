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
module: ce_evpn_bgp
version_added: "2.4"
short_description: Manages BGP EVPN configuration on HUAWEI CloudEngine switches.
description:
    - This module offers the ability to configure a BGP EVPN peer relationship on HUAWEI CloudEngine switches.
author:
    - Li Yanfeng (@CloudEngine-Ansible)
options:
    bgp_instance:
        description:
            - Name of a BGP instance. The value is a string of 1 to 31 case-sensitive characters, spaces not supported.
        required: True
    as_number:
        description:
            - Specifies integral AS number. The value is an integer ranging from 1 to 4294967295.
    peer_address:
        description:
            - Specifies the IPv4 address of a BGP EVPN peer. The value is in dotted decimal notation.
    peer_group_name:
        description:
            - Specify the name of a peer group that BGP peers need to join.
              The value is a string of 1 to 47 case-sensitive characters, spaces not supported.
    peer_enable:
        description:
            - Enable or disable a BGP device to exchange routes with a specified peer or peer group in the address
              family view.
        choices: ['true','false']
    advertise_router_type:
        description:
            - Configures a device to advertise routes to its BGP EVPN peers.
        choices: ['arp','irb']
    vpn_name:
        description:
            - Associates a specified VPN instance with the IPv4 address family.
              The value is a string of 1 to 31 case-sensitive characters, spaces not supported.
    advertise_l2vpn_evpn:
        description:
            - Enable or disable a device to advertise IP routes imported to a VPN instance to its EVPN instance.
        choices: ['enable','disable']
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
- name: evpn bgp module test
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

  - name: Enable peer address.
    ce_evpn_bgp:
      bgp_instance: 100
      peer_address: 1.1.1.1
      as_number: 100
      peer_enable: true
      provider: "{{ cli }}"

  - name: Enable peer group arp.
    ce_evpn_bgp:
      bgp_instance: 100
      peer_group_name: aaa
      advertise_router_type: arp
      provider: "{{ cli }}"

  - name: Enable advertise l2vpn evpn.
    ce_evpn_bgp:
      bgp_instance: 100
      vpn_name: aaa
      advertise_l2vpn_evpn: enable
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"advertise_router_type": "arp", "bgp_instance": "100", "peer_group_name": "aaa", "state": "present"}
existing:
    description: k/v pairs of existing rollback
    returned: always
    type: dict
    sample: {"bgp_instance": "100", "peer_group_advertise_type": []}

updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["peer 1.1.1.1 enable",
             "peer aaa advertise arp"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"advertise_l2vpn_evpn": "enable", "bgp_instance": "100", "vpn_name": "aaa"}
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_config, load_config
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec


def is_config_exist(cmp_cfg, test_cfg):
    """check configuration is exist"""

    if not cmp_cfg or not test_cfg:
        return False

    return bool(test_cfg in cmp_cfg)


def is_valid_address(address):
    """check ip-address is valid"""

    if address.find('.') != -1:
        addr_list = address.split('.')
        if len(addr_list) != 4:
            return False
        for each_num in addr_list:
            if not each_num.isdigit():
                return False
            if int(each_num) > 255:
                return False
        return True

    return False


def is_valid_as_number(as_number):
    """check as-number is valid"""

    if as_number.isdigit():
        if int(as_number) > 4294967295 or int(as_number) < 1:
            return False
        return True
    else:
        if as_number.find('.') != -1:
            number_list = as_number.split('.')
            if len(number_list) != 2:
                return False
            if number_list[1] == 0:
                return False
            for each_num in number_list:
                if not each_num.isdigit():
                    return False
                if int(each_num) > 65535:
                    return False
            return True

        return False


class EvpnBgp(object):
    """
    Manages evpn bgp configuration.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.netconf = None
        self.init_module()

        # module input info
        self.as_number = self.module.params['as_number']
        self.bgp_instance = self.module.params['bgp_instance']
        self.peer_address = self.module.params['peer_address']
        self.peer_group_name = self.module.params['peer_group_name']
        self.peer_enable = self.module.params['peer_enable']
        self.advertise_router_type = self.module.params[
            'advertise_router_type']
        self.vpn_name = self.module.params['vpn_name']
        self.advertise_l2vpn_evpn = self.module.params['advertise_l2vpn_evpn']
        self.state = self.module.params['state']

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        # state
        self.config = ""
        self.config_list = list()
        self.l2vpn_evpn_exist = False
        self.changed = False
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.existing = dict()
        self.proposed = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """
        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def get_evpn_overlay_config(self):
        """get evpn-overlay enable configuration"""

        flags = list()
        exp = "| ignore-case include evpn-overlay enable"
        flags.append(exp)
        return get_config(self.module, flags)

    def get_current_config(self):
        """get current configuration"""

        flags = list()
        exp = "| ignore-case section include bgp %s" % self.bgp_instance
        flags.append(exp)
        return get_config(self.module, flags)

    def cli_add_command(self, command, undo=False):
        """add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command

        self.commands.append(cmd)          # set to device
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)   # show updates result

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def check_params(self):
        """Check all input params"""

        # as_number check
        if not self.bgp_instance:
            self.module.fail_json(
                msg='Error: The bgp_instance can not be none.')
        if not self.peer_enable and not self.advertise_router_type and not self.advertise_l2vpn_evpn:
            self.module.fail_json(
                msg='Error: The peer_enable, advertise_router_type, advertise_l2vpn_evpn '
                    'can not be none at the same time.')
        if self.as_number:
            if not is_valid_as_number(self.as_number):
                self.module.fail_json(
                    msg='Error: The parameter of as_number %s is invalid.' % self.as_number)
        # bgp_instance check
        if self.bgp_instance:
            if not is_valid_as_number(self.bgp_instance):
                self.module.fail_json(
                    msg='Error: The parameter of bgp_instance %s is invalid.' % self.bgp_instance)

        # peer_address check
        if self.peer_address:
            if not is_valid_address(self.peer_address):
                self.module.fail_json(
                    msg='Error: The %s is not a valid ip address.' % self.peer_address)

        # peer_group_name check
        if self.peer_group_name:
            if len(self.peer_group_name) > 47 \
                    or len(self.peer_group_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: peer group name is not in the range from 1 to 47.')

        # vpn_name check
        if self.vpn_name:
            if len(self.vpn_name) > 31 \
                    or len(self.vpn_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: peer group name is not in the range from 1 to 31.')

    def get_proposed(self):
        """get proposed info"""

        if self.as_number:
            self.proposed["as_number"] = self.as_number
        if self.bgp_instance:
            self.proposed["bgp_instance"] = self.bgp_instance
        if self.peer_address:
            self.proposed["peer_address"] = self.peer_address
        if self.peer_group_name:
            self.proposed["peer_group_name"] = self.peer_group_name
        if self.peer_enable:
            self.proposed["peer_enable"] = self.peer_enable
        if self.advertise_router_type:
            self.proposed["advertise_router_type"] = self.advertise_router_type
        if self.vpn_name:
            self.proposed["vpn_name"] = self.vpn_name
        if self.advertise_l2vpn_evpn:
            self.proposed["advertise_l2vpn_evpn"] = self.advertise_l2vpn_evpn
        if not self.peer_enable or not self.advertise_l2vpn_evpn:
            if self.state:
                self.proposed["state"] = self.state

    def get_peers_enable(self):
        """get evpn peer address enable list"""

        if len(self.config_list) != 2:
            return None
        self.config_list = self.config.split('l2vpn-family evpn')
        get = re.findall(
            r"peer ([0-9]+.[0-9]+.[0-9]+.[0-9]+)\s?as-number\s?(\S*)", self.config_list[0])
        if not get:
            return None
        else:
            peers = list()
            for item in get:
                cmd = "peer %s enable" % item[0]
                exist = is_config_exist(self.config_list[1], cmd)
                if exist:
                    peers.append(
                        dict(peer_address=item[0], as_number=item[1], peer_enable='true'))
                else:
                    peers.append(dict(peer_address=item[0], as_number=item[1], peer_enable='false'))
            return peers

    def get_peers_advertise_type(self):
        """get evpn peer address advertise type list"""

        if len(self.config_list) != 2:
            return None
        self.config_list = self.config.split('l2vpn-family evpn')
        get = re.findall(
            r"peer ([0-9]+.[0-9]+.[0-9]+.[0-9]+)\s?as-number\s?(\S*)", self.config_list[0])
        if not get:
            return None
        else:
            peers = list()
            for item in get:
                cmd = "peer %s advertise arp" % item[0]
                exist1 = is_config_exist(self.config_list[1], cmd)
                cmd = "peer %s advertise irb" % item[0]
                exist2 = is_config_exist(self.config_list[1], cmd)
                if exist1:
                    peers.append(dict(peer_address=item[0], as_number=item[1], advertise_type='arp'))
                if exist2:
                    peers.append(dict(peer_address=item[0], as_number=item[1], advertise_type='irb'))
            return peers

    def get_peers_group_enable(self):
        """get evpn peer group name enable list"""

        if len(self.config_list) != 2:
            return None
        self.config_list = self.config.split('l2vpn-family evpn')
        get1 = re.findall(
            r"group (\S+) external", self.config_list[0])

        get2 = re.findall(
            r"group (\S+) internal", self.config_list[0])

        if not get1 and not get2:
            return None
        else:
            peer_groups = list()
            for item in get1:
                cmd = "peer %s enable" % item
                exist = is_config_exist(self.config_list[1], cmd)
                if exist:
                    peer_groups.append(
                        dict(peer_group_name=item, peer_enable='true'))
                else:
                    peer_groups.append(
                        dict(peer_group_name=item, peer_enable='false'))

            for item in get2:
                cmd = "peer %s enable" % item
                exist = is_config_exist(self.config_list[1], cmd)
                if exist:
                    peer_groups.append(
                        dict(peer_group_name=item, peer_enable='true'))
                else:
                    peer_groups.append(
                        dict(peer_group_name=item, peer_enable='false'))
            return peer_groups

    def get_peer_groups_advertise_type(self):
        """get evpn peer group name advertise type list"""

        if len(self.config_list) != 2:
            return None
        self.config_list = self.config.split('l2vpn-family evpn')
        get1 = re.findall(
            r"group (\S+) external", self.config_list[0])

        get2 = re.findall(
            r"group (\S+) internal", self.config_list[0])
        if not get1 and not get2:
            return None
        else:
            peer_groups = list()
            for item in get1:
                cmd = "peer %s advertise arp" % item
                exist1 = is_config_exist(self.config_list[1], cmd)
                cmd = "peer %s advertise irb" % item
                exist2 = is_config_exist(self.config_list[1], cmd)
                if exist1:
                    peer_groups.append(
                        dict(peer_group_name=item, advertise_type='arp'))
                if exist2:
                    peer_groups.append(
                        dict(peer_group_name=item, advertise_type='irb'))

            for item in get2:
                cmd = "peer %s advertise arp" % item
                exist1 = is_config_exist(self.config_list[1], cmd)
                cmd = "peer %s advertise irb" % item
                exist2 = is_config_exist(self.config_list[1], cmd)
                if exist1:
                    peer_groups.append(
                        dict(peer_group_name=item, advertise_type='arp'))
                if exist2:
                    peer_groups.append(
                        dict(peer_group_name=item, advertise_type='irb'))
            return peer_groups

    def get_existing(self):
        """get existing info"""

        if not self.config:
            return
        if self.bgp_instance:
            self.existing["bgp_instance"] = self.bgp_instance

        if self.peer_address and self.peer_enable:
            if self.l2vpn_evpn_exist:
                self.existing["peer_address_enable"] = self.get_peers_enable()

        if self.peer_group_name and self.peer_enable:
            if self.l2vpn_evpn_exist:
                self.existing[
                    "peer_group_enable"] = self.get_peers_group_enable()

        if self.peer_address and self.advertise_router_type:
            if self.l2vpn_evpn_exist:
                self.existing[
                    "peer_address_advertise_type"] = self.get_peers_advertise_type()

        if self.peer_group_name and self.advertise_router_type:
            if self.l2vpn_evpn_exist:
                self.existing[
                    "peer_group_advertise_type"] = self.get_peer_groups_advertise_type()

        if self.advertise_l2vpn_evpn and self.vpn_name:
            cmd = " ipv4-family vpn-instance %s" % self.vpn_name
            exist = is_config_exist(self.config, cmd)
            if exist:
                self.existing["vpn_name"] = self.vpn_name
                l2vpn_cmd = "advertise l2vpn evpn"
                l2vpn_exist = is_config_exist(self.config, l2vpn_cmd)
                if l2vpn_exist:
                    self.existing["advertise_l2vpn_evpn"] = 'enable'
                else:
                    self.existing["advertise_l2vpn_evpn"] = 'disable'

    def get_end_state(self):
        """get end state info"""

        self.config = self.get_current_config()
        if not self.config:
            return

        if self.bgp_instance:
            self.end_state["bgp_instance"] = self.bgp_instance

        if self.peer_address and self.peer_enable:
            if self.l2vpn_evpn_exist:
                self.end_state["peer_address_enable"] = self.get_peers_enable()

        if self.peer_group_name and self.peer_enable:
            if self.l2vpn_evpn_exist:
                self.end_state[
                    "peer_group_enable"] = self.get_peers_group_enable()

        if self.peer_address and self.advertise_router_type:
            if self.l2vpn_evpn_exist:
                self.end_state[
                    "peer_address_advertise_type"] = self.get_peers_advertise_type()

        if self.peer_group_name and self.advertise_router_type:
            if self.l2vpn_evpn_exist:
                self.end_state[
                    "peer_group_advertise_type"] = self.get_peer_groups_advertise_type()

        if self.advertise_l2vpn_evpn and self.vpn_name:
            cmd = " ipv4-family vpn-instance %s" % self.vpn_name
            exist = is_config_exist(self.config, cmd)
            if exist:
                self.end_state["vpn_name"] = self.vpn_name
                l2vpn_cmd = "advertise l2vpn evpn"
                l2vpn_exist = is_config_exist(self.config, l2vpn_cmd)
                if l2vpn_exist:
                    self.end_state["advertise_l2vpn_evpn"] = 'enable'
                else:
                    self.end_state["advertise_l2vpn_evpn"] = 'disable'

    def config_peer(self):
        """configure evpn bgp peer command"""

        if self.as_number and self.peer_address:
            cmd = "peer %s as-number %s" % (self.peer_address, self.as_number)
            exist = is_config_exist(self.config, cmd)
            if not exist:
                self.module.fail_json(
                    msg='Error:  The peer session %s does not exist or the peer already '
                        'exists in another as-number.' % self.peer_address)
            cmd = "bgp %s" % self.bgp_instance
            self.cli_add_command(cmd)
            cmd = "l2vpn-family evpn"
            self.cli_add_command(cmd)
            exist_l2vpn = is_config_exist(self.config, cmd)
            if self.peer_enable:
                cmd = "peer %s enable" % self.peer_address
                if exist_l2vpn:
                    exist = is_config_exist(self.config_list[1], cmd)
                    if self.peer_enable == "true" and not exist:
                        self.cli_add_command(cmd)
                        self.changed = True
                    elif self.peer_enable == "false" and exist:
                        self.cli_add_command(cmd, undo=True)
                        self.changed = True
                else:
                    self.cli_add_command(cmd)
                    self.changed = True

            if self.advertise_router_type:
                cmd = "peer %s advertise %s" % (
                    self.peer_address, self.advertise_router_type)
                exist = is_config_exist(self.config, cmd)
                if self.state == "present" and not exist:
                    self.cli_add_command(cmd)
                    self.changed = True
                elif self.state == "absent" and exist:
                    self.cli_add_command(cmd, undo=True)
                    self.changed = True
        elif self.peer_group_name:
            cmd_1 = "group %s external" % self.peer_group_name
            exist_1 = is_config_exist(self.config, cmd_1)
            cmd_2 = "group %s internal" % self.peer_group_name
            exist_2 = is_config_exist(self.config, cmd_2)
            exist = False
            if exist_1:
                exist = True
            if exist_2:
                exist = True
            if not exist:
                self.module.fail_json(
                    msg='Error: The peer-group %s does not exist.' % self.peer_group_name)
            cmd = "bgp %s" % self.bgp_instance
            self.cli_add_command(cmd)
            cmd = "l2vpn-family evpn"
            self.cli_add_command(cmd)
            exist_l2vpn = is_config_exist(self.config, cmd)
            if self.peer_enable:
                cmd = "peer %s enable" % self.peer_group_name
                if exist_l2vpn:
                    exist = is_config_exist(self.config_list[1], cmd)
                    if self.peer_enable == "true" and not exist:
                        self.cli_add_command(cmd)
                        self.changed = True
                    elif self.peer_enable == "false" and exist:
                        self.cli_add_command(cmd, undo=True)
                        self.changed = True
                else:
                    self.cli_add_command(cmd)
                    self.changed = True

            if self.advertise_router_type:
                cmd = "peer %s advertise %s" % (
                    self.peer_group_name, self.advertise_router_type)
                exist = is_config_exist(self.config, cmd)
                if self.state == "present" and not exist:
                    self.cli_add_command(cmd)
                    self.changed = True
                elif self.state == "absent" and exist:
                    self.cli_add_command(cmd, undo=True)
                    self.changed = True

    def config_advertise_l2vpn_evpn(self):
        """configure advertise l2vpn evpn"""

        cmd = "ipv4-family vpn-instance %s" % self.vpn_name
        exist = is_config_exist(self.config, cmd)
        if not exist:
            self.module.fail_json(
                msg='Error: The VPN instance name %s does not exist.' % self.vpn_name)
        config_vpn_list = self.config.split(cmd)
        cmd = "ipv4-family vpn-instance"
        exist_vpn = is_config_exist(config_vpn_list[1], cmd)
        cmd_l2vpn = "advertise l2vpn evpn"
        if exist_vpn:
            config_vpn = config_vpn_list[1].split('ipv4-family vpn-instance')
            exist_l2vpn = is_config_exist(config_vpn[0], cmd_l2vpn)
        else:
            exist_l2vpn = is_config_exist(config_vpn_list[1], cmd_l2vpn)
        cmd = "advertise l2vpn evpn"
        if self.advertise_l2vpn_evpn == "enable" and not exist_l2vpn:
            cmd = "bgp %s" % self.bgp_instance
            self.cli_add_command(cmd)
            cmd = "ipv4-family vpn-instance %s" % self.vpn_name
            self.cli_add_command(cmd)
            cmd = "advertise l2vpn evpn"
            self.cli_add_command(cmd)
            self.changed = True
        elif self.advertise_l2vpn_evpn == "disable" and exist_l2vpn:
            cmd = "bgp %s" % self.bgp_instance
            self.cli_add_command(cmd)
            cmd = "ipv4-family vpn-instance %s" % self.vpn_name
            self.cli_add_command(cmd)
            cmd = "advertise l2vpn evpn"
            self.cli_add_command(cmd, undo=True)
            self.changed = True

    def work(self):
        """worker"""

        self.check_params()
        evpn_config = self.get_evpn_overlay_config()
        if not evpn_config:
            self.module.fail_json(
                msg="Error: evpn-overlay enable is not configured.")
        self.config = self.get_current_config()
        if not self.config:
            self.module.fail_json(
                msg="Error: Bgp instance %s does not exist." % self.bgp_instance)

        self.config_list = self.config.split('l2vpn-family evpn')
        if len(self.config_list) == 2:
            self.l2vpn_evpn_exist = True
        self.get_existing()
        self.get_proposed()

        if self.peer_enable or self.advertise_router_type:
            self.config_peer()

        if self.advertise_l2vpn_evpn:
            self.config_advertise_l2vpn_evpn()
        if self.commands:
            self.cli_load_config(self.commands)
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
        bgp_instance=dict(required=True, type='str'),
        as_number=dict(required=False, type='str'),
        peer_address=dict(required=False, type='str'),
        peer_group_name=dict(required=False, type='str'),
        peer_enable=dict(required=False, type='str', choices=[
            'true', 'false']),
        advertise_router_type=dict(required=False, type='str', choices=[
            'arp', 'irb']),

        vpn_name=dict(required=False, type='str'),
        advertise_l2vpn_evpn=dict(required=False, type='str', choices=[
            'enable', 'disable']),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )
    argument_spec.update(ce_argument_spec)
    module = EvpnBgp(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
