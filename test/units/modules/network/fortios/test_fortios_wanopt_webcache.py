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
    from ansible.modules.network.fortios import fortios_wanopt_webcache
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wanopt_webcache.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wanopt_webcache_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wanopt_webcache': {
            'always_revalidate': 'enable',
            'cache_by_default': 'enable',
            'cache_cookie': 'enable',
            'cache_expired': 'enable',
            'default_ttl': '7',
            'external': 'enable',
            'fresh_factor': '9',
            'host_validate': 'enable',
            'ignore_conditional': 'enable',
            'ignore_ie_reload': 'enable',
            'ignore_ims': 'enable',
            'ignore_pnc': 'enable',
            'max_object_size': '15',
            'max_ttl': '16',
            'min_ttl': '17',
            'neg_resp_time': '18',
            'reval_pnc': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wanopt_webcache.fortios_wanopt(input_data, fos_instance)

    expected_data = {
        'always-revalidate': 'enable',
        'cache-by-default': 'enable',
        'cache-cookie': 'enable',
        'cache-expired': 'enable',
        'default-ttl': '7',
        'external': 'enable',
        'fresh-factor': '9',
        'host-validate': 'enable',
        'ignore-conditional': 'enable',
        'ignore-ie-reload': 'enable',
        'ignore-ims': 'enable',
        'ignore-pnc': 'enable',
        'max-object-size': '15',
        'max-ttl': '16',
        'min-ttl': '17',
        'neg-resp-time': '18',
        'reval-pnc': 'enable'
    }

    set_method_mock.assert_called_with('wanopt', 'webcache', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wanopt_webcache_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wanopt_webcache': {
            'always_revalidate': 'enable',
            'cache_by_default': 'enable',
            'cache_cookie': 'enable',
            'cache_expired': 'enable',
            'default_ttl': '7',
            'external': 'enable',
            'fresh_factor': '9',
            'host_validate': 'enable',
            'ignore_conditional': 'enable',
            'ignore_ie_reload': 'enable',
            'ignore_ims': 'enable',
            'ignore_pnc': 'enable',
            'max_object_size': '15',
            'max_ttl': '16',
            'min_ttl': '17',
            'neg_resp_time': '18',
            'reval_pnc': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wanopt_webcache.fortios_wanopt(input_data, fos_instance)

    expected_data = {
        'always-revalidate': 'enable',
        'cache-by-default': 'enable',
        'cache-cookie': 'enable',
        'cache-expired': 'enable',
        'default-ttl': '7',
        'external': 'enable',
        'fresh-factor': '9',
        'host-validate': 'enable',
        'ignore-conditional': 'enable',
        'ignore-ie-reload': 'enable',
        'ignore-ims': 'enable',
        'ignore-pnc': 'enable',
        'max-object-size': '15',
        'max-ttl': '16',
        'min-ttl': '17',
        'neg-resp-time': '18',
        'reval-pnc': 'enable'
    }

    set_method_mock.assert_called_with('wanopt', 'webcache', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wanopt_webcache_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wanopt_webcache': {
            'always_revalidate': 'enable',
            'cache_by_default': 'enable',
            'cache_cookie': 'enable',
            'cache_expired': 'enable',
            'default_ttl': '7',
            'external': 'enable',
            'fresh_factor': '9',
            'host_validate': 'enable',
            'ignore_conditional': 'enable',
            'ignore_ie_reload': 'enable',
            'ignore_ims': 'enable',
            'ignore_pnc': 'enable',
            'max_object_size': '15',
            'max_ttl': '16',
            'min_ttl': '17',
            'neg_resp_time': '18',
            'reval_pnc': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wanopt_webcache.fortios_wanopt(input_data, fos_instance)

    expected_data = {
        'always-revalidate': 'enable',
        'cache-by-default': 'enable',
        'cache-cookie': 'enable',
        'cache-expired': 'enable',
        'default-ttl': '7',
        'external': 'enable',
        'fresh-factor': '9',
        'host-validate': 'enable',
        'ignore-conditional': 'enable',
        'ignore-ie-reload': 'enable',
        'ignore-ims': 'enable',
        'ignore-pnc': 'enable',
        'max-object-size': '15',
        'max-ttl': '16',
        'min-ttl': '17',
        'neg-resp-time': '18',
        'reval-pnc': 'enable'
    }

    set_method_mock.assert_called_with('wanopt', 'webcache', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wanopt_webcache_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wanopt_webcache': {
            'random_attribute_not_valid': 'tag',
            'always_revalidate': 'enable',
            'cache_by_default': 'enable',
            'cache_cookie': 'enable',
            'cache_expired': 'enable',
            'default_ttl': '7',
            'external': 'enable',
            'fresh_factor': '9',
            'host_validate': 'enable',
            'ignore_conditional': 'enable',
            'ignore_ie_reload': 'enable',
            'ignore_ims': 'enable',
            'ignore_pnc': 'enable',
            'max_object_size': '15',
            'max_ttl': '16',
            'min_ttl': '17',
            'neg_resp_time': '18',
            'reval_pnc': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wanopt_webcache.fortios_wanopt(input_data, fos_instance)

    expected_data = {
        'always-revalidate': 'enable',
        'cache-by-default': 'enable',
        'cache-cookie': 'enable',
        'cache-expired': 'enable',
        'default-ttl': '7',
        'external': 'enable',
        'fresh-factor': '9',
        'host-validate': 'enable',
        'ignore-conditional': 'enable',
        'ignore-ie-reload': 'enable',
        'ignore-ims': 'enable',
        'ignore-pnc': 'enable',
        'max-object-size': '15',
        'max-ttl': '16',
        'min-ttl': '17',
        'neg-resp-time': '18',
        'reval-pnc': 'enable'
    }

    set_method_mock.assert_called_with('wanopt', 'webcache', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
