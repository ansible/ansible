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
    from ansible.modules.network.fortios import fortios_switch_controller_managed_switch
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_switch_controller_managed_switch.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_switch_controller_managed_switch_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'switch_controller_managed_switch': {'delayed_restart_trigger': '3',
                                             'description': 'test_value_4',
                                             'directly_connected': '5',
                                             'dynamic_capability': '6',
                                             'dynamically_discovered': '7',
                                             'fsw_wan1_admin': 'discovered',
                                             'fsw_wan1_peer': 'test_value_9',
                                             'fsw_wan2_admin': 'discovered',
                                             'fsw_wan2_peer': 'test_value_11',
                                             'max_allowed_trunk_members': '12',
                                             'name': 'default_name_13',
                                             'owner_vdom': 'test_value_14',
                                             'poe_detection_type': '15',
                                             'poe_pre_standard_detection': 'enable',
                                             'pre_provisioned': '17',
                                             'staged_image_version': 'test_value_18',
                                             'switch_device_tag': 'test_value_19',
                                             'switch_id': 'test_value_20',
                                             'switch_profile': 'test_value_21',
                                             'type': 'virtual',
                                             'version': '23'
                                             },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_managed_switch.fortios_switch_controller(input_data, fos_instance)

    expected_data = {'delayed-restart-trigger': '3',
                     'description': 'test_value_4',
                     'directly-connected': '5',
                     'dynamic-capability': '6',
                     'dynamically-discovered': '7',
                     'fsw-wan1-admin': 'discovered',
                     'fsw-wan1-peer': 'test_value_9',
                     'fsw-wan2-admin': 'discovered',
                     'fsw-wan2-peer': 'test_value_11',
                     'max-allowed-trunk-members': '12',
                     'name': 'default_name_13',
                     'owner-vdom': 'test_value_14',
                     'poe-detection-type': '15',
                     'poe-pre-standard-detection': 'enable',
                     'pre-provisioned': '17',
                     'staged-image-version': 'test_value_18',
                     'switch-device-tag': 'test_value_19',
                     'switch-id': 'test_value_20',
                     'switch-profile': 'test_value_21',
                     'type': 'virtual',
                     'version': '23'
                     }

    set_method_mock.assert_called_with('switch-controller', 'managed-switch', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_switch_controller_managed_switch_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'switch_controller_managed_switch': {'delayed_restart_trigger': '3',
                                             'description': 'test_value_4',
                                             'directly_connected': '5',
                                             'dynamic_capability': '6',
                                             'dynamically_discovered': '7',
                                             'fsw_wan1_admin': 'discovered',
                                             'fsw_wan1_peer': 'test_value_9',
                                             'fsw_wan2_admin': 'discovered',
                                             'fsw_wan2_peer': 'test_value_11',
                                             'max_allowed_trunk_members': '12',
                                             'name': 'default_name_13',
                                             'owner_vdom': 'test_value_14',
                                             'poe_detection_type': '15',
                                             'poe_pre_standard_detection': 'enable',
                                             'pre_provisioned': '17',
                                             'staged_image_version': 'test_value_18',
                                             'switch_device_tag': 'test_value_19',
                                             'switch_id': 'test_value_20',
                                             'switch_profile': 'test_value_21',
                                             'type': 'virtual',
                                             'version': '23'
                                             },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_managed_switch.fortios_switch_controller(input_data, fos_instance)

    expected_data = {'delayed-restart-trigger': '3',
                     'description': 'test_value_4',
                     'directly-connected': '5',
                     'dynamic-capability': '6',
                     'dynamically-discovered': '7',
                     'fsw-wan1-admin': 'discovered',
                     'fsw-wan1-peer': 'test_value_9',
                     'fsw-wan2-admin': 'discovered',
                     'fsw-wan2-peer': 'test_value_11',
                     'max-allowed-trunk-members': '12',
                     'name': 'default_name_13',
                     'owner-vdom': 'test_value_14',
                     'poe-detection-type': '15',
                     'poe-pre-standard-detection': 'enable',
                     'pre-provisioned': '17',
                     'staged-image-version': 'test_value_18',
                     'switch-device-tag': 'test_value_19',
                     'switch-id': 'test_value_20',
                     'switch-profile': 'test_value_21',
                     'type': 'virtual',
                     'version': '23'
                     }

    set_method_mock.assert_called_with('switch-controller', 'managed-switch', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_switch_controller_managed_switch_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'switch_controller_managed_switch': {'delayed_restart_trigger': '3',
                                             'description': 'test_value_4',
                                             'directly_connected': '5',
                                             'dynamic_capability': '6',
                                             'dynamically_discovered': '7',
                                             'fsw_wan1_admin': 'discovered',
                                             'fsw_wan1_peer': 'test_value_9',
                                             'fsw_wan2_admin': 'discovered',
                                             'fsw_wan2_peer': 'test_value_11',
                                             'max_allowed_trunk_members': '12',
                                             'name': 'default_name_13',
                                             'owner_vdom': 'test_value_14',
                                             'poe_detection_type': '15',
                                             'poe_pre_standard_detection': 'enable',
                                             'pre_provisioned': '17',
                                             'staged_image_version': 'test_value_18',
                                             'switch_device_tag': 'test_value_19',
                                             'switch_id': 'test_value_20',
                                             'switch_profile': 'test_value_21',
                                             'type': 'virtual',
                                             'version': '23'
                                             },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_managed_switch.fortios_switch_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('switch-controller', 'managed-switch', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_switch_controller_managed_switch_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'switch_controller_managed_switch': {'delayed_restart_trigger': '3',
                                             'description': 'test_value_4',
                                             'directly_connected': '5',
                                             'dynamic_capability': '6',
                                             'dynamically_discovered': '7',
                                             'fsw_wan1_admin': 'discovered',
                                             'fsw_wan1_peer': 'test_value_9',
                                             'fsw_wan2_admin': 'discovered',
                                             'fsw_wan2_peer': 'test_value_11',
                                             'max_allowed_trunk_members': '12',
                                             'name': 'default_name_13',
                                             'owner_vdom': 'test_value_14',
                                             'poe_detection_type': '15',
                                             'poe_pre_standard_detection': 'enable',
                                             'pre_provisioned': '17',
                                             'staged_image_version': 'test_value_18',
                                             'switch_device_tag': 'test_value_19',
                                             'switch_id': 'test_value_20',
                                             'switch_profile': 'test_value_21',
                                             'type': 'virtual',
                                             'version': '23'
                                             },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_managed_switch.fortios_switch_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('switch-controller', 'managed-switch', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_switch_controller_managed_switch_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'switch_controller_managed_switch': {'delayed_restart_trigger': '3',
                                             'description': 'test_value_4',
                                             'directly_connected': '5',
                                             'dynamic_capability': '6',
                                             'dynamically_discovered': '7',
                                             'fsw_wan1_admin': 'discovered',
                                             'fsw_wan1_peer': 'test_value_9',
                                             'fsw_wan2_admin': 'discovered',
                                             'fsw_wan2_peer': 'test_value_11',
                                             'max_allowed_trunk_members': '12',
                                             'name': 'default_name_13',
                                             'owner_vdom': 'test_value_14',
                                             'poe_detection_type': '15',
                                             'poe_pre_standard_detection': 'enable',
                                             'pre_provisioned': '17',
                                             'staged_image_version': 'test_value_18',
                                             'switch_device_tag': 'test_value_19',
                                             'switch_id': 'test_value_20',
                                             'switch_profile': 'test_value_21',
                                             'type': 'virtual',
                                             'version': '23'
                                             },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_managed_switch.fortios_switch_controller(input_data, fos_instance)

    expected_data = {'delayed-restart-trigger': '3',
                     'description': 'test_value_4',
                     'directly-connected': '5',
                     'dynamic-capability': '6',
                     'dynamically-discovered': '7',
                     'fsw-wan1-admin': 'discovered',
                     'fsw-wan1-peer': 'test_value_9',
                     'fsw-wan2-admin': 'discovered',
                     'fsw-wan2-peer': 'test_value_11',
                     'max-allowed-trunk-members': '12',
                     'name': 'default_name_13',
                     'owner-vdom': 'test_value_14',
                     'poe-detection-type': '15',
                     'poe-pre-standard-detection': 'enable',
                     'pre-provisioned': '17',
                     'staged-image-version': 'test_value_18',
                     'switch-device-tag': 'test_value_19',
                     'switch-id': 'test_value_20',
                     'switch-profile': 'test_value_21',
                     'type': 'virtual',
                     'version': '23'
                     }

    set_method_mock.assert_called_with('switch-controller', 'managed-switch', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_switch_controller_managed_switch_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'switch_controller_managed_switch': {
            'random_attribute_not_valid': 'tag', 'delayed_restart_trigger': '3',
            'description': 'test_value_4',
            'directly_connected': '5',
            'dynamic_capability': '6',
            'dynamically_discovered': '7',
            'fsw_wan1_admin': 'discovered',
            'fsw_wan1_peer': 'test_value_9',
            'fsw_wan2_admin': 'discovered',
            'fsw_wan2_peer': 'test_value_11',
            'max_allowed_trunk_members': '12',
            'name': 'default_name_13',
            'owner_vdom': 'test_value_14',
            'poe_detection_type': '15',
            'poe_pre_standard_detection': 'enable',
            'pre_provisioned': '17',
            'staged_image_version': 'test_value_18',
            'switch_device_tag': 'test_value_19',
            'switch_id': 'test_value_20',
            'switch_profile': 'test_value_21',
            'type': 'virtual',
            'version': '23'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_switch_controller_managed_switch.fortios_switch_controller(input_data, fos_instance)

    expected_data = {'delayed-restart-trigger': '3',
                     'description': 'test_value_4',
                     'directly-connected': '5',
                     'dynamic-capability': '6',
                     'dynamically-discovered': '7',
                     'fsw-wan1-admin': 'discovered',
                     'fsw-wan1-peer': 'test_value_9',
                     'fsw-wan2-admin': 'discovered',
                     'fsw-wan2-peer': 'test_value_11',
                     'max-allowed-trunk-members': '12',
                     'name': 'default_name_13',
                     'owner-vdom': 'test_value_14',
                     'poe-detection-type': '15',
                     'poe-pre-standard-detection': 'enable',
                     'pre-provisioned': '17',
                     'staged-image-version': 'test_value_18',
                     'switch-device-tag': 'test_value_19',
                     'switch-id': 'test_value_20',
                     'switch-profile': 'test_value_21',
                     'type': 'virtual',
                     'version': '23'
                     }

    set_method_mock.assert_called_with('switch-controller', 'managed-switch', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
