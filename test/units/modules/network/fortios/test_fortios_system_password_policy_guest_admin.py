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
    from ansible.modules.network.fortios import fortios_system_password_policy_guest_admin
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_system_password_policy_guest_admin.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_system_password_policy_guest_admin_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_password_policy_guest_admin': {
            'apply_to': 'guest-admin-password',
            'change_4_characters': 'enable',
            'expire_day': '5',
            'expire_status': 'enable',
            'min_lower_case_letter': '7',
            'min_non_alphanumeric': '8',
            'min_number': '9',
            'min_upper_case_letter': '10',
            'minimum_length': '11',
            'reuse_password': 'enable',
            'status': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_password_policy_guest_admin.fortios_system(input_data, fos_instance)

    expected_data = {
        'apply-to': 'guest-admin-password',
        'change-4-characters': 'enable',
        'expire-day': '5',
        'expire-status': 'enable',
        'min-lower-case-letter': '7',
        'min-non-alphanumeric': '8',
        'min-number': '9',
        'min-upper-case-letter': '10',
        'minimum-length': '11',
        'reuse-password': 'enable',
        'status': 'enable'
    }

    set_method_mock.assert_called_with('system', 'password-policy-guest-admin', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_password_policy_guest_admin_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_password_policy_guest_admin': {
            'apply_to': 'guest-admin-password',
            'change_4_characters': 'enable',
            'expire_day': '5',
            'expire_status': 'enable',
            'min_lower_case_letter': '7',
            'min_non_alphanumeric': '8',
            'min_number': '9',
            'min_upper_case_letter': '10',
            'minimum_length': '11',
            'reuse_password': 'enable',
            'status': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_password_policy_guest_admin.fortios_system(input_data, fos_instance)

    expected_data = {
        'apply-to': 'guest-admin-password',
        'change-4-characters': 'enable',
        'expire-day': '5',
        'expire-status': 'enable',
        'min-lower-case-letter': '7',
        'min-non-alphanumeric': '8',
        'min-number': '9',
        'min-upper-case-letter': '10',
        'minimum-length': '11',
        'reuse-password': 'enable',
        'status': 'enable'
    }

    set_method_mock.assert_called_with('system', 'password-policy-guest-admin', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_password_policy_guest_admin_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_password_policy_guest_admin': {
            'apply_to': 'guest-admin-password',
            'change_4_characters': 'enable',
            'expire_day': '5',
            'expire_status': 'enable',
            'min_lower_case_letter': '7',
            'min_non_alphanumeric': '8',
            'min_number': '9',
            'min_upper_case_letter': '10',
            'minimum_length': '11',
            'reuse_password': 'enable',
            'status': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_password_policy_guest_admin.fortios_system(input_data, fos_instance)

    expected_data = {
        'apply-to': 'guest-admin-password',
        'change-4-characters': 'enable',
        'expire-day': '5',
        'expire-status': 'enable',
        'min-lower-case-letter': '7',
        'min-non-alphanumeric': '8',
        'min-number': '9',
        'min-upper-case-letter': '10',
        'minimum-length': '11',
        'reuse-password': 'enable',
        'status': 'enable'
    }

    set_method_mock.assert_called_with('system', 'password-policy-guest-admin', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_system_password_policy_guest_admin_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_password_policy_guest_admin': {
            'random_attribute_not_valid': 'tag',
            'apply_to': 'guest-admin-password',
            'change_4_characters': 'enable',
            'expire_day': '5',
            'expire_status': 'enable',
            'min_lower_case_letter': '7',
            'min_non_alphanumeric': '8',
            'min_number': '9',
            'min_upper_case_letter': '10',
            'minimum_length': '11',
            'reuse_password': 'enable',
            'status': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_password_policy_guest_admin.fortios_system(input_data, fos_instance)

    expected_data = {
        'apply-to': 'guest-admin-password',
        'change-4-characters': 'enable',
        'expire-day': '5',
        'expire-status': 'enable',
        'min-lower-case-letter': '7',
        'min-non-alphanumeric': '8',
        'min-number': '9',
        'min-upper-case-letter': '10',
        'minimum-length': '11',
        'reuse-password': 'enable',
        'status': 'enable'
    }

    set_method_mock.assert_called_with('system', 'password-policy-guest-admin', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
