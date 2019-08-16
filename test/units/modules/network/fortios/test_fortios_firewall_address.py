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
    from ansible.modules.network.fortios import fortios_firewall_address
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_firewall_address.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_firewall_address_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_address': {
            'allow_routing': 'enable',
            'associated_interface': 'test_value_4',
            'cache_ttl': '5',
            'color': '6',
            'comment': 'Comment.',
            'country': 'test_value_8',
            'end_ip': 'test_value_9',
            'epg_name': 'test_value_10',
            'filter': 'test_value_11',
            'fqdn': 'test_value_12',
            'name': 'default_name_13',
            'obj_id': 'test_value_14',
            'organization': 'test_value_15',
            'policy_group': 'test_value_16',
            'sdn': 'aci',
            'sdn_tag': 'test_value_18',
            'start_ip': 'test_value_19',
            'subnet': 'test_value_20',
            'subnet_name': 'test_value_21',
            'tenant': 'test_value_22',
            'type': 'ipmask',
            'uuid': 'test_value_24',
            'visibility': 'enable',
            'wildcard': 'test_value_26',
            'wildcard_fqdn': 'test_value_27'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_address.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'allow-routing': 'enable',
        'associated-interface': 'test_value_4',
        'cache-ttl': '5',
        'color': '6',
        'comment': 'Comment.',
        'country': 'test_value_8',
        'end-ip': 'test_value_9',
        'epg-name': 'test_value_10',
        'filter': 'test_value_11',
        'fqdn': 'test_value_12',
                'name': 'default_name_13',
                'obj-id': 'test_value_14',
                'organization': 'test_value_15',
                'policy-group': 'test_value_16',
                'sdn': 'aci',
                'sdn-tag': 'test_value_18',
                'start-ip': 'test_value_19',
                'subnet': 'test_value_20',
                'subnet-name': 'test_value_21',
                'tenant': 'test_value_22',
                'type': 'ipmask',
                'uuid': 'test_value_24',
                'visibility': 'enable',
                'wildcard': 'test_value_26',
                'wildcard-fqdn': 'test_value_27'
    }

    set_method_mock.assert_called_with('firewall', 'address', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_address_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_address': {
            'allow_routing': 'enable',
            'associated_interface': 'test_value_4',
            'cache_ttl': '5',
            'color': '6',
            'comment': 'Comment.',
            'country': 'test_value_8',
            'end_ip': 'test_value_9',
            'epg_name': 'test_value_10',
            'filter': 'test_value_11',
            'fqdn': 'test_value_12',
            'name': 'default_name_13',
            'obj_id': 'test_value_14',
            'organization': 'test_value_15',
            'policy_group': 'test_value_16',
            'sdn': 'aci',
            'sdn_tag': 'test_value_18',
            'start_ip': 'test_value_19',
            'subnet': 'test_value_20',
            'subnet_name': 'test_value_21',
            'tenant': 'test_value_22',
            'type': 'ipmask',
            'uuid': 'test_value_24',
            'visibility': 'enable',
            'wildcard': 'test_value_26',
            'wildcard_fqdn': 'test_value_27'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_address.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'allow-routing': 'enable',
        'associated-interface': 'test_value_4',
        'cache-ttl': '5',
        'color': '6',
        'comment': 'Comment.',
        'country': 'test_value_8',
        'end-ip': 'test_value_9',
        'epg-name': 'test_value_10',
        'filter': 'test_value_11',
        'fqdn': 'test_value_12',
                'name': 'default_name_13',
                'obj-id': 'test_value_14',
                'organization': 'test_value_15',
                'policy-group': 'test_value_16',
                'sdn': 'aci',
                'sdn-tag': 'test_value_18',
                'start-ip': 'test_value_19',
                'subnet': 'test_value_20',
                'subnet-name': 'test_value_21',
                'tenant': 'test_value_22',
                'type': 'ipmask',
                'uuid': 'test_value_24',
                'visibility': 'enable',
                'wildcard': 'test_value_26',
                'wildcard-fqdn': 'test_value_27'
    }

    set_method_mock.assert_called_with('firewall', 'address', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_address_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_address': {
            'allow_routing': 'enable',
            'associated_interface': 'test_value_4',
            'cache_ttl': '5',
            'color': '6',
            'comment': 'Comment.',
            'country': 'test_value_8',
            'end_ip': 'test_value_9',
            'epg_name': 'test_value_10',
            'filter': 'test_value_11',
            'fqdn': 'test_value_12',
            'name': 'default_name_13',
            'obj_id': 'test_value_14',
            'organization': 'test_value_15',
            'policy_group': 'test_value_16',
            'sdn': 'aci',
            'sdn_tag': 'test_value_18',
            'start_ip': 'test_value_19',
            'subnet': 'test_value_20',
            'subnet_name': 'test_value_21',
            'tenant': 'test_value_22',
            'type': 'ipmask',
            'uuid': 'test_value_24',
            'visibility': 'enable',
            'wildcard': 'test_value_26',
            'wildcard_fqdn': 'test_value_27'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_address.fortios_firewall(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall', 'address', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_firewall_address_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'firewall_address': {
            'allow_routing': 'enable',
            'associated_interface': 'test_value_4',
            'cache_ttl': '5',
            'color': '6',
            'comment': 'Comment.',
            'country': 'test_value_8',
            'end_ip': 'test_value_9',
            'epg_name': 'test_value_10',
            'filter': 'test_value_11',
            'fqdn': 'test_value_12',
            'name': 'default_name_13',
            'obj_id': 'test_value_14',
            'organization': 'test_value_15',
            'policy_group': 'test_value_16',
            'sdn': 'aci',
            'sdn_tag': 'test_value_18',
            'start_ip': 'test_value_19',
            'subnet': 'test_value_20',
            'subnet_name': 'test_value_21',
            'tenant': 'test_value_22',
            'type': 'ipmask',
            'uuid': 'test_value_24',
            'visibility': 'enable',
            'wildcard': 'test_value_26',
            'wildcard_fqdn': 'test_value_27'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_address.fortios_firewall(input_data, fos_instance)

    delete_method_mock.assert_called_with('firewall', 'address', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_firewall_address_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_address': {
            'allow_routing': 'enable',
            'associated_interface': 'test_value_4',
            'cache_ttl': '5',
            'color': '6',
            'comment': 'Comment.',
            'country': 'test_value_8',
            'end_ip': 'test_value_9',
            'epg_name': 'test_value_10',
            'filter': 'test_value_11',
            'fqdn': 'test_value_12',
            'name': 'default_name_13',
            'obj_id': 'test_value_14',
            'organization': 'test_value_15',
            'policy_group': 'test_value_16',
            'sdn': 'aci',
            'sdn_tag': 'test_value_18',
            'start_ip': 'test_value_19',
            'subnet': 'test_value_20',
            'subnet_name': 'test_value_21',
            'tenant': 'test_value_22',
            'type': 'ipmask',
            'uuid': 'test_value_24',
            'visibility': 'enable',
            'wildcard': 'test_value_26',
            'wildcard_fqdn': 'test_value_27'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_address.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'allow-routing': 'enable',
        'associated-interface': 'test_value_4',
        'cache-ttl': '5',
        'color': '6',
        'comment': 'Comment.',
        'country': 'test_value_8',
        'end-ip': 'test_value_9',
        'epg-name': 'test_value_10',
        'filter': 'test_value_11',
        'fqdn': 'test_value_12',
                'name': 'default_name_13',
                'obj-id': 'test_value_14',
                'organization': 'test_value_15',
                'policy-group': 'test_value_16',
                'sdn': 'aci',
                'sdn-tag': 'test_value_18',
                'start-ip': 'test_value_19',
                'subnet': 'test_value_20',
                'subnet-name': 'test_value_21',
                'tenant': 'test_value_22',
                'type': 'ipmask',
                'uuid': 'test_value_24',
                'visibility': 'enable',
                'wildcard': 'test_value_26',
                'wildcard-fqdn': 'test_value_27'
    }

    set_method_mock.assert_called_with('firewall', 'address', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_firewall_address_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'firewall_address': {
            'random_attribute_not_valid': 'tag',
            'allow_routing': 'enable',
            'associated_interface': 'test_value_4',
            'cache_ttl': '5',
            'color': '6',
            'comment': 'Comment.',
            'country': 'test_value_8',
            'end_ip': 'test_value_9',
            'epg_name': 'test_value_10',
            'filter': 'test_value_11',
            'fqdn': 'test_value_12',
            'name': 'default_name_13',
            'obj_id': 'test_value_14',
            'organization': 'test_value_15',
            'policy_group': 'test_value_16',
            'sdn': 'aci',
            'sdn_tag': 'test_value_18',
            'start_ip': 'test_value_19',
            'subnet': 'test_value_20',
            'subnet_name': 'test_value_21',
            'tenant': 'test_value_22',
            'type': 'ipmask',
            'uuid': 'test_value_24',
            'visibility': 'enable',
            'wildcard': 'test_value_26',
            'wildcard_fqdn': 'test_value_27'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_firewall_address.fortios_firewall(input_data, fos_instance)

    expected_data = {
        'allow-routing': 'enable',
        'associated-interface': 'test_value_4',
        'cache-ttl': '5',
        'color': '6',
        'comment': 'Comment.',
        'country': 'test_value_8',
        'end-ip': 'test_value_9',
        'epg-name': 'test_value_10',
        'filter': 'test_value_11',
        'fqdn': 'test_value_12',
                'name': 'default_name_13',
                'obj-id': 'test_value_14',
                'organization': 'test_value_15',
                'policy-group': 'test_value_16',
                'sdn': 'aci',
                'sdn-tag': 'test_value_18',
                'start-ip': 'test_value_19',
                'subnet': 'test_value_20',
                'subnet-name': 'test_value_21',
                'tenant': 'test_value_22',
                'type': 'ipmask',
                'uuid': 'test_value_24',
                'visibility': 'enable',
                'wildcard': 'test_value_26',
                'wildcard-fqdn': 'test_value_27'
    }

    set_method_mock.assert_called_with('firewall', 'address', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
