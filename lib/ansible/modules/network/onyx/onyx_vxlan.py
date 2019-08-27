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
module: onyx_vxlan
version_added: "2.8"
author: "Anas Badaha (@anasb)"
short_description: Configures Vxlan
description:
  - This module provides declarative management of Vxlan configuration
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX evpn_dev.031.
  - nve protocol must be enabled.
options:
  nve_id:
    description:
      - nve interface ID.
    required: true
  loopback_id:
    description:
      - loopback interface ID.
  bgp:
    description:
      - configure bgp on nve interface.
    type: bool
    default: true
  mlag_tunnel_ip:
    description:
      - vxlan Mlag tunnel IP
  vni_vlan_list:
    description:
      - Each item in the list has two attributes vlan_id, vni_id.
  arp_suppression:
    description:
      - A flag telling if to configure arp suppression.
    type: bool
    default: false
"""

EXAMPLES = """
- name: configure Vxlan
  onyx_vxlan:
    nve_id: 1
    loopback_id: 1
    bgp: yes
    mlag-tunnel-ip: 100.0.0.1
    vni_vlan_list:
      - vlan_id: 10
        vni_id: 10010
      - vlan_id: 6
        vni_id: 10060
    arp_suppression: yes
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface nve 1
    - interface nve 1 vxlan source interface loopback 1
    - interface nve 1 nve controller bgp
    - interface nve 1 vxlan mlag-tunnel-ip 100.0.0.1
    - interface nve 1 nve vni 10010 vlan 10
    - interface nve 1 nve vni 10060 vlan 6
    - interface nve 1 nve neigh-suppression
    - interface vlan 6
    - interface vlan 10
