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
    from ansible.modules.network.fortios import fortios_router_ospf
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_router_ospf.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_router_ospf_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_ospf': {
            'abr_type': 'cisco',
            'auto_cost_ref_bandwidth': '4',
            'bfd': 'enable',
            'database_overflow': 'enable',
            'database_overflow_max_lsas': '7',
            'database_overflow_time_to_recover': '8',
            'default_information_metric': '9',
            'default_information_metric_type': '1',
            'default_information_originate': 'enable',
            'default_information_route_map': 'test_value_12',
            'default_metric': '13',
            'distance': '14',
            'distance_external': '15',
            'distance_inter_area': '16',
            'distance_intra_area': '17',
            'distribute_list_in': 'test_value_18',
            'distribute_route_map_in': 'test_value_19',
            'log_neighbour_changes': 'enable',
            'restart_mode': 'none',
            'restart_period': '22',
            'rfc1583_compatible': 'enable',
            'router_id': 'test_value_24',
            'spf_timers': 'test_value_25',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_ospf.fortios_router(input_data, fos_instance)

    expected_data = {
        'abr-type': 'cisco',
        'auto-cost-ref-bandwidth': '4',
        'bfd': 'enable',
        'database-overflow': 'enable',
        'database-overflow-max-lsas': '7',
        'database-overflow-time-to-recover': '8',
        'default-information-metric': '9',
        'default-information-metric-type': '1',
        'default-information-originate': 'enable',
        'default-information-route-map': 'test_value_12',
        'default-metric': '13',
        'distance': '14',
        'distance-external': '15',
        'distance-inter-area': '16',
        'distance-intra-area': '17',
        'distribute-list-in': 'test_value_18',
        'distribute-route-map-in': 'test_value_19',
        'log-neighbour-changes': 'enable',
        'restart-mode': 'none',
        'restart-period': '22',
        'rfc1583-compatible': 'enable',
        'router-id': 'test_value_24',
        'spf-timers': 'test_value_25',

    }

    set_method_mock.assert_called_with('router', 'ospf', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_router_ospf_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_ospf': {
            'abr_type': 'cisco',
            'auto_cost_ref_bandwidth': '4',
            'bfd': 'enable',
            'database_overflow': 'enable',
            'database_overflow_max_lsas': '7',
            'database_overflow_time_to_recover': '8',
            'default_information_metric': '9',
            'default_information_metric_type': '1',
            'default_information_originate': 'enable',
            'default_information_route_map': 'test_value_12',
            'default_metric': '13',
            'distance': '14',
            'distance_external': '15',
            'distance_inter_area': '16',
            'distance_intra_area': '17',
            'distribute_list_in': 'test_value_18',
            'distribute_route_map_in': 'test_value_19',
            'log_neighbour_changes': 'enable',
            'restart_mode': 'none',
            'restart_period': '22',
            'rfc1583_compatible': 'enable',
            'router_id': 'test_value_24',
            'spf_timers': 'test_value_25',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_ospf.fortios_router(input_data, fos_instance)

    expected_data = {
        'abr-type': 'cisco',
        'auto-cost-ref-bandwidth': '4',
        'bfd': 'enable',
        'database-overflow': 'enable',
        'database-overflow-max-lsas': '7',
        'database-overflow-time-to-recover': '8',
        'default-information-metric': '9',
        'default-information-metric-type': '1',
        'default-information-originate': 'enable',
        'default-information-route-map': 'test_value_12',
        'default-metric': '13',
        'distance': '14',
        'distance-external': '15',
        'distance-inter-area': '16',
        'distance-intra-area': '17',
        'distribute-list-in': 'test_value_18',
        'distribute-route-map-in': 'test_value_19',
        'log-neighbour-changes': 'enable',
        'restart-mode': 'none',
        'restart-period': '22',
        'rfc1583-compatible': 'enable',
        'router-id': 'test_value_24',
        'spf-timers': 'test_value_25',

    }

    set_method_mock.assert_called_with('router', 'ospf', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_router_ospf_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_ospf': {
            'abr_type': 'cisco',
            'auto_cost_ref_bandwidth': '4',
            'bfd': 'enable',
            'database_overflow': 'enable',
            'database_overflow_max_lsas': '7',
            'database_overflow_time_to_recover': '8',
            'default_information_metric': '9',
            'default_information_metric_type': '1',
            'default_information_originate': 'enable',
            'default_information_route_map': 'test_value_12',
            'default_metric': '13',
            'distance': '14',
            'distance_external': '15',
            'distance_inter_area': '16',
            'distance_intra_area': '17',
            'distribute_list_in': 'test_value_18',
            'distribute_route_map_in': 'test_value_19',
            'log_neighbour_changes': 'enable',
            'restart_mode': 'none',
            'restart_period': '22',
            'rfc1583_compatible': 'enable',
            'router_id': 'test_value_24',
            'spf_timers': 'test_value_25',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_ospf.fortios_router(input_data, fos_instance)

    expected_data = {
        'abr-type': 'cisco',
        'auto-cost-ref-bandwidth': '4',
        'bfd': 'enable',
        'database-overflow': 'enable',
        'database-overflow-max-lsas': '7',
        'database-overflow-time-to-recover': '8',
        'default-information-metric': '9',
        'default-information-metric-type': '1',
        'default-information-originate': 'enable',
        'default-information-route-map': 'test_value_12',
        'default-metric': '13',
        'distance': '14',
        'distance-external': '15',
        'distance-inter-area': '16',
        'distance-intra-area': '17',
        'distribute-list-in': 'test_value_18',
        'distribute-route-map-in': 'test_value_19',
        'log-neighbour-changes': 'enable',
        'restart-mode': 'none',
        'restart-period': '22',
        'rfc1583-compatible': 'enable',
        'router-id': 'test_value_24',
        'spf-timers': 'test_value_25',

    }

    set_method_mock.assert_called_with('router', 'ospf', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_router_ospf_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_ospf': {
            'random_attribute_not_valid': 'tag',
            'abr_type': 'cisco',
            'auto_cost_ref_bandwidth': '4',
            'bfd': 'enable',
            'database_overflow': 'enable',
            'database_overflow_max_lsas': '7',
            'database_overflow_time_to_recover': '8',
            'default_information_metric': '9',
            'default_information_metric_type': '1',
            'default_information_originate': 'enable',
            'default_information_route_map': 'test_value_12',
            'default_metric': '13',
            'distance': '14',
            'distance_external': '15',
            'distance_inter_area': '16',
            'distance_intra_area': '17',
            'distribute_list_in': 'test_value_18',
            'distribute_route_map_in': 'test_value_19',
            'log_neighbour_changes': 'enable',
            'restart_mode': 'none',
            'restart_period': '22',
            'rfc1583_compatible': 'enable',
            'router_id': 'test_value_24',
            'spf_timers': 'test_value_25',

        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_ospf.fortios_router(input_data, fos_instance)

    expected_data = {
        'abr-type': 'cisco',
        'auto-cost-ref-bandwidth': '4',
        'bfd': 'enable',
        'database-overflow': 'enable',
        'database-overflow-max-lsas': '7',
        'database-overflow-time-to-recover': '8',
        'default-information-metric': '9',
        'default-information-metric-type': '1',
        'default-information-originate': 'enable',
        'default-information-route-map': 'test_value_12',
        'default-metric': '13',
        'distance': '14',
        'distance-external': '15',
        'distance-inter-area': '16',
        'distance-intra-area': '17',
        'distribute-list-in': 'test_value_18',
        'distribute-route-map-in': 'test_value_19',
        'log-neighbour-changes': 'enable',
        'restart-mode': 'none',
        'restart-period': '22',
        'rfc1583-compatible': 'enable',
        'router-id': 'test_value_24',
        'spf-timers': 'test_value_25',

    }

    set_method_mock.assert_called_with('router', 'ospf', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
