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
    from ansible.modules.network.fortios import fortios_wireless_controller_wtp
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_wtp.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_wtp_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wtp': {
            'admin': 'discovered',
            'allowaccess': 'telnet',
            'bonjour_profile': 'test_value_5',
            'coordinate_enable': 'enable',
            'coordinate_latitude': 'test_value_7',
            'coordinate_longitude': 'test_value_8',
            'coordinate_x': 'test_value_9',
            'coordinate_y': 'test_value_10',
            'image_download': 'enable',
            'index': '12',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'location': 'test_value_15',
            'login_passwd': 'test_value_16',
            'login_passwd_change': 'yes',
            'mesh_bridge_enable': 'default',
            'name': 'default_name_19',
            'override_allowaccess': 'enable',
            'override_ip_fragment': 'enable',
            'override_lan': 'enable',
            'override_led_state': 'enable',
            'override_login_passwd_change': 'enable',
            'override_split_tunnel': 'enable',
            'override_wan_port_mode': 'enable',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '29',
            'tun_mtu_uplink': '30',
            'wan_port_mode': 'wan-lan',
            'wtp_id': 'test_value_32',
            'wtp_mode': 'normal',
            'wtp_profile': 'test_value_34'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'admin': 'discovered',
        'allowaccess': 'telnet',
        'bonjour-profile': 'test_value_5',
        'coordinate-enable': 'enable',
        'coordinate-latitude': 'test_value_7',
        'coordinate-longitude': 'test_value_8',
        'coordinate-x': 'test_value_9',
        'coordinate-y': 'test_value_10',
        'image-download': 'enable',
        'index': '12',
        'ip-fragment-preventing': 'tcp-mss-adjust',
        'led-state': 'enable',
        'location': 'test_value_15',
        'login-passwd': 'test_value_16',
        'login-passwd-change': 'yes',
        'mesh-bridge-enable': 'default',
        'name': 'default_name_19',
                'override-allowaccess': 'enable',
                'override-ip-fragment': 'enable',
                'override-lan': 'enable',
                'override-led-state': 'enable',
                'override-login-passwd-change': 'enable',
                'override-split-tunnel': 'enable',
                'override-wan-port-mode': 'enable',
                'split-tunneling-acl-local-ap-subnet': 'enable',
                'split-tunneling-acl-path': 'tunnel',
                'tun-mtu-downlink': '29',
                'tun-mtu-uplink': '30',
                'wan-port-mode': 'wan-lan',
                'wtp-id': 'test_value_32',
                'wtp-mode': 'normal',
                'wtp-profile': 'test_value_34'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wtp', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_wtp_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wtp': {
            'admin': 'discovered',
            'allowaccess': 'telnet',
            'bonjour_profile': 'test_value_5',
            'coordinate_enable': 'enable',
            'coordinate_latitude': 'test_value_7',
            'coordinate_longitude': 'test_value_8',
            'coordinate_x': 'test_value_9',
            'coordinate_y': 'test_value_10',
            'image_download': 'enable',
            'index': '12',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'location': 'test_value_15',
            'login_passwd': 'test_value_16',
            'login_passwd_change': 'yes',
            'mesh_bridge_enable': 'default',
            'name': 'default_name_19',
            'override_allowaccess': 'enable',
            'override_ip_fragment': 'enable',
            'override_lan': 'enable',
            'override_led_state': 'enable',
            'override_login_passwd_change': 'enable',
            'override_split_tunnel': 'enable',
            'override_wan_port_mode': 'enable',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '29',
            'tun_mtu_uplink': '30',
            'wan_port_mode': 'wan-lan',
            'wtp_id': 'test_value_32',
            'wtp_mode': 'normal',
            'wtp_profile': 'test_value_34'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'admin': 'discovered',
        'allowaccess': 'telnet',
        'bonjour-profile': 'test_value_5',
        'coordinate-enable': 'enable',
        'coordinate-latitude': 'test_value_7',
        'coordinate-longitude': 'test_value_8',
        'coordinate-x': 'test_value_9',
        'coordinate-y': 'test_value_10',
        'image-download': 'enable',
        'index': '12',
        'ip-fragment-preventing': 'tcp-mss-adjust',
        'led-state': 'enable',
        'location': 'test_value_15',
        'login-passwd': 'test_value_16',
        'login-passwd-change': 'yes',
        'mesh-bridge-enable': 'default',
        'name': 'default_name_19',
                'override-allowaccess': 'enable',
                'override-ip-fragment': 'enable',
                'override-lan': 'enable',
                'override-led-state': 'enable',
                'override-login-passwd-change': 'enable',
                'override-split-tunnel': 'enable',
                'override-wan-port-mode': 'enable',
                'split-tunneling-acl-local-ap-subnet': 'enable',
                'split-tunneling-acl-path': 'tunnel',
                'tun-mtu-downlink': '29',
                'tun-mtu-uplink': '30',
                'wan-port-mode': 'wan-lan',
                'wtp-id': 'test_value_32',
                'wtp-mode': 'normal',
                'wtp-profile': 'test_value_34'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wtp', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_wtp_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_wtp': {
            'admin': 'discovered',
            'allowaccess': 'telnet',
            'bonjour_profile': 'test_value_5',
            'coordinate_enable': 'enable',
            'coordinate_latitude': 'test_value_7',
            'coordinate_longitude': 'test_value_8',
            'coordinate_x': 'test_value_9',
            'coordinate_y': 'test_value_10',
            'image_download': 'enable',
            'index': '12',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'location': 'test_value_15',
            'login_passwd': 'test_value_16',
            'login_passwd_change': 'yes',
            'mesh_bridge_enable': 'default',
            'name': 'default_name_19',
            'override_allowaccess': 'enable',
            'override_ip_fragment': 'enable',
            'override_lan': 'enable',
            'override_led_state': 'enable',
            'override_login_passwd_change': 'enable',
            'override_split_tunnel': 'enable',
            'override_wan_port_mode': 'enable',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '29',
            'tun_mtu_uplink': '30',
            'wan_port_mode': 'wan-lan',
            'wtp_id': 'test_value_32',
            'wtp_mode': 'normal',
            'wtp_profile': 'test_value_34'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp.fortios_wireless_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller', 'wtp', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_wtp_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_wtp': {
            'admin': 'discovered',
            'allowaccess': 'telnet',
            'bonjour_profile': 'test_value_5',
            'coordinate_enable': 'enable',
            'coordinate_latitude': 'test_value_7',
            'coordinate_longitude': 'test_value_8',
            'coordinate_x': 'test_value_9',
            'coordinate_y': 'test_value_10',
            'image_download': 'enable',
            'index': '12',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'location': 'test_value_15',
            'login_passwd': 'test_value_16',
            'login_passwd_change': 'yes',
            'mesh_bridge_enable': 'default',
            'name': 'default_name_19',
            'override_allowaccess': 'enable',
            'override_ip_fragment': 'enable',
            'override_lan': 'enable',
            'override_led_state': 'enable',
            'override_login_passwd_change': 'enable',
            'override_split_tunnel': 'enable',
            'override_wan_port_mode': 'enable',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '29',
            'tun_mtu_uplink': '30',
            'wan_port_mode': 'wan-lan',
            'wtp_id': 'test_value_32',
            'wtp_mode': 'normal',
            'wtp_profile': 'test_value_34'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp.fortios_wireless_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller', 'wtp', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_wtp_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wtp': {
            'admin': 'discovered',
            'allowaccess': 'telnet',
            'bonjour_profile': 'test_value_5',
            'coordinate_enable': 'enable',
            'coordinate_latitude': 'test_value_7',
            'coordinate_longitude': 'test_value_8',
            'coordinate_x': 'test_value_9',
            'coordinate_y': 'test_value_10',
            'image_download': 'enable',
            'index': '12',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'location': 'test_value_15',
            'login_passwd': 'test_value_16',
            'login_passwd_change': 'yes',
            'mesh_bridge_enable': 'default',
            'name': 'default_name_19',
            'override_allowaccess': 'enable',
            'override_ip_fragment': 'enable',
            'override_lan': 'enable',
            'override_led_state': 'enable',
            'override_login_passwd_change': 'enable',
            'override_split_tunnel': 'enable',
            'override_wan_port_mode': 'enable',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '29',
            'tun_mtu_uplink': '30',
            'wan_port_mode': 'wan-lan',
            'wtp_id': 'test_value_32',
            'wtp_mode': 'normal',
            'wtp_profile': 'test_value_34'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'admin': 'discovered',
        'allowaccess': 'telnet',
        'bonjour-profile': 'test_value_5',
        'coordinate-enable': 'enable',
        'coordinate-latitude': 'test_value_7',
        'coordinate-longitude': 'test_value_8',
        'coordinate-x': 'test_value_9',
        'coordinate-y': 'test_value_10',
        'image-download': 'enable',
        'index': '12',
        'ip-fragment-preventing': 'tcp-mss-adjust',
        'led-state': 'enable',
        'location': 'test_value_15',
        'login-passwd': 'test_value_16',
        'login-passwd-change': 'yes',
        'mesh-bridge-enable': 'default',
        'name': 'default_name_19',
                'override-allowaccess': 'enable',
                'override-ip-fragment': 'enable',
                'override-lan': 'enable',
                'override-led-state': 'enable',
                'override-login-passwd-change': 'enable',
                'override-split-tunnel': 'enable',
                'override-wan-port-mode': 'enable',
                'split-tunneling-acl-local-ap-subnet': 'enable',
                'split-tunneling-acl-path': 'tunnel',
                'tun-mtu-downlink': '29',
                'tun-mtu-uplink': '30',
                'wan-port-mode': 'wan-lan',
                'wtp-id': 'test_value_32',
                'wtp-mode': 'normal',
                'wtp-profile': 'test_value_34'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wtp', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_wtp_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wtp': {
            'random_attribute_not_valid': 'tag',
            'admin': 'discovered',
            'allowaccess': 'telnet',
            'bonjour_profile': 'test_value_5',
            'coordinate_enable': 'enable',
            'coordinate_latitude': 'test_value_7',
            'coordinate_longitude': 'test_value_8',
            'coordinate_x': 'test_value_9',
            'coordinate_y': 'test_value_10',
            'image_download': 'enable',
            'index': '12',
            'ip_fragment_preventing': 'tcp-mss-adjust',
            'led_state': 'enable',
            'location': 'test_value_15',
            'login_passwd': 'test_value_16',
            'login_passwd_change': 'yes',
            'mesh_bridge_enable': 'default',
            'name': 'default_name_19',
            'override_allowaccess': 'enable',
            'override_ip_fragment': 'enable',
            'override_lan': 'enable',
            'override_led_state': 'enable',
            'override_login_passwd_change': 'enable',
            'override_split_tunnel': 'enable',
            'override_wan_port_mode': 'enable',
            'split_tunneling_acl_local_ap_subnet': 'enable',
            'split_tunneling_acl_path': 'tunnel',
            'tun_mtu_downlink': '29',
            'tun_mtu_uplink': '30',
            'wan_port_mode': 'wan-lan',
            'wtp_id': 'test_value_32',
            'wtp_mode': 'normal',
            'wtp_profile': 'test_value_34'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wtp.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'admin': 'discovered',
        'allowaccess': 'telnet',
        'bonjour-profile': 'test_value_5',
        'coordinate-enable': 'enable',
        'coordinate-latitude': 'test_value_7',
        'coordinate-longitude': 'test_value_8',
        'coordinate-x': 'test_value_9',
        'coordinate-y': 'test_value_10',
        'image-download': 'enable',
        'index': '12',
        'ip-fragment-preventing': 'tcp-mss-adjust',
        'led-state': 'enable',
        'location': 'test_value_15',
        'login-passwd': 'test_value_16',
        'login-passwd-change': 'yes',
        'mesh-bridge-enable': 'default',
        'name': 'default_name_19',
                'override-allowaccess': 'enable',
                'override-ip-fragment': 'enable',
                'override-lan': 'enable',
                'override-led-state': 'enable',
                'override-login-passwd-change': 'enable',
                'override-split-tunnel': 'enable',
                'override-wan-port-mode': 'enable',
                'split-tunneling-acl-local-ap-subnet': 'enable',
                'split-tunneling-acl-path': 'tunnel',
                'tun-mtu-downlink': '29',
                'tun-mtu-uplink': '30',
                'wan-port-mode': 'wan-lan',
                'wtp-id': 'test_value_32',
                'wtp-mode': 'normal',
                'wtp-profile': 'test_value_34'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wtp', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
