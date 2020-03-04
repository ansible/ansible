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
    from ansible.modules.network.fortios import fortios_vpn_ipsec_phase2_interface
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_vpn_ipsec_phase2_interface.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_vpn_ipsec_phase2_interface_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ipsec_phase2_interface': {
            'add_route': 'phase1',
            'auto_discovery_forwarder': 'phase1',
            'auto_discovery_sender': 'phase1',
            'auto_negotiate': 'enable',
            'comments': 'test_value_7',
            'dhcp_ipsec': 'enable',
            'dhgrp': '1',
            'dst_addr_type': 'subnet',
            'dst_end_ip': 'test_value_11',
            'dst_end_ip6': 'test_value_12',
            'dst_name': 'test_value_13',
            'dst_name6': 'test_value_14',
            'dst_port': '15',
            'dst_start_ip': 'test_value_16',
            'dst_start_ip6': 'test_value_17',
            'dst_subnet': 'test_value_18',
            'dst_subnet6': 'test_value_19',
            'encapsulation': 'tunnel-mode',
            'keepalive': 'enable',
            'keylife_type': 'seconds',
            'keylifekbs': '23',
            'keylifeseconds': '24',
            'l2tp': 'enable',
            'name': 'default_name_26',
            'pfs': 'enable',
            'phase1name': 'test_value_28',
            'protocol': '29',
            'replay': 'enable',
            'route_overlap': 'use-old',
            'single_source': 'enable',
            'src_addr_type': 'subnet',
            'src_end_ip': 'test_value_34',
            'src_end_ip6': 'test_value_35',
            'src_name': 'test_value_36',
            'src_name6': 'test_value_37',
            'src_port': '38',
            'src_start_ip': 'test_value_39',
            'src_start_ip6': 'test_value_40',
            'src_subnet': 'test_value_41',
            'src_subnet6': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_phase2_interface.fortios_vpn_ipsec(input_data, fos_instance)

    expected_data = {
        'add-route': 'phase1',
        'auto-discovery-forwarder': 'phase1',
        'auto-discovery-sender': 'phase1',
        'auto-negotiate': 'enable',
        'comments': 'test_value_7',
        'dhcp-ipsec': 'enable',
        'dhgrp': '1',
        'dst-addr-type': 'subnet',
        'dst-end-ip': 'test_value_11',
        'dst-end-ip6': 'test_value_12',
        'dst-name': 'test_value_13',
        'dst-name6': 'test_value_14',
        'dst-port': '15',
        'dst-start-ip': 'test_value_16',
        'dst-start-ip6': 'test_value_17',
        'dst-subnet': 'test_value_18',
        'dst-subnet6': 'test_value_19',
        'encapsulation': 'tunnel-mode',
        'keepalive': 'enable',
        'keylife-type': 'seconds',
        'keylifekbs': '23',
        'keylifeseconds': '24',
        'l2tp': 'enable',
                'name': 'default_name_26',
                'pfs': 'enable',
                'phase1name': 'test_value_28',
                'protocol': '29',
                'replay': 'enable',
                'route-overlap': 'use-old',
                'single-source': 'enable',
                'src-addr-type': 'subnet',
                'src-end-ip': 'test_value_34',
                'src-end-ip6': 'test_value_35',
                'src-name': 'test_value_36',
                'src-name6': 'test_value_37',
                'src-port': '38',
                'src-start-ip': 'test_value_39',
                'src-start-ip6': 'test_value_40',
                'src-subnet': 'test_value_41',
                'src-subnet6': 'test_value_42'
    }

    set_method_mock.assert_called_with('vpn.ipsec', 'phase2-interface', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_vpn_ipsec_phase2_interface_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ipsec_phase2_interface': {
            'add_route': 'phase1',
            'auto_discovery_forwarder': 'phase1',
            'auto_discovery_sender': 'phase1',
            'auto_negotiate': 'enable',
            'comments': 'test_value_7',
            'dhcp_ipsec': 'enable',
            'dhgrp': '1',
            'dst_addr_type': 'subnet',
            'dst_end_ip': 'test_value_11',
            'dst_end_ip6': 'test_value_12',
            'dst_name': 'test_value_13',
            'dst_name6': 'test_value_14',
            'dst_port': '15',
            'dst_start_ip': 'test_value_16',
            'dst_start_ip6': 'test_value_17',
            'dst_subnet': 'test_value_18',
            'dst_subnet6': 'test_value_19',
            'encapsulation': 'tunnel-mode',
            'keepalive': 'enable',
            'keylife_type': 'seconds',
            'keylifekbs': '23',
            'keylifeseconds': '24',
            'l2tp': 'enable',
            'name': 'default_name_26',
            'pfs': 'enable',
            'phase1name': 'test_value_28',
            'protocol': '29',
            'replay': 'enable',
            'route_overlap': 'use-old',
            'single_source': 'enable',
            'src_addr_type': 'subnet',
            'src_end_ip': 'test_value_34',
            'src_end_ip6': 'test_value_35',
            'src_name': 'test_value_36',
            'src_name6': 'test_value_37',
            'src_port': '38',
            'src_start_ip': 'test_value_39',
            'src_start_ip6': 'test_value_40',
            'src_subnet': 'test_value_41',
            'src_subnet6': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_phase2_interface.fortios_vpn_ipsec(input_data, fos_instance)

    expected_data = {
        'add-route': 'phase1',
        'auto-discovery-forwarder': 'phase1',
        'auto-discovery-sender': 'phase1',
        'auto-negotiate': 'enable',
        'comments': 'test_value_7',
        'dhcp-ipsec': 'enable',
        'dhgrp': '1',
        'dst-addr-type': 'subnet',
        'dst-end-ip': 'test_value_11',
        'dst-end-ip6': 'test_value_12',
        'dst-name': 'test_value_13',
        'dst-name6': 'test_value_14',
        'dst-port': '15',
        'dst-start-ip': 'test_value_16',
        'dst-start-ip6': 'test_value_17',
        'dst-subnet': 'test_value_18',
        'dst-subnet6': 'test_value_19',
        'encapsulation': 'tunnel-mode',
        'keepalive': 'enable',
        'keylife-type': 'seconds',
        'keylifekbs': '23',
        'keylifeseconds': '24',
        'l2tp': 'enable',
                'name': 'default_name_26',
                'pfs': 'enable',
                'phase1name': 'test_value_28',
                'protocol': '29',
                'replay': 'enable',
                'route-overlap': 'use-old',
                'single-source': 'enable',
                'src-addr-type': 'subnet',
                'src-end-ip': 'test_value_34',
                'src-end-ip6': 'test_value_35',
                'src-name': 'test_value_36',
                'src-name6': 'test_value_37',
                'src-port': '38',
                'src-start-ip': 'test_value_39',
                'src-start-ip6': 'test_value_40',
                'src-subnet': 'test_value_41',
                'src-subnet6': 'test_value_42'
    }

    set_method_mock.assert_called_with('vpn.ipsec', 'phase2-interface', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_vpn_ipsec_phase2_interface_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'vpn_ipsec_phase2_interface': {
            'add_route': 'phase1',
            'auto_discovery_forwarder': 'phase1',
            'auto_discovery_sender': 'phase1',
            'auto_negotiate': 'enable',
            'comments': 'test_value_7',
            'dhcp_ipsec': 'enable',
            'dhgrp': '1',
            'dst_addr_type': 'subnet',
            'dst_end_ip': 'test_value_11',
            'dst_end_ip6': 'test_value_12',
            'dst_name': 'test_value_13',
            'dst_name6': 'test_value_14',
            'dst_port': '15',
            'dst_start_ip': 'test_value_16',
            'dst_start_ip6': 'test_value_17',
            'dst_subnet': 'test_value_18',
            'dst_subnet6': 'test_value_19',
            'encapsulation': 'tunnel-mode',
            'keepalive': 'enable',
            'keylife_type': 'seconds',
            'keylifekbs': '23',
            'keylifeseconds': '24',
            'l2tp': 'enable',
            'name': 'default_name_26',
            'pfs': 'enable',
            'phase1name': 'test_value_28',
            'protocol': '29',
            'replay': 'enable',
            'route_overlap': 'use-old',
            'single_source': 'enable',
            'src_addr_type': 'subnet',
            'src_end_ip': 'test_value_34',
            'src_end_ip6': 'test_value_35',
            'src_name': 'test_value_36',
            'src_name6': 'test_value_37',
            'src_port': '38',
            'src_start_ip': 'test_value_39',
            'src_start_ip6': 'test_value_40',
            'src_subnet': 'test_value_41',
            'src_subnet6': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_phase2_interface.fortios_vpn_ipsec(input_data, fos_instance)

    delete_method_mock.assert_called_with('vpn.ipsec', 'phase2-interface', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_vpn_ipsec_phase2_interface_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'vpn_ipsec_phase2_interface': {
            'add_route': 'phase1',
            'auto_discovery_forwarder': 'phase1',
            'auto_discovery_sender': 'phase1',
            'auto_negotiate': 'enable',
            'comments': 'test_value_7',
            'dhcp_ipsec': 'enable',
            'dhgrp': '1',
            'dst_addr_type': 'subnet',
            'dst_end_ip': 'test_value_11',
            'dst_end_ip6': 'test_value_12',
            'dst_name': 'test_value_13',
            'dst_name6': 'test_value_14',
            'dst_port': '15',
            'dst_start_ip': 'test_value_16',
            'dst_start_ip6': 'test_value_17',
            'dst_subnet': 'test_value_18',
            'dst_subnet6': 'test_value_19',
            'encapsulation': 'tunnel-mode',
            'keepalive': 'enable',
            'keylife_type': 'seconds',
            'keylifekbs': '23',
            'keylifeseconds': '24',
            'l2tp': 'enable',
            'name': 'default_name_26',
            'pfs': 'enable',
            'phase1name': 'test_value_28',
            'protocol': '29',
            'replay': 'enable',
            'route_overlap': 'use-old',
            'single_source': 'enable',
            'src_addr_type': 'subnet',
            'src_end_ip': 'test_value_34',
            'src_end_ip6': 'test_value_35',
            'src_name': 'test_value_36',
            'src_name6': 'test_value_37',
            'src_port': '38',
            'src_start_ip': 'test_value_39',
            'src_start_ip6': 'test_value_40',
            'src_subnet': 'test_value_41',
            'src_subnet6': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_phase2_interface.fortios_vpn_ipsec(input_data, fos_instance)

    delete_method_mock.assert_called_with('vpn.ipsec', 'phase2-interface', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_vpn_ipsec_phase2_interface_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ipsec_phase2_interface': {
            'add_route': 'phase1',
            'auto_discovery_forwarder': 'phase1',
            'auto_discovery_sender': 'phase1',
            'auto_negotiate': 'enable',
            'comments': 'test_value_7',
            'dhcp_ipsec': 'enable',
            'dhgrp': '1',
            'dst_addr_type': 'subnet',
            'dst_end_ip': 'test_value_11',
            'dst_end_ip6': 'test_value_12',
            'dst_name': 'test_value_13',
            'dst_name6': 'test_value_14',
            'dst_port': '15',
            'dst_start_ip': 'test_value_16',
            'dst_start_ip6': 'test_value_17',
            'dst_subnet': 'test_value_18',
            'dst_subnet6': 'test_value_19',
            'encapsulation': 'tunnel-mode',
            'keepalive': 'enable',
            'keylife_type': 'seconds',
            'keylifekbs': '23',
            'keylifeseconds': '24',
            'l2tp': 'enable',
            'name': 'default_name_26',
            'pfs': 'enable',
            'phase1name': 'test_value_28',
            'protocol': '29',
            'replay': 'enable',
            'route_overlap': 'use-old',
            'single_source': 'enable',
            'src_addr_type': 'subnet',
            'src_end_ip': 'test_value_34',
            'src_end_ip6': 'test_value_35',
            'src_name': 'test_value_36',
            'src_name6': 'test_value_37',
            'src_port': '38',
            'src_start_ip': 'test_value_39',
            'src_start_ip6': 'test_value_40',
            'src_subnet': 'test_value_41',
            'src_subnet6': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_phase2_interface.fortios_vpn_ipsec(input_data, fos_instance)

    expected_data = {
        'add-route': 'phase1',
        'auto-discovery-forwarder': 'phase1',
        'auto-discovery-sender': 'phase1',
        'auto-negotiate': 'enable',
        'comments': 'test_value_7',
        'dhcp-ipsec': 'enable',
        'dhgrp': '1',
        'dst-addr-type': 'subnet',
        'dst-end-ip': 'test_value_11',
        'dst-end-ip6': 'test_value_12',
        'dst-name': 'test_value_13',
        'dst-name6': 'test_value_14',
        'dst-port': '15',
        'dst-start-ip': 'test_value_16',
        'dst-start-ip6': 'test_value_17',
        'dst-subnet': 'test_value_18',
        'dst-subnet6': 'test_value_19',
        'encapsulation': 'tunnel-mode',
        'keepalive': 'enable',
        'keylife-type': 'seconds',
        'keylifekbs': '23',
        'keylifeseconds': '24',
        'l2tp': 'enable',
                'name': 'default_name_26',
                'pfs': 'enable',
                'phase1name': 'test_value_28',
                'protocol': '29',
                'replay': 'enable',
                'route-overlap': 'use-old',
                'single-source': 'enable',
                'src-addr-type': 'subnet',
                'src-end-ip': 'test_value_34',
                'src-end-ip6': 'test_value_35',
                'src-name': 'test_value_36',
                'src-name6': 'test_value_37',
                'src-port': '38',
                'src-start-ip': 'test_value_39',
                'src-start-ip6': 'test_value_40',
                'src-subnet': 'test_value_41',
                'src-subnet6': 'test_value_42'
    }

    set_method_mock.assert_called_with('vpn.ipsec', 'phase2-interface', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_vpn_ipsec_phase2_interface_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ipsec_phase2_interface': {
            'random_attribute_not_valid': 'tag',
            'add_route': 'phase1',
            'auto_discovery_forwarder': 'phase1',
            'auto_discovery_sender': 'phase1',
            'auto_negotiate': 'enable',
            'comments': 'test_value_7',
            'dhcp_ipsec': 'enable',
            'dhgrp': '1',
            'dst_addr_type': 'subnet',
            'dst_end_ip': 'test_value_11',
            'dst_end_ip6': 'test_value_12',
            'dst_name': 'test_value_13',
            'dst_name6': 'test_value_14',
            'dst_port': '15',
            'dst_start_ip': 'test_value_16',
            'dst_start_ip6': 'test_value_17',
            'dst_subnet': 'test_value_18',
            'dst_subnet6': 'test_value_19',
            'encapsulation': 'tunnel-mode',
            'keepalive': 'enable',
            'keylife_type': 'seconds',
            'keylifekbs': '23',
            'keylifeseconds': '24',
            'l2tp': 'enable',
            'name': 'default_name_26',
            'pfs': 'enable',
            'phase1name': 'test_value_28',
            'protocol': '29',
            'replay': 'enable',
            'route_overlap': 'use-old',
            'single_source': 'enable',
            'src_addr_type': 'subnet',
            'src_end_ip': 'test_value_34',
            'src_end_ip6': 'test_value_35',
            'src_name': 'test_value_36',
            'src_name6': 'test_value_37',
            'src_port': '38',
            'src_start_ip': 'test_value_39',
            'src_start_ip6': 'test_value_40',
            'src_subnet': 'test_value_41',
            'src_subnet6': 'test_value_42'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ipsec_phase2_interface.fortios_vpn_ipsec(input_data, fos_instance)

    expected_data = {
        'add-route': 'phase1',
        'auto-discovery-forwarder': 'phase1',
        'auto-discovery-sender': 'phase1',
        'auto-negotiate': 'enable',
        'comments': 'test_value_7',
        'dhcp-ipsec': 'enable',
        'dhgrp': '1',
        'dst-addr-type': 'subnet',
        'dst-end-ip': 'test_value_11',
        'dst-end-ip6': 'test_value_12',
        'dst-name': 'test_value_13',
        'dst-name6': 'test_value_14',
        'dst-port': '15',
        'dst-start-ip': 'test_value_16',
        'dst-start-ip6': 'test_value_17',
        'dst-subnet': 'test_value_18',
        'dst-subnet6': 'test_value_19',
        'encapsulation': 'tunnel-mode',
        'keepalive': 'enable',
        'keylife-type': 'seconds',
        'keylifekbs': '23',
        'keylifeseconds': '24',
        'l2tp': 'enable',
                'name': 'default_name_26',
                'pfs': 'enable',
                'phase1name': 'test_value_28',
                'protocol': '29',
                'replay': 'enable',
                'route-overlap': 'use-old',
                'single-source': 'enable',
                'src-addr-type': 'subnet',
                'src-end-ip': 'test_value_34',
                'src-end-ip6': 'test_value_35',
                'src-name': 'test_value_36',
                'src-name6': 'test_value_37',
                'src-port': '38',
                'src-start-ip': 'test_value_39',
                'src-start-ip6': 'test_value_40',
                'src-subnet': 'test_value_41',
                'src-subnet6': 'test_value_42'
    }

    set_method_mock.assert_called_with('vpn.ipsec', 'phase2-interface', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
