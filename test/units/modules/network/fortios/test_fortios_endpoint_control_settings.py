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
    from ansible.modules.network.fortios import fortios_endpoint_control_settings
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_endpoint_control_settings.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_endpoint_control_settings_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'endpoint_control_settings': {
            'download_custom_link': 'test_value_3',
            'download_location': 'fortiguard',
            'forticlient_avdb_update_interval': '5',
            'forticlient_dereg_unsupported_client': 'enable',
            'forticlient_ems_rest_api_call_timeout': '7',
            'forticlient_keepalive_interval': '8',
            'forticlient_offline_grace': 'enable',
            'forticlient_offline_grace_interval': '10',
            'forticlient_reg_key': 'test_value_11',
            'forticlient_reg_key_enforce': 'enable',
            'forticlient_reg_timeout': '13',
            'forticlient_sys_update_interval': '14',
            'forticlient_user_avatar': 'enable',
            'forticlient_warning_interval': '16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_endpoint_control_settings.fortios_endpoint_control(input_data, fos_instance)

    expected_data = {
        'download-custom-link': 'test_value_3',
        'download-location': 'fortiguard',
        'forticlient-avdb-update-interval': '5',
        'forticlient-dereg-unsupported-client': 'enable',
        'forticlient-ems-rest-api-call-timeout': '7',
        'forticlient-keepalive-interval': '8',
        'forticlient-offline-grace': 'enable',
        'forticlient-offline-grace-interval': '10',
        'forticlient-reg-key': 'test_value_11',
        'forticlient-reg-key-enforce': 'enable',
        'forticlient-reg-timeout': '13',
        'forticlient-sys-update-interval': '14',
        'forticlient-user-avatar': 'enable',
        'forticlient-warning-interval': '16'
    }

    set_method_mock.assert_called_with('endpoint-control', 'settings', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_endpoint_control_settings_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'endpoint_control_settings': {
            'download_custom_link': 'test_value_3',
            'download_location': 'fortiguard',
            'forticlient_avdb_update_interval': '5',
            'forticlient_dereg_unsupported_client': 'enable',
            'forticlient_ems_rest_api_call_timeout': '7',
            'forticlient_keepalive_interval': '8',
            'forticlient_offline_grace': 'enable',
            'forticlient_offline_grace_interval': '10',
            'forticlient_reg_key': 'test_value_11',
            'forticlient_reg_key_enforce': 'enable',
            'forticlient_reg_timeout': '13',
            'forticlient_sys_update_interval': '14',
            'forticlient_user_avatar': 'enable',
            'forticlient_warning_interval': '16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_endpoint_control_settings.fortios_endpoint_control(input_data, fos_instance)

    expected_data = {
        'download-custom-link': 'test_value_3',
        'download-location': 'fortiguard',
        'forticlient-avdb-update-interval': '5',
        'forticlient-dereg-unsupported-client': 'enable',
        'forticlient-ems-rest-api-call-timeout': '7',
        'forticlient-keepalive-interval': '8',
        'forticlient-offline-grace': 'enable',
        'forticlient-offline-grace-interval': '10',
        'forticlient-reg-key': 'test_value_11',
        'forticlient-reg-key-enforce': 'enable',
        'forticlient-reg-timeout': '13',
        'forticlient-sys-update-interval': '14',
        'forticlient-user-avatar': 'enable',
        'forticlient-warning-interval': '16'
    }

    set_method_mock.assert_called_with('endpoint-control', 'settings', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_endpoint_control_settings_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'endpoint_control_settings': {
            'download_custom_link': 'test_value_3',
            'download_location': 'fortiguard',
            'forticlient_avdb_update_interval': '5',
            'forticlient_dereg_unsupported_client': 'enable',
            'forticlient_ems_rest_api_call_timeout': '7',
            'forticlient_keepalive_interval': '8',
            'forticlient_offline_grace': 'enable',
            'forticlient_offline_grace_interval': '10',
            'forticlient_reg_key': 'test_value_11',
            'forticlient_reg_key_enforce': 'enable',
            'forticlient_reg_timeout': '13',
            'forticlient_sys_update_interval': '14',
            'forticlient_user_avatar': 'enable',
            'forticlient_warning_interval': '16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_endpoint_control_settings.fortios_endpoint_control(input_data, fos_instance)

    expected_data = {
        'download-custom-link': 'test_value_3',
        'download-location': 'fortiguard',
        'forticlient-avdb-update-interval': '5',
        'forticlient-dereg-unsupported-client': 'enable',
        'forticlient-ems-rest-api-call-timeout': '7',
        'forticlient-keepalive-interval': '8',
        'forticlient-offline-grace': 'enable',
        'forticlient-offline-grace-interval': '10',
        'forticlient-reg-key': 'test_value_11',
        'forticlient-reg-key-enforce': 'enable',
        'forticlient-reg-timeout': '13',
        'forticlient-sys-update-interval': '14',
        'forticlient-user-avatar': 'enable',
        'forticlient-warning-interval': '16'
    }

    set_method_mock.assert_called_with('endpoint-control', 'settings', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_endpoint_control_settings_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'endpoint_control_settings': {
            'random_attribute_not_valid': 'tag',
            'download_custom_link': 'test_value_3',
            'download_location': 'fortiguard',
            'forticlient_avdb_update_interval': '5',
            'forticlient_dereg_unsupported_client': 'enable',
            'forticlient_ems_rest_api_call_timeout': '7',
            'forticlient_keepalive_interval': '8',
            'forticlient_offline_grace': 'enable',
            'forticlient_offline_grace_interval': '10',
            'forticlient_reg_key': 'test_value_11',
            'forticlient_reg_key_enforce': 'enable',
            'forticlient_reg_timeout': '13',
            'forticlient_sys_update_interval': '14',
            'forticlient_user_avatar': 'enable',
            'forticlient_warning_interval': '16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_endpoint_control_settings.fortios_endpoint_control(input_data, fos_instance)

    expected_data = {
        'download-custom-link': 'test_value_3',
        'download-location': 'fortiguard',
        'forticlient-avdb-update-interval': '5',
        'forticlient-dereg-unsupported-client': 'enable',
        'forticlient-ems-rest-api-call-timeout': '7',
        'forticlient-keepalive-interval': '8',
        'forticlient-offline-grace': 'enable',
        'forticlient-offline-grace-interval': '10',
        'forticlient-reg-key': 'test_value_11',
        'forticlient-reg-key-enforce': 'enable',
        'forticlient-reg-timeout': '13',
        'forticlient-sys-update-interval': '14',
        'forticlient-user-avatar': 'enable',
        'forticlient-warning-interval': '16'
    }

    set_method_mock.assert_called_with('endpoint-control', 'settings', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
