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
    from ansible.modules.network.fortios import fortios_vpn_ipsec_manualkey_interface
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_vpn_ipsec_manualkey_interface.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_vpn_ipsec_manualkey_interface_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ipsec_manualkey_interface': {
            'addr_type': '4',
            'auth_alg': 'null',
            'auth_key': 'test_value_5',
            'enc_alg': 'null',
            'enc_key': 'test_value_7',
            'interface': 'test_value_8',
            'ip_version': '4',
            'local_gw': 'test_value_10',
            'local_gw6': 'test_value_11',
            'local_spi': 'test_value_12',
            'name': 'default_name_13',
            'remote_gw': 'test_value_14',
            'remote_gw6': 'test_value_15',
            'remote_spi': 'test_value_16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_manualkey_interface.fortios_vpn_ipsec(input_data, fos_instance)

    expected_data = {
        'addr-type': '4',
        'auth-alg': 'null',
        'auth-key': 'test_value_5',
        'enc-alg': 'null',
        'enc-key': 'test_value_7',
        'interface': 'test_value_8',
        'ip-version': '4',
        'local-gw': 'test_value_10',
        'local-gw6': 'test_value_11',
        'local-spi': 'test_value_12',
        'name': 'default_name_13',
                'remote-gw': 'test_value_14',
                'remote-gw6': 'test_value_15',
                'remote-spi': 'test_value_16'
    }

    set_method_mock.assert_called_with('vpn.ipsec', 'manualkey-interface', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_vpn_ipsec_manualkey_interface_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ipsec_manualkey_interface': {
            'addr_type': '4',
            'auth_alg': 'null',
            'auth_key': 'test_value_5',
            'enc_alg': 'null',
            'enc_key': 'test_value_7',
            'interface': 'test_value_8',
            'ip_version': '4',
            'local_gw': 'test_value_10',
            'local_gw6': 'test_value_11',
            'local_spi': 'test_value_12',
            'name': 'default_name_13',
            'remote_gw': 'test_value_14',
            'remote_gw6': 'test_value_15',
            'remote_spi': 'test_value_16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_manualkey_interface.fortios_vpn_ipsec(input_data, fos_instance)

    expected_data = {
        'addr-type': '4',
        'auth-alg': 'null',
        'auth-key': 'test_value_5',
        'enc-alg': 'null',
        'enc-key': 'test_value_7',
        'interface': 'test_value_8',
        'ip-version': '4',
        'local-gw': 'test_value_10',
        'local-gw6': 'test_value_11',
        'local-spi': 'test_value_12',
        'name': 'default_name_13',
                'remote-gw': 'test_value_14',
                'remote-gw6': 'test_value_15',
                'remote-spi': 'test_value_16'
    }

    set_method_mock.assert_called_with('vpn.ipsec', 'manualkey-interface', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_vpn_ipsec_manualkey_interface_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'vpn_ipsec_manualkey_interface': {
            'addr_type': '4',
            'auth_alg': 'null',
            'auth_key': 'test_value_5',
            'enc_alg': 'null',
            'enc_key': 'test_value_7',
            'interface': 'test_value_8',
            'ip_version': '4',
            'local_gw': 'test_value_10',
            'local_gw6': 'test_value_11',
            'local_spi': 'test_value_12',
            'name': 'default_name_13',
            'remote_gw': 'test_value_14',
            'remote_gw6': 'test_value_15',
            'remote_spi': 'test_value_16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_manualkey_interface.fortios_vpn_ipsec(input_data, fos_instance)

    delete_method_mock.assert_called_with('vpn.ipsec', 'manualkey-interface', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_vpn_ipsec_manualkey_interface_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'vpn_ipsec_manualkey_interface': {
            'addr_type': '4',
            'auth_alg': 'null',
            'auth_key': 'test_value_5',
            'enc_alg': 'null',
            'enc_key': 'test_value_7',
            'interface': 'test_value_8',
            'ip_version': '4',
            'local_gw': 'test_value_10',
            'local_gw6': 'test_value_11',
            'local_spi': 'test_value_12',
            'name': 'default_name_13',
            'remote_gw': 'test_value_14',
            'remote_gw6': 'test_value_15',
            'remote_spi': 'test_value_16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_manualkey_interface.fortios_vpn_ipsec(input_data, fos_instance)

    delete_method_mock.assert_called_with('vpn.ipsec', 'manualkey-interface', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_vpn_ipsec_manualkey_interface_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ipsec_manualkey_interface': {
            'addr_type': '4',
            'auth_alg': 'null',
            'auth_key': 'test_value_5',
            'enc_alg': 'null',
            'enc_key': 'test_value_7',
            'interface': 'test_value_8',
            'ip_version': '4',
            'local_gw': 'test_value_10',
            'local_gw6': 'test_value_11',
            'local_spi': 'test_value_12',
            'name': 'default_name_13',
            'remote_gw': 'test_value_14',
            'remote_gw6': 'test_value_15',
            'remote_spi': 'test_value_16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_manualkey_interface.fortios_vpn_ipsec(input_data, fos_instance)

    expected_data = {
        'addr-type': '4',
        'auth-alg': 'null',
        'auth-key': 'test_value_5',
        'enc-alg': 'null',
        'enc-key': 'test_value_7',
        'interface': 'test_value_8',
        'ip-version': '4',
        'local-gw': 'test_value_10',
        'local-gw6': 'test_value_11',
        'local-spi': 'test_value_12',
        'name': 'default_name_13',
                'remote-gw': 'test_value_14',
                'remote-gw6': 'test_value_15',
                'remote-spi': 'test_value_16'
    }

    set_method_mock.assert_called_with('vpn.ipsec', 'manualkey-interface', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_vpn_ipsec_manualkey_interface_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ipsec_manualkey_interface': {
            'random_attribute_not_valid': 'tag',
            'addr_type': '4',
            'auth_alg': 'null',
            'auth_key': 'test_value_5',
            'enc_alg': 'null',
            'enc_key': 'test_value_7',
            'interface': 'test_value_8',
            'ip_version': '4',
            'local_gw': 'test_value_10',
            'local_gw6': 'test_value_11',
            'local_spi': 'test_value_12',
            'name': 'default_name_13',
            'remote_gw': 'test_value_14',
            'remote_gw6': 'test_value_15',
            'remote_spi': 'test_value_16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_manualkey_interface.fortios_vpn_ipsec(input_data, fos_instance)

    expected_data = {
        'addr-type': '4',
        'auth-alg': 'null',
        'auth-key': 'test_value_5',
        'enc-alg': 'null',
        'enc-key': 'test_value_7',
        'interface': 'test_value_8',
        'ip-version': '4',
        'local-gw': 'test_value_10',
        'local-gw6': 'test_value_11',
        'local-spi': 'test_value_12',
        'name': 'default_name_13',
                'remote-gw': 'test_value_14',
                'remote-gw6': 'test_value_15',
                'remote-spi': 'test_value_16'
    }

    set_method_mock.assert_called_with('vpn.ipsec', 'manualkey-interface', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
