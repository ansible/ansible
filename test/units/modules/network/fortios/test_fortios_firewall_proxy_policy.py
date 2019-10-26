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
    from ansible.modules.network.fortios import fortios_firewall_proxy_policy
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_firewall_proxy_policy.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_firewall_proxy_policy_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_proxy_policy': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'disclaimer': 'disable',
            'dlp_sensor': 'test_value_8',
            'dstaddr_negate': 'enable',
            'global_label': 'test_value_10',
            'http_tunnel_auth': 'enable',
            'icap_profile': 'test_value_12',
            'internet_service': 'enable',
            'internet_service_negate': 'enable',
            'ips_sensor': 'test_value_15',
            'label': 'test_value_16',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'policyid': '19',
            'profile_group': 'test_value_20',
            'profile_protocol_options': 'test_value_21',
            'profile_type': 'single',
            'proxy': 'explicit-web',
            'redirect_url': 'test_value_24',
            'replacemsg_override_group': 'test_value_25',
            'scan_botnet_connections': 'disable',
            'schedule': 'test_value_27',
            'service_negate': 'enable',
            'session_ttl': '29',
            'spamfilter_profile': 'test_value_30',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_32',
            'ssl_ssh_profile': 'test_value_33',
            'status': 'enable',
            'transparent': 'enable',
            'utm_status': 'enable',
            'uuid': 'test_value_37',
            'waf_profile': 'test_value_38',
            'webcache': 'enable',
            'webcache_https': 'disable',
            'webfilter_profile': 'test_value_41',
            'webproxy_forward_server': 'test_value_42',
            'webproxy_profile': 'test_value_43'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_proxy_policy.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'action': 'accept',
        'application-list': 'test_value_4',
        'av-profile': 'test_value_5',
        'comments': 'test_value_6',
        'disclaimer': 'disable',
        'dlp-sensor': 'test_value_8',
        'dstaddr-negate': 'enable',
        'global-label': 'test_value_10',
        'http-tunnel-auth': 'enable',
        'icap-profile': 'test_value_12',
        'internet-service': 'enable',
        'internet-service-negate': 'enable',
        'ips-sensor': 'test_value_15',
        'label': 'test_value_16',
        'logtraffic': 'all',
        'logtraffic-start': 'enable',
        'policyid': '19',
        'profile-group': 'test_value_20',
        'profile-protocol-options': 'test_value_21',
        'profile-type': 'single',
        'proxy': 'explicit-web',
        'redirect-url': 'test_value_24',
        'replacemsg-override-group': 'test_value_25',
        'scan-botnet-connections': 'disable',
        'schedule': 'test_value_27',
        'service-negate': 'enable',
        'session-ttl': '29',
        'spamfilter-profile': 'test_value_30',
        'srcaddr-negate': 'enable',
        'ssh-filter-profile': 'test_value_32',
        'ssl-ssh-profile': 'test_value_33',
        'status': 'enable',
        'transparent': 'enable',
        'utm-status': 'enable',
        'uuid': 'test_value_37',
                'waf-profile': 'test_value_38',
                'webcache': 'enable',
                'webcache-https': 'disable',
                'webfilter-profile': 'test_value_41',
                'webproxy-forward-server': 'test_value_42',
                'webproxy-profile': 'test_value_43'
    }

    set_method_mock.assert_called_with('firewall', 'proxy-policy', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_proxy_policy_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_proxy_policy': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'disclaimer': 'disable',
            'dlp_sensor': 'test_value_8',
            'dstaddr_negate': 'enable',
            'global_label': 'test_value_10',
            'http_tunnel_auth': 'enable',
            'icap_profile': 'test_value_12',
            'internet_service': 'enable',
            'internet_service_negate': 'enable',
            'ips_sensor': 'test_value_15',
            'label': 'test_value_16',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'policyid': '19',
            'profile_group': 'test_value_20',
            'profile_protocol_options': 'test_value_21',
            'profile_type': 'single',
            'proxy': 'explicit-web',
            'redirect_url': 'test_value_24',
            'replacemsg_override_group': 'test_value_25',
            'scan_botnet_connections': 'disable',
            'schedule': 'test_value_27',
            'service_negate': 'enable',
            'session_ttl': '29',
            'spamfilter_profile': 'test_value_30',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_32',
            'ssl_ssh_profile': 'test_value_33',
            'status': 'enable',
            'transparent': 'enable',
            'utm_status': 'enable',
            'uuid': 'test_value_37',
            'waf_profile': 'test_value_38',
            'webcache': 'enable',
            'webcache_https': 'disable',
            'webfilter_profile': 'test_value_41',
            'webproxy_forward_server': 'test_value_42',
            'webproxy_profile': 'test_value_43'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_proxy_policy.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'action': 'accept',
        'application-list': 'test_value_4',
        'av-profile': 'test_value_5',
        'comments': 'test_value_6',
        'disclaimer': 'disable',
        'dlp-sensor': 'test_value_8',
        'dstaddr-negate': 'enable',
        'global-label': 'test_value_10',
        'http-tunnel-auth': 'enable',
        'icap-profile': 'test_value_12',
        'internet-service': 'enable',
        'internet-service-negate': 'enable',
        'ips-sensor': 'test_value_15',
        'label': 'test_value_16',
        'logtraffic': 'all',
        'logtraffic-start': 'enable',
        'policyid': '19',
        'profile-group': 'test_value_20',
        'profile-protocol-options': 'test_value_21',
        'profile-type': 'single',
        'proxy': 'explicit-web',
        'redirect-url': 'test_value_24',
        'replacemsg-override-group': 'test_value_25',
        'scan-botnet-connections': 'disable',
        'schedule': 'test_value_27',
        'service-negate': 'enable',
        'session-ttl': '29',
        'spamfilter-profile': 'test_value_30',
        'srcaddr-negate': 'enable',
        'ssh-filter-profile': 'test_value_32',
        'ssl-ssh-profile': 'test_value_33',
        'status': 'enable',
        'transparent': 'enable',
        'utm-status': 'enable',
        'uuid': 'test_value_37',
                'waf-profile': 'test_value_38',
                'webcache': 'enable',
                'webcache-https': 'disable',
                'webfilter-profile': 'test_value_41',
                'webproxy-forward-server': 'test_value_42',
                'webproxy-profile': 'test_value_43'
    }

    set_method_mock.assert_called_with('firewall', 'proxy-policy', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_proxy_policy_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_proxy_policy': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'disclaimer': 'disable',
            'dlp_sensor': 'test_value_8',
            'dstaddr_negate': 'enable',
            'global_label': 'test_value_10',
            'http_tunnel_auth': 'enable',
            'icap_profile': 'test_value_12',
            'internet_service': 'enable',
            'internet_service_negate': 'enable',
            'ips_sensor': 'test_value_15',
            'label': 'test_value_16',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'policyid': '19',
            'profile_group': 'test_value_20',
            'profile_protocol_options': 'test_value_21',
            'profile_type': 'single',
            'proxy': 'explicit-web',
            'redirect_url': 'test_value_24',
            'replacemsg_override_group': 'test_value_25',
            'scan_botnet_connections': 'disable',
            'schedule': 'test_value_27',
            'service_negate': 'enable',
            'session_ttl': '29',
            'spamfilter_profile': 'test_value_30',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_32',
            'ssl_ssh_profile': 'test_value_33',
            'status': 'enable',
            'transparent': 'enable',
            'utm_status': 'enable',
            'uuid': 'test_value_37',
            'waf_profile': 'test_value_38',
            'webcache': 'enable',
            'webcache_https': 'disable',
            'webfilter_profile': 'test_value_41',
            'webproxy_forward_server': 'test_value_42',
            'webproxy_profile': 'test_value_43'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_proxy_policy.fortios_firewall(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall', 'proxy-policy', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_proxy_policy_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_proxy_policy': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'disclaimer': 'disable',
            'dlp_sensor': 'test_value_8',
            'dstaddr_negate': 'enable',
            'global_label': 'test_value_10',
            'http_tunnel_auth': 'enable',
            'icap_profile': 'test_value_12',
            'internet_service': 'enable',
            'internet_service_negate': 'enable',
            'ips_sensor': 'test_value_15',
            'label': 'test_value_16',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'policyid': '19',
            'profile_group': 'test_value_20',
            'profile_protocol_options': 'test_value_21',
            'profile_type': 'single',
            'proxy': 'explicit-web',
            'redirect_url': 'test_value_24',
            'replacemsg_override_group': 'test_value_25',
            'scan_botnet_connections': 'disable',
            'schedule': 'test_value_27',
            'service_negate': 'enable',
            'session_ttl': '29',
            'spamfilter_profile': 'test_value_30',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_32',
            'ssl_ssh_profile': 'test_value_33',
            'status': 'enable',
            'transparent': 'enable',
            'utm_status': 'enable',
            'uuid': 'test_value_37',
            'waf_profile': 'test_value_38',
            'webcache': 'enable',
            'webcache_https': 'disable',
            'webfilter_profile': 'test_value_41',
            'webproxy_forward_server': 'test_value_42',
            'webproxy_profile': 'test_value_43'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_proxy_policy.fortios_firewall(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall', 'proxy-policy', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_proxy_policy_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_proxy_policy': {
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'disclaimer': 'disable',
            'dlp_sensor': 'test_value_8',
            'dstaddr_negate': 'enable',
            'global_label': 'test_value_10',
            'http_tunnel_auth': 'enable',
            'icap_profile': 'test_value_12',
            'internet_service': 'enable',
            'internet_service_negate': 'enable',
            'ips_sensor': 'test_value_15',
            'label': 'test_value_16',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'policyid': '19',
            'profile_group': 'test_value_20',
            'profile_protocol_options': 'test_value_21',
            'profile_type': 'single',
            'proxy': 'explicit-web',
            'redirect_url': 'test_value_24',
            'replacemsg_override_group': 'test_value_25',
            'scan_botnet_connections': 'disable',
            'schedule': 'test_value_27',
            'service_negate': 'enable',
            'session_ttl': '29',
            'spamfilter_profile': 'test_value_30',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_32',
            'ssl_ssh_profile': 'test_value_33',
            'status': 'enable',
            'transparent': 'enable',
            'utm_status': 'enable',
            'uuid': 'test_value_37',
            'waf_profile': 'test_value_38',
            'webcache': 'enable',
            'webcache_https': 'disable',
            'webfilter_profile': 'test_value_41',
            'webproxy_forward_server': 'test_value_42',
            'webproxy_profile': 'test_value_43'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_proxy_policy.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'action': 'accept',
        'application-list': 'test_value_4',
        'av-profile': 'test_value_5',
        'comments': 'test_value_6',
        'disclaimer': 'disable',
        'dlp-sensor': 'test_value_8',
        'dstaddr-negate': 'enable',
        'global-label': 'test_value_10',
        'http-tunnel-auth': 'enable',
        'icap-profile': 'test_value_12',
        'internet-service': 'enable',
        'internet-service-negate': 'enable',
        'ips-sensor': 'test_value_15',
        'label': 'test_value_16',
        'logtraffic': 'all',
        'logtraffic-start': 'enable',
        'policyid': '19',
        'profile-group': 'test_value_20',
        'profile-protocol-options': 'test_value_21',
        'profile-type': 'single',
        'proxy': 'explicit-web',
        'redirect-url': 'test_value_24',
        'replacemsg-override-group': 'test_value_25',
        'scan-botnet-connections': 'disable',
        'schedule': 'test_value_27',
        'service-negate': 'enable',
        'session-ttl': '29',
        'spamfilter-profile': 'test_value_30',
        'srcaddr-negate': 'enable',
        'ssh-filter-profile': 'test_value_32',
        'ssl-ssh-profile': 'test_value_33',
        'status': 'enable',
        'transparent': 'enable',
        'utm-status': 'enable',
        'uuid': 'test_value_37',
                'waf-profile': 'test_value_38',
                'webcache': 'enable',
                'webcache-https': 'disable',
                'webfilter-profile': 'test_value_41',
                'webproxy-forward-server': 'test_value_42',
                'webproxy-profile': 'test_value_43'
    }

    set_method_mock.assert_called_with('firewall', 'proxy-policy', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_firewall_proxy_policy_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_proxy_policy': {
            'random_attribute_not_valid': 'tag',
            'action': 'accept',
            'application_list': 'test_value_4',
            'av_profile': 'test_value_5',
            'comments': 'test_value_6',
            'disclaimer': 'disable',
            'dlp_sensor': 'test_value_8',
            'dstaddr_negate': 'enable',
            'global_label': 'test_value_10',
            'http_tunnel_auth': 'enable',
            'icap_profile': 'test_value_12',
            'internet_service': 'enable',
            'internet_service_negate': 'enable',
            'ips_sensor': 'test_value_15',
            'label': 'test_value_16',
            'logtraffic': 'all',
            'logtraffic_start': 'enable',
            'policyid': '19',
            'profile_group': 'test_value_20',
            'profile_protocol_options': 'test_value_21',
            'profile_type': 'single',
            'proxy': 'explicit-web',
            'redirect_url': 'test_value_24',
            'replacemsg_override_group': 'test_value_25',
            'scan_botnet_connections': 'disable',
            'schedule': 'test_value_27',
            'service_negate': 'enable',
            'session_ttl': '29',
            'spamfilter_profile': 'test_value_30',
            'srcaddr_negate': 'enable',
            'ssh_filter_profile': 'test_value_32',
            'ssl_ssh_profile': 'test_value_33',
            'status': 'enable',
            'transparent': 'enable',
            'utm_status': 'enable',
            'uuid': 'test_value_37',
            'waf_profile': 'test_value_38',
            'webcache': 'enable',
            'webcache_https': 'disable',
            'webfilter_profile': 'test_value_41',
            'webproxy_forward_server': 'test_value_42',
            'webproxy_profile': 'test_value_43'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_proxy_policy.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'action': 'accept',
        'application-list': 'test_value_4',
        'av-profile': 'test_value_5',
        'comments': 'test_value_6',
        'disclaimer': 'disable',
        'dlp-sensor': 'test_value_8',
        'dstaddr-negate': 'enable',
        'global-label': 'test_value_10',
        'http-tunnel-auth': 'enable',
        'icap-profile': 'test_value_12',
        'internet-service': 'enable',
        'internet-service-negate': 'enable',
        'ips-sensor': 'test_value_15',
        'label': 'test_value_16',
        'logtraffic': 'all',
        'logtraffic-start': 'enable',
        'policyid': '19',
        'profile-group': 'test_value_20',
        'profile-protocol-options': 'test_value_21',
        'profile-type': 'single',
        'proxy': 'explicit-web',
        'redirect-url': 'test_value_24',
        'replacemsg-override-group': 'test_value_25',
        'scan-botnet-connections': 'disable',
        'schedule': 'test_value_27',
        'service-negate': 'enable',
        'session-ttl': '29',
        'spamfilter-profile': 'test_value_30',
        'srcaddr-negate': 'enable',
        'ssh-filter-profile': 'test_value_32',
        'ssl-ssh-profile': 'test_value_33',
        'status': 'enable',
        'transparent': 'enable',
        'utm-status': 'enable',
        'uuid': 'test_value_37',
                'waf-profile': 'test_value_38',
                'webcache': 'enable',
                'webcache-https': 'disable',
                'webfilter-profile': 'test_value_41',
                'webproxy-forward-server': 'test_value_42',
                'webproxy-profile': 'test_value_43'
    }

    set_method_mock.assert_called_with('firewall', 'proxy-policy', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
