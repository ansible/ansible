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
module: onyx_bgp
version_added: "2.5"
author: "Samer Deeb (@samerd), Anas Badaha (@anasb)"
short_description: Configures BGP on Mellanox ONYX network devices
description:
  - This module provides declarative management of BGP router and neighbors
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.4000
options:
  as_number:
    description:
      - Local AS number.
    required: true
  router_id:
    description:
      - Router IP address.
  neighbors:
    description:
      - List of neighbors. Required if I(state=present).
    suboptions:
      remote_as:
        description:
          - Remote AS number.
        required: true
      neighbor:
        description:
          - Neighbor IP address.
        required: true
      multihop:
        description:
          - multihop number.
  networks:
    description:
      - List of advertised networks.
  fast_external_fallover:
    description:
      - will configure fast_external_fallover when it is True.
    type: bool
    version_added: 2.9
  max_paths:
    description:
      - Maximum bgp paths.
    version_added: 2.9
  ecmp_bestpath:
    description:
      - Enables ECMP across AS paths.
    type: bool
    version_added: 2.9
  evpn:
    description:
      - Configure evpn peer-group.
    type: bool
    version_added: 2.9
  vrf:
    description:
      - vrf name.
    version_added: 2.9
  state:
    description:
      - BGP state.
    default: present
    choices: ['present', 'absent']
  purge:
    description:
      - will remove all neighbors when it is True.
    type: bool
    default: false
    version_added: 2.8
"""

EXAMPLES = """
- name: configure bgp
  onyx_bgp:
    as_number: 320
    router_id: 10.3.3.3
    neighbors:
      - remote_as: 321
        neighbor: 10.3.3.4
      - remote_as: 322
        neighbor: 10.3.3.5
        multihop: 250
    purge: True
    state: present
    networks:
      - 172.16.1.0/24
    vrf: default
    evpn: yes
    fast_external_fallover: yes
    max_paths: 32
    ecmp_bestpath: yes

"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - router bgp 320 vrf default
    - exit
    - router bgp 320 router-id 10.3.3.3 force
    - router bgp 320 vrf default bgp fast-external-fallover
    - router bgp 320 vrf default maximum-paths 32
    - router bgp 320 vrf default bestpath as-path multipath-relax force
    - router bgp 320 vrf default neighbor evpn peer-group
    - router bgp 320 vrf default neighbor evpn send-community extended
    - router bgp 320 vrf default address-family l2vpn-evpn neighbor evpn next-hop-unchanged
    - router bgp 320 vrf default address-family l2vpn-evpn neighbor evpn activate
    - router bgp 320 vrf default address-family l2vpn-evpn auto-create
    - router bgp 320 vrf default neighbor 10.3.3.4 remote-as 321
    - router bgp 320 vrf default neighbor 10.3.3.4 ebgp-multihop 250
    - router bgp 320 vrf default neighbor 10.3.3.5 remote-as 322
    - router bgp 320 vrf default network 172.16.1.0 /24
