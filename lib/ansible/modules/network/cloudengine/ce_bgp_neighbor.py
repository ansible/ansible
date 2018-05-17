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
module: ce_bgp_neighbor
version_added: "2.4"
short_description: Manages BGP peer configuration on HUAWEI CloudEngine switches.
description:
    - Manages BGP peer configurations on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@CloudEngine-Ansible)
options:
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present','absent']
    vrf_name:
        description:
            - Name of a BGP instance. The name is a case-sensitive string of characters.
              The BGP instance can be used only after the corresponding VPN instance is created.
        required: true
    peer_addr:
        description:
            - Connection address of a peer, which can be an IPv4 or IPv6 address.
        required: true
    remote_as:
        description:
            - AS number of a peer.
              The value is a string of 1 to 11 characters.
        required: true
    description:
        description:
            - Description of a peer, which can be letters or digits.
              The value is a string of 1 to 80 characters.
    fake_as:
        description:
            - Fake AS number that is specified for a local peer.
              The value is a string of 1 to 11 characters.
    dual_as:
        description:
            - If the value is true, the EBGP peer can use either a fake AS number or the actual AS number.
              If the value is false, the EBGP peer can only use a fake AS number.
        choices: ['no_use','true','false']
        default: no_use
    conventional:
        description:
            - If the value is true, the router has all extended capabilities.
              If the value is false, the router does not have all extended capabilities.
        choices: ['no_use','true','false']
        default: no_use
    route_refresh:
        description:
            - If the value is true, BGP is enabled to advertise REFRESH packets.
              If the value is false, the route refresh function is enabled.
        choices: ['no_use','true','false']
        default: no_use
    is_ignore:
        description:
            - If the value is true, the session with a specified peer is torn down and all related
              routing entries are cleared.
              If the value is false, the session with a specified peer is retained.
        choices: ['no_use','true','false']
        default: no_use
    local_if_name:
        description:
            - Name of a source interface that sends BGP packets.
              The value is a string of 1 to 63 characters.
    ebgp_max_hop:
        description:
            - Maximum number of hops in an indirect EBGP connection.
              The value is an ranging from 1 to 255.
    valid_ttl_hops:
        description:
            - Enable GTSM on a peer or peer group.
              The valid-TTL-Value parameter is used to specify the number of TTL hops to be detected.
              The value is an integer ranging from 1 to 255.
    connect_mode:
        description:
            - The value can be Connect-only, Listen-only, or Both.
    is_log_change:
        description:
            - If the value is true, BGP is enabled to record peer session status and event information.
              If the value is false, BGP is disabled from recording peer session status and event information.
        choices: ['no_use','true','false']
        default: no_use
    pswd_type:
        description:
            - Enable BGP peers to establish a TCP connection and perform the Message Digest 5 (MD5)
              authentication for BGP messages.
        choices: ['null','cipher','simple']
    pswd_cipher_text:
        description:
            - The character string in a password identifies the contents of the password, spaces not supported.
              The value is a string of 1 to 255 characters.
    keep_alive_time:
        description:
            - Specify the Keepalive time of a peer or peer group.
              The value is an integer ranging from 0 to 21845. The default value is 60.
    hold_time:
        description:
            - Specify the Hold time of a peer or peer group.
              The value is 0 or an integer ranging from 3 to 65535.
    min_hold_time:
        description:
            - Specify the Min hold time of a peer or peer group.
    key_chain_name:
        description:
            - Specify the Keychain authentication name used when BGP peers establish a TCP connection.
              The value is a string of 1 to 47 case-insensitive characters.
    conn_retry_time:
        description:
            - ConnectRetry interval.
              The value is an integer ranging from 1 to 65535.
    tcp_MSS:
        description:
            - Maximum TCP MSS value used for TCP connection establishment for a peer.
              The value is an integer ranging from 176 to 4096.
    mpls_local_ifnet_disable:
        description:
            - If the value is true, peer create MPLS Local IFNET disable.
              If the value is false, peer create MPLS Local IFNET enable.
        choices: ['no_use','true','false']
        default: no_use
    prepend_global_as:
        description:
            - Add the global AS number to the Update packets to be advertised.
        choices: ['no_use','true','false']
        default: no_use
    prepend_fake_as:
        description:
            - Add the Fake AS number to received Update packets.
        choices: ['no_use','true','false']
        default: no_use
    is_bfd_block:
        description:
            - If the value is true, peers are enabled to inherit the BFD function from the peer group.
              If the value is false, peers are disabled to inherit the BFD function from the peer group.
        choices: ['no_use','true','false']
        default: no_use
    multiplier:
        description:
            - Specify the detection multiplier. The default value is 3.
              The value is an integer ranging from 3 to 50.
    is_bfd_enable:
        description:
            - If the value is true, BFD is enabled.
              If the value is false, BFD is disabled.
        choices: ['no_use','true','false']
        default: no_use
    rx_interval:
        description:
            - Specify the minimum interval at which BFD packets are received.
              The value is an integer ranging from 50 to 1000, in milliseconds.
    tx_interval:
        description:
            - Specify the minimum interval at which BFD packets are sent.
              The value is an integer ranging from 50 to 1000, in milliseconds.
    is_single_hop:
        description:
            - If the value is true, the system is enabled to preferentially use the single-hop mode for
              BFD session setup between IBGP peers.
              If the value is false, the system is disabled from preferentially using the single-hop
              mode for BFD session setup between IBGP peers.
        choices: ['no_use','true','false']
        default: no_use
'''

EXAMPLES = '''

- name: CloudEngine BGP neighbor test
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

  - name: "Config bgp peer"
    ce_bgp_neighbor:
      state: present
      vrf_name: js
      peer_addr: 192.168.10.10
      remote_as: 500
      provider: "{{ cli }}"

  - name: "Config bgp route id"
    ce_bgp_neighbor:
      state: absent
      vrf_name: js
      peer_addr: 192.168.10.10
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"peer_addr": "192.168.10.10", "remote_as": "500", "state": "present", "vrf_name": "js"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"bgp peer": []}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bgp peer": [["192.168.10.10", "500"]]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["peer 192.168.10.10 as-number 500"]
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec, check_ip_addr


