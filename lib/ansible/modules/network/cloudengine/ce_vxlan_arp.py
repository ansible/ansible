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
module: ce_vxlan_arp
version_added: "2.4"
short_description: Manages ARP attributes of VXLAN on HUAWEI CloudEngine devices.
description:
    - Manages ARP attributes of VXLAN on HUAWEI CloudEngine devices.
author: QijunPan (@QijunPan)
options:
    evn_bgp:
        description:
            - Enables EVN BGP.
        choices: ['enable', 'disable']
    evn_source_ip:
        description:
            - Specifies the source address of an EVN BGP peer.
              The value is in dotted decimal notation.
    evn_peer_ip:
        description:
            - Specifies the IP address of an EVN BGP peer.
              The value is in dotted decimal notation.
    evn_server:
        description:
            - Configures the local device as the router reflector (RR) on the EVN network.
        choices: ['enable', 'disable']
    evn_reflect_client:
        description:
            - Configures the local device as the route reflector (RR) and its peer as the client.
        choices: ['enable', 'disable']
    vbdif_name:
        description:
            -  Full name of VBDIF interface, i.e. Vbdif100.
    arp_collect_host:
        description:
            - Enables EVN BGP or BGP EVPN to collect host information.
        choices: ['enable', 'disable']
    host_collect_protocol:
        description:
            - Enables EVN BGP or BGP EVPN to advertise host information.
        choices: ['bgp','none']
    bridge_domain_id:
        description:
            - Specifies a BD(bridge domain) ID.
              The value is an integer ranging from 1 to 16777215.
    arp_suppress:
        description:
            - Enables ARP broadcast suppression in a BD.
        choices: ['enable', 'disable']
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        default: present
        choices: ['present', 'absent']
