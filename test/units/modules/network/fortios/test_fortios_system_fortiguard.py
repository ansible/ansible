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
    from ansible.modules.network.fortios import fortios_system_fortiguard
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_system_fortiguard.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_system_fortiguard_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_fortiguard': {
            'antispam_cache': 'enable',
            'antispam_cache_mpercent': '4',
            'antispam_cache_ttl': '5',
            'antispam_expiration': '6',
            'antispam_force_off': 'enable',
            'antispam_license': '8',
            'antispam_timeout': '9',
            'auto_join_forticloud': 'enable',
            'ddns_server_ip': 'test_value_11',
            'ddns_server_port': '12',
            'load_balance_servers': '13',
            'outbreak_prevention_cache': 'enable',
            'outbreak_prevention_cache_mpercent': '15',
            'outbreak_prevention_cache_ttl': '16',
            'outbreak_prevention_expiration': '17',
            'outbreak_prevention_force_off': 'enable',
            'outbreak_prevention_license': '19',
            'outbreak_prevention_timeout': '20',
            'port': '53',
            'sdns_server_ip': 'test_value_22',
            'sdns_server_port': '23',
            'service_account_id': 'test_value_24',
            'source_ip': '84.230.14.25',
            'source_ip6': 'test_value_26',
            'update_server_location': 'usa',
            'webfilter_cache': 'enable',
            'webfilter_cache_ttl': '29',
            'webfilter_expiration': '30',
            'webfilter_force_off': 'enable',
            'webfilter_license': '32',
            'webfilter_timeout': '33'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_fortiguard.fortios_system(input_data, fos_instance)

    expected_data = {
        'antispam-cache': 'enable',
        'antispam-cache-mpercent': '4',
        'antispam-cache-ttl': '5',
        'antispam-expiration': '6',
        'antispam-force-off': 'enable',
        'antispam-license': '8',
        'antispam-timeout': '9',
        'auto-join-forticloud': 'enable',
        'ddns-server-ip': 'test_value_11',
        'ddns-server-port': '12',
        'load-balance-servers': '13',
        'outbreak-prevention-cache': 'enable',
        'outbreak-prevention-cache-mpercent': '15',
        'outbreak-prevention-cache-ttl': '16',
        'outbreak-prevention-expiration': '17',
        'outbreak-prevention-force-off': 'enable',
        'outbreak-prevention-license': '19',
        'outbreak-prevention-timeout': '20',
        'port': '53',
                'sdns-server-ip': 'test_value_22',
                'sdns-server-port': '23',
                'service-account-id': 'test_value_24',
                'source-ip': '84.230.14.25',
                'source-ip6': 'test_value_26',
                'update-server-location': 'usa',
                'webfilter-cache': 'enable',
                'webfilter-cache-ttl': '29',
                'webfilter-expiration': '30',
                'webfilter-force-off': 'enable',
                'webfilter-license': '32',
                'webfilter-timeout': '33'
    }

    set_method_mock.assert_called_with('system', 'fortiguard', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_fortiguard_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_fortiguard': {
            'antispam_cache': 'enable',
            'antispam_cache_mpercent': '4',
            'antispam_cache_ttl': '5',
            'antispam_expiration': '6',
            'antispam_force_off': 'enable',
            'antispam_license': '8',
            'antispam_timeout': '9',
            'auto_join_forticloud': 'enable',
            'ddns_server_ip': 'test_value_11',
            'ddns_server_port': '12',
            'load_balance_servers': '13',
            'outbreak_prevention_cache': 'enable',
            'outbreak_prevention_cache_mpercent': '15',
            'outbreak_prevention_cache_ttl': '16',
            'outbreak_prevention_expiration': '17',
            'outbreak_prevention_force_off': 'enable',
            'outbreak_prevention_license': '19',
            'outbreak_prevention_timeout': '20',
            'port': '53',
            'sdns_server_ip': 'test_value_22',
            'sdns_server_port': '23',
            'service_account_id': 'test_value_24',
            'source_ip': '84.230.14.25',
            'source_ip6': 'test_value_26',
            'update_server_location': 'usa',
            'webfilter_cache': 'enable',
            'webfilter_cache_ttl': '29',
            'webfilter_expiration': '30',
            'webfilter_force_off': 'enable',
            'webfilter_license': '32',
            'webfilter_timeout': '33'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_fortiguard.fortios_system(input_data, fos_instance)

    expected_data = {
        'antispam-cache': 'enable',
        'antispam-cache-mpercent': '4',
        'antispam-cache-ttl': '5',
        'antispam-expiration': '6',
        'antispam-force-off': 'enable',
        'antispam-license': '8',
        'antispam-timeout': '9',
        'auto-join-forticloud': 'enable',
        'ddns-server-ip': 'test_value_11',
        'ddns-server-port': '12',
        'load-balance-servers': '13',
        'outbreak-prevention-cache': 'enable',
        'outbreak-prevention-cache-mpercent': '15',
        'outbreak-prevention-cache-ttl': '16',
        'outbreak-prevention-expiration': '17',
        'outbreak-prevention-force-off': 'enable',
        'outbreak-prevention-license': '19',
        'outbreak-prevention-timeout': '20',
        'port': '53',
                'sdns-server-ip': 'test_value_22',
                'sdns-server-port': '23',
                'service-account-id': 'test_value_24',
                'source-ip': '84.230.14.25',
                'source-ip6': 'test_value_26',
                'update-server-location': 'usa',
                'webfilter-cache': 'enable',
                'webfilter-cache-ttl': '29',
                'webfilter-expiration': '30',
                'webfilter-force-off': 'enable',
                'webfilter-license': '32',
                'webfilter-timeout': '33'
    }

    set_method_mock.assert_called_with('system', 'fortiguard', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_fortiguard_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_fortiguard': {
            'antispam_cache': 'enable',
            'antispam_cache_mpercent': '4',
            'antispam_cache_ttl': '5',
            'antispam_expiration': '6',
            'antispam_force_off': 'enable',
            'antispam_license': '8',
            'antispam_timeout': '9',
            'auto_join_forticloud': 'enable',
            'ddns_server_ip': 'test_value_11',
            'ddns_server_port': '12',
            'load_balance_servers': '13',
            'outbreak_prevention_cache': 'enable',
            'outbreak_prevention_cache_mpercent': '15',
            'outbreak_prevention_cache_ttl': '16',
            'outbreak_prevention_expiration': '17',
            'outbreak_prevention_force_off': 'enable',
            'outbreak_prevention_license': '19',
            'outbreak_prevention_timeout': '20',
            'port': '53',
            'sdns_server_ip': 'test_value_22',
            'sdns_server_port': '23',
            'service_account_id': 'test_value_24',
            'source_ip': '84.230.14.25',
            'source_ip6': 'test_value_26',
            'update_server_location': 'usa',
            'webfilter_cache': 'enable',
            'webfilter_cache_ttl': '29',
            'webfilter_expiration': '30',
            'webfilter_force_off': 'enable',
            'webfilter_license': '32',
            'webfilter_timeout': '33'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_fortiguard.fortios_system(input_data, fos_instance)

    expected_data = {
        'antispam-cache': 'enable',
        'antispam-cache-mpercent': '4',
        'antispam-cache-ttl': '5',
        'antispam-expiration': '6',
        'antispam-force-off': 'enable',
        'antispam-license': '8',
        'antispam-timeout': '9',
        'auto-join-forticloud': 'enable',
        'ddns-server-ip': 'test_value_11',
        'ddns-server-port': '12',
        'load-balance-servers': '13',
        'outbreak-prevention-cache': 'enable',
        'outbreak-prevention-cache-mpercent': '15',
        'outbreak-prevention-cache-ttl': '16',
        'outbreak-prevention-expiration': '17',
        'outbreak-prevention-force-off': 'enable',
        'outbreak-prevention-license': '19',
        'outbreak-prevention-timeout': '20',
        'port': '53',
                'sdns-server-ip': 'test_value_22',
                'sdns-server-port': '23',
                'service-account-id': 'test_value_24',
                'source-ip': '84.230.14.25',
                'source-ip6': 'test_value_26',
                'update-server-location': 'usa',
                'webfilter-cache': 'enable',
                'webfilter-cache-ttl': '29',
                'webfilter-expiration': '30',
                'webfilter-force-off': 'enable',
                'webfilter-license': '32',
                'webfilter-timeout': '33'
    }

    set_method_mock.assert_called_with('system', 'fortiguard', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_system_fortiguard_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_fortiguard': {
            'random_attribute_not_valid': 'tag',
            'antispam_cache': 'enable',
            'antispam_cache_mpercent': '4',
            'antispam_cache_ttl': '5',
            'antispam_expiration': '6',
            'antispam_force_off': 'enable',
            'antispam_license': '8',
            'antispam_timeout': '9',
            'auto_join_forticloud': 'enable',
            'ddns_server_ip': 'test_value_11',
            'ddns_server_port': '12',
            'load_balance_servers': '13',
            'outbreak_prevention_cache': 'enable',
            'outbreak_prevention_cache_mpercent': '15',
            'outbreak_prevention_cache_ttl': '16',
            'outbreak_prevention_expiration': '17',
            'outbreak_prevention_force_off': 'enable',
            'outbreak_prevention_license': '19',
            'outbreak_prevention_timeout': '20',
            'port': '53',
            'sdns_server_ip': 'test_value_22',
            'sdns_server_port': '23',
            'service_account_id': 'test_value_24',
            'source_ip': '84.230.14.25',
            'source_ip6': 'test_value_26',
            'update_server_location': 'usa',
            'webfilter_cache': 'enable',
            'webfilter_cache_ttl': '29',
            'webfilter_expiration': '30',
            'webfilter_force_off': 'enable',
            'webfilter_license': '32',
            'webfilter_timeout': '33'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_fortiguard.fortios_system(input_data, fos_instance)

    expected_data = {
        'antispam-cache': 'enable',
        'antispam-cache-mpercent': '4',
        'antispam-cache-ttl': '5',
        'antispam-expiration': '6',
        'antispam-force-off': 'enable',
        'antispam-license': '8',
        'antispam-timeout': '9',
        'auto-join-forticloud': 'enable',
        'ddns-server-ip': 'test_value_11',
        'ddns-server-port': '12',
        'load-balance-servers': '13',
        'outbreak-prevention-cache': 'enable',
        'outbreak-prevention-cache-mpercent': '15',
        'outbreak-prevention-cache-ttl': '16',
        'outbreak-prevention-expiration': '17',
        'outbreak-prevention-force-off': 'enable',
        'outbreak-prevention-license': '19',
        'outbreak-prevention-timeout': '20',
        'port': '53',
                'sdns-server-ip': 'test_value_22',
                'sdns-server-port': '23',
                'service-account-id': 'test_value_24',
                'source-ip': '84.230.14.25',
                'source-ip6': 'test_value_26',
                'update-server-location': 'usa',
                'webfilter-cache': 'enable',
                'webfilter-cache-ttl': '29',
                'webfilter-expiration': '30',
                'webfilter-force-off': 'enable',
                'webfilter-license': '32',
                'webfilter-timeout': '33'
    }

    set_method_mock.assert_called_with('system', 'fortiguard', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
