#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_ntp_servers_peers
version_added: "2.5"
author: "Sara Touqan"
short_description: Manage NTP peers and servers on Mellanox ONYX network devices
description:
  - This module provides declarative management of NTP servers and peers
    on Mellanox ONYX network devices.
options:
 peers:
    description:
      - List of ntp peers.
    suboptions:
      ip_or_name:
        description:
          - Configures ntp peer name or ip.
        required: true
      state_enabled:
        description:
          - disables/enables ntp server.
        default: no
        choices: ['yes', 'no']
      version:
        description:
          - version number for the ntp peer.
        choices: ['3', '4']
      key_id:
         description:
             - Used to configure the key-id for the ntp peer
      delete:
         description:
             - Used to decide if you want to delete given peer or not.
         default: no
         choices: ['yes', 'no']
 ntp_servers:
    description:
      - List of ntp servers.
    suboptions:
      ip_or_name:
        description:
          - Configures the name or ip of the ntp server.
        required: true
      state_enabled:
        description:
          - disables/enables ntp server.
         default: no
         choices: ['yes', 'no']
      version:
        description:
          - version number for the ntp server.
        choices: ['3', '4']
      trusted_enable:
         description:
             - Enables/Disables the trusted state for the ntp server
         default: no
         choices: ['yes', 'no']
      key_id:
         description:
             - Used to configure the key-id for the ntp server
      delete:
         description:
             - Used to decide if you want to delete given server or not.
         default: no
         choices: ['yes', 'no']
 ntpdate:
    description:
      - Sets system clock once from a remote server using NTP.

"""

EXAMPLES = """
- name: configure NTP peers and servers
  onyx_ntp_peers_servers:
    peers:
       - ip_or_name: 1.1.1.1
         state_enabled: yes
         version: 4
         key_id: 6
         delete: yes
    serevrs:
       - ip_or_name: 2.2.2.2
         state_enabled: yes
         version: 3
         key_id: 8
         trusted_enable: no
         delete: yes
    ntpdate: 192.168.10.10
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - ntp peer 1.1.1.1 disable
      no ntp peer 1.1.1.1 disable
      ntp peer 1.1.1.1 keyId 6
      ntp peer 1.1.1.1 version 4
      no ntp peer 1.1.1.1
      ntp server 2.2.2.2 disable
      no ntp server 2.2.2.2 disable
      ntp server 2.2.2.2 keyID 8
      ntp server 2.2.2.2 version 3
      ntp server 2.2.2.2 trusted-enable
      no ntp server 2.2.2.2
      ntp server 192.168.10.10
      ntpdate 192.168.10.10
