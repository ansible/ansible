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
    from ansible.modules.network.fortios import fortios_router_bgp
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_router_bgp.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_router_bgp_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_bgp': {'always_compare_med': 'enable',
                       'as': '4',
                       'bestpath_as_path_ignore': 'enable',
                       'bestpath_cmp_confed_aspath': 'enable',
                       'bestpath_cmp_routerid': 'enable',
                       'bestpath_med_confed': 'enable',
                       'bestpath_med_missing_as_worst': 'enable',
                       'client_to_client_reflection': 'enable',
                       'cluster_id': 'test_value_11',
                       'confederation_identifier': '12',
                       'dampening': 'enable',
                       'dampening_max_suppress_time': '14',
                       'dampening_reachability_half_life': '15',
                       'dampening_reuse': '16',
                       'dampening_route_map': 'test_value_17',
                       'dampening_suppress': '18',
                       'dampening_unreachability_half_life': '19',
                       'default_local_preference': '20',
                       'deterministic_med': 'enable',
                       'distance_external': '22',
                       'distance_internal': '23',
                       'distance_local': '24',
                       'ebgp_multipath': 'enable',
                       'enforce_first_as': 'enable',
                       'fast_external_failover': 'enable',
                       'graceful_end_on_timer': 'enable',
                       'graceful_restart': 'enable',
                       'graceful_restart_time': '30',
                       'graceful_stalepath_time': '31',
                       'graceful_update_delay': '32',
                       'holdtime_timer': '33',
                       'ibgp_multipath': 'enable',
                       'ignore_optional_capability': 'enable',
                       'keepalive_timer': '36',
                       'log_neighbour_changes': 'enable',
                       'network_import_check': 'enable',
                       'router_id': 'test_value_39',
                       'scan_time': '40',
                       'synchronization': 'enable'
                       },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_bgp.fortios_router(input_data, fos_instance)

    expected_data = {'always-compare-med': 'enable',
                     'as': '4',
                     'bestpath-as-path-ignore': 'enable',
                     'bestpath-cmp-confed-aspath': 'enable',
                     'bestpath-cmp-routerid': 'enable',
                     'bestpath-med-confed': 'enable',
                     'bestpath-med-missing-as-worst': 'enable',
                     'client-to-client-reflection': 'enable',
                     'cluster-id': 'test_value_11',
                     'confederation-identifier': '12',
                     'dampening': 'enable',
                     'dampening-max-suppress-time': '14',
                     'dampening-reachability-half-life': '15',
                     'dampening-reuse': '16',
                     'dampening-route-map': 'test_value_17',
                     'dampening-suppress': '18',
                     'dampening-unreachability-half-life': '19',
                     'default-local-preference': '20',
                     'deterministic-med': 'enable',
                     'distance-external': '22',
                     'distance-internal': '23',
                     'distance-local': '24',
                     'ebgp-multipath': 'enable',
                     'enforce-first-as': 'enable',
                     'fast-external-failover': 'enable',
                     'graceful-end-on-timer': 'enable',
                     'graceful-restart': 'enable',
                     'graceful-restart-time': '30',
                     'graceful-stalepath-time': '31',
                     'graceful-update-delay': '32',
                     'holdtime-timer': '33',
                     'ibgp-multipath': 'enable',
                     'ignore-optional-capability': 'enable',
                     'keepalive-timer': '36',
                     'log-neighbour-changes': 'enable',
                     'network-import-check': 'enable',
                     'router-id': 'test_value_39',
                     'scan-time': '40',
                     'synchronization': 'enable'
                     }

    set_method_mock.assert_called_with('router', 'bgp', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_router_bgp_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_bgp': {'always_compare_med': 'enable',
                       'as': '4',
                       'bestpath_as_path_ignore': 'enable',
                       'bestpath_cmp_confed_aspath': 'enable',
                       'bestpath_cmp_routerid': 'enable',
                       'bestpath_med_confed': 'enable',
                       'bestpath_med_missing_as_worst': 'enable',
                       'client_to_client_reflection': 'enable',
                       'cluster_id': 'test_value_11',
                       'confederation_identifier': '12',
                       'dampening': 'enable',
                       'dampening_max_suppress_time': '14',
                       'dampening_reachability_half_life': '15',
                       'dampening_reuse': '16',
                       'dampening_route_map': 'test_value_17',
                       'dampening_suppress': '18',
                       'dampening_unreachability_half_life': '19',
                       'default_local_preference': '20',
                       'deterministic_med': 'enable',
                       'distance_external': '22',
                       'distance_internal': '23',
                       'distance_local': '24',
                       'ebgp_multipath': 'enable',
                       'enforce_first_as': 'enable',
                       'fast_external_failover': 'enable',
                       'graceful_end_on_timer': 'enable',
                       'graceful_restart': 'enable',
                       'graceful_restart_time': '30',
                       'graceful_stalepath_time': '31',
                       'graceful_update_delay': '32',
                       'holdtime_timer': '33',
                       'ibgp_multipath': 'enable',
                       'ignore_optional_capability': 'enable',
                       'keepalive_timer': '36',
                       'log_neighbour_changes': 'enable',
                       'network_import_check': 'enable',
                       'router_id': 'test_value_39',
                       'scan_time': '40',
                       'synchronization': 'enable'
                       },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_bgp.fortios_router(input_data, fos_instance)

    expected_data = {'always-compare-med': 'enable',
                     'as': '4',
                     'bestpath-as-path-ignore': 'enable',
                     'bestpath-cmp-confed-aspath': 'enable',
                     'bestpath-cmp-routerid': 'enable',
                     'bestpath-med-confed': 'enable',
                     'bestpath-med-missing-as-worst': 'enable',
                     'client-to-client-reflection': 'enable',
                     'cluster-id': 'test_value_11',
                     'confederation-identifier': '12',
                     'dampening': 'enable',
                     'dampening-max-suppress-time': '14',
                     'dampening-reachability-half-life': '15',
                     'dampening-reuse': '16',
                     'dampening-route-map': 'test_value_17',
                     'dampening-suppress': '18',
                     'dampening-unreachability-half-life': '19',
                     'default-local-preference': '20',
                     'deterministic-med': 'enable',
                     'distance-external': '22',
                     'distance-internal': '23',
                     'distance-local': '24',
                     'ebgp-multipath': 'enable',
                     'enforce-first-as': 'enable',
                     'fast-external-failover': 'enable',
                     'graceful-end-on-timer': 'enable',
                     'graceful-restart': 'enable',
                     'graceful-restart-time': '30',
                     'graceful-stalepath-time': '31',
                     'graceful-update-delay': '32',
                     'holdtime-timer': '33',
                     'ibgp-multipath': 'enable',
                     'ignore-optional-capability': 'enable',
                     'keepalive-timer': '36',
                     'log-neighbour-changes': 'enable',
                     'network-import-check': 'enable',
                     'router-id': 'test_value_39',
                     'scan-time': '40',
                     'synchronization': 'enable'
                     }

    set_method_mock.assert_called_with('router', 'bgp', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_router_bgp_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_bgp': {'always_compare_med': 'enable',
                       'as': '4',
                       'bestpath_as_path_ignore': 'enable',
                       'bestpath_cmp_confed_aspath': 'enable',
                       'bestpath_cmp_routerid': 'enable',
                       'bestpath_med_confed': 'enable',
                       'bestpath_med_missing_as_worst': 'enable',
                       'client_to_client_reflection': 'enable',
                       'cluster_id': 'test_value_11',
                       'confederation_identifier': '12',
                       'dampening': 'enable',
                       'dampening_max_suppress_time': '14',
                       'dampening_reachability_half_life': '15',
                       'dampening_reuse': '16',
                       'dampening_route_map': 'test_value_17',
                       'dampening_suppress': '18',
                       'dampening_unreachability_half_life': '19',
                       'default_local_preference': '20',
                       'deterministic_med': 'enable',
                       'distance_external': '22',
                       'distance_internal': '23',
                       'distance_local': '24',
                       'ebgp_multipath': 'enable',
                       'enforce_first_as': 'enable',
                       'fast_external_failover': 'enable',
                       'graceful_end_on_timer': 'enable',
                       'graceful_restart': 'enable',
                       'graceful_restart_time': '30',
                       'graceful_stalepath_time': '31',
                       'graceful_update_delay': '32',
                       'holdtime_timer': '33',
                       'ibgp_multipath': 'enable',
                       'ignore_optional_capability': 'enable',
                       'keepalive_timer': '36',
                       'log_neighbour_changes': 'enable',
                       'network_import_check': 'enable',
                       'router_id': 'test_value_39',
                       'scan_time': '40',
                       'synchronization': 'enable'
                       },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_bgp.fortios_router(input_data, fos_instance)

    expected_data = {'always-compare-med': 'enable',
                     'as': '4',
                     'bestpath-as-path-ignore': 'enable',
                     'bestpath-cmp-confed-aspath': 'enable',
                     'bestpath-cmp-routerid': 'enable',
                     'bestpath-med-confed': 'enable',
                     'bestpath-med-missing-as-worst': 'enable',
                     'client-to-client-reflection': 'enable',
                     'cluster-id': 'test_value_11',
                     'confederation-identifier': '12',
                     'dampening': 'enable',
                     'dampening-max-suppress-time': '14',
                     'dampening-reachability-half-life': '15',
                     'dampening-reuse': '16',
                     'dampening-route-map': 'test_value_17',
                     'dampening-suppress': '18',
                     'dampening-unreachability-half-life': '19',
                     'default-local-preference': '20',
                     'deterministic-med': 'enable',
                     'distance-external': '22',
                     'distance-internal': '23',
                     'distance-local': '24',
                     'ebgp-multipath': 'enable',
                     'enforce-first-as': 'enable',
                     'fast-external-failover': 'enable',
                     'graceful-end-on-timer': 'enable',
                     'graceful-restart': 'enable',
                     'graceful-restart-time': '30',
                     'graceful-stalepath-time': '31',
                     'graceful-update-delay': '32',
                     'holdtime-timer': '33',
                     'ibgp-multipath': 'enable',
                     'ignore-optional-capability': 'enable',
                     'keepalive-timer': '36',
                     'log-neighbour-changes': 'enable',
                     'network-import-check': 'enable',
                     'router-id': 'test_value_39',
                     'scan-time': '40',
                     'synchronization': 'enable'
                     }

    set_method_mock.assert_called_with('router', 'bgp', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_router_bgp_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'router_bgp': {
            'random_attribute_not_valid': 'tag', 'always_compare_med': 'enable',
            'as': '4',
            'bestpath_as_path_ignore': 'enable',
            'bestpath_cmp_confed_aspath': 'enable',
            'bestpath_cmp_routerid': 'enable',
            'bestpath_med_confed': 'enable',
            'bestpath_med_missing_as_worst': 'enable',
            'client_to_client_reflection': 'enable',
            'cluster_id': 'test_value_11',
            'confederation_identifier': '12',
            'dampening': 'enable',
            'dampening_max_suppress_time': '14',
            'dampening_reachability_half_life': '15',
            'dampening_reuse': '16',
            'dampening_route_map': 'test_value_17',
            'dampening_suppress': '18',
            'dampening_unreachability_half_life': '19',
            'default_local_preference': '20',
            'deterministic_med': 'enable',
            'distance_external': '22',
            'distance_internal': '23',
            'distance_local': '24',
            'ebgp_multipath': 'enable',
            'enforce_first_as': 'enable',
            'fast_external_failover': 'enable',
            'graceful_end_on_timer': 'enable',
            'graceful_restart': 'enable',
            'graceful_restart_time': '30',
            'graceful_stalepath_time': '31',
            'graceful_update_delay': '32',
            'holdtime_timer': '33',
            'ibgp_multipath': 'enable',
            'ignore_optional_capability': 'enable',
            'keepalive_timer': '36',
            'log_neighbour_changes': 'enable',
            'network_import_check': 'enable',
            'router_id': 'test_value_39',
            'scan_time': '40',
            'synchronization': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_router_bgp.fortios_router(input_data, fos_instance)

    expected_data = {'always-compare-med': 'enable',
                     'as': '4',
                     'bestpath-as-path-ignore': 'enable',
                     'bestpath-cmp-confed-aspath': 'enable',
                     'bestpath-cmp-routerid': 'enable',
                     'bestpath-med-confed': 'enable',
                     'bestpath-med-missing-as-worst': 'enable',
                     'client-to-client-reflection': 'enable',
                     'cluster-id': 'test_value_11',
                     'confederation-identifier': '12',
                     'dampening': 'enable',
                     'dampening-max-suppress-time': '14',
                     'dampening-reachability-half-life': '15',
                     'dampening-reuse': '16',
                     'dampening-route-map': 'test_value_17',
                     'dampening-suppress': '18',
                     'dampening-unreachability-half-life': '19',
                     'default-local-preference': '20',
                     'deterministic-med': 'enable',
                     'distance-external': '22',
                     'distance-internal': '23',
                     'distance-local': '24',
                     'ebgp-multipath': 'enable',
                     'enforce-first-as': 'enable',
                     'fast-external-failover': 'enable',
                     'graceful-end-on-timer': 'enable',
                     'graceful-restart': 'enable',
                     'graceful-restart-time': '30',
                     'graceful-stalepath-time': '31',
                     'graceful-update-delay': '32',
                     'holdtime-timer': '33',
                     'ibgp-multipath': 'enable',
                     'ignore-optional-capability': 'enable',
                     'keepalive-timer': '36',
                     'log-neighbour-changes': 'enable',
                     'network-import-check': 'enable',
                     'router-id': 'test_value_39',
                     'scan-time': '40',
                     'synchronization': 'enable'
                     }

    set_method_mock.assert_called_with('router', 'bgp', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
