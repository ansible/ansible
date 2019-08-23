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
    from ansible.modules.network.fortios import fortios_wireless_controller_timers
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_timers.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_timers_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_timers': {
            'ble_scan_report_intv': '3',
            'client_idle_timeout': '4',
            'darrp_day': 'sunday',
            'darrp_optimize': '6',
            'discovery_interval': '7',
            'echo_interval': '8',
            'fake_ap_log': '9',
            'ipsec_intf_cleanup': '10',
            'radio_stats_interval': '11',
            'rogue_ap_log': '12',
            'sta_capability_interval': '13',
            'sta_locate_timer': '14',
            'sta_stats_interval': '15',
            'vap_stats_interval': '16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_timers.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ble-scan-report-intv': '3',
        'client-idle-timeout': '4',
        'darrp-day': 'sunday',
        'darrp-optimize': '6',
        'discovery-interval': '7',
        'echo-interval': '8',
        'fake-ap-log': '9',
        'ipsec-intf-cleanup': '10',
        'radio-stats-interval': '11',
        'rogue-ap-log': '12',
        'sta-capability-interval': '13',
        'sta-locate-timer': '14',
        'sta-stats-interval': '15',
        'vap-stats-interval': '16'
    }

    set_method_mock.assert_called_with('wireless-controller', 'timers', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_timers_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_timers': {
            'ble_scan_report_intv': '3',
            'client_idle_timeout': '4',
            'darrp_day': 'sunday',
            'darrp_optimize': '6',
            'discovery_interval': '7',
            'echo_interval': '8',
            'fake_ap_log': '9',
            'ipsec_intf_cleanup': '10',
            'radio_stats_interval': '11',
            'rogue_ap_log': '12',
            'sta_capability_interval': '13',
            'sta_locate_timer': '14',
            'sta_stats_interval': '15',
            'vap_stats_interval': '16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_timers.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ble-scan-report-intv': '3',
        'client-idle-timeout': '4',
        'darrp-day': 'sunday',
        'darrp-optimize': '6',
        'discovery-interval': '7',
        'echo-interval': '8',
        'fake-ap-log': '9',
        'ipsec-intf-cleanup': '10',
        'radio-stats-interval': '11',
        'rogue-ap-log': '12',
        'sta-capability-interval': '13',
        'sta-locate-timer': '14',
        'sta-stats-interval': '15',
        'vap-stats-interval': '16'
    }

    set_method_mock.assert_called_with('wireless-controller', 'timers', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_timers_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_timers': {
            'ble_scan_report_intv': '3',
            'client_idle_timeout': '4',
            'darrp_day': 'sunday',
            'darrp_optimize': '6',
            'discovery_interval': '7',
            'echo_interval': '8',
            'fake_ap_log': '9',
            'ipsec_intf_cleanup': '10',
            'radio_stats_interval': '11',
            'rogue_ap_log': '12',
            'sta_capability_interval': '13',
            'sta_locate_timer': '14',
            'sta_stats_interval': '15',
            'vap_stats_interval': '16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_timers.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ble-scan-report-intv': '3',
        'client-idle-timeout': '4',
        'darrp-day': 'sunday',
        'darrp-optimize': '6',
        'discovery-interval': '7',
        'echo-interval': '8',
        'fake-ap-log': '9',
        'ipsec-intf-cleanup': '10',
        'radio-stats-interval': '11',
        'rogue-ap-log': '12',
        'sta-capability-interval': '13',
        'sta-locate-timer': '14',
        'sta-stats-interval': '15',
        'vap-stats-interval': '16'
    }

    set_method_mock.assert_called_with('wireless-controller', 'timers', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_timers_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_timers': {
            'random_attribute_not_valid': 'tag',
            'ble_scan_report_intv': '3',
            'client_idle_timeout': '4',
            'darrp_day': 'sunday',
            'darrp_optimize': '6',
            'discovery_interval': '7',
            'echo_interval': '8',
            'fake_ap_log': '9',
            'ipsec_intf_cleanup': '10',
            'radio_stats_interval': '11',
            'rogue_ap_log': '12',
            'sta_capability_interval': '13',
            'sta_locate_timer': '14',
            'sta_stats_interval': '15',
            'vap_stats_interval': '16'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_timers.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ble-scan-report-intv': '3',
        'client-idle-timeout': '4',
        'darrp-day': 'sunday',
        'darrp-optimize': '6',
        'discovery-interval': '7',
        'echo-interval': '8',
        'fake-ap-log': '9',
        'ipsec-intf-cleanup': '10',
        'radio-stats-interval': '11',
        'rogue-ap-log': '12',
        'sta-capability-interval': '13',
        'sta-locate-timer': '14',
        'sta-stats-interval': '15',
        'vap-stats-interval': '16'
    }

    set_method_mock.assert_called_with('wireless-controller', 'timers', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
