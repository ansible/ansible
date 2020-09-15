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
    from ansible.modules.network.fortios import fortios_firewall_ippool
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_firewall_ippool.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_firewall_ippool_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_ippool': {
            'arp_intf': 'test_value_3',
            'arp_reply': 'disable',
            'associated_interface': 'test_value_5',
            'block_size': '6',
            'comments': 'test_value_7',
            'endip': 'test_value_8',
            'name': 'default_name_9',
            'num_blocks_per_user': '10',
            'pba_timeout': '11',
            'permit_any_host': 'disable',
            'source_endip': 'test_value_13',
            'source_startip': 'test_value_14',
            'startip': 'test_value_15',
            'type': 'overload'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ippool.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'arp-intf': 'test_value_3',
        'arp-reply': 'disable',
        'associated-interface': 'test_value_5',
        'block-size': '6',
        'comments': 'test_value_7',
        'endip': 'test_value_8',
        'name': 'default_name_9',
                'num-blocks-per-user': '10',
                'pba-timeout': '11',
                'permit-any-host': 'disable',
                'source-endip': 'test_value_13',
                'source-startip': 'test_value_14',
                'startip': 'test_value_15',
                'type': 'overload'
    }

    set_method_mock.assert_called_with('firewall', 'ippool', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_ippool_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_ippool': {
            'arp_intf': 'test_value_3',
            'arp_reply': 'disable',
            'associated_interface': 'test_value_5',
            'block_size': '6',
            'comments': 'test_value_7',
            'endip': 'test_value_8',
            'name': 'default_name_9',
            'num_blocks_per_user': '10',
            'pba_timeout': '11',
            'permit_any_host': 'disable',
            'source_endip': 'test_value_13',
            'source_startip': 'test_value_14',
            'startip': 'test_value_15',
            'type': 'overload'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ippool.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'arp-intf': 'test_value_3',
        'arp-reply': 'disable',
        'associated-interface': 'test_value_5',
        'block-size': '6',
        'comments': 'test_value_7',
        'endip': 'test_value_8',
        'name': 'default_name_9',
                'num-blocks-per-user': '10',
                'pba-timeout': '11',
                'permit-any-host': 'disable',
                'source-endip': 'test_value_13',
                'source-startip': 'test_value_14',
                'startip': 'test_value_15',
                'type': 'overload'
    }

    set_method_mock.assert_called_with('firewall', 'ippool', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_ippool_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_ippool': {
            'arp_intf': 'test_value_3',
            'arp_reply': 'disable',
            'associated_interface': 'test_value_5',
            'block_size': '6',
            'comments': 'test_value_7',
            'endip': 'test_value_8',
            'name': 'default_name_9',
            'num_blocks_per_user': '10',
            'pba_timeout': '11',
            'permit_any_host': 'disable',
            'source_endip': 'test_value_13',
            'source_startip': 'test_value_14',
            'startip': 'test_value_15',
            'type': 'overload'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ippool.fortios_firewall(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall', 'ippool', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_ippool_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_ippool': {
            'arp_intf': 'test_value_3',
            'arp_reply': 'disable',
            'associated_interface': 'test_value_5',
            'block_size': '6',
            'comments': 'test_value_7',
            'endip': 'test_value_8',
            'name': 'default_name_9',
            'num_blocks_per_user': '10',
            'pba_timeout': '11',
            'permit_any_host': 'disable',
            'source_endip': 'test_value_13',
            'source_startip': 'test_value_14',
            'startip': 'test_value_15',
            'type': 'overload'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ippool.fortios_firewall(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall', 'ippool', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_ippool_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_ippool': {
            'arp_intf': 'test_value_3',
            'arp_reply': 'disable',
            'associated_interface': 'test_value_5',
            'block_size': '6',
            'comments': 'test_value_7',
            'endip': 'test_value_8',
            'name': 'default_name_9',
            'num_blocks_per_user': '10',
            'pba_timeout': '11',
            'permit_any_host': 'disable',
            'source_endip': 'test_value_13',
            'source_startip': 'test_value_14',
            'startip': 'test_value_15',
            'type': 'overload'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ippool.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'arp-intf': 'test_value_3',
        'arp-reply': 'disable',
        'associated-interface': 'test_value_5',
        'block-size': '6',
        'comments': 'test_value_7',
        'endip': 'test_value_8',
        'name': 'default_name_9',
                'num-blocks-per-user': '10',
                'pba-timeout': '11',
                'permit-any-host': 'disable',
                'source-endip': 'test_value_13',
                'source-startip': 'test_value_14',
                'startip': 'test_value_15',
                'type': 'overload'
    }

    set_method_mock.assert_called_with('firewall', 'ippool', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_firewall_ippool_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_ippool': {
            'random_attribute_not_valid': 'tag',
            'arp_intf': 'test_value_3',
            'arp_reply': 'disable',
            'associated_interface': 'test_value_5',
            'block_size': '6',
            'comments': 'test_value_7',
            'endip': 'test_value_8',
            'name': 'default_name_9',
            'num_blocks_per_user': '10',
            'pba_timeout': '11',
            'permit_any_host': 'disable',
            'source_endip': 'test_value_13',
            'source_startip': 'test_value_14',
            'startip': 'test_value_15',
            'type': 'overload'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ippool.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'arp-intf': 'test_value_3',
        'arp-reply': 'disable',
        'associated-interface': 'test_value_5',
        'block-size': '6',
        'comments': 'test_value_7',
        'endip': 'test_value_8',
        'name': 'default_name_9',
                'num-blocks-per-user': '10',
                'pba-timeout': '11',
                'permit-any-host': 'disable',
                'source-endip': 'test_value_13',
                'source-startip': 'test_value_14',
                'startip': 'test_value_15',
                'type': 'overload'
    }

    set_method_mock.assert_called_with('firewall', 'ippool', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
