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
    from ansible.modules.network.fortios import fortios_wireless_controller_global
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_global.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_global_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_global': {
            'ap_log_server': 'enable',
            'ap_log_server_ip': 'test_value_4',
            'ap_log_server_port': '5',
            'control_message_offload': 'ebp-frame',
            'data_ethernet_II': 'enable',
            'discovery_mc_addr': 'test_value_8',
            'fiapp_eth_type': '9',
            'image_download': 'enable',
            'ipsec_base_ip': 'test_value_11',
            'link_aggregation': 'enable',
            'location': 'test_value_13',
            'max_clients': '14',
            'max_retransmit': '15',
            'mesh_eth_type': '16',
            'name': 'default_name_17',
            'rogue_scan_mac_adjacency': '18',
            'wtp_share': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_global.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ap-log-server': 'enable',
        'ap-log-server-ip': 'test_value_4',
        'ap-log-server-port': '5',
        'control-message-offload': 'ebp-frame',
        'data-ethernet-II': 'enable',
        'discovery-mc-addr': 'test_value_8',
        'fiapp-eth-type': '9',
        'image-download': 'enable',
        'ipsec-base-ip': 'test_value_11',
        'link-aggregation': 'enable',
        'location': 'test_value_13',
        'max-clients': '14',
        'max-retransmit': '15',
        'mesh-eth-type': '16',
        'name': 'default_name_17',
                'rogue-scan-mac-adjacency': '18',
                'wtp-share': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_global_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_global': {
            'ap_log_server': 'enable',
            'ap_log_server_ip': 'test_value_4',
            'ap_log_server_port': '5',
            'control_message_offload': 'ebp-frame',
            'data_ethernet_II': 'enable',
            'discovery_mc_addr': 'test_value_8',
            'fiapp_eth_type': '9',
            'image_download': 'enable',
            'ipsec_base_ip': 'test_value_11',
            'link_aggregation': 'enable',
            'location': 'test_value_13',
            'max_clients': '14',
            'max_retransmit': '15',
            'mesh_eth_type': '16',
            'name': 'default_name_17',
            'rogue_scan_mac_adjacency': '18',
            'wtp_share': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_global.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ap-log-server': 'enable',
        'ap-log-server-ip': 'test_value_4',
        'ap-log-server-port': '5',
        'control-message-offload': 'ebp-frame',
        'data-ethernet-II': 'enable',
        'discovery-mc-addr': 'test_value_8',
        'fiapp-eth-type': '9',
        'image-download': 'enable',
        'ipsec-base-ip': 'test_value_11',
        'link-aggregation': 'enable',
        'location': 'test_value_13',
        'max-clients': '14',
        'max-retransmit': '15',
        'mesh-eth-type': '16',
        'name': 'default_name_17',
                'rogue-scan-mac-adjacency': '18',
                'wtp-share': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_global_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_global': {
            'ap_log_server': 'enable',
            'ap_log_server_ip': 'test_value_4',
            'ap_log_server_port': '5',
            'control_message_offload': 'ebp-frame',
            'data_ethernet_II': 'enable',
            'discovery_mc_addr': 'test_value_8',
            'fiapp_eth_type': '9',
            'image_download': 'enable',
            'ipsec_base_ip': 'test_value_11',
            'link_aggregation': 'enable',
            'location': 'test_value_13',
            'max_clients': '14',
            'max_retransmit': '15',
            'mesh_eth_type': '16',
            'name': 'default_name_17',
            'rogue_scan_mac_adjacency': '18',
            'wtp_share': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_global.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ap-log-server': 'enable',
        'ap-log-server-ip': 'test_value_4',
        'ap-log-server-port': '5',
        'control-message-offload': 'ebp-frame',
        'data-ethernet-II': 'enable',
        'discovery-mc-addr': 'test_value_8',
        'fiapp-eth-type': '9',
        'image-download': 'enable',
        'ipsec-base-ip': 'test_value_11',
        'link-aggregation': 'enable',
        'location': 'test_value_13',
        'max-clients': '14',
        'max-retransmit': '15',
        'mesh-eth-type': '16',
        'name': 'default_name_17',
                'rogue-scan-mac-adjacency': '18',
                'wtp-share': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_global_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_global': {
            'random_attribute_not_valid': 'tag',
            'ap_log_server': 'enable',
            'ap_log_server_ip': 'test_value_4',
            'ap_log_server_port': '5',
            'control_message_offload': 'ebp-frame',
            'data_ethernet_II': 'enable',
            'discovery_mc_addr': 'test_value_8',
            'fiapp_eth_type': '9',
            'image_download': 'enable',
            'ipsec_base_ip': 'test_value_11',
            'link_aggregation': 'enable',
            'location': 'test_value_13',
            'max_clients': '14',
            'max_retransmit': '15',
            'mesh_eth_type': '16',
            'name': 'default_name_17',
            'rogue_scan_mac_adjacency': '18',
            'wtp_share': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_global.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ap-log-server': 'enable',
        'ap-log-server-ip': 'test_value_4',
        'ap-log-server-port': '5',
        'control-message-offload': 'ebp-frame',
        'data-ethernet-II': 'enable',
        'discovery-mc-addr': 'test_value_8',
        'fiapp-eth-type': '9',
        'image-download': 'enable',
        'ipsec-base-ip': 'test_value_11',
        'link-aggregation': 'enable',
        'location': 'test_value_13',
        'max-clients': '14',
        'max-retransmit': '15',
        'mesh-eth-type': '16',
        'name': 'default_name_17',
                'rogue-scan-mac-adjacency': '18',
                'wtp-share': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
