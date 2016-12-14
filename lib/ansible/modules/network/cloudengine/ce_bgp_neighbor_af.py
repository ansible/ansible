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

module: ce_bgp_af
version_added: "2.2"
short_description: Manages BGP neighbor Address-family configuration.
description:
    - Manages BGP neighbor Address-family configurations on cloudengine switches.
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
            - vpn instance name.
        default: _public_
    af_type:
        description:
            - address-family type.
        required: true
        default: ipv4uni
        choices: ['ipv4uni', 'ipv4multi', 'ipv4vpn', 'ipv6uni', 'ipv6vpn', 'evpn']
    remote_address:
        description:
            - remote as address.
        required: true
        default: none
    advertise_irb:
        description:
            - advertise IRB route.
        default: none
        choices: ['true','false']
    advertise_arp:
        description:
            - advertise ARP route.
        default: none
        choices: ['true','false']
    advertise_remote_nexthop:
        description:
            - advertise remote nexthop.
        default: none
        choices: ['true','false']
    advertise_community:
        description:
            - advertise community.
        default: none
        choices: ['true','false']
    advertise_ext_community:
        description:
            - advertise extended community.
        default: none
        choices: ['true','false']
    discard_ext_community:
        description:
            - discard extended community.
        default: none
        choices: ['true','false']
    allow_as_loop_enable:
        description:
            - allow as loop enable.
        default: none
        choices: ['true','false']
    allow_as_loop_limit:
        description:
            - allow as loop limit.
        default: none
    keep_all_routes:
        description:
            - keep all routes info between as.
        default: none
        choices: ['true','false']
    nexthop_configure:
        description:
            - nexthop configure.
        default: none
        choices: ['null', 'local', 'invariable']
    preferred_value:
        description:
            - preferred value for as.
        default: none
    public_as_only:
        description:
            - public or private as number.
        default: none
        choices: ['true','false']
    public_as_only_force:
        description:
            - force use public as number.
        default: none
        choices: ['true','false']
    public_as_only_limited:
        description:
            - limited use public as number.
        default: none
        choices: ['true','false']
    public_as_only_replace:
        description:
            - private as replaced by public as number.
        default: none
        choices: ['true','false']
    public_as_only_skip_peer_as:
        description:
            - public as only skip peer as.
        default: none
        choices: ['true','false']
    route_limit:
        description:
            - route limited revice from peer.
        default: none
    route_limit_percent:
        description:
            - the percent of route to alarm.
        default: none
    route_limit_type:
        description:
            - route limit type.
        default: none
        choices: ['noparameter', 'alertOnly', 'idleForever', 'idleTimeout']
    route_limit_idle_timeout:
        description:
            - route limit idle timeout.
        default: none
    rt_updt_interval:
        description:
            - route update interval.
        default: none
    redirect_ip:
        description:
            - redirect ip.
        default: none
        choices: ['true','false']
    redirect_ip_vaildation:
        description:
            - redirect ip vaildation.
        default: none
        choices: ['true','false']
    reflect_client:
        description:
            - reflect client.
        default: none
        choices: ['true','false']
    substitute_as_enable:
        description:
            - substitute as enable.
        default: none
        choices: ['true','false']
    import_rt_policy_name:
        description:
            - import route policy name.
        default: none
    export_rt_policy_name:
        description:
            - export route policy name.
        default: none
    import_pref_filt_name:
        description:
            - import pref filter name.
        default: none
    export_pref_filt_name:
        description:
            - export pref filter name.
        default: none
    import_as_path_filter:
        description:
            - import as path filter.
        default: none
    export_as_path_filter:
        description:
            - export as path filter.
        default: none
    import_as_path_name_or_num:
        description:
            - import as path name or num.
        default: none
    export_as_path_name_or_num:
        description:
            - export as path name or num.
        default: none
    import_acl_name_or_num:
        description:
            - import acl name or num.
        default: none
    export_acl_name_or_num:
        description:
            - export acl name or num.
        default: none
    ipprefix_orf_enable:
        description:
            - ipprefix orf enable.
        default: none
    is_nonstd_ipprefix_mod:
        description:
            - is nonstd ipprefix mod.
        default: none
        choices: ['true','false']
    orftype:
        description:
            - orf type.
        default: none
    orf_mode:
        description:
            - orf mode.
        default: none
        choices: ['null', 'receive', 'send', 'both']
    soostring:
        description:
            - soostring.
        default: none
    default_rt_adv_enable:
        description:
            - default route advertise enable.
        default: none
        choices: ['true', 'false']
    default_rt_adv_policy:
        description:
            - default route advertise policy.
        default: none
    default_rt_match_mode:
        description:
            - default route match mode.
        default: none
        choices: ['null', 'matchall', 'matchany']
    add_path_mode:
        description:
            - add path mode.
        default: none
        choices: ['null', 'receive', 'send', 'both']
    adv_add_path_num:
        description:
            - advertise add path num.
        default: none
    origin_as_valid:
        description:
            - origin as valid.
        default: none
        choices: ['true', 'false']
    vpls_enable:
        description:
            - vpls enable.
        default: none
        choices: ['true', 'false']
    vpls_ad_disable:
        description:
            - vpls advertise disable.
        default: none
        choices: ['true', 'false']
    update_pkt_standard_compatible:
        description:
            - update pkt standard compatible.
        default: none
        choices: ['true', 'false']
'''

EXAMPLES = '''
# config BGP peer Address_Family
  - name: "config BGP peer Address_Family"
    ce_bgp_neighbor_af:
        state:  present
        vrf_name:  js
        af_type:  ipv4uni
        remote_address:  192.168.10.10
        nexthop_configure:  null
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
    sample: {"af_type": "ipv4uni", "nexthop_configure": "null",
             "remote_address": "192.168.10.10",
             "state": "present", "vrf_name": "js"}
existing:
    description:
        - k/v pairs of existing aaa server
    type: dict
    sample: {"bgp neighbor af": {"af_type": "ipv4uni", "remote_address": "192.168.10.10",
                                 "vrf_name": "js"},
             "bgp neighbor af other": {"af_type": "ipv4uni", "nexthop_configure": "local",
                                  "vrf_name": "js"}}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bgp neighbor af": {"af_type": "ipv4uni", "remote_address": "192.168.10.10",
                                 "vrf_name": "js"},
             "bgp neighbor af other": {"af_type": "ipv4uni", "nexthop_configure": "null",
                                  "vrf_name": "js"}}
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


