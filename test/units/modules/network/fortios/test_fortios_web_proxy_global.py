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
    from ansible.modules.network.fortios import fortios_web_proxy_global
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_web_proxy_global.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_web_proxy_global_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'web_proxy_global': {
            'fast_policy_match': 'enable',
            'forward_proxy_auth': 'enable',
            'forward_server_affinity_timeout': '5',
            'learn_client_ip': 'enable',
            'learn_client_ip_from_header': 'true-client-ip',
            'max_message_length': '8',
            'max_request_length': '9',
            'max_waf_body_cache_length': '10',
            'proxy_fqdn': 'test_value_11',
            'strict_web_check': 'enable',
            'tunnel_non_http': 'enable',
            'unknown_http_version': 'reject',
            'webproxy_profile': 'test_value_15'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_web_proxy_global.fortios_web_proxy(input_data, fos_instance)

    expected_data = {
        'fast-policy-match': 'enable',
        'forward-proxy-auth': 'enable',
        'forward-server-affinity-timeout': '5',
        'learn-client-ip': 'enable',
        'learn-client-ip-from-header': 'true-client-ip',
        'max-message-length': '8',
        'max-request-length': '9',
        'max-waf-body-cache-length': '10',
        'proxy-fqdn': 'test_value_11',
        'strict-web-check': 'enable',
        'tunnel-non-http': 'enable',
        'unknown-http-version': 'reject',
        'webproxy-profile': 'test_value_15'
    }

    set_method_mock.assert_called_with('web-proxy', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_web_proxy_global_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'web_proxy_global': {
            'fast_policy_match': 'enable',
            'forward_proxy_auth': 'enable',
            'forward_server_affinity_timeout': '5',
            'learn_client_ip': 'enable',
            'learn_client_ip_from_header': 'true-client-ip',
            'max_message_length': '8',
            'max_request_length': '9',
            'max_waf_body_cache_length': '10',
            'proxy_fqdn': 'test_value_11',
            'strict_web_check': 'enable',
            'tunnel_non_http': 'enable',
            'unknown_http_version': 'reject',
            'webproxy_profile': 'test_value_15'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_web_proxy_global.fortios_web_proxy(input_data, fos_instance)

    expected_data = {
        'fast-policy-match': 'enable',
        'forward-proxy-auth': 'enable',
        'forward-server-affinity-timeout': '5',
        'learn-client-ip': 'enable',
        'learn-client-ip-from-header': 'true-client-ip',
        'max-message-length': '8',
        'max-request-length': '9',
        'max-waf-body-cache-length': '10',
        'proxy-fqdn': 'test_value_11',
        'strict-web-check': 'enable',
        'tunnel-non-http': 'enable',
        'unknown-http-version': 'reject',
        'webproxy-profile': 'test_value_15'
    }

    set_method_mock.assert_called_with('web-proxy', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_web_proxy_global_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'web_proxy_global': {
            'fast_policy_match': 'enable',
            'forward_proxy_auth': 'enable',
            'forward_server_affinity_timeout': '5',
            'learn_client_ip': 'enable',
            'learn_client_ip_from_header': 'true-client-ip',
            'max_message_length': '8',
            'max_request_length': '9',
            'max_waf_body_cache_length': '10',
            'proxy_fqdn': 'test_value_11',
            'strict_web_check': 'enable',
            'tunnel_non_http': 'enable',
            'unknown_http_version': 'reject',
            'webproxy_profile': 'test_value_15'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_web_proxy_global.fortios_web_proxy(input_data, fos_instance)

    expected_data = {
        'fast-policy-match': 'enable',
        'forward-proxy-auth': 'enable',
        'forward-server-affinity-timeout': '5',
        'learn-client-ip': 'enable',
        'learn-client-ip-from-header': 'true-client-ip',
        'max-message-length': '8',
        'max-request-length': '9',
        'max-waf-body-cache-length': '10',
        'proxy-fqdn': 'test_value_11',
        'strict-web-check': 'enable',
        'tunnel-non-http': 'enable',
        'unknown-http-version': 'reject',
        'webproxy-profile': 'test_value_15'
    }

    set_method_mock.assert_called_with('web-proxy', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_web_proxy_global_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'web_proxy_global': {
            'random_attribute_not_valid': 'tag',
            'fast_policy_match': 'enable',
            'forward_proxy_auth': 'enable',
            'forward_server_affinity_timeout': '5',
            'learn_client_ip': 'enable',
            'learn_client_ip_from_header': 'true-client-ip',
            'max_message_length': '8',
            'max_request_length': '9',
            'max_waf_body_cache_length': '10',
            'proxy_fqdn': 'test_value_11',
            'strict_web_check': 'enable',
            'tunnel_non_http': 'enable',
            'unknown_http_version': 'reject',
            'webproxy_profile': 'test_value_15'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_web_proxy_global.fortios_web_proxy(input_data, fos_instance)

    expected_data = {
        'fast-policy-match': 'enable',
        'forward-proxy-auth': 'enable',
        'forward-server-affinity-timeout': '5',
        'learn-client-ip': 'enable',
        'learn-client-ip-from-header': 'true-client-ip',
        'max-message-length': '8',
        'max-request-length': '9',
        'max-waf-body-cache-length': '10',
        'proxy-fqdn': 'test_value_11',
        'strict-web-check': 'enable',
        'tunnel-non-http': 'enable',
        'unknown-http-version': 'reject',
        'webproxy-profile': 'test_value_15'
    }

    set_method_mock.assert_called_with('web-proxy', 'global', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
