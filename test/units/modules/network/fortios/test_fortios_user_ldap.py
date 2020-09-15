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
    from ansible.modules.network.fortios import fortios_user_ldap
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_user_ldap.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_user_ldap_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_ldap': {
            'account_key_filter': 'test_value_3',
            'account_key_processing': 'same',
            'ca_cert': 'test_value_5',
            'cnid': 'test_value_6',
            'dn': 'test_value_7',
            'group_filter': 'test_value_8',
            'group_member_check': 'user-attr',
            'group_object_filter': 'test_value_10',
            'group_search_base': 'test_value_11',
            'member_attr': 'test_value_12',
            'name': 'default_name_13',
            'password': 'test_value_14',
            'password_expiry_warning': 'enable',
            'password_renewal': 'enable',
            'port': '17',
            'secondary_server': 'test_value_18',
            'secure': 'disable',
            'server': '192.168.100.20',
            'server_identity_check': 'enable',
            'source_ip': '84.230.14.22',
            'ssl_min_proto_version': 'default',
            'tertiary_server': 'test_value_24',
            'type': 'simple',
            'username': 'test_value_26'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_ldap.fortios_user(input_data, fos_instance)

    expected_data = {
        'account-key-filter': 'test_value_3',
        'account-key-processing': 'same',
        'ca-cert': 'test_value_5',
        'cnid': 'test_value_6',
                'dn': 'test_value_7',
                'group-filter': 'test_value_8',
                'group-member-check': 'user-attr',
                'group-object-filter': 'test_value_10',
                'group-search-base': 'test_value_11',
                'member-attr': 'test_value_12',
                'name': 'default_name_13',
                'password': 'test_value_14',
                'password-expiry-warning': 'enable',
                'password-renewal': 'enable',
                'port': '17',
                'secondary-server': 'test_value_18',
                'secure': 'disable',
                'server': '192.168.100.20',
                'server-identity-check': 'enable',
                'source-ip': '84.230.14.22',
                'ssl-min-proto-version': 'default',
                'tertiary-server': 'test_value_24',
                'type': 'simple',
                'username': 'test_value_26'
    }

    set_method_mock.assert_called_with('user', 'ldap', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_user_ldap_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_ldap': {
            'account_key_filter': 'test_value_3',
            'account_key_processing': 'same',
            'ca_cert': 'test_value_5',
            'cnid': 'test_value_6',
            'dn': 'test_value_7',
            'group_filter': 'test_value_8',
            'group_member_check': 'user-attr',
            'group_object_filter': 'test_value_10',
            'group_search_base': 'test_value_11',
            'member_attr': 'test_value_12',
            'name': 'default_name_13',
            'password': 'test_value_14',
            'password_expiry_warning': 'enable',
            'password_renewal': 'enable',
            'port': '17',
            'secondary_server': 'test_value_18',
            'secure': 'disable',
            'server': '192.168.100.20',
            'server_identity_check': 'enable',
            'source_ip': '84.230.14.22',
            'ssl_min_proto_version': 'default',
            'tertiary_server': 'test_value_24',
            'type': 'simple',
            'username': 'test_value_26'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_ldap.fortios_user(input_data, fos_instance)

    expected_data = {
        'account-key-filter': 'test_value_3',
        'account-key-processing': 'same',
        'ca-cert': 'test_value_5',
        'cnid': 'test_value_6',
                'dn': 'test_value_7',
                'group-filter': 'test_value_8',
                'group-member-check': 'user-attr',
                'group-object-filter': 'test_value_10',
                'group-search-base': 'test_value_11',
                'member-attr': 'test_value_12',
                'name': 'default_name_13',
                'password': 'test_value_14',
                'password-expiry-warning': 'enable',
                'password-renewal': 'enable',
                'port': '17',
                'secondary-server': 'test_value_18',
                'secure': 'disable',
                'server': '192.168.100.20',
                'server-identity-check': 'enable',
                'source-ip': '84.230.14.22',
                'ssl-min-proto-version': 'default',
                'tertiary-server': 'test_value_24',
                'type': 'simple',
                'username': 'test_value_26'
    }

    set_method_mock.assert_called_with('user', 'ldap', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_user_ldap_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'user_ldap': {
            'account_key_filter': 'test_value_3',
            'account_key_processing': 'same',
            'ca_cert': 'test_value_5',
            'cnid': 'test_value_6',
            'dn': 'test_value_7',
            'group_filter': 'test_value_8',
            'group_member_check': 'user-attr',
            'group_object_filter': 'test_value_10',
            'group_search_base': 'test_value_11',
            'member_attr': 'test_value_12',
            'name': 'default_name_13',
            'password': 'test_value_14',
            'password_expiry_warning': 'enable',
            'password_renewal': 'enable',
            'port': '17',
            'secondary_server': 'test_value_18',
            'secure': 'disable',
            'server': '192.168.100.20',
            'server_identity_check': 'enable',
            'source_ip': '84.230.14.22',
            'ssl_min_proto_version': 'default',
            'tertiary_server': 'test_value_24',
            'type': 'simple',
            'username': 'test_value_26'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_ldap.fortios_user(input_data, fos_instance)

    delete_method_mock.assert_called_with('user', 'ldap', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_user_ldap_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'user_ldap': {
            'account_key_filter': 'test_value_3',
            'account_key_processing': 'same',
            'ca_cert': 'test_value_5',
            'cnid': 'test_value_6',
            'dn': 'test_value_7',
            'group_filter': 'test_value_8',
            'group_member_check': 'user-attr',
            'group_object_filter': 'test_value_10',
            'group_search_base': 'test_value_11',
            'member_attr': 'test_value_12',
            'name': 'default_name_13',
            'password': 'test_value_14',
            'password_expiry_warning': 'enable',
            'password_renewal': 'enable',
            'port': '17',
            'secondary_server': 'test_value_18',
            'secure': 'disable',
            'server': '192.168.100.20',
            'server_identity_check': 'enable',
            'source_ip': '84.230.14.22',
            'ssl_min_proto_version': 'default',
            'tertiary_server': 'test_value_24',
            'type': 'simple',
            'username': 'test_value_26'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_ldap.fortios_user(input_data, fos_instance)

    delete_method_mock.assert_called_with('user', 'ldap', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_user_ldap_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_ldap': {
            'account_key_filter': 'test_value_3',
            'account_key_processing': 'same',
            'ca_cert': 'test_value_5',
            'cnid': 'test_value_6',
            'dn': 'test_value_7',
            'group_filter': 'test_value_8',
            'group_member_check': 'user-attr',
            'group_object_filter': 'test_value_10',
            'group_search_base': 'test_value_11',
            'member_attr': 'test_value_12',
            'name': 'default_name_13',
            'password': 'test_value_14',
            'password_expiry_warning': 'enable',
            'password_renewal': 'enable',
            'port': '17',
            'secondary_server': 'test_value_18',
            'secure': 'disable',
            'server': '192.168.100.20',
            'server_identity_check': 'enable',
            'source_ip': '84.230.14.22',
            'ssl_min_proto_version': 'default',
            'tertiary_server': 'test_value_24',
            'type': 'simple',
            'username': 'test_value_26'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_ldap.fortios_user(input_data, fos_instance)

    expected_data = {
        'account-key-filter': 'test_value_3',
        'account-key-processing': 'same',
        'ca-cert': 'test_value_5',
        'cnid': 'test_value_6',
                'dn': 'test_value_7',
                'group-filter': 'test_value_8',
                'group-member-check': 'user-attr',
                'group-object-filter': 'test_value_10',
                'group-search-base': 'test_value_11',
                'member-attr': 'test_value_12',
                'name': 'default_name_13',
                'password': 'test_value_14',
                'password-expiry-warning': 'enable',
                'password-renewal': 'enable',
                'port': '17',
                'secondary-server': 'test_value_18',
                'secure': 'disable',
                'server': '192.168.100.20',
                'server-identity-check': 'enable',
                'source-ip': '84.230.14.22',
                'ssl-min-proto-version': 'default',
                'tertiary-server': 'test_value_24',
                'type': 'simple',
                'username': 'test_value_26'
    }

    set_method_mock.assert_called_with('user', 'ldap', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_user_ldap_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_ldap': {
            'random_attribute_not_valid': 'tag',
            'account_key_filter': 'test_value_3',
            'account_key_processing': 'same',
            'ca_cert': 'test_value_5',
            'cnid': 'test_value_6',
            'dn': 'test_value_7',
            'group_filter': 'test_value_8',
            'group_member_check': 'user-attr',
            'group_object_filter': 'test_value_10',
            'group_search_base': 'test_value_11',
            'member_attr': 'test_value_12',
            'name': 'default_name_13',
            'password': 'test_value_14',
            'password_expiry_warning': 'enable',
            'password_renewal': 'enable',
            'port': '17',
            'secondary_server': 'test_value_18',
            'secure': 'disable',
            'server': '192.168.100.20',
            'server_identity_check': 'enable',
            'source_ip': '84.230.14.22',
            'ssl_min_proto_version': 'default',
            'tertiary_server': 'test_value_24',
            'type': 'simple',
            'username': 'test_value_26'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_ldap.fortios_user(input_data, fos_instance)

    expected_data = {
        'account-key-filter': 'test_value_3',
        'account-key-processing': 'same',
        'ca-cert': 'test_value_5',
        'cnid': 'test_value_6',
                'dn': 'test_value_7',
                'group-filter': 'test_value_8',
                'group-member-check': 'user-attr',
                'group-object-filter': 'test_value_10',
                'group-search-base': 'test_value_11',
                'member-attr': 'test_value_12',
                'name': 'default_name_13',
                'password': 'test_value_14',
                'password-expiry-warning': 'enable',
                'password-renewal': 'enable',
                'port': '17',
                'secondary-server': 'test_value_18',
                'secure': 'disable',
                'server': '192.168.100.20',
                'server-identity-check': 'enable',
                'source-ip': '84.230.14.22',
                'ssl-min-proto-version': 'default',
                'tertiary-server': 'test_value_24',
                'type': 'simple',
                'username': 'test_value_26'
    }

    set_method_mock.assert_called_with('user', 'ldap', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
