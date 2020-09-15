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
    from ansible.modules.network.fortios import fortios_system_sdn_connector
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_system_sdn_connector.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_system_sdn_connector_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_sdn_connector': {
            'access_key': 'test_value_3',
            'azure_region': 'global',
            'client_id': 'test_value_5',
            'client_secret': 'test_value_6',
            'compartment_id': 'test_value_7',
            'gcp_project': 'test_value_8',
            'key_passwd': 'test_value_9',
            'login_endpoint': 'test_value_10',
            'name': 'default_name_11',
            'oci_cert': 'test_value_12',
            'oci_fingerprint': 'test_value_13',
            'oci_region': 'phoenix',
            'password': 'test_value_15',
            'private_key': 'test_value_16',
            'region': 'test_value_17',
            'resource_group': 'test_value_18',
            'resource_url': 'test_value_19',
            'secret_key': 'test_value_20',
            'server': '192.168.100.21',
            'server_port': '22',
            'service_account': 'test_value_23',
            'status': 'disable',
            'subscription_id': 'test_value_25',
            'tenant_id': 'test_value_26',
            'type': 'aci',
            'update_interval': '28',
            'use_metadata_iam': 'disable',
            'user_id': 'test_value_30',
            'username': 'test_value_31',
            'vpc_id': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_sdn_connector.fortios_system(input_data, fos_instance)

    expected_data = {
        'access-key': 'test_value_3',
        'azure-region': 'global',
        'client-id': 'test_value_5',
        'client-secret': 'test_value_6',
        'compartment-id': 'test_value_7',
        'gcp-project': 'test_value_8',
        'key-passwd': 'test_value_9',
        'login-endpoint': 'test_value_10',
        'name': 'default_name_11',
                'oci-cert': 'test_value_12',
                'oci-fingerprint': 'test_value_13',
                'oci-region': 'phoenix',
                'password': 'test_value_15',
                'private-key': 'test_value_16',
                'region': 'test_value_17',
                'resource-group': 'test_value_18',
                'resource-url': 'test_value_19',
                'secret-key': 'test_value_20',
                'server': '192.168.100.21',
                'server-port': '22',
                'service-account': 'test_value_23',
                'status': 'disable',
                'subscription-id': 'test_value_25',
                'tenant-id': 'test_value_26',
                'type': 'aci',
                'update-interval': '28',
                'use-metadata-iam': 'disable',
                'user-id': 'test_value_30',
                'username': 'test_value_31',
                'vpc-id': 'test_value_32'
    }

    set_method_mock.assert_called_with('system', 'sdn-connector', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_sdn_connector_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_sdn_connector': {
            'access_key': 'test_value_3',
            'azure_region': 'global',
            'client_id': 'test_value_5',
            'client_secret': 'test_value_6',
            'compartment_id': 'test_value_7',
            'gcp_project': 'test_value_8',
            'key_passwd': 'test_value_9',
            'login_endpoint': 'test_value_10',
            'name': 'default_name_11',
            'oci_cert': 'test_value_12',
            'oci_fingerprint': 'test_value_13',
            'oci_region': 'phoenix',
            'password': 'test_value_15',
            'private_key': 'test_value_16',
            'region': 'test_value_17',
            'resource_group': 'test_value_18',
            'resource_url': 'test_value_19',
            'secret_key': 'test_value_20',
            'server': '192.168.100.21',
            'server_port': '22',
            'service_account': 'test_value_23',
            'status': 'disable',
            'subscription_id': 'test_value_25',
            'tenant_id': 'test_value_26',
            'type': 'aci',
            'update_interval': '28',
            'use_metadata_iam': 'disable',
            'user_id': 'test_value_30',
            'username': 'test_value_31',
            'vpc_id': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_sdn_connector.fortios_system(input_data, fos_instance)

    expected_data = {
        'access-key': 'test_value_3',
        'azure-region': 'global',
        'client-id': 'test_value_5',
        'client-secret': 'test_value_6',
        'compartment-id': 'test_value_7',
        'gcp-project': 'test_value_8',
        'key-passwd': 'test_value_9',
        'login-endpoint': 'test_value_10',
        'name': 'default_name_11',
                'oci-cert': 'test_value_12',
                'oci-fingerprint': 'test_value_13',
                'oci-region': 'phoenix',
                'password': 'test_value_15',
                'private-key': 'test_value_16',
                'region': 'test_value_17',
                'resource-group': 'test_value_18',
                'resource-url': 'test_value_19',
                'secret-key': 'test_value_20',
                'server': '192.168.100.21',
                'server-port': '22',
                'service-account': 'test_value_23',
                'status': 'disable',
                'subscription-id': 'test_value_25',
                'tenant-id': 'test_value_26',
                'type': 'aci',
                'update-interval': '28',
                'use-metadata-iam': 'disable',
                'user-id': 'test_value_30',
                'username': 'test_value_31',
                'vpc-id': 'test_value_32'
    }

    set_method_mock.assert_called_with('system', 'sdn-connector', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_sdn_connector_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'system_sdn_connector': {
            'access_key': 'test_value_3',
            'azure_region': 'global',
            'client_id': 'test_value_5',
            'client_secret': 'test_value_6',
            'compartment_id': 'test_value_7',
            'gcp_project': 'test_value_8',
            'key_passwd': 'test_value_9',
            'login_endpoint': 'test_value_10',
            'name': 'default_name_11',
            'oci_cert': 'test_value_12',
            'oci_fingerprint': 'test_value_13',
            'oci_region': 'phoenix',
            'password': 'test_value_15',
            'private_key': 'test_value_16',
            'region': 'test_value_17',
            'resource_group': 'test_value_18',
            'resource_url': 'test_value_19',
            'secret_key': 'test_value_20',
            'server': '192.168.100.21',
            'server_port': '22',
            'service_account': 'test_value_23',
            'status': 'disable',
            'subscription_id': 'test_value_25',
            'tenant_id': 'test_value_26',
            'type': 'aci',
            'update_interval': '28',
            'use_metadata_iam': 'disable',
            'user_id': 'test_value_30',
            'username': 'test_value_31',
            'vpc_id': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_sdn_connector.fortios_system(input_data, fos_instance)

    delete_method_mock.assert_called_with('system', 'sdn-connector', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_sdn_connector_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'system_sdn_connector': {
            'access_key': 'test_value_3',
            'azure_region': 'global',
            'client_id': 'test_value_5',
            'client_secret': 'test_value_6',
            'compartment_id': 'test_value_7',
            'gcp_project': 'test_value_8',
            'key_passwd': 'test_value_9',
            'login_endpoint': 'test_value_10',
            'name': 'default_name_11',
            'oci_cert': 'test_value_12',
            'oci_fingerprint': 'test_value_13',
            'oci_region': 'phoenix',
            'password': 'test_value_15',
            'private_key': 'test_value_16',
            'region': 'test_value_17',
            'resource_group': 'test_value_18',
            'resource_url': 'test_value_19',
            'secret_key': 'test_value_20',
            'server': '192.168.100.21',
            'server_port': '22',
            'service_account': 'test_value_23',
            'status': 'disable',
            'subscription_id': 'test_value_25',
            'tenant_id': 'test_value_26',
            'type': 'aci',
            'update_interval': '28',
            'use_metadata_iam': 'disable',
            'user_id': 'test_value_30',
            'username': 'test_value_31',
            'vpc_id': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_sdn_connector.fortios_system(input_data, fos_instance)

    delete_method_mock.assert_called_with('system', 'sdn-connector', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_sdn_connector_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_sdn_connector': {
            'access_key': 'test_value_3',
            'azure_region': 'global',
            'client_id': 'test_value_5',
            'client_secret': 'test_value_6',
            'compartment_id': 'test_value_7',
            'gcp_project': 'test_value_8',
            'key_passwd': 'test_value_9',
            'login_endpoint': 'test_value_10',
            'name': 'default_name_11',
            'oci_cert': 'test_value_12',
            'oci_fingerprint': 'test_value_13',
            'oci_region': 'phoenix',
            'password': 'test_value_15',
            'private_key': 'test_value_16',
            'region': 'test_value_17',
            'resource_group': 'test_value_18',
            'resource_url': 'test_value_19',
            'secret_key': 'test_value_20',
            'server': '192.168.100.21',
            'server_port': '22',
            'service_account': 'test_value_23',
            'status': 'disable',
            'subscription_id': 'test_value_25',
            'tenant_id': 'test_value_26',
            'type': 'aci',
            'update_interval': '28',
            'use_metadata_iam': 'disable',
            'user_id': 'test_value_30',
            'username': 'test_value_31',
            'vpc_id': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_sdn_connector.fortios_system(input_data, fos_instance)

    expected_data = {
        'access-key': 'test_value_3',
        'azure-region': 'global',
        'client-id': 'test_value_5',
        'client-secret': 'test_value_6',
        'compartment-id': 'test_value_7',
        'gcp-project': 'test_value_8',
        'key-passwd': 'test_value_9',
        'login-endpoint': 'test_value_10',
        'name': 'default_name_11',
                'oci-cert': 'test_value_12',
                'oci-fingerprint': 'test_value_13',
                'oci-region': 'phoenix',
                'password': 'test_value_15',
                'private-key': 'test_value_16',
                'region': 'test_value_17',
                'resource-group': 'test_value_18',
                'resource-url': 'test_value_19',
                'secret-key': 'test_value_20',
                'server': '192.168.100.21',
                'server-port': '22',
                'service-account': 'test_value_23',
                'status': 'disable',
                'subscription-id': 'test_value_25',
                'tenant-id': 'test_value_26',
                'type': 'aci',
                'update-interval': '28',
                'use-metadata-iam': 'disable',
                'user-id': 'test_value_30',
                'username': 'test_value_31',
                'vpc-id': 'test_value_32'
    }

    set_method_mock.assert_called_with('system', 'sdn-connector', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_system_sdn_connector_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_sdn_connector': {
            'random_attribute_not_valid': 'tag',
            'access_key': 'test_value_3',
            'azure_region': 'global',
            'client_id': 'test_value_5',
            'client_secret': 'test_value_6',
            'compartment_id': 'test_value_7',
            'gcp_project': 'test_value_8',
            'key_passwd': 'test_value_9',
            'login_endpoint': 'test_value_10',
            'name': 'default_name_11',
            'oci_cert': 'test_value_12',
            'oci_fingerprint': 'test_value_13',
            'oci_region': 'phoenix',
            'password': 'test_value_15',
            'private_key': 'test_value_16',
            'region': 'test_value_17',
            'resource_group': 'test_value_18',
            'resource_url': 'test_value_19',
            'secret_key': 'test_value_20',
            'server': '192.168.100.21',
            'server_port': '22',
            'service_account': 'test_value_23',
            'status': 'disable',
            'subscription_id': 'test_value_25',
            'tenant_id': 'test_value_26',
            'type': 'aci',
            'update_interval': '28',
            'use_metadata_iam': 'disable',
            'user_id': 'test_value_30',
            'username': 'test_value_31',
            'vpc_id': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_sdn_connector.fortios_system(input_data, fos_instance)

    expected_data = {
        'access-key': 'test_value_3',
        'azure-region': 'global',
        'client-id': 'test_value_5',
        'client-secret': 'test_value_6',
        'compartment-id': 'test_value_7',
        'gcp-project': 'test_value_8',
        'key-passwd': 'test_value_9',
        'login-endpoint': 'test_value_10',
        'name': 'default_name_11',
                'oci-cert': 'test_value_12',
                'oci-fingerprint': 'test_value_13',
                'oci-region': 'phoenix',
                'password': 'test_value_15',
                'private-key': 'test_value_16',
                'region': 'test_value_17',
                'resource-group': 'test_value_18',
                'resource-url': 'test_value_19',
                'secret-key': 'test_value_20',
                'server': '192.168.100.21',
                'server-port': '22',
                'service-account': 'test_value_23',
                'status': 'disable',
                'subscription-id': 'test_value_25',
                'tenant-id': 'test_value_26',
                'type': 'aci',
                'update-interval': '28',
                'use-metadata-iam': 'disable',
                'user-id': 'test_value_30',
                'username': 'test_value_31',
                'vpc-id': 'test_value_32'
    }

    set_method_mock.assert_called_with('system', 'sdn-connector', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
