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

DOCUMENTATION = '''
---

module: ce_bgp_neighbor
version_added: "2.2"
short_description: Manages BGP peer configuration.
description:
    - Manages BGP peer configurations on cloudengine switches.
extends_documentation_fragment: cloudengine
author:
    - wangdezhuang (@CloudEngine-Ansible)
notes:
    - The server_type parameter is always required.
options:
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']
    vrf_name:
        description:
            - vrf name.
        required: true
        default: _public_
    peer_addr:
        description:
            - peer adress.
        required: true
        default: None
    remote_as:
        description:
            - remote as.
        required: true
        default: None
    description:
        description:
            - description.
        required: false
        default: None
    fake_as:
        description:
            - fake as.
        required: false
        default: None
    dual_as:
        description:
            - remote as can use fake as or real as.
        required: false
        choices: ['true','false']
        default: None
    conventional:
        description:
            - enable Eextended router function.
        required: false
        choices: ['true','false']
        default: None
    route_refresh:
        description:
            - route refresh.
        required: false
        choices: ['true','false']
        default: None
    is_ignore:
        description:
            - stop session between peers.
        required: false
        choices: ['true','false']
        default: None
    local_if_name:
        description:
            - loacl interface name.
        required: false
        default: None
    ebgp_max_hop:
        description:
            - ebgp max hop.
        required: false
        default: None
    valid_ttl_hops:
        description:
            - valid ttl hops.
        required: false
        default: None
    connect_mode:
        description:
            - connect mode.
        required: false
        default: None
    is_log_change:
        description:
            - is log change.
        required: false
        choices: ['true','false']
        default: None
    pswd_type:
        description:
            - password type.
        required: false
        choices: ['null','cipher','simple']
        default: None
    pswd_cipher_text:
        description:
            - password cipher text.
        required: false
        default: None
    keep_alive_time:
        description:
            - keep alive time.
        required: false
        default: None
    hold_time:
        description:
            - hold time.
        required: false
        default: None
    min_hold_time:
        description:
            - min hold time.
        required: false
        default: None
    key_chain_name:
        description:
            - key chain name.
        required: false
        default: None
    conn_retry_time:
        description:
            - connection retry time.
        required: false
        default: None
    tcp_MSS:
        description:
            - tcp MSS.
        required: false
        default: None
    mpls_local_ifnet_disable:
        description:
            - mpls local ifnet disable.
        required: false
        default: None
    prepend_global_as:
        description:
            - prepend global as.
        required: false
        default: None
    prepend_fake_as:
        description:
            - prepend fake as.
        required: false
        default: None
    is_bfd_block:
        description:
            - is bfd block.
        required: false
        default: None
    multiplier:
        description:
            - multiplier.
        required: false
        default: None
    is_bfd_enable:
        description:
            - is bfd enable.
        required: false
        default: None
    rx_interval:
        description:
            - rx interval.
        required: false
        default: None
    tx_interval:
        description:
            - tx interval.
        required: false
        default: None
    is_single_hop:
        description:
            - is single hop.
        required: false
        default: None
'''

EXAMPLES = '''
# config bgp peer
  - name: "config bgp peer"
    ce_bgp_neighbor:
        state:  present
        peer_addr:  192.168.10.10
        remote_as:  500
        host:  {{inventory_hostname}}
        username:  {{username}}
        password:  {{password}}
# delete bgp peer
  - name: "config bgp route id"
    ce_bgp_neighbor:
        state:  absent
        peer_addr:  192.168.10.10
        host:  {{inventory_hostname}}
        username:  {{username}}
        password:  {{password}}
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
    sample: {"peer_addr": "192.168.10.10", "remote_as": "500", "state": "present"}
existing:
    description:
        - k/v pairs of existing aaa server
    type: dict
    sample: {"bgp peer": []}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bgp peer": [["192.168.10.10", "500"]]}
execute_time:
    description: the module execute time
    returned: always
    type: string
    sample: "0:00:03.380753"
'''

import re
import datetime
import socket
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


SUCCESS = """success"""
FAILED = """failed"""

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


