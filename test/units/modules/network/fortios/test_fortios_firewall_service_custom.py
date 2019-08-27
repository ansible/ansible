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
    from ansible.modules.network.fortios import fortios_firewall_service_custom
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_firewall_service_custom.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_firewall_service_custom_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_service_custom': {'app_service_type': 'disable',
                                    'category': 'test_value_4',
                                    'check_reset_range': 'disable',
                                    'color': '6',
                                    'comment': 'Comment.',
                                    'fqdn': 'test_value_8',
                                    'helper': 'auto',
                                    'icmpcode': '10',
                                    'icmptype': '11',
                                    'iprange': 'test_value_12',
                                    'name': 'default_name_13',
                                    'protocol': 'TCP/UDP/SCTP',
                                    'protocol_number': '15',
                                    'proxy': 'enable',
                                    'sctp_portrange': 'test_value_17',
                                    'session_ttl': '18',
                                    'tcp_halfclose_timer': '19',
                                    'tcp_halfopen_timer': '20',
                                    'tcp_portrange': 'test_value_21',
                                    'tcp_timewait_timer': '22',
                                    'udp_idle_timer': '23',
                                    'udp_portrange': 'test_value_24',
                                    'visibility': 'enable'
                                    },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_service_custom.fortios_firewall_service(input_data, fos_instance)

    expected_data = {'app-service-type': 'disable',
                     'category': 'test_value_4',
                     'check-reset-range': 'disable',
                     'color': '6',
                     'comment': 'Comment.',
                     'fqdn': 'test_value_8',
                     'helper': 'auto',
                     'icmpcode': '10',
                     'icmptype': '11',
                     'iprange': 'test_value_12',
                     'name': 'default_name_13',
                     'protocol': 'TCP/UDP/SCTP',
                     'protocol-number': '15',
                     'proxy': 'enable',
                     'sctp-portrange': 'test_value_17',
                     'session-ttl': '18',
                     'tcp-halfclose-timer': '19',
                     'tcp-halfopen-timer': '20',
                     'tcp-portrange': 'test_value_21',
                     'tcp-timewait-timer': '22',
                     'udp-idle-timer': '23',
                     'udp-portrange': 'test_value_24',
                     'visibility': 'enable'
                     }

    set_method_mock.assert_called_with('firewall.service', 'custom', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_service_custom_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_service_custom': {'app_service_type': 'disable',
                                    'category': 'test_value_4',
                                    'check_reset_range': 'disable',
                                    'color': '6',
                                    'comment': 'Comment.',
                                    'fqdn': 'test_value_8',
                                    'helper': 'auto',
                                    'icmpcode': '10',
                                    'icmptype': '11',
                                    'iprange': 'test_value_12',
                                    'name': 'default_name_13',
                                    'protocol': 'TCP/UDP/SCTP',
                                    'protocol_number': '15',
                                    'proxy': 'enable',
                                    'sctp_portrange': 'test_value_17',
                                    'session_ttl': '18',
                                    'tcp_halfclose_timer': '19',
                                    'tcp_halfopen_timer': '20',
                                    'tcp_portrange': 'test_value_21',
                                    'tcp_timewait_timer': '22',
                                    'udp_idle_timer': '23',
                                    'udp_portrange': 'test_value_24',
                                    'visibility': 'enable'
                                    },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_service_custom.fortios_firewall_service(input_data, fos_instance)

    expected_data = {'app-service-type': 'disable',
                     'category': 'test_value_4',
                     'check-reset-range': 'disable',
                     'color': '6',
                     'comment': 'Comment.',
                     'fqdn': 'test_value_8',
                     'helper': 'auto',
                     'icmpcode': '10',
                     'icmptype': '11',
                     'iprange': 'test_value_12',
                     'name': 'default_name_13',
                     'protocol': 'TCP/UDP/SCTP',
                     'protocol-number': '15',
                     'proxy': 'enable',
                     'sctp-portrange': 'test_value_17',
                     'session-ttl': '18',
                     'tcp-halfclose-timer': '19',
                     'tcp-halfopen-timer': '20',
                     'tcp-portrange': 'test_value_21',
                     'tcp-timewait-timer': '22',
                     'udp-idle-timer': '23',
                     'udp-portrange': 'test_value_24',
                     'visibility': 'enable'
                     }

    set_method_mock.assert_called_with('firewall.service', 'custom', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_service_custom_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_service_custom': {'app_service_type': 'disable',
                                    'category': 'test_value_4',
                                    'check_reset_range': 'disable',
                                    'color': '6',
                                    'comment': 'Comment.',
                                    'fqdn': 'test_value_8',
                                    'helper': 'auto',
                                    'icmpcode': '10',
                                    'icmptype': '11',
                                    'iprange': 'test_value_12',
                                    'name': 'default_name_13',
                                    'protocol': 'TCP/UDP/SCTP',
                                    'protocol_number': '15',
                                    'proxy': 'enable',
                                    'sctp_portrange': 'test_value_17',
                                    'session_ttl': '18',
                                    'tcp_halfclose_timer': '19',
                                    'tcp_halfopen_timer': '20',
                                    'tcp_portrange': 'test_value_21',
                                    'tcp_timewait_timer': '22',
                                    'udp_idle_timer': '23',
                                    'udp_portrange': 'test_value_24',
                                    'visibility': 'enable'
                                    },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_service_custom.fortios_firewall_service(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall.service', 'custom', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_service_custom_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_service_custom': {'app_service_type': 'disable',
                                    'category': 'test_value_4',
                                    'check_reset_range': 'disable',
                                    'color': '6',
                                    'comment': 'Comment.',
                                    'fqdn': 'test_value_8',
                                    'helper': 'auto',
                                    'icmpcode': '10',
                                    'icmptype': '11',
                                    'iprange': 'test_value_12',
                                    'name': 'default_name_13',
                                    'protocol': 'TCP/UDP/SCTP',
                                    'protocol_number': '15',
                                    'proxy': 'enable',
                                    'sctp_portrange': 'test_value_17',
                                    'session_ttl': '18',
                                    'tcp_halfclose_timer': '19',
                                    'tcp_halfopen_timer': '20',
                                    'tcp_portrange': 'test_value_21',
                                    'tcp_timewait_timer': '22',
                                    'udp_idle_timer': '23',
                                    'udp_portrange': 'test_value_24',
                                    'visibility': 'enable'
                                    },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_service_custom.fortios_firewall_service(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall.service', 'custom', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_service_custom_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_service_custom': {'app_service_type': 'disable',
                                    'category': 'test_value_4',
                                    'check_reset_range': 'disable',
                                    'color': '6',
                                    'comment': 'Comment.',
                                    'fqdn': 'test_value_8',
                                    'helper': 'auto',
                                    'icmpcode': '10',
                                    'icmptype': '11',
                                    'iprange': 'test_value_12',
                                    'name': 'default_name_13',
                                    'protocol': 'TCP/UDP/SCTP',
                                    'protocol_number': '15',
                                    'proxy': 'enable',
                                    'sctp_portrange': 'test_value_17',
                                    'session_ttl': '18',
                                    'tcp_halfclose_timer': '19',
                                    'tcp_halfopen_timer': '20',
                                    'tcp_portrange': 'test_value_21',
                                    'tcp_timewait_timer': '22',
                                    'udp_idle_timer': '23',
                                    'udp_portrange': 'test_value_24',
                                    'visibility': 'enable'
                                    },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_service_custom.fortios_firewall_service(input_data, fos_instance)

    expected_data = {'app-service-type': 'disable',
                     'category': 'test_value_4',
                     'check-reset-range': 'disable',
                     'color': '6',
                     'comment': 'Comment.',
                     'fqdn': 'test_value_8',
                     'helper': 'auto',
                     'icmpcode': '10',
                     'icmptype': '11',
                     'iprange': 'test_value_12',
                     'name': 'default_name_13',
                     'protocol': 'TCP/UDP/SCTP',
                     'protocol-number': '15',
                     'proxy': 'enable',
                     'sctp-portrange': 'test_value_17',
                     'session-ttl': '18',
                     'tcp-halfclose-timer': '19',
                     'tcp-halfopen-timer': '20',
                     'tcp-portrange': 'test_value_21',
                     'tcp-timewait-timer': '22',
                     'udp-idle-timer': '23',
                     'udp-portrange': 'test_value_24',
                     'visibility': 'enable'
                     }

    set_method_mock.assert_called_with('firewall.service', 'custom', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_firewall_service_custom_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_service_custom': {
            'random_attribute_not_valid': 'tag', 'app_service_type': 'disable',
            'category': 'test_value_4',
            'check_reset_range': 'disable',
            'color': '6',
            'comment': 'Comment.',
            'fqdn': 'test_value_8',
            'helper': 'auto',
            'icmpcode': '10',
            'icmptype': '11',
            'iprange': 'test_value_12',
            'name': 'default_name_13',
            'protocol': 'TCP/UDP/SCTP',
            'protocol_number': '15',
            'proxy': 'enable',
            'sctp_portrange': 'test_value_17',
            'session_ttl': '18',
            'tcp_halfclose_timer': '19',
            'tcp_halfopen_timer': '20',
            'tcp_portrange': 'test_value_21',
            'tcp_timewait_timer': '22',
            'udp_idle_timer': '23',
            'udp_portrange': 'test_value_24',
            'visibility': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_service_custom.fortios_firewall_service(input_data, fos_instance)

    expected_data = {'app-service-type': 'disable',
                     'category': 'test_value_4',
                     'check-reset-range': 'disable',
                     'color': '6',
                     'comment': 'Comment.',
                     'fqdn': 'test_value_8',
                     'helper': 'auto',
                     'icmpcode': '10',
                     'icmptype': '11',
                     'iprange': 'test_value_12',
                     'name': 'default_name_13',
                     'protocol': 'TCP/UDP/SCTP',
                     'protocol-number': '15',
                     'proxy': 'enable',
                     'sctp-portrange': 'test_value_17',
                     'session-ttl': '18',
                     'tcp-halfclose-timer': '19',
                     'tcp-halfopen-timer': '20',
                     'tcp-portrange': 'test_value_21',
                     'tcp-timewait-timer': '22',
                     'udp-idle-timer': '23',
                     'udp-portrange': 'test_value_24',
                     'visibility': 'enable'
                     }

    set_method_mock.assert_called_with('firewall.service', 'custom', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
