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
    from ansible.modules.network.fortios import fortios_wireless_controller_ble_profile
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_ble_profile.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_ble_profile_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_ble_profile': {
            'advertising': 'ibeacon',
            'beacon_interval': '4',
            'ble_scanning': 'enable',
            'comment': 'Comment.',
            'eddystone_instance': 'test_value_7',
            'eddystone_namespace': 'test_value_8',
            'eddystone_url': 'test_value_9',
            'eddystone_url_encode_hex': 'test_value_10',
            'ibeacon_uuid': 'test_value_11',
            'major_id': '12',
            'minor_id': '13',
            'name': 'default_name_14',
            'txpower': '0'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_ble_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'advertising': 'ibeacon',
        'beacon-interval': '4',
        'ble-scanning': 'enable',
        'comment': 'Comment.',
        'eddystone-instance': 'test_value_7',
        'eddystone-namespace': 'test_value_8',
        'eddystone-url': 'test_value_9',
        'eddystone-url-encode-hex': 'test_value_10',
        'ibeacon-uuid': 'test_value_11',
        'major-id': '12',
        'minor-id': '13',
        'name': 'default_name_14',
                'txpower': '0'
    }

    set_method_mock.assert_called_with('wireless-controller', 'ble-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_ble_profile_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_ble_profile': {
            'advertising': 'ibeacon',
            'beacon_interval': '4',
            'ble_scanning': 'enable',
            'comment': 'Comment.',
            'eddystone_instance': 'test_value_7',
            'eddystone_namespace': 'test_value_8',
            'eddystone_url': 'test_value_9',
            'eddystone_url_encode_hex': 'test_value_10',
            'ibeacon_uuid': 'test_value_11',
            'major_id': '12',
            'minor_id': '13',
            'name': 'default_name_14',
            'txpower': '0'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_ble_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'advertising': 'ibeacon',
        'beacon-interval': '4',
        'ble-scanning': 'enable',
        'comment': 'Comment.',
        'eddystone-instance': 'test_value_7',
        'eddystone-namespace': 'test_value_8',
        'eddystone-url': 'test_value_9',
        'eddystone-url-encode-hex': 'test_value_10',
        'ibeacon-uuid': 'test_value_11',
        'major-id': '12',
        'minor-id': '13',
        'name': 'default_name_14',
                'txpower': '0'
    }

    set_method_mock.assert_called_with('wireless-controller', 'ble-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_ble_profile_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_ble_profile': {
            'advertising': 'ibeacon',
            'beacon_interval': '4',
            'ble_scanning': 'enable',
            'comment': 'Comment.',
            'eddystone_instance': 'test_value_7',
            'eddystone_namespace': 'test_value_8',
            'eddystone_url': 'test_value_9',
            'eddystone_url_encode_hex': 'test_value_10',
            'ibeacon_uuid': 'test_value_11',
            'major_id': '12',
            'minor_id': '13',
            'name': 'default_name_14',
            'txpower': '0'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_ble_profile.fortios_wireless_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller', 'ble-profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_ble_profile_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_ble_profile': {
            'advertising': 'ibeacon',
            'beacon_interval': '4',
            'ble_scanning': 'enable',
            'comment': 'Comment.',
            'eddystone_instance': 'test_value_7',
            'eddystone_namespace': 'test_value_8',
            'eddystone_url': 'test_value_9',
            'eddystone_url_encode_hex': 'test_value_10',
            'ibeacon_uuid': 'test_value_11',
            'major_id': '12',
            'minor_id': '13',
            'name': 'default_name_14',
            'txpower': '0'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_ble_profile.fortios_wireless_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller', 'ble-profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_ble_profile_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_ble_profile': {
            'advertising': 'ibeacon',
            'beacon_interval': '4',
            'ble_scanning': 'enable',
            'comment': 'Comment.',
            'eddystone_instance': 'test_value_7',
            'eddystone_namespace': 'test_value_8',
            'eddystone_url': 'test_value_9',
            'eddystone_url_encode_hex': 'test_value_10',
            'ibeacon_uuid': 'test_value_11',
            'major_id': '12',
            'minor_id': '13',
            'name': 'default_name_14',
            'txpower': '0'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_ble_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'advertising': 'ibeacon',
        'beacon-interval': '4',
        'ble-scanning': 'enable',
        'comment': 'Comment.',
        'eddystone-instance': 'test_value_7',
        'eddystone-namespace': 'test_value_8',
        'eddystone-url': 'test_value_9',
        'eddystone-url-encode-hex': 'test_value_10',
        'ibeacon-uuid': 'test_value_11',
        'major-id': '12',
        'minor-id': '13',
        'name': 'default_name_14',
                'txpower': '0'
    }

    set_method_mock.assert_called_with('wireless-controller', 'ble-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_ble_profile_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_ble_profile': {
            'random_attribute_not_valid': 'tag',
            'advertising': 'ibeacon',
            'beacon_interval': '4',
            'ble_scanning': 'enable',
            'comment': 'Comment.',
            'eddystone_instance': 'test_value_7',
            'eddystone_namespace': 'test_value_8',
            'eddystone_url': 'test_value_9',
            'eddystone_url_encode_hex': 'test_value_10',
            'ibeacon_uuid': 'test_value_11',
            'major_id': '12',
            'minor_id': '13',
            'name': 'default_name_14',
            'txpower': '0'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_ble_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'advertising': 'ibeacon',
        'beacon-interval': '4',
        'ble-scanning': 'enable',
        'comment': 'Comment.',
        'eddystone-instance': 'test_value_7',
        'eddystone-namespace': 'test_value_8',
        'eddystone-url': 'test_value_9',
        'eddystone-url-encode-hex': 'test_value_10',
        'ibeacon-uuid': 'test_value_11',
        'major-id': '12',
        'minor-id': '13',
        'name': 'default_name_14',
                'txpower': '0'
    }

    set_method_mock.assert_called_with('wireless-controller', 'ble-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
