# Copyright 2019 Fortinet, Inc.
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
import pytest
from mock import ANY
from ansible.module_utils.network.fortios.fortios import FortiOSHandler

try:
    from ansible.modules.network.fortios import fortios_firewall_policy6
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_firewall_policy6.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_firewall_policy6_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_policy6': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'diffserv_forward': 'enable',
            'diffserv_reverse': 'enable',
            'diffservcode_forward': 'test_value_9',
            'diffservcode_rev': 'test_value_10',
            'dlp_sensor': 'test_value_11',
            'dscp_match': 'enable',
            'dscp_negate': 'enable',
            'dscp_value': 'test_value_14',
            'dsri': 'enable',
            'dstaddr_negate': 'enable',
            'firewall_session_dirty': 'check-all',
            'fixedport': 'enable',
            'global_label': 'test_value_19',
            'icap_profile': 'test_value_20',
            'inbound': 'enable',
            'ippool': 'enable',
            'ips_sensor': 'test_value_23',
            'label': 'test_value_24',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'name': 'default_name_27',
            'nat': 'enable',
            'natinbound': 'enable',
            'natoutbound': 'enable',
            'outbound': 'enable',
            'per_ip_shaper': 'test_value_32',
            'policyid': '33',
            'profile_group': 'test_value_34',
            'profile_protocol_options': 'test_value_35',
            'profile_type': 'single',
            'replacemsg_override_group': 'test_value_37',
            'rsso': 'enable',
            'schedule': 'test_value_39',
            'send_deny_packet': 'enable',
            'service_negate': 'enable',
            'session_ttl': '42',
            'spamfilter_profile': 'test_value_43',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_45',
            'ssl_mirror': 'enable',
            'ssl_ssh_profile': 'test_value_47',
            'status': 'enable',
            'tcp_mss_receiver': '49',
            'tcp_mss_sender': '50',
            'tcp_session_without_syn': 'all',
            'timeout_send_rst': 'enable',
            'traffic_shaper': 'test_value_53',
            'traffic_shaper_reverse': 'test_value_54',
            'utm_status': 'enable',
            'uuid': 'test_value_56',
            'vlan_cos_fwd': '57',
            'vlan_cos_rev': '58',
            'vlan_filter': 'test_value_59',
            'voip_profile': 'test_value_60',
            'vpntunnel': 'test_value_61',
            'webfilter_profile': 'test_value_62'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_policy6.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'action': 'accept',
        'application-list': 'test_value_4',
        'av-profile': 'test_value_5',
        'comments': 'test_value_6',
        'diffserv-forward': 'enable',
        'diffserv-reverse': 'enable',
        'diffservcode-forward': 'test_value_9',
        'diffservcode-rev': 'test_value_10',
        'dlp-sensor': 'test_value_11',
        'dscp-match': 'enable',
        'dscp-negate': 'enable',
        'dscp-value': 'test_value_14',
        'dsri': 'enable',
                'dstaddr-negate': 'enable',
                'firewall-session-dirty': 'check-all',
                'fixedport': 'enable',
                'global-label': 'test_value_19',
                'icap-profile': 'test_value_20',
                'inbound': 'enable',
                'ippool': 'enable',
                'ips-sensor': 'test_value_23',
                'label': 'test_value_24',
                'logtraffic': 'all',
                'logtraffic-start': 'enable',
                'name': 'default_name_27',
                'nat': 'enable',
                'natinbound': 'enable',
                'natoutbound': 'enable',
                'outbound': 'enable',
                'per-ip-shaper': 'test_value_32',
                'policyid': '33',
                'profile-group': 'test_value_34',
                'profile-protocol-options': 'test_value_35',
                'profile-type': 'single',
                'replacemsg-override-group': 'test_value_37',
                'rsso': 'enable',
                'schedule': 'test_value_39',
                'send-deny-packet': 'enable',
                'service-negate': 'enable',
                'session-ttl': '42',
                'spamfilter-profile': 'test_value_43',
                'srcaddr-negate': 'enable',
                'ssh-filter-profile': 'test_value_45',
                'ssl-mirror': 'enable',
                'ssl-ssh-profile': 'test_value_47',
                'status': 'enable',
                'tcp-mss-receiver': '49',
                'tcp-mss-sender': '50',
                'tcp-session-without-syn': 'all',
                'timeout-send-rst': 'enable',
                'traffic-shaper': 'test_value_53',
                'traffic-shaper-reverse': 'test_value_54',
                'utm-status': 'enable',
                'uuid': 'test_value_56',
                'vlan-cos-fwd': '57',
                'vlan-cos-rev': '58',
                'vlan-filter': 'test_value_59',
                'voip-profile': 'test_value_60',
                'vpntunnel': 'test_value_61',
                'webfilter-profile': 'test_value_62'
    }

    set_method_mock.assert_called_with('firewall', 'policy6', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_policy6_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_policy6': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'diffserv_forward': 'enable',
            'diffserv_reverse': 'enable',
            'diffservcode_forward': 'test_value_9',
            'diffservcode_rev': 'test_value_10',
            'dlp_sensor': 'test_value_11',
            'dscp_match': 'enable',
            'dscp_negate': 'enable',
            'dscp_value': 'test_value_14',
            'dsri': 'enable',
            'dstaddr_negate': 'enable',
            'firewall_session_dirty': 'check-all',
            'fixedport': 'enable',
            'global_label': 'test_value_19',
            'icap_profile': 'test_value_20',
            'inbound': 'enable',
            'ippool': 'enable',
            'ips_sensor': 'test_value_23',
            'label': 'test_value_24',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'name': 'default_name_27',
            'nat': 'enable',
            'natinbound': 'enable',
            'natoutbound': 'enable',
            'outbound': 'enable',
            'per_ip_shaper': 'test_value_32',
            'policyid': '33',
            'profile_group': 'test_value_34',
            'profile_protocol_options': 'test_value_35',
            'profile_type': 'single',
            'replacemsg_override_group': 'test_value_37',
            'rsso': 'enable',
            'schedule': 'test_value_39',
            'send_deny_packet': 'enable',
            'service_negate': 'enable',
            'session_ttl': '42',
            'spamfilter_profile': 'test_value_43',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_45',
            'ssl_mirror': 'enable',
            'ssl_ssh_profile': 'test_value_47',
            'status': 'enable',
            'tcp_mss_receiver': '49',
            'tcp_mss_sender': '50',
            'tcp_session_without_syn': 'all',
            'timeout_send_rst': 'enable',
            'traffic_shaper': 'test_value_53',
            'traffic_shaper_reverse': 'test_value_54',
            'utm_status': 'enable',
            'uuid': 'test_value_56',
            'vlan_cos_fwd': '57',
            'vlan_cos_rev': '58',
            'vlan_filter': 'test_value_59',
            'voip_profile': 'test_value_60',
            'vpntunnel': 'test_value_61',
            'webfilter_profile': 'test_value_62'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_policy6.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'action': 'accept',
        'application-list': 'test_value_4',
        'av-profile': 'test_value_5',
        'comments': 'test_value_6',
        'diffserv-forward': 'enable',
        'diffserv-reverse': 'enable',
        'diffservcode-forward': 'test_value_9',
        'diffservcode-rev': 'test_value_10',
        'dlp-sensor': 'test_value_11',
        'dscp-match': 'enable',
        'dscp-negate': 'enable',
        'dscp-value': 'test_value_14',
        'dsri': 'enable',
                'dstaddr-negate': 'enable',
                'firewall-session-dirty': 'check-all',
                'fixedport': 'enable',
                'global-label': 'test_value_19',
                'icap-profile': 'test_value_20',
                'inbound': 'enable',
                'ippool': 'enable',
                'ips-sensor': 'test_value_23',
                'label': 'test_value_24',
                'logtraffic': 'all',
                'logtraffic-start': 'enable',
                'name': 'default_name_27',
                'nat': 'enable',
                'natinbound': 'enable',
                'natoutbound': 'enable',
                'outbound': 'enable',
                'per-ip-shaper': 'test_value_32',
                'policyid': '33',
                'profile-group': 'test_value_34',
                'profile-protocol-options': 'test_value_35',
                'profile-type': 'single',
                'replacemsg-override-group': 'test_value_37',
                'rsso': 'enable',
                'schedule': 'test_value_39',
                'send-deny-packet': 'enable',
                'service-negate': 'enable',
                'session-ttl': '42',
                'spamfilter-profile': 'test_value_43',
                'srcaddr-negate': 'enable',
                'ssh-filter-profile': 'test_value_45',
                'ssl-mirror': 'enable',
                'ssl-ssh-profile': 'test_value_47',
                'status': 'enable',
                'tcp-mss-receiver': '49',
                'tcp-mss-sender': '50',
                'tcp-session-without-syn': 'all',
                'timeout-send-rst': 'enable',
                'traffic-shaper': 'test_value_53',
                'traffic-shaper-reverse': 'test_value_54',
                'utm-status': 'enable',
                'uuid': 'test_value_56',
                'vlan-cos-fwd': '57',
                'vlan-cos-rev': '58',
                'vlan-filter': 'test_value_59',
                'voip-profile': 'test_value_60',
                'vpntunnel': 'test_value_61',
                'webfilter-profile': 'test_value_62'
    }

    set_method_mock.assert_called_with('firewall', 'policy6', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_policy6_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_policy6': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'diffserv_forward': 'enable',
            'diffserv_reverse': 'enable',
            'diffservcode_forward': 'test_value_9',
            'diffservcode_rev': 'test_value_10',
            'dlp_sensor': 'test_value_11',
            'dscp_match': 'enable',
            'dscp_negate': 'enable',
            'dscp_value': 'test_value_14',
            'dsri': 'enable',
            'dstaddr_negate': 'enable',
            'firewall_session_dirty': 'check-all',
            'fixedport': 'enable',
            'global_label': 'test_value_19',
            'icap_profile': 'test_value_20',
            'inbound': 'enable',
            'ippool': 'enable',
            'ips_sensor': 'test_value_23',
            'label': 'test_value_24',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'name': 'default_name_27',
            'nat': 'enable',
            'natinbound': 'enable',
            'natoutbound': 'enable',
            'outbound': 'enable',
            'per_ip_shaper': 'test_value_32',
            'policyid': '33',
            'profile_group': 'test_value_34',
            'profile_protocol_options': 'test_value_35',
            'profile_type': 'single',
            'replacemsg_override_group': 'test_value_37',
            'rsso': 'enable',
            'schedule': 'test_value_39',
            'send_deny_packet': 'enable',
            'service_negate': 'enable',
            'session_ttl': '42',
            'spamfilter_profile': 'test_value_43',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_45',
            'ssl_mirror': 'enable',
            'ssl_ssh_profile': 'test_value_47',
            'status': 'enable',
            'tcp_mss_receiver': '49',
            'tcp_mss_sender': '50',
            'tcp_session_without_syn': 'all',
            'timeout_send_rst': 'enable',
            'traffic_shaper': 'test_value_53',
            'traffic_shaper_reverse': 'test_value_54',
            'utm_status': 'enable',
            'uuid': 'test_value_56',
            'vlan_cos_fwd': '57',
            'vlan_cos_rev': '58',
            'vlan_filter': 'test_value_59',
            'voip_profile': 'test_value_60',
            'vpntunnel': 'test_value_61',
            'webfilter_profile': 'test_value_62'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_policy6.fortios_firewall(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall', 'policy6', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_policy6_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_policy6': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'diffserv_forward': 'enable',
            'diffserv_reverse': 'enable',
            'diffservcode_forward': 'test_value_9',
            'diffservcode_rev': 'test_value_10',
            'dlp_sensor': 'test_value_11',
            'dscp_match': 'enable',
            'dscp_negate': 'enable',
            'dscp_value': 'test_value_14',
            'dsri': 'enable',
            'dstaddr_negate': 'enable',
            'firewall_session_dirty': 'check-all',
            'fixedport': 'enable',
            'global_label': 'test_value_19',
            'icap_profile': 'test_value_20',
            'inbound': 'enable',
            'ippool': 'enable',
            'ips_sensor': 'test_value_23',
            'label': 'test_value_24',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'name': 'default_name_27',
            'nat': 'enable',
            'natinbound': 'enable',
            'natoutbound': 'enable',
            'outbound': 'enable',
            'per_ip_shaper': 'test_value_32',
            'policyid': '33',
            'profile_group': 'test_value_34',
            'profile_protocol_options': 'test_value_35',
            'profile_type': 'single',
            'replacemsg_override_group': 'test_value_37',
            'rsso': 'enable',
            'schedule': 'test_value_39',
            'send_deny_packet': 'enable',
            'service_negate': 'enable',
            'session_ttl': '42',
            'spamfilter_profile': 'test_value_43',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_45',
            'ssl_mirror': 'enable',
            'ssl_ssh_profile': 'test_value_47',
            'status': 'enable',
            'tcp_mss_receiver': '49',
            'tcp_mss_sender': '50',
            'tcp_session_without_syn': 'all',
            'timeout_send_rst': 'enable',
            'traffic_shaper': 'test_value_53',
            'traffic_shaper_reverse': 'test_value_54',
            'utm_status': 'enable',
            'uuid': 'test_value_56',
            'vlan_cos_fwd': '57',
            'vlan_cos_rev': '58',
            'vlan_filter': 'test_value_59',
            'voip_profile': 'test_value_60',
            'vpntunnel': 'test_value_61',
            'webfilter_profile': 'test_value_62'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_policy6.fortios_firewall(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall', 'policy6', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_policy6_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_policy6': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'diffserv_forward': 'enable',
            'diffserv_reverse': 'enable',
            'diffservcode_forward': 'test_value_9',
            'diffservcode_rev': 'test_value_10',
            'dlp_sensor': 'test_value_11',
            'dscp_match': 'enable',
            'dscp_negate': 'enable',
            'dscp_value': 'test_value_14',
            'dsri': 'enable',
            'dstaddr_negate': 'enable',
            'firewall_session_dirty': 'check-all',
            'fixedport': 'enable',
            'global_label': 'test_value_19',
            'icap_profile': 'test_value_20',
            'inbound': 'enable',
            'ippool': 'enable',
            'ips_sensor': 'test_value_23',
            'label': 'test_value_24',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'name': 'default_name_27',
            'nat': 'enable',
            'natinbound': 'enable',
            'natoutbound': 'enable',
            'outbound': 'enable',
            'per_ip_shaper': 'test_value_32',
            'policyid': '33',
            'profile_group': 'test_value_34',
            'profile_protocol_options': 'test_value_35',
            'profile_type': 'single',
            'replacemsg_override_group': 'test_value_37',
            'rsso': 'enable',
            'schedule': 'test_value_39',
            'send_deny_packet': 'enable',
            'service_negate': 'enable',
            'session_ttl': '42',
            'spamfilter_profile': 'test_value_43',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_45',
            'ssl_mirror': 'enable',
            'ssl_ssh_profile': 'test_value_47',
            'status': 'enable',
            'tcp_mss_receiver': '49',
            'tcp_mss_sender': '50',
            'tcp_session_without_syn': 'all',
            'timeout_send_rst': 'enable',
            'traffic_shaper': 'test_value_53',
            'traffic_shaper_reverse': 'test_value_54',
            'utm_status': 'enable',
            'uuid': 'test_value_56',
            'vlan_cos_fwd': '57',
            'vlan_cos_rev': '58',
            'vlan_filter': 'test_value_59',
            'voip_profile': 'test_value_60',
            'vpntunnel': 'test_value_61',
            'webfilter_profile': 'test_value_62'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_policy6.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'action': 'accept',
        'application-list': 'test_value_4',
        'av-profile': 'test_value_5',
        'comments': 'test_value_6',
        'diffserv-forward': 'enable',
        'diffserv-reverse': 'enable',
        'diffservcode-forward': 'test_value_9',
        'diffservcode-rev': 'test_value_10',
        'dlp-sensor': 'test_value_11',
        'dscp-match': 'enable',
        'dscp-negate': 'enable',
        'dscp-value': 'test_value_14',
        'dsri': 'enable',
                'dstaddr-negate': 'enable',
                'firewall-session-dirty': 'check-all',
                'fixedport': 'enable',
                'global-label': 'test_value_19',
                'icap-profile': 'test_value_20',
                'inbound': 'enable',
                'ippool': 'enable',
                'ips-sensor': 'test_value_23',
                'label': 'test_value_24',
                'logtraffic': 'all',
                'logtraffic-start': 'enable',
                'name': 'default_name_27',
                'nat': 'enable',
                'natinbound': 'enable',
                'natoutbound': 'enable',
                'outbound': 'enable',
                'per-ip-shaper': 'test_value_32',
                'policyid': '33',
                'profile-group': 'test_value_34',
                'profile-protocol-options': 'test_value_35',
                'profile-type': 'single',
                'replacemsg-override-group': 'test_value_37',
                'rsso': 'enable',
                'schedule': 'test_value_39',
                'send-deny-packet': 'enable',
                'service-negate': 'enable',
                'session-ttl': '42',
                'spamfilter-profile': 'test_value_43',
                'srcaddr-negate': 'enable',
                'ssh-filter-profile': 'test_value_45',
                'ssl-mirror': 'enable',
                'ssl-ssh-profile': 'test_value_47',
                'status': 'enable',
                'tcp-mss-receiver': '49',
                'tcp-mss-sender': '50',
                'tcp-session-without-syn': 'all',
                'timeout-send-rst': 'enable',
                'traffic-shaper': 'test_value_53',
                'traffic-shaper-reverse': 'test_value_54',
                'utm-status': 'enable',
                'uuid': 'test_value_56',
                'vlan-cos-fwd': '57',
                'vlan-cos-rev': '58',
                'vlan-filter': 'test_value_59',
                'voip-profile': 'test_value_60',
                'vpntunnel': 'test_value_61',
                'webfilter-profile': 'test_value_62'
    }

    set_method_mock.assert_called_with('firewall', 'policy6', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_firewall_policy6_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_policy6': {
            'random_attribute_not_valid': 'tag',
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'diffserv_forward': 'enable',
            'diffserv_reverse': 'enable',
            'diffservcode_forward': 'test_value_9',
            'diffservcode_rev': 'test_value_10',
            'dlp_sensor': 'test_value_11',
            'dscp_match': 'enable',
            'dscp_negate': 'enable',
            'dscp_value': 'test_value_14',
            'dsri': 'enable',
            'dstaddr_negate': 'enable',
            'firewall_session_dirty': 'check-all',
            'fixedport': 'enable',
            'global_label': 'test_value_19',
            'icap_profile': 'test_value_20',
            'inbound': 'enable',
            'ippool': 'enable',
            'ips_sensor': 'test_value_23',
            'label': 'test_value_24',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'name': 'default_name_27',
            'nat': 'enable',
            'natinbound': 'enable',
            'natoutbound': 'enable',
            'outbound': 'enable',
            'per_ip_shaper': 'test_value_32',
            'policyid': '33',
            'profile_group': 'test_value_34',
            'profile_protocol_options': 'test_value_35',
            'profile_type': 'single',
            'replacemsg_override_group': 'test_value_37',
            'rsso': 'enable',
            'schedule': 'test_value_39',
            'send_deny_packet': 'enable',
            'service_negate': 'enable',
            'session_ttl': '42',
            'spamfilter_profile': 'test_value_43',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_45',
            'ssl_mirror': 'enable',
            'ssl_ssh_profile': 'test_value_47',
            'status': 'enable',
            'tcp_mss_receiver': '49',
            'tcp_mss_sender': '50',
            'tcp_session_without_syn': 'all',
            'timeout_send_rst': 'enable',
            'traffic_shaper': 'test_value_53',
            'traffic_shaper_reverse': 'test_value_54',
            'utm_status': 'enable',
            'uuid': 'test_value_56',
            'vlan_cos_fwd': '57',
            'vlan_cos_rev': '58',
            'vlan_filter': 'test_value_59',
            'voip_profile': 'test_value_60',
            'vpntunnel': 'test_value_61',
            'webfilter_profile': 'test_value_62'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_policy6.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'action': 'accept',
        'application-list': 'test_value_4',
        'av-profile': 'test_value_5',
        'comments': 'test_value_6',
        'diffserv-forward': 'enable',
        'diffserv-reverse': 'enable',
        'diffservcode-forward': 'test_value_9',
        'diffservcode-rev': 'test_value_10',
        'dlp-sensor': 'test_value_11',
        'dscp-match': 'enable',
        'dscp-negate': 'enable',
        'dscp-value': 'test_value_14',
        'dsri': 'enable',
                'dstaddr-negate': 'enable',
                'firewall-session-dirty': 'check-all',
                'fixedport': 'enable',
                'global-label': 'test_value_19',
                'icap-profile': 'test_value_20',
                'inbound': 'enable',
                'ippool': 'enable',
                'ips-sensor': 'test_value_23',
                'label': 'test_value_24',
                'logtraffic': 'all',
                'logtraffic-start': 'enable',
                'name': 'default_name_27',
                'nat': 'enable',
                'natinbound': 'enable',
                'natoutbound': 'enable',
                'outbound': 'enable',
                'per-ip-shaper': 'test_value_32',
                'policyid': '33',
                'profile-group': 'test_value_34',
                'profile-protocol-options': 'test_value_35',
                'profile-type': 'single',
                'replacemsg-override-group': 'test_value_37',
                'rsso': 'enable',
                'schedule': 'test_value_39',
                'send-deny-packet': 'enable',
                'service-negate': 'enable',
                'session-ttl': '42',
                'spamfilter-profile': 'test_value_43',
                'srcaddr-negate': 'enable',
                'ssh-filter-profile': 'test_value_45',
                'ssl-mirror': 'enable',
                'ssl-ssh-profile': 'test_value_47',
                'status': 'enable',
                'tcp-mss-receiver': '49',
                'tcp-mss-sender': '50',
                'tcp-session-without-syn': 'all',
                'timeout-send-rst': 'enable',
                'traffic-shaper': 'test_value_53',
                'traffic-shaper-reverse': 'test_value_54',
                'utm-status': 'enable',
                'uuid': 'test_value_56',
                'vlan-cos-fwd': '57',
                'vlan-cos-rev': '58',
                'vlan-filter': 'test_value_59',
                'voip-profile': 'test_value_60',
                'vpntunnel': 'test_value_61',
                'webfilter-profile': 'test_value_62'
    }

    set_method_mock.assert_called_with('firewall', 'policy6', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