"""

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import remove_default_spec

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxNTPServersPeersModule(BaseOnyxModule):

    def init_module(self):
        """ module initialization
        """
        peer_spec = dict(ip_or_name=dict(required=True),
                         state_enabled=dict(choices=['yes', 'no']),
                         version=dict(type='int', choices=[3, 4]),
                         key_id=dict(type='int'),
                         delete=dict(choices=['yes', 'no']))
        server_spec = dict(ip_or_name=dict(required=True),
                           state_enabled=dict(choices=['yes', 'no']),
                           version=dict(type='int', choices=[3, 4]),
                           trusted_enable=dict(choices=['yes', 'no']),
                           key_id=dict(type='int'),
                           delete=dict(choices=['yes', 'no']))
        element_spec = dict(peers=dict(type='list', elements='dict', options=peer_spec),
                            servers=dict(type='list', elements='dict', options=server_spec),
                            ntpdate=dict())
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def _show_peers_servers_config(self):
        cmd = "show ntp configured"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def _set_servers_config(self, peers_servers_config):
        servers = dict()
        peers = dict()
        if not peers_servers_config:
            return
        index = 0
        for peer_server in peers_servers_config:
            if (index == 0):
                index += 1
                continue
            else:
                header_list = peer_server.get("header").split(" ")
                type = header_list[1]
                if (type == 'server'):
                    server_entry = {"version": peer_server.get("NTP version"),
                                    "state_enabled": peer_server.get("Enabled"),
                                    "trusted_enable": peer_server.get("Trusted"),
                                    "key_id": peer_server.get("Key ID")}
                    servers.update({header_list[2]: server_entry})
                else:
                    peer_entry = {"version": peer_server.get("NTP version"),
                                  "state_enabled": peer_server.get("Enabled"),
                                  "key_id": peer_server.get("Key ID")}
                    peers.update({header_list[2]: peer_entry})
            index += 1
            self._current_config.update({"servers": servers})
            self._current_config.update({"peers": peers})

    def load_current_config(self):
        self._current_config = dict()
        peers_servers_config = self._show_peers_servers_config()
        if peers_servers_config:
            self._set_servers_config(peers_servers_config)

    def generate_commands(self):
        ntp_options = ["peers", "servers"]
        for option in ntp_options:
            option_name = "peer"
            if option == "servers":
                option_name = "server"
            req_ntp = self._required_config.get(option)
            if req_ntp is not None:
                for ntp_peer in req_ntp:
                    curr_name = None
                    if self._current_config:
                        curr_name = self._current_config.get(option).get(ntp_peer.get("ip_or_name"))
                        if curr_name:
                            if ntp_peer.get("delete"):
                                if(ntp_peer.get("delete") == "yes"):
                                    self._commands.append('no ntp {0} {1}' .format(option_name, ntp_peer.get('ip_or_name')))
                                    continue
                            if ntp_peer.get("state_enabled"):
                                if (curr_name.get("state_enabled") != ntp_peer.get("state_enabled")):
                                    if(ntp_peer.get("state_enabled") == "yes"):
                                        self._commands.append('no ntp {0} {1} disable' .format(option_name, ntp_peer.get('ip_or_name')))
                                    else:
                                        self._commands.append('ntp {0} {1} disable'  .format(option_name, ntp_peer.get('ip_or_name')))
                            if ntp_peer.get("version"):
                                if (int(curr_name.get("version")) != ntp_peer.get("version")):
                                    self._commands.append('ntp {0} {1} version {2}'  .format(option_name, ntp_peer.get('ip_or_name'), ntp_peer.get('version')))
                            if ntp_peer.get("key_id"):
                                if curr_name.get("key_id") != "none":
                                    if (int(curr_name.get("key_id")) != ntp_peer.get("key_id")):
                                        self._commands.append('ntp {0} {1} keyID {2}'  .format(option_name, ntp_peer.get('ip_or_name'), ntp_peer.get('key_id')))
                                else:
                                    self._commands.append('ntp {0} {1} keyID {2}'  .format(option_name, ntp_peer.get('ip_or_name'), ntp_peer.get('key_id')))
                            if option_name == "server":
                                if ntp_peer.get("trusted_enable"):
                                    if (curr_name.get("trusted_enable") != ntp_peer.get("trusted_enable")):
                                        if ntp_peer.get("trusted_enable") == "yes":
                                            self._commands.append('ntp {0} {1} trusted-enable'  .format(option_name, ntp_peer.get('ip_or_name')))
                                        else:
                                            self._commands.append('no ntp {0} {1} trusted-enable'  .format(option_name, ntp_peer.get('ip_or_name')))
                    else:
                        if ntp_peer.get("delete"):
                            if(ntp_peer.get("delete") == "yes"):
                                continue
                        if ntp_peer.get("state_enabled"):
                            if(ntp_peer.get("state_enabled") == "yes"):
                                self._commands.append('no ntp {0} {1} disable' .format(option_name, ntp_peer.get('ip_or_name')))
                            else:
                                self._commands.append('ntp {0} {1} disable'  .format(option_name, ntp_peer.get('ip_or_name')))
                        else:
                            self._commands.append('ntp {0} {1} disable'  .format(option_name, ntp_peer.get('ip_or_name')))
                        if ntp_peer.get("version"):
                            self._commands.append('ntp {0} {1} version {2}'  .format(option_name, ntp_peer.get('ip_or_name'), ntp_peer.get('version')))
                        if ntp_peer.get("key_id"):
                            self._commands.append('ntp {0} {1} keyID {2}'  .format(option_name, ntp_peer.get('ip_or_name'), ntp_peer.get('key_id')))

        ntpdate = self._required_config.get("ntpdate")
        if ntpdate is not None:
            self._commands.append('ntpdate {0}' .format(ntpdate))


def main():
    """ main entry point for module execution
    """
    OnyxNTPServersPeersModule.main()


if __name__ == '__main__':
    main()