"""

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxVxlanModule(BaseOnyxModule):

    LOOPBACK_REGEX = re.compile(r'^loopback (\d+).*')
    NVE_ID_REGEX = re.compile(r'^Interface NVE (\d+).*')

    def init_module(self):
        """ initialize module
        """
        vni_vlan_spec = dict(vlan_id=dict(type=int),
                             vni_id=dict(type=int))
        element_spec = dict(
            nve_id=dict(type=int),
            loopback_id=dict(type=int),
            bgp=dict(default=True, type='bool'),
            mlag_tunnel_ip=dict(type='str'),
            vni_vlan_list=dict(type='list',
                               elements='dict',
                               options=vni_vlan_spec),
            arp_suppression=dict(default=False, type='bool')
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def _set_vxlan_config(self, vxlan_config):
        vxlan_config = vxlan_config[0]
        if not vxlan_config:
            return
        nve_header = vxlan_config.get("header")
        match = self.NVE_ID_REGEX.match(nve_header)
        if match:
            current_nve_id = int(match.group(1))
            self._current_config['nve_id'] = current_nve_id
            if int(current_nve_id) != self._required_config.get("nve_id"):
                return

        self._current_config['mlag_tunnel_ip'] = vxlan_config.get("Mlag tunnel IP")
        controller_mode = vxlan_config.get("Controller mode")
        if controller_mode == "BGP":
            self._current_config['bgp'] = True
        else:
            self._current_config['bgp'] = False

        loopback_str = vxlan_config.get("Source interface")
        match = self.LOOPBACK_REGEX.match(loopback_str)
        if match:
            loopback_id = match.group(1)
            self._current_config['loopback_id'] = int(loopback_id)

        self._current_config['global_neigh_suppression'] = vxlan_config.get("Global Neigh-Suppression")

        vni_vlan_mapping = self._current_config['vni_vlan_mapping'] = dict()
        nve_detail = self._show_nve_detail()

        if nve_detail is not None:
            nve_detail = nve_detail[0]

            if nve_detail:
                for vlan_id in nve_detail:
                    vni_vlan_mapping[int(vlan_id)] = dict(
                        vni_id=int(nve_detail[vlan_id][0].get("VNI")),
                        arp_suppression=nve_detail[vlan_id][0].get("Neigh Suppression"))

    def _show_vxlan_config(self):
        cmd = "show interfaces nve"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def _show_nve_detail(self):
        cmd = "show interface nve {0} detail".format(self._required_config.get("nve_id"))
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        vxlan_config = self._show_vxlan_config()
        if vxlan_config:
            self._set_vxlan_config(vxlan_config)

    def generate_commands(self):
        nve_id = self._required_config.get("nve_id")
        current_nve_id = self._current_config.get("nve_id")

        if current_nve_id is None:
            self._add_nve_commands(nve_id)
        elif current_nve_id != nve_id:
            self._add_no_nve_commands(current_nve_id)
            self._add_nve_commands(nve_id)

        bgp = self._required_config.get("bgp")
        if bgp is not None:
            curr_bgp = self._current_config.get("bgp")
            if bgp and bgp != curr_bgp:
                self._commands.append('interface nve {0} nve controller bgp'.format(nve_id))

        loopback_id = self._required_config.get("loopback_id")
        if loopback_id is not None:
            curr_loopback_id = self._current_config.get("loopback_id")
            if loopback_id != curr_loopback_id:
                self._commands.append('interface nve {0} vxlan source interface '
                                      'loopback {1} '.format(nve_id, loopback_id))

        mlag_tunnel_ip = self._required_config.get("mlag_tunnel_ip")
        if mlag_tunnel_ip is not None:
            curr_mlag_tunnel_ip = self._current_config.get("mlag_tunnel_ip")
            if mlag_tunnel_ip != curr_mlag_tunnel_ip:
                self._commands.append('interface nve {0} vxlan '
                                      'mlag-tunnel-ip {1}'.format(nve_id, mlag_tunnel_ip))

        vni_vlan_list = self._required_config.get("vni_vlan_list")
        arp_suppression = self._required_config.get("arp_suppression")
        if vni_vlan_list is not None:
            self._generate_vni_vlan_cmds(vni_vlan_list, nve_id, arp_suppression)

    def _generate_vni_vlan_cmds(self, vni_vlan_list, nve_id, arp_suppression):

        current_global_arp_suppression = self._current_config.get('global_neigh_suppression')
        if arp_suppression is True and current_global_arp_suppression != "Enable":
            self._commands.append('interface nve {0} nve neigh-suppression'.format(nve_id))

        current_vni_vlan_mapping = self._current_config.get('vni_vlan_mapping')
        if current_vni_vlan_mapping is None:
            for vni_vlan in vni_vlan_list:
                vlan_id = vni_vlan.get("vlan_id")
                vni_id = vni_vlan.get("vni_id")
                self._add_vni_vlan_cmds(nve_id, vni_id, vlan_id)
                self._add_arp_suppression_cmds(arp_suppression, vlan_id)
        else:
            for vni_vlan in vni_vlan_list:
                vlan_id = vni_vlan.get("vlan_id")
                vni_id = vni_vlan.get("vni_id")

                currt_vlan_id = current_vni_vlan_mapping.get(vlan_id)

                if currt_vlan_id is None:
                    self._add_vni_vlan_cmds(nve_id, vni_id, vlan_id)
                    self._add_arp_suppression_cmds(arp_suppression, vlan_id)
                else:
                    current_vni_id = currt_vlan_id.get("vni_id")
                    current_arp_suppression = currt_vlan_id.get("arp_suppression")

                    if int(current_vni_id) != vni_id:
                        self._add_vni_vlan_cmds(nve_id, vni_id, vlan_id)

                    if current_arp_suppression == "Disable":
                        self._add_arp_suppression_cmds(arp_suppression, vlan_id)

    def _add_no_nve_commands(self, current_nve_id):
        self._commands.append('no interface nve {0}'.format(current_nve_id))

    def _add_nve_commands(self, nve_id):
        self._commands.append('interface nve {0}'.format(nve_id))
        self._commands.append('exit')

    def _add_vni_vlan_cmds(self, nve_id, vni_id, vlan_id):
        self._commands.append('interface nve {0} nve vni {1} '
                              'vlan {2}'.format(nve_id, vni_id, vlan_id))

    def _add_arp_suppression_cmds(self, arp_suppression, vlan_id):
        if arp_suppression is True:
            self._commands.append('interface vlan {0}'.format(vlan_id))
            self._commands.append('exit')


def main():
    """ main entry point for module execution
    """
    OnyxVxlanModule.main()


if __name__ == '__main__':
    main()