# get bgp peer
CE_GET_BGP_PEER_HEADER = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpPeers>
                <bgpPeer>
                  <peerAddr></peerAddr>
"""
CE_GET_BGP_PEER_TAIL = """
                </bgpPeer>
              </bgpPeers>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </filter>
"""


# merge bgp peer
CE_MERGE_BGP_PEER_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpPeers>
                <bgpPeer operation="merge">
                  <peerAddr>%s</peerAddr>
"""
CE_MERGE_BGP_PEER_TAIL = """
                </bgpPeer>
              </bgpPeers>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# create bgp peer
CE_CREATE_BGP_PEER_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpPeers>
                <bgpPeer operation="create">
                  <peerAddr>%s</peerAddr>
"""
CE_CREATE_BGP_PEER_TAIL = """
                </bgpPeer>
              </bgpPeers>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# delete bgp peer
CE_DELETE_BGP_PEER_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpPeers>
                <bgpPeer operation="delete">
                  <peerAddr>%s</peerAddr>
"""
CE_DELETE_BGP_PEER_TAIL = """
                </bgpPeer>
              </bgpPeers>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# get peer bfd
CE_GET_PEER_BFD_HEADER = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpPeers>
                <bgpPeer>
                  <peerAddr>%s</peerAddr>
                  <peerBfd>
"""
CE_GET_PEER_BFD_TAIL = """
                  </peerBfd>
                </bgpPeer>
              </bgpPeers>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </filter>
"""

# merge peer bfd
CE_MERGE_PEER_BFD_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpPeers>
                <bgpPeer>
                  <peerAddr>%s</peerAddr>
                  <peerBfd operation="merge">
"""
CE_MERGE_PEER_BFD_TAIL = """
                  </peerBfd>
                </bgpPeer>
              </bgpPeers>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# delete peer bfd
CE_DELETE_PEER_BFD_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpPeers>
                <bgpPeer>
                  <peerAddr>%s</peerAddr>
                  <peerBfd operation="delete">
"""
CE_DELETE_PEER_BFD_TAIL = """
                  </peerBfd>
                </bgpPeer>
              </bgpPeers>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""


