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
    from ansible.modules.network.fortios import fortios_web_proxy_explicit
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_web_proxy_explicit.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_web_proxy_explicit_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'web_proxy_explicit': {
            'ftp_incoming_port': 'test_value_3',
            'ftp_over_http': 'enable',
            'http_incoming_port': 'test_value_5',
            'https_incoming_port': 'test_value_6',
            'https_replacement_message': 'enable',
            'incoming_ip': 'test_value_8',
            'incoming_ip6': 'test_value_9',
            'ipv6_status': 'enable',
            'message_upon_server_error': 'enable',
            'outgoing_ip': 'test_value_12',
            'outgoing_ip6': 'test_value_13',
            'pac_file_data': 'test_value_14',
            'pac_file_name': 'test_value_15',
            'pac_file_server_port': 'test_value_16',
            'pac_file_server_status': 'enable',
            'pac_file_url': 'test_value_18',
            'pref_dns_result': 'ipv4',
            'realm': 'test_value_20',
            'sec_default_action': 'accept',
            'socks': 'enable',
            'socks_incoming_port': 'test_value_23',
            'ssl_algorithm': 'low',
            'status': 'enable',
            'strict_guest': 'enable',
            'trace_auth_no_rsp': 'enable',
            'unknown_http_version': 'reject'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_web_proxy_explicit.fortios_web_proxy(input_data, fos_instance)

    expected_data = {
        'ftp-incoming-port': 'test_value_3',
        'ftp-over-http': 'enable',
        'http-incoming-port': 'test_value_5',
        'https-incoming-port': 'test_value_6',
        'https-replacement-message': 'enable',
        'incoming-ip': 'test_value_8',
        'incoming-ip6': 'test_value_9',
        'ipv6-status': 'enable',
        'message-upon-server-error': 'enable',
        'outgoing-ip': 'test_value_12',
        'outgoing-ip6': 'test_value_13',
        'pac-file-data': 'test_value_14',
        'pac-file-name': 'test_value_15',
        'pac-file-server-port': 'test_value_16',
        'pac-file-server-status': 'enable',
        'pac-file-url': 'test_value_18',
        'pref-dns-result': 'ipv4',
        'realm': 'test_value_20',
        'sec-default-action': 'accept',
        'socks': 'enable',
        'socks-incoming-port': 'test_value_23',
        'ssl-algorithm': 'low',
        'status': 'enable',
        'strict-guest': 'enable',
        'trace-auth-no-rsp': 'enable',
        'unknown-http-version': 'reject'
    }

    set_method_mock.assert_called_with('web-proxy', 'explicit', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_web_proxy_explicit_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'web_proxy_explicit': {
            'ftp_incoming_port': 'test_value_3',
            'ftp_over_http': 'enable',
            'http_incoming_port': 'test_value_5',
            'https_incoming_port': 'test_value_6',
            'https_replacement_message': 'enable',
            'incoming_ip': 'test_value_8',
            'incoming_ip6': 'test_value_9',
            'ipv6_status': 'enable',
            'message_upon_server_error': 'enable',
            'outgoing_ip': 'test_value_12',
            'outgoing_ip6': 'test_value_13',
            'pac_file_data': 'test_value_14',
            'pac_file_name': 'test_value_15',
            'pac_file_server_port': 'test_value_16',
            'pac_file_server_status': 'enable',
            'pac_file_url': 'test_value_18',
            'pref_dns_result': 'ipv4',
            'realm': 'test_value_20',
            'sec_default_action': 'accept',
            'socks': 'enable',
            'socks_incoming_port': 'test_value_23',
            'ssl_algorithm': 'low',
            'status': 'enable',
            'strict_guest': 'enable',
            'trace_auth_no_rsp': 'enable',
            'unknown_http_version': 'reject'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_web_proxy_explicit.fortios_web_proxy(input_data, fos_instance)

    expected_data = {
        'ftp-incoming-port': 'test_value_3',
        'ftp-over-http': 'enable',
        'http-incoming-port': 'test_value_5',
        'https-incoming-port': 'test_value_6',
        'https-replacement-message': 'enable',
        'incoming-ip': 'test_value_8',
        'incoming-ip6': 'test_value_9',
        'ipv6-status': 'enable',
        'message-upon-server-error': 'enable',
        'outgoing-ip': 'test_value_12',
        'outgoing-ip6': 'test_value_13',
        'pac-file-data': 'test_value_14',
        'pac-file-name': 'test_value_15',
        'pac-file-server-port': 'test_value_16',
        'pac-file-server-status': 'enable',
        'pac-file-url': 'test_value_18',
        'pref-dns-result': 'ipv4',
        'realm': 'test_value_20',
        'sec-default-action': 'accept',
        'socks': 'enable',
        'socks-incoming-port': 'test_value_23',
        'ssl-algorithm': 'low',
        'status': 'enable',
        'strict-guest': 'enable',
        'trace-auth-no-rsp': 'enable',
        'unknown-http-version': 'reject'
    }

    set_method_mock.assert_called_with('web-proxy', 'explicit', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_web_proxy_explicit_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'web_proxy_explicit': {
            'ftp_incoming_port': 'test_value_3',
            'ftp_over_http': 'enable',
            'http_incoming_port': 'test_value_5',
            'https_incoming_port': 'test_value_6',
            'https_replacement_message': 'enable',
            'incoming_ip': 'test_value_8',
            'incoming_ip6': 'test_value_9',
            'ipv6_status': 'enable',
            'message_upon_server_error': 'enable',
            'outgoing_ip': 'test_value_12',
            'outgoing_ip6': 'test_value_13',
            'pac_file_data': 'test_value_14',
            'pac_file_name': 'test_value_15',
            'pac_file_server_port': 'test_value_16',
            'pac_file_server_status': 'enable',
            'pac_file_url': 'test_value_18',
            'pref_dns_result': 'ipv4',
            'realm': 'test_value_20',
            'sec_default_action': 'accept',
            'socks': 'enable',
            'socks_incoming_port': 'test_value_23',
            'ssl_algorithm': 'low',
            'status': 'enable',
            'strict_guest': 'enable',
            'trace_auth_no_rsp': 'enable',
            'unknown_http_version': 'reject'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_web_proxy_explicit.fortios_web_proxy(input_data, fos_instance)

    expected_data = {
        'ftp-incoming-port': 'test_value_3',
        'ftp-over-http': 'enable',
        'http-incoming-port': 'test_value_5',
        'https-incoming-port': 'test_value_6',
        'https-replacement-message': 'enable',
        'incoming-ip': 'test_value_8',
        'incoming-ip6': 'test_value_9',
        'ipv6-status': 'enable',
        'message-upon-server-error': 'enable',
        'outgoing-ip': 'test_value_12',
        'outgoing-ip6': 'test_value_13',
        'pac-file-data': 'test_value_14',
        'pac-file-name': 'test_value_15',
        'pac-file-server-port': 'test_value_16',
        'pac-file-server-status': 'enable',
        'pac-file-url': 'test_value_18',
        'pref-dns-result': 'ipv4',
        'realm': 'test_value_20',
        'sec-default-action': 'accept',
        'socks': 'enable',
        'socks-incoming-port': 'test_value_23',
        'ssl-algorithm': 'low',
        'status': 'enable',
        'strict-guest': 'enable',
        'trace-auth-no-rsp': 'enable',
        'unknown-http-version': 'reject'
    }

    set_method_mock.assert_called_with('web-proxy', 'explicit', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_web_proxy_explicit_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'web_proxy_explicit': {
            'random_attribute_not_valid': 'tag',
            'ftp_incoming_port': 'test_value_3',
            'ftp_over_http': 'enable',
            'http_incoming_port': 'test_value_5',
            'https_incoming_port': 'test_value_6',
            'https_replacement_message': 'enable',
            'incoming_ip': 'test_value_8',
            'incoming_ip6': 'test_value_9',
            'ipv6_status': 'enable',
            'message_upon_server_error': 'enable',
            'outgoing_ip': 'test_value_12',
            'outgoing_ip6': 'test_value_13',
            'pac_file_data': 'test_value_14',
            'pac_file_name': 'test_value_15',
            'pac_file_server_port': 'test_value_16',
            'pac_file_server_status': 'enable',
            'pac_file_url': 'test_value_18',
            'pref_dns_result': 'ipv4',
            'realm': 'test_value_20',
            'sec_default_action': 'accept',
            'socks': 'enable',
            'socks_incoming_port': 'test_value_23',
            'ssl_algorithm': 'low',
            'status': 'enable',
            'strict_guest': 'enable',
            'trace_auth_no_rsp': 'enable',
            'unknown_http_version': 'reject'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_web_proxy_explicit.fortios_web_proxy(input_data, fos_instance)

    expected_data = {
        'ftp-incoming-port': 'test_value_3',
        'ftp-over-http': 'enable',
        'http-incoming-port': 'test_value_5',
        'https-incoming-port': 'test_value_6',
        'https-replacement-message': 'enable',
        'incoming-ip': 'test_value_8',
        'incoming-ip6': 'test_value_9',
        'ipv6-status': 'enable',
        'message-upon-server-error': 'enable',
        'outgoing-ip': 'test_value_12',
        'outgoing-ip6': 'test_value_13',
        'pac-file-data': 'test_value_14',
        'pac-file-name': 'test_value_15',
        'pac-file-server-port': 'test_value_16',
        'pac-file-server-status': 'enable',
        'pac-file-url': 'test_value_18',
        'pref-dns-result': 'ipv4',
        'realm': 'test_value_20',
        'sec-default-action': 'accept',
        'socks': 'enable',
        'socks-incoming-port': 'test_value_23',
        'ssl-algorithm': 'low',
        'status': 'enable',
        'strict-guest': 'enable',
        'trace-auth-no-rsp': 'enable',
        'unknown-http-version': 'reject'
    }

    set_method_mock.assert_called_with('web-proxy', 'explicit', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
