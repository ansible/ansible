# Copyright 2018 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <https://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
import pytest

try:
    from ansible.modules.network.fortimanager import fmgr_fwpol_ipv4
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


def load_fixtures():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures') + "/{filename}.json".format(
        filename=os.path.splitext(os.path.basename(__file__))[0])
    try:
        with open(fixture_path, "r") as fixture_file:
            fixture_data = json.load(fixture_file)
    except IOError:
        return []
    return [fixture_data]


@pytest.fixture(autouse=True)
def module_mock(mocker):
    connection_class_mock = mocker.patch('ansible.module_utils.basic.AnsibleModule')
    return connection_class_mock


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortimanager.fmgr_fwpol_ipv4.Connection')
    return connection_class_mock


@pytest.fixture(scope="function", params=load_fixtures())
def fixture_data(request):
    func_name = request.function.__name__.replace("test_", "")
    return request.param.get(func_name, None)


fmg_instance = FortiManagerHandler(connection_mock, module_mock)


def test_fmgr_firewall_policy_modify(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # wanopt-passive-opt: None
    # package_name: default
    # wanopt-detection: None
    # scan-botnet-connections: None
    # profile-group: None
    # wanopt-peer: None
    # dscp-match: None
    # replacemsg-override-group: None
    # internet-service-negate: None
    # np-acceleration: None
    # learning-mode: None
    # session-ttl: None
    # ntlm-guest: None
    # ips-sensor: None
    # diffservcode-rev: None
    # match-vip: None
    # natip: None
    # dlp-sensor: None
    # traffic-shaper: None
    # groups: None
    # schedule-timeout: None
    # name: Basic_IPv4_Policy
    # tcp-session-without-syn: None
    # ntlm: None
    # permit-stun-host: None
    # diffservcode-forward: None
    # internet-service-src-custom: None
    # mode: set
    # disclaimer: None
    # rtp-nat: None
    # auth-cert: None
    # timeout-send-rst: None
    # auth-redirect-addr: None
    # ssl-mirror-intf: None
    # identity-based-route: None
    # natoutbound: None
    # wanopt-profile: None
    # per-ip-shaper: None
    # profile-protocol-options: None
    # diffserv-forward: None
    # poolname: None
    # comments: Created by Ansible
    # label: None
    # global-label: None
    # firewall-session-dirty: None
    # wanopt: None
    # schedule: always
    # internet-service-id: None
    # auth-path: None
    # vlan-cos-fwd: None
    # custom-log-fields: None
    # dstintf: any
    # srcintf: any
    # block-notification: None
    # internet-service-src-id: None
    # redirect-url: None
    # waf-profile: None
    # ntlm-enabled-browsers: None
    # dscp-negate: None
    # action: accept
    # fsso-agent-for-ntlm: None
    # logtraffic: utm
    # vlan-filter: None
    # policyid: None
    # logtraffic-start: None
    # webcache-https: None
    # webfilter-profile: None
    # internet-service-src: None
    # webcache: None
    # utm-status: None
    # vpn_src_node: {'subnet': None, 'host': None, 'seq': None}
    # ippool: None
    # service: ALL
    # wccp: None
    # auto-asic-offload: None
    # dscp-value: None
    # url-category: None
    # capture-packet: None
    # adom: ansible
    # inbound: None
    # internet-service: None
    # profile-type: None
    # ssl-mirror: None
    # srcaddr-negate: None
    # gtp-profile: None
    # mms-profile: None
    # send-deny-packet: None
    # devices: None
    # permit-any-host: None
    # av-profile: None
    # internet-service-src-negate: None
    # service-negate: None
    # rsso: None
    # app-group: None
    # tcp-mss-sender: None
    # natinbound: None
    # fixedport: None
    # ssl-ssh-profile: None
    # outbound: None
    # spamfilter-profile: None
    # application-list: None
    # application: None
    # dnsfilter-profile: None
    # nat: None
    # fsso: None
    # vlan-cos-rev: None
    # status: None
    # dsri: None
    # users: None
    # voip-profile: None
    # dstaddr-negate: None
    # traffic-shaper-reverse: None
    # internet-service-custom: None
    # diffserv-reverse: None
    # srcaddr: all
    # ssh-filter-profile: None
    # delay-tcp-npu-session: None
    # icap-profile: None
    # captive-portal-exempt: None
    # vpn_dst_node: {'subnet': None, 'host': None, 'seq': None}
    # app-category: None
    # rtp-addr: None
    # wsso: None
    # tcp-mss-receiver: None
    # dstaddr: all
    # radius-mac-auth-bypass: None
    # vpntunnel: None
    ##################################################
    ##################################################
    # package_name: default
    # wanopt-detection: None
    # scan-botnet-connections: None
    # profile-group: None
    # dlp-sensor: None
    # dscp-match: None
    # replacemsg-override-group: None
    # internet-service-negate: None
    # np-acceleration: None
    # learning-mode: None
    # session-ttl: None
    # ntlm-guest: None
    # ips-sensor: None
    # diffservcode-rev: None
    # match-vip: None
    # natip: None
    # wanopt-peer: None
    # traffic-shaper: None
    # groups: None
    # schedule-timeout: None
    # name: Basic_IPv4_Policy_2
    # tcp-session-without-syn: None
    # rtp-nat: None
    # permit-stun-host: None
    # natoutbound: None
    # internet-service-src-custom: None
    # mode: set
    # logtraffic: utm
    # ntlm: None
    # auth-cert: None
    # timeout-send-rst: None
    # auth-redirect-addr: None
    # ssl-mirror-intf: None
    # identity-based-route: None
    # diffservcode-forward: None
    # wanopt-profile: None
    # per-ip-shaper: None
    # users: None
    # diffserv-forward: None
    # poolname: None
    # comments: Created by Ansible
    # label: None
    # global-label: None
    # firewall-session-dirty: None
    # wanopt: None
    # schedule: always
    # internet-service-id: None
    # auth-path: None
    # vlan-cos-fwd: None
    # custom-log-fields: None
    # dstintf: any
    # srcintf: any
    # block-notification: None
    # internet-service-src-id: None
    # redirect-url: None
    # waf-profile: None
    # ntlm-enabled-browsers: None
    # dscp-negate: None
    # action: accept
    # fsso-agent-for-ntlm: None
    # disclaimer: None
    # vlan-filter: None
    # dstaddr-negate: None
    # logtraffic-start: None
    # webcache-https: None
    # webfilter-profile: None
    # internet-service-src: None
    # webcache: None
    # utm-status: None
    # vpn_src_node: {'subnet': None, 'host': None, 'seq': None}
    # ippool: None
    # service: HTTP, HTTPS
    # wccp: None
    # auto-asic-offload: None
    # dscp-value: None
    # url-category: None
    # capture-packet: None
    # adom: ansible
    # inbound: None
    # internet-service: None
    # profile-type: None
    # ssl-mirror: None
    # srcaddr-negate: None
    # gtp-profile: None
    # mms-profile: None
    # send-deny-packet: None
    # devices: None
    # permit-any-host: None
    # av-profile: None
    # internet-service-src-negate: None
    # service-negate: None
    # rsso: None
    # application-list: None
    # app-group: None
    # tcp-mss-sender: None
    # natinbound: None
    # fixedport: None
    # ssl-ssh-profile: None
    # outbound: None
    # spamfilter-profile: None
    # wanopt-passive-opt: None
    # application: None
    # dnsfilter-profile: None
    # nat: enable
    # fsso: None
    # vlan-cos-rev: None
    # status: None
    # dsri: None
    # profile-protocol-options: None
    # voip-profile: None
    # policyid: None
    # traffic-shaper-reverse: None
    # internet-service-custom: None
    # diffserv-reverse: None
    # srcaddr: all
    # dstaddr: google-play
    # delay-tcp-npu-session: None
    # icap-profile: None
    # captive-portal-exempt: None
    # vpn_dst_node: {'subnet': None, 'host': None, 'seq': None}
    # app-category: None
    # rtp-addr: None
    # wsso: None
    # tcp-mss-receiver: None
    # ssh-filter-profile: None
    # radius-mac-auth-bypass: None
    # vpntunnel: None
    ##################################################
    ##################################################
    # wanopt-passive-opt: None
    # package_name: default
    # wanopt-detection: None
    # scan-botnet-connections: None
    # profile-group: None
    # wanopt-peer: None
    # dscp-match: None
    # replacemsg-override-group: None
    # internet-service-negate: None
    # np-acceleration: None
    # learning-mode: None
    # session-ttl: None
    # ntlm-guest: None
    # ips-sensor: None
    # diffservcode-rev: None
    # match-vip: None
    # natip: None
    # dlp-sensor: None
    # traffic-shaper: None
    # groups: None
    # schedule-timeout: None
    # name: Basic_IPv4_Policy
    # tcp-session-without-syn: None
    # ntlm: None
    # permit-stun-host: None
    # diffservcode-forward: None
    # internet-service-src-custom: None
    # mode: delete
    # disclaimer: None
    # rtp-nat: None
    # auth-cert: None
    # timeout-send-rst: None
    # auth-redirect-addr: None
    # ssl-mirror-intf: None
    # identity-based-route: None
    # natoutbound: None
    # wanopt-profile: None
    # per-ip-shaper: None
    # profile-protocol-options: None
    # diffserv-forward: None
    # poolname: None
    # comments: None
    # label: None
    # global-label: None
    # firewall-session-dirty: None
    # wanopt: None
    # schedule: None
    # internet-service-id: None
    # auth-path: None
    # vlan-cos-fwd: None
    # custom-log-fields: None
    # dstintf: None
    # srcintf: None
    # block-notification: None
    # internet-service-src-id: None
    # redirect-url: None
    # waf-profile: None
    # ntlm-enabled-browsers: None
    # dscp-negate: None
    # action: None
    # fsso-agent-for-ntlm: None
    # logtraffic: None
    # vlan-filter: None
    # policyid: 36
    # logtraffic-start: None
    # webcache-https: None
    # webfilter-profile: None
    # internet-service-src: None
    # webcache: None
    # utm-status: None
    # vpn_src_node: {'subnet': None, 'host': None, 'seq': None}
    # ippool: None
    # service: None
    # wccp: None
    # auto-asic-offload: None
    # dscp-value: None
    # url-category: None
    # capture-packet: None
    # adom: ansible
    # inbound: None
    # internet-service: None
    # profile-type: None
    # ssl-mirror: None
    # srcaddr-negate: None
    # gtp-profile: None
    # mms-profile: None
    # send-deny-packet: None
    # devices: None
    # permit-any-host: None
    # av-profile: None
    # internet-service-src-negate: None
    # service-negate: None
    # rsso: None
    # app-group: None
    # tcp-mss-sender: None
    # natinbound: None
    # fixedport: None
    # ssl-ssh-profile: None
    # outbound: None
    # spamfilter-profile: None
    # application-list: None
    # application: None
    # dnsfilter-profile: None
    # nat: None
    # fsso: None
    # vlan-cos-rev: None
    # status: None
    # dsri: None
    # users: None
    # voip-profile: None
    # dstaddr-negate: None
    # traffic-shaper-reverse: None
    # internet-service-custom: None
    # diffserv-reverse: None
    # srcaddr: None
    # ssh-filter-profile: None
    # delay-tcp-npu-session: None
    # icap-profile: None
    # captive-portal-exempt: None
    # vpn_dst_node: {'subnet': None, 'host': None, 'seq': None}
    # app-category: None
    # rtp-addr: None
    # wsso: None
    # tcp-mss-receiver: None
    # dstaddr: None
    # radius-mac-auth-bypass: None
    # vpntunnel: None
    ##################################################
    ##################################################
    # package_name: default
    # wanopt-detection: None
    # scan-botnet-connections: None
    # profile-group: None
    # dlp-sensor: None
    # dscp-match: None
    # replacemsg-override-group: None
    # internet-service-negate: None
    # np-acceleration: None
    # learning-mode: None
    # session-ttl: None
    # ntlm-guest: None
    # ips-sensor: None
    # diffservcode-rev: None
    # match-vip: None
    # natip: None
    # wanopt-peer: None
    # traffic-shaper: None
    # groups: None
    # schedule-timeout: None
    # name: Basic_IPv4_Policy_2
    # tcp-session-without-syn: None
    # rtp-nat: None
    # permit-stun-host: None
    # natoutbound: None
    # internet-service-src-custom: None
    # mode: delete
    # logtraffic: None
    # ntlm: None
    # auth-cert: None
    # timeout-send-rst: None
    # auth-redirect-addr: None
    # ssl-mirror-intf: None
    # identity-based-route: None
    # diffservcode-forward: None
    # wanopt-profile: None
    # per-ip-shaper: None
    # users: None
    # diffserv-forward: None
    # poolname: None
    # comments: None
    # label: None
    # global-label: None
    # firewall-session-dirty: None
    # wanopt: None
    # schedule: None
    # internet-service-id: None
    # auth-path: None
    # vlan-cos-fwd: None
    # custom-log-fields: None
    # dstintf: None
    # srcintf: None
    # block-notification: None
    # internet-service-src-id: None
    # redirect-url: None
    # waf-profile: None
    # ntlm-enabled-browsers: None
    # dscp-negate: None
    # action: None
    # fsso-agent-for-ntlm: None
    # disclaimer: None
    # vlan-filter: None
    # dstaddr-negate: None
    # logtraffic-start: None
    # webcache-https: None
    # webfilter-profile: None
    # internet-service-src: None
    # webcache: None
    # utm-status: None
    # vpn_src_node: {'subnet': None, 'host': None, 'seq': None}
    # ippool: None
    # service: None
    # wccp: None
    # auto-asic-offload: None
    # dscp-value: None
    # url-category: None
    # capture-packet: None
    # adom: ansible
    # internet-service: None
    # inbound: None
    # profile-type: None
    # ssl-mirror: None
    # srcaddr-negate: None
    # gtp-profile: None
    # mms-profile: None
    # send-deny-packet: None
    # devices: None
    # permit-any-host: None
    # av-profile: None
    # internet-service-src-negate: None
    # service-negate: None
    # rsso: None
    # application-list: None
    # app-group: None
    # tcp-mss-sender: None
    # natinbound: None
    # fixedport: None
    # ssl-ssh-profile: None
    # outbound: None
    # spamfilter-profile: None
    # wanopt-passive-opt: None
    # application: None
    # dnsfilter-profile: None
    # nat: None
    # fsso: None
    # vlan-cos-rev: None
    # status: None
    # dsri: None
    # profile-protocol-options: None
    # voip-profile: None
    # policyid: 37
    # traffic-shaper-reverse: None
    # internet-service-custom: None
    # diffserv-reverse: None
    # srcaddr: None
    # dstaddr: None
    # delay-tcp-npu-session: None
    # icap-profile: None
    # captive-portal-exempt: None
    # vpn_dst_node: {'subnet': None, 'host': None, 'seq': None}
    # app-category: None
    # rtp-addr: None
    # wsso: None
    # tcp-mss-receiver: None
    # ssh-filter-profile: None
    # radius-mac-auth-bypass: None
    # vpntunnel: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_modify(fmg_instance, fixture_data[0]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 2 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_modify(fmg_instance, fixture_data[1]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 3 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_modify(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_modify(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