class BgpNeighbor(object):
    """ Manages BGP peer configuration """

    def netconf_get_config(self, **kwargs):
        """ netconf_get_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = get_nc_config(module, conf_str)

        return xml_str

    def netconf_set_config(self, **kwargs):
        """ netconf_set_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = set_nc_config(module, conf_str)

        return xml_str

    def check_bgp_peer_args(self, **kwargs):
        """ check_bgp_peer_args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='Error: The len of vrf_name %s is out of [1 - 31].' % vrf_name)

        peer_addr = module.params['peer_addr']
        if peer_addr:
            if not check_ip_addr(ipaddr=peer_addr):
                module.fail_json(
                    msg='Error: The peer_addr %s is invalid.' % peer_addr)

            need_cfg = True

        remote_as = module.params['remote_as']
        if remote_as:
            if len(remote_as) > 11 or len(remote_as) < 1:
                module.fail_json(
                    msg='Error: The len of remote_as %s is out of [1 - 11].' % remote_as)

            need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_peer_other_args(self, **kwargs):
        """ check_bgp_peer_other_args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='Error: The len of vrf_name %s is out of [1 - 31].' % vrf_name)

        description = module.params['description']
        if description:
            if len(description) > 80 or len(description) < 1:
                module.fail_json(
                    msg='Error: The len of description %s is out of [1 - 80].' % description)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<description></description>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<description>(.*)</description>.*', recv_xml)

                if re_find:
                    result["description"] = re_find
                    if re_find[0] != description:
                        need_cfg = True
                else:
                    need_cfg = True

        fake_as = module.params['fake_as']
        if fake_as:
            if len(fake_as) > 11 or len(fake_as) < 1:
                module.fail_json(
                    msg='Error: The len of fake_as %s is out of [1 - 11].' % fake_as)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<fakeAs></fakeAs>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<fakeAs>(.*)</fakeAs>.*', recv_xml)

                if re_find:
                    result["fake_as"] = re_find
                    if re_find[0] != fake_as:
                        need_cfg = True
                else:
                    need_cfg = True

        dual_as = module.params['dual_as']
        if dual_as != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<dualAs></dualAs>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<dualAs>(.*)</dualAs>.*', recv_xml)

                if re_find:
                    result["dual_as"] = re_find
                    if re_find[0] != fake_as:
                        need_cfg = True
                else:
                    need_cfg = True

        conventional = module.params['conventional']
        if conventional != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<conventional></conventional>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<conventional>(.*)</conventional>.*', recv_xml)

                if re_find:
                    result["conventional"] = re_find
                    if re_find[0] != conventional:
                        need_cfg = True
                else:
                    need_cfg = True

        route_refresh = module.params['route_refresh']
        if route_refresh != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<routeRefresh></routeRefresh>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeRefresh>(.*)</routeRefresh>.*', recv_xml)

                if re_find:
                    result["route_refresh"] = re_find
                    if re_find[0] != route_refresh:
                        need_cfg = True
                else:
                    need_cfg = True

        four_byte_as = module.params['four_byte_as']
        if four_byte_as != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<fourByteAs></fourByteAs>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<fourByteAs>(.*)</fourByteAs>.*', recv_xml)

                if re_find:
                    result["four_byte_as"] = re_find
                    if re_find[0] != four_byte_as:
                        need_cfg = True
                else:
                    need_cfg = True

        is_ignore = module.params['is_ignore']
        if is_ignore != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<isIgnore></isIgnore>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isIgnore>(.*)</isIgnore>.*', recv_xml)

                if re_find:
                    result["is_ignore"] = re_find
                    if re_find[0] != is_ignore:
                        need_cfg = True
                else:
                    need_cfg = True

        local_if_name = module.params['local_if_name']
        if local_if_name:
            if len(local_if_name) > 63 or len(local_if_name) < 1:
                module.fail_json(
                    msg='Error: The len of local_if_name %s is out of [1 - 63].' % local_if_name)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<localIfName></localIfName>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<localIfName>(.*)</localIfName>.*', recv_xml)

                if re_find:
                    result["local_if_name"] = re_find
                    if re_find[0] != local_if_name:
                        need_cfg = True
                else:
                    need_cfg = True

        ebgp_max_hop = module.params['ebgp_max_hop']
        if ebgp_max_hop:
            if int(ebgp_max_hop) > 255 or int(ebgp_max_hop) < 1:
                module.fail_json(
                    msg='Error: The value of ebgp_max_hop %s is out of [1 - 255].' % ebgp_max_hop)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<ebgpMaxHop></ebgpMaxHop>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ebgpMaxHop>(.*)</ebgpMaxHop>.*', recv_xml)

                if re_find:
                    result["ebgp_max_hop"] = re_find
                    if re_find[0] != ebgp_max_hop:
                        need_cfg = True
                else:
                    need_cfg = True

        valid_ttl_hops = module.params['valid_ttl_hops']
        if valid_ttl_hops:
            if int(valid_ttl_hops) > 255 or int(valid_ttl_hops) < 1:
                module.fail_json(
                    msg='Error: The value of valid_ttl_hops %s is out of [1 - 255].' % valid_ttl_hops)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<validTtlHops></validTtlHops>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<validTtlHops>(.*)</validTtlHops>.*', recv_xml)

                if re_find:
                    result["valid_ttl_hops"] = re_find
                    if re_find[0] != valid_ttl_hops:
                        need_cfg = True
                else:
                    need_cfg = True

        connect_mode = module.params['connect_mode']
        if connect_mode:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<connectMode></connectMode>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<connectMode>(.*)</connectMode>.*', recv_xml)

                if re_find:
                    result["connect_mode"] = re_find
                    if re_find[0] != connect_mode:
                        need_cfg = True
                else:
                    need_cfg = True

        is_log_change = module.params['is_log_change']
        if is_log_change != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<isLogChange></isLogChange>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isLogChange>(.*)</isLogChange>.*', recv_xml)

                if re_find:
                    result["is_log_change"] = re_find
                    if re_find[0] != is_log_change:
                        need_cfg = True
                else:
                    need_cfg = True

        pswd_type = module.params['pswd_type']
        if pswd_type:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<pswdType></pswdType>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<pswdType>(.*)</pswdType>.*', recv_xml)

                if re_find:
                    result["pswd_type"] = re_find
                    if re_find[0] != pswd_type:
                        need_cfg = True
                else:
                    need_cfg = True

        pswd_cipher_text = module.params['pswd_cipher_text']
        if pswd_cipher_text:
            if len(pswd_cipher_text) > 255 or len(pswd_cipher_text) < 1:
                module.fail_json(
                    msg='Error: The len of pswd_cipher_text %s is out of [1 - 255].' % pswd_cipher_text)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<pswdCipherText></pswdCipherText>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<pswdCipherText>(.*)</pswdCipherText>.*', recv_xml)

                if re_find:
                    result["pswd_cipher_text"] = re_find
                    if re_find[0] != pswd_cipher_text:
                        need_cfg = True
                else:
                    need_cfg = True

        keep_alive_time = module.params['keep_alive_time']
        if keep_alive_time:
            if int(keep_alive_time) > 21845 or len(keep_alive_time) < 0:
                module.fail_json(
                    msg='Error: The len of keep_alive_time %s is out of [0 - 21845].' % keep_alive_time)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<keepAliveTime></keepAliveTime>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<keepAliveTime>(.*)</keepAliveTime>.*', recv_xml)

                if re_find:
                    result["keep_alive_time"] = re_find
                    if re_find[0] != keep_alive_time:
                        need_cfg = True
                else:
                    need_cfg = True

        hold_time = module.params['hold_time']
        if hold_time:
            if int(hold_time) != 0 and (int(hold_time) > 65535 or int(hold_time) < 3):
                module.fail_json(
                    msg='Error: The value of hold_time %s is out of [0 or 3 - 65535].' % hold_time)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<holdTime></holdTime>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<holdTime>(.*)</holdTime>.*', recv_xml)

                if re_find:
                    result["hold_time"] = re_find
                    if re_find[0] != hold_time:
                        need_cfg = True
                else:
                    need_cfg = True

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            if int(min_hold_time) != 0 and (int(min_hold_time) > 65535 or int(min_hold_time) < 20):
                module.fail_json(
                    msg='Error: The value of min_hold_time %s is out of [0 or 20 - 65535].' % min_hold_time)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<minHoldTime></minHoldTime>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<minHoldTime>(.*)</minHoldTime>.*', recv_xml)

                if re_find:
                    result["min_hold_time"] = re_find
                    if re_find[0] != min_hold_time:
                        need_cfg = True
                else:
                    need_cfg = True

        key_chain_name = module.params['key_chain_name']
        if key_chain_name:
            if len(key_chain_name) > 47 or len(key_chain_name) < 1:
                module.fail_json(
                    msg='Error: The len of key_chain_name %s is out of [1 - 47].' % key_chain_name)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<keyChainName></keyChainName>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<keyChainName>(.*)</keyChainName>.*', recv_xml)

                if re_find:
                    result["key_chain_name"] = re_find
                    if re_find[0] != key_chain_name:
                        need_cfg = True
                else:
                    need_cfg = True

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            if int(conn_retry_time) > 65535 or int(conn_retry_time) < 1:
                module.fail_json(
                    msg='Error: The value of conn_retry_time %s is out of [1 - 65535].' % conn_retry_time)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<connRetryTime></connRetryTime>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<connRetryTime>(.*)</connRetryTime>.*', recv_xml)

                if re_find:
                    result["conn_retry_time"] = re_find
                    if re_find[0] != conn_retry_time:
                        need_cfg = True
                else:
                    need_cfg = True

        tcp_mss = module.params['tcp_MSS']
        if tcp_mss:
            if int(tcp_mss) > 4096 or int(tcp_mss) < 176:
                module.fail_json(
                    msg='Error: The value of tcp_mss %s is out of [176 - 4096].' % tcp_mss)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<tcpMSS></tcpMSS>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<tcpMSS>(.*)</tcpMSS>.*', recv_xml)

                if re_find:
                    result["tcp_MSS"] = re_find
                    if re_find[0] != tcp_mss:
                        need_cfg = True
                else:
                    need_cfg = True

        mpls_local_ifnet_disable = module.params['mpls_local_ifnet_disable']
        if mpls_local_ifnet_disable != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<mplsLocalIfnetDisable></mplsLocalIfnetDisable>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<mplsLocalIfnetDisable>(.*)</mplsLocalIfnetDisable>.*', recv_xml)

                if re_find:
                    result["mpls_local_ifnet_disable"] = re_find
                    if re_find[0] != mpls_local_ifnet_disable:
                        need_cfg = True
                else:
                    need_cfg = True

        prepend_global_as = module.params['prepend_global_as']
        if prepend_global_as != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<prependGlobalAs></prependGlobalAs>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<prependGlobalAs>(.*)</prependGlobalAs>.*', recv_xml)

                if re_find:
                    result["prepend_global_as"] = re_find
                    if re_find[0] != prepend_global_as:
                        need_cfg = True
                else:
                    need_cfg = True

        prepend_fake_as = module.params['prepend_fake_as']
        if prepend_fake_as != 'no_use':

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<prependFakeAs></prependFakeAs>" + CE_GET_BGP_PEER_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<prependFakeAs>(.*)</prependFakeAs>.*', recv_xml)

                if re_find:
                    result["prepend_fake_as"] = re_find
                    if re_find[0] != prepend_fake_as:
                        need_cfg = True
                else:
                    need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_peer_bfd_merge_args(self, **kwargs):
        """ check_peer_bfd_merge_args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        state = module.params['state']
        if state == "absent":
            result["need_cfg"] = need_cfg
            return result

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='Error: The len of vrf_name %s is out of [1 - 31].' % vrf_name)

        peer_addr = module.params['peer_addr']

        is_bfd_block = module.params['is_bfd_block']
        if is_bfd_block != 'no_use':

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isBfdBlock></isBfdBlock>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isBfdBlock>(.*)</isBfdBlock>.*', recv_xml)

                if re_find:
                    result["is_bfd_block"] = re_find
                    if re_find[0] != is_bfd_block:
                        need_cfg = True
                else:
                    need_cfg = True

        multiplier = module.params['multiplier']
        if multiplier:
            if int(multiplier) > 50 or int(multiplier) < 3:
                module.fail_json(
                    msg='Error: The value of multiplier %s is out of [3 - 50].' % multiplier)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<multiplier></multiplier>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<multiplier>(.*)</multiplier>.*', recv_xml)

                if re_find:
                    result["multiplier"] = re_find
                    if re_find[0] != multiplier:
                        need_cfg = True
                else:
                    need_cfg = True

        is_bfd_enable = module.params['is_bfd_enable']
        if is_bfd_enable != 'no_use':

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isBfdEnable></isBfdEnable>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isBfdEnable>(.*)</isBfdEnable>.*', recv_xml)

                if re_find:
                    result["is_bfd_enable"] = re_find
                    if re_find[0] != is_bfd_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        rx_interval = module.params['rx_interval']
        if rx_interval:
            if int(rx_interval) > 1000 or int(rx_interval) < 50:
                module.fail_json(
                    msg='Error: The value of rx_interval %s is out of [50 - 1000].' % rx_interval)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<rxInterval></rxInterval>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<rxInterval>(.*)</rxInterval>.*', recv_xml)

                if re_find:
                    result["rx_interval"] = re_find
                    if re_find[0] != rx_interval:
                        need_cfg = True
                else:
                    need_cfg = True

        tx_interval = module.params['tx_interval']
        if tx_interval:
            if int(tx_interval) > 1000 or int(tx_interval) < 50:
                module.fail_json(
                    msg='Error: The value of tx_interval %s is out of [50 - 1000].' % tx_interval)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<txInterval></txInterval>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<txInterval>(.*)</txInterval>.*', recv_xml)

                if re_find:
                    result["tx_interval"] = re_find
                    if re_find[0] != tx_interval:
                        need_cfg = True
                else:
                    need_cfg = True

        is_single_hop = module.params['is_single_hop']
        if is_single_hop != 'no_use':

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isSingleHop></isSingleHop>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isSingleHop>(.*)</isSingleHop>.*', recv_xml)

                if re_find:
                    result["is_single_hop"] = re_find
                    if re_find[0] != is_single_hop:
                        need_cfg = True
                else:
                    need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_peer_bfd_delete_args(self, **kwargs):
        """ check_peer_bfd_delete_args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        state = module.params['state']
        if state == "present":
            result["need_cfg"] = need_cfg
            return result

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='Error: The len of vrf_name %s is out of [1 - 31].' % vrf_name)

        peer_addr = module.params['peer_addr']

        is_bfd_block = module.params['is_bfd_block']
        if is_bfd_block != 'no_use':

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isBfdBlock></isBfdBlock>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<isBfdBlock>(.*)</isBfdBlock>.*', recv_xml)

                if re_find:
                    result["is_bfd_block"] = re_find
                    if re_find[0] == is_bfd_block:
                        need_cfg = True

        multiplier = module.params['multiplier']
        if multiplier:
            if int(multiplier) > 50 or int(multiplier) < 3:
                module.fail_json(
                    msg='Error: The value of multiplier %s is out of [3 - 50].' % multiplier)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<multiplier></multiplier>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<multiplier>(.*)</multiplier>.*', recv_xml)

                if re_find:
                    result["multiplier"] = re_find
                    if re_find[0] == multiplier:
                        need_cfg = True

        is_bfd_enable = module.params['is_bfd_enable']
        if is_bfd_enable != 'no_use':

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isBfdEnable></isBfdEnable>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<isBfdEnable>(.*)</isBfdEnable>.*', recv_xml)

                if re_find:
                    result["is_bfd_enable"] = re_find
                    if re_find[0] == is_bfd_enable:
                        need_cfg = True

        rx_interval = module.params['rx_interval']
        if rx_interval:
            if int(rx_interval) > 1000 or int(rx_interval) < 50:
                module.fail_json(
                    msg='Error: The value of rx_interval %s is out of [50 - 1000].' % rx_interval)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<rxInterval></rxInterval>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<rxInterval>(.*)</rxInterval>.*', recv_xml)

                if re_find:
                    result["rx_interval"] = re_find
                    if re_find[0] == rx_interval:
                        need_cfg = True

        tx_interval = module.params['tx_interval']
        if tx_interval:
            if int(tx_interval) > 1000 or int(tx_interval) < 50:
                module.fail_json(
                    msg='Error: The value of tx_interval %s is out of [50 - 1000].' % tx_interval)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<txInterval></txInterval>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<txInterval>(.*)</txInterval>.*', recv_xml)

                if re_find:
                    result["tx_interval"] = re_find
                    if re_find[0] == tx_interval:
                        need_cfg = True

        is_single_hop = module.params['is_single_hop']
        if is_single_hop != 'no_use':

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isSingleHop></isSingleHop>" + CE_GET_PEER_BFD_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<isSingleHop>(.*)</isSingleHop>.*', recv_xml)

                if re_find:
                    result["is_single_hop"] = re_find
                    if re_find[0] == is_single_hop:
                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def get_bgp_peer(self, **kwargs):
        """ get_bgp_peer """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='Error: The len of vrf_name %s is out of [1 - 31].' % vrf_name)

        conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
            "<remoteAs></remoteAs>" + CE_GET_BGP_PEER_TAIL

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<peerAddr>(.*)</peerAddr>.*\s.*<remoteAs>(.*)</remoteAs>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def get_bgp_del_peer(self, **kwargs):
        """ get_bgp_del_peer """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='Error: The len of vrf_name %s is out of [1 - 31].' % vrf_name)

        conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + CE_GET_BGP_PEER_TAIL

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<peerAddr>(.*)</peerAddr>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_bgp_peer(self, **kwargs):
        """ merge_bgp_peer """

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']
        remote_as = module.params['remote_as']

        conf_str = CE_MERGE_BGP_PEER_HEADER % (
            vrf_name, peer_addr) + "<remoteAs>%s</remoteAs>" % remote_as + CE_MERGE_BGP_PEER_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp peer failed.')

        cmds = []
        cmd = "peer %s as-number %s" % (peer_addr, remote_as)
        cmds.append(cmd)

        return cmds

    def create_bgp_peer(self, **kwargs):
        """ create_bgp_peer """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        peer_addr = module.params['peer_addr']
        remote_as = module.params['remote_as']

        conf_str = CE_CREATE_BGP_PEER_HEADER % (
            vrf_name, peer_addr) + "<remoteAs>%s</remoteAs>" % remote_as + CE_CREATE_BGP_PEER_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create bgp peer failed.')

        cmds = []
        cmd = "peer %s as-number %s" % (peer_addr, remote_as)
        cmds.append(cmd)

        return cmds

    def delete_bgp_peer(self, **kwargs):
        """ delete_bgp_peer """

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']

        conf_str = CE_DELETE_BGP_PEER_HEADER % (
            vrf_name, peer_addr) + CE_DELETE_BGP_PEER_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete bgp peer failed.')

        cmds = []
        cmd = "undo peer %s" % peer_addr
        cmds.append(cmd)

        return cmds

    def merge_bgp_peer_other(self, **kwargs):
        """ merge_bgp_peer """

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']

        conf_str = CE_MERGE_BGP_PEER_HEADER % (vrf_name, peer_addr)

        cmds = []

        description = module.params['description']
        if description:
            conf_str += "<description>%s</description>" % description

            cmd = "peer %s description %s" % (peer_addr, description)
            cmds.append(cmd)

        fake_as = module.params['fake_as']
        if fake_as:
            conf_str += "<fakeAs>%s</fakeAs>" % fake_as

            cmd = "peer %s local-as %s" % (peer_addr, fake_as)
            cmds.append(cmd)

        dual_as = module.params['dual_as']
        if dual_as != 'no_use':
            conf_str += "<dualAs>%s</dualAs>" % dual_as

            if dual_as == "true":
                cmd = "peer %s local-as %s dual-as" % (peer_addr, fake_as)
            else:
                cmd = "peer %s local-as %s" % (peer_addr, fake_as)
            cmds.append(cmd)

        conventional = module.params['conventional']
        if conventional != 'no_use':
            conf_str += "<conventional>%s</conventional>" % conventional

            if conventional == "true":
                cmd = "peer %s capability-advertise conventional" % peer_addr
            else:
                cmd = "undo peer %s capability-advertise conventional" % peer_addr
            cmds.append(cmd)

        route_refresh = module.params['route_refresh']
        if route_refresh != 'no_use':
            conf_str += "<routeRefresh>%s</routeRefresh>" % route_refresh

            if route_refresh == "true":
                cmd = "peer %s capability-advertise route-refresh" % peer_addr
            else:
                cmd = "undo peer %s capability-advertise route-refresh" % peer_addr
            cmds.append(cmd)

        four_byte_as = module.params['four_byte_as']
        if four_byte_as != 'no_use':
            conf_str += "<fourByteAs>%s</fourByteAs>" % four_byte_as

            if four_byte_as == "true":
                cmd = "peer %s capability-advertise 4-byte-as" % peer_addr
            else:
                cmd = "undo peer %s capability-advertise 4-byte-as" % peer_addr
            cmds.append(cmd)

        is_ignore = module.params['is_ignore']
        if is_ignore != 'no_use':
            conf_str += "<isIgnore>%s</isIgnore>" % is_ignore

            if is_ignore == "true":
                cmd = "peer %s ignore" % peer_addr
            else:
                cmd = "undo peer %s ignore" % peer_addr
            cmds.append(cmd)

        local_if_name = module.params['local_if_name']
        if local_if_name:
            conf_str += "<localIfName>%s</localIfName>" % local_if_name

            cmd = "peer %s connect-interface local_if_name" % peer_addr
            cmds.append(cmd)

        ebgp_max_hop = module.params['ebgp_max_hop']
        if ebgp_max_hop:
            conf_str += "<ebgpMaxHop>%s</ebgpMaxHop>" % ebgp_max_hop

            cmd = "peer %s ebgp-max-hop %s" % (peer_addr, ebgp_max_hop)
            cmds.append(cmd)

        valid_ttl_hops = module.params['valid_ttl_hops']
        if valid_ttl_hops:
            conf_str += "<validTtlHops>%s</validTtlHops>" % valid_ttl_hops

            cmd = "peer %s valid-ttl-hops %s" % (peer_addr, valid_ttl_hops)
            cmds.append(cmd)

        connect_mode = module.params['connect_mode']
        if connect_mode:
            conf_str += "<connectMode>%s</connectMode>" % connect_mode

            if connect_mode == "listenOnly":
                cmd = "peer %s listen-only" % peer_addr
                cmds.append(cmd)
            elif connect_mode == "connectOnly":
                cmd = "peer %s connect-only" % peer_addr
                cmds.append(cmd)
            elif connect_mode == "null":
                cmd = "peer %s listen-only" % peer_addr
                cmds.append(cmd)
                cmd = "peer %s connect-only" % peer_addr
                cmds.append(cmd)

        is_log_change = module.params['is_log_change']
        if is_log_change != 'no_use':
            conf_str += "<isLogChange>%s</isLogChange>" % is_log_change

            if is_log_change == "true":
                cmd = "peer %s log-change" % peer_addr
            else:
                cmd = "undo peer %s log-change" % peer_addr
            cmds.append(cmd)

        pswd_type = module.params['pswd_type']
        if pswd_type:
            conf_str += "<pswdType>%s</pswdType>" % pswd_type

        pswd_cipher_text = module.params['pswd_cipher_text']
        if pswd_cipher_text:
            conf_str += "<pswdCipherText>%s</pswdCipherText>" % pswd_cipher_text

            if pswd_type == "cipher":
                cmd = "peer %s password cipher %s" % (
                    peer_addr, pswd_cipher_text)
            elif pswd_type == "simple":
                cmd = "peer %s password simple %s" % (
                    peer_addr, pswd_cipher_text)
            cmds.append(cmd)

        keep_alive_time = module.params['keep_alive_time']
        if keep_alive_time:
            conf_str += "<keepAliveTime>%s</keepAliveTime>" % keep_alive_time

            cmd = "peer %s timer keepalive %s" % (peer_addr, keep_alive_time)
            cmds.append(cmd)

        hold_time = module.params['hold_time']
        if hold_time:
            conf_str += "<holdTime>%s</holdTime>" % hold_time

            cmd = "peer %s timer hold %s" % (peer_addr, hold_time)
            cmds.append(cmd)

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            conf_str += "<minHoldTime>%s</minHoldTime>" % min_hold_time

            cmd = "peer %s timer min-holdtime %s" % (peer_addr, min_hold_time)
            cmds.append(cmd)

        key_chain_name = module.params['key_chain_name']
        if key_chain_name:
            conf_str += "<keyChainName>%s</keyChainName>" % key_chain_name

            cmd = "peer %s keychain %s" % (peer_addr, key_chain_name)
            cmds.append(cmd)

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            conf_str += "<connRetryTime>%s</connRetryTime>" % conn_retry_time

            cmd = "peer %s timer connect-retry %s" % (
                peer_addr, conn_retry_time)
            cmds.append(cmd)

        tcp_mss = module.params['tcp_MSS']
        if tcp_mss:
            conf_str += "<tcpMSS>%s</tcpMSS>" % tcp_mss

            cmd = "peer %s tcp-mss %s" % (peer_addr, tcp_mss)
            cmds.append(cmd)

        mpls_local_ifnet_disable = module.params['mpls_local_ifnet_disable']
        if mpls_local_ifnet_disable != 'no_use':
            conf_str += "<mplsLocalIfnetDisable>%s</mplsLocalIfnetDisable>" % mpls_local_ifnet_disable

        prepend_global_as = module.params['prepend_global_as']
        if prepend_global_as != 'no_use':
            conf_str += "<prependGlobalAs>%s</prependGlobalAs>" % prepend_global_as

            if prepend_global_as == "true":
                cmd = "peer %s public-as-only" % peer_addr
            else:
                cmd = "undo peer %s public-as-only" % peer_addr
            cmds.append(cmd)

        prepend_fake_as = module.params['prepend_fake_as']
        if prepend_fake_as != 'no_use':
            conf_str += "<prependFakeAs>%s</prependFakeAs>" % prepend_fake_as

        conf_str += CE_MERGE_BGP_PEER_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp peer other failed.')

        return cmds

    def merge_peer_bfd(self, **kwargs):
        """ merge_peer_bfd """

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']

        conf_str = CE_MERGE_PEER_BFD_HEADER % (vrf_name, peer_addr)

        cmds = []

        is_bfd_block = module.params['is_bfd_block']
        if is_bfd_block != 'no_use':
            conf_str += "<isBfdBlock>%s</isBfdBlock>" % is_bfd_block

            if is_bfd_block == "true":
                cmd = "peer %s bfd block" % peer_addr
            else:
                cmd = "undo peer %s bfd block" % peer_addr
            cmds.append(cmd)

        multiplier = module.params['multiplier']
        if multiplier:
            conf_str += "<multiplier>%s</multiplier>" % multiplier

            cmd = "peer %s bfd detect-multiplier %s" % (peer_addr, multiplier)
            cmds.append(cmd)

        is_bfd_enable = module.params['is_bfd_enable']
        if is_bfd_enable != 'no_use':
            conf_str += "<isBfdEnable>%s</isBfdEnable>" % is_bfd_enable

            if is_bfd_enable == "true":
                cmd = "peer %s bfd enable" % peer_addr
            else:
                cmd = "undo peer %s bfd enable" % peer_addr
            cmds.append(cmd)

        rx_interval = module.params['rx_interval']
        if rx_interval:
            conf_str += "<rxInterval>%s</rxInterval>" % rx_interval

            cmd = "peer %s bfd min-rx-interval %s" % (peer_addr, rx_interval)
            cmds.append(cmd)

        tx_interval = module.params['tx_interval']
        if tx_interval:
            conf_str += "<txInterval>%s</txInterval>" % tx_interval

            cmd = "peer %s bfd min-tx-interval %s" % (peer_addr, tx_interval)
            cmds.append(cmd)

        is_single_hop = module.params['is_single_hop']
        if is_single_hop != 'no_use':
            conf_str += "<isSingleHop>%s</isSingleHop>" % is_single_hop

            if is_single_hop == "true":
                cmd = "peer %s bfd enable single-hop-prefer" % peer_addr
            else:
                cmd = "undo peer %s bfd enable single-hop-prefer" % peer_addr
            cmds.append(cmd)

        conf_str += CE_MERGE_PEER_BFD_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge peer bfd failed.')

        return cmds

    def delete_peer_bfd(self, **kwargs):
        """ delete_peer_bfd """

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']

        conf_str = CE_DELETE_PEER_BFD_HEADER % (vrf_name, peer_addr)

        cmds = []

        is_bfd_block = module.params['is_bfd_block']
        if is_bfd_block != 'no_use':
            conf_str += "<isBfdBlock>%s</isBfdBlock>" % is_bfd_block

            cmd = "undo peer %s bfd block" % peer_addr
            cmds.append(cmd)

        multiplier = module.params['multiplier']
        if multiplier:
            conf_str += "<multiplier>%s</multiplier>" % multiplier

            cmd = "undo peer %s bfd detect-multiplier %s" % (
                peer_addr, multiplier)
            cmds.append(cmd)

        is_bfd_enable = module.params['is_bfd_enable']
        if is_bfd_enable != 'no_use':
            conf_str += "<isBfdEnable>%s</isBfdEnable>" % is_bfd_enable

            cmd = "undo peer %s bfd enable" % peer_addr
            cmds.append(cmd)

        rx_interval = module.params['rx_interval']
        if rx_interval:
            conf_str += "<rxInterval>%s</rxInterval>" % rx_interval

            cmd = "undo peer %s bfd min-rx-interval %s" % (
                peer_addr, rx_interval)
            cmds.append(cmd)

        tx_interval = module.params['tx_interval']
        if tx_interval:
            conf_str += "<txInterval>%s</txInterval>" % tx_interval

            cmd = "undo peer %s bfd min-tx-interval %s" % (
                peer_addr, tx_interval)
            cmds.append(cmd)

        is_single_hop = module.params['is_single_hop']
        if is_single_hop != 'no_use':
            conf_str += "<isSingleHop>%s</isSingleHop>" % is_single_hop

            cmd = "undo peer %s bfd enable single-hop-prefer" % peer_addr
            cmds.append(cmd)

        conf_str += CE_DELETE_PEER_BFD_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete peer bfd failed.')

        return cmds


