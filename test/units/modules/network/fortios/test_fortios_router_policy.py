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
    from ansible.modules.network.fortios import fortios_router_policy
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_router_policy.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_router_policy_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_policy': {
            'action': 'deny',
            'comments': 'test_value_4',
            'dst_negate': 'enable',
            'end_port': '6',
            'end_source_port': '7',
            'gateway': 'test_value_8',
            'output_device': 'test_value_9',
            'protocol': '10',
            'seq_num': '11',
            'src_negate': 'enable',
            'start_port': '13',
            'start_source_port': '14',
            'status': 'enable',
            'tos': 'test_value_16',
            'tos_mask': 'test_value_17'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_policy.fortios_router(input_data, fos_instance)

    expected_data = {
        'action': 'deny',
        'comments': 'test_value_4',
        'dst-negate': 'enable',
        'end-port': '6',
        'end-source-port': '7',
        'gateway': 'test_value_8',
        'output-device': 'test_value_9',
        'protocol': '10',
        'seq-num': '11',
        'src-negate': 'enable',
        'start-port': '13',
        'start-source-port': '14',
        'status': 'enable',
        'tos': 'test_value_16',
        'tos-mask': 'test_value_17'
    }

    set_method_mock.assert_called_with('router', 'policy', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_router_policy_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_policy': {
            'action': 'deny',
            'comments': 'test_value_4',
            'dst_negate': 'enable',
            'end_port': '6',
            'end_source_port': '7',
            'gateway': 'test_value_8',
            'output_device': 'test_value_9',
            'protocol': '10',
            'seq_num': '11',
            'src_negate': 'enable',
            'start_port': '13',
            'start_source_port': '14',
            'status': 'enable',
            'tos': 'test_value_16',
            'tos_mask': 'test_value_17'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_policy.fortios_router(input_data, fos_instance)

    expected_data = {
        'action': 'deny',
        'comments': 'test_value_4',
        'dst-negate': 'enable',
        'end-port': '6',
        'end-source-port': '7',
        'gateway': 'test_value_8',
        'output-device': 'test_value_9',
        'protocol': '10',
        'seq-num': '11',
        'src-negate': 'enable',
        'start-port': '13',
        'start-source-port': '14',
        'status': 'enable',
        'tos': 'test_value_16',
        'tos-mask': 'test_value_17'
    }

    set_method_mock.assert_called_with('router', 'policy', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_router_policy_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'router_policy': {
            'action': 'deny',
            'comments': 'test_value_4',
            'dst_negate': 'enable',
            'end_port': '6',
            'end_source_port': '7',
            'gateway': 'test_value_8',
            'output_device': 'test_value_9',
            'protocol': '10',
            'seq_num': '11',
            'src_negate': 'enable',
            'start_port': '13',
            'start_source_port': '14',
            'status': 'enable',
            'tos': 'test_value_16',
            'tos_mask': 'test_value_17'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_policy.fortios_router(input_data, fos_instance)

    delete_method_mock.assert_called_with('router', 'policy', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_router_policy_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'router_policy': {
            'action': 'deny',
            'comments': 'test_value_4',
            'dst_negate': 'enable',
            'end_port': '6',
            'end_source_port': '7',
            'gateway': 'test_value_8',
            'output_device': 'test_value_9',
            'protocol': '10',
            'seq_num': '11',
            'src_negate': 'enable',
            'start_port': '13',
            'start_source_port': '14',
            'status': 'enable',
            'tos': 'test_value_16',
            'tos_mask': 'test_value_17'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_policy.fortios_router(input_data, fos_instance)

    delete_method_mock.assert_called_with('router', 'policy', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_router_policy_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_policy': {
            'action': 'deny',
            'comments': 'test_value_4',
            'dst_negate': 'enable',
            'end_port': '6',
            'end_source_port': '7',
            'gateway': 'test_value_8',
            'output_device': 'test_value_9',
            'protocol': '10',
            'seq_num': '11',
            'src_negate': 'enable',
            'start_port': '13',
            'start_source_port': '14',
            'status': 'enable',
            'tos': 'test_value_16',
            'tos_mask': 'test_value_17'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_policy.fortios_router(input_data, fos_instance)

    expected_data = {
        'action': 'deny',
        'comments': 'test_value_4',
        'dst-negate': 'enable',
        'end-port': '6',
        'end-source-port': '7',
        'gateway': 'test_value_8',
        'output-device': 'test_value_9',
        'protocol': '10',
        'seq-num': '11',
        'src-negate': 'enable',
        'start-port': '13',
        'start-source-port': '14',
        'status': 'enable',
        'tos': 'test_value_16',
        'tos-mask': 'test_value_17'
    }

    set_method_mock.assert_called_with('router', 'policy', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_router_policy_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_policy': {
            'random_attribute_not_valid': 'tag',
            'action': 'deny',
            'comments': 'test_value_4',
            'dst_negate': 'enable',
            'end_port': '6',
            'end_source_port': '7',
            'gateway': 'test_value_8',
            'output_device': 'test_value_9',
            'protocol': '10',
            'seq_num': '11',
            'src_negate': 'enable',
            'start_port': '13',
            'start_source_port': '14',
            'status': 'enable',
            'tos': 'test_value_16',
            'tos_mask': 'test_value_17'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_policy.fortios_router(input_data, fos_instance)

    expected_data = {
        'action': 'deny',
        'comments': 'test_value_4',
        'dst-negate': 'enable',
        'end-port': '6',
        'end-source-port': '7',
        'gateway': 'test_value_8',
        'output-device': 'test_value_9',
        'protocol': '10',
        'seq-num': '11',
        'src-negate': 'enable',
        'start-port': '13',
        'start-source-port': '14',
        'status': 'enable',
        'tos': 'test_value_16',
        'tos-mask': 'test_value_17'
    }

    set_method_mock.assert_called_with('router', 'policy', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
