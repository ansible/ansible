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
    from ansible.modules.network.fortios import fortios_system_ha
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_system_ha.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_system_ha_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_ha': {
            'arps': '3',
            'arps_interval': '4',
            'authentication': 'enable',
            'cpu_threshold': 'test_value_6',
            'encryption': 'enable',
            'ftp_proxy_threshold': 'test_value_8',
            'gratuitous_arps': 'enable',
            'group_id': '10',
            'group_name': 'test_value_11',
            'ha_direct': 'enable',
            'ha_eth_type': 'test_value_13',
            'ha_mgmt_status': 'enable',
            'ha_uptime_diff_margin': '15',
            'hb_interval': '16',
            'hb_lost_threshold': '17',
            'hbdev': 'test_value_18',
            'hc_eth_type': 'test_value_19',
            'hello_holddown': '20',
            'http_proxy_threshold': 'test_value_21',
            'imap_proxy_threshold': 'test_value_22',
            'inter_cluster_session_sync': 'enable',
            'key': 'test_value_24',
            'l2ep_eth_type': 'test_value_25',
            'link_failed_signal': 'enable',
            'load_balance_all': 'enable',
            'memory_compatible_mode': 'enable',
            'memory_threshold': 'test_value_29',
            'mode': 'standalone',
            'monitor': 'test_value_31',
            'multicast_ttl': '32',
            'nntp_proxy_threshold': 'test_value_33',
            'override': 'enable',
            'override_wait_time': '35',
            'password': 'test_value_36',
            'pingserver_failover_threshold': '37',
            'pingserver_flip_timeout': '38',
            'pingserver_monitor_interface': 'test_value_39',
            'pingserver_slave_force_reset': 'enable',
            'pop3_proxy_threshold': 'test_value_41',
            'priority': '42',
            'route_hold': '43',
            'route_ttl': '44',
            'route_wait': '45',
            'schedule': 'none',
            'session_pickup': 'enable',
            'session_pickup_connectionless': 'enable',
            'session_pickup_delay': 'enable',
            'session_pickup_expectation': 'enable',
            'session_pickup_nat': 'enable',
            'session_sync_dev': 'test_value_52',
            'smtp_proxy_threshold': 'test_value_53',
            'standalone_config_sync': 'enable',
            'standalone_mgmt_vdom': 'enable',
            'sync_config': 'enable',
            'sync_packet_balance': 'enable',
            'unicast_hb': 'enable',
            'unicast_hb_netmask': 'test_value_59',
            'unicast_hb_peerip': 'test_value_60',
            'uninterruptible_upgrade': 'enable',
            'vcluster_id': '62',
            'vcluster2': 'enable',
            'vdom': 'test_value_64',
            'weight': 'test_value_65'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_ha.fortios_system(input_data, fos_instance)

    expected_data = {
        'arps': '3',
                'arps-interval': '4',
                'authentication': 'enable',
                'cpu-threshold': 'test_value_6',
                'encryption': 'enable',
                'ftp-proxy-threshold': 'test_value_8',
                'gratuitous-arps': 'enable',
                'group-id': '10',
                'group-name': 'test_value_11',
                'ha-direct': 'enable',
                'ha-eth-type': 'test_value_13',
                'ha-mgmt-status': 'enable',
                'ha-uptime-diff-margin': '15',
                'hb-interval': '16',
                'hb-lost-threshold': '17',
                'hbdev': 'test_value_18',
                'hc-eth-type': 'test_value_19',
                'hello-holddown': '20',
                'http-proxy-threshold': 'test_value_21',
                'imap-proxy-threshold': 'test_value_22',
                'inter-cluster-session-sync': 'enable',
                'key': 'test_value_24',
                'l2ep-eth-type': 'test_value_25',
                'link-failed-signal': 'enable',
                'load-balance-all': 'enable',
                'memory-compatible-mode': 'enable',
                'memory-threshold': 'test_value_29',
                'mode': 'standalone',
                'monitor': 'test_value_31',
                'multicast-ttl': '32',
                'nntp-proxy-threshold': 'test_value_33',
                'override': 'enable',
                'override-wait-time': '35',
                'password': 'test_value_36',
                'pingserver-failover-threshold': '37',
                'pingserver-flip-timeout': '38',
                'pingserver-monitor-interface': 'test_value_39',
                'pingserver-slave-force-reset': 'enable',
                'pop3-proxy-threshold': 'test_value_41',
                'priority': '42',
                'route-hold': '43',
                'route-ttl': '44',
                'route-wait': '45',
                'schedule': 'none',
                'session-pickup': 'enable',
                'session-pickup-connectionless': 'enable',
                'session-pickup-delay': 'enable',
                'session-pickup-expectation': 'enable',
                'session-pickup-nat': 'enable',
                'session-sync-dev': 'test_value_52',
                'smtp-proxy-threshold': 'test_value_53',
                'standalone-config-sync': 'enable',
                'standalone-mgmt-vdom': 'enable',
                'sync-config': 'enable',
                'sync-packet-balance': 'enable',
                'unicast-hb': 'enable',
                'unicast-hb-netmask': 'test_value_59',
                'unicast-hb-peerip': 'test_value_60',
                'uninterruptible-upgrade': 'enable',
                'vcluster-id': '62',
                'vcluster2': 'enable',
                'vdom': 'test_value_64',
                'weight': 'test_value_65'
    }

    set_method_mock.assert_called_with('system', 'ha', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_ha_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_ha': {
            'arps': '3',
            'arps_interval': '4',
            'authentication': 'enable',
            'cpu_threshold': 'test_value_6',
            'encryption': 'enable',
            'ftp_proxy_threshold': 'test_value_8',
            'gratuitous_arps': 'enable',
            'group_id': '10',
            'group_name': 'test_value_11',
            'ha_direct': 'enable',
            'ha_eth_type': 'test_value_13',
            'ha_mgmt_status': 'enable',
            'ha_uptime_diff_margin': '15',
            'hb_interval': '16',
            'hb_lost_threshold': '17',
            'hbdev': 'test_value_18',
            'hc_eth_type': 'test_value_19',
            'hello_holddown': '20',
            'http_proxy_threshold': 'test_value_21',
            'imap_proxy_threshold': 'test_value_22',
            'inter_cluster_session_sync': 'enable',
            'key': 'test_value_24',
            'l2ep_eth_type': 'test_value_25',
            'link_failed_signal': 'enable',
            'load_balance_all': 'enable',
            'memory_compatible_mode': 'enable',
            'memory_threshold': 'test_value_29',
            'mode': 'standalone',
            'monitor': 'test_value_31',
            'multicast_ttl': '32',
            'nntp_proxy_threshold': 'test_value_33',
            'override': 'enable',
            'override_wait_time': '35',
            'password': 'test_value_36',
            'pingserver_failover_threshold': '37',
            'pingserver_flip_timeout': '38',
            'pingserver_monitor_interface': 'test_value_39',
            'pingserver_slave_force_reset': 'enable',
            'pop3_proxy_threshold': 'test_value_41',
            'priority': '42',
            'route_hold': '43',
            'route_ttl': '44',
            'route_wait': '45',
            'schedule': 'none',
            'session_pickup': 'enable',
            'session_pickup_connectionless': 'enable',
            'session_pickup_delay': 'enable',
            'session_pickup_expectation': 'enable',
            'session_pickup_nat': 'enable',
            'session_sync_dev': 'test_value_52',
            'smtp_proxy_threshold': 'test_value_53',
            'standalone_config_sync': 'enable',
            'standalone_mgmt_vdom': 'enable',
            'sync_config': 'enable',
            'sync_packet_balance': 'enable',
            'unicast_hb': 'enable',
            'unicast_hb_netmask': 'test_value_59',
            'unicast_hb_peerip': 'test_value_60',
            'uninterruptible_upgrade': 'enable',
            'vcluster_id': '62',
            'vcluster2': 'enable',
            'vdom': 'test_value_64',
            'weight': 'test_value_65'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_ha.fortios_system(input_data, fos_instance)

    expected_data = {
        'arps': '3',
                'arps-interval': '4',
                'authentication': 'enable',
                'cpu-threshold': 'test_value_6',
                'encryption': 'enable',
                'ftp-proxy-threshold': 'test_value_8',
                'gratuitous-arps': 'enable',
                'group-id': '10',
                'group-name': 'test_value_11',
                'ha-direct': 'enable',
                'ha-eth-type': 'test_value_13',
                'ha-mgmt-status': 'enable',
                'ha-uptime-diff-margin': '15',
                'hb-interval': '16',
                'hb-lost-threshold': '17',
                'hbdev': 'test_value_18',
                'hc-eth-type': 'test_value_19',
                'hello-holddown': '20',
                'http-proxy-threshold': 'test_value_21',
                'imap-proxy-threshold': 'test_value_22',
                'inter-cluster-session-sync': 'enable',
                'key': 'test_value_24',
                'l2ep-eth-type': 'test_value_25',
                'link-failed-signal': 'enable',
                'load-balance-all': 'enable',
                'memory-compatible-mode': 'enable',
                'memory-threshold': 'test_value_29',
                'mode': 'standalone',
                'monitor': 'test_value_31',
                'multicast-ttl': '32',
                'nntp-proxy-threshold': 'test_value_33',
                'override': 'enable',
                'override-wait-time': '35',
                'password': 'test_value_36',
                'pingserver-failover-threshold': '37',
                'pingserver-flip-timeout': '38',
                'pingserver-monitor-interface': 'test_value_39',
                'pingserver-slave-force-reset': 'enable',
                'pop3-proxy-threshold': 'test_value_41',
                'priority': '42',
                'route-hold': '43',
                'route-ttl': '44',
                'route-wait': '45',
                'schedule': 'none',
                'session-pickup': 'enable',
                'session-pickup-connectionless': 'enable',
                'session-pickup-delay': 'enable',
                'session-pickup-expectation': 'enable',
                'session-pickup-nat': 'enable',
                'session-sync-dev': 'test_value_52',
                'smtp-proxy-threshold': 'test_value_53',
                'standalone-config-sync': 'enable',
                'standalone-mgmt-vdom': 'enable',
                'sync-config': 'enable',
                'sync-packet-balance': 'enable',
                'unicast-hb': 'enable',
                'unicast-hb-netmask': 'test_value_59',
                'unicast-hb-peerip': 'test_value_60',
                'uninterruptible-upgrade': 'enable',
                'vcluster-id': '62',
                'vcluster2': 'enable',
                'vdom': 'test_value_64',
                'weight': 'test_value_65'
    }

    set_method_mock.assert_called_with('system', 'ha', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_ha_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_ha': {
            'arps': '3',
            'arps_interval': '4',
            'authentication': 'enable',
            'cpu_threshold': 'test_value_6',
            'encryption': 'enable',
            'ftp_proxy_threshold': 'test_value_8',
            'gratuitous_arps': 'enable',
            'group_id': '10',
            'group_name': 'test_value_11',
            'ha_direct': 'enable',
            'ha_eth_type': 'test_value_13',
            'ha_mgmt_status': 'enable',
            'ha_uptime_diff_margin': '15',
            'hb_interval': '16',
            'hb_lost_threshold': '17',
            'hbdev': 'test_value_18',
            'hc_eth_type': 'test_value_19',
            'hello_holddown': '20',
            'http_proxy_threshold': 'test_value_21',
            'imap_proxy_threshold': 'test_value_22',
            'inter_cluster_session_sync': 'enable',
            'key': 'test_value_24',
            'l2ep_eth_type': 'test_value_25',
            'link_failed_signal': 'enable',
            'load_balance_all': 'enable',
            'memory_compatible_mode': 'enable',
            'memory_threshold': 'test_value_29',
            'mode': 'standalone',
            'monitor': 'test_value_31',
            'multicast_ttl': '32',
            'nntp_proxy_threshold': 'test_value_33',
            'override': 'enable',
            'override_wait_time': '35',
            'password': 'test_value_36',
            'pingserver_failover_threshold': '37',
            'pingserver_flip_timeout': '38',
            'pingserver_monitor_interface': 'test_value_39',
            'pingserver_slave_force_reset': 'enable',
            'pop3_proxy_threshold': 'test_value_41',
            'priority': '42',
            'route_hold': '43',
            'route_ttl': '44',
            'route_wait': '45',
            'schedule': 'none',
            'session_pickup': 'enable',
            'session_pickup_connectionless': 'enable',
            'session_pickup_delay': 'enable',
            'session_pickup_expectation': 'enable',
            'session_pickup_nat': 'enable',
            'session_sync_dev': 'test_value_52',
            'smtp_proxy_threshold': 'test_value_53',
            'standalone_config_sync': 'enable',
            'standalone_mgmt_vdom': 'enable',
            'sync_config': 'enable',
            'sync_packet_balance': 'enable',
            'unicast_hb': 'enable',
            'unicast_hb_netmask': 'test_value_59',
            'unicast_hb_peerip': 'test_value_60',
            'uninterruptible_upgrade': 'enable',
            'vcluster_id': '62',
            'vcluster2': 'enable',
            'vdom': 'test_value_64',
            'weight': 'test_value_65'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_ha.fortios_system(input_data, fos_instance)

    expected_data = {
        'arps': '3',
                'arps-interval': '4',
                'authentication': 'enable',
                'cpu-threshold': 'test_value_6',
                'encryption': 'enable',
                'ftp-proxy-threshold': 'test_value_8',
                'gratuitous-arps': 'enable',
                'group-id': '10',
                'group-name': 'test_value_11',
                'ha-direct': 'enable',
                'ha-eth-type': 'test_value_13',
                'ha-mgmt-status': 'enable',
                'ha-uptime-diff-margin': '15',
                'hb-interval': '16',
                'hb-lost-threshold': '17',
                'hbdev': 'test_value_18',
                'hc-eth-type': 'test_value_19',
                'hello-holddown': '20',
                'http-proxy-threshold': 'test_value_21',
                'imap-proxy-threshold': 'test_value_22',
                'inter-cluster-session-sync': 'enable',
                'key': 'test_value_24',
                'l2ep-eth-type': 'test_value_25',
                'link-failed-signal': 'enable',
                'load-balance-all': 'enable',
                'memory-compatible-mode': 'enable',
                'memory-threshold': 'test_value_29',
                'mode': 'standalone',
                'monitor': 'test_value_31',
                'multicast-ttl': '32',
                'nntp-proxy-threshold': 'test_value_33',
                'override': 'enable',
                'override-wait-time': '35',
                'password': 'test_value_36',
                'pingserver-failover-threshold': '37',
                'pingserver-flip-timeout': '38',
                'pingserver-monitor-interface': 'test_value_39',
                'pingserver-slave-force-reset': 'enable',
                'pop3-proxy-threshold': 'test_value_41',
                'priority': '42',
                'route-hold': '43',
                'route-ttl': '44',
                'route-wait': '45',
                'schedule': 'none',
                'session-pickup': 'enable',
                'session-pickup-connectionless': 'enable',
                'session-pickup-delay': 'enable',
                'session-pickup-expectation': 'enable',
                'session-pickup-nat': 'enable',
                'session-sync-dev': 'test_value_52',
                'smtp-proxy-threshold': 'test_value_53',
                'standalone-config-sync': 'enable',
                'standalone-mgmt-vdom': 'enable',
                'sync-config': 'enable',
                'sync-packet-balance': 'enable',
                'unicast-hb': 'enable',
                'unicast-hb-netmask': 'test_value_59',
                'unicast-hb-peerip': 'test_value_60',
                'uninterruptible-upgrade': 'enable',
                'vcluster-id': '62',
                'vcluster2': 'enable',
                'vdom': 'test_value_64',
                'weight': 'test_value_65'
    }

    set_method_mock.assert_called_with('system', 'ha', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_system_ha_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_ha': {
            'random_attribute_not_valid': 'tag',
            'arps': '3',
            'arps_interval': '4',
            'authentication': 'enable',
            'cpu_threshold': 'test_value_6',
            'encryption': 'enable',
            'ftp_proxy_threshold': 'test_value_8',
            'gratuitous_arps': 'enable',
            'group_id': '10',
            'group_name': 'test_value_11',
            'ha_direct': 'enable',
            'ha_eth_type': 'test_value_13',
            'ha_mgmt_status': 'enable',
            'ha_uptime_diff_margin': '15',
            'hb_interval': '16',
            'hb_lost_threshold': '17',
            'hbdev': 'test_value_18',
            'hc_eth_type': 'test_value_19',
            'hello_holddown': '20',
            'http_proxy_threshold': 'test_value_21',
            'imap_proxy_threshold': 'test_value_22',
            'inter_cluster_session_sync': 'enable',
            'key': 'test_value_24',
            'l2ep_eth_type': 'test_value_25',
            'link_failed_signal': 'enable',
            'load_balance_all': 'enable',
            'memory_compatible_mode': 'enable',
            'memory_threshold': 'test_value_29',
            'mode': 'standalone',
            'monitor': 'test_value_31',
            'multicast_ttl': '32',
            'nntp_proxy_threshold': 'test_value_33',
            'override': 'enable',
            'override_wait_time': '35',
            'password': 'test_value_36',
            'pingserver_failover_threshold': '37',
            'pingserver_flip_timeout': '38',
            'pingserver_monitor_interface': 'test_value_39',
            'pingserver_slave_force_reset': 'enable',
            'pop3_proxy_threshold': 'test_value_41',
            'priority': '42',
            'route_hold': '43',
            'route_ttl': '44',
            'route_wait': '45',
            'schedule': 'none',
            'session_pickup': 'enable',
            'session_pickup_connectionless': 'enable',
            'session_pickup_delay': 'enable',
            'session_pickup_expectation': 'enable',
            'session_pickup_nat': 'enable',
            'session_sync_dev': 'test_value_52',
            'smtp_proxy_threshold': 'test_value_53',
            'standalone_config_sync': 'enable',
            'standalone_mgmt_vdom': 'enable',
            'sync_config': 'enable',
            'sync_packet_balance': 'enable',
            'unicast_hb': 'enable',
            'unicast_hb_netmask': 'test_value_59',
            'unicast_hb_peerip': 'test_value_60',
            'uninterruptible_upgrade': 'enable',
            'vcluster_id': '62',
            'vcluster2': 'enable',
            'vdom': 'test_value_64',
            'weight': 'test_value_65'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_ha.fortios_system(input_data, fos_instance)

    expected_data = {
        'arps': '3',
                'arps-interval': '4',
                'authentication': 'enable',
                'cpu-threshold': 'test_value_6',
                'encryption': 'enable',
                'ftp-proxy-threshold': 'test_value_8',
                'gratuitous-arps': 'enable',
                'group-id': '10',
                'group-name': 'test_value_11',
                'ha-direct': 'enable',
                'ha-eth-type': 'test_value_13',
                'ha-mgmt-status': 'enable',
                'ha-uptime-diff-margin': '15',
                'hb-interval': '16',
                'hb-lost-threshold': '17',
                'hbdev': 'test_value_18',
                'hc-eth-type': 'test_value_19',
                'hello-holddown': '20',
                'http-proxy-threshold': 'test_value_21',
                'imap-proxy-threshold': 'test_value_22',
                'inter-cluster-session-sync': 'enable',
                'key': 'test_value_24',
                'l2ep-eth-type': 'test_value_25',
                'link-failed-signal': 'enable',
                'load-balance-all': 'enable',
                'memory-compatible-mode': 'enable',
                'memory-threshold': 'test_value_29',
                'mode': 'standalone',
                'monitor': 'test_value_31',
                'multicast-ttl': '32',
                'nntp-proxy-threshold': 'test_value_33',
                'override': 'enable',
                'override-wait-time': '35',
                'password': 'test_value_36',
                'pingserver-failover-threshold': '37',
                'pingserver-flip-timeout': '38',
                'pingserver-monitor-interface': 'test_value_39',
                'pingserver-slave-force-reset': 'enable',
                'pop3-proxy-threshold': 'test_value_41',
                'priority': '42',
                'route-hold': '43',
                'route-ttl': '44',
                'route-wait': '45',
                'schedule': 'none',
                'session-pickup': 'enable',
                'session-pickup-connectionless': 'enable',
                'session-pickup-delay': 'enable',
                'session-pickup-expectation': 'enable',
                'session-pickup-nat': 'enable',
                'session-sync-dev': 'test_value_52',
                'smtp-proxy-threshold': 'test_value_53',
                'standalone-config-sync': 'enable',
                'standalone-mgmt-vdom': 'enable',
                'sync-config': 'enable',
                'sync-packet-balance': 'enable',
                'unicast-hb': 'enable',
                'unicast-hb-netmask': 'test_value_59',
                'unicast-hb-peerip': 'test_value_60',
                'uninterruptible-upgrade': 'enable',
                'vcluster-id': '62',
                'vcluster2': 'enable',
                'vdom': 'test_value_64',
                'weight': 'test_value_65'
    }

    set_method_mock.assert_called_with('system', 'ha', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
