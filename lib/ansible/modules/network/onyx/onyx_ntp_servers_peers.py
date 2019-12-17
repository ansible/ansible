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
version_added: "2.10"
author: "Sara-Touqan (@sarato)"
short_description: Configures NTP peers and servers parameters
description:
  - This module provides declarative management of NTP peers and servers configuration on Mellanox ONYX network devices.
options:
  peer:
    type: list
    description:
      - List of ntp peers.
    suboptions:
      ip_or_name:
        description:
          - Configures ntp peer name or ip.
        required: true
        type: str
      enabled:
        description:
          - Disables/Enables ntp peer state
        type: bool
      version:
        description:
          - version number for the ntp peer
        choices: [3, 4]
        type: int
      key_id:
        description:
          - Used to configure the key-id for the ntp peer
        type: int
      state:
        description:
          - Indicates if the ntp peer exists or should be deleted
        choices: ['present', 'absent']
        type: str
  server:
    type: list
    description:
      - List of ntp servers.
    suboptions:
      ip_or_name:
        description:
          - Configures ntp server name or ip.
        required: true
        type: str
      enabled:
        description:
          - Disables/Enables ntp server
        type: bool
      trusted_enable:
        description:
          - Disables/Enables the trusted state for the ntp server.
        type: bool
      version:
        description:
          - version number for the ntp server
        choices: [3, 4]
        type: int
      key_id:
        description:
          - Used to configure the key-id for the ntp server
        type: int
      state:
        description:
          - Indicates if the ntp peer exists or should be deleted.
        choices: ['present', 'absent']
        type: str
  ntpdate:
    description:
      - Sets system clock once from a remote server using NTP.
    type: str
"""

EXAMPLES = """
- name: configure NTP peers and servers
  onyx_ntp_peers_servers:
    peer:
       - ip_or_name: 1.1.1.1
         enabled: yes
         version: 4
         key_id: 6
         state: present
    server:
       - ip_or_name: 2.2.2.2
         enabled: true
         version: 3
         key_id: 8
         trusted_enable: no
         state: present
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
                         enabled=dict(type='bool'),
                         version=dict(type='int', choices=[3, 4]),
                         key_id=dict(type='int'),
                         state=dict(choices=['present', 'absent']))
        server_spec = dict(ip_or_name=dict(required=True),
                           enabled=dict(type='bool'),
                           version=dict(type='int', choices=[3, 4]),
                           trusted_enable=dict(type='bool'),
                           key_id=dict(type='int'),
                           state=dict(choices=['present', 'absent']))
        element_spec = dict(peer=dict(type='list', elements='dict', options=peer_spec),
                            server=dict(type='list', elements='dict', options=server_spec),
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
                header_type = header_list[1]
                if peer_server.get("Enabled") == "yes":
                    enabled_state = True
                else:
                    enabled_state = False
                if (header_type == 'server'):
                    trusted_state = peer_server.get("Trusted")
                    if trusted_state == 'yes':
                        trusted_state = True
                    else:
                        trusted_state = False
                    server_entry = {"version": peer_server.get("NTP version"),
                                    "enabled": enabled_state,
                                    "trusted_enable": trusted_state,
                                    "key_id": peer_server.get("Key ID")}
                    servers[header_list[2]] = server_entry
                else:
                    peer_entry = {"version": peer_server.get("NTP version"),
                                  "enabled": enabled_state,
                                  "key_id": peer_server.get("Key ID")}
                    peers[header_list[2]] = peer_entry
            index += 1
            self._current_config = dict(server=servers,
                                        peer=peers)

    def load_current_config(self):
        servers = dict()
        peers = dict()
        self._current_config = dict(server=servers,
                                    peer=peers)
        peers_servers_config = self._show_peers_servers_config()
        if peers_servers_config:
            self._set_servers_config(peers_servers_config)

    def generate_commands(self):
        for option in self._current_config:
            req_ntp = self._required_config.get(option)
            if req_ntp is not None:
                for ntp_peer in req_ntp:
                    peer_name = ntp_peer.get('ip_or_name')
                    peer_key = ntp_peer.get('key_id')
                    peer_state = ntp_peer.get("state")
                    peer_enabled = ntp_peer.get("enabled")
                    peer_version = ntp_peer.get("version")
                    peer_key = ntp_peer.get("key_id")
                    curr_name = self._current_config.get(option).get(peer_name)
                    peer_version = ntp_peer.get('version')
                    if self._current_config.get(option) and curr_name:
                        if peer_state:
                            if(peer_state == "absent"):
                                self._commands.append('no ntp {0} {1}' .format(option, peer_name))
                                continue
                        if peer_enabled is not None:
                            if curr_name.get("enabled") != peer_enabled:
                                if(peer_enabled is True):
                                    self._commands.append('no ntp {0} {1} disable' .format(option, peer_name))
                                else:
                                    self._commands.append('ntp {0} {1} disable'  .format(option, peer_name))
                        if peer_version:
                            if (int(curr_name.get("version")) != peer_version):
                                self._commands.append('ntp {0} {1} version {2}'  .format(option, peer_name, peer_version))
                        if peer_key:
                            if curr_name.get("key_id") != "none":
                                if (int(curr_name.get("key_id")) != peer_key):
                                    self._commands.append('ntp {0} {1} keyID {2}'  .format(option, peer_name, peer_key))
                            else:
                                self._commands.append('ntp {0} {1} keyID {2}'  .format(option, peer_name, peer_key))
                        if option == "server":
                            server_trusted = ntp_peer.get("trusted_enable")
                            if server_trusted is not None:
                                if (curr_name.get("trusted_enable") != server_trusted):
                                    if server_trusted is True:
                                        self._commands.append('ntp {0} {1} trusted-enable'  .format(option, peer_name))
                                    else:
                                        self._commands.append('no ntp {0} {1} trusted-enable'  .format(option, peer_name))
                    else:
                        if peer_state:
                            if(peer_state == "absent"):
                                continue
                        if peer_enabled is not None:
                            if(peer_enabled is True):
                                self._commands.append('no ntp {0} {1} disable' .format(option, peer_name))
                            else:
                                self._commands.append('ntp {0} {1} disable'  .format(option, peer_name))
                        else:
                            self._commands.append('ntp {0} {1} disable'  .format(option, peer_name))
                        if peer_version:
                            self._commands.append('ntp {0} {1} version {2}'  .format(option, peer_name, peer_version))
                        if peer_key:
                            self._commands.append('ntp {0} {1} keyID {2}'  .format(option, peer_name, peer_key))

        ntpdate = self._required_config.get("ntpdate")
        if ntpdate is not None:
            self._commands.append('ntpdate {0}' .format(ntpdate))


def main():
    """ main entry point for module execution
    """
    OnyxNTPServersPeersModule.main()


if __name__ == '__main__':
    main()
