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
    from ansible.modules.network.fortios import fortios_user_fsso
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_user_fsso.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_user_fsso_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_fsso': {
            'ldap_server': 'test_value_3',
            'name': 'default_name_4',
            'password': 'test_value_5',
            'password2': 'test_value_6',
            'password3': 'test_value_7',
            'password4': 'test_value_8',
            'password5': 'test_value_9',
            'port': '10',
            'port2': '11',
            'port3': '12',
            'port4': '13',
            'port5': '14',
            'server': '192.168.100.15',
            'server2': 'test_value_16',
            'server3': 'test_value_17',
            'server4': 'test_value_18',
            'server5': 'test_value_19',
            'source_ip': '84.230.14.20',
            'source_ip6': 'test_value_21'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_fsso.fortios_user(input_data, fos_instance)

    expected_data = {
        'ldap-server': 'test_value_3',
        'name': 'default_name_4',
                'password': 'test_value_5',
                'password2': 'test_value_6',
                'password3': 'test_value_7',
                'password4': 'test_value_8',
                'password5': 'test_value_9',
                'port': '10',
                'port2': '11',
                'port3': '12',
                'port4': '13',
                'port5': '14',
                'server': '192.168.100.15',
                'server2': 'test_value_16',
                'server3': 'test_value_17',
                'server4': 'test_value_18',
                'server5': 'test_value_19',
                'source-ip': '84.230.14.20',
                'source-ip6': 'test_value_21'
    }

    set_method_mock.assert_called_with('user', 'fsso', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_user_fsso_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_fsso': {
            'ldap_server': 'test_value_3',
            'name': 'default_name_4',
            'password': 'test_value_5',
            'password2': 'test_value_6',
            'password3': 'test_value_7',
            'password4': 'test_value_8',
            'password5': 'test_value_9',
            'port': '10',
            'port2': '11',
            'port3': '12',
            'port4': '13',
            'port5': '14',
            'server': '192.168.100.15',
            'server2': 'test_value_16',
            'server3': 'test_value_17',
            'server4': 'test_value_18',
            'server5': 'test_value_19',
            'source_ip': '84.230.14.20',
            'source_ip6': 'test_value_21'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_fsso.fortios_user(input_data, fos_instance)

    expected_data = {
        'ldap-server': 'test_value_3',
        'name': 'default_name_4',
                'password': 'test_value_5',
                'password2': 'test_value_6',
                'password3': 'test_value_7',
                'password4': 'test_value_8',
                'password5': 'test_value_9',
                'port': '10',
                'port2': '11',
                'port3': '12',
                'port4': '13',
                'port5': '14',
                'server': '192.168.100.15',
                'server2': 'test_value_16',
                'server3': 'test_value_17',
                'server4': 'test_value_18',
                'server5': 'test_value_19',
                'source-ip': '84.230.14.20',
                'source-ip6': 'test_value_21'
    }

    set_method_mock.assert_called_with('user', 'fsso', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_user_fsso_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'user_fsso': {
            'ldap_server': 'test_value_3',
            'name': 'default_name_4',
            'password': 'test_value_5',
            'password2': 'test_value_6',
            'password3': 'test_value_7',
            'password4': 'test_value_8',
            'password5': 'test_value_9',
            'port': '10',
            'port2': '11',
            'port3': '12',
            'port4': '13',
            'port5': '14',
            'server': '192.168.100.15',
            'server2': 'test_value_16',
            'server3': 'test_value_17',
            'server4': 'test_value_18',
            'server5': 'test_value_19',
            'source_ip': '84.230.14.20',
            'source_ip6': 'test_value_21'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_fsso.fortios_user(input_data, fos_instance)

    delete_method_mock.assert_called_with('user', 'fsso', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_user_fsso_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'user_fsso': {
            'ldap_server': 'test_value_3',
            'name': 'default_name_4',
            'password': 'test_value_5',
            'password2': 'test_value_6',
            'password3': 'test_value_7',
            'password4': 'test_value_8',
            'password5': 'test_value_9',
            'port': '10',
            'port2': '11',
            'port3': '12',
            'port4': '13',
            'port5': '14',
            'server': '192.168.100.15',
            'server2': 'test_value_16',
            'server3': 'test_value_17',
            'server4': 'test_value_18',
            'server5': 'test_value_19',
            'source_ip': '84.230.14.20',
            'source_ip6': 'test_value_21'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_fsso.fortios_user(input_data, fos_instance)

    delete_method_mock.assert_called_with('user', 'fsso', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_user_fsso_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_fsso': {
            'ldap_server': 'test_value_3',
            'name': 'default_name_4',
            'password': 'test_value_5',
            'password2': 'test_value_6',
            'password3': 'test_value_7',
            'password4': 'test_value_8',
            'password5': 'test_value_9',
            'port': '10',
            'port2': '11',
            'port3': '12',
            'port4': '13',
            'port5': '14',
            'server': '192.168.100.15',
            'server2': 'test_value_16',
            'server3': 'test_value_17',
            'server4': 'test_value_18',
            'server5': 'test_value_19',
            'source_ip': '84.230.14.20',
            'source_ip6': 'test_value_21'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_fsso.fortios_user(input_data, fos_instance)

    expected_data = {
        'ldap-server': 'test_value_3',
        'name': 'default_name_4',
                'password': 'test_value_5',
                'password2': 'test_value_6',
                'password3': 'test_value_7',
                'password4': 'test_value_8',
                'password5': 'test_value_9',
                'port': '10',
                'port2': '11',
                'port3': '12',
                'port4': '13',
                'port5': '14',
                'server': '192.168.100.15',
                'server2': 'test_value_16',
                'server3': 'test_value_17',
                'server4': 'test_value_18',
                'server5': 'test_value_19',
                'source-ip': '84.230.14.20',
                'source-ip6': 'test_value_21'
    }

    set_method_mock.assert_called_with('user', 'fsso', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_user_fsso_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'user_fsso': {
            'random_attribute_not_valid': 'tag',
            'ldap_server': 'test_value_3',
            'name': 'default_name_4',
            'password': 'test_value_5',
            'password2': 'test_value_6',
            'password3': 'test_value_7',
            'password4': 'test_value_8',
            'password5': 'test_value_9',
            'port': '10',
            'port2': '11',
            'port3': '12',
            'port4': '13',
            'port5': '14',
            'server': '192.168.100.15',
            'server2': 'test_value_16',
            'server3': 'test_value_17',
            'server4': 'test_value_18',
            'server5': 'test_value_19',
            'source_ip': '84.230.14.20',
            'source_ip6': 'test_value_21'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_user_fsso.fortios_user(input_data, fos_instance)

    expected_data = {
        'ldap-server': 'test_value_3',
        'name': 'default_name_4',
                'password': 'test_value_5',
                'password2': 'test_value_6',
                'password3': 'test_value_7',
                'password4': 'test_value_8',
                'password5': 'test_value_9',
                'port': '10',
                'port2': '11',
                'port3': '12',
                'port4': '13',
                'port5': '14',
                'server': '192.168.100.15',
                'server2': 'test_value_16',
                'server3': 'test_value_17',
                'server4': 'test_value_18',
                'server5': 'test_value_19',
                'source-ip': '84.230.14.20',
                'source-ip6': 'test_value_21'
    }

    set_method_mock.assert_called_with('user', 'fsso', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
