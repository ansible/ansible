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
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ce_bgp_neighbor_af
version_added: "2.4"
short_description: Manages BGP neighbor Address-family configuration on HUAWEI CloudEngine switches.
description:
    - Manages BGP neighbor Address-family configurations on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@CloudEngine-Ansible)
options:
    vrf_name:
        description:
            - Name of a BGP instance. The name is a case-sensitive string of characters.
              The BGP instance can be used only after the corresponding VPN instance is created.
        required: true
    af_type:
        description:
            - Address family type of a BGP instance.
        required: true
        choices: ['ipv4uni', 'ipv4multi', 'ipv4vpn', 'ipv6uni', 'ipv6vpn', 'evpn']
    remote_address:
        description:
            - IPv4 or IPv6 peer connection address.
        required: true
    advertise_irb:
        description:
            - If the value is true, advertised IRB routes are distinguished.
              If the value is false, advertised IRB routes are not distinguished.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    advertise_arp:
        description:
            - If the value is true, advertised ARP routes are distinguished.
              If the value is false, advertised ARP routes are not distinguished.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    advertise_remote_nexthop:
        description:
            - If the value is true, the remote next-hop attribute is advertised to peers.
              If the value is false, the remote next-hop attribute is not advertised to any peers.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    advertise_community:
        description:
            - If the value is true, the community attribute is advertised to peers.
              If the value is false, the community attribute is not advertised to peers.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    advertise_ext_community:
        description:
            - If the value is true, the extended community attribute is advertised to peers.
              If the value is false, the extended community attribute is not advertised to peers.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    discard_ext_community:
        description:
            - If the value is true, the extended community attribute in the peer route information is discarded.
              If the value is false, the extended community attribute in the peer route information is not discarded.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    allow_as_loop_enable:
        description:
            - If the value is true, repetitive local AS numbers are allowed.
              If the value is false, repetitive local AS numbers are not allowed.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    allow_as_loop_limit:
        description:
            - Set the maximum number of repetitive local AS number.
              The value is an integer ranging from 1 to 10.
        required: false
        default: null
    keep_all_routes:
        description:
            - If the value is true, the system stores all route update messages received from all peers (groups)
              after BGP connection setup.
              If the value is false, the system stores only BGP update messages that are received from peers
              and pass the configured import policy.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    nexthop_configure:
        description:
            - null, The next hop is not changed.
              local, The next hop is changed to the local IP address.
              invariable, Prevent the device from changing the next hop of each imported IGP route
              when advertising it to its BGP peers.
        required: false
        default: null
        choices: ['null', 'local', 'invariable']
    preferred_value:
        description:
            - Assign a preferred value for the routes learned from a specified peer.
              The value is an integer ranging from 0 to 65535.
        required: false
        default: null
    public_as_only:
        description:
            - If the value is true, sent BGP update messages carry only the public AS number but do not carry
              private AS numbers.
              If the value is false, sent BGP update messages can carry private AS numbers.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    public_as_only_force:
        description:
            - If the value is true, sent BGP update messages carry only the public AS number but do not carry
              private AS numbers.
              If the value is false, sent BGP update messages can carry private AS numbers.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    public_as_only_limited:
        description:
            - Limited use public as number.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    public_as_only_replace:
        description:
            - Private as replaced by public as number.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    public_as_only_skip_peer_as:
        description:
            - Public as only skip peer as.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    route_limit:
        description:
            - Configure the maximum number of routes that can be accepted from a peer.
              The value is an integer ranging from 1 to 4294967295.
        required: false
        default: null
    route_limit_percent:
        description:
            - Specify the percentage of routes when a router starts to generate an alarm.
              The value is an integer ranging from 1 to 100.
        required: false
        default: null
    route_limit_type:
        description:
            - Noparameter, After the number of received routes exceeds the threshold and the timeout
              timer expires,no action.
              AlertOnly, An alarm is generated and no additional routes will be accepted if the maximum
              number of routes allowed have been received.
              IdleForever, The connection that is interrupted is not automatically re-established if the
              maximum number of routes allowed have been received.
              IdleTimeout, After the number of received routes exceeds the threshold and the timeout timer
              expires, the connection that is interrupted is automatically re-established.
        required: false
        default: null
        choices: ['noparameter', 'alertOnly', 'idleForever', 'idleTimeout']
    route_limit_idle_timeout:
        description:
            - Specify the value of the idle-timeout timer to automatically reestablish the connections after
              they are cut off when the number of routes exceeds the set threshold.
              The value is an integer ranging from 1 to 1200.
        required: false
        default: null
    rt_updt_interval:
        description:
            - Specify the minimum interval at which Update packets are sent. The value is an integer, in seconds.
              The value is an integer ranging from 0 to 600.
        required: false
        default: null
    redirect_ip:
        description:
            - Redirect ip.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    redirect_ip_vaildation:
        description:
            - Redirect ip vaildation.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    reflect_client:
        description:
            - If the value is true, the local device functions as the route reflector and a peer functions
              as a client of the route reflector.
              If the value is false, the route reflector and client functions are not configured.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    substitute_as_enable:
        description:
            - If the value is true, the function to replace a specified peer's AS number in the AS-Path attribute with
              the local AS number is enabled.
              If the value is false, the function to replace a specified peer's AS number in the AS-Path attribute with
              the local AS number is disabled.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    import_rt_policy_name:
        description:
            - Specify the filtering policy applied to the routes learned from a peer.
              The value is a string of 1 to 40 characters.
        required: false
        default: null
    export_rt_policy_name:
        description:
            - Specify the filtering policy applied to the routes to be advertised to a peer.
              The value is a string of 1 to 40 characters.
        required: false
        default: null
    import_pref_filt_name:
        description:
            - Specify the IPv4 filtering policy applied to the routes received from a specified peer.
              The value is a string of 1 to 169 characters.
        required: false
        default: null
    export_pref_filt_name:
        description:
            - Specify the IPv4 filtering policy applied to the routes to be advertised to a specified peer.
              The value is a string of 1 to 169 characters.
        required: false
        default: null
    import_as_path_filter:
        description:
            - Apply an AS_Path-based filtering policy to the routes received from a specified peer.
              The value is an integer ranging from 1 to 256.
        required: false
        default: null
    export_as_path_filter:
        description:
            - Apply an AS_Path-based filtering policy to the routes to be advertised to a specified peer.
              The value is an integer ranging from 1 to 256.
        required: false
        default: null
    import_as_path_name_or_num:
        description:
            - A routing strategy based on the AS path list for routing received by a designated peer.
        required: false
        default: null
    export_as_path_name_or_num:
        description:
            - Application of a AS path list based filtering policy to the routing of a specified peer.
        required: false
        default: null
    import_acl_name_or_num:
        description:
            - Apply an IPv4 ACL-based filtering policy to the routes received from a specified peer.
              The value is a string of 1 to 32 characters.
        required: false
        default: null
    export_acl_name_or_num:
        description:
            - Apply an IPv4 ACL-based filtering policy to the routes to be advertised to a specified peer.
              The value is a string of 1 to 32 characters.
        required: false
        default: null
    ipprefix_orf_enable:
        description:
            - If the value is true, the address prefix-based Outbound Route Filter (ORF) capability is
              enabled for peers.
              If the value is false, the address prefix-based Outbound Route Filter (ORF) capability is
              disabled for peers.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    is_nonstd_ipprefix_mod:
        description:
            - If the value is true, Non-standard capability codes are used during capability negotiation.
              If the value is false, RFC-defined standard ORF capability codes are used during capability negotiation.
        required: false
        default: no_use
        choices: ['no_use','true','false']
    orftype:
        description:
            - ORF Type.
              The value is an integer ranging from 0 to 65535.
        required: false
        default: null
    orf_mode:
        description:
            - ORF mode.
              null, Default value.
              receive, ORF for incoming packets.
              send, ORF for outgoing packets.
              both, ORF for incoming and outgoing packets.
        required: false
        default: null
        choices: ['null', 'receive', 'send', 'both']
    soostring:
        description:
            - Configure the Site-of-Origin (SoO) extended community attribute.
              The value is a string of 3 to 21 characters.
        required: false
        default: null
    default_rt_adv_enable:
        description:
            - If the value is true, the function to advertise default routes to peers is enabled.
              If the value is false, the function to advertise default routes to peers is disabled.
        required: false
        default: no_use
        choices: ['no_use','true', 'false']
    default_rt_adv_policy:
        description:
            - Specify the name of a used policy. The value is a string.
              The value is a string of 1 to 40 characters.
        required: false
        default: null
    default_rt_match_mode:
        description:
            - null, Null.
              matchall, Advertise the default route if all matching conditions are met.
              matchany, Advertise the default route if any matching condition is met.
        required: false
        default: null
        choices: ['null', 'matchall', 'matchany']
    add_path_mode:
        description:
            - null, Null.
              receive, Support receiving Add-Path routes.
              send, Support sending Add-Path routes.
              both, Support receiving and sending Add-Path routes.
        required: false
        default: null
        choices: ['null', 'receive', 'send', 'both']
    adv_add_path_num:
        description:
            - The number of addPath advertise route.
              The value is an integer ranging from 2 to 64.
        required: false
        default: null
    origin_as_valid:
        description:
            - If the value is true, Application results of route announcement.
              If the value is false, Routing application results are not notified.
        required: false
        default: no_use
        choices: ['no_use','true', 'false']
    vpls_enable:
        description:
            - If the value is true, vpls enable.
              If the value is false, vpls disable.
        required: false
        default: no_use
        choices: ['no_use','true', 'false']
    vpls_ad_disable:
        description:
            - If the value is true, enable vpls-ad.
              If the value is false, disable vpls-ad.
        required: false
        default: no_use
        choices: ['no_use','true', 'false']
    update_pkt_standard_compatible:
        description:
            - If the value is true, When the vpnv4 multicast neighbor receives and updates the message,
              the message has no label.
              If the value is false, When the vpnv4 multicast neighbor receives and updates the message,
              the message has label.
        required: false
        default: no_use
        choices: ['no_use','true', 'false']