"""
import re
from ansible.module_utils.six import iteritems

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import get_bgp_summary
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxBgpModule(BaseOnyxModule):
    LOCAL_AS_REGEX = re.compile(r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+).*')
    ROUTER_ID_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+).*router-id\s+(\S+)\s+.*')
    NEIGHBOR_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+).*neighbor\s+(\S+)\s+remote\-as\s+(\d+).*')
    NEIGHBOR_MULTIHOP_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+).*neighbor\s+(\S+)\s+ebgp\-multihop\s+(\d+).*')
    NETWORK_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+).*network\s+(\S+)\s+(\S+).*')
    FAST_EXTERNAL_FALLOVER_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+bgp fast\-external\-fallover.*')
    MAX_PATHS_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+maximum\-paths\s+(\d+).*')
    ECMP_BESTPATH_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+bestpath as\-path multipath\-relax.*')
    NEIGHBOR_EVPN_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+neighbor\s+(\S+)\s+peer\-group evpn.*')
    EVPN_PEER_GROUP_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+neighbor evpn peer\-group.*')
    EVPN_SEND_COMMUNITY_EXTENDED_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+neighbor evpn send-community extended.*')
    EVPN_NEXT_HOP_UNCHANGED_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+address\-family l2vpn\-evpn neighbor evpn next\-hop-unchanged.*')
    EVPN_ACTIVATE_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+address-family l2vpn\-evpn neighbor evpn activate.*')
    EVPN_AUTO_CREATE_REGEX = re.compile(
        r'^\s.*router bgp\s+(\d+)\s+vrf\s+(\S+)\s+address-family l2vpn\-evpn auto-create.*')

    _purge = False

    EVPN_PEER_GROUP_ATTR = "evpn_peer_group"
    EVPN_SEND_COMMUNITY_EXTENDED_ATTR = "evpn_send_community_extended"
    EVPN_NEXT_HOP_UNCHANGED_ATTR = "evpn_next_hop_unchanged"
    EVPN_ACTIVATE_ATTR = "evpn_activate"
    EVPN_AUTO_CREATE_ATTR = "evpn_auto_create"

    EVPN_PEER_GROUP_CMD = "router bgp %s vrf %s neighbor evpn peer-group"
    EVPN_SEND_COMMUNITY_EXTENDED_CMD = "router bgp %s vrf %s neighbor evpn send-community extended"
    EVPN_NEXT_HOP_UNCHANGED_CMD = "router bgp %s vrf %s address-family l2vpn-evpn neighbor evpn next-hop-unchanged"
    EVPN_ACTIVATE_CMD = "router bgp %s vrf %s address-family l2vpn-evpn neighbor evpn activate"
    EVPN_AUTO_CREATE_CMD = "router bgp %s vrf %s address-family l2vpn-evpn auto-create"

    EVPN_ENABLE_ATTRS = [EVPN_PEER_GROUP_ATTR, EVPN_SEND_COMMUNITY_EXTENDED_ATTR,
                         EVPN_NEXT_HOP_UNCHANGED_ATTR, EVPN_ACTIVATE_ATTR, EVPN_AUTO_CREATE_ATTR]

    EVPN_DISABLE_ATTRS = [EVPN_PEER_GROUP_ATTR, EVPN_AUTO_CREATE_ATTR]

    EVPN_COMMANDS_REGEX_MAPPER = {
        EVPN_PEER_GROUP_ATTR: (EVPN_PEER_GROUP_REGEX, EVPN_PEER_GROUP_CMD),
        EVPN_SEND_COMMUNITY_EXTENDED_ATTR: (EVPN_SEND_COMMUNITY_EXTENDED_REGEX,
                                            EVPN_SEND_COMMUNITY_EXTENDED_CMD),
        EVPN_NEXT_HOP_UNCHANGED_ATTR: (EVPN_NEXT_HOP_UNCHANGED_REGEX,
                                       EVPN_NEXT_HOP_UNCHANGED_CMD),
        EVPN_ACTIVATE_ATTR: (EVPN_ACTIVATE_REGEX, EVPN_ACTIVATE_CMD),
        EVPN_AUTO_CREATE_ATTR: (EVPN_AUTO_CREATE_REGEX, EVPN_AUTO_CREATE_CMD)
    }

    def init_module(self):
        """ initialize module
        """
        neighbor_spec = dict(
            remote_as=dict(type='int', required=True),
            neighbor=dict(required=True),
            multihop=dict(type='int')
        )
        element_spec = dict(
            as_number=dict(type='int', required=True),
            router_id=dict(),
            neighbors=dict(type='list', elements='dict',
                           options=neighbor_spec),
            networks=dict(type='list', elements='str'),
            state=dict(choices=['present', 'absent'], default='present'),
            purge=dict(default=False, type='bool'),
            vrf=dict(),
            fast_external_fallover=dict(type='bool'),
            max_paths=dict(type='int'),
            ecmp_bestpath=dict(type='bool'),
            evpn=dict(type='bool')
        )
        argument_spec = dict()

        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self._purge = self._required_config.get('purge', False)
        self.validate_param_values(self._required_config)

    def _set_bgp_config(self, bgp_config):
        lines = bgp_config.split('\n')
        self._current_config['router_id'] = None
        self._current_config['as_number'] = None
        self._current_config['fast_external_fallover'] = False
        self._current_config['ecmp_bestpath'] = False
        self._current_config[self.EVPN_PEER_GROUP_ATTR] = False
        self._current_config[self.EVPN_SEND_COMMUNITY_EXTENDED_ATTR] = False
        self._current_config[self.EVPN_NEXT_HOP_UNCHANGED_ATTR] = False
        self._current_config[self.EVPN_AUTO_CREATE_ATTR] = False
        self._current_config[self.EVPN_ACTIVATE_ATTR] = False
        neighbors = self._current_config['neighbors'] = dict()
        networks = self._current_config['networks'] = list()
        for line in lines:
            if line.startswith('#'):
                continue
            if not self._current_config['as_number']:
                match = self.LOCAL_AS_REGEX.match(line)
                if match:
                    self._current_config['as_number'] = int(match.group(1))
                    self._current_config['vrf'] = match.group(2)
                    continue
            if not self._current_config['router_id']:
                match = self.ROUTER_ID_REGEX.match(line)
                if match:
                    self._current_config['router_id'] = match.group(2)
                    continue
            match = self.NEIGHBOR_REGEX.match(line)
            if match:
                neighbor = neighbors.setdefault(match.group(2), dict())
                neighbor['remote_as'] = int(match.group(3))
                continue
            match = self.NEIGHBOR_MULTIHOP_REGEX.match(line)
            if match:
                neighbor = neighbors.setdefault(match.group(2), dict())
                neighbor["multihop"] = int(match.group(3))
                continue
            match = self.NEIGHBOR_EVPN_REGEX.match(line)
            if match:
                neighbor = neighbors.setdefault(match.group(3), dict())
                neighbor["evpn"] = True
                continue
            match = self.NETWORK_REGEX.match(line)
            if match:
                network = match.group(2) + match.group(3)
                networks.append(network)
                continue
            match = self.FAST_EXTERNAL_FALLOVER_REGEX.match(line)
            if match:
                self._current_config['fast_external_fallover'] = True
                continue
            match = self.ECMP_BESTPATH_REGEX.match(line)
            if match:
                self._current_config['ecmp_bestpath'] = True
                continue
            match = self.MAX_PATHS_REGEX.match(line)
            if match:
                self._current_config['max_paths'] = int(match.group(3))
                continue
            for key, value in iteritems(self.EVPN_COMMANDS_REGEX_MAPPER):
                match = value[0].match(line)
                if match:
                    self._current_config[key] = True
                    break

    def _get_bgp_summary(self):
        return get_bgp_summary(self._module)

    def load_current_config(self):
        self._current_config = dict()
        bgp_config = self._get_bgp_summary()
        if bgp_config:
            self._set_bgp_config(bgp_config)

    def generate_commands(self):
        state = self._required_config['state']
        if state == 'present':
            self._generate_bgp_cmds()
        else:
            self._generate_no_bgp_cmds()

    def _generate_bgp_cmds(self):
        vrf = self._required_config.get('vrf')
        if vrf is None:
            vrf = "default"

        as_number = self._required_config['as_number']
        curr_as_num = self._current_config.get('as_number')
        curr_vrf = self._current_config.get("vrf")
        bgp_removed = False
        if curr_as_num != as_number or vrf != curr_vrf:
            if curr_as_num:
                self._commands.append('no router bgp %d vrf %s' % (curr_as_num, curr_vrf))
                bgp_removed = True
            self._commands.append('router bgp %d vrf %s' % (as_number, vrf))
            self._commands.append('exit')

        req_router_id = self._required_config.get('router_id')
        if req_router_id is not None:
            curr_route_id = self._current_config.get('router_id')
            if bgp_removed or req_router_id != curr_route_id:
                self._commands.append('router bgp %d vrf %s router-id %s force' % (as_number, vrf, req_router_id))

        fast_external_fallover = self._required_config.get('fast_external_fallover')
        if fast_external_fallover is not None:
            current_fast_external_fallover = self._current_config.get('fast_external_fallover')
            if fast_external_fallover and (bgp_removed or fast_external_fallover != current_fast_external_fallover):
                self._commands.append('router bgp %d vrf %s bgp fast-external-fallover' % (as_number, vrf))
            elif not fast_external_fallover and (bgp_removed or fast_external_fallover != current_fast_external_fallover):
                self._commands.append('router bgp %d vrf %s no bgp fast-external-fallover' % (as_number, vrf))

        max_paths = self._required_config.get('max_paths')
        if max_paths is not None:
            current_max_paths = self._current_config.get('max_paths')
            if bgp_removed or max_paths != current_max_paths:
                self._commands.append('router bgp %d vrf %s maximum-paths %s' % (as_number, vrf, max_paths))

        ecmp_bestpath = self._required_config.get('ecmp_bestpath')
        if ecmp_bestpath is not None:
            current_ecmp_bestpath = self._current_config.get('ecmp_bestpath')
            if ecmp_bestpath and (bgp_removed or ecmp_bestpath != current_ecmp_bestpath):
                self._commands.append('router bgp %d vrf %s bestpath as-path multipath-relax force' % (as_number, vrf))
            elif not ecmp_bestpath and (bgp_removed or ecmp_bestpath != current_ecmp_bestpath):
                self._commands.append('router bgp %d vrf %s no bestpath as-path multipath-relax force' % (as_number, vrf))

        evpn = self._required_config.get('evpn')
        if evpn is not None:
            self._generate_evpn_cmds(evpn, as_number, vrf)

        self._generate_neighbors_cmds(as_number, vrf, bgp_removed)
        self._generate_networks_cmds(as_number, vrf, bgp_removed)

    def _generate_neighbors_cmds(self, as_number, vrf, bgp_removed):
        req_neighbors = self._required_config['neighbors']
        curr_neighbors = self._current_config.get('neighbors', {})
        evpn = self._required_config.get('evpn')
        if self._purge:
            for neighbor in curr_neighbors:
                remote_as = curr_neighbors[neighbor].get("remote_as")
                self._commands.append('router bgp %s vrf %s no neighbor %s remote-as %s' % (
                    as_number, vrf, neighbor, remote_as))

        if req_neighbors is not None:
            for neighbor_data in req_neighbors:
                neighbor = neighbor_data.get("neighbor")
                curr_neighbor = curr_neighbors.get(neighbor)
                remote_as = neighbor_data.get("remote_as")
                multihop = neighbor_data.get("multihop")
                if bgp_removed or curr_neighbor is None:
                    if remote_as is not None:
                        self._commands.append(
                            'router bgp %s vrf %s neighbor %s remote-as %s' % (as_number, vrf, neighbor, remote_as))
                    if multihop is not None:
                        self._commands.append(
                            'router bgp %s vrf %s neighbor %s ebgp-multihop %s' % (as_number, vrf, neighbor, multihop))
                    if evpn:
                        self._commands.append(
                            'router bgp %s vrf %s neighbor %s peer-group evpn' % (as_number, vrf, neighbor))
                elif curr_neighbor is not None:
                    curr_remote_as = curr_neighbor.get("remote_as")
                    curr_multihop = curr_neighbor.get("multihop")
                    curr_neighbor_evpn = curr_neighbor.get("evpn")
                    if remote_as != curr_remote_as:
                        self._commands.append(
                            'router bgp %s vrf %s neighbor %s remote-as %s' % (as_number, vrf, neighbor, remote_as))
                    if multihop is not None and multihop != curr_multihop:
                        self._commands.append(
                            'router bgp %s vrf %s neighbor %s ebgp-multihop %s' % (as_number, vrf, neighbor, multihop))
                    if evpn and curr_neighbor_evpn is not True:
                        self._commands.append(
                            'router bgp %s vrf %s neighbor %s peer-group evpn' % (as_number, vrf, neighbor))

    def _generate_networks_cmds(self, as_number, vrf, bgp_removed):
        req_networks = self._required_config['networks'] or []
        curr_networks = self._current_config.get('networks', [])
        if not bgp_removed:
            for network in curr_networks:
                if network not in req_networks:
                    net_attrs = network.split('/')
                    if len(net_attrs) != 2:
                        self._module.fail_json(
                            msg='Invalid network %s' % network)

                    net_address, netmask = net_attrs
                    cmd = 'router bgp %s no network %s /%s' % (
                        as_number, net_address, netmask)
                    self._commands.append(cmd)

        for network in req_networks:
            if bgp_removed or network not in curr_networks:
                net_attrs = network.split('/')
                if len(net_attrs) != 2:
                    self._module.fail_json(
                        msg='Invalid network %s' % network)
                net_address, netmask = net_attrs
                cmd = 'router bgp %s vrf %s network %s /%s' % (
                    as_number, vrf, net_address, netmask)
                self._commands.append(cmd)

    def _generate_no_bgp_cmds(self):
        as_number = self._required_config['as_number']
        curr_as_num = self._current_config.get('as_number')
        if curr_as_num and curr_as_num == as_number:
            self._commands.append('no router bgp %d' % as_number)

    def _generate_evpn_cmds(self, evpn, as_number, vrf):
        if evpn:
            for attr in self.EVPN_ENABLE_ATTRS:
                curr_attr = self._current_config.get(attr)
                if curr_attr is not True:
                    self._commands.append(self.EVPN_COMMANDS_REGEX_MAPPER.get(attr)[1] % (as_number, vrf))
        elif not evpn:
            for attr in self.EVPN_DISABLE_ATTRS:
                curr_attr = self._current_config.get(attr)
                if curr_attr is not False:
                    self._commands.append("no " + self.EVPN_COMMANDS_REGEX_MAPPER.get(attr)[1] % (as_number, vrf))


def main():
    """ main entry point for module execution
    """
    OnyxBgpModule.main()


if __name__ == '__main__':
    main()
