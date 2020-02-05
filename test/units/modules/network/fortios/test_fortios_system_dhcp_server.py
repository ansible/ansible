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
    from ansible.modules.network.fortios import fortios_system_dhcp_server
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_system_dhcp_server.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_system_dhcp_server_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_dhcp_server': {
            'auto_configuration': 'disable',
            'conflicted_ip_timeout': '4',
            'ddns_auth': 'disable',
            'ddns_key': 'test_value_6',
            'ddns_keyname': 'test_value_7',
            'ddns_server_ip': 'test_value_8',
            'ddns_ttl': '9',
            'ddns_update': 'disable',
            'ddns_update_override': 'disable',
            'ddns_zone': 'test_value_12',
            'default_gateway': 'test_value_13',
            'dns_server1': 'test_value_14',
            'dns_server2': 'test_value_15',
            'dns_server3': 'test_value_16',
            'dns_service': 'local',
            'domain': 'test_value_18',
            'filename': 'test_value_19',
            'forticlient_on_net_status': 'disable',
            'id': '21',
            'interface': 'test_value_22',
            'ip_mode': 'range',
            'ipsec_lease_hold': '24',
            'lease_time': '25',
            'mac_acl_default_action': 'assign',
            'netmask': 'test_value_27',
            'next_server': 'test_value_28',
            'ntp_server1': 'test_value_29',
            'ntp_server2': 'test_value_30',
            'ntp_server3': 'test_value_31',
            'ntp_service': 'local',
            'server_type': 'regular',
            'status': 'disable',
            'timezone': '01',
            'timezone_option': 'disable',
            'vci_match': 'disable',
            'wifi_ac1': 'test_value_38',
            'wifi_ac2': 'test_value_39',
            'wifi_ac3': 'test_value_40',
            'wins_server1': 'test_value_41',
            'wins_server2': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp_server.fortios_system_dhcp(input_data, fos_instance)

    expected_data = {
        'auto-configuration': 'disable',
        'conflicted-ip-timeout': '4',
        'ddns-auth': 'disable',
        'ddns-key': 'test_value_6',
        'ddns-keyname': 'test_value_7',
        'ddns-server-ip': 'test_value_8',
        'ddns-ttl': '9',
        'ddns-update': 'disable',
        'ddns-update-override': 'disable',
        'ddns-zone': 'test_value_12',
        'default-gateway': 'test_value_13',
        'dns-server1': 'test_value_14',
        'dns-server2': 'test_value_15',
        'dns-server3': 'test_value_16',
        'dns-service': 'local',
        'domain': 'test_value_18',
        'filename': 'test_value_19',
        'forticlient-on-net-status': 'disable',
        'id': '21',
        'interface': 'test_value_22',
        'ip-mode': 'range',
        'ipsec-lease-hold': '24',
        'lease-time': '25',
        'mac-acl-default-action': 'assign',
        'netmask': 'test_value_27',
        'next-server': 'test_value_28',
        'ntp-server1': 'test_value_29',
        'ntp-server2': 'test_value_30',
        'ntp-server3': 'test_value_31',
        'ntp-service': 'local',
        'server-type': 'regular',
        'status': 'disable',
        'timezone': '01',
        'timezone-option': 'disable',
        'vci-match': 'disable',
        'wifi-ac1': 'test_value_38',
        'wifi-ac2': 'test_value_39',
        'wifi-ac3': 'test_value_40',
        'wins-server1': 'test_value_41',
        'wins-server2': 'test_value_42'
    }

    set_method_mock.assert_called_with('system.dhcp', 'server', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_dhcp_server_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_dhcp_server': {
            'auto_configuration': 'disable',
            'conflicted_ip_timeout': '4',
            'ddns_auth': 'disable',
            'ddns_key': 'test_value_6',
            'ddns_keyname': 'test_value_7',
            'ddns_server_ip': 'test_value_8',
            'ddns_ttl': '9',
            'ddns_update': 'disable',
            'ddns_update_override': 'disable',
            'ddns_zone': 'test_value_12',
            'default_gateway': 'test_value_13',
            'dns_server1': 'test_value_14',
            'dns_server2': 'test_value_15',
            'dns_server3': 'test_value_16',
            'dns_service': 'local',
            'domain': 'test_value_18',
            'filename': 'test_value_19',
            'forticlient_on_net_status': 'disable',
            'id': '21',
            'interface': 'test_value_22',
            'ip_mode': 'range',
            'ipsec_lease_hold': '24',
            'lease_time': '25',
            'mac_acl_default_action': 'assign',
            'netmask': 'test_value_27',
            'next_server': 'test_value_28',
            'ntp_server1': 'test_value_29',
            'ntp_server2': 'test_value_30',
            'ntp_server3': 'test_value_31',
            'ntp_service': 'local',
            'server_type': 'regular',
            'status': 'disable',
            'timezone': '01',
            'timezone_option': 'disable',
            'vci_match': 'disable',
            'wifi_ac1': 'test_value_38',
            'wifi_ac2': 'test_value_39',
            'wifi_ac3': 'test_value_40',
            'wins_server1': 'test_value_41',
            'wins_server2': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp_server.fortios_system_dhcp(input_data, fos_instance)

    expected_data = {
        'auto-configuration': 'disable',
        'conflicted-ip-timeout': '4',
        'ddns-auth': 'disable',
        'ddns-key': 'test_value_6',
        'ddns-keyname': 'test_value_7',
        'ddns-server-ip': 'test_value_8',
        'ddns-ttl': '9',
        'ddns-update': 'disable',
        'ddns-update-override': 'disable',
        'ddns-zone': 'test_value_12',
        'default-gateway': 'test_value_13',
        'dns-server1': 'test_value_14',
        'dns-server2': 'test_value_15',
        'dns-server3': 'test_value_16',
        'dns-service': 'local',
        'domain': 'test_value_18',
        'filename': 'test_value_19',
        'forticlient-on-net-status': 'disable',
        'id': '21',
        'interface': 'test_value_22',
        'ip-mode': 'range',
        'ipsec-lease-hold': '24',
        'lease-time': '25',
        'mac-acl-default-action': 'assign',
        'netmask': 'test_value_27',
        'next-server': 'test_value_28',
        'ntp-server1': 'test_value_29',
        'ntp-server2': 'test_value_30',
        'ntp-server3': 'test_value_31',
        'ntp-service': 'local',
        'server-type': 'regular',
        'status': 'disable',
        'timezone': '01',
        'timezone-option': 'disable',
        'vci-match': 'disable',
        'wifi-ac1': 'test_value_38',
        'wifi-ac2': 'test_value_39',
        'wifi-ac3': 'test_value_40',
        'wins-server1': 'test_value_41',
        'wins-server2': 'test_value_42'
    }

    set_method_mock.assert_called_with('system.dhcp', 'server', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_dhcp_server_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'system_dhcp_server': {
            'auto_configuration': 'disable',
            'conflicted_ip_timeout': '4',
            'ddns_auth': 'disable',
            'ddns_key': 'test_value_6',
            'ddns_keyname': 'test_value_7',
            'ddns_server_ip': 'test_value_8',
            'ddns_ttl': '9',
            'ddns_update': 'disable',
            'ddns_update_override': 'disable',
            'ddns_zone': 'test_value_12',
            'default_gateway': 'test_value_13',
            'dns_server1': 'test_value_14',
            'dns_server2': 'test_value_15',
            'dns_server3': 'test_value_16',
            'dns_service': 'local',
            'domain': 'test_value_18',
            'filename': 'test_value_19',
            'forticlient_on_net_status': 'disable',
            'id': '21',
            'interface': 'test_value_22',
            'ip_mode': 'range',
            'ipsec_lease_hold': '24',
            'lease_time': '25',
            'mac_acl_default_action': 'assign',
            'netmask': 'test_value_27',
            'next_server': 'test_value_28',
            'ntp_server1': 'test_value_29',
            'ntp_server2': 'test_value_30',
            'ntp_server3': 'test_value_31',
            'ntp_service': 'local',
            'server_type': 'regular',
            'status': 'disable',
            'timezone': '01',
            'timezone_option': 'disable',
            'vci_match': 'disable',
            'wifi_ac1': 'test_value_38',
            'wifi_ac2': 'test_value_39',
            'wifi_ac3': 'test_value_40',
            'wins_server1': 'test_value_41',
            'wins_server2': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp_server.fortios_system_dhcp(input_data, fos_instance)

    delete_method_mock.assert_called_with('system.dhcp', 'server', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_dhcp_server_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'system_dhcp_server': {
            'auto_configuration': 'disable',
            'conflicted_ip_timeout': '4',
            'ddns_auth': 'disable',
            'ddns_key': 'test_value_6',
            'ddns_keyname': 'test_value_7',
            'ddns_server_ip': 'test_value_8',
            'ddns_ttl': '9',
            'ddns_update': 'disable',
            'ddns_update_override': 'disable',
            'ddns_zone': 'test_value_12',
            'default_gateway': 'test_value_13',
            'dns_server1': 'test_value_14',
            'dns_server2': 'test_value_15',
            'dns_server3': 'test_value_16',
            'dns_service': 'local',
            'domain': 'test_value_18',
            'filename': 'test_value_19',
            'forticlient_on_net_status': 'disable',
            'id': '21',
            'interface': 'test_value_22',
            'ip_mode': 'range',
            'ipsec_lease_hold': '24',
            'lease_time': '25',
            'mac_acl_default_action': 'assign',
            'netmask': 'test_value_27',
            'next_server': 'test_value_28',
            'ntp_server1': 'test_value_29',
            'ntp_server2': 'test_value_30',
            'ntp_server3': 'test_value_31',
            'ntp_service': 'local',
            'server_type': 'regular',
            'status': 'disable',
            'timezone': '01',
            'timezone_option': 'disable',
            'vci_match': 'disable',
            'wifi_ac1': 'test_value_38',
            'wifi_ac2': 'test_value_39',
            'wifi_ac3': 'test_value_40',
            'wins_server1': 'test_value_41',
            'wins_server2': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp_server.fortios_system_dhcp(input_data, fos_instance)

    delete_method_mock.assert_called_with('system.dhcp', 'server', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_dhcp_server_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_dhcp_server': {
            'auto_configuration': 'disable',
            'conflicted_ip_timeout': '4',
            'ddns_auth': 'disable',
            'ddns_key': 'test_value_6',
            'ddns_keyname': 'test_value_7',
            'ddns_server_ip': 'test_value_8',
            'ddns_ttl': '9',
            'ddns_update': 'disable',
            'ddns_update_override': 'disable',
            'ddns_zone': 'test_value_12',
            'default_gateway': 'test_value_13',
            'dns_server1': 'test_value_14',
            'dns_server2': 'test_value_15',
            'dns_server3': 'test_value_16',
            'dns_service': 'local',
            'domain': 'test_value_18',
            'filename': 'test_value_19',
            'forticlient_on_net_status': 'disable',
            'id': '21',
            'interface': 'test_value_22',
            'ip_mode': 'range',
            'ipsec_lease_hold': '24',
            'lease_time': '25',
            'mac_acl_default_action': 'assign',
            'netmask': 'test_value_27',
            'next_server': 'test_value_28',
            'ntp_server1': 'test_value_29',
            'ntp_server2': 'test_value_30',
            'ntp_server3': 'test_value_31',
            'ntp_service': 'local',
            'server_type': 'regular',
            'status': 'disable',
            'timezone': '01',
            'timezone_option': 'disable',
            'vci_match': 'disable',
            'wifi_ac1': 'test_value_38',
            'wifi_ac2': 'test_value_39',
            'wifi_ac3': 'test_value_40',
            'wins_server1': 'test_value_41',
            'wins_server2': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp_server.fortios_system_dhcp(input_data, fos_instance)

    expected_data = {
        'auto-configuration': 'disable',
        'conflicted-ip-timeout': '4',
        'ddns-auth': 'disable',
        'ddns-key': 'test_value_6',
        'ddns-keyname': 'test_value_7',
        'ddns-server-ip': 'test_value_8',
        'ddns-ttl': '9',
        'ddns-update': 'disable',
        'ddns-update-override': 'disable',
        'ddns-zone': 'test_value_12',
        'default-gateway': 'test_value_13',
        'dns-server1': 'test_value_14',
        'dns-server2': 'test_value_15',
        'dns-server3': 'test_value_16',
        'dns-service': 'local',
        'domain': 'test_value_18',
        'filename': 'test_value_19',
        'forticlient-on-net-status': 'disable',
        'id': '21',
        'interface': 'test_value_22',
        'ip-mode': 'range',
        'ipsec-lease-hold': '24',
        'lease-time': '25',
        'mac-acl-default-action': 'assign',
        'netmask': 'test_value_27',
        'next-server': 'test_value_28',
        'ntp-server1': 'test_value_29',
        'ntp-server2': 'test_value_30',
        'ntp-server3': 'test_value_31',
        'ntp-service': 'local',
        'server-type': 'regular',
        'status': 'disable',
        'timezone': '01',
        'timezone-option': 'disable',
        'vci-match': 'disable',
        'wifi-ac1': 'test_value_38',
        'wifi-ac2': 'test_value_39',
        'wifi-ac3': 'test_value_40',
        'wins-server1': 'test_value_41',
        'wins-server2': 'test_value_42'
    }

    set_method_mock.assert_called_with('system.dhcp', 'server', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_system_dhcp_server_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_dhcp_server': {
            'random_attribute_not_valid': 'tag',
            'auto_configuration': 'disable',
            'conflicted_ip_timeout': '4',
            'ddns_auth': 'disable',
            'ddns_key': 'test_value_6',
            'ddns_keyname': 'test_value_7',
            'ddns_server_ip': 'test_value_8',
            'ddns_ttl': '9',
            'ddns_update': 'disable',
            'ddns_update_override': 'disable',
            'ddns_zone': 'test_value_12',
            'default_gateway': 'test_value_13',
            'dns_server1': 'test_value_14',
            'dns_server2': 'test_value_15',
            'dns_server3': 'test_value_16',
            'dns_service': 'local',
            'domain': 'test_value_18',
            'filename': 'test_value_19',
            'forticlient_on_net_status': 'disable',
            'id': '21',
            'interface': 'test_value_22',
            'ip_mode': 'range',
            'ipsec_lease_hold': '24',
            'lease_time': '25',
            'mac_acl_default_action': 'assign',
            'netmask': 'test_value_27',
            'next_server': 'test_value_28',
            'ntp_server1': 'test_value_29',
            'ntp_server2': 'test_value_30',
            'ntp_server3': 'test_value_31',
            'ntp_service': 'local',
            'server_type': 'regular',
            'status': 'disable',
            'timezone': '01',
            'timezone_option': 'disable',
            'vci_match': 'disable',
            'wifi_ac1': 'test_value_38',
            'wifi_ac2': 'test_value_39',
            'wifi_ac3': 'test_value_40',
            'wins_server1': 'test_value_41',
            'wins_server2': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp_server.fortios_system_dhcp(input_data, fos_instance)

    expected_data = {
        'auto-configuration': 'disable',
        'conflicted-ip-timeout': '4',
        'ddns-auth': 'disable',
        'ddns-key': 'test_value_6',
        'ddns-keyname': 'test_value_7',
        'ddns-server-ip': 'test_value_8',
        'ddns-ttl': '9',
        'ddns-update': 'disable',
        'ddns-update-override': 'disable',
        'ddns-zone': 'test_value_12',
        'default-gateway': 'test_value_13',
        'dns-server1': 'test_value_14',
        'dns-server2': 'test_value_15',
        'dns-server3': 'test_value_16',
        'dns-service': 'local',
        'domain': 'test_value_18',
        'filename': 'test_value_19',
        'forticlient-on-net-status': 'disable',
        'id': '21',
        'interface': 'test_value_22',
        'ip-mode': 'range',
        'ipsec-lease-hold': '24',
        'lease-time': '25',
        'mac-acl-default-action': 'assign',
        'netmask': 'test_value_27',
        'next-server': 'test_value_28',
        'ntp-server1': 'test_value_29',
        'ntp-server2': 'test_value_30',
        'ntp-server3': 'test_value_31',
        'ntp-service': 'local',
        'server-type': 'regular',
        'status': 'disable',
        'timezone': '01',
        'timezone-option': 'disable',
        'vci-match': 'disable',
        'wifi-ac1': 'test_value_38',
        'wifi-ac2': 'test_value_39',
        'wifi-ac3': 'test_value_40',
        'wins-server1': 'test_value_41',
        'wins-server2': 'test_value_42'
    }

    set_method_mock.assert_called_with('system.dhcp', 'server', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
