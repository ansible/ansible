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
    from ansible.modules.network.fortios import fortios_firewall_ssl_setting
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_firewall_ssl_setting.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_firewall_ssl_setting_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_ssl_setting': {
            'abbreviate_handshake': 'enable',
            'cert_cache_capacity': '4',
            'cert_cache_timeout': '5',
            'kxp_queue_threshold': '6',
            'no_matching_cipher_action': 'bypass',
            'proxy_connect_timeout': '8',
            'session_cache_capacity': '9',
            'session_cache_timeout': '10',
            'ssl_dh_bits': '768',
            'ssl_queue_threshold': '12',
            'ssl_send_empty_frags': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ssl_setting.fortios_firewall_ssl(input_data, fos_instance)

    expected_data = {
        'abbreviate-handshake': 'enable',
        'cert-cache-capacity': '4',
        'cert-cache-timeout': '5',
        'kxp-queue-threshold': '6',
        'no-matching-cipher-action': 'bypass',
        'proxy-connect-timeout': '8',
        'session-cache-capacity': '9',
        'session-cache-timeout': '10',
        'ssl-dh-bits': '768',
        'ssl-queue-threshold': '12',
        'ssl-send-empty-frags': 'enable'
    }

    set_method_mock.assert_called_with('firewall.ssl', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_ssl_setting_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_ssl_setting': {
            'abbreviate_handshake': 'enable',
            'cert_cache_capacity': '4',
            'cert_cache_timeout': '5',
            'kxp_queue_threshold': '6',
            'no_matching_cipher_action': 'bypass',
            'proxy_connect_timeout': '8',
            'session_cache_capacity': '9',
            'session_cache_timeout': '10',
            'ssl_dh_bits': '768',
            'ssl_queue_threshold': '12',
            'ssl_send_empty_frags': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ssl_setting.fortios_firewall_ssl(input_data, fos_instance)

    expected_data = {
        'abbreviate-handshake': 'enable',
        'cert-cache-capacity': '4',
        'cert-cache-timeout': '5',
        'kxp-queue-threshold': '6',
        'no-matching-cipher-action': 'bypass',
        'proxy-connect-timeout': '8',
        'session-cache-capacity': '9',
        'session-cache-timeout': '10',
        'ssl-dh-bits': '768',
        'ssl-queue-threshold': '12',
        'ssl-send-empty-frags': 'enable'
    }

    set_method_mock.assert_called_with('firewall.ssl', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_ssl_setting_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_ssl_setting': {
            'abbreviate_handshake': 'enable',
            'cert_cache_capacity': '4',
            'cert_cache_timeout': '5',
            'kxp_queue_threshold': '6',
            'no_matching_cipher_action': 'bypass',
            'proxy_connect_timeout': '8',
            'session_cache_capacity': '9',
            'session_cache_timeout': '10',
            'ssl_dh_bits': '768',
            'ssl_queue_threshold': '12',
            'ssl_send_empty_frags': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ssl_setting.fortios_firewall_ssl(input_data, fos_instance)

    expected_data = {
        'abbreviate-handshake': 'enable',
        'cert-cache-capacity': '4',
        'cert-cache-timeout': '5',
        'kxp-queue-threshold': '6',
        'no-matching-cipher-action': 'bypass',
        'proxy-connect-timeout': '8',
        'session-cache-capacity': '9',
        'session-cache-timeout': '10',
        'ssl-dh-bits': '768',
        'ssl-queue-threshold': '12',
        'ssl-send-empty-frags': 'enable'
    }

    set_method_mock.assert_called_with('firewall.ssl', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_firewall_ssl_setting_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_ssl_setting': {
            'random_attribute_not_valid': 'tag',
            'abbreviate_handshake': 'enable',
            'cert_cache_capacity': '4',
            'cert_cache_timeout': '5',
            'kxp_queue_threshold': '6',
            'no_matching_cipher_action': 'bypass',
            'proxy_connect_timeout': '8',
            'session_cache_capacity': '9',
            'session_cache_timeout': '10',
            'ssl_dh_bits': '768',
            'ssl_queue_threshold': '12',
            'ssl_send_empty_frags': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_ssl_setting.fortios_firewall_ssl(input_data, fos_instance)

    expected_data = {
        'abbreviate-handshake': 'enable',
        'cert-cache-capacity': '4',
        'cert-cache-timeout': '5',
        'kxp-queue-threshold': '6',
        'no-matching-cipher-action': 'bypass',
        'proxy-connect-timeout': '8',
        'session-cache-capacity': '9',
        'session-cache-timeout': '10',
        'ssl-dh-bits': '768',
        'ssl-queue-threshold': '12',
        'ssl-send-empty-frags': 'enable'
    }

    set_method_mock.assert_called_with('firewall.ssl', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