def main():
    """ main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        vrf_name=dict(type='str', required=True),
        peer_addr=dict(type='str', required=True),
        remote_as=dict(type='str', required=True),
        description=dict(type='str'),
        fake_as=dict(type='str'),
        dual_as=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        conventional=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        route_refresh=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        four_byte_as=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        is_ignore=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        local_if_name=dict(type='str'),
        ebgp_max_hop=dict(type='str'),
        valid_ttl_hops=dict(type='str'),
        connect_mode=dict(choices=['listenOnly', 'connectOnly', 'null']),
        is_log_change=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        pswd_type=dict(choices=['null', 'cipher', 'simple']),
        pswd_cipher_text=dict(type='str', no_log=True),
        keep_alive_time=dict(type='str'),
        hold_time=dict(type='str'),
        min_hold_time=dict(type='str'),
        key_chain_name=dict(type='str'),
        conn_retry_time=dict(type='str'),
        tcp_MSS=dict(type='str'),
        mpls_local_ifnet_disable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        prepend_global_as=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        prepend_fake_as=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        is_bfd_block=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        multiplier=dict(type='str'),
        is_bfd_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        rx_interval=dict(type='str'),
        tx_interval=dict(type='str'),
        is_single_hop=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']))

    argument_spec.update(ce_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    changed = False
    proposed = dict()
    existing = dict()
    end_state = dict()
    updates = []

    state = module.params['state']
    vrf_name = module.params['vrf_name']
    peer_addr = module.params['peer_addr']
    remote_as = module.params['remote_as']
    description = module.params['description']
    fake_as = module.params['fake_as']
    dual_as = module.params['dual_as']
    conventional = module.params['conventional']
    route_refresh = module.params['route_refresh']
    four_byte_as = module.params['four_byte_as']
    is_ignore = module.params['is_ignore']
    local_if_name = module.params['local_if_name']
    ebgp_max_hop = module.params['ebgp_max_hop']
    valid_ttl_hops = module.params['valid_ttl_hops']
    connect_mode = module.params['connect_mode']
    is_log_change = module.params['is_log_change']
    pswd_type = module.params['pswd_type']
    pswd_cipher_text = module.params['pswd_cipher_text']
    keep_alive_time = module.params['keep_alive_time']
    hold_time = module.params['hold_time']
    min_hold_time = module.params['min_hold_time']
    key_chain_name = module.params['key_chain_name']
    conn_retry_time = module.params['conn_retry_time']
    tcp_mss = module.params['tcp_MSS']
    mpls_local_ifnet_disable = module.params['mpls_local_ifnet_disable']
    prepend_global_as = module.params['prepend_global_as']
    prepend_fake_as = module.params['prepend_fake_as']
    is_bfd_block = module.params['is_bfd_block']
    multiplier = module.params['multiplier']
    is_bfd_enable = module.params['is_bfd_enable']
    rx_interval = module.params['rx_interval']
    tx_interval = module.params['tx_interval']
    is_single_hop = module.params['is_single_hop']

    ce_bgp_peer_obj = BgpNeighbor()

    # get proposed
    proposed["state"] = state
    if vrf_name:
        proposed["vrf_name"] = vrf_name
    if peer_addr:
        proposed["peer_addr"] = peer_addr
    if remote_as:
        proposed["remote_as"] = remote_as
    if description:
        proposed["description"] = description
    if fake_as:
        proposed["fake_as"] = fake_as
    if dual_as != 'no_use':
        proposed["dual_as"] = dual_as
    if conventional != 'no_use':
        proposed["conventional"] = conventional
    if route_refresh != 'no_use':
        proposed["route_refresh"] = route_refresh
    if four_byte_as != 'no_use':
        proposed["four_byte_as"] = four_byte_as
    if is_ignore != 'no_use':
        proposed["is_ignore"] = is_ignore
    if local_if_name:
        proposed["local_if_name"] = local_if_name
    if ebgp_max_hop:
        proposed["ebgp_max_hop"] = ebgp_max_hop
    if valid_ttl_hops:
        proposed["valid_ttl_hops"] = valid_ttl_hops
    if connect_mode:
        proposed["connect_mode"] = connect_mode
    if is_log_change != 'no_use':
        proposed["is_log_change"] = is_log_change
    if pswd_type:
        proposed["pswd_type"] = pswd_type
    if pswd_cipher_text:
        proposed["pswd_cipher_text"] = pswd_cipher_text
    if keep_alive_time:
        proposed["keep_alive_time"] = keep_alive_time
    if hold_time:
        proposed["hold_time"] = hold_time
    if min_hold_time:
        proposed["min_hold_time"] = min_hold_time
    if key_chain_name:
        proposed["key_chain_name"] = key_chain_name
    if conn_retry_time:
        proposed["conn_retry_time"] = conn_retry_time
    if tcp_mss:
        proposed["tcp_MSS"] = tcp_mss
    if mpls_local_ifnet_disable != 'no_use':
        proposed["mpls_local_ifnet_disable"] = mpls_local_ifnet_disable
    if prepend_global_as != 'no_use':
        proposed["prepend_global_as"] = prepend_global_as
    if prepend_fake_as != 'no_use':
        proposed["prepend_fake_as"] = prepend_fake_as
    if is_bfd_block != 'no_use':
        proposed["is_bfd_block"] = is_bfd_block
    if multiplier:
        proposed["multiplier"] = multiplier
    if is_bfd_enable != 'no_use':
        proposed["is_bfd_enable"] = is_bfd_enable
    if rx_interval:
        proposed["rx_interval"] = rx_interval
    if tx_interval:
        proposed["tx_interval"] = tx_interval
    if is_single_hop != 'no_use':
        proposed["is_single_hop"] = is_single_hop

    if not ce_bgp_peer_obj:
        module.fail_json(msg='Error: Init module failed.')

    need_bgp_peer_enable = ce_bgp_peer_obj.check_bgp_peer_args(module=module)
    need_bgp_peer_other_rst = ce_bgp_peer_obj.check_bgp_peer_other_args(
        module=module)
    need_peer_bfd_merge_rst = ce_bgp_peer_obj.check_peer_bfd_merge_args(
        module=module)
    need_peer_bfd_del_rst = ce_bgp_peer_obj.check_peer_bfd_delete_args(
        module=module)

    # bgp peer config
    if need_bgp_peer_enable["need_cfg"]:

        if state == "present":

            if remote_as:

                bgp_peer_exist = ce_bgp_peer_obj.get_bgp_peer(module=module)
                existing["bgp peer"] = bgp_peer_exist

                bgp_peer_new = (peer_addr, remote_as)

                if len(bgp_peer_exist) == 0:
                    cmd = ce_bgp_peer_obj.create_bgp_peer(module=module)
                    changed = True
                    for item in cmd:
                        updates.append(item)

                elif bgp_peer_new in bgp_peer_exist:
                    pass

                else:
                    cmd = ce_bgp_peer_obj.merge_bgp_peer(module=module)
                    changed = True
                    for item in cmd:
                        updates.append(item)

                bgp_peer_end = ce_bgp_peer_obj.get_bgp_peer(module=module)
                end_state["bgp peer"] = bgp_peer_end

        else:

            bgp_peer_exist = ce_bgp_peer_obj.get_bgp_del_peer(module=module)
            existing["bgp peer"] = bgp_peer_exist

            bgp_peer_new = (peer_addr)

            if len(bgp_peer_exist) == 0:
                pass

            elif bgp_peer_new in bgp_peer_exist:
                cmd = ce_bgp_peer_obj.delete_bgp_peer(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

            bgp_peer_end = ce_bgp_peer_obj.get_bgp_del_peer(module=module)
            end_state["bgp peer"] = bgp_peer_end

    # bgp peer other args
    exist_tmp = dict()
    for item in need_bgp_peer_other_rst:
        if item != "need_cfg":
            exist_tmp[item] = need_bgp_peer_other_rst[item]
    if exist_tmp:
        existing["bgp peer other"] = exist_tmp

    if need_bgp_peer_other_rst["need_cfg"]:

        if state == "present":
            cmd = ce_bgp_peer_obj.merge_bgp_peer_other(module=module)
            changed = True
            for item in cmd:
                updates.append(item)

    need_bgp_peer_other_rst = ce_bgp_peer_obj.check_bgp_peer_other_args(
        module=module)
    end_tmp = dict()
    for item in need_bgp_peer_other_rst:
        if item != "need_cfg":
            end_tmp[item] = need_bgp_peer_other_rst[item]
    if end_tmp:
        end_state["bgp peer other"] = end_tmp

    # peer bfd args
    if state == "present":
        exist_tmp = dict()
        for item in need_peer_bfd_merge_rst:
            if item != "need_cfg":
                exist_tmp[item] = need_peer_bfd_merge_rst[item]
        if exist_tmp:
            existing["peer bfd"] = exist_tmp

        if need_peer_bfd_merge_rst["need_cfg"]:
            cmd = ce_bgp_peer_obj.merge_peer_bfd(module=module)
            changed = True
            for item in cmd:
                updates.append(item)

        need_peer_bfd_merge_rst = ce_bgp_peer_obj.check_peer_bfd_merge_args(
            module=module)
        end_tmp = dict()
        for item in need_peer_bfd_merge_rst:
            if item != "need_cfg":
                end_tmp[item] = need_peer_bfd_merge_rst[item]
        if end_tmp:
            end_state["peer bfd"] = end_tmp
    else:
        exist_tmp = dict()
        for item in need_peer_bfd_del_rst:
            if item != "need_cfg":
                exist_tmp[item] = need_peer_bfd_del_rst[item]
        if exist_tmp:
            existing["peer bfd"] = exist_tmp

        # has already delete with bgp peer

        need_peer_bfd_del_rst = ce_bgp_peer_obj.check_peer_bfd_delete_args(
            module=module)
        end_tmp = dict()
        for item in need_peer_bfd_del_rst:
            if item != "need_cfg":
                end_tmp[item] = need_peer_bfd_del_rst[item]
        if end_tmp:
            end_state["peer bfd"] = end_tmp

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state
    results['updates'] = updates

    module.exit_json(**results)


if __name__ == '__main__':
    main()