"""

EXAMPLES = '''
- name: vxlan arp module test
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

  - name: Configure EVN BGP on Layer 2 and Layer 3 VXLAN gateways to establish EVN BGP peer relationships.
    ce_vxlan_arp:
      evn_bgp: enable
      evn_source_ip: 6.6.6.6
      evn_peer_ip: 7.7.7.7
      provider: "{{ cli }}"
  - name: Configure a Layer 3 VXLAN gateway as a BGP RR.
    ce_vxlan_arp:
      evn_bgp: enable
      evn_server: enable
      provider: "{{ cli }}"
  - name: Enable EVN BGP on a Layer 3 VXLAN gateway to collect host information.
    ce_vxlan_arp:
      vbdif_name: Vbdif100
      arp_collect_host: enable
      provider: "{{ cli }}"
  - name: Enable Layer 2 and Layer 3 VXLAN gateways to use EVN BGP to advertise host information.
    ce_vxlan_arp:
      host_collect_protocol: bgp
      provider: "{{ cli }}"
  - name: Enable ARP broadcast suppression on a Layer 2 VXLAN gateway.
    ce_vxlan_arp:
      bridge_domain_id: 100
      arp_suppress: enable
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"evn_bgp": "enable", "evn_source_ip": "6.6.6.6", "evn_peer_ip":"7.7.7.7", state: "present"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"evn_bgp": "disable", "evn_source_ip": null, "evn_peer_ip": []}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"evn_bgp": "enable", "evn_source_ip": "6.6.6.6", "evn_peer_ip": ["7.7.7.7"]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["evn bgp",
             "source-address 6.6.6.6",
             "peer 7.7.7.7"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_config, load_config
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec


def is_config_exist(cmp_cfg, test_cfg):
    """is configuration exist"""

    if not cmp_cfg or not test_cfg:
        return False

    return bool(test_cfg in cmp_cfg)


def is_valid_v4addr(addr):
    """check is ipv4 addr is valid"""

    if addr.count('.') == 3:
        addr_list = addr.split('.')
        if len(addr_list) != 4:
            return False
        for each_num in addr_list:
            if not each_num.isdigit():
                return False
            if int(each_num) > 255:
                return False
        return True

    return False


def get_evn_peers(config):
    """get evn peer ip list"""

    get = re.findall(r"peer ([0-9]+.[0-9]+.[0-9]+.[0-9]+)", config)
    if not get:
        return None
    else:
        return list(set(get))


def get_evn_srouce(config):
    """get evn peer ip list"""

    get = re.findall(
        r"source-address ([0-9]+.[0-9]+.[0-9]+.[0-9]+)", config)
    if not get:
        return None
    else:
        return get[0]


def get_evn_reflect_client(config):
    """get evn reflect client list"""

    get = re.findall(
        r"peer ([0-9]+.[0-9]+.[0-9]+.[0-9]+)\s*reflect-client", config)
    if not get:
        return None
    else:
        return list(get)


class VxlanArp(object):
    """
    Manages arp attributes of VXLAN.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.evn_bgp = self.module.params['evn_bgp']
        self.evn_source_ip = self.module.params['evn_source_ip']
        self.evn_peer_ip = self.module.params['evn_peer_ip']
        self.evn_server = self.module.params['evn_server']
        self.evn_reflect_client = self.module.params['evn_reflect_client']
        self.vbdif_name = self.module.params['vbdif_name']
        self.arp_collect_host = self.module.params['arp_collect_host']
        self.host_collect_protocol = self.module.params[
            'host_collect_protocol']
        self.bridge_domain_id = self.module.params['bridge_domain_id']
        self.arp_suppress = self.module.params['arp_suppress']
        self.state = self.module.params['state']

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        # state
        self.config = ""  # current config
        self.changed = False
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init module"""

        required_together = [("vbdif_name", "arp_collect_host"), ("bridge_domain_id", "arp_suppress")]
        self.module = AnsibleModule(argument_spec=self.spec,
                                    required_together=required_together,
                                    supports_check_mode=True)

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def get_current_config(self):
        """get current configuration"""

        flags = list()
        exp = "| ignore-case section include evn bgp|host collect protocol bgp"
        if self.vbdif_name:
            exp += "|^interface %s$" % self.vbdif_name

        if self.bridge_domain_id:
            exp += "|^bridge-domain %s$" % self.bridge_domain_id

        flags.append(exp)
        config = get_config(self.module, flags)

        return config

    def cli_add_command(self, command, undo=False):
        """add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command

        self.commands.append(cmd)          # set to device
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)   # show updates result

    def config_bridge_domain(self):
        """manage bridge domain configuration"""

        if not self.bridge_domain_id:
            return

        # bridge-domain bd-id
        # [undo] arp broadcast-suppress enable

        cmd = "bridge-domain %s" % self.bridge_domain_id
        if not is_config_exist(self.config, cmd):
            self.module.fail_json(msg="Error: Bridge domain %s is not exist." % self.bridge_domain_id)

        cmd = "arp broadcast-suppress enable"
        exist = is_config_exist(self.config, cmd)
        if self.arp_suppress == "enable" and not exist:
            self.cli_add_command("bridge-domain %s" % self.bridge_domain_id)
            self.cli_add_command(cmd)
            self.cli_add_command("quit")
        elif self.arp_suppress == "disable" and exist:
            self.cli_add_command("bridge-domain %s" % self.bridge_domain_id)
            self.cli_add_command(cmd, undo=True)
            self.cli_add_command("quit")

    def config_evn_bgp(self):
        """enables EVN BGP and configure evn bgp command"""

        evn_bgp_view = False
        evn_bgp_enable = False

        cmd = "evn bgp"
        exist = is_config_exist(self.config, cmd)
        if self.evn_bgp == "enable" or exist:
            evn_bgp_enable = True

        # [undo] evn bgp
        if self.evn_bgp:
            if self.evn_bgp == "enable" and not exist:
                self.cli_add_command(cmd)
                evn_bgp_view = True
            elif self.evn_bgp == "disable" and exist:
                self.cli_add_command(cmd, undo=True)
                return

        # [undo] source-address ip-address
        if evn_bgp_enable and self.evn_source_ip:
            cmd = "source-address %s" % self.evn_source_ip
            exist = is_config_exist(self.config, cmd)
            if self.state == "present" and not exist:
                if not evn_bgp_view:
                    self.cli_add_command("evn bgp")
                    evn_bgp_view = True
                self.cli_add_command(cmd)
            elif self.state == "absent" and exist:
                if not evn_bgp_view:
                    self.cli_add_command("evn bgp")
                    evn_bgp_view = True
                self.cli_add_command(cmd, undo=True)

        # [undo] peer ip-address
        # [undo] peer ipv4-address reflect-client
        if evn_bgp_enable and self.evn_peer_ip:
            cmd = "peer %s" % self.evn_peer_ip
            exist = is_config_exist(self.config, cmd)
            if self.state == "present":
                if not exist:
                    if not evn_bgp_view:
                        self.cli_add_command("evn bgp")
                        evn_bgp_view = True
                    self.cli_add_command(cmd)
                    if self.evn_reflect_client == "enable":
                        self.cli_add_command(
                            "peer %s reflect-client" % self.evn_peer_ip)
                else:
                    if self.evn_reflect_client:
                        cmd = "peer %s reflect-client" % self.evn_peer_ip
                        exist = is_config_exist(self.config, cmd)
                        if self.evn_reflect_client == "enable" and not exist:
                            if not evn_bgp_view:
                                self.cli_add_command("evn bgp")
                                evn_bgp_view = True
                            self.cli_add_command(cmd)
                        elif self.evn_reflect_client == "disable" and exist:
                            if not evn_bgp_view:
                                self.cli_add_command("evn bgp")
                                evn_bgp_view = True
                            self.cli_add_command(cmd, undo=True)
            else:
                if exist:
                    if not evn_bgp_view:
                        self.cli_add_command("evn bgp")
                        evn_bgp_view = True
                    self.cli_add_command(cmd, undo=True)

        # [undo] server enable
        if evn_bgp_enable and self.evn_server:
            cmd = "server enable"
            exist = is_config_exist(self.config, cmd)
            if self.evn_server == "enable" and not exist:
                if not evn_bgp_view:
                    self.cli_add_command("evn bgp")
                    evn_bgp_view = True
                self.cli_add_command(cmd)
            elif self.evn_server == "disable" and exist:
                if not evn_bgp_view:
                    self.cli_add_command("evn bgp")
                    evn_bgp_view = True
                self.cli_add_command(cmd, undo=True)

        if evn_bgp_view:
            self.cli_add_command("quit")

    def config_vbdif(self):
        """configure command at the VBDIF interface view"""

        # interface vbdif bd-id
        # [undo] arp collect host enable

        cmd = "interface %s" % self.vbdif_name.lower().capitalize()
        exist = is_config_exist(self.config, cmd)

        if not exist:
            self.module.fail_json(
                msg="Error: Interface %s does not exist." % self.vbdif_name)

        cmd = "arp collect host enable"
        exist = is_config_exist(self.config, cmd)
        if self.arp_collect_host == "enable" and not exist:
            self.cli_add_command("interface %s" %
                                 self.vbdif_name.lower().capitalize())
            self.cli_add_command(cmd)
            self.cli_add_command("quit")
        elif self.arp_collect_host == "disable" and exist:
            self.cli_add_command("interface %s" %
                                 self.vbdif_name.lower().capitalize())
            self.cli_add_command(cmd, undo=True)
            self.cli_add_command("quit")

    def config_host_collect_protocal(self):
        """Enable EVN BGP or BGP EVPN to advertise host information"""

        # [undo] host collect protocol bgp
        cmd = "host collect protocol bgp"
        exist = is_config_exist(self.config, cmd)

        if self.state == "present":
            if self.host_collect_protocol == "bgp" and not exist:
                self.cli_add_command(cmd)
            elif self.host_collect_protocol == "none" and exist:
                self.cli_add_command(cmd, undo=True)
        else:
            if self.host_collect_protocol == "bgp" and exist:
                self.cli_add_command(cmd, undo=True)

    def is_valid_vbdif(self, ifname):
        """check is interface vbdif is valid"""

        if not ifname.upper().startswith('VBDIF'):
            return False
        bdid = self.vbdif_name.replace(" ", "").upper().replace("VBDIF", "")
        if not bdid.isdigit():
            return False
        if int(bdid) < 1 or int(bdid) > 16777215:
            return False

        return True

    def check_params(self):
        """Check all input params"""

        # bridge domain id check
        if self.bridge_domain_id:
            if not self.bridge_domain_id.isdigit():
                self.module.fail_json(
                    msg="Error: Bridge domain id is not digit.")
            if int(self.bridge_domain_id) < 1 or int(self.bridge_domain_id) > 16777215:
                self.module.fail_json(
                    msg="Error: Bridge domain id is not in the range from 1 to 16777215.")

        # evn_source_ip check
        if self.evn_source_ip:
            if not is_valid_v4addr(self.evn_source_ip):
                self.module.fail_json(msg="Error: evn_source_ip is invalid.")

        # evn_peer_ip check
        if self.evn_peer_ip:
            if not is_valid_v4addr(self.evn_peer_ip):
                self.module.fail_json(msg="Error: evn_peer_ip is invalid.")

        # vbdif_name check
        if self.vbdif_name:
            self.vbdif_name = self.vbdif_name.replace(
                " ", "").lower().capitalize()
            if not self.is_valid_vbdif(self.vbdif_name):
                self.module.fail_json(msg="Error: vbdif_name is invalid.")

        # evn_reflect_client and evn_peer_ip must set at the same time
        if self.evn_reflect_client and not self.evn_peer_ip:
            self.module.fail_json(
                msg="Error: evn_reflect_client and evn_peer_ip must set at the same time.")

        # evn_server and evn_reflect_client can not set at the same time
        if self.evn_server == "enable" and self.evn_reflect_client == "enable":
            self.module.fail_json(
                msg="Error: evn_server and evn_reflect_client can not set at the same time.")

    def get_proposed(self):
        """get proposed info"""

        if self.evn_bgp:
            self.proposed["evn_bgp"] = self.evn_bgp
        if self.evn_source_ip:
            self.proposed["evn_source_ip"] = self.evn_source_ip
        if self.evn_peer_ip:
            self.proposed["evn_peer_ip"] = self.evn_peer_ip
        if self.evn_server:
            self.proposed["evn_server"] = self.evn_server
        if self.evn_reflect_client:
            self.proposed["evn_reflect_client"] = self.evn_reflect_client
        if self.arp_collect_host:
            self.proposed["arp_collect_host"] = self.arp_collect_host
        if self.host_collect_protocol:
            self.proposed["host_collect_protocol"] = self.host_collect_protocol
        if self.arp_suppress:
            self.proposed["arp_suppress"] = self.arp_suppress
        if self.vbdif_name:
            self.proposed["vbdif_name"] = self.evn_peer_ip
        if self.bridge_domain_id:
            self.proposed["bridge_domain_id"] = self.bridge_domain_id
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        evn_bgp_exist = is_config_exist(self.config, "evn bgp")
        if evn_bgp_exist:
            self.existing["evn_bgp"] = "enable"
        else:
            self.existing["evn_bgp"] = "disable"

        if evn_bgp_exist:
            if is_config_exist(self.config, "server enable"):
                self.existing["evn_server"] = "enable"
            else:
                self.existing["evn_server"] = "disable"

            self.existing["evn_source_ip"] = get_evn_srouce(self.config)
            self.existing["evn_peer_ip"] = get_evn_peers(self.config)
            self.existing["evn_reflect_client"] = get_evn_reflect_client(
                self.config)

        if is_config_exist(self.config, "arp collect host enable"):
            self.existing["host_collect_protocol"] = "enable"
        else:
            self.existing["host_collect_protocol"] = "disable"

        if is_config_exist(self.config, "host collect protocol bgp"):
            self.existing["host_collect_protocol"] = "bgp"
        else:
            self.existing["host_collect_protocol"] = None

        if is_config_exist(self.config, "arp broadcast-suppress enable"):
            self.existing["arp_suppress"] = "enable"
        else:
            self.existing["arp_suppress"] = "disable"

    def get_end_state(self):
        """get end state info"""

        config = self.get_current_config()
        evn_bgp_exist = is_config_exist(config, "evn bgp")
        if evn_bgp_exist:
            self.end_state["evn_bgp"] = "enable"
        else:
            self.end_state["evn_bgp"] = "disable"

        if evn_bgp_exist:
            if is_config_exist(config, "server enable"):
                self.end_state["evn_server"] = "enable"
            else:
                self.end_state["evn_server"] = "disable"

            self.end_state["evn_source_ip"] = get_evn_srouce(config)
            self.end_state["evn_peer_ip"] = get_evn_peers(config)
            self.end_state[
                "evn_reflect_client"] = get_evn_reflect_client(config)

        if is_config_exist(config, "arp collect host enable"):
            self.end_state["host_collect_protocol"] = "enable"
        else:
            self.end_state["host_collect_protocol"] = "disable"

        if is_config_exist(config, "host collect protocol bgp"):
            self.end_state["host_collect_protocol"] = "bgp"
        else:
            self.end_state["host_collect_protocol"] = None

        if is_config_exist(config, "arp broadcast-suppress enable"):
            self.end_state["arp_suppress"] = "enable"
        else:
            self.end_state["arp_suppress"] = "disable"

    def work(self):
        """worker"""

        self.check_params()
        self.config = self.get_current_config()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        if self.evn_bgp or self.evn_server or self.evn_peer_ip or self.evn_source_ip:
            self.config_evn_bgp()

        if self.vbdif_name and self.arp_collect_host:
            self.config_vbdif()

        if self.host_collect_protocol:
            self.config_host_collect_protocal()

        if self.bridge_domain_id and self.arp_suppress:
            self.config_bridge_domain()

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
        evn_bgp=dict(required=False, type='str',
                     choices=['enable', 'disable']),
        evn_source_ip=dict(required=False, type='str'),
        evn_peer_ip=dict(required=False, type='str'),
        evn_server=dict(required=False, type='str',
                        choices=['enable', 'disable']),
        evn_reflect_client=dict(
            required=False, type='str', choices=['enable', 'disable']),
        vbdif_name=dict(required=False, type='str'),
        arp_collect_host=dict(required=False, type='str',
                              choices=['enable', 'disable']),
        host_collect_protocol=dict(
            required=False, type='str', choices=['bgp', 'none']),
        bridge_domain_id=dict(required=False, type='str'),
        arp_suppress=dict(required=False, type='str',
                          choices=['enable', 'disable']),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )
    argument_spec.update(ce_argument_spec)
    module = VxlanArp(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
