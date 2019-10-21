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
    from ansible.modules.network.fortios import fortios_system_dhcp6_server
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_system_dhcp6_server.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_system_dhcp6_server_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_dhcp6_server': {
            'dns_search_list': 'delegated',
            'dns_server1': 'test_value_4',
            'dns_server2': 'test_value_5',
            'dns_server3': 'test_value_6',
            'dns_service': 'delegated',
            'domain': 'test_value_8',
            'id': '9',
            'interface': 'test_value_10',
            'ip_mode': 'range',
            'lease_time': '12',
            'option1': 'test_value_13',
            'option2': 'test_value_14',
            'option3': 'test_value_15',
            'rapid_commit': 'disable',
            'status': 'disable',
            'subnet': 'test_value_18',
            'upstream_interface': 'test_value_19'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp6_server.fortios_system_dhcp6(input_data, fos_instance)

    expected_data = {
        'dns-search-list': 'delegated',
        'dns-server1': 'test_value_4',
        'dns-server2': 'test_value_5',
        'dns-server3': 'test_value_6',
        'dns-service': 'delegated',
        'domain': 'test_value_8',
        'id': '9',
        'interface': 'test_value_10',
        'ip-mode': 'range',
        'lease-time': '12',
        'option1': 'test_value_13',
        'option2': 'test_value_14',
        'option3': 'test_value_15',
        'rapid-commit': 'disable',
        'status': 'disable',
        'subnet': 'test_value_18',
        'upstream-interface': 'test_value_19'
    }

    set_method_mock.assert_called_with('system.dhcp6', 'server', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_dhcp6_server_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_dhcp6_server': {
            'dns_search_list': 'delegated',
            'dns_server1': 'test_value_4',
            'dns_server2': 'test_value_5',
            'dns_server3': 'test_value_6',
            'dns_service': 'delegated',
            'domain': 'test_value_8',
            'id': '9',
            'interface': 'test_value_10',
            'ip_mode': 'range',
            'lease_time': '12',
            'option1': 'test_value_13',
            'option2': 'test_value_14',
            'option3': 'test_value_15',
            'rapid_commit': 'disable',
            'status': 'disable',
            'subnet': 'test_value_18',
            'upstream_interface': 'test_value_19'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp6_server.fortios_system_dhcp6(input_data, fos_instance)

    expected_data = {
        'dns-search-list': 'delegated',
        'dns-server1': 'test_value_4',
        'dns-server2': 'test_value_5',
        'dns-server3': 'test_value_6',
        'dns-service': 'delegated',
        'domain': 'test_value_8',
        'id': '9',
        'interface': 'test_value_10',
        'ip-mode': 'range',
        'lease-time': '12',
        'option1': 'test_value_13',
        'option2': 'test_value_14',
        'option3': 'test_value_15',
        'rapid-commit': 'disable',
        'status': 'disable',
        'subnet': 'test_value_18',
        'upstream-interface': 'test_value_19'
    }

    set_method_mock.assert_called_with('system.dhcp6', 'server', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_dhcp6_server_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'system_dhcp6_server': {
            'dns_search_list': 'delegated',
            'dns_server1': 'test_value_4',
            'dns_server2': 'test_value_5',
            'dns_server3': 'test_value_6',
            'dns_service': 'delegated',
            'domain': 'test_value_8',
            'id': '9',
            'interface': 'test_value_10',
            'ip_mode': 'range',
            'lease_time': '12',
            'option1': 'test_value_13',
            'option2': 'test_value_14',
            'option3': 'test_value_15',
            'rapid_commit': 'disable',
            'status': 'disable',
            'subnet': 'test_value_18',
            'upstream_interface': 'test_value_19'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp6_server.fortios_system_dhcp6(input_data, fos_instance)

    delete_method_mock.assert_called_with('system.dhcp6', 'server', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_dhcp6_server_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'system_dhcp6_server': {
            'dns_search_list': 'delegated',
            'dns_server1': 'test_value_4',
            'dns_server2': 'test_value_5',
            'dns_server3': 'test_value_6',
            'dns_service': 'delegated',
            'domain': 'test_value_8',
            'id': '9',
            'interface': 'test_value_10',
            'ip_mode': 'range',
            'lease_time': '12',
            'option1': 'test_value_13',
            'option2': 'test_value_14',
            'option3': 'test_value_15',
            'rapid_commit': 'disable',
            'status': 'disable',
            'subnet': 'test_value_18',
            'upstream_interface': 'test_value_19'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp6_server.fortios_system_dhcp6(input_data, fos_instance)

    delete_method_mock.assert_called_with('system.dhcp6', 'server', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_dhcp6_server_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_dhcp6_server': {
            'dns_search_list': 'delegated',
            'dns_server1': 'test_value_4',
            'dns_server2': 'test_value_5',
            'dns_server3': 'test_value_6',
            'dns_service': 'delegated',
            'domain': 'test_value_8',
            'id': '9',
            'interface': 'test_value_10',
            'ip_mode': 'range',
            'lease_time': '12',
            'option1': 'test_value_13',
            'option2': 'test_value_14',
            'option3': 'test_value_15',
            'rapid_commit': 'disable',
            'status': 'disable',
            'subnet': 'test_value_18',
            'upstream_interface': 'test_value_19'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp6_server.fortios_system_dhcp6(input_data, fos_instance)

    expected_data = {
        'dns-search-list': 'delegated',
        'dns-server1': 'test_value_4',
        'dns-server2': 'test_value_5',
        'dns-server3': 'test_value_6',
        'dns-service': 'delegated',
        'domain': 'test_value_8',
        'id': '9',
        'interface': 'test_value_10',
        'ip-mode': 'range',
        'lease-time': '12',
        'option1': 'test_value_13',
        'option2': 'test_value_14',
        'option3': 'test_value_15',
        'rapid-commit': 'disable',
        'status': 'disable',
        'subnet': 'test_value_18',
        'upstream-interface': 'test_value_19'
    }

    set_method_mock.assert_called_with('system.dhcp6', 'server', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_system_dhcp6_server_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_dhcp6_server': {
            'random_attribute_not_valid': 'tag',
            'dns_search_list': 'delegated',
            'dns_server1': 'test_value_4',
            'dns_server2': 'test_value_5',
            'dns_server3': 'test_value_6',
            'dns_service': 'delegated',
            'domain': 'test_value_8',
            'id': '9',
            'interface': 'test_value_10',
            'ip_mode': 'range',
            'lease_time': '12',
            'option1': 'test_value_13',
            'option2': 'test_value_14',
            'option3': 'test_value_15',
            'rapid_commit': 'disable',
            'status': 'disable',
            'subnet': 'test_value_18',
            'upstream_interface': 'test_value_19'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_dhcp6_server.fortios_system_dhcp6(input_data, fos_instance)

    expected_data = {
        'dns-search-list': 'delegated',
        'dns-server1': 'test_value_4',
        'dns-server2': 'test_value_5',
        'dns-server3': 'test_value_6',
        'dns-service': 'delegated',
        'domain': 'test_value_8',
        'id': '9',
        'interface': 'test_value_10',
        'ip-mode': 'range',
        'lease-time': '12',
        'option1': 'test_value_13',
        'option2': 'test_value_14',
        'option3': 'test_value_15',
        'rapid-commit': 'disable',
        'status': 'disable',
        'subnet': 'test_value_18',
        'upstream-interface': 'test_value_19'
    }

    set_method_mock.assert_called_with('system.dhcp6', 'server', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