'''

EXAMPLES = '''

- name: CloudEngine BGP neighbor address family test
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

  - name: "Config BGP peer Address_Family"
    ce_bgp_neighbor_af:
      state: present
      vrf_name: js
      af_type: ipv4uni
      remote_address: 192.168.10.10
      nexthop_configure: local
      provider: "{{ cli }}"

  - name: "Undo BGP peer Address_Family"
    ce_bgp_neighbor_af:
      state: absent
      vrf_name: js
      af_type: ipv4uni
      remote_address: 192.168.10.10
      nexthop_configure: local
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
    sample: {"af_type": "ipv4uni", "nexthop_configure": "local",
             "remote_address": "192.168.10.10",
             "state": "present", "vrf_name": "js"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"bgp neighbor af": {"af_type": "ipv4uni", "remote_address": "192.168.10.10",
                                 "vrf_name": "js"},
             "bgp neighbor af other": {"af_type": "ipv4uni", "nexthop_configure": "null",
                                  "vrf_name": "js"}}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bgp neighbor af": {"af_type": "ipv4uni", "remote_address": "192.168.10.10",
                                 "vrf_name": "js"},
             "bgp neighbor af other": {"af_type": "ipv4uni", "nexthop_configure": "local",
                                  "vrf_name": "js"}}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["peer 192.168.10.10 next-hop-local"]
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ce import get_nc_config, set_nc_config, ce_argument_spec, check_ip_addr

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


