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
    from ansible.modules.network.fortios import fortios_wireless_controller_hotspot20_h2qp_wan_metric
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_hotspot20_h2qp_wan_metric.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_hotspot20_h2qp_wan_metric_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_hotspot20_h2qp_wan_metric': {
            'downlink_load': '3',
            'downlink_speed': '4',
            'link_at_capacity': 'enable',
            'link_status': 'up',
            'load_measurement_duration': '7',
            'name': 'default_name_8',
            'symmetric_wan_link': 'symmetric',
            'uplink_load': '10',
            'uplink_speed': '11'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_h2qp_wan_metric.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    expected_data = {
        'downlink-load': '3',
        'downlink-speed': '4',
        'link-at-capacity': 'enable',
        'link-status': 'up',
        'load-measurement-duration': '7',
        'name': 'default_name_8',
                'symmetric-wan-link': 'symmetric',
                'uplink-load': '10',
                'uplink-speed': '11'
    }

    set_method_mock.assert_called_with('wireless-controller.hotspot20', 'h2qp-wan-metric', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_hotspot20_h2qp_wan_metric_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_hotspot20_h2qp_wan_metric': {
            'downlink_load': '3',
            'downlink_speed': '4',
            'link_at_capacity': 'enable',
            'link_status': 'up',
            'load_measurement_duration': '7',
            'name': 'default_name_8',
            'symmetric_wan_link': 'symmetric',
            'uplink_load': '10',
            'uplink_speed': '11'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_h2qp_wan_metric.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    expected_data = {
        'downlink-load': '3',
        'downlink-speed': '4',
        'link-at-capacity': 'enable',
        'link-status': 'up',
        'load-measurement-duration': '7',
        'name': 'default_name_8',
                'symmetric-wan-link': 'symmetric',
                'uplink-load': '10',
                'uplink-speed': '11'
    }

    set_method_mock.assert_called_with('wireless-controller.hotspot20', 'h2qp-wan-metric', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_hotspot20_h2qp_wan_metric_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_hotspot20_h2qp_wan_metric': {
            'downlink_load': '3',
            'downlink_speed': '4',
            'link_at_capacity': 'enable',
            'link_status': 'up',
            'load_measurement_duration': '7',
            'name': 'default_name_8',
            'symmetric_wan_link': 'symmetric',
            'uplink_load': '10',
            'uplink_speed': '11'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_h2qp_wan_metric.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller.hotspot20', 'h2qp-wan-metric', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_hotspot20_h2qp_wan_metric_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_hotspot20_h2qp_wan_metric': {
            'downlink_load': '3',
            'downlink_speed': '4',
            'link_at_capacity': 'enable',
            'link_status': 'up',
            'load_measurement_duration': '7',
            'name': 'default_name_8',
            'symmetric_wan_link': 'symmetric',
            'uplink_load': '10',
            'uplink_speed': '11'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_h2qp_wan_metric.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller.hotspot20', 'h2qp-wan-metric', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_hotspot20_h2qp_wan_metric_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_hotspot20_h2qp_wan_metric': {
            'downlink_load': '3',
            'downlink_speed': '4',
            'link_at_capacity': 'enable',
            'link_status': 'up',
            'load_measurement_duration': '7',
            'name': 'default_name_8',
            'symmetric_wan_link': 'symmetric',
            'uplink_load': '10',
            'uplink_speed': '11'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_h2qp_wan_metric.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    expected_data = {
        'downlink-load': '3',
        'downlink-speed': '4',
        'link-at-capacity': 'enable',
        'link-status': 'up',
        'load-measurement-duration': '7',
        'name': 'default_name_8',
                'symmetric-wan-link': 'symmetric',
                'uplink-load': '10',
                'uplink-speed': '11'
    }

    set_method_mock.assert_called_with('wireless-controller.hotspot20', 'h2qp-wan-metric', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_hotspot20_h2qp_wan_metric_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_hotspot20_h2qp_wan_metric': {
            'random_attribute_not_valid': 'tag',
            'downlink_load': '3',
            'downlink_speed': '4',
            'link_at_capacity': 'enable',
            'link_status': 'up',
            'load_measurement_duration': '7',
            'name': 'default_name_8',
            'symmetric_wan_link': 'symmetric',
            'uplink_load': '10',
            'uplink_speed': '11'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_hotspot20_h2qp_wan_metric.fortios_wireless_controller_hotspot20(input_data, fos_instance)

    expected_data = {
        'downlink-load': '3',
        'downlink-speed': '4',
        'link-at-capacity': 'enable',
        'link-status': 'up',
        'load-measurement-duration': '7',
        'name': 'default_name_8',
                'symmetric-wan-link': 'symmetric',
                'uplink-load': '10',
                'uplink-speed': '11'
    }

    set_method_mock.assert_called_with('wireless-controller.hotspot20', 'h2qp-wan-metric', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
