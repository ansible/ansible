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
    from ansible.modules.network.fortios import fortios_switch_controller_security_policy_802_1X
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_switch_controller_security_policy_802_1X.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_switch_controller_security_policy_802_1X_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'switch_controller_security_policy_802_1X': {
            'auth_fail_vlan': 'disable',
            'auth_fail_vlan_id': 'test_value_4',
            'auth_fail_vlanid': '5',
            'eap_passthru': 'disable',
            'guest_auth_delay': '7',
            'guest_vlan': 'disable',
            'guest_vlan_id': 'test_value_9',
            'guest_vlanid': '10',
            'mac_auth_bypass': 'disable',
            'name': 'default_name_12',
            'open_auth': 'disable',
            'policy_type': '802.1X',
            'radius_timeout_overwrite': 'disable',
            'security_mode': '802.1X',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_security_policy_802_1X.fortios_switch_controller_security_policy(input_data, fos_instance)

    expected_data = {
        'auth-fail-vlan': 'disable',
        'auth-fail-vlan-id': 'test_value_4',
        'auth-fail-vlanid': '5',
        'eap-passthru': 'disable',
        'guest-auth-delay': '7',
        'guest-vlan': 'disable',
        'guest-vlan-id': 'test_value_9',
        'guest-vlanid': '10',
        'mac-auth-bypass': 'disable',
        'name': 'default_name_12',
                'open-auth': 'disable',
                'policy-type': '802.1X',
                'radius-timeout-overwrite': 'disable',
                'security-mode': '802.1X',

    }

    set_method_mock.assert_called_with('switch-controller.security-policy', '802-1X', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_switch_controller_security_policy_802_1X_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'switch_controller_security_policy_802_1X': {
            'auth_fail_vlan': 'disable',
            'auth_fail_vlan_id': 'test_value_4',
            'auth_fail_vlanid': '5',
            'eap_passthru': 'disable',
            'guest_auth_delay': '7',
            'guest_vlan': 'disable',
            'guest_vlan_id': 'test_value_9',
            'guest_vlanid': '10',
            'mac_auth_bypass': 'disable',
            'name': 'default_name_12',
            'open_auth': 'disable',
            'policy_type': '802.1X',
            'radius_timeout_overwrite': 'disable',
            'security_mode': '802.1X',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_security_policy_802_1X.fortios_switch_controller_security_policy(input_data, fos_instance)

    expected_data = {
        'auth-fail-vlan': 'disable',
        'auth-fail-vlan-id': 'test_value_4',
        'auth-fail-vlanid': '5',
        'eap-passthru': 'disable',
        'guest-auth-delay': '7',
        'guest-vlan': 'disable',
        'guest-vlan-id': 'test_value_9',
        'guest-vlanid': '10',
        'mac-auth-bypass': 'disable',
        'name': 'default_name_12',
                'open-auth': 'disable',
                'policy-type': '802.1X',
                'radius-timeout-overwrite': 'disable',
                'security-mode': '802.1X',

    }

    set_method_mock.assert_called_with('switch-controller.security-policy', '802-1X', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_switch_controller_security_policy_802_1X_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'switch_controller_security_policy_802_1X': {
            'auth_fail_vlan': 'disable',
            'auth_fail_vlan_id': 'test_value_4',
            'auth_fail_vlanid': '5',
            'eap_passthru': 'disable',
            'guest_auth_delay': '7',
            'guest_vlan': 'disable',
            'guest_vlan_id': 'test_value_9',
            'guest_vlanid': '10',
            'mac_auth_bypass': 'disable',
            'name': 'default_name_12',
            'open_auth': 'disable',
            'policy_type': '802.1X',
            'radius_timeout_overwrite': 'disable',
            'security_mode': '802.1X',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_security_policy_802_1X.fortios_switch_controller_security_policy(input_data, fos_instance)

    delete_method_mock.assert_called_with('switch-controller.security-policy', '802-1X', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_switch_controller_security_policy_802_1X_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'switch_controller_security_policy_802_1X': {
            'auth_fail_vlan': 'disable',
            'auth_fail_vlan_id': 'test_value_4',
            'auth_fail_vlanid': '5',
            'eap_passthru': 'disable',
            'guest_auth_delay': '7',
            'guest_vlan': 'disable',
            'guest_vlan_id': 'test_value_9',
            'guest_vlanid': '10',
            'mac_auth_bypass': 'disable',
            'name': 'default_name_12',
            'open_auth': 'disable',
            'policy_type': '802.1X',
            'radius_timeout_overwrite': 'disable',
            'security_mode': '802.1X',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_security_policy_802_1X.fortios_switch_controller_security_policy(input_data, fos_instance)

    delete_method_mock.assert_called_with('switch-controller.security-policy', '802-1X', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_switch_controller_security_policy_802_1X_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'switch_controller_security_policy_802_1X': {
            'auth_fail_vlan': 'disable',
            'auth_fail_vlan_id': 'test_value_4',
            'auth_fail_vlanid': '5',
            'eap_passthru': 'disable',
            'guest_auth_delay': '7',
            'guest_vlan': 'disable',
            'guest_vlan_id': 'test_value_9',
            'guest_vlanid': '10',
            'mac_auth_bypass': 'disable',
            'name': 'default_name_12',
            'open_auth': 'disable',
            'policy_type': '802.1X',
            'radius_timeout_overwrite': 'disable',
            'security_mode': '802.1X',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_security_policy_802_1X.fortios_switch_controller_security_policy(input_data, fos_instance)

    expected_data = {
        'auth-fail-vlan': 'disable',
        'auth-fail-vlan-id': 'test_value_4',
        'auth-fail-vlanid': '5',
        'eap-passthru': 'disable',
        'guest-auth-delay': '7',
        'guest-vlan': 'disable',
        'guest-vlan-id': 'test_value_9',
        'guest-vlanid': '10',
        'mac-auth-bypass': 'disable',
        'name': 'default_name_12',
                'open-auth': 'disable',
                'policy-type': '802.1X',
                'radius-timeout-overwrite': 'disable',
                'security-mode': '802.1X',

    }

    set_method_mock.assert_called_with('switch-controller.security-policy', '802-1X', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_switch_controller_security_policy_802_1X_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'switch_controller_security_policy_802_1X': {
            'random_attribute_not_valid': 'tag',
            'auth_fail_vlan': 'disable',
            'auth_fail_vlan_id': 'test_value_4',
            'auth_fail_vlanid': '5',
            'eap_passthru': 'disable',
            'guest_auth_delay': '7',
            'guest_vlan': 'disable',
            'guest_vlan_id': 'test_value_9',
            'guest_vlanid': '10',
            'mac_auth_bypass': 'disable',
            'name': 'default_name_12',
            'open_auth': 'disable',
            'policy_type': '802.1X',
            'radius_timeout_overwrite': 'disable',
            'security_mode': '802.1X',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_security_policy_802_1X.fortios_switch_controller_security_policy(input_data, fos_instance)

    expected_data = {
        'auth-fail-vlan': 'disable',
        'auth-fail-vlan-id': 'test_value_4',
        'auth-fail-vlanid': '5',
        'eap-passthru': 'disable',
        'guest-auth-delay': '7',
        'guest-vlan': 'disable',
        'guest-vlan-id': 'test_value_9',
        'guest-vlanid': '10',
        'mac-auth-bypass': 'disable',
        'name': 'default_name_12',
                'open-auth': 'disable',
                'policy-type': '802.1X',
                'radius-timeout-overwrite': 'disable',
                'security-mode': '802.1X',

    }

    set_method_mock.assert_called_with('switch-controller.security-policy', '802-1X', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
