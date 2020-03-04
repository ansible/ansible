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
    from ansible.modules.network.fortios import fortios_wireless_controller_wtp_profile
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_wtp_profile.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_wtp_profile_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wtp_profile': {
            'allowaccess': 'telnet',
            'ap_country': 'NA',
            'ble_profile': 'test_value_5',
            'comment': 'Comment.',
            'control_message_offload': 'ebp-frame',
            'dtls_in_kernel': 'enable',
            'dtls_policy': 'clear-text',
            'energy_efficient_ethernet': 'enable',
            'ext_info_enable': 'enable',
            'handoff_roaming': 'enable',
            'handoff_rssi': '13',
            'handoff_sta_thresh': '14',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'lldp': 'enable',
            'login_passwd': 'test_value_18',
            'login_passwd_change': 'yes',
            'max_clients': '20',
            'name': 'default_name_21',
            'poe_mode': 'auto',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '25',
            'tun_mtu_uplink': '26',
            'wan_port_mode': 'wan-lan'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'allowaccess': 'telnet',
        'ap-country': 'NA',
        'ble-profile': 'test_value_5',
        'comment': 'Comment.',
        'control-message-offload': 'ebp-frame',
        'dtls-in-kernel': 'enable',
        'dtls-policy': 'clear-text',
        'energy-efficient-ethernet': 'enable',
        'ext-info-enable': 'enable',
        'handoff-roaming': 'enable',
        'handoff-rssi': '13',
        'handoff-sta-thresh': '14',
        'ip-fragment-preventing': 'tcp-mss-adjust',
        'led-state': 'enable',
        'lldp': 'enable',
                'login-passwd': 'test_value_18',
                'login-passwd-change': 'yes',
                'max-clients': '20',
                'name': 'default_name_21',
                'poe-mode': 'auto',
                'split-tunneling-acl-local-ap-subnet': 'enable',
                'split-tunneling-acl-path': 'tunnel',
                'tun-mtu-downlink': '25',
                'tun-mtu-uplink': '26',
                'wan-port-mode': 'wan-lan'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wtp-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_wtp_profile_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wtp_profile': {
            'allowaccess': 'telnet',
            'ap_country': 'NA',
            'ble_profile': 'test_value_5',
            'comment': 'Comment.',
            'control_message_offload': 'ebp-frame',
            'dtls_in_kernel': 'enable',
            'dtls_policy': 'clear-text',
            'energy_efficient_ethernet': 'enable',
            'ext_info_enable': 'enable',
            'handoff_roaming': 'enable',
            'handoff_rssi': '13',
            'handoff_sta_thresh': '14',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'lldp': 'enable',
            'login_passwd': 'test_value_18',
            'login_passwd_change': 'yes',
            'max_clients': '20',
            'name': 'default_name_21',
            'poe_mode': 'auto',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '25',
            'tun_mtu_uplink': '26',
            'wan_port_mode': 'wan-lan'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'allowaccess': 'telnet',
        'ap-country': 'NA',
        'ble-profile': 'test_value_5',
        'comment': 'Comment.',
        'control-message-offload': 'ebp-frame',
        'dtls-in-kernel': 'enable',
        'dtls-policy': 'clear-text',
        'energy-efficient-ethernet': 'enable',
        'ext-info-enable': 'enable',
        'handoff-roaming': 'enable',
        'handoff-rssi': '13',
        'handoff-sta-thresh': '14',
        'ip-fragment-preventing': 'tcp-mss-adjust',
        'led-state': 'enable',
        'lldp': 'enable',
                'login-passwd': 'test_value_18',
                'login-passwd-change': 'yes',
                'max-clients': '20',
                'name': 'default_name_21',
                'poe-mode': 'auto',
                'split-tunneling-acl-local-ap-subnet': 'enable',
                'split-tunneling-acl-path': 'tunnel',
                'tun-mtu-downlink': '25',
                'tun-mtu-uplink': '26',
                'wan-port-mode': 'wan-lan'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wtp-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_wtp_profile_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_wtp_profile': {
            'allowaccess': 'telnet',
            'ap_country': 'NA',
            'ble_profile': 'test_value_5',
            'comment': 'Comment.',
            'control_message_offload': 'ebp-frame',
            'dtls_in_kernel': 'enable',
            'dtls_policy': 'clear-text',
            'energy_efficient_ethernet': 'enable',
            'ext_info_enable': 'enable',
            'handoff_roaming': 'enable',
            'handoff_rssi': '13',
            'handoff_sta_thresh': '14',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'lldp': 'enable',
            'login_passwd': 'test_value_18',
            'login_passwd_change': 'yes',
            'max_clients': '20',
            'name': 'default_name_21',
            'poe_mode': 'auto',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '25',
            'tun_mtu_uplink': '26',
            'wan_port_mode': 'wan-lan'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp_profile.fortios_wireless_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller', 'wtp-profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_wtp_profile_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_wtp_profile': {
            'allowaccess': 'telnet',
            'ap_country': 'NA',
            'ble_profile': 'test_value_5',
            'comment': 'Comment.',
            'control_message_offload': 'ebp-frame',
            'dtls_in_kernel': 'enable',
            'dtls_policy': 'clear-text',
            'energy_efficient_ethernet': 'enable',
            'ext_info_enable': 'enable',
            'handoff_roaming': 'enable',
            'handoff_rssi': '13',
            'handoff_sta_thresh': '14',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'lldp': 'enable',
            'login_passwd': 'test_value_18',
            'login_passwd_change': 'yes',
            'max_clients': '20',
            'name': 'default_name_21',
            'poe_mode': 'auto',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '25',
            'tun_mtu_uplink': '26',
            'wan_port_mode': 'wan-lan'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp_profile.fortios_wireless_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller', 'wtp-profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_wtp_profile_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wtp_profile': {
            'allowaccess': 'telnet',
            'ap_country': 'NA',
            'ble_profile': 'test_value_5',
            'comment': 'Comment.',
            'control_message_offload': 'ebp-frame',
            'dtls_in_kernel': 'enable',
            'dtls_policy': 'clear-text',
            'energy_efficient_ethernet': 'enable',
            'ext_info_enable': 'enable',
            'handoff_roaming': 'enable',
            'handoff_rssi': '13',
            'handoff_sta_thresh': '14',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'lldp': 'enable',
            'login_passwd': 'test_value_18',
            'login_passwd_change': 'yes',
            'max_clients': '20',
            'name': 'default_name_21',
            'poe_mode': 'auto',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '25',
            'tun_mtu_uplink': '26',
            'wan_port_mode': 'wan-lan'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'allowaccess': 'telnet',
        'ap-country': 'NA',
        'ble-profile': 'test_value_5',
        'comment': 'Comment.',
        'control-message-offload': 'ebp-frame',
        'dtls-in-kernel': 'enable',
        'dtls-policy': 'clear-text',
        'energy-efficient-ethernet': 'enable',
        'ext-info-enable': 'enable',
        'handoff-roaming': 'enable',
        'handoff-rssi': '13',
        'handoff-sta-thresh': '14',
        'ip-fragment-preventing': 'tcp-mss-adjust',
        'led-state': 'enable',
        'lldp': 'enable',
                'login-passwd': 'test_value_18',
                'login-passwd-change': 'yes',
                'max-clients': '20',
                'name': 'default_name_21',
                'poe-mode': 'auto',
                'split-tunneling-acl-local-ap-subnet': 'enable',
                'split-tunneling-acl-path': 'tunnel',
                'tun-mtu-downlink': '25',
                'tun-mtu-uplink': '26',
                'wan-port-mode': 'wan-lan'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wtp-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_wtp_profile_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wtp_profile': {
            'random_attribute_not_valid': 'tag',
            'allowaccess': 'telnet',
            'ap_country': 'NA',
            'ble_profile': 'test_value_5',
            'comment': 'Comment.',
            'control_message_offload': 'ebp-frame',
            'dtls_in_kernel': 'enable',
            'dtls_policy': 'clear-text',
            'energy_efficient_ethernet': 'enable',
            'ext_info_enable': 'enable',
            'handoff_roaming': 'enable',
            'handoff_rssi': '13',
            'handoff_sta_thresh': '14',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'lldp': 'enable',
            'login_passwd': 'test_value_18',
            'login_passwd_change': 'yes',
            'max_clients': '20',
            'name': 'default_name_21',
            'poe_mode': 'auto',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '25',
            'tun_mtu_uplink': '26',
            'wan_port_mode': 'wan-lan'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'allowaccess': 'telnet',
        'ap-country': 'NA',
        'ble-profile': 'test_value_5',
        'comment': 'Comment.',
        'control-message-offload': 'ebp-frame',
        'dtls-in-kernel': 'enable',
        'dtls-policy': 'clear-text',
        'energy-efficient-ethernet': 'enable',
        'ext-info-enable': 'enable',
        'handoff-roaming': 'enable',
        'handoff-rssi': '13',
        'handoff-sta-thresh': '14',
        'ip-fragment-preventing': 'tcp-mss-adjust',
        'led-state': 'enable',
        'lldp': 'enable',
                'login-passwd': 'test_value_18',
                'login-passwd-change': 'yes',
                'max-clients': '20',
                'name': 'default_name_21',
                'poe-mode': 'auto',
                'split-tunneling-acl-local-ap-subnet': 'enable',
                'split-tunneling-acl-path': 'tunnel',
                'tun-mtu-downlink': '25',
                'tun-mtu-uplink': '26',
                'wan-port-mode': 'wan-lan'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wtp-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