class ce_bgp_neighbor(object):
    """ Manages BGP peer configuration """

    def __init__(self, **kwargs):
        """ __init__ """

        self.netconf = get_netconf(**kwargs)

    def netconf_get_config(self, **kwargs):
        """ netconf_get_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        try:
            con_obj = self.netconf.get_config(filter=conf_str)
        except RPCError as err:
            module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def netconf_set_config(self, **kwargs):
        """ netconf_set_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        try:
            con_obj = self.netconf.set_config(config=conf_str)
        except RPCError as err:
            module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def check_ip_addr(self, **kwargs):
        """ check_ip_addr, Supports IPv4 and IPv6"""

        ipaddr = kwargs["ipaddr"]

        if not ipaddr or '\x00' in ipaddr:
            return False

        try:
            res = socket.getaddrinfo(ipaddr, 0, socket.AF_UNSPEC,
                                     socket.SOCK_STREAM,
                                     0, socket.AI_NUMERICHOST)
            return bool(res)
        except socket.gaierror as err:
            if err.args[0] == socket.EAI_NONAME:
                return False
            raise
        return True

    def check_bgp_peer_args(self, **kwargs):
        """check_bgp_peer_args"""

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)

        peer_addr = module.params['peer_addr']
        if peer_addr:
            if not self.check_ip_addr(ipaddr=peer_addr):
                module.fail_json(
                    msg='the peer_addr %s is invalid.' % peer_addr)

            need_cfg = True

        remote_as = module.params['remote_as']
        if remote_as:
            if len(remote_as) > 11 or len(remote_as) < 1:
                module.fail_json(
                    msg='the len of remote_as %s is out of [1 - 11].' % remote_as)

            need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_peer_other_args(self, **kwargs):
        """check_bgp_peer_other_args"""

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)

        description = module.params['description']
        if description:
            if len(description) > 80 or len(description) < 1:
                module.fail_json(
                    msg='the len of description %s is out of [1 - 80].' % description)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<description></description>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<description>(.*)</description>.*', con_obj.xml)

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
                    msg='the len of fake_as %s is out of [1 - 11].' % fake_as)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<fakeAs></fakeAs>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<fakeAs>(.*)</fakeAs>.*', con_obj.xml)

                if re_find:
                    result["fake_as"] = re_find
                    if re_find[0] != fake_as:
                        need_cfg = True
                else:
                    need_cfg = True

        dual_as = module.params['dual_as']
        if dual_as:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<dualAs></dualAs>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<dualAs>(.*)</dualAs>.*', con_obj.xml)

                if re_find:
                    result["dual_as"] = re_find
                    if re_find[0] != fake_as:
                        need_cfg = True
                else:
                    need_cfg = True

        conventional = module.params['conventional']
        if conventional:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<conventional></conventional>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<conventional>(.*)</conventional>.*', con_obj.xml)

                if re_find:
                    result["conventional"] = re_find
                    if re_find[0] != conventional:
                        need_cfg = True
                else:
                    need_cfg = True

        route_refresh = module.params['route_refresh']
        if route_refresh:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<routeRefresh></routeRefresh>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeRefresh>(.*)</routeRefresh>.*', con_obj.xml)

                if re_find:
                    result["route_refresh"] = re_find
                    if re_find[0] != route_refresh:
                        need_cfg = True
                else:
                    need_cfg = True

        four_byte_as = module.params['four_byte_as']
        if four_byte_as:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<fourByteAs></fourByteAs>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<fourByteAs>(.*)</fourByteAs>.*', con_obj.xml)

                if re_find:
                    result["four_byte_as"] = re_find
                    if re_find[0] != four_byte_as:
                        need_cfg = True
                else:
                    need_cfg = True

        is_ignore = module.params['is_ignore']
        if is_ignore:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<isIgnore></isIgnore>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isIgnore>(.*)</isIgnore>.*', con_obj.xml)

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
                    msg='the len of local_if_name %s is out of [1 - 63].' % local_if_name)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<localIfName></localIfName>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<localIfName>(.*)</localIfName>.*', con_obj.xml)

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
                    msg='the value of ebgp_max_hop %s is out of [1 - 255].' % ebgp_max_hop)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<ebgpMaxHop></ebgpMaxHop>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ebgpMaxHop>(.*)</ebgpMaxHop>.*', con_obj.xml)

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
                    msg='the value of valid_ttl_hops %s is out of [1 - 255].' % valid_ttl_hops)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<validTtlHops></validTtlHops>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<validTtlHops>(.*)</validTtlHops>.*', con_obj.xml)

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
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<connectMode>(.*)</connectMode>.*', con_obj.xml)

                if re_find:
                    result["connect_mode"] = re_find
                    if re_find[0] != connect_mode:
                        need_cfg = True
                else:
                    need_cfg = True

        is_log_change = module.params['is_log_change']
        if is_log_change:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<isLogChange></isLogChange>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isLogChange>(.*)</isLogChange>.*', con_obj.xml)

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
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<pswdType>(.*)</pswdType>.*', con_obj.xml)

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
                    msg='the len of pswd_cipher_text %s is out of [1 - 255].' % pswd_cipher_text)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<pswdCipherText></pswdCipherText>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<pswdCipherText>(.*)</pswdCipherText>.*', con_obj.xml)

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
                    msg='the len of keep_alive_time %s is out of [0 - 21845].' % keep_alive_time)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<keepAliveTime></keepAliveTime>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<keepAliveTime>(.*)</keepAliveTime>.*', con_obj.xml)

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
                    msg='the value of hold_time %s is out of [0 or 3 - 65535].' % hold_time)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<holdTime></holdTime>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<holdTime>(.*)</holdTime>.*', con_obj.xml)

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
                    msg='the value of min_hold_time %s is out of [0 or 20 - 65535].' % min_hold_time)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<minHoldTime></minHoldTime>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<minHoldTime>(.*)</minHoldTime>.*', con_obj.xml)

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
                    msg='the len of key_chain_name %s is out of [1 - 47].' % key_chain_name)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<keyChainName></keyChainName>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<keyChainName>(.*)</keyChainName>.*', con_obj.xml)

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
                    msg='the value of conn_retry_time %s is out of [1 - 65535].' % conn_retry_time)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<connRetryTime></connRetryTime>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<connRetryTime>(.*)</connRetryTime>.*', con_obj.xml)

                if re_find:
                    result["conn_retry_time"] = re_find
                    if re_find[0] != conn_retry_time:
                        need_cfg = True
                else:
                    need_cfg = True

        tcp_MSS = module.params['tcp_MSS']
        if tcp_MSS:
            if int(tcp_MSS) > 4096 or int(tcp_MSS) < 176:
                module.fail_json(
                    msg='the value of tcp_MSS %s is out of [176 - 4096].' % tcp_MSS)

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<tcpMSS></tcpMSS>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<tcpMSS>(.*)</tcpMSS>.*', con_obj.xml)

                if re_find:
                    result["tcp_MSS"] = re_find
                    if re_find[0] != tcp_MSS:
                        need_cfg = True
                else:
                    need_cfg = True

        mpls_local_ifnet_disable = module.params['mpls_local_ifnet_disable']
        if mpls_local_ifnet_disable:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<mplsLocalIfnetDisable></mplsLocalIfnetDisable>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<mplsLocalIfnetDisable>(.*)</mplsLocalIfnetDisable>.*', con_obj.xml)

                if re_find:
                    result["mpls_local_ifnet_disable"] = re_find
                    if re_find[0] != mpls_local_ifnet_disable:
                        need_cfg = True
                else:
                    need_cfg = True

        prepend_global_as = module.params['prepend_global_as']
        if prepend_global_as:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<prependGlobalAs></prependGlobalAs>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<prependGlobalAs>(.*)</prependGlobalAs>.*', con_obj.xml)

                if re_find:
                    result["prepend_global_as"] = re_find
                    if re_find[0] != prepend_global_as:
                        need_cfg = True
                else:
                    need_cfg = True

        prepend_fake_as = module.params['prepend_fake_as']
        if prepend_fake_as:

            conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
                "<prependFakeAs></prependFakeAs>" + CE_GET_BGP_PEER_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<prependFakeAs>(.*)</prependFakeAs>.*', con_obj.xml)

                if re_find:
                    result["prepend_fake_as"] = re_find
                    if re_find[0] != prepend_fake_as:
                        need_cfg = True
                else:
                    need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_peer_bfd_merge_args(self, **kwargs):
        """check_peer_bfd_merge_args"""

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
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)

        peer_addr = module.params['peer_addr']

        is_bfd_block = module.params['is_bfd_block']
        if is_bfd_block:

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isBfdBlock></isBfdBlock>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isBfdBlock>(.*)</isBfdBlock>.*', con_obj.xml)

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
                    msg='the value of multiplier %s is out of [3 - 50].' % multiplier)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<multiplier></multiplier>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<multiplier>(.*)</multiplier>.*', con_obj.xml)

                if re_find:
                    result["multiplier"] = re_find
                    if re_find[0] != multiplier:
                        need_cfg = True
                else:
                    need_cfg = True

        is_bfd_enable = module.params['is_bfd_enable']
        if is_bfd_enable:

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isBfdEnable></isBfdEnable>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isBfdEnable>(.*)</isBfdEnable>.*', con_obj.xml)

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
                    msg='the value of rx_interval %s is out of [50 - 1000].' % rx_interval)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<rxInterval></rxInterval>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<rxInterval>(.*)</rxInterval>.*', con_obj.xml)

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
                    msg='the value of tx_interval %s is out of [50 - 1000].' % tx_interval)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<txInterval></txInterval>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<txInterval>(.*)</txInterval>.*', con_obj.xml)

                if re_find:
                    result["tx_interval"] = re_find
                    if re_find[0] != tx_interval:
                        need_cfg = True
                else:
                    need_cfg = True

        is_single_hop = module.params['is_single_hop']
        if is_single_hop:

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isSingleHop></isSingleHop>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isSingleHop>(.*)</isSingleHop>.*', con_obj.xml)

                if re_find:
                    result["is_single_hop"] = re_find
                    if re_find[0] != is_single_hop:
                        need_cfg = True
                else:
                    need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_peer_bfd_delete_args(self, **kwargs):
        """check_peer_bfd_delete_args"""

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
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)

        peer_addr = module.params['peer_addr']

        is_bfd_block = module.params['is_bfd_block']
        if is_bfd_block:

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isBfdBlock></isBfdBlock>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<isBfdBlock>(.*)</isBfdBlock>.*', con_obj.xml)

                if re_find:
                    result["is_bfd_block"] = re_find
                    if re_find[0] == is_bfd_block:
                        need_cfg = True

        multiplier = module.params['multiplier']
        if multiplier:
            if int(multiplier) > 50 or int(multiplier) < 3:
                module.fail_json(
                    msg='the value of multiplier %s is out of [3 - 50].' % multiplier)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<multiplier></multiplier>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<multiplier>(.*)</multiplier>.*', con_obj.xml)

                if re_find:
                    result["multiplier"] = re_find
                    if re_find[0] == multiplier:
                        need_cfg = True

        is_bfd_enable = module.params['is_bfd_enable']
        if is_bfd_enable:

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isBfdEnable></isBfdEnable>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<isBfdEnable>(.*)</isBfdEnable>.*', con_obj.xml)

                if re_find:
                    result["is_bfd_enable"] = re_find
                    if re_find[0] == is_bfd_enable:
                        need_cfg = True

        rx_interval = module.params['rx_interval']
        if rx_interval:
            if int(rx_interval) > 1000 or int(rx_interval) < 50:
                module.fail_json(
                    msg='the value of rx_interval %s is out of [50 - 1000].' % rx_interval)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<rxInterval></rxInterval>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<rxInterval>(.*)</rxInterval>.*', con_obj.xml)

                if re_find:
                    result["rx_interval"] = re_find
                    if re_find[0] == rx_interval:
                        need_cfg = True

        tx_interval = module.params['tx_interval']
        if tx_interval:
            if int(tx_interval) > 1000 or int(tx_interval) < 50:
                module.fail_json(
                    msg='the value of tx_interval %s is out of [50 - 1000].' % tx_interval)

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<txInterval></txInterval>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<txInterval>(.*)</txInterval>.*', con_obj.xml)

                if re_find:
                    result["tx_interval"] = re_find
                    if re_find[0] == tx_interval:
                        need_cfg = True

        is_single_hop = module.params['is_single_hop']
        if is_single_hop:

            conf_str = CE_GET_PEER_BFD_HEADER % (
                vrf_name, peer_addr) + "<isSingleHop></isSingleHop>" + CE_GET_PEER_BFD_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<isSingleHop>(.*)</isSingleHop>.*', con_obj.xml)

                if re_find:
                    result["is_single_hop"] = re_find
                    if re_find[0] == is_single_hop:
                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def get_bgp_peer(self, **kwargs):
        """get_bgp_peer"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)

        conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + \
            "<remoteAs></remoteAs>" + CE_GET_BGP_PEER_TAIL

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """get_bgp_del_peer"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)

        conf_str = CE_GET_BGP_PEER_HEADER % vrf_name + CE_GET_BGP_PEER_TAIL

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """merge_bgp_peer"""

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']
        remote_as = module.params['remote_as']

        conf_str = CE_MERGE_BGP_PEER_HEADER % (
            vrf_name, peer_addr) + "<remoteAs>%s</remoteAs>" % remote_as + CE_MERGE_BGP_PEER_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp peer failed.')

        return SUCCESS

    def create_bgp_peer(self, **kwargs):
        """create_bgp_peer"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        peer_addr = module.params['peer_addr']
        remote_as = module.params['remote_as']

        conf_str = CE_CREATE_BGP_PEER_HEADER % (
            vrf_name, peer_addr) + "<remoteAs>%s</remoteAs>" % remote_as + CE_CREATE_BGP_PEER_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create bgp peer failed.')

        return SUCCESS

    def delete_bgp_peer(self, **kwargs):
        """delete_bgp_peer"""

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']

        conf_str = CE_DELETE_BGP_PEER_HEADER % (
            vrf_name, peer_addr) + CE_DELETE_BGP_PEER_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete bgp peer failed.')

        return SUCCESS

    def merge_bgp_peer_other(self, **kwargs):
        """merge_bgp_peer"""

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']

        conf_str = CE_MERGE_BGP_PEER_HEADER % (vrf_name, peer_addr)

        description = module.params['description']
        if description:
            conf_str += "<description>%s</description>" % description

        fake_as = module.params['fake_as']
        if fake_as:
            conf_str += "<fakeAs>%s</fakeAs>" % fake_as

        dual_as = module.params['dual_as']
        if dual_as:
            conf_str += "<dualAs>%s</dualAs>" % dual_as

        conventional = module.params['conventional']
        if conventional:
            conf_str += "<conventional>%s</conventional>" % conventional

        route_refresh = module.params['route_refresh']
        if route_refresh:
            conf_str += "<routeRefresh>%s</routeRefresh>" % route_refresh

        four_byte_as = module.params['four_byte_as']
        if four_byte_as:
            conf_str += "<fourByteAs>%s</fourByteAs>" % four_byte_as

        is_ignore = module.params['is_ignore']
        if is_ignore:
            conf_str += "<isIgnore>%s</isIgnore>" % is_ignore

        local_if_name = module.params['local_if_name']
        if local_if_name:
            conf_str += "<localIfName>%s</localIfName>" % local_if_name

        ebgp_max_hop = module.params['ebgp_max_hop']
        if ebgp_max_hop:
            conf_str += "<ebgpMaxHop>%s</ebgpMaxHop>" % ebgp_max_hop

        valid_ttl_hops = module.params['valid_ttl_hops']
        if valid_ttl_hops:
            conf_str += "<validTtlHops>%s</validTtlHops>" % valid_ttl_hops

        connect_mode = module.params['connect_mode']
        if connect_mode:
            conf_str += "<connectMode>%s</connectMode>" % connect_mode

        is_log_change = module.params['is_log_change']
        if is_log_change:
            conf_str += "<isLogChange>%s</isLogChange>" % is_log_change

        pswd_type = module.params['pswd_type']
        if pswd_type:
            conf_str += "<pswdType>%s</pswdType>" % pswd_type

        pswd_cipher_text = module.params['pswd_cipher_text']
        if pswd_cipher_text:
            conf_str += "<pswdCipherText>%s</pswdCipherText>" % pswd_cipher_text

        keep_alive_time = module.params['keep_alive_time']
        if keep_alive_time:
            conf_str += "<keepAliveTime>%s</keepAliveTime>" % keep_alive_time

        hold_time = module.params['hold_time']
        if hold_time:
            conf_str += "<holdTime>%s</holdTime>" % hold_time

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            conf_str += "<minHoldTime>%s</minHoldTime>" % min_hold_time

        key_chain_name = module.params['key_chain_name']
        if key_chain_name:
            conf_str += "<keyChainName>%s</keyChainName>" % key_chain_name

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            conf_str += "<connRetryTime>%s</connRetryTime>" % conn_retry_time

        tcp_MSS = module.params['tcp_MSS']
        if tcp_MSS:
            conf_str += "<tcpMSS>%s</tcpMSS>" % tcp_MSS

        mpls_local_ifnet_disable = module.params['mpls_local_ifnet_disable']
        if mpls_local_ifnet_disable:
            conf_str += "<mplsLocalIfnetDisable>%s</mplsLocalIfnetDisable>" % mpls_local_ifnet_disable

        prepend_global_as = module.params['prepend_global_as']
        if prepend_global_as:
            conf_str += "<prependGlobalAs>%s</prependGlobalAs>" % prepend_global_as

        prepend_fake_as = module.params['prepend_fake_as']
        if prepend_fake_as:
            conf_str += "<prependFakeAs>%s</prependFakeAs>" % prepend_fake_as

        conf_str += CE_MERGE_BGP_PEER_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp peer other failed.')

        return SUCCESS

    def merge_peer_bfd(self, **kwargs):
        """merge_peer_bfd"""

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']

        conf_str = CE_MERGE_PEER_BFD_HEADER % (vrf_name, peer_addr)

        is_bfd_block = module.params['is_bfd_block']
        if is_bfd_block:
            conf_str += "<isBfdBlock>%s</isBfdBlock>" % is_bfd_block

        multiplier = module.params['multiplier']
        if multiplier:
            conf_str += "<multiplier>%s</multiplier>" % multiplier

        is_bfd_enable = module.params['is_bfd_enable']
        if is_bfd_enable:
            conf_str += "<isBfdEnable>%s</isBfdEnable>" % is_bfd_enable

        rx_interval = module.params['rx_interval']
        if rx_interval:
            conf_str += "<rxInterval>%s</rxInterval>" % rx_interval

        tx_interval = module.params['tx_interval']
        if tx_interval:
            conf_str += "<txInterval>%s</txInterval>" % tx_interval

        is_single_hop = module.params['is_single_hop']
        if is_single_hop:
            conf_str += "<isSingleHop>%s</isSingleHop>" % is_single_hop

        conf_str += CE_MERGE_PEER_BFD_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge peer bfd failed.')

        return SUCCESS

    def delete_peer_bfd(self, **kwargs):
        """delete_peer_bfd"""

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        peer_addr = module.params['peer_addr']

        conf_str = CE_DELETE_PEER_BFD_HEADER % (vrf_name, peer_addr)

        is_bfd_block = module.params['is_bfd_block']
        if is_bfd_block:
            conf_str += "<isBfdBlock>%s</isBfdBlock>" % is_bfd_block

        multiplier = module.params['multiplier']
        if multiplier:
            conf_str += "<multiplier>%s</multiplier>" % multiplier

        is_bfd_enable = module.params['is_bfd_enable']
        if is_bfd_enable:
            conf_str += "<isBfdEnable>%s</isBfdEnable>" % is_bfd_enable

        rx_interval = module.params['rx_interval']
        if rx_interval:
            conf_str += "<rxInterval>%s</rxInterval>" % rx_interval

        tx_interval = module.params['tx_interval']
        if tx_interval:
            conf_str += "<txInterval>%s</txInterval>" % tx_interval

        is_single_hop = module.params['is_single_hop']
        if is_single_hop:
            conf_str += "<isSingleHop>%s</isSingleHop>" % is_single_hop

        conf_str += CE_DELETE_PEER_BFD_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete peer bfd failed.')

        return SUCCESS


def main():
    """ main """

    start_time = datetime.datetime.now()

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        host=dict(required=True),
        username=dict(required=True),
        password=dict(required=True),
        vrf_name=dict(type='str', default='_public_'),
        peer_addr=dict(type='str', required=True),
        remote_as=dict(type='str', required=True),
        description=dict(type='str'),
        fake_as=dict(type='str'),
        dual_as=dict(choices=['true', 'false']),
        conventional=dict(choices=['true', 'false']),
        route_refresh=dict(choices=['true', 'false']),
        four_byte_as=dict(choices=['true', 'false']),
        is_ignore=dict(choices=['true', 'false']),
        local_if_name=dict(type='str'),
        ebgp_max_hop=dict(type='str'),
        valid_ttl_hops=dict(type='str'),
        connect_mode=dict(choices=['listenOnly', 'connectOnly', 'null']),
        is_log_change=dict(choices=['true', 'false']),
        pswd_type=dict(choices=['null', 'cipher', 'simple']),
        pswd_cipher_text=dict(type='str', no_log=True),
        keep_alive_time=dict(type='str'),
        hold_time=dict(type='str'),
        min_hold_time=dict(type='str'),
        key_chain_name=dict(type='str'),
        conn_retry_time=dict(type='str'),
        tcp_MSS=dict(type='str'),
        mpls_local_ifnet_disable=dict(choices=['true', 'false']),
        prepend_global_as=dict(choices=['true', 'false']),
        prepend_fake_as=dict(choices=['true', 'false']),
        is_bfd_block=dict(choices=['true', 'false']),
        multiplier=dict(type='str'),
        is_bfd_enable=dict(choices=['true', 'false']),
        rx_interval=dict(type='str'),
        tx_interval=dict(type='str'),
        is_single_hop=dict(choices=['true', 'false']))

    if not HAS_NCCLIENT:
        raise Exception("the ncclient library is required")

    module = NetworkModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    state = module.params['state']
    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
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
    tcp_MSS = module.params['tcp_MSS']
    mpls_local_ifnet_disable = module.params['mpls_local_ifnet_disable']
    prepend_global_as = module.params['prepend_global_as']
    prepend_fake_as = module.params['prepend_fake_as']
    is_bfd_block = module.params['is_bfd_block']
    multiplier = module.params['multiplier']
    is_bfd_enable = module.params['is_bfd_enable']
    rx_interval = module.params['rx_interval']
    tx_interval = module.params['tx_interval']
    is_single_hop = module.params['is_single_hop']

    ce_bgp_peer_obj = ce_bgp_neighbor(
        host=host, port=port, username=username, password=password)

    if not ce_bgp_peer_obj:
        module.fail_json(msg='init module failed.')

    need_bgp_peer_enable = ce_bgp_peer_obj.check_bgp_peer_args(module=module)
    need_bgp_peer_other_rst = ce_bgp_peer_obj.check_bgp_peer_other_args(
        module=module)
    need_peer_bfd_merge_rst = ce_bgp_peer_obj.check_peer_bfd_merge_args(
        module=module)
    need_peer_bfd_del_rst = ce_bgp_peer_obj.check_peer_bfd_delete_args(
        module=module)

    args = dict(state=state,
                vrf_name=vrf_name,
                peer_addr=peer_addr,
                remote_as=remote_as,
                description=description,
                fake_as=fake_as,
                dual_as=dual_as,
                conventional=conventional,
                route_refresh=route_refresh,
                four_byte_as=four_byte_as,
                is_ignore=is_ignore,
                local_if_name=local_if_name,
                ebgp_max_hop=ebgp_max_hop,
                valid_ttl_hops=valid_ttl_hops,
                connect_mode=connect_mode,
                is_log_change=is_log_change,
                pswd_type=pswd_type,
                pswd_cipher_text=pswd_cipher_text,
                keep_alive_time=keep_alive_time,
                hold_time=hold_time,
                min_hold_time=min_hold_time,
                key_chain_name=key_chain_name,
                conn_retry_time=conn_retry_time,
                tcp_MSS=tcp_MSS,
                mpls_local_ifnet_disable=mpls_local_ifnet_disable,
                prepend_global_as=prepend_global_as,
                prepend_fake_as=prepend_fake_as,
                is_bfd_block=is_bfd_block,
                multiplier=multiplier,
                is_bfd_enable=is_bfd_enable,
                rx_interval=rx_interval,
                tx_interval=tx_interval,
                is_single_hop=is_single_hop)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = dict()
    end_state = dict()

    # bgp peer config
    if need_bgp_peer_enable["need_cfg"]:

        if state == "present":

            if remote_as:

                bgp_peer_exist = ce_bgp_peer_obj.get_bgp_peer(module=module)
                existing["bgp peer"] = bgp_peer_exist

                bgp_peer_new = (peer_addr, remote_as)

                if len(bgp_peer_exist) == 0:
                    ce_bgp_peer_obj.create_bgp_peer(module=module)
                    changed = True

                elif bgp_peer_new in bgp_peer_exist:
                    pass

                else:
                    ce_bgp_peer_obj.merge_bgp_peer(module=module)
                    changed = True

                bgp_peer_end = ce_bgp_peer_obj.get_bgp_peer(module=module)
                end_state["bgp peer"] = bgp_peer_end

            else:
                pass

        else:

            bgp_peer_exist = ce_bgp_peer_obj.get_bgp_del_peer(module=module)
            existing["bgp peer"] = bgp_peer_exist

            bgp_peer_new = (peer_addr)

            if len(bgp_peer_exist) == 0:
                pass

            elif bgp_peer_new in bgp_peer_exist:
                ce_bgp_peer_obj.delete_bgp_peer(module=module)
                changed = True

            else:
                pass

            bgp_peer_end = ce_bgp_peer_obj.get_bgp_del_peer(module=module)
            end_state["bgp peer"] = bgp_peer_end

    # bgp peer other args
    exist_tmp = dict(
        (k, v) for k, v in need_bgp_peer_other_rst.iteritems() if k is not "need_cfg")
    if exist_tmp:
        existing["bgp peer other"] = exist_tmp

    if need_bgp_peer_other_rst["need_cfg"]:

        if state == "present":
            ce_bgp_peer_obj.merge_bgp_peer_other(module=module)
            changed = True

    need_bgp_peer_other_rst = ce_bgp_peer_obj.check_bgp_peer_other_args(
        module=module)
    end_tmp = dict(
        (k, v) for k, v in need_bgp_peer_other_rst.iteritems() if k is not "need_cfg")
    if end_tmp:
        end_state["bgp peer other"] = end_tmp

    # peer bfd args
    if state == "present":
        exist_tmp = dict(
            (k, v) for k, v in need_peer_bfd_merge_rst.iteritems() if k is not "need_cfg")
        if exist_tmp:
            existing["peer bfd"] = exist_tmp

        if need_peer_bfd_merge_rst["need_cfg"]:
            ce_bgp_peer_obj.merge_peer_bfd(module=module)
            changed = True

        need_peer_bfd_merge_rst = ce_bgp_peer_obj.check_peer_bfd_merge_args(
            module=module)
        end_tmp = dict(
            (k, v) for k, v in need_peer_bfd_merge_rst.iteritems() if k is not "need_cfg")
        if end_tmp:
            end_state["peer bfd"] = end_tmp
    else:
        exist_tmp = dict(
            (k, v) for k, v in need_peer_bfd_del_rst.iteritems() if k is not "need_cfg")
        if exist_tmp:
            existing["peer bfd"] = exist_tmp

        # has already delete with bgp peer

        need_peer_bfd_del_rst = ce_bgp_peer_obj.check_peer_bfd_delete_args(
            module=module)
        end_tmp = dict(
            (k, v) for k, v in need_peer_bfd_del_rst.iteritems() if k is not "need_cfg")
        if end_tmp:
            end_state["peer bfd"] = end_tmp

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state

    end_time = datetime.datetime.now()
    results['execute_time'] = str(end_time - start_time)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
