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
    from ansible.modules.network.fortios import fortios_user_setting
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_user_setting.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_user_setting_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_setting': {
            'auth_blackout_time': '3',
            'auth_ca_cert': 'test_value_4',
            'auth_cert': 'test_value_5',
            'auth_http_basic': 'enable',
            'auth_invalid_max': '7',
            'auth_lockout_duration': '8',
            'auth_lockout_threshold': '9',
            'auth_portal_timeout': '10',
            'auth_secure_http': 'enable',
            'auth_src_mac': 'enable',
            'auth_ssl_allow_renegotiation': 'enable',
            'auth_timeout': '14',
            'auth_timeout_type': 'idle-timeout',
            'auth_type': 'http',
            'radius_ses_timeout_act': 'hard-timeout'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_setting.fortios_user(input_data, fos_instance)

    expected_data = {
        'auth-blackout-time': '3',
        'auth-ca-cert': 'test_value_4',
        'auth-cert': 'test_value_5',
        'auth-http-basic': 'enable',
        'auth-invalid-max': '7',
        'auth-lockout-duration': '8',
        'auth-lockout-threshold': '9',
        'auth-portal-timeout': '10',
        'auth-secure-http': 'enable',
        'auth-src-mac': 'enable',
        'auth-ssl-allow-renegotiation': 'enable',
        'auth-timeout': '14',
        'auth-timeout-type': 'idle-timeout',
        'auth-type': 'http',
        'radius-ses-timeout-act': 'hard-timeout'
    }

    set_method_mock.assert_called_with('user', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_user_setting_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_setting': {
            'auth_blackout_time': '3',
            'auth_ca_cert': 'test_value_4',
            'auth_cert': 'test_value_5',
            'auth_http_basic': 'enable',
            'auth_invalid_max': '7',
            'auth_lockout_duration': '8',
            'auth_lockout_threshold': '9',
            'auth_portal_timeout': '10',
            'auth_secure_http': 'enable',
            'auth_src_mac': 'enable',
            'auth_ssl_allow_renegotiation': 'enable',
            'auth_timeout': '14',
            'auth_timeout_type': 'idle-timeout',
            'auth_type': 'http',
            'radius_ses_timeout_act': 'hard-timeout'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_setting.fortios_user(input_data, fos_instance)

    expected_data = {
        'auth-blackout-time': '3',
        'auth-ca-cert': 'test_value_4',
        'auth-cert': 'test_value_5',
        'auth-http-basic': 'enable',
        'auth-invalid-max': '7',
        'auth-lockout-duration': '8',
        'auth-lockout-threshold': '9',
        'auth-portal-timeout': '10',
        'auth-secure-http': 'enable',
        'auth-src-mac': 'enable',
        'auth-ssl-allow-renegotiation': 'enable',
        'auth-timeout': '14',
        'auth-timeout-type': 'idle-timeout',
        'auth-type': 'http',
        'radius-ses-timeout-act': 'hard-timeout'
    }

    set_method_mock.assert_called_with('user', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_user_setting_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_setting': {
            'auth_blackout_time': '3',
            'auth_ca_cert': 'test_value_4',
            'auth_cert': 'test_value_5',
            'auth_http_basic': 'enable',
            'auth_invalid_max': '7',
            'auth_lockout_duration': '8',
            'auth_lockout_threshold': '9',
            'auth_portal_timeout': '10',
            'auth_secure_http': 'enable',
            'auth_src_mac': 'enable',
            'auth_ssl_allow_renegotiation': 'enable',
            'auth_timeout': '14',
            'auth_timeout_type': 'idle-timeout',
            'auth_type': 'http',
            'radius_ses_timeout_act': 'hard-timeout'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_setting.fortios_user(input_data, fos_instance)

    expected_data = {
        'auth-blackout-time': '3',
        'auth-ca-cert': 'test_value_4',
        'auth-cert': 'test_value_5',
        'auth-http-basic': 'enable',
        'auth-invalid-max': '7',
        'auth-lockout-duration': '8',
        'auth-lockout-threshold': '9',
        'auth-portal-timeout': '10',
        'auth-secure-http': 'enable',
        'auth-src-mac': 'enable',
        'auth-ssl-allow-renegotiation': 'enable',
        'auth-timeout': '14',
        'auth-timeout-type': 'idle-timeout',
        'auth-type': 'http',
        'radius-ses-timeout-act': 'hard-timeout'
    }

    set_method_mock.assert_called_with('user', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_user_setting_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_setting': {
            'random_attribute_not_valid': 'tag',
            'auth_blackout_time': '3',
            'auth_ca_cert': 'test_value_4',
            'auth_cert': 'test_value_5',
            'auth_http_basic': 'enable',
            'auth_invalid_max': '7',
            'auth_lockout_duration': '8',
            'auth_lockout_threshold': '9',
            'auth_portal_timeout': '10',
            'auth_secure_http': 'enable',
            'auth_src_mac': 'enable',
            'auth_ssl_allow_renegotiation': 'enable',
            'auth_timeout': '14',
            'auth_timeout_type': 'idle-timeout',
            'auth_type': 'http',
            'radius_ses_timeout_act': 'hard-timeout'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_setting.fortios_user(input_data, fos_instance)

    expected_data = {
        'auth-blackout-time': '3',
        'auth-ca-cert': 'test_value_4',
        'auth-cert': 'test_value_5',
        'auth-http-basic': 'enable',
        'auth-invalid-max': '7',
        'auth-lockout-duration': '8',
        'auth-lockout-threshold': '9',
        'auth-portal-timeout': '10',
        'auth-secure-http': 'enable',
        'auth-src-mac': 'enable',
        'auth-ssl-allow-renegotiation': 'enable',
        'auth-timeout': '14',
        'auth-timeout-type': 'idle-timeout',
        'auth-type': 'http',
        'radius-ses-timeout-act': 'hard-timeout'
    }

    set_method_mock.assert_called_with('user', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
