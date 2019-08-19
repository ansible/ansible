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
    from ansible.modules.network.fortios import fortios_router_isis
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_router_isis.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_router_isis_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_isis': {
            'adjacency_check': 'enable',
            'adjacency_check6': 'enable',
            'adv_passive_only': 'enable',
            'adv_passive_only6': 'enable',
            'auth_keychain_l1': 'test_value_7',
            'auth_keychain_l2': 'test_value_8',
            'auth_mode_l1': 'password',
            'auth_mode_l2': 'password',
            'auth_password_l1': 'test_value_11',
            'auth_password_l2': 'test_value_12',
            'auth_sendonly_l1': 'enable',
            'auth_sendonly_l2': 'enable',
            'default_originate': 'enable',
            'default_originate6': 'enable',
            'dynamic_hostname': 'enable',
            'ignore_lsp_errors': 'enable',
            'is_type': 'level-1-2',
            'lsp_gen_interval_l1': '20',
            'lsp_gen_interval_l2': '21',
            'lsp_refresh_interval': '22',
            'max_lsp_lifetime': '23',
            'metric_style': 'narrow',
            'overload_bit': 'enable',
            'overload_bit_on_startup': '26',
            'overload_bit_suppress': 'external',
            'redistribute_l1': 'enable',
            'redistribute_l1_list': 'test_value_29',
            'redistribute_l2': 'enable',
            'redistribute_l2_list': 'test_value_31',
            'redistribute6_l1': 'enable',
            'redistribute6_l1_list': 'test_value_33',
            'redistribute6_l2': 'enable',
            'redistribute6_l2_list': 'test_value_35',
            'spf_interval_exp_l1': 'test_value_36',
            'spf_interval_exp_l2': 'test_value_37',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_isis.fortios_router(input_data, fos_instance)

    expected_data = {
        'adjacency-check': 'enable',
        'adjacency-check6': 'enable',
        'adv-passive-only': 'enable',
        'adv-passive-only6': 'enable',
        'auth-keychain-l1': 'test_value_7',
        'auth-keychain-l2': 'test_value_8',
        'auth-mode-l1': 'password',
        'auth-mode-l2': 'password',
        'auth-password-l1': 'test_value_11',
        'auth-password-l2': 'test_value_12',
        'auth-sendonly-l1': 'enable',
        'auth-sendonly-l2': 'enable',
        'default-originate': 'enable',
        'default-originate6': 'enable',
        'dynamic-hostname': 'enable',
        'ignore-lsp-errors': 'enable',
        'is-type': 'level-1-2',
        'lsp-gen-interval-l1': '20',
        'lsp-gen-interval-l2': '21',
        'lsp-refresh-interval': '22',
        'max-lsp-lifetime': '23',
        'metric-style': 'narrow',
        'overload-bit': 'enable',
        'overload-bit-on-startup': '26',
        'overload-bit-suppress': 'external',
        'redistribute-l1': 'enable',
        'redistribute-l1-list': 'test_value_29',
        'redistribute-l2': 'enable',
        'redistribute-l2-list': 'test_value_31',
        'redistribute6-l1': 'enable',
        'redistribute6-l1-list': 'test_value_33',
        'redistribute6-l2': 'enable',
        'redistribute6-l2-list': 'test_value_35',
        'spf-interval-exp-l1': 'test_value_36',
        'spf-interval-exp-l2': 'test_value_37',

    }

    set_method_mock.assert_called_with('router', 'isis', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_router_isis_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_isis': {
            'adjacency_check': 'enable',
            'adjacency_check6': 'enable',
            'adv_passive_only': 'enable',
            'adv_passive_only6': 'enable',
            'auth_keychain_l1': 'test_value_7',
            'auth_keychain_l2': 'test_value_8',
            'auth_mode_l1': 'password',
            'auth_mode_l2': 'password',
            'auth_password_l1': 'test_value_11',
            'auth_password_l2': 'test_value_12',
            'auth_sendonly_l1': 'enable',
            'auth_sendonly_l2': 'enable',
            'default_originate': 'enable',
            'default_originate6': 'enable',
            'dynamic_hostname': 'enable',
            'ignore_lsp_errors': 'enable',
            'is_type': 'level-1-2',
            'lsp_gen_interval_l1': '20',
            'lsp_gen_interval_l2': '21',
            'lsp_refresh_interval': '22',
            'max_lsp_lifetime': '23',
            'metric_style': 'narrow',
            'overload_bit': 'enable',
            'overload_bit_on_startup': '26',
            'overload_bit_suppress': 'external',
            'redistribute_l1': 'enable',
            'redistribute_l1_list': 'test_value_29',
            'redistribute_l2': 'enable',
            'redistribute_l2_list': 'test_value_31',
            'redistribute6_l1': 'enable',
            'redistribute6_l1_list': 'test_value_33',
            'redistribute6_l2': 'enable',
            'redistribute6_l2_list': 'test_value_35',
            'spf_interval_exp_l1': 'test_value_36',
            'spf_interval_exp_l2': 'test_value_37',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_isis.fortios_router(input_data, fos_instance)

    expected_data = {
        'adjacency-check': 'enable',
        'adjacency-check6': 'enable',
        'adv-passive-only': 'enable',
        'adv-passive-only6': 'enable',
        'auth-keychain-l1': 'test_value_7',
        'auth-keychain-l2': 'test_value_8',
        'auth-mode-l1': 'password',
        'auth-mode-l2': 'password',
        'auth-password-l1': 'test_value_11',
        'auth-password-l2': 'test_value_12',
        'auth-sendonly-l1': 'enable',
        'auth-sendonly-l2': 'enable',
        'default-originate': 'enable',
        'default-originate6': 'enable',
        'dynamic-hostname': 'enable',
        'ignore-lsp-errors': 'enable',
        'is-type': 'level-1-2',
        'lsp-gen-interval-l1': '20',
        'lsp-gen-interval-l2': '21',
        'lsp-refresh-interval': '22',
        'max-lsp-lifetime': '23',
        'metric-style': 'narrow',
        'overload-bit': 'enable',
        'overload-bit-on-startup': '26',
        'overload-bit-suppress': 'external',
        'redistribute-l1': 'enable',
        'redistribute-l1-list': 'test_value_29',
        'redistribute-l2': 'enable',
        'redistribute-l2-list': 'test_value_31',
        'redistribute6-l1': 'enable',
        'redistribute6-l1-list': 'test_value_33',
        'redistribute6-l2': 'enable',
        'redistribute6-l2-list': 'test_value_35',
        'spf-interval-exp-l1': 'test_value_36',
        'spf-interval-exp-l2': 'test_value_37',

    }

    set_method_mock.assert_called_with('router', 'isis', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_router_isis_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_isis': {
            'adjacency_check': 'enable',
            'adjacency_check6': 'enable',
            'adv_passive_only': 'enable',
            'adv_passive_only6': 'enable',
            'auth_keychain_l1': 'test_value_7',
            'auth_keychain_l2': 'test_value_8',
            'auth_mode_l1': 'password',
            'auth_mode_l2': 'password',
            'auth_password_l1': 'test_value_11',
            'auth_password_l2': 'test_value_12',
            'auth_sendonly_l1': 'enable',
            'auth_sendonly_l2': 'enable',
            'default_originate': 'enable',
            'default_originate6': 'enable',
            'dynamic_hostname': 'enable',
            'ignore_lsp_errors': 'enable',
            'is_type': 'level-1-2',
            'lsp_gen_interval_l1': '20',
            'lsp_gen_interval_l2': '21',
            'lsp_refresh_interval': '22',
            'max_lsp_lifetime': '23',
            'metric_style': 'narrow',
            'overload_bit': 'enable',
            'overload_bit_on_startup': '26',
            'overload_bit_suppress': 'external',
            'redistribute_l1': 'enable',
            'redistribute_l1_list': 'test_value_29',
            'redistribute_l2': 'enable',
            'redistribute_l2_list': 'test_value_31',
            'redistribute6_l1': 'enable',
            'redistribute6_l1_list': 'test_value_33',
            'redistribute6_l2': 'enable',
            'redistribute6_l2_list': 'test_value_35',
            'spf_interval_exp_l1': 'test_value_36',
            'spf_interval_exp_l2': 'test_value_37',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_isis.fortios_router(input_data, fos_instance)

    expected_data = {
        'adjacency-check': 'enable',
        'adjacency-check6': 'enable',
        'adv-passive-only': 'enable',
        'adv-passive-only6': 'enable',
        'auth-keychain-l1': 'test_value_7',
        'auth-keychain-l2': 'test_value_8',
        'auth-mode-l1': 'password',
        'auth-mode-l2': 'password',
        'auth-password-l1': 'test_value_11',
        'auth-password-l2': 'test_value_12',
        'auth-sendonly-l1': 'enable',
        'auth-sendonly-l2': 'enable',
        'default-originate': 'enable',
        'default-originate6': 'enable',
        'dynamic-hostname': 'enable',
        'ignore-lsp-errors': 'enable',
        'is-type': 'level-1-2',
        'lsp-gen-interval-l1': '20',
        'lsp-gen-interval-l2': '21',
        'lsp-refresh-interval': '22',
        'max-lsp-lifetime': '23',
        'metric-style': 'narrow',
        'overload-bit': 'enable',
        'overload-bit-on-startup': '26',
        'overload-bit-suppress': 'external',
        'redistribute-l1': 'enable',
        'redistribute-l1-list': 'test_value_29',
        'redistribute-l2': 'enable',
        'redistribute-l2-list': 'test_value_31',
        'redistribute6-l1': 'enable',
        'redistribute6-l1-list': 'test_value_33',
        'redistribute6-l2': 'enable',
        'redistribute6-l2-list': 'test_value_35',
        'spf-interval-exp-l1': 'test_value_36',
        'spf-interval-exp-l2': 'test_value_37',

    }

    set_method_mock.assert_called_with('router', 'isis', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_router_isis_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_isis': {
            'random_attribute_not_valid': 'tag',
            'adjacency_check': 'enable',
            'adjacency_check6': 'enable',
            'adv_passive_only': 'enable',
            'adv_passive_only6': 'enable',
            'auth_keychain_l1': 'test_value_7',
            'auth_keychain_l2': 'test_value_8',
            'auth_mode_l1': 'password',
            'auth_mode_l2': 'password',
            'auth_password_l1': 'test_value_11',
            'auth_password_l2': 'test_value_12',
            'auth_sendonly_l1': 'enable',
            'auth_sendonly_l2': 'enable',
            'default_originate': 'enable',
            'default_originate6': 'enable',
            'dynamic_hostname': 'enable',
            'ignore_lsp_errors': 'enable',
            'is_type': 'level-1-2',
            'lsp_gen_interval_l1': '20',
            'lsp_gen_interval_l2': '21',
            'lsp_refresh_interval': '22',
            'max_lsp_lifetime': '23',
            'metric_style': 'narrow',
            'overload_bit': 'enable',
            'overload_bit_on_startup': '26',
            'overload_bit_suppress': 'external',
            'redistribute_l1': 'enable',
            'redistribute_l1_list': 'test_value_29',
            'redistribute_l2': 'enable',
            'redistribute_l2_list': 'test_value_31',
            'redistribute6_l1': 'enable',
            'redistribute6_l1_list': 'test_value_33',
            'redistribute6_l2': 'enable',
            'redistribute6_l2_list': 'test_value_35',
            'spf_interval_exp_l1': 'test_value_36',
            'spf_interval_exp_l2': 'test_value_37',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_isis.fortios_router(input_data, fos_instance)

    expected_data = {
        'adjacency-check': 'enable',
        'adjacency-check6': 'enable',
        'adv-passive-only': 'enable',
        'adv-passive-only6': 'enable',
        'auth-keychain-l1': 'test_value_7',
        'auth-keychain-l2': 'test_value_8',
        'auth-mode-l1': 'password',
        'auth-mode-l2': 'password',
        'auth-password-l1': 'test_value_11',
        'auth-password-l2': 'test_value_12',
        'auth-sendonly-l1': 'enable',
        'auth-sendonly-l2': 'enable',
        'default-originate': 'enable',
        'default-originate6': 'enable',
        'dynamic-hostname': 'enable',
        'ignore-lsp-errors': 'enable',
        'is-type': 'level-1-2',
        'lsp-gen-interval-l1': '20',
        'lsp-gen-interval-l2': '21',
        'lsp-refresh-interval': '22',
        'max-lsp-lifetime': '23',
        'metric-style': 'narrow',
        'overload-bit': 'enable',
        'overload-bit-on-startup': '26',
        'overload-bit-suppress': 'external',
        'redistribute-l1': 'enable',
        'redistribute-l1-list': 'test_value_29',
        'redistribute-l2': 'enable',
        'redistribute-l2-list': 'test_value_31',
        'redistribute6-l1': 'enable',
        'redistribute6-l1-list': 'test_value_33',
        'redistribute6-l2': 'enable',
        'redistribute6-l2-list': 'test_value_35',
        'spf-interval-exp-l1': 'test_value_36',
        'spf-interval-exp-l2': 'test_value_37',

    }

    set_method_mock.assert_called_with('router', 'isis', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
