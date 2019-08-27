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
    from ansible.modules.network.fortios import fortios_wireless_controller_hotspot20_hs_profile
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_hotspot20_hs_profile.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_hotspot20_hs_profile_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_hotspot20_hs_profile': {
            'access_network_asra': 'enable',
            'access_network_esr': 'enable',
            'access_network_internet': 'enable',
            'access_network_type': 'private-network',
            'access_network_uesa': 'enable',
            'anqp_domain_id': '9',
            'bss_transition': 'enable',
            'conn_cap': 'test_value_11',
            'deauth_request_timeout': '12',
            'dgaf': 'enable',
            'domain_name': 'test_value_14',
            'gas_comeback_delay': '15',
            'gas_fragmentation_limit': '16',
            'hessid': 'test_value_17',
            'ip_addr_type': 'test_value_18',
            'l2tif': 'enable',
            'nai_realm': 'test_value_20',
            'name': 'default_name_21',
            'network_auth': 'test_value_22',
            'oper_friendly_name': 'test_value_23',
            'osu_ssid': 'test_value_24',
            'pame_bi': 'disable',
            'proxy_arp': 'enable',
            'qos_map': 'test_value_27',
            'roaming_consortium': 'test_value_28',
            'venue_group': 'unspecified',
            'venue_name': 'test_value_30',
            'venue_type': 'unspecified',
            'wan_metrics': 'test_value_32',
            'wnm_sleep_mode': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_hs_profile.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    expected_data = {
        'access-network-asra': 'enable',
        'access-network-esr': 'enable',
        'access-network-internet': 'enable',
        'access-network-type': 'private-network',
        'access-network-uesa': 'enable',
        'anqp-domain-id': '9',
        'bss-transition': 'enable',
        'conn-cap': 'test_value_11',
        'deauth-request-timeout': '12',
        'dgaf': 'enable',
                'domain-name': 'test_value_14',
                'gas-comeback-delay': '15',
                'gas-fragmentation-limit': '16',
                'hessid': 'test_value_17',
                'ip-addr-type': 'test_value_18',
                'l2tif': 'enable',
                'nai-realm': 'test_value_20',
                'name': 'default_name_21',
                'network-auth': 'test_value_22',
                'oper-friendly-name': 'test_value_23',
                'osu-ssid': 'test_value_24',
                'pame-bi': 'disable',
                'proxy-arp': 'enable',
                'qos-map': 'test_value_27',
                'roaming-consortium': 'test_value_28',
                'venue-group': 'unspecified',
                'venue-name': 'test_value_30',
                'venue-type': 'unspecified',
                'wan-metrics': 'test_value_32',
                'wnm-sleep-mode': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller.hotspot20', 'hs-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_hotspot20_hs_profile_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_hotspot20_hs_profile': {
            'access_network_asra': 'enable',
            'access_network_esr': 'enable',
            'access_network_internet': 'enable',
            'access_network_type': 'private-network',
            'access_network_uesa': 'enable',
            'anqp_domain_id': '9',
            'bss_transition': 'enable',
            'conn_cap': 'test_value_11',
            'deauth_request_timeout': '12',
            'dgaf': 'enable',
            'domain_name': 'test_value_14',
            'gas_comeback_delay': '15',
            'gas_fragmentation_limit': '16',
            'hessid': 'test_value_17',
            'ip_addr_type': 'test_value_18',
            'l2tif': 'enable',
            'nai_realm': 'test_value_20',
            'name': 'default_name_21',
            'network_auth': 'test_value_22',
            'oper_friendly_name': 'test_value_23',
            'osu_ssid': 'test_value_24',
            'pame_bi': 'disable',
            'proxy_arp': 'enable',
            'qos_map': 'test_value_27',
            'roaming_consortium': 'test_value_28',
            'venue_group': 'unspecified',
            'venue_name': 'test_value_30',
            'venue_type': 'unspecified',
            'wan_metrics': 'test_value_32',
            'wnm_sleep_mode': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_hs_profile.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    expected_data = {
        'access-network-asra': 'enable',
        'access-network-esr': 'enable',
        'access-network-internet': 'enable',
        'access-network-type': 'private-network',
        'access-network-uesa': 'enable',
        'anqp-domain-id': '9',
        'bss-transition': 'enable',
        'conn-cap': 'test_value_11',
        'deauth-request-timeout': '12',
        'dgaf': 'enable',
                'domain-name': 'test_value_14',
                'gas-comeback-delay': '15',
                'gas-fragmentation-limit': '16',
                'hessid': 'test_value_17',
                'ip-addr-type': 'test_value_18',
                'l2tif': 'enable',
                'nai-realm': 'test_value_20',
                'name': 'default_name_21',
                'network-auth': 'test_value_22',
                'oper-friendly-name': 'test_value_23',
                'osu-ssid': 'test_value_24',
                'pame-bi': 'disable',
                'proxy-arp': 'enable',
                'qos-map': 'test_value_27',
                'roaming-consortium': 'test_value_28',
                'venue-group': 'unspecified',
                'venue-name': 'test_value_30',
                'venue-type': 'unspecified',
                'wan-metrics': 'test_value_32',
                'wnm-sleep-mode': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller.hotspot20', 'hs-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_hotspot20_hs_profile_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_hotspot20_hs_profile': {
            'access_network_asra': 'enable',
            'access_network_esr': 'enable',
            'access_network_internet': 'enable',
            'access_network_type': 'private-network',
            'access_network_uesa': 'enable',
            'anqp_domain_id': '9',
            'bss_transition': 'enable',
            'conn_cap': 'test_value_11',
            'deauth_request_timeout': '12',
            'dgaf': 'enable',
            'domain_name': 'test_value_14',
            'gas_comeback_delay': '15',
            'gas_fragmentation_limit': '16',
            'hessid': 'test_value_17',
            'ip_addr_type': 'test_value_18',
            'l2tif': 'enable',
            'nai_realm': 'test_value_20',
            'name': 'default_name_21',
            'network_auth': 'test_value_22',
            'oper_friendly_name': 'test_value_23',
            'osu_ssid': 'test_value_24',
            'pame_bi': 'disable',
            'proxy_arp': 'enable',
            'qos_map': 'test_value_27',
            'roaming_consortium': 'test_value_28',
            'venue_group': 'unspecified',
            'venue_name': 'test_value_30',
            'venue_type': 'unspecified',
            'wan_metrics': 'test_value_32',
            'wnm_sleep_mode': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_hs_profile.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller.hotspot20', 'hs-profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_hotspot20_hs_profile_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_hotspot20_hs_profile': {
            'access_network_asra': 'enable',
            'access_network_esr': 'enable',
            'access_network_internet': 'enable',
            'access_network_type': 'private-network',
            'access_network_uesa': 'enable',
            'anqp_domain_id': '9',
            'bss_transition': 'enable',
            'conn_cap': 'test_value_11',
            'deauth_request_timeout': '12',
            'dgaf': 'enable',
            'domain_name': 'test_value_14',
            'gas_comeback_delay': '15',
            'gas_fragmentation_limit': '16',
            'hessid': 'test_value_17',
            'ip_addr_type': 'test_value_18',
            'l2tif': 'enable',
            'nai_realm': 'test_value_20',
            'name': 'default_name_21',
            'network_auth': 'test_value_22',
            'oper_friendly_name': 'test_value_23',
            'osu_ssid': 'test_value_24',
            'pame_bi': 'disable',
            'proxy_arp': 'enable',
            'qos_map': 'test_value_27',
            'roaming_consortium': 'test_value_28',
            'venue_group': 'unspecified',
            'venue_name': 'test_value_30',
            'venue_type': 'unspecified',
            'wan_metrics': 'test_value_32',
            'wnm_sleep_mode': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_hs_profile.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller.hotspot20', 'hs-profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_hotspot20_hs_profile_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_hotspot20_hs_profile': {
            'access_network_asra': 'enable',
            'access_network_esr': 'enable',
            'access_network_internet': 'enable',
            'access_network_type': 'private-network',
            'access_network_uesa': 'enable',
            'anqp_domain_id': '9',
            'bss_transition': 'enable',
            'conn_cap': 'test_value_11',
            'deauth_request_timeout': '12',
            'dgaf': 'enable',
            'domain_name': 'test_value_14',
            'gas_comeback_delay': '15',
            'gas_fragmentation_limit': '16',
            'hessid': 'test_value_17',
            'ip_addr_type': 'test_value_18',
            'l2tif': 'enable',
            'nai_realm': 'test_value_20',
            'name': 'default_name_21',
            'network_auth': 'test_value_22',
            'oper_friendly_name': 'test_value_23',
            'osu_ssid': 'test_value_24',
            'pame_bi': 'disable',
            'proxy_arp': 'enable',
            'qos_map': 'test_value_27',
            'roaming_consortium': 'test_value_28',
            'venue_group': 'unspecified',
            'venue_name': 'test_value_30',
            'venue_type': 'unspecified',
            'wan_metrics': 'test_value_32',
            'wnm_sleep_mode': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_hs_profile.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    expected_data = {
        'access-network-asra': 'enable',
        'access-network-esr': 'enable',
        'access-network-internet': 'enable',
        'access-network-type': 'private-network',
        'access-network-uesa': 'enable',
        'anqp-domain-id': '9',
        'bss-transition': 'enable',
        'conn-cap': 'test_value_11',
        'deauth-request-timeout': '12',
        'dgaf': 'enable',
                'domain-name': 'test_value_14',
                'gas-comeback-delay': '15',
                'gas-fragmentation-limit': '16',
                'hessid': 'test_value_17',
                'ip-addr-type': 'test_value_18',
                'l2tif': 'enable',
                'nai-realm': 'test_value_20',
                'name': 'default_name_21',
                'network-auth': 'test_value_22',
                'oper-friendly-name': 'test_value_23',
                'osu-ssid': 'test_value_24',
                'pame-bi': 'disable',
                'proxy-arp': 'enable',
                'qos-map': 'test_value_27',
                'roaming-consortium': 'test_value_28',
                'venue-group': 'unspecified',
                'venue-name': 'test_value_30',
                'venue-type': 'unspecified',
                'wan-metrics': 'test_value_32',
                'wnm-sleep-mode': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller.hotspot20', 'hs-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_hotspot20_hs_profile_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_hotspot20_hs_profile': {
            'random_attribute_not_valid': 'tag',
            'access_network_asra': 'enable',
            'access_network_esr': 'enable',
            'access_network_internet': 'enable',
            'access_network_type': 'private-network',
            'access_network_uesa': 'enable',
            'anqp_domain_id': '9',
            'bss_transition': 'enable',
            'conn_cap': 'test_value_11',
            'deauth_request_timeout': '12',
            'dgaf': 'enable',
            'domain_name': 'test_value_14',
            'gas_comeback_delay': '15',
            'gas_fragmentation_limit': '16',
            'hessid': 'test_value_17',
            'ip_addr_type': 'test_value_18',
            'l2tif': 'enable',
            'nai_realm': 'test_value_20',
            'name': 'default_name_21',
            'network_auth': 'test_value_22',
            'oper_friendly_name': 'test_value_23',
            'osu_ssid': 'test_value_24',
            'pame_bi': 'disable',
            'proxy_arp': 'enable',
            'qos_map': 'test_value_27',
            'roaming_consortium': 'test_value_28',
            'venue_group': 'unspecified',
            'venue_name': 'test_value_30',
            'venue_type': 'unspecified',
            'wan_metrics': 'test_value_32',
            'wnm_sleep_mode': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_hs_profile.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    expected_data = {
        'access-network-asra': 'enable',
        'access-network-esr': 'enable',
        'access-network-internet': 'enable',
        'access-network-type': 'private-network',
        'access-network-uesa': 'enable',
        'anqp-domain-id': '9',
        'bss-transition': 'enable',
        'conn-cap': 'test_value_11',
        'deauth-request-timeout': '12',
        'dgaf': 'enable',
                'domain-name': 'test_value_14',
                'gas-comeback-delay': '15',
                'gas-fragmentation-limit': '16',
                'hessid': 'test_value_17',
                'ip-addr-type': 'test_value_18',
                'l2tif': 'enable',
                'nai-realm': 'test_value_20',
                'name': 'default_name_21',
                'network-auth': 'test_value_22',
                'oper-friendly-name': 'test_value_23',
                'osu-ssid': 'test_value_24',
                'pame-bi': 'disable',
                'proxy-arp': 'enable',
                'qos-map': 'test_value_27',
                'roaming-consortium': 'test_value_28',
                'venue-group': 'unspecified',
                'venue-name': 'test_value_30',
                'venue-type': 'unspecified',
                'wan-metrics': 'test_value_32',
                'wnm-sleep-mode': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller.hotspot20', 'hs-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