# get bgp peer af
CE_GET_BGP_PEER_AF_HEADER = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <peerAFs>
                    <peerAF>
                      <remoteAddress></remoteAddress>
"""
CE_GET_BGP_PEER_AF_TAIL = """
                    </peerAF>
                  </peerAFs>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </filter>
"""

# merge bgp peer af
CE_MERGE_BGP_PEER_AF_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <peerAFs>
                    <peerAF operation="merge">
                      <remoteAddress>%s</remoteAddress>
"""
CE_MERGE_BGP_PEER_AF_TAIL = """
                    </peerAF>
                  </peerAFs>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# create bgp peer af
CE_CREATE_BGP_PEER_AF = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <peerAFs>
                    <peerAF operation="create">
                      <remoteAddress>%s</remoteAddress>
                    </peerAF>
                  </peerAFs>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# delete bgp peer af
CE_DELETE_BGP_PEER_AF = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <peerAFs>
                    <peerAF operation="delete">
                      <remoteAddress>%s</remoteAddress>
                    </peerAF>
                  </peerAFs>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""


class ce_bgp_neighbor_af(object):
    """ Manages BGP neighbor Address-family configuration """

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

    def check_bgp_neighbor_af_args(self, **kwargs):
        """check_bgp_neighbor_af_args"""

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)

        state = module.params['state']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        if self.check_ip_addr(ipaddr=remote_address) == False:
            module.fail_json(
                msg='the remote_address %s is invalid.' % remote_address)

        conf_str = CE_GET_BGP_PEER_AF_HEADER % (
            vrf_name, af_type) + CE_GET_BGP_PEER_AF_TAIL
        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        if state == "present":
            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<remoteAddress>(.*)</remoteAddress>.*', con_obj.xml)

                if re_find:
                    result["remote_address"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != remote_address:
                        need_cfg = True
                else:
                    need_cfg = True
        else:
            if "<data/>" in con_obj.xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<remoteAddress>(.*)</remoteAddress>.*', con_obj.xml)

                if re_find:
                    result["remote_address"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] == remote_address:
                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_neighbor_af_other(self, **kwargs):
        """check_bgp_neighbor_af_other"""

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        state = module.params['state']
        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']

        if state == "absent":
            result["need_cfg"] = need_cfg
            return result

        advertise_irb = module.params['advertise_irb']
        if advertise_irb:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseIrb></advertiseIrb>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseIrb>(.*)</advertiseIrb>.*', con_obj.xml)

                if re_find:
                    result["advertise_irb"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_irb:
                        need_cfg = True
                else:
                    need_cfg = True

        advertise_arp = module.params['advertise_arp']
        if advertise_arp:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseArp></advertiseArp>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseArp>(.*)</advertiseArp>.*', con_obj.xml)

                if re_find:
                    result["advertise_arp"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_arp:
                        need_cfg = True
                else:
                    need_cfg = True

        advertise_remote_nexthop = module.params['advertise_remote_nexthop']
        if advertise_remote_nexthop:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseRemoteNexthop></advertiseRemoteNexthop>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseRemoteNexthop>(.*)</advertiseRemoteNexthop>.*', con_obj.xml)

                if re_find:
                    result["advertise_remote_nexthop"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_remote_nexthop:
                        need_cfg = True
                else:
                    need_cfg = True

        advertise_community = module.params['advertise_community']
        if advertise_community:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseCommunity></advertiseCommunity>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseCommunity>(.*)</advertiseCommunity>.*', con_obj.xml)

                if re_find:
                    result["advertise_community"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_community:
                        need_cfg = True
                else:
                    need_cfg = True

        advertise_ext_community = module.params['advertise_ext_community']
        if advertise_ext_community:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseExtCommunity></advertiseExtCommunity>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseExtCommunity>(.*)</advertiseExtCommunity>.*', con_obj.xml)

                if re_find:
                    result["advertise_ext_community"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_ext_community:
                        need_cfg = True
                else:
                    need_cfg = True

        discard_ext_community = module.params['discard_ext_community']
        if discard_ext_community:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<discardExtCommunity></discardExtCommunity>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<discardExtCommunity>(.*)</discardExtCommunity>.*', con_obj.xml)

                if re_find:
                    result["discard_ext_community"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != discard_ext_community:
                        need_cfg = True
                else:
                    need_cfg = True

        allow_as_loop_enable = module.params['allow_as_loop_enable']
        if allow_as_loop_enable:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<allowAsLoopEnable></allowAsLoopEnable>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<allowAsLoopEnable>(.*)</allowAsLoopEnable>.*', con_obj.xml)

                if re_find:
                    result["allow_as_loop_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != allow_as_loop_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        allow_as_loop_limit = module.params['allow_as_loop_limit']
        if allow_as_loop_limit:
            if int(allow_as_loop_limit) > 10 or int(allow_as_loop_limit) < 1:
                module.fail_json(
                    msg='the value of allow_as_loop_limit %s is out of [1 - 10].' % allow_as_loop_limit)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<allowAsLoopLimit></allowAsLoopLimit>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<allowAsLoopLimit>(.*)</allowAsLoopLimit>.*', con_obj.xml)

                if re_find:
                    result["allow_as_loop_limit"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != allow_as_loop_limit:
                        need_cfg = True
                else:
                    need_cfg = True

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<keepAllRoutes></keepAllRoutes>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<keepAllRoutes>(.*)</keepAllRoutes>.*', con_obj.xml)

                if re_find:
                    result["keep_all_routes"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != keep_all_routes:
                        need_cfg = True
                else:
                    need_cfg = True

        nexthop_configure = module.params['nexthop_configure']
        if nexthop_configure:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<nextHopConfigure></nextHopConfigure>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<nextHopConfigure>(.*)</nextHopConfigure>.*', con_obj.xml)

                if re_find:
                    result["nexthop_configure"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != nexthop_configure:
                        need_cfg = True
                else:
                    need_cfg = True

        preferred_value = module.params['preferred_value']
        if preferred_value:
            if int(preferred_value) > 65535 or int(preferred_value) < 0:
                module.fail_json(
                    msg='the value of preferred_value %s is out of [0 - 65535].' % preferred_value)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<preferredValue></preferredValue>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<preferredValue>(.*)</preferredValue>.*', con_obj.xml)

                if re_find:
                    result["preferred_value"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != preferred_value:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only = module.params['public_as_only']
        if public_as_only:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnly></publicAsOnly>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnly>(.*)</publicAsOnly>.*', con_obj.xml)

                if re_find:
                    result["public_as_only"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != public_as_only:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only_force = module.params['public_as_only_force']
        if public_as_only_force:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnlyForce></publicAsOnlyForce>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnlyForce>(.*)</publicAsOnlyForce>.*', con_obj.xml)

                if re_find:
                    result["public_as_only_force"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != public_as_only_force:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only_limited = module.params['public_as_only_limited']
        if public_as_only_limited:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnlyLimited></publicAsOnlyLimited>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnlyLimited>(.*)</publicAsOnlyLimited>.*', con_obj.xml)

                if re_find:
                    result["public_as_only_limited"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != public_as_only_limited:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only_replace = module.params['public_as_only_replace']
        if public_as_only_replace:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnlyReplace></publicAsOnlyReplace>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnlyReplace>(.*)</publicAsOnlyReplace>.*', con_obj.xml)

                if re_find:
                    result["public_as_only_replace"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != public_as_only_replace:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only_skip_peer_as = module.params[
            'public_as_only_skip_peer_as']
        if public_as_only_skip_peer_as:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnlySkipPeerAs></publicAsOnlySkipPeerAs>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnlySkipPeerAs>(.*)</publicAsOnlySkipPeerAs>.*', con_obj.xml)

                if re_find:
                    result["public_as_only_skip_peer_as"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != public_as_only_skip_peer_as:
                        need_cfg = True
                else:
                    need_cfg = True

        route_limit = module.params['route_limit']
        if route_limit:

            if int(route_limit) < 1:
                module.fail_json(
                    msg='the value of route_limit %s is out of [1 - 4294967295].' % route_limit)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<routeLimit></routeLimit>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeLimit>(.*)</routeLimit>.*', con_obj.xml)

                if re_find:
                    result["route_limit"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != route_limit:
                        need_cfg = True
                else:
                    need_cfg = True

        route_limit_percent = module.params['route_limit_percent']
        if route_limit_percent:

            if int(route_limit_percent) < 1 or int(route_limit_percent) > 100:
                module.fail_json(
                    msg='the value of route_limit_percent %s is out of [1 - 100].' % route_limit_percent)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<routeLimitPercent></routeLimitPercent>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeLimitPercent>(.*)</routeLimitPercent>.*', con_obj.xml)

                if re_find:
                    result["route_limit_percent"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != route_limit_percent:
                        need_cfg = True
                else:
                    need_cfg = True

        route_limit_type = module.params['route_limit_type']
        if route_limit_type:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<routeLimitType></routeLimitType>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeLimitType>(.*)</routeLimitType>.*', con_obj.xml)

                if re_find:
                    result["route_limit_type"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != route_limit_type:
                        need_cfg = True
                else:
                    need_cfg = True

        route_limit_idle_timeout = module.params['route_limit_idle_timeout']
        if route_limit_idle_timeout:

            if int(route_limit_idle_timeout) < 1 or int(route_limit_idle_timeout) > 1200:
                module.fail_json(
                    msg='the value of route_limit_idle_timeout %s is out of [1 - 1200].' % route_limit_idle_timeout)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<routeLimitIdleTimeout></routeLimitPercent>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeLimitIdleTimeout>(.*)</routeLimitIdleTimeout>.*', con_obj.xml)

                if re_find:
                    result["route_limit_idle_timeout"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != route_limit_idle_timeout:
                        need_cfg = True
                else:
                    need_cfg = True

        rt_updt_interval = module.params['rt_updt_interval']
        if rt_updt_interval:

            if int(rt_updt_interval) < 0 or int(rt_updt_interval) > 600:
                module.fail_json(
                    msg='the value of rt_updt_interval %s is out of [0 - 600].' % rt_updt_interval)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<rtUpdtInterval></rtUpdtInterval>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<rtUpdtInterval>(.*)</rtUpdtInterval>.*', con_obj.xml)

                if re_find:
                    result["rt_updt_interval"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != rt_updt_interval:
                        need_cfg = True
                else:
                    need_cfg = True

        redirect_ip = module.params['redirect_ip']
        if redirect_ip:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<redirectIP></redirectIP>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<redirectIP>(.*)</redirectIP>.*', con_obj.xml)

                if re_find:
                    result["redirect_ip"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != redirect_ip:
                        need_cfg = True
                else:
                    need_cfg = True

        redirect_ip_vaildation = module.params['redirect_ip_vaildation']
        if redirect_ip_vaildation:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<redirectIPVaildation></redirectIPVaildation>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<redirectIPVaildation>(.*)</redirectIPVaildation>.*', con_obj.xml)

                if re_find:
                    result["redirect_ip_vaildation"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != redirect_ip_vaildation:
                        need_cfg = True
                else:
                    need_cfg = True

        reflect_client = module.params['reflect_client']
        if reflect_client:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<reflectClient></reflectClient>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectClient>(.*)</reflectClient>.*', con_obj.xml)

                if re_find:
                    result["reflect_client"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != reflect_client:
                        need_cfg = True
                else:
                    need_cfg = True

        substitute_as_enable = module.params['substitute_as_enable']
        if substitute_as_enable:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<substituteAsEnable></substituteAsEnable>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<substituteAsEnable>(.*)</substituteAsEnable>.*', con_obj.xml)

                if re_find:
                    result["substitute_as_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != substitute_as_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        import_rt_policy_name = module.params['import_rt_policy_name']
        if import_rt_policy_name:

            if len(import_rt_policy_name) < 1 or len(import_rt_policy_name) > 40:
                module.fail_json(
                    msg='the len of import_rt_policy_name %s is out of [1 - 40].' % import_rt_policy_name)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importRtPolicyName></importRtPolicyName>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importRtPolicyName>(.*)</importRtPolicyName>.*', con_obj.xml)

                if re_find:
                    result["import_rt_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != import_rt_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        export_rt_policy_name = module.params['export_rt_policy_name']
        if export_rt_policy_name:

            if len(export_rt_policy_name) < 1 or len(export_rt_policy_name) > 40:
                module.fail_json(
                    msg='the len of export_rt_policy_name %s is out of [1 - 40].' % export_rt_policy_name)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportRtPolicyName></exportRtPolicyName>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportRtPolicyName>(.*)</exportRtPolicyName>.*', con_obj.xml)

                if re_find:
                    result["export_rt_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != export_rt_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        import_pref_filt_name = module.params['import_pref_filt_name']
        if import_pref_filt_name:

            if len(import_pref_filt_name) < 1 or len(import_pref_filt_name) > 169:
                module.fail_json(
                    msg='the len of import_pref_filt_name %s is out of [1 - 169].' % import_pref_filt_name)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importPrefFiltName></importPrefFiltName>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importPrefFiltName>(.*)</importPrefFiltName>.*', con_obj.xml)

                if re_find:
                    result["import_pref_filt_name"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != import_pref_filt_name:
                        need_cfg = True
                else:
                    need_cfg = True

        export_pref_filt_name = module.params['export_pref_filt_name']
        if export_pref_filt_name:

            if len(export_pref_filt_name) < 1 or len(export_pref_filt_name) > 169:
                module.fail_json(
                    msg='the len of export_pref_filt_name %s is out of [1 - 169].' % export_pref_filt_name)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportPrefFiltName></exportPrefFiltName>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportPrefFiltName>(.*)</exportPrefFiltName>.*', con_obj.xml)

                if re_find:
                    result["export_pref_filt_name"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != export_pref_filt_name:
                        need_cfg = True
                else:
                    need_cfg = True

        import_as_path_filter = module.params['import_as_path_filter']
        if import_as_path_filter:

            if int(import_as_path_filter) < 1 or int(import_as_path_filter) > 256:
                module.fail_json(
                    msg='the value of import_as_path_filter %s is out of [1 - 256].' % import_as_path_filter)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importAsPathFilter></importAsPathFilter>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importAsPathFilter>(.*)</importAsPathFilter>.*', con_obj.xml)

                if re_find:
                    result["import_as_path_filter"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != import_as_path_filter:
                        need_cfg = True
                else:
                    need_cfg = True

        export_as_path_filter = module.params['export_as_path_filter']
        if export_as_path_filter:

            if int(export_as_path_filter) < 1 or int(export_as_path_filter) > 256:
                module.fail_json(
                    msg='the value of export_as_path_filter %s is out of [1 - 256].' % export_as_path_filter)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportAsPathFilter></exportAsPathFilter>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportAsPathFilter>(.*)</exportAsPathFilter>.*', con_obj.xml)

                if re_find:
                    result["export_as_path_filter"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != export_as_path_filter:
                        need_cfg = True
                else:
                    need_cfg = True

        import_as_path_name_or_num = module.params[
            'import_as_path_name_or_num']
        if import_as_path_name_or_num:

            if len(import_as_path_name_or_num) < 1 or len(import_as_path_name_or_num) > 51:
                module.fail_json(
                    msg='the len of import_as_path_name_or_num %s is out of [1 - 51].' % import_as_path_name_or_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importAsPathNameOrNum></importAsPathNameOrNum>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importAsPathNameOrNum>(.*)</importAsPathNameOrNum>.*', con_obj.xml)

                if re_find:
                    result["import_as_path_name_or_num"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != import_as_path_name_or_num:
                        need_cfg = True
                else:
                    need_cfg = True

        export_as_path_name_or_num = module.params[
            'export_as_path_name_or_num']
        if export_as_path_name_or_num:

            if len(export_as_path_name_or_num) < 1 or len(export_as_path_name_or_num) > 51:
                module.fail_json(
                    msg='the len of export_as_path_name_or_num %s is out of [1 - 51].' % export_as_path_name_or_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportAsPathNameOrNum></exportAsPathNameOrNum>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportAsPathNameOrNum>(.*)</exportAsPathNameOrNum>.*', con_obj.xml)

                if re_find:
                    result["export_as_path_name_or_num"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != export_as_path_name_or_num:
                        need_cfg = True
                else:
                    need_cfg = True

        import_acl_name_or_num = module.params['import_acl_name_or_num']
        if import_acl_name_or_num:

            if len(import_acl_name_or_num) < 1 or len(import_acl_name_or_num) > 32:
                module.fail_json(
                    msg='the len of import_acl_name_or_num %s is out of [1 - 32].' % import_acl_name_or_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importAclNameOrNum></importAclNameOrNum>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importAclNameOrNum>(.*)</importAclNameOrNum>.*', con_obj.xml)

                if re_find:
                    result["import_acl_name_or_num"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != import_acl_name_or_num:
                        need_cfg = True
                else:
                    need_cfg = True

        export_acl_name_or_num = module.params['export_acl_name_or_num']
        if export_acl_name_or_num:

            if len(export_acl_name_or_num) < 1 or len(export_acl_name_or_num) > 32:
                module.fail_json(
                    msg='the len of export_acl_name_or_num %s is out of [1 - 32].' % export_acl_name_or_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportAclNameOrNum></exportAclNameOrNum>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportAclNameOrNum>(.*)</exportAclNameOrNum>.*', con_obj.xml)

                if re_find:
                    result["export_acl_name_or_num"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != export_acl_name_or_num:
                        need_cfg = True
                else:
                    need_cfg = True

        ipprefix_orf_enable = module.params['ipprefix_orf_enable']
        if ipprefix_orf_enable:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<ipprefixOrfEnable></ipprefixOrfEnable>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ipprefixOrfEnable>(.*)</ipprefixOrfEnable>.*', con_obj.xml)

                if re_find:
                    result["ipprefix_orf_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != ipprefix_orf_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        is_nonstd_ipprefix_mod = module.params['is_nonstd_ipprefix_mod']
        if is_nonstd_ipprefix_mod:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<isNonstdIpprefixMod></isNonstdIpprefixMod>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isNonstdIpprefixMod>(.*)</isNonstdIpprefixMod>.*', con_obj.xml)

                if re_find:
                    result["is_nonstd_ipprefix_mod"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != is_nonstd_ipprefix_mod:
                        need_cfg = True
                else:
                    need_cfg = True

        orftype = module.params['orftype']
        if orftype:

            if int(orftype) < 0 or int(orftype) > 65535:
                module.fail_json(
                    msg='the value of orftype %s is out of [0 - 65535].' % orftype)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<orftype></orftype>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<orftype>(.*)</orftype>.*', con_obj.xml)

                if re_find:
                    result["orftype"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != orftype:
                        need_cfg = True
                else:
                    need_cfg = True

        orf_mode = module.params['orf_mode']
        if orf_mode:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<orfMode></orfMode>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<orfMode>(.*)</orfMode>.*', con_obj.xml)

                if re_find:
                    result["orf_mode"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != orf_mode:
                        need_cfg = True
                else:
                    need_cfg = True

        soostring = module.params['soostring']
        if soostring:

            if len(soostring) < 3 or len(soostring) > 21:
                module.fail_json(
                    msg='the len of soostring %s is out of [3 - 21].' % soostring)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<soostring></soostring>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<soostring>(.*)</soostring>.*', con_obj.xml)

                if re_find:
                    result["soostring"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != soostring:
                        need_cfg = True
                else:
                    need_cfg = True

        default_rt_adv_enable = module.params['default_rt_adv_enable']
        if default_rt_adv_enable:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<defaultRtAdvEnable></defaultRtAdvEnable>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultRtAdvEnable>(.*)</defaultRtAdvEnable>.*', con_obj.xml)

                if re_find:
                    result["default_rt_adv_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != default_rt_adv_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        default_rt_adv_policy = module.params['default_rt_adv_policy']
        if default_rt_adv_policy:

            if len(default_rt_adv_policy) < 1 or len(default_rt_adv_policy) > 40:
                module.fail_json(
                    msg='the len of default_rt_adv_policy %s is out of [1 - 40].' % default_rt_adv_policy)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<defaultRtAdvPolicy></defaultRtAdvPolicy>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultRtAdvPolicy>(.*)</defaultRtAdvPolicy>.*', con_obj.xml)

                if re_find:
                    result["default_rt_adv_policy"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != default_rt_adv_policy:
                        need_cfg = True
                else:
                    need_cfg = True

        default_rt_match_mode = module.params['default_rt_match_mode']
        if default_rt_match_mode:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<defaultRtMatchMode></defaultRtMatchMode>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultRtMatchMode>(.*)</defaultRtMatchMode>.*', con_obj.xml)

                if re_find:
                    result["default_rt_match_mode"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != default_rt_match_mode:
                        need_cfg = True
                else:
                    need_cfg = True

        add_path_mode = module.params['add_path_mode']
        if add_path_mode:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<addPathMode></addPathMode>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<addPathMode>(.*)</addPathMode>.*', con_obj.xml)

                if re_find:
                    result["add_path_mode"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != add_path_mode:
                        need_cfg = True
                else:
                    need_cfg = True

        adv_add_path_num = module.params['adv_add_path_num']
        if adv_add_path_num:

            if int(orftype) < 2 or int(orftype) > 64:
                module.fail_json(
                    msg='the value of adv_add_path_num %s is out of [2 - 64].' % adv_add_path_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advAddPathNum></advAddPathNum>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advAddPathNum>(.*)</advAddPathNum>.*', con_obj.xml)

                if re_find:
                    result["adv_add_path_num"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != adv_add_path_num:
                        need_cfg = True
                else:
                    need_cfg = True

        origin_as_valid = module.params['origin_as_valid']
        if origin_as_valid:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<originAsValid></originAsValid>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<originAsValid>(.*)</originAsValid>.*', con_obj.xml)

                if re_find:
                    result["origin_as_valid"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != origin_as_valid:
                        need_cfg = True
                else:
                    need_cfg = True

        vpls_enable = module.params['vpls_enable']
        if vpls_enable:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<vplsEnable></vplsEnable>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<vplsEnable>(.*)</vplsEnable>.*', con_obj.xml)

                if re_find:
                    result["vpls_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != vpls_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        vpls_ad_disable = module.params['vpls_ad_disable']
        if vpls_ad_disable:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<vplsAdDisable></vplsAdDisable>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<vplsAdDisable>(.*)</vplsAdDisable>.*', con_obj.xml)

                if re_find:
                    result["vpls_ad_disable"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != vpls_ad_disable:
                        need_cfg = True
                else:
                    need_cfg = True

        update_pkt_standard_compatible = module.params[
            'update_pkt_standard_compatible']
        if update_pkt_standard_compatible:

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<updatePktStandardCompatible></updatePktStandardCompatible>" + CE_GET_BGP_PEER_AF_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<updatePktStandardCompatible>(.*)</updatePktStandardCompatible>.*', con_obj.xml)

                if re_find:
                    result["update_pkt_standard_compatible"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != update_pkt_standard_compatible:
                        need_cfg = True
                else:
                    need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def merge_bgp_peer_af(self, **kwargs):
        """merge_bgp_peer_af"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        conf_str = CE_MERGE_BGP_PEER_AF_HEADER % (
            vrf_name, af_type, remote_address) + CE_MERGE_BGP_PEER_AF_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp peer address family failed.')

        return SUCCESS

    def create_bgp_peer_af(self, **kwargs):
        """create_bgp_peer_af"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        conf_str = CE_CREATE_BGP_PEER_AF % (vrf_name, af_type, remote_address)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create bgp peer address family failed.')

        return SUCCESS

    def delete_bgp_peer_af(self, **kwargs):
        """delete_bgp_peer_af"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        conf_str = CE_DELETE_BGP_PEER_AF % (vrf_name, af_type, remote_address)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete bgp peer address family failed.')

        return SUCCESS

    def merge_bgp_peer_af_other(self, **kwargs):
        """merge_bgp_peer_af_other"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        conf_str = CE_MERGE_BGP_PEER_AF_HEADER % (
            vrf_name, af_type, remote_address)

        advertise_irb = module.params['advertise_irb']
        if advertise_irb:
            conf_str += "<advertiseIrb>%s</advertiseIrb>" % advertise_irb

        advertise_arp = module.params['advertise_arp']
        if advertise_arp:
            conf_str += "<advertiseArp>%s</advertiseArp>" % advertise_arp

        advertise_remote_nexthop = module.params['advertise_remote_nexthop']
        if advertise_remote_nexthop:
            conf_str += "<advertiseRemoteNexthop>%s</advertiseRemoteNexthop>" % advertise_remote_nexthop

        advertise_community = module.params['advertise_community']
        if advertise_community:
            conf_str += "<advertiseCommunity>%s</advertiseCommunity>" % advertise_community

        advertise_ext_community = module.params['advertise_ext_community']
        if advertise_ext_community:
            conf_str += "<advertiseExtCommunity>%s</advertiseExtCommunity>" % advertise_ext_community

        discard_ext_community = module.params['discard_ext_community']
        if discard_ext_community:
            conf_str += "<discardExtCommunity>%s</discardExtCommunity>" % discard_ext_community

        allow_as_loop_enable = module.params['allow_as_loop_enable']
        if allow_as_loop_enable:
            conf_str += "<allowAsLoopEnable>%s</allowAsLoopEnable>" % allow_as_loop_enable

        allow_as_loop_limit = module.params['allow_as_loop_limit']
        if allow_as_loop_limit:
            conf_str += "<allowAsLoopLimit>%s</allowAsLoopLimit>" % allow_as_loop_limit

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes:
            conf_str += "<keepAllRoutes>%s</keepAllRoutes>" % keep_all_routes

        nexthop_configure = module.params['nexthop_configure']
        if nexthop_configure:
            conf_str += "<nextHopConfigure>%s</nextHopConfigure>" % nexthop_configure

        preferred_value = module.params['preferred_value']
        if preferred_value:
            conf_str += "<preferredValue>%s</preferredValue>" % preferred_value

        public_as_only = module.params['public_as_only']
        if public_as_only:
            conf_str += "<publicAsOnly>%s</publicAsOnly>" % public_as_only

        public_as_only_force = module.params['public_as_only_force']
        if public_as_only_force:
            conf_str += "<publicAsOnlyForce>%s</publicAsOnlyForce>" % public_as_only_force

        public_as_only_limited = module.params['public_as_only_limited']
        if public_as_only_limited:
            conf_str += "<publicAsOnlyLimited>%s</publicAsOnlyLimited>" % public_as_only_limited

        public_as_only_replace = module.params['public_as_only_replace']
        if public_as_only_replace:
            conf_str += "<publicAsOnlyReplace>%s</publicAsOnlyReplace>" % public_as_only_replace

        public_as_only_skip_peer_as = module.params[
            'public_as_only_skip_peer_as']
        if public_as_only_skip_peer_as:
            conf_str += "<publicAsOnlySkipPeerAs>%s</publicAsOnlySkipPeerAs>" % public_as_only_skip_peer_as

        route_limit = module.params['route_limit']
        if route_limit:
            conf_str += "<routeLimit>%s</routeLimit>" % route_limit

        route_limit_percent = module.params['route_limit_percent']
        if route_limit_percent:
            conf_str += "<routeLimitPercent>%s</routeLimitPercent>" % route_limit_percent

        route_limit_type = module.params['route_limit_type']
        if route_limit_type:
            conf_str += "<routeLimitType>%s</routeLimitType>" % route_limit_type

        route_limit_idle_timeout = module.params['route_limit_idle_timeout']
        if route_limit_idle_timeout:
            conf_str += "<routeLimitIdleTimeout>%s</routeLimitIdleTimeout>" % route_limit_idle_timeout

        rt_updt_interval = module.params['rt_updt_interval']
        if rt_updt_interval:
            conf_str += "<rtUpdtInterval>%s</rtUpdtInterval>" % rt_updt_interval

        redirect_ip = module.params['redirect_ip']
        if redirect_ip:
            conf_str += "<redirectIP>%s</redirectIP>" % redirect_ip

        redirect_ip_vaildation = module.params['redirect_ip_vaildation']
        if redirect_ip_vaildation:
            conf_str += "<redirectIPVaildation>%s</redirectIPVaildation>" % redirect_ip_vaildation

        reflect_client = module.params['reflect_client']
        if reflect_client:
            conf_str += "<reflectClient>%s</reflectClient>" % reflect_client

        substitute_as_enable = module.params['substitute_as_enable']
        if substitute_as_enable:
            conf_str += "<substituteAsEnable>%s</substituteAsEnable>" % substitute_as_enable

        import_rt_policy_name = module.params['import_rt_policy_name']
        if import_rt_policy_name:
            conf_str += "<importRtPolicyName>%s</importRtPolicyName>" % import_rt_policy_name

        export_rt_policy_name = module.params['export_rt_policy_name']
        if export_rt_policy_name:
            conf_str += "<exportRtPolicyName>%s</exportRtPolicyName>" % export_rt_policy_name

        import_pref_filt_name = module.params['import_pref_filt_name']
        if import_pref_filt_name:
            conf_str += "<importPrefFiltName>%s</importPrefFiltName>" % import_pref_filt_name

        export_pref_filt_name = module.params['export_pref_filt_name']
        if export_pref_filt_name:
            conf_str += "<exportPrefFiltName>%s</exportPrefFiltName>" % export_pref_filt_name

        import_as_path_filter = module.params['import_as_path_filter']
        if import_as_path_filter:
            conf_str += "<importAsPathFilter>%s</importAsPathFilter>" % import_as_path_filter

        export_as_path_filter = module.params['export_as_path_filter']
        if export_as_path_filter:
            conf_str += "<exportAsPathFilter>%s</exportAsPathFilter>" % export_as_path_filter

        import_as_path_name_or_num = module.params[
            'import_as_path_name_or_num']
        if import_as_path_name_or_num:
            conf_str += "<importAsPathNameOrNum>%s</importAsPathNameOrNum>" % import_as_path_name_or_num

        export_as_path_name_or_num = module.params[
            'export_as_path_name_or_num']
        if export_as_path_name_or_num:
            conf_str += "<exportAsPathNameOrNum>%s</exportAsPathNameOrNum>" % export_as_path_name_or_num

        import_acl_name_or_num = module.params['import_acl_name_or_num']
        if import_acl_name_or_num:
            conf_str += "<importAclNameOrNum>%s</importAclNameOrNum>" % import_acl_name_or_num

        export_acl_name_or_num = module.params['export_acl_name_or_num']
        if export_acl_name_or_num:
            conf_str += "<exportAclNameOrNum>%s</exportAclNameOrNum>" % export_acl_name_or_num

        ipprefix_orf_enable = module.params['ipprefix_orf_enable']
        if ipprefix_orf_enable:
            conf_str += "<ipprefixOrfEnable>%s</ipprefixOrfEnable>" % ipprefix_orf_enable

        is_nonstd_ipprefix_mod = module.params['is_nonstd_ipprefix_mod']
        if is_nonstd_ipprefix_mod:
            conf_str += "<isNonstdIpprefixMod>%s</isNonstdIpprefixMod>" % is_nonstd_ipprefix_mod

        orftype = module.params['orftype']
        if orftype:
            conf_str += "<orftype>%s</orftype>" % orftype

        orf_mode = module.params['orf_mode']
        if orf_mode:
            conf_str += "<orfMode>%s</orfMode>" % orf_mode

        soostring = module.params['soostring']
        if soostring:
            conf_str += "<soostring>%s</soostring>" % soostring

        default_rt_adv_enable = module.params['default_rt_adv_enable']
        if default_rt_adv_enable:
            conf_str += "<defaultRtAdvEnable>%s</defaultRtAdvEnable>" % default_rt_adv_enable

        default_rt_adv_policy = module.params['default_rt_adv_policy']
        if default_rt_adv_policy:
            conf_str += "<defaultRtAdvPolicy>%s</defaultRtAdvPolicy>" % default_rt_adv_policy

        default_rt_match_mode = module.params['default_rt_match_mode']
        if default_rt_match_mode:
            conf_str += "<defaultRtMatchMode>%s</defaultRtMatchMode>" % default_rt_match_mode

        add_path_mode = module.params['add_path_mode']
        if add_path_mode:
            conf_str += "<addPathMode>%s</addPathMode>" % add_path_mode

        adv_add_path_num = module.params['adv_add_path_num']
        if adv_add_path_num:
            conf_str += "<advAddPathNum>%s</advAddPathNum>" % adv_add_path_num

        origin_as_valid = module.params['origin_as_valid']
        if origin_as_valid:
            conf_str += "<originAsValid>%s</originAsValid>" % origin_as_valid

        vpls_enable = module.params['vpls_enable']
        if vpls_enable:
            conf_str += "<vplsEnable>%s</vplsEnable>" % vpls_enable

        vpls_ad_disable = module.params['vpls_ad_disable']
        if vpls_ad_disable:
            conf_str += "<vplsAdDisable>%s</vplsAdDisable>" % vpls_ad_disable

        update_pkt_standard_compatible = module.params[
            'update_pkt_standard_compatible']
        if update_pkt_standard_compatible:
            conf_str += "<updatePktStandardCompatible>%s</updatePktStandardCompatible>" % update_pkt_standard_compatible

        conf_str += CE_MERGE_BGP_PEER_AF_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp peer address family other failed.')

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
        af_type=dict(choices=['ipv4uni', 'ipv4multi', 'ipv4vpn',
                              'ipv6uni', 'ipv6vpn', 'evpn'], required=True),
        remote_address=dict(type='str', required=True),
        advertise_irb=dict(choices=['true', 'false']),
        advertise_arp=dict(choices=['true', 'false']),
        advertise_remote_nexthop=dict(choices=['true', 'false']),
        advertise_community=dict(choices=['true', 'false']),
        advertise_ext_community=dict(choices=['true', 'false']),
        discard_ext_community=dict(choices=['true', 'false']),
        allow_as_loop_enable=dict(choices=['true', 'false']),
        allow_as_loop_limit=dict(type='str'),
        keep_all_routes=dict(choices=['true', 'false']),
        nexthop_configure=dict(choices=['null', 'local', 'invariable']),
        preferred_value=dict(type='str'),
        public_as_only=dict(choices=['true', 'false']),
        public_as_only_force=dict(choices=['true', 'false']),
        public_as_only_limited=dict(choices=['true', 'false']),
        public_as_only_replace=dict(choices=['true', 'false']),
        public_as_only_skip_peer_as=dict(choices=['true', 'false']),
        route_limit=dict(type='str'),
        route_limit_percent=dict(type='str'),
        route_limit_type=dict(
            choices=['noparameter', 'alertOnly', 'idleForever', 'idleTimeout']),
        route_limit_idle_timeout=dict(type='str'),
        rt_updt_interval=dict(type='str'),
        redirect_ip=dict(choices=['true', 'false']),
        redirect_ip_vaildation=dict(choices=['true', 'false']),
        reflect_client=dict(choices=['true', 'false']),
        substitute_as_enable=dict(choices=['true', 'false']),
        import_rt_policy_name=dict(type='str'),
        export_rt_policy_name=dict(type='str'),
        import_pref_filt_name=dict(type='str'),
        export_pref_filt_name=dict(type='str'),
        import_as_path_filter=dict(type='str'),
        export_as_path_filter=dict(type='str'),
        import_as_path_name_or_num=dict(type='str'),
        export_as_path_name_or_num=dict(type='str'),
        import_acl_name_or_num=dict(type='str'),
        export_acl_name_or_num=dict(type='str'),
        ipprefix_orf_enable=dict(choices=['true', 'false']),
        is_nonstd_ipprefix_mod=dict(choices=['true', 'false']),
        orftype=dict(type='str'),
        orf_mode=dict(choices=['null', 'receive', 'send', 'both']),
        soostring=dict(type='str'),
        default_rt_adv_enable=dict(choices=['true', 'false']),
        default_rt_adv_policy=dict(type='str'),
        default_rt_match_mode=dict(choices=['null', 'matchall', 'matchany']),
        add_path_mode=dict(choices=['null', 'receive', 'send', 'both']),
        adv_add_path_num=dict(type='str'),
        origin_as_valid=dict(choices=['true', 'false']),
        vpls_enable=dict(choices=['true', 'false']),
        vpls_ad_disable=dict(choices=['true', 'false']),
        update_pkt_standard_compatible=dict(choices=['true', 'false']))

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
    af_type = module.params['af_type']
    remote_address = module.params['remote_address']
    advertise_irb = module.params['advertise_irb']
    advertise_arp = module.params['advertise_arp']
    advertise_remote_nexthop = module.params['advertise_remote_nexthop']
    advertise_community = module.params['advertise_community']
    advertise_ext_community = module.params['advertise_ext_community']
    discard_ext_community = module.params['discard_ext_community']
    allow_as_loop_enable = module.params['allow_as_loop_enable']
    allow_as_loop_limit = module.params['allow_as_loop_limit']
    keep_all_routes = module.params['keep_all_routes']
    nexthop_configure = module.params['nexthop_configure']
    preferred_value = module.params['preferred_value']
    public_as_only = module.params['public_as_only']
    public_as_only_force = module.params['public_as_only_force']
    public_as_only_limited = module.params['public_as_only_limited']
    public_as_only_replace = module.params['public_as_only_replace']
    public_as_only_skip_peer_as = module.params['public_as_only_skip_peer_as']
    route_limit = module.params['route_limit']
    route_limit_percent = module.params['route_limit_percent']
    route_limit_type = module.params['route_limit_type']
    route_limit_idle_timeout = module.params['route_limit_idle_timeout']
    rt_updt_interval = module.params['rt_updt_interval']
    redirect_ip = module.params['redirect_ip']
    redirect_ip_vaildation = module.params['redirect_ip_vaildation']
    reflect_client = module.params['reflect_client']
    substitute_as_enable = module.params['substitute_as_enable']
    import_rt_policy_name = module.params['import_rt_policy_name']
    export_rt_policy_name = module.params['export_rt_policy_name']
    import_pref_filt_name = module.params['import_pref_filt_name']
    export_pref_filt_name = module.params['export_pref_filt_name']
    import_as_path_filter = module.params['import_as_path_filter']
    export_as_path_filter = module.params['export_as_path_filter']
    import_as_path_name_or_num = module.params['import_as_path_name_or_num']
    export_as_path_name_or_num = module.params['export_as_path_name_or_num']
    import_acl_name_or_num = module.params['import_acl_name_or_num']
    export_acl_name_or_num = module.params['export_acl_name_or_num']
    ipprefix_orf_enable = module.params['ipprefix_orf_enable']
    is_nonstd_ipprefix_mod = module.params['is_nonstd_ipprefix_mod']
    orftype = module.params['orftype']
    orf_mode = module.params['orf_mode']
    soostring = module.params['soostring']
    default_rt_adv_enable = module.params['default_rt_adv_enable']
    default_rt_adv_policy = module.params['default_rt_adv_policy']
    default_rt_match_mode = module.params['default_rt_match_mode']
    add_path_mode = module.params['add_path_mode']
    adv_add_path_num = module.params['adv_add_path_num']
    origin_as_valid = module.params['origin_as_valid']
    vpls_enable = module.params['vpls_enable']
    vpls_ad_disable = module.params['vpls_ad_disable']
    update_pkt_standard_compatible = module.params[
        'update_pkt_standard_compatible']

    ce_bgp_peer_af_obj = ce_bgp_neighbor_af(
        host=host, port=port, username=username, password=password)

    if not ce_bgp_peer_af_obj:
        module.fail_json(msg='init module failed.')

    bgp_peer_af_rst = ce_bgp_peer_af_obj.check_bgp_neighbor_af_args(
        module=module)
    bgp_peer_af_other_rst = ce_bgp_peer_af_obj.check_bgp_neighbor_af_other(
        module=module)

    args = dict(state=state,
                vrf_name=vrf_name,
                af_type=af_type,
                remote_address=remote_address,
                advertise_irb=advertise_irb,
                advertise_arp=advertise_arp,
                advertise_remote_nexthop=advertise_remote_nexthop,
                advertise_community=advertise_community,
                advertise_ext_community=advertise_ext_community,
                discard_ext_community=discard_ext_community,
                allow_as_loop_enable=allow_as_loop_enable,
                allow_as_loop_limit=allow_as_loop_limit,
                keep_all_routes=keep_all_routes,
                nexthop_configure=nexthop_configure,
                preferred_value=preferred_value,
                public_as_only=public_as_only,
                public_as_only_force=public_as_only_force,
                public_as_only_limited=public_as_only_limited,
                public_as_only_replace=public_as_only_replace,
                public_as_only_skip_peer_as=public_as_only_skip_peer_as,
                route_limit=route_limit,
                route_limit_percent=route_limit_percent,
                route_limit_type=route_limit_type,
                route_limit_idle_timeout=route_limit_idle_timeout,
                rt_updt_interval=rt_updt_interval,
                redirect_ip=redirect_ip,
                redirect_ip_vaildation=redirect_ip_vaildation,
                reflect_client=reflect_client,
                substitute_as_enable=substitute_as_enable,
                import_rt_policy_name=import_rt_policy_name,
                export_rt_policy_name=export_rt_policy_name,
                import_pref_filt_name=import_pref_filt_name,
                export_pref_filt_name=export_pref_filt_name,
                import_as_path_filter=import_as_path_filter,
                export_as_path_filter=export_as_path_filter,
                import_as_path_name_or_num=import_as_path_name_or_num,
                export_as_path_name_or_num=export_as_path_name_or_num,
                import_acl_name_or_num=import_acl_name_or_num,
                export_acl_name_or_num=export_acl_name_or_num,
                ipprefix_orf_enable=ipprefix_orf_enable,
                is_nonstd_ipprefix_mod=is_nonstd_ipprefix_mod,
                orftype=orftype,
                orf_mode=orf_mode,
                soostring=soostring,
                default_rt_adv_enable=default_rt_adv_enable,
                default_rt_adv_policy=default_rt_adv_policy,
                default_rt_match_mode=default_rt_match_mode,
                add_path_mode=add_path_mode,
                adv_add_path_num=adv_add_path_num,
                origin_as_valid=origin_as_valid,
                vpls_enable=vpls_enable,
                vpls_ad_disable=vpls_ad_disable,
                update_pkt_standard_compatible=update_pkt_standard_compatible)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = dict()
    end_state = dict()

    # state exist bgp peer address family config
    exist_tmp = dict(
        (k, v) for k, v in bgp_peer_af_rst.iteritems() if k is not "need_cfg")
    if exist_tmp:
        existing["bgp neighbor af"] = exist_tmp
    # state exist bgp peer address family other config
    exist_tmp = dict(
        (k, v) for k, v in bgp_peer_af_other_rst.iteritems() if k is not "need_cfg")
    if exist_tmp:
        existing["bgp neighbor af other"] = exist_tmp

    if state == "present":
        if bgp_peer_af_rst["need_cfg"]:
            if "remote_address" in bgp_peer_af_rst.keys():
                ce_bgp_peer_af_obj.merge_bgp_peer_af(module=module)
                changed = True
            else:
                ce_bgp_peer_af_obj.create_bgp_peer_af(module=module)
                changed = True

        if bgp_peer_af_other_rst["need_cfg"]:
            ce_bgp_peer_af_obj.merge_bgp_peer_af_other(module=module)
            changed = True

    else:
        if bgp_peer_af_rst["need_cfg"]:
            ce_bgp_peer_af_obj.delete_bgp_peer_af(module=module)
            changed = True

        if bgp_peer_af_other_rst["need_cfg"]:
            pass

    # state end bgp peer address family config
    bgp_peer_af_rst = ce_bgp_peer_af_obj.check_bgp_neighbor_af_args(
        module=module)
    end_tmp = dict(
        (k, v) for k, v in bgp_peer_af_rst.iteritems() if k is not "need_cfg")
    if end_tmp:
        end_state["bgp neighbor af"] = end_tmp
    # state end bgp peer address family other config
    bgp_peer_af_other_rst = ce_bgp_peer_af_obj.check_bgp_neighbor_af_other(
        module=module)
    end_tmp = dict(
        (k, v) for k, v in bgp_peer_af_other_rst.iteritems() if k is not "need_cfg")
    if end_tmp:
        end_state["bgp neighbor af other"] = end_tmp

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
