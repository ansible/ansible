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
    from ansible.modules.network.fortios import fortios_log_setting
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_log_setting.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_log_setting_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'log_setting': {
            'brief_traffic_format': 'enable',
            'daemon_log': 'enable',
            'expolicy_implicit_log': 'enable',
            'fwpolicy_implicit_log': 'enable',
            'fwpolicy6_implicit_log': 'enable',
            'local_in_allow': 'enable',
            'local_in_deny_broadcast': 'enable',
            'local_in_deny_unicast': 'enable',
            'local_out': 'enable',
            'log_invalid_packet': 'enable',
            'log_policy_comment': 'enable',
            'log_policy_name': 'enable',
            'log_user_in_upper': 'enable',
            'neighbor_event': 'enable',
            'resolve_ip': 'enable',
            'resolve_port': 'enable',
            'user_anonymize': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_log_setting.fortios_log(input_data, fos_instance)

    expected_data = {
        'brief-traffic-format': 'enable',
        'daemon-log': 'enable',
        'expolicy-implicit-log': 'enable',
        'fwpolicy-implicit-log': 'enable',
        'fwpolicy6-implicit-log': 'enable',
        'local-in-allow': 'enable',
        'local-in-deny-broadcast': 'enable',
        'local-in-deny-unicast': 'enable',
        'local-out': 'enable',
        'log-invalid-packet': 'enable',
        'log-policy-comment': 'enable',
        'log-policy-name': 'enable',
        'log-user-in-upper': 'enable',
        'neighbor-event': 'enable',
        'resolve-ip': 'enable',
        'resolve-port': 'enable',
        'user-anonymize': 'enable'
    }

    set_method_mock.assert_called_with('log', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_log_setting_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'log_setting': {
            'brief_traffic_format': 'enable',
            'daemon_log': 'enable',
            'expolicy_implicit_log': 'enable',
            'fwpolicy_implicit_log': 'enable',
            'fwpolicy6_implicit_log': 'enable',
            'local_in_allow': 'enable',
            'local_in_deny_broadcast': 'enable',
            'local_in_deny_unicast': 'enable',
            'local_out': 'enable',
            'log_invalid_packet': 'enable',
            'log_policy_comment': 'enable',
            'log_policy_name': 'enable',
            'log_user_in_upper': 'enable',
            'neighbor_event': 'enable',
            'resolve_ip': 'enable',
            'resolve_port': 'enable',
            'user_anonymize': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_log_setting.fortios_log(input_data, fos_instance)

    expected_data = {
        'brief-traffic-format': 'enable',
        'daemon-log': 'enable',
        'expolicy-implicit-log': 'enable',
        'fwpolicy-implicit-log': 'enable',
        'fwpolicy6-implicit-log': 'enable',
        'local-in-allow': 'enable',
        'local-in-deny-broadcast': 'enable',
        'local-in-deny-unicast': 'enable',
        'local-out': 'enable',
        'log-invalid-packet': 'enable',
        'log-policy-comment': 'enable',
        'log-policy-name': 'enable',
        'log-user-in-upper': 'enable',
        'neighbor-event': 'enable',
        'resolve-ip': 'enable',
        'resolve-port': 'enable',
        'user-anonymize': 'enable'
    }

    set_method_mock.assert_called_with('log', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_log_setting_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'log_setting': {
            'brief_traffic_format': 'enable',
            'daemon_log': 'enable',
            'expolicy_implicit_log': 'enable',
            'fwpolicy_implicit_log': 'enable',
            'fwpolicy6_implicit_log': 'enable',
            'local_in_allow': 'enable',
            'local_in_deny_broadcast': 'enable',
            'local_in_deny_unicast': 'enable',
            'local_out': 'enable',
            'log_invalid_packet': 'enable',
            'log_policy_comment': 'enable',
            'log_policy_name': 'enable',
            'log_user_in_upper': 'enable',
            'neighbor_event': 'enable',
            'resolve_ip': 'enable',
            'resolve_port': 'enable',
            'user_anonymize': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_log_setting.fortios_log(input_data, fos_instance)

    expected_data = {
        'brief-traffic-format': 'enable',
        'daemon-log': 'enable',
        'expolicy-implicit-log': 'enable',
        'fwpolicy-implicit-log': 'enable',
        'fwpolicy6-implicit-log': 'enable',
        'local-in-allow': 'enable',
        'local-in-deny-broadcast': 'enable',
        'local-in-deny-unicast': 'enable',
        'local-out': 'enable',
        'log-invalid-packet': 'enable',
        'log-policy-comment': 'enable',
        'log-policy-name': 'enable',
        'log-user-in-upper': 'enable',
        'neighbor-event': 'enable',
        'resolve-ip': 'enable',
        'resolve-port': 'enable',
        'user-anonymize': 'enable'
    }

    set_method_mock.assert_called_with('log', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_log_setting_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'log_setting': {
            'random_attribute_not_valid': 'tag',
            'brief_traffic_format': 'enable',
            'daemon_log': 'enable',
            'expolicy_implicit_log': 'enable',
            'fwpolicy_implicit_log': 'enable',
            'fwpolicy6_implicit_log': 'enable',
            'local_in_allow': 'enable',
            'local_in_deny_broadcast': 'enable',
            'local_in_deny_unicast': 'enable',
            'local_out': 'enable',
            'log_invalid_packet': 'enable',
            'log_policy_comment': 'enable',
            'log_policy_name': 'enable',
            'log_user_in_upper': 'enable',
            'neighbor_event': 'enable',
            'resolve_ip': 'enable',
            'resolve_port': 'enable',
            'user_anonymize': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_log_setting.fortios_log(input_data, fos_instance)

    expected_data = {
        'brief-traffic-format': 'enable',
        'daemon-log': 'enable',
        'expolicy-implicit-log': 'enable',
        'fwpolicy-implicit-log': 'enable',
        'fwpolicy6-implicit-log': 'enable',
        'local-in-allow': 'enable',
        'local-in-deny-broadcast': 'enable',
        'local-in-deny-unicast': 'enable',
        'local-out': 'enable',
        'log-invalid-packet': 'enable',
        'log-policy-comment': 'enable',
        'log-policy-name': 'enable',
        'log-user-in-upper': 'enable',
        'neighbor-event': 'enable',
        'resolve-ip': 'enable',
        'resolve-port': 'enable',
        'user-anonymize': 'enable'
    }

    set_method_mock.assert_called_with('log', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
