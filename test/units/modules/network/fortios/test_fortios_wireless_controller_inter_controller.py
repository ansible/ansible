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
    from ansible.modules.network.fortios import fortios_wireless_controller_inter_controller
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_inter_controller.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_inter_controller_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_inter_controller': {
            'fast_failover_max': '3',
            'fast_failover_wait': '4',
            'inter_controller_key': 'test_value_5',
            'inter_controller_mode': 'disable',
            'inter_controller_pri': 'primary'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_inter_controller.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'fast-failover-max': '3',
        'fast-failover-wait': '4',
        'inter-controller-key': 'test_value_5',
        'inter-controller-mode': 'disable',
        'inter-controller-pri': 'primary'
    }

    set_method_mock.assert_called_with('wireless-controller', 'inter-controller', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_inter_controller_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_inter_controller': {
            'fast_failover_max': '3',
            'fast_failover_wait': '4',
            'inter_controller_key': 'test_value_5',
            'inter_controller_mode': 'disable',
            'inter_controller_pri': 'primary'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_inter_controller.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'fast-failover-max': '3',
        'fast-failover-wait': '4',
        'inter-controller-key': 'test_value_5',
        'inter-controller-mode': 'disable',
        'inter-controller-pri': 'primary'
    }

    set_method_mock.assert_called_with('wireless-controller', 'inter-controller', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_inter_controller_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_inter_controller': {
            'fast_failover_max': '3',
            'fast_failover_wait': '4',
            'inter_controller_key': 'test_value_5',
            'inter_controller_mode': 'disable',
            'inter_controller_pri': 'primary'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_inter_controller.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'fast-failover-max': '3',
        'fast-failover-wait': '4',
        'inter-controller-key': 'test_value_5',
        'inter-controller-mode': 'disable',
        'inter-controller-pri': 'primary'
    }

    set_method_mock.assert_called_with('wireless-controller', 'inter-controller', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_inter_controller_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_inter_controller': {
            'random_attribute_not_valid': 'tag',
            'fast_failover_max': '3',
            'fast_failover_wait': '4',
            'inter_controller_key': 'test_value_5',
            'inter_controller_mode': 'disable',
            'inter_controller_pri': 'primary'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_inter_controller.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'fast-failover-max': '3',
        'fast-failover-wait': '4',
        'inter-controller-key': 'test_value_5',
        'inter-controller-mode': 'disable',
        'inter-controller-pri': 'primary'
    }

    set_method_mock.assert_called_with('wireless-controller', 'inter-controller', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