class BgpNeighborAf(object):
    """ Manages BGP neighbor Address-family configuration """

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

    def check_bgp_neighbor_af_args(self, **kwargs):
        """ check_bgp_neighbor_af_args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='Error: The len of vrf_name %s is out of [1 - 31].' % vrf_name)

        state = module.params['state']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        if not check_ip_addr(ipaddr=remote_address):
            module.fail_json(
                msg='Error: The remote_address %s is invalid.' % remote_address)

        conf_str = CE_GET_BGP_PEER_AF_HEADER % (
            vrf_name, af_type) + CE_GET_BGP_PEER_AF_TAIL
        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if state == "present":
            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<remoteAddress>(.*)</remoteAddress>.*', recv_xml)

                if re_find:
                    result["remote_address"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != remote_address:
                        need_cfg = True
                else:
                    need_cfg = True
        else:
            if "<data/>" in recv_xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<remoteAddress>(.*)</remoteAddress>.*', recv_xml)

                if re_find:
                    result["remote_address"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] == remote_address:
                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_neighbor_af_other(self, **kwargs):
        """ check_bgp_neighbor_af_other """

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
        if advertise_irb != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseIrb></advertiseIrb>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseIrb>(.*)</advertiseIrb>.*', recv_xml)

                if re_find:
                    result["advertise_irb"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_irb:
                        need_cfg = True
                else:
                    need_cfg = True

        advertise_arp = module.params['advertise_arp']
        if advertise_arp != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseArp></advertiseArp>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseArp>(.*)</advertiseArp>.*', recv_xml)

                if re_find:
                    result["advertise_arp"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_arp:
                        need_cfg = True
                else:
                    need_cfg = True

        advertise_remote_nexthop = module.params['advertise_remote_nexthop']
        if advertise_remote_nexthop != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseRemoteNexthop></advertiseRemoteNexthop>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseRemoteNexthop>(.*)</advertiseRemoteNexthop>.*', recv_xml)

                if re_find:
                    result["advertise_remote_nexthop"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_remote_nexthop:
                        need_cfg = True
                else:
                    need_cfg = True

        advertise_community = module.params['advertise_community']
        if advertise_community != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseCommunity></advertiseCommunity>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseCommunity>(.*)</advertiseCommunity>.*', recv_xml)

                if re_find:
                    result["advertise_community"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_community:
                        need_cfg = True
                else:
                    need_cfg = True

        advertise_ext_community = module.params['advertise_ext_community']
        if advertise_ext_community != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advertiseExtCommunity></advertiseExtCommunity>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advertiseExtCommunity>(.*)</advertiseExtCommunity>.*', recv_xml)

                if re_find:
                    result["advertise_ext_community"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != advertise_ext_community:
                        need_cfg = True
                else:
                    need_cfg = True

        discard_ext_community = module.params['discard_ext_community']
        if discard_ext_community != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<discardExtCommunity></discardExtCommunity>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<discardExtCommunity>(.*)</discardExtCommunity>.*', recv_xml)

                if re_find:
                    result["discard_ext_community"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != discard_ext_community:
                        need_cfg = True
                else:
                    need_cfg = True

        allow_as_loop_enable = module.params['allow_as_loop_enable']
        if allow_as_loop_enable != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<allowAsLoopEnable></allowAsLoopEnable>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<allowAsLoopEnable>(.*)</allowAsLoopEnable>.*', recv_xml)

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
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<allowAsLoopLimit>(.*)</allowAsLoopLimit>.*', recv_xml)

                if re_find:
                    result["allow_as_loop_limit"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != allow_as_loop_limit:
                        need_cfg = True
                else:
                    need_cfg = True

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<keepAllRoutes></keepAllRoutes>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<keepAllRoutes>(.*)</keepAllRoutes>.*', recv_xml)

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
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<nextHopConfigure>(.*)</nextHopConfigure>.*', recv_xml)

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
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<preferredValue>(.*)</preferredValue>.*', recv_xml)

                if re_find:
                    result["preferred_value"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != preferred_value:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only = module.params['public_as_only']
        if public_as_only != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnly></publicAsOnly>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnly>(.*)</publicAsOnly>.*', recv_xml)

                if re_find:
                    result["public_as_only"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != public_as_only:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only_force = module.params['public_as_only_force']
        if public_as_only_force != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnlyForce></publicAsOnlyForce>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnlyForce>(.*)</publicAsOnlyForce>.*', recv_xml)

                if re_find:
                    result["public_as_only_force"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != public_as_only_force:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only_limited = module.params['public_as_only_limited']
        if public_as_only_limited != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnlyLimited></publicAsOnlyLimited>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnlyLimited>(.*)</publicAsOnlyLimited>.*', recv_xml)

                if re_find:
                    result["public_as_only_limited"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != public_as_only_limited:
                        need_cfg = True
                else:
                    need_cfg = True

        public_as_only_replace = module.params['public_as_only_replace']
        if public_as_only_replace != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnlyReplace></publicAsOnlyReplace>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnlyReplace>(.*)</publicAsOnlyReplace>.*', recv_xml)

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
        if public_as_only_skip_peer_as != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<publicAsOnlySkipPeerAs></publicAsOnlySkipPeerAs>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<publicAsOnlySkipPeerAs>(.*)</publicAsOnlySkipPeerAs>.*', recv_xml)

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
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeLimit>(.*)</routeLimit>.*', recv_xml)

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
                    msg='Error: The value of route_limit_percent %s is out of [1 - 100].' % route_limit_percent)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<routeLimitPercent></routeLimitPercent>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeLimitPercent>(.*)</routeLimitPercent>.*', recv_xml)

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
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeLimitType>(.*)</routeLimitType>.*', recv_xml)

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
                    msg='Error: The value of route_limit_idle_timeout %s is out of '
                        '[1 - 1200].' % route_limit_idle_timeout)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<routeLimitIdleTimeout></routeLimitPercent>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeLimitIdleTimeout>(.*)</routeLimitIdleTimeout>.*', recv_xml)

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
                    msg='Error: The value of rt_updt_interval %s is out of [0 - 600].' % rt_updt_interval)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<rtUpdtInterval></rtUpdtInterval>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<rtUpdtInterval>(.*)</rtUpdtInterval>.*', recv_xml)

                if re_find:
                    result["rt_updt_interval"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != rt_updt_interval:
                        need_cfg = True
                else:
                    need_cfg = True

        redirect_ip = module.params['redirect_ip']
        if redirect_ip != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<redirectIP></redirectIP>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<redirectIP>(.*)</redirectIP>.*', recv_xml)

                if re_find:
                    result["redirect_ip"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != redirect_ip:
                        need_cfg = True
                else:
                    need_cfg = True

        redirect_ip_vaildation = module.params['redirect_ip_vaildation']
        if redirect_ip_vaildation != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<redirectIPVaildation></redirectIPVaildation>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<redirectIPVaildation>(.*)</redirectIPVaildation>.*', recv_xml)

                if re_find:
                    result["redirect_ip_vaildation"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != redirect_ip_vaildation:
                        need_cfg = True
                else:
                    need_cfg = True

        reflect_client = module.params['reflect_client']
        if reflect_client != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<reflectClient></reflectClient>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectClient>(.*)</reflectClient>.*', recv_xml)

                if re_find:
                    result["reflect_client"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != reflect_client:
                        need_cfg = True
                else:
                    need_cfg = True

        substitute_as_enable = module.params['substitute_as_enable']
        if substitute_as_enable != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<substituteAsEnable></substituteAsEnable>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<substituteAsEnable>(.*)</substituteAsEnable>.*', recv_xml)

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
                    msg='Error: The len of import_rt_policy_name %s is out of [1 - 40].' % import_rt_policy_name)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importRtPolicyName></importRtPolicyName>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importRtPolicyName>(.*)</importRtPolicyName>.*', recv_xml)

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
                    msg='Error: The len of export_rt_policy_name %s is out of [1 - 40].' % export_rt_policy_name)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportRtPolicyName></exportRtPolicyName>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportRtPolicyName>(.*)</exportRtPolicyName>.*', recv_xml)

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
                    msg='Error: The len of import_pref_filt_name %s is out of [1 - 169].' % import_pref_filt_name)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importPrefFiltName></importPrefFiltName>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importPrefFiltName>(.*)</importPrefFiltName>.*', recv_xml)

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
                    msg='Error: The len of export_pref_filt_name %s is out of [1 - 169].' % export_pref_filt_name)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportPrefFiltName></exportPrefFiltName>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportPrefFiltName>(.*)</exportPrefFiltName>.*', recv_xml)

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
                    msg='Error: The value of import_as_path_filter %s is out of [1 - 256].' % import_as_path_filter)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importAsPathFilter></importAsPathFilter>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importAsPathFilter>(.*)</importAsPathFilter>.*', recv_xml)

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
                    msg='Error: The value of export_as_path_filter %s is out of [1 - 256].' % export_as_path_filter)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportAsPathFilter></exportAsPathFilter>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportAsPathFilter>(.*)</exportAsPathFilter>.*', recv_xml)

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
                    msg='Error: The len of import_as_path_name_or_num %s is out '
                        'of [1 - 51].' % import_as_path_name_or_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importAsPathNameOrNum></importAsPathNameOrNum>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importAsPathNameOrNum>(.*)</importAsPathNameOrNum>.*', recv_xml)

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
                    msg='Error: The len of export_as_path_name_or_num %s is out '
                        'of [1 - 51].' % export_as_path_name_or_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportAsPathNameOrNum></exportAsPathNameOrNum>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportAsPathNameOrNum>(.*)</exportAsPathNameOrNum>.*', recv_xml)

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
                    msg='Error: The len of import_acl_name_or_num %s is out of [1 - 32].' % import_acl_name_or_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<importAclNameOrNum></importAclNameOrNum>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<importAclNameOrNum>(.*)</importAclNameOrNum>.*', recv_xml)

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
                    msg='Error: The len of export_acl_name_or_num %s is out of [1 - 32].' % export_acl_name_or_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<exportAclNameOrNum></exportAclNameOrNum>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<exportAclNameOrNum>(.*)</exportAclNameOrNum>.*', recv_xml)

                if re_find:
                    result["export_acl_name_or_num"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != export_acl_name_or_num:
                        need_cfg = True
                else:
                    need_cfg = True

        ipprefix_orf_enable = module.params['ipprefix_orf_enable']
        if ipprefix_orf_enable != 'no_use':
            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<ipprefixOrfEnable></ipprefixOrfEnable>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ipprefixOrfEnable>(.*)</ipprefixOrfEnable>.*', recv_xml)

                if re_find:
                    result["ipprefix_orf_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != ipprefix_orf_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        is_nonstd_ipprefix_mod = module.params['is_nonstd_ipprefix_mod']
        if is_nonstd_ipprefix_mod != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<isNonstdIpprefixMod></isNonstdIpprefixMod>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isNonstdIpprefixMod>(.*)</isNonstdIpprefixMod>.*', recv_xml)

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
                    msg='Error: The value of orftype %s is out of [0 - 65535].' % orftype)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<orftype></orftype>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<orftype>(.*)</orftype>.*', recv_xml)

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
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<orfMode>(.*)</orfMode>.*', recv_xml)

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
                    msg='Error: The len of soostring %s is out of [3 - 21].' % soostring)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<soostring></soostring>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<soostring>(.*)</soostring>.*', recv_xml)

                if re_find:
                    result["soostring"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != soostring:
                        need_cfg = True
                else:
                    need_cfg = True

        default_rt_adv_enable = module.params['default_rt_adv_enable']
        if default_rt_adv_enable != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<defaultRtAdvEnable></defaultRtAdvEnable>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultRtAdvEnable>(.*)</defaultRtAdvEnable>.*', recv_xml)

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
                    msg='Error: The len of default_rt_adv_policy %s is out of [1 - 40].' % default_rt_adv_policy)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<defaultRtAdvPolicy></defaultRtAdvPolicy>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultRtAdvPolicy>(.*)</defaultRtAdvPolicy>.*', recv_xml)

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
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultRtMatchMode>(.*)</defaultRtMatchMode>.*', recv_xml)

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
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<addPathMode>(.*)</addPathMode>.*', recv_xml)

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
                    msg='Error: The value of adv_add_path_num %s is out of [2 - 64].' % adv_add_path_num)

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<advAddPathNum></advAddPathNum>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<advAddPathNum>(.*)</advAddPathNum>.*', recv_xml)

                if re_find:
                    result["adv_add_path_num"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != adv_add_path_num:
                        need_cfg = True
                else:
                    need_cfg = True

        origin_as_valid = module.params['origin_as_valid']
        if origin_as_valid != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<originAsValid></originAsValid>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<originAsValid>(.*)</originAsValid>.*', recv_xml)

                if re_find:
                    result["origin_as_valid"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != origin_as_valid:
                        need_cfg = True
                else:
                    need_cfg = True

        vpls_enable = module.params['vpls_enable']
        if vpls_enable != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<vplsEnable></vplsEnable>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<vplsEnable>(.*)</vplsEnable>.*', recv_xml)

                if re_find:
                    result["vpls_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    result["af_type"] = af_type
                    if re_find[0] != vpls_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        vpls_ad_disable = module.params['vpls_ad_disable']
        if vpls_ad_disable != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<vplsAdDisable></vplsAdDisable>" + CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<vplsAdDisable>(.*)</vplsAdDisable>.*', recv_xml)

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
        if update_pkt_standard_compatible != 'no_use':

            conf_str = CE_GET_BGP_PEER_AF_HEADER % (
                vrf_name, af_type) + "<updatePktStandardCompatible></updatePktStandardCompatible>" + \
                CE_GET_BGP_PEER_AF_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<updatePktStandardCompatible>(.*)</updatePktStandardCompatible>.*', recv_xml)

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
        """ merge_bgp_peer_af """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        conf_str = CE_MERGE_BGP_PEER_AF_HEADER % (
            vrf_name, af_type, remote_address) + CE_MERGE_BGP_PEER_AF_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp peer address family failed.')

        cmds = []
        if af_type == "ipv4uni":
            cmd = "ipv4-family unicast"
        elif af_type == "ipv4multi":
            cmd = "ipv4-family multicast"
        elif af_type == "ipv6uni":
            cmd = "ipv6-family unicast"
        cmds.append(cmd)
        cmd = "peer %s" % remote_address
        cmds.append(cmd)

        return cmds

    def create_bgp_peer_af(self, **kwargs):
        """ create_bgp_peer_af """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        conf_str = CE_CREATE_BGP_PEER_AF % (vrf_name, af_type, remote_address)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create bgp peer address family failed.')

        cmds = []
        if af_type == "ipv4uni":
            cmd = "ipv4-family unicast"
        elif af_type == "ipv4multi":
            cmd = "ipv4-family multicast"
        elif af_type == "ipv6uni":
            cmd = "ipv6-family unicast"
        cmds.append(cmd)
        cmd = "peer %s" % remote_address
        cmds.append(cmd)

        return cmds

    def delete_bgp_peer_af(self, **kwargs):
        """ delete_bgp_peer_af """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        conf_str = CE_DELETE_BGP_PEER_AF % (vrf_name, af_type, remote_address)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete bgp peer address family failed.')

        cmds = []
        if af_type == "ipv4uni":
            cmd = "ipv4-family unicast"
        elif af_type == "ipv4multi":
            cmd = "ipv4-family multicast"
        elif af_type == "ipv6uni":
            cmd = "ipv6-family unicast"
        cmds.append(cmd)
        cmd = "undo peer %s" % remote_address
        cmds.append(cmd)

        return cmds

    def merge_bgp_peer_af_other(self, **kwargs):
        """ merge_bgp_peer_af_other """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        remote_address = module.params['remote_address']

        conf_str = CE_MERGE_BGP_PEER_AF_HEADER % (
            vrf_name, af_type, remote_address)

        cmds = []

        advertise_irb = module.params['advertise_irb']
        if advertise_irb != 'no_use':
            conf_str += "<advertiseIrb>%s</advertiseIrb>" % advertise_irb

            if advertise_irb == "ture":
                cmd = "peer %s advertise irb" % remote_address
            else:
                cmd = "undo peer %s advertise irb" % remote_address
            cmds.append(cmd)

        advertise_arp = module.params['advertise_arp']
        if advertise_arp != 'no_use':
            conf_str += "<advertiseArp>%s</advertiseArp>" % advertise_arp

            if advertise_arp == "ture":
                cmd = "peer %s advertise arp" % remote_address
            else:
                cmd = "undo peer %s advertise arp" % remote_address
            cmds.append(cmd)

        advertise_remote_nexthop = module.params['advertise_remote_nexthop']
        if advertise_remote_nexthop != 'no_use':
            conf_str += "<advertiseRemoteNexthop>%s</advertiseRemoteNexthop>" % advertise_remote_nexthop

            if advertise_remote_nexthop == "true":
                cmd = "peer %s advertise remote-nexthop" % remote_address
            else:
                cmd = "undo peer %s advertise remote-nexthop" % remote_address
            cmds.append(cmd)

        advertise_community = module.params['advertise_community']
        if advertise_community != 'no_use':
            conf_str += "<advertiseCommunity>%s</advertiseCommunity>" % advertise_community

            if advertise_community == "true":
                cmd = "peer %s advertise-community" % remote_address
            else:
                cmd = "undo peer %s advertise-community" % remote_address
            cmds.append(cmd)

        advertise_ext_community = module.params['advertise_ext_community']
        if advertise_ext_community != 'no_use':
            conf_str += "<advertiseExtCommunity>%s</advertiseExtCommunity>" % advertise_ext_community

            if advertise_ext_community == "true":
                cmd = "peer %s advertise-ext-community" % remote_address
            else:
                cmd = "undo peer %s advertise-ext-community" % remote_address
            cmds.append(cmd)

        discard_ext_community = module.params['discard_ext_community']
        if discard_ext_community != 'no_use':
            conf_str += "<discardExtCommunity>%s</discardExtCommunity>" % discard_ext_community

            if discard_ext_community == "true":
                cmd = "peer %s discard-ext-community" % remote_address
            else:
                cmd = "undo peer %s discard-ext-community" % remote_address
            cmds.append(cmd)

        allow_as_loop_enable = module.params['allow_as_loop_enable']
        if allow_as_loop_enable != 'no_use':
            conf_str += "<allowAsLoopEnable>%s</allowAsLoopEnable>" % allow_as_loop_enable

            if allow_as_loop_enable == "true":
                cmd = "peer %s allow-as-loop" % remote_address
            else:
                cmd = "undo peer %s allow-as-loop" % remote_address
            cmds.append(cmd)

        allow_as_loop_limit = module.params['allow_as_loop_limit']
        if allow_as_loop_limit:
            conf_str += "<allowAsLoopLimit>%s</allowAsLoopLimit>" % allow_as_loop_limit

            if allow_as_loop_enable == "true":
                cmd = "peer %s allow-as-loop %s" % (remote_address, allow_as_loop_limit)
            else:
                cmd = "undo peer %s allow-as-loop" % remote_address
            cmds.append(cmd)

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes != 'no_use':
            conf_str += "<keepAllRoutes>%s</keepAllRoutes>" % keep_all_routes

            if keep_all_routes == "true":
                cmd = "peer %s keep-all-routes" % remote_address
            else:
                cmd = "undo peer %s keep-all-routes" % remote_address
            cmds.append(cmd)

        nexthop_configure = module.params['nexthop_configure']
        if nexthop_configure:
            conf_str += "<nextHopConfigure>%s</nextHopConfigure>" % nexthop_configure

            if nexthop_configure == "local":
                cmd = "peer %s next-hop-local" % remote_address
                cmds.append(cmd)
            elif nexthop_configure == "invariable":
                cmd = "peer %s next-hop-invariable" % remote_address
                cmds.append(cmd)

        preferred_value = module.params['preferred_value']
        if preferred_value:
            conf_str += "<preferredValue>%s</preferredValue>" % preferred_value

            cmd = "peer %s preferred-value %s" % (remote_address, preferred_value)
            cmds.append(cmd)

        public_as_only = module.params['public_as_only']
        if public_as_only != 'no_use':
            conf_str += "<publicAsOnly>%s</publicAsOnly>" % public_as_only

            if public_as_only == "true":
                cmd = "peer %s public-as-only" % remote_address
            else:
                cmd = "undo peer %s public-as-only" % remote_address
            cmds.append(cmd)

        public_as_only_force = module.params['public_as_only_force']
        if public_as_only_force != 'no_use':
            conf_str += "<publicAsOnlyForce>%s</publicAsOnlyForce>" % public_as_only_force

            if public_as_only_force == "true":
                cmd = "peer %s public-as-only force" % remote_address
            else:
                cmd = "undo peer %s public-as-only force" % remote_address
            cmds.append(cmd)

        public_as_only_limited = module.params['public_as_only_limited']
        if public_as_only_limited != 'no_use':
            conf_str += "<publicAsOnlyLimited>%s</publicAsOnlyLimited>" % public_as_only_limited

            if public_as_only_limited == "true":
                cmd = "peer %s public-as-only limited" % remote_address
            else:
                cmd = "undo peer %s public-as-only limited" % remote_address
            cmds.append(cmd)

        public_as_only_replace = module.params['public_as_only_replace']
        if public_as_only_replace != 'no_use':
            conf_str += "<publicAsOnlyReplace>%s</publicAsOnlyReplace>" % public_as_only_replace

            if public_as_only_replace == "true":
                cmd = "peer %s public-as-only force replace" % remote_address
            else:
                cmd = "undo peer %s public-as-only force replace" % remote_address
            cmds.append(cmd)

        public_as_only_skip_peer_as = module.params[
            'public_as_only_skip_peer_as']
        if public_as_only_skip_peer_as != 'no_use':
            conf_str += "<publicAsOnlySkipPeerAs>%s</publicAsOnlySkipPeerAs>" % public_as_only_skip_peer_as

            if public_as_only_skip_peer_as == "true":
                cmd = "peer %s public-as-only force include-peer-as" % remote_address
            else:
                cmd = "undo peer %s public-as-only force include-peer-as" % remote_address
            cmds.append(cmd)

        route_limit = module.params['route_limit']
        if route_limit:
            conf_str += "<routeLimit>%s</routeLimit>" % route_limit

            cmd = "peer %s route-limit %s" % (remote_address, route_limit)
            cmds.append(cmd)

        route_limit_percent = module.params['route_limit_percent']
        if route_limit_percent:
            conf_str += "<routeLimitPercent>%s</routeLimitPercent>" % route_limit_percent

            cmd = "peer %s route-limit %s %s" % (remote_address, route_limit, route_limit_percent)
            cmds.append(cmd)

        route_limit_type = module.params['route_limit_type']
        if route_limit_type:
            conf_str += "<routeLimitType>%s</routeLimitType>" % route_limit_type

            if route_limit_type == "alertOnly":
                cmd = "peer %s route-limit %s %s alert-only" % (remote_address, route_limit, route_limit_percent)
                cmds.append(cmd)
            elif route_limit_type == "idleForever":
                cmd = "peer %s route-limit %s %s idle-forever" % (remote_address, route_limit, route_limit_percent)
                cmds.append(cmd)
            elif route_limit_type == "idleTimeout":
                cmd = "peer %s route-limit %s %s idle-timeout" % (remote_address, route_limit, route_limit_percent)
                cmds.append(cmd)

        route_limit_idle_timeout = module.params['route_limit_idle_timeout']
        if route_limit_idle_timeout:
            conf_str += "<routeLimitIdleTimeout>%s</routeLimitIdleTimeout>" % route_limit_idle_timeout

            cmd = "peer %s route-limit %s %s idle-timeout %s" % (remote_address, route_limit,
                                                                 route_limit_percent, route_limit_idle_timeout)
            cmds.append(cmd)

        rt_updt_interval = module.params['rt_updt_interval']
        if rt_updt_interval:
            conf_str += "<rtUpdtInterval>%s</rtUpdtInterval>" % rt_updt_interval

            cmd = "peer %s route-update-interval %s" % (remote_address, rt_updt_interval)
            cmds.append(cmd)

        redirect_ip = module.params['redirect_ip']
        if redirect_ip != 'no_use':
            conf_str += "<redirectIP>%s</redirectIP>" % redirect_ip

        redirect_ip_vaildation = module.params['redirect_ip_vaildation']
        if redirect_ip_vaildation != 'no_use':
            conf_str += "<redirectIPVaildation>%s</redirectIPVaildation>" % redirect_ip_vaildation

        reflect_client = module.params['reflect_client']
        if reflect_client != 'no_use':
            conf_str += "<reflectClient>%s</reflectClient>" % reflect_client

            if reflect_client == "true":
                cmd = "peer %s reflect-client" % remote_address
            else:
                cmd = "undo peer %s reflect-client" % remote_address
            cmds.append(cmd)

        substitute_as_enable = module.params['substitute_as_enable']
        if substitute_as_enable != 'no_use':
            conf_str += "<substituteAsEnable>%s</substituteAsEnable>" % substitute_as_enable

        import_rt_policy_name = module.params['import_rt_policy_name']
        if import_rt_policy_name:
            conf_str += "<importRtPolicyName>%s</importRtPolicyName>" % import_rt_policy_name

            cmd = "peer %s route-policy %s import" % (remote_address, import_rt_policy_name)
            cmds.append(cmd)

        export_rt_policy_name = module.params['export_rt_policy_name']
        if export_rt_policy_name:
            conf_str += "<exportRtPolicyName>%s</exportRtPolicyName>" % export_rt_policy_name

            cmd = "peer %s route-policy %s export" % (remote_address, export_rt_policy_name)
            cmds.append(cmd)

        import_pref_filt_name = module.params['import_pref_filt_name']
        if import_pref_filt_name:
            conf_str += "<importPrefFiltName>%s</importPrefFiltName>" % import_pref_filt_name

            cmd = "peer %s filter-policy %s import" % (remote_address, import_pref_filt_name)
            cmds.append(cmd)

        export_pref_filt_name = module.params['export_pref_filt_name']
        if export_pref_filt_name:
            conf_str += "<exportPrefFiltName>%s</exportPrefFiltName>" % export_pref_filt_name

            cmd = "peer %s filter-policy %s export" % (remote_address, export_pref_filt_name)
            cmds.append(cmd)

        import_as_path_filter = module.params['import_as_path_filter']
        if import_as_path_filter:
            conf_str += "<importAsPathFilter>%s</importAsPathFilter>" % import_as_path_filter

            cmd = "peer %s as-path-filter %s import" % (remote_address, import_as_path_filter)
            cmds.append(cmd)

        export_as_path_filter = module.params['export_as_path_filter']
        if export_as_path_filter:
            conf_str += "<exportAsPathFilter>%s</exportAsPathFilter>" % export_as_path_filter

            cmd = "peer %s as-path-filter %s export" % (remote_address, export_as_path_filter)
            cmds.append(cmd)

        import_as_path_name_or_num = module.params[
            'import_as_path_name_or_num']
        if import_as_path_name_or_num:
            conf_str += "<importAsPathNameOrNum>%s</importAsPathNameOrNum>" % import_as_path_name_or_num

            cmd = "peer %s as-path-filter %s import" % (remote_address, import_as_path_name_or_num)
            cmds.append(cmd)

        export_as_path_name_or_num = module.params[
            'export_as_path_name_or_num']
        if export_as_path_name_or_num:
            conf_str += "<exportAsPathNameOrNum>%s</exportAsPathNameOrNum>" % export_as_path_name_or_num

            cmd = "peer %s as-path-filter %s export" % (remote_address, export_as_path_name_or_num)
            cmds.append(cmd)

        import_acl_name_or_num = module.params['import_acl_name_or_num']
        if import_acl_name_or_num:
            conf_str += "<importAclNameOrNum>%s</importAclNameOrNum>" % import_acl_name_or_num

            cmd = "peer %s filter-policy %s import" % (remote_address, import_acl_name_or_num)
            cmds.append(cmd)

        export_acl_name_or_num = module.params['export_acl_name_or_num']
        if export_acl_name_or_num:
            conf_str += "<exportAclNameOrNum>%s</exportAclNameOrNum>" % export_acl_name_or_num

            cmd = "peer %s filter-policy %s export" % (remote_address, export_acl_name_or_num)
            cmds.append(cmd)

        ipprefix_orf_enable = module.params['ipprefix_orf_enable']
        if ipprefix_orf_enable != 'no_use':
            conf_str += "<ipprefixOrfEnable>%s</ipprefixOrfEnable>" % ipprefix_orf_enable

            if ipprefix_orf_enable == "true":
                cmd = "peer %s capability-advertise orf ip-prefix" % remote_address
            else:
                cmd = "undo peer %s capability-advertise orf ip-prefix" % remote_address
            cmds.append(cmd)

        is_nonstd_ipprefix_mod = module.params['is_nonstd_ipprefix_mod']
        if is_nonstd_ipprefix_mod != 'no_use':
            conf_str += "<isNonstdIpprefixMod>%s</isNonstdIpprefixMod>" % is_nonstd_ipprefix_mod

            if is_nonstd_ipprefix_mod == "true":
                if ipprefix_orf_enable == "true":
                    cmd = "peer %s capability-advertise orf non-standard-compatible" % remote_address
                else:
                    cmd = "undo peer %s capability-advertise orf non-standard-compatible" % remote_address
                cmds.append(cmd)
            else:
                if ipprefix_orf_enable == "true":
                    cmd = "peer %s capability-advertise orf" % remote_address
                else:
                    cmd = "undo peer %s capability-advertise orf" % remote_address
                cmds.append(cmd)

        orftype = module.params['orftype']
        if orftype:
            conf_str += "<orftype>%s</orftype>" % orftype

        orf_mode = module.params['orf_mode']
        if orf_mode:
            conf_str += "<orfMode>%s</orfMode>" % orf_mode

            if ipprefix_orf_enable == "true":
                cmd = "peer %s capability-advertise orf ip-prefix %s" % (remote_address, orf_mode)
            else:
                cmd = "undo peer %s capability-advertise orf ip-prefix %s" % (remote_address, orf_mode)
            cmds.append(cmd)

        soostring = module.params['soostring']
        if soostring:
            conf_str += "<soostring>%s</soostring>" % soostring

            cmd = "peer %s soo %s" % (remote_address, soostring)
            cmds.append(cmd)

        cmd = ""
        default_rt_adv_enable = module.params['default_rt_adv_enable']
        if default_rt_adv_enable != 'no_use':
            conf_str += "<defaultRtAdvEnable>%s</defaultRtAdvEnable>" % default_rt_adv_enable

            if default_rt_adv_enable == "true":
                cmd += "peer %s default-route-advertise" % remote_address
            else:
                cmd += "undo peer %s default-route-advertise" % remote_address

        default_rt_adv_policy = module.params['default_rt_adv_policy']
        if default_rt_adv_policy:
            conf_str += "<defaultRtAdvPolicy>%s</defaultRtAdvPolicy>" % default_rt_adv_policy

            cmd += " route-policy %s" % default_rt_adv_policy

        default_rt_match_mode = module.params['default_rt_match_mode']
        if default_rt_match_mode:
            conf_str += "<defaultRtMatchMode>%s</defaultRtMatchMode>" % default_rt_match_mode

            if default_rt_match_mode == "matchall":
                cmd += " conditional-route-match-all"
            elif default_rt_match_mode == "matchany":
                cmd += " conditional-route-match-any"

        if cmd:
            cmds.append(cmd)

        add_path_mode = module.params['add_path_mode']
        if add_path_mode:
            conf_str += "<addPathMode>%s</addPathMode>" % add_path_mode

        adv_add_path_num = module.params['adv_add_path_num']
        if adv_add_path_num:
            conf_str += "<advAddPathNum>%s</advAddPathNum>" % adv_add_path_num

        origin_as_valid = module.params['origin_as_valid']
        if origin_as_valid != 'no_use':
            conf_str += "<originAsValid>%s</originAsValid>" % origin_as_valid

        vpls_enable = module.params['vpls_enable']
        if vpls_enable != 'no_use':
            conf_str += "<vplsEnable>%s</vplsEnable>" % vpls_enable

        vpls_ad_disable = module.params['vpls_ad_disable']
        if vpls_ad_disable != 'no_use':
            conf_str += "<vplsAdDisable>%s</vplsAdDisable>" % vpls_ad_disable

        update_pkt_standard_compatible = module.params[
            'update_pkt_standard_compatible']
        if update_pkt_standard_compatible != 'no_use':
            conf_str += "<updatePktStandardCompatible>%s</updatePktStandardCompatible>" % update_pkt_standard_compatible

        conf_str += CE_MERGE_BGP_PEER_AF_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp peer address family other failed.')

        return cmds


def main():
    """ main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        vrf_name=dict(type='str', required=True),
        af_type=dict(choices=['ipv4uni', 'ipv4multi', 'ipv4vpn',
                              'ipv6uni', 'ipv6vpn', 'evpn'], required=True),
        remote_address=dict(type='str', required=True),
        advertise_irb=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        advertise_arp=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        advertise_remote_nexthop=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        advertise_community=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        advertise_ext_community=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        discard_ext_community=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        allow_as_loop_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        allow_as_loop_limit=dict(type='str'),
        keep_all_routes=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        nexthop_configure=dict(choices=['null', 'local', 'invariable']),
        preferred_value=dict(type='str'),
        public_as_only=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        public_as_only_force=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        public_as_only_limited=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        public_as_only_replace=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        public_as_only_skip_peer_as=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        route_limit=dict(type='str'),
        route_limit_percent=dict(type='str'),
        route_limit_type=dict(
            choices=['noparameter', 'alertOnly', 'idleForever', 'idleTimeout']),
        route_limit_idle_timeout=dict(type='str'),
        rt_updt_interval=dict(type='str'),
        redirect_ip=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        redirect_ip_vaildation=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        reflect_client=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        substitute_as_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
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
        ipprefix_orf_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        is_nonstd_ipprefix_mod=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        orftype=dict(type='str'),
        orf_mode=dict(choices=['null', 'receive', 'send', 'both']),
        soostring=dict(type='str'),
        default_rt_adv_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        default_rt_adv_policy=dict(type='str'),
        default_rt_match_mode=dict(choices=['null', 'matchall', 'matchany']),
        add_path_mode=dict(choices=['null', 'receive', 'send', 'both']),
        adv_add_path_num=dict(type='str'),
        origin_as_valid=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        vpls_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        vpls_ad_disable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        update_pkt_standard_compatible=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']))

    argument_spec.update(ce_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    changed = False
    proposed = dict()
    existing = dict()
    end_state = dict()
    updates = []

    state = module.params['state']
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

    ce_bgp_peer_af_obj = BgpNeighborAf()

    # get proposed
    proposed["state"] = state
    if vrf_name:
        proposed["vrf_name"] = vrf_name
    if af_type:
        proposed["af_type"] = af_type
    if remote_address:
        proposed["remote_address"] = remote_address
    if advertise_irb != 'no_use':
        proposed["advertise_irb"] = advertise_irb
    if advertise_arp != 'no_use':
        proposed["advertise_arp"] = advertise_arp
    if advertise_remote_nexthop != 'no_use':
        proposed["advertise_remote_nexthop"] = advertise_remote_nexthop
    if advertise_community != 'no_use':
        proposed["advertise_community"] = advertise_community
    if advertise_ext_community != 'no_use':
        proposed["advertise_ext_community"] = advertise_ext_community
    if discard_ext_community != 'no_use':
        proposed["discard_ext_community"] = discard_ext_community
    if allow_as_loop_enable != 'no_use':
        proposed["allow_as_loop_enable"] = allow_as_loop_enable
    if allow_as_loop_limit:
        proposed["allow_as_loop_limit"] = allow_as_loop_limit
    if keep_all_routes != 'no_use':
        proposed["keep_all_routes"] = keep_all_routes
    if nexthop_configure:
        proposed["nexthop_configure"] = nexthop_configure
    if preferred_value:
        proposed["preferred_value"] = preferred_value
    if public_as_only != 'no_use':
        proposed["public_as_only"] = public_as_only
    if public_as_only_force != 'no_use':
        proposed["public_as_only_force"] = public_as_only_force
    if public_as_only_limited != 'no_use':
        proposed["public_as_only_limited"] = public_as_only_limited
    if public_as_only_replace != 'no_use':
        proposed["public_as_only_replace"] = public_as_only_replace
    if public_as_only_skip_peer_as != 'no_use':
        proposed["public_as_only_skip_peer_as"] = public_as_only_skip_peer_as
    if route_limit:
        proposed["route_limit"] = route_limit
    if route_limit_percent:
        proposed["route_limit_percent"] = route_limit_percent
    if route_limit_type:
        proposed["route_limit_type"] = route_limit_type
    if route_limit_idle_timeout:
        proposed["route_limit_idle_timeout"] = route_limit_idle_timeout
    if rt_updt_interval:
        proposed["rt_updt_interval"] = rt_updt_interval
    if redirect_ip != 'no_use':
        proposed["redirect_ip"] = redirect_ip
    if redirect_ip_vaildation != 'no_use':
        proposed["redirect_ip_vaildation"] = redirect_ip_vaildation
    if reflect_client != 'no_use':
        proposed["reflect_client"] = reflect_client
    if substitute_as_enable != 'no_use':
        proposed["substitute_as_enable"] = substitute_as_enable
    if import_rt_policy_name:
        proposed["import_rt_policy_name"] = import_rt_policy_name
    if export_rt_policy_name:
        proposed["export_rt_policy_name"] = export_rt_policy_name
    if import_pref_filt_name:
        proposed["import_pref_filt_name"] = import_pref_filt_name
    if export_pref_filt_name:
        proposed["export_pref_filt_name"] = export_pref_filt_name
    if import_as_path_filter:
        proposed["import_as_path_filter"] = import_as_path_filter
    if export_as_path_filter:
        proposed["export_as_path_filter"] = export_as_path_filter
    if import_as_path_name_or_num:
        proposed["import_as_path_name_or_num"] = import_as_path_name_or_num
    if export_as_path_name_or_num:
        proposed["export_as_path_name_or_num"] = export_as_path_name_or_num
    if import_acl_name_or_num:
        proposed["import_acl_name_or_num"] = import_acl_name_or_num
    if export_acl_name_or_num:
        proposed["export_acl_name_or_num"] = export_acl_name_or_num
    if ipprefix_orf_enable != 'no_use':
        proposed["ipprefix_orf_enable"] = ipprefix_orf_enable
    if is_nonstd_ipprefix_mod != 'no_use':
        proposed["is_nonstd_ipprefix_mod"] = is_nonstd_ipprefix_mod
    if orftype:
        proposed["orftype"] = orftype
    if orf_mode:
        proposed["orf_mode"] = orf_mode
    if soostring:
        proposed["soostring"] = soostring
    if default_rt_adv_enable != 'no_use':
        proposed["default_rt_adv_enable"] = default_rt_adv_enable
    if default_rt_adv_policy:
        proposed["default_rt_adv_policy"] = default_rt_adv_policy
    if default_rt_match_mode:
        proposed["default_rt_match_mode"] = default_rt_match_mode
    if add_path_mode:
        proposed["add_path_mode"] = add_path_mode
    if adv_add_path_num:
        proposed["adv_add_path_num"] = adv_add_path_num
    if origin_as_valid != 'no_use':
        proposed["origin_as_valid"] = origin_as_valid
    if vpls_enable != 'no_use':
        proposed["vpls_enable"] = vpls_enable
    if vpls_ad_disable != 'no_use':
        proposed["vpls_ad_disable"] = vpls_ad_disable
    if update_pkt_standard_compatible != 'no_use':
        proposed["update_pkt_standard_compatible"] = update_pkt_standard_compatible

    if not ce_bgp_peer_af_obj:
        module.fail_json(msg='Error: Init module failed.')

    bgp_peer_af_rst = ce_bgp_peer_af_obj.check_bgp_neighbor_af_args(
        module=module)
    bgp_peer_af_other_rst = ce_bgp_peer_af_obj.check_bgp_neighbor_af_other(
        module=module)

    # state exist bgp peer address family config
    exist_tmp = dict()
    for item in bgp_peer_af_rst:
        if item != "need_cfg":
            exist_tmp[item] = bgp_peer_af_rst[item]
    if exist_tmp:
        existing["bgp neighbor af"] = exist_tmp
    # state exist bgp peer address family other config
    exist_tmp = dict()
    for item in bgp_peer_af_other_rst:
        if item != "need_cfg":
            exist_tmp[item] = bgp_peer_af_other_rst[item]
    if exist_tmp:
        existing["bgp neighbor af other"] = exist_tmp

    if state == "present":
        if bgp_peer_af_rst["need_cfg"]:
            if "remote_address" in bgp_peer_af_rst.keys():
                cmd = ce_bgp_peer_af_obj.merge_bgp_peer_af(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)
            else:
                cmd = ce_bgp_peer_af_obj.create_bgp_peer_af(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

        if bgp_peer_af_other_rst["need_cfg"]:
            cmd = ce_bgp_peer_af_obj.merge_bgp_peer_af_other(module=module)
            changed = True
            for item in cmd:
                updates.append(item)

    else:
        if bgp_peer_af_rst["need_cfg"]:
            cmd = ce_bgp_peer_af_obj.delete_bgp_peer_af(module=module)
            changed = True
            for item in cmd:
                updates.append(item)

        if bgp_peer_af_other_rst["need_cfg"]:
            pass

    # state end bgp peer address family config
    bgp_peer_af_rst = ce_bgp_peer_af_obj.check_bgp_neighbor_af_args(
        module=module)
    end_tmp = dict()
    for item in bgp_peer_af_rst:
        if item != "need_cfg":
            end_tmp[item] = bgp_peer_af_rst[item]
    if end_tmp:
        end_state["bgp neighbor af"] = end_tmp
    # state end bgp peer address family other config
    bgp_peer_af_other_rst = ce_bgp_peer_af_obj.check_bgp_neighbor_af_other(
        module=module)
    end_tmp = dict()
    for item in bgp_peer_af_other_rst:
        if item != "need_cfg":
            end_tmp[item] = bgp_peer_af_other_rst[item]
    if end_tmp:
        end_state["bgp neighbor af other"] = end_tmp

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state
    results['updates'] = updates

    module.exit_json(**results)


if __name__ == '__main__':
    main()
