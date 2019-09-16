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
    from ansible.modules.network.fortios import fortios_user_radius
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_user_radius.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_user_radius_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_radius': {'acct_all_servers': 'enable',
                        'acct_interim_interval': '4',
                        'all_usergroup': 'disable',
                        'auth_type': 'auto',
                        'h3c_compatibility': 'enable',
                        'name': 'default_name_8',
                        'nas_ip': 'test_value_9',
                        'password_encoding': 'auto',
                        'password_renewal': 'enable',
                        'radius_coa': 'enable',
                        'radius_port': '13',
                        'rsso': 'enable',
                        'rsso_context_timeout': '15',
                        'rsso_endpoint_attribute': 'User-Name',
                        'rsso_endpoint_block_attribute': 'User-Name',
                        'rsso_ep_one_ip_only': 'enable',
                        'rsso_flush_ip_session': 'enable',
                        'rsso_log_flags': 'protocol-error',
                        'rsso_log_period': '21',
                        'rsso_radius_response': 'enable',
                        'rsso_radius_server_port': '23',
                        'rsso_secret': 'test_value_24',
                        'rsso_validate_request_secret': 'enable',
                        'secondary_secret': 'test_value_26',
                        'secondary_server': 'test_value_27',
                        'secret': 'test_value_28',
                        'server': '192.168.100.29',
                        'source_ip': '84.230.14.30',
                        'sso_attribute': 'User-Name',
                        'sso_attribute_key': 'test_value_32',
                        'sso_attribute_value_override': 'enable',
                        'tertiary_secret': 'test_value_34',
                        'tertiary_server': 'test_value_35',
                        'timeout': '36',
                        'use_management_vdom': 'enable',
                        'username_case_sensitive': 'enable'
                        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_radius.fortios_user(input_data, fos_instance)

    expected_data = {'acct-all-servers': 'enable',
                     'acct-interim-interval': '4',
                     'all-usergroup': 'disable',
                     'auth-type': 'auto',
                     'h3c-compatibility': 'enable',
                     'name': 'default_name_8',
                     'nas-ip': 'test_value_9',
                     'password-encoding': 'auto',
                     'password-renewal': 'enable',
                     'radius-coa': 'enable',
                     'radius-port': '13',
                     'rsso': 'enable',
                     'rsso-context-timeout': '15',
                     'rsso-endpoint-attribute': 'User-Name',
                     'rsso-endpoint-block-attribute': 'User-Name',
                     'rsso-ep-one-ip-only': 'enable',
                     'rsso-flush-ip-session': 'enable',
                     'rsso-log-flags': 'protocol-error',
                     'rsso-log-period': '21',
                     'rsso-radius-response': 'enable',
                     'rsso-radius-server-port': '23',
                     'rsso-secret': 'test_value_24',
                     'rsso-validate-request-secret': 'enable',
                     'secondary-secret': 'test_value_26',
                     'secondary-server': 'test_value_27',
                     'secret': 'test_value_28',
                     'server': '192.168.100.29',
                     'source-ip': '84.230.14.30',
                     'sso-attribute': 'User-Name',
                     'sso-attribute-key': 'test_value_32',
                     'sso-attribute-value-override': 'enable',
                     'tertiary-secret': 'test_value_34',
                     'tertiary-server': 'test_value_35',
                     'timeout': '36',
                     'use-management-vdom': 'enable',
                     'username-case-sensitive': 'enable'
                     }

    set_method_mock.assert_called_with('user', 'radius', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_user_radius_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_radius': {'acct_all_servers': 'enable',
                        'acct_interim_interval': '4',
                        'all_usergroup': 'disable',
                        'auth_type': 'auto',
                        'h3c_compatibility': 'enable',
                        'name': 'default_name_8',
                        'nas_ip': 'test_value_9',
                        'password_encoding': 'auto',
                        'password_renewal': 'enable',
                        'radius_coa': 'enable',
                        'radius_port': '13',
                        'rsso': 'enable',
                        'rsso_context_timeout': '15',
                        'rsso_endpoint_attribute': 'User-Name',
                        'rsso_endpoint_block_attribute': 'User-Name',
                        'rsso_ep_one_ip_only': 'enable',
                        'rsso_flush_ip_session': 'enable',
                        'rsso_log_flags': 'protocol-error',
                        'rsso_log_period': '21',
                        'rsso_radius_response': 'enable',
                        'rsso_radius_server_port': '23',
                        'rsso_secret': 'test_value_24',
                        'rsso_validate_request_secret': 'enable',
                        'secondary_secret': 'test_value_26',
                        'secondary_server': 'test_value_27',
                        'secret': 'test_value_28',
                        'server': '192.168.100.29',
                        'source_ip': '84.230.14.30',
                        'sso_attribute': 'User-Name',
                        'sso_attribute_key': 'test_value_32',
                        'sso_attribute_value_override': 'enable',
                        'tertiary_secret': 'test_value_34',
                        'tertiary_server': 'test_value_35',
                        'timeout': '36',
                        'use_management_vdom': 'enable',
                        'username_case_sensitive': 'enable'
                        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_radius.fortios_user(input_data, fos_instance)

    expected_data = {'acct-all-servers': 'enable',
                     'acct-interim-interval': '4',
                     'all-usergroup': 'disable',
                     'auth-type': 'auto',
                     'h3c-compatibility': 'enable',
                     'name': 'default_name_8',
                     'nas-ip': 'test_value_9',
                     'password-encoding': 'auto',
                     'password-renewal': 'enable',
                     'radius-coa': 'enable',
                     'radius-port': '13',
                     'rsso': 'enable',
                     'rsso-context-timeout': '15',
                     'rsso-endpoint-attribute': 'User-Name',
                     'rsso-endpoint-block-attribute': 'User-Name',
                     'rsso-ep-one-ip-only': 'enable',
                     'rsso-flush-ip-session': 'enable',
                     'rsso-log-flags': 'protocol-error',
                     'rsso-log-period': '21',
                     'rsso-radius-response': 'enable',
                     'rsso-radius-server-port': '23',
                     'rsso-secret': 'test_value_24',
                     'rsso-validate-request-secret': 'enable',
                     'secondary-secret': 'test_value_26',
                     'secondary-server': 'test_value_27',
                     'secret': 'test_value_28',
                     'server': '192.168.100.29',
                     'source-ip': '84.230.14.30',
                     'sso-attribute': 'User-Name',
                     'sso-attribute-key': 'test_value_32',
                     'sso-attribute-value-override': 'enable',
                     'tertiary-secret': 'test_value_34',
                     'tertiary-server': 'test_value_35',
                     'timeout': '36',
                     'use-management-vdom': 'enable',
                     'username-case-sensitive': 'enable'
                     }

    set_method_mock.assert_called_with('user', 'radius', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_user_radius_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'user_radius': {'acct_all_servers': 'enable',
                        'acct_interim_interval': '4',
                        'all_usergroup': 'disable',
                        'auth_type': 'auto',
                        'h3c_compatibility': 'enable',
                        'name': 'default_name_8',
                        'nas_ip': 'test_value_9',
                        'password_encoding': 'auto',
                        'password_renewal': 'enable',
                        'radius_coa': 'enable',
                        'radius_port': '13',
                        'rsso': 'enable',
                        'rsso_context_timeout': '15',
                        'rsso_endpoint_attribute': 'User-Name',
                        'rsso_endpoint_block_attribute': 'User-Name',
                        'rsso_ep_one_ip_only': 'enable',
                        'rsso_flush_ip_session': 'enable',
                        'rsso_log_flags': 'protocol-error',
                        'rsso_log_period': '21',
                        'rsso_radius_response': 'enable',
                        'rsso_radius_server_port': '23',
                        'rsso_secret': 'test_value_24',
                        'rsso_validate_request_secret': 'enable',
                        'secondary_secret': 'test_value_26',
                        'secondary_server': 'test_value_27',
                        'secret': 'test_value_28',
                        'server': '192.168.100.29',
                        'source_ip': '84.230.14.30',
                        'sso_attribute': 'User-Name',
                        'sso_attribute_key': 'test_value_32',
                        'sso_attribute_value_override': 'enable',
                        'tertiary_secret': 'test_value_34',
                        'tertiary_server': 'test_value_35',
                        'timeout': '36',
                        'use_management_vdom': 'enable',
                        'username_case_sensitive': 'enable'
                        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_radius.fortios_user(input_data, fos_instance)

    delete_method_mock.assert_called_with('user', 'radius', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_user_radius_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'user_radius': {'acct_all_servers': 'enable',
                        'acct_interim_interval': '4',
                        'all_usergroup': 'disable',
                        'auth_type': 'auto',
                        'h3c_compatibility': 'enable',
                        'name': 'default_name_8',
                        'nas_ip': 'test_value_9',
                        'password_encoding': 'auto',
                        'password_renewal': 'enable',
                        'radius_coa': 'enable',
                        'radius_port': '13',
                        'rsso': 'enable',
                        'rsso_context_timeout': '15',
                        'rsso_endpoint_attribute': 'User-Name',
                        'rsso_endpoint_block_attribute': 'User-Name',
                        'rsso_ep_one_ip_only': 'enable',
                        'rsso_flush_ip_session': 'enable',
                        'rsso_log_flags': 'protocol-error',
                        'rsso_log_period': '21',
                        'rsso_radius_response': 'enable',
                        'rsso_radius_server_port': '23',
                        'rsso_secret': 'test_value_24',
                        'rsso_validate_request_secret': 'enable',
                        'secondary_secret': 'test_value_26',
                        'secondary_server': 'test_value_27',
                        'secret': 'test_value_28',
                        'server': '192.168.100.29',
                        'source_ip': '84.230.14.30',
                        'sso_attribute': 'User-Name',
                        'sso_attribute_key': 'test_value_32',
                        'sso_attribute_value_override': 'enable',
                        'tertiary_secret': 'test_value_34',
                        'tertiary_server': 'test_value_35',
                        'timeout': '36',
                        'use_management_vdom': 'enable',
                        'username_case_sensitive': 'enable'
                        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_radius.fortios_user(input_data, fos_instance)

    delete_method_mock.assert_called_with('user', 'radius', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_user_radius_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_radius': {'acct_all_servers': 'enable',
                        'acct_interim_interval': '4',
                        'all_usergroup': 'disable',
                        'auth_type': 'auto',
                        'h3c_compatibility': 'enable',
                        'name': 'default_name_8',
                        'nas_ip': 'test_value_9',
                        'password_encoding': 'auto',
                        'password_renewal': 'enable',
                        'radius_coa': 'enable',
                        'radius_port': '13',
                        'rsso': 'enable',
                        'rsso_context_timeout': '15',
                        'rsso_endpoint_attribute': 'User-Name',
                        'rsso_endpoint_block_attribute': 'User-Name',
                        'rsso_ep_one_ip_only': 'enable',
                        'rsso_flush_ip_session': 'enable',
                        'rsso_log_flags': 'protocol-error',
                        'rsso_log_period': '21',
                        'rsso_radius_response': 'enable',
                        'rsso_radius_server_port': '23',
                        'rsso_secret': 'test_value_24',
                        'rsso_validate_request_secret': 'enable',
                        'secondary_secret': 'test_value_26',
                        'secondary_server': 'test_value_27',
                        'secret': 'test_value_28',
                        'server': '192.168.100.29',
                        'source_ip': '84.230.14.30',
                        'sso_attribute': 'User-Name',
                        'sso_attribute_key': 'test_value_32',
                        'sso_attribute_value_override': 'enable',
                        'tertiary_secret': 'test_value_34',
                        'tertiary_server': 'test_value_35',
                        'timeout': '36',
                        'use_management_vdom': 'enable',
                        'username_case_sensitive': 'enable'
                        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_radius.fortios_user(input_data, fos_instance)

    expected_data = {'acct-all-servers': 'enable',
                     'acct-interim-interval': '4',
                     'all-usergroup': 'disable',
                     'auth-type': 'auto',
                     'h3c-compatibility': 'enable',
                     'name': 'default_name_8',
                     'nas-ip': 'test_value_9',
                     'password-encoding': 'auto',
                     'password-renewal': 'enable',
                     'radius-coa': 'enable',
                     'radius-port': '13',
                     'rsso': 'enable',
                     'rsso-context-timeout': '15',
                     'rsso-endpoint-attribute': 'User-Name',
                     'rsso-endpoint-block-attribute': 'User-Name',
                     'rsso-ep-one-ip-only': 'enable',
                     'rsso-flush-ip-session': 'enable',
                     'rsso-log-flags': 'protocol-error',
                     'rsso-log-period': '21',
                     'rsso-radius-response': 'enable',
                     'rsso-radius-server-port': '23',
                     'rsso-secret': 'test_value_24',
                     'rsso-validate-request-secret': 'enable',
                     'secondary-secret': 'test_value_26',
                     'secondary-server': 'test_value_27',
                     'secret': 'test_value_28',
                     'server': '192.168.100.29',
                     'source-ip': '84.230.14.30',
                     'sso-attribute': 'User-Name',
                     'sso-attribute-key': 'test_value_32',
                     'sso-attribute-value-override': 'enable',
                     'tertiary-secret': 'test_value_34',
                     'tertiary-server': 'test_value_35',
                     'timeout': '36',
                     'use-management-vdom': 'enable',
                     'username-case-sensitive': 'enable'
                     }

    set_method_mock.assert_called_with('user', 'radius', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_user_radius_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_radius': {
            'random_attribute_not_valid': 'tag', 'acct_all_servers': 'enable',
            'acct_interim_interval': '4',
            'all_usergroup': 'disable',
            'auth_type': 'auto',
            'h3c_compatibility': 'enable',
            'name': 'default_name_8',
            'nas_ip': 'test_value_9',
            'password_encoding': 'auto',
            'password_renewal': 'enable',
            'radius_coa': 'enable',
            'radius_port': '13',
            'rsso': 'enable',
            'rsso_context_timeout': '15',
            'rsso_endpoint_attribute': 'User-Name',
            'rsso_endpoint_block_attribute': 'User-Name',
            'rsso_ep_one_ip_only': 'enable',
            'rsso_flush_ip_session': 'enable',
            'rsso_log_flags': 'protocol-error',
            'rsso_log_period': '21',
            'rsso_radius_response': 'enable',
            'rsso_radius_server_port': '23',
            'rsso_secret': 'test_value_24',
            'rsso_validate_request_secret': 'enable',
            'secondary_secret': 'test_value_26',
            'secondary_server': 'test_value_27',
            'secret': 'test_value_28',
            'server': '192.168.100.29',
            'source_ip': '84.230.14.30',
            'sso_attribute': 'User-Name',
            'sso_attribute_key': 'test_value_32',
            'sso_attribute_value_override': 'enable',
            'tertiary_secret': 'test_value_34',
            'tertiary_server': 'test_value_35',
            'timeout': '36',
            'use_management_vdom': 'enable',
            'username_case_sensitive': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_radius.fortios_user(input_data, fos_instance)

    expected_data = {'acct-all-servers': 'enable',
                     'acct-interim-interval': '4',
                     'all-usergroup': 'disable',
                     'auth-type': 'auto',
                     'h3c-compatibility': 'enable',
                     'name': 'default_name_8',
                     'nas-ip': 'test_value_9',
                     'password-encoding': 'auto',
                     'password-renewal': 'enable',
                     'radius-coa': 'enable',
                     'radius-port': '13',
                     'rsso': 'enable',
                     'rsso-context-timeout': '15',
                     'rsso-endpoint-attribute': 'User-Name',
                     'rsso-endpoint-block-attribute': 'User-Name',
                     'rsso-ep-one-ip-only': 'enable',
                     'rsso-flush-ip-session': 'enable',
                     'rsso-log-flags': 'protocol-error',
                     'rsso-log-period': '21',
                     'rsso-radius-response': 'enable',
                     'rsso-radius-server-port': '23',
                     'rsso-secret': 'test_value_24',
                     'rsso-validate-request-secret': 'enable',
                     'secondary-secret': 'test_value_26',
                     'secondary-server': 'test_value_27',
                     'secret': 'test_value_28',
                     'server': '192.168.100.29',
                     'source-ip': '84.230.14.30',
                     'sso-attribute': 'User-Name',
                     'sso-attribute-key': 'test_value_32',
                     'sso-attribute-value-override': 'enable',
                     'tertiary-secret': 'test_value_34',
                     'tertiary-server': 'test_value_35',
                     'timeout': '36',
                     'use-management-vdom': 'enable',
                     'username-case-sensitive': 'enable'
                     }

    set_method_mock.assert_called_with('user', 'radius', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
