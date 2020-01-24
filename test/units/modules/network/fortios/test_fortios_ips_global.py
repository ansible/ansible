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
    from ansible.modules.network.fortios import fortios_ips_global
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_ips_global.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_ips_global_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'ips_global': {
            'anomaly_mode': 'periodical',
            'database': 'regular',
            'deep_app_insp_db_limit': '5',
            'deep_app_insp_timeout': '6',
            'engine_count': '7',
            'exclude_signatures': 'none',
            'fail_open': 'enable',
            'intelligent_mode': 'enable',
            'session_limit_mode': 'accurate',
            'skype_client_public_ipaddr': 'test_value_12',
            'socket_size': '13',
            'sync_session_ttl': 'enable',
            'traffic_submit': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_ips_global.fortios_ips(input_data, fos_instance)

    expected_data = {
        'anomaly-mode': 'periodical',
        'database': 'regular',
        'deep-app-insp-db-limit': '5',
        'deep-app-insp-timeout': '6',
        'engine-count': '7',
        'exclude-signatures': 'none',
        'fail-open': 'enable',
        'intelligent-mode': 'enable',
        'session-limit-mode': 'accurate',
        'skype-client-public-ipaddr': 'test_value_12',
        'socket-size': '13',
        'sync-session-ttl': 'enable',
        'traffic-submit': 'enable'
    }

    set_method_mock.assert_called_with('ips', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_ips_global_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'ips_global': {
            'anomaly_mode': 'periodical',
            'database': 'regular',
            'deep_app_insp_db_limit': '5',
            'deep_app_insp_timeout': '6',
            'engine_count': '7',
            'exclude_signatures': 'none',
            'fail_open': 'enable',
            'intelligent_mode': 'enable',
            'session_limit_mode': 'accurate',
            'skype_client_public_ipaddr': 'test_value_12',
            'socket_size': '13',
            'sync_session_ttl': 'enable',
            'traffic_submit': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_ips_global.fortios_ips(input_data, fos_instance)

    expected_data = {
        'anomaly-mode': 'periodical',
        'database': 'regular',
        'deep-app-insp-db-limit': '5',
        'deep-app-insp-timeout': '6',
        'engine-count': '7',
        'exclude-signatures': 'none',
        'fail-open': 'enable',
        'intelligent-mode': 'enable',
        'session-limit-mode': 'accurate',
        'skype-client-public-ipaddr': 'test_value_12',
        'socket-size': '13',
        'sync-session-ttl': 'enable',
        'traffic-submit': 'enable'
    }

    set_method_mock.assert_called_with('ips', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_ips_global_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'ips_global': {
            'anomaly_mode': 'periodical',
            'database': 'regular',
            'deep_app_insp_db_limit': '5',
            'deep_app_insp_timeout': '6',
            'engine_count': '7',
            'exclude_signatures': 'none',
            'fail_open': 'enable',
            'intelligent_mode': 'enable',
            'session_limit_mode': 'accurate',
            'skype_client_public_ipaddr': 'test_value_12',
            'socket_size': '13',
            'sync_session_ttl': 'enable',
            'traffic_submit': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_ips_global.fortios_ips(input_data, fos_instance)

    expected_data = {
        'anomaly-mode': 'periodical',
        'database': 'regular',
        'deep-app-insp-db-limit': '5',
        'deep-app-insp-timeout': '6',
        'engine-count': '7',
        'exclude-signatures': 'none',
        'fail-open': 'enable',
        'intelligent-mode': 'enable',
        'session-limit-mode': 'accurate',
        'skype-client-public-ipaddr': 'test_value_12',
        'socket-size': '13',
        'sync-session-ttl': 'enable',
        'traffic-submit': 'enable'
    }

    set_method_mock.assert_called_with('ips', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_ips_global_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'ips_global': {
            'random_attribute_not_valid': 'tag',
            'anomaly_mode': 'periodical',
            'database': 'regular',
            'deep_app_insp_db_limit': '5',
            'deep_app_insp_timeout': '6',
            'engine_count': '7',
            'exclude_signatures': 'none',
            'fail_open': 'enable',
            'intelligent_mode': 'enable',
            'session_limit_mode': 'accurate',
            'skype_client_public_ipaddr': 'test_value_12',
            'socket_size': '13',
            'sync_session_ttl': 'enable',
            'traffic_submit': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_ips_global.fortios_ips(input_data, fos_instance)

    expected_data = {
        'anomaly-mode': 'periodical',
        'database': 'regular',
        'deep-app-insp-db-limit': '5',
        'deep-app-insp-timeout': '6',
        'engine-count': '7',
        'exclude-signatures': 'none',
        'fail-open': 'enable',
        'intelligent-mode': 'enable',
        'session-limit-mode': 'accurate',
        'skype-client-public-ipaddr': 'test_value_12',
        'socket-size': '13',
        'sync-session-ttl': 'enable',
        'traffic-submit': 'enable'
    }

    set_method_mock.assert_called_with('ips', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
