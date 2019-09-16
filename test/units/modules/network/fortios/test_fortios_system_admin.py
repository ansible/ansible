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
    from ansible.modules.network.fortios import fortios_system_admin
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_system_admin.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_system_admin_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_admin': {
            'accprofile': 'test_value_3',
            'accprofile_override': 'enable',
            'allow_remove_admin_session': 'enable',
            'comments': 'test_value_6',
            'email_to': 'test_value_7',
            'force_password_change': 'enable',
            'fortitoken': 'test_value_9',
            'guest_auth': 'disable',
            'guest_lang': 'test_value_11',
            'hidden': '12',
            'history0': 'test_value_13',
            'history1': 'test_value_14',
            'ip6_trusthost1': 'test_value_15',
            'ip6_trusthost10': 'test_value_16',
            'ip6_trusthost2': 'test_value_17',
            'ip6_trusthost3': 'test_value_18',
            'ip6_trusthost4': 'test_value_19',
            'ip6_trusthost5': 'test_value_20',
            'ip6_trusthost6': 'test_value_21',
            'ip6_trusthost7': 'test_value_22',
            'ip6_trusthost8': 'test_value_23',
            'ip6_trusthost9': 'test_value_24',
            'name': 'default_name_25',
            'password': 'test_value_26',
            'password_expire': 'test_value_27',
            'peer_auth': 'enable',
            'peer_group': 'test_value_29',
            'radius_vdom_override': 'enable',
            'remote_auth': 'enable',
            'remote_group': 'test_value_32',
            'schedule': 'test_value_33',
            'sms_custom_server': 'test_value_34',
            'sms_phone': 'test_value_35',
            'sms_server': 'fortiguard',
            'ssh_certificate': 'test_value_37',
            'ssh_public_key1': 'test_value_38',
            'ssh_public_key2': 'test_value_39',
            'ssh_public_key3': 'test_value_40',
            'trusthost1': 'test_value_41',
            'trusthost10': 'test_value_42',
            'trusthost2': 'test_value_43',
            'trusthost3': 'test_value_44',
            'trusthost4': 'test_value_45',
            'trusthost5': 'test_value_46',
            'trusthost6': 'test_value_47',
            'trusthost7': 'test_value_48',
            'trusthost8': 'test_value_49',
            'trusthost9': 'test_value_50',
            'two_factor': 'disable',
            'wildcard': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_admin.fortios_system(input_data, fos_instance)

    expected_data = {
        'accprofile': 'test_value_3',
        'accprofile-override': 'enable',
        'allow-remove-admin-session': 'enable',
        'comments': 'test_value_6',
        'email-to': 'test_value_7',
        'force-password-change': 'enable',
        'fortitoken': 'test_value_9',
        'guest-auth': 'disable',
        'guest-lang': 'test_value_11',
        'hidden': '12',
        'history0': 'test_value_13',
        'history1': 'test_value_14',
        'ip6-trusthost1': 'test_value_15',
        'ip6-trusthost10': 'test_value_16',
        'ip6-trusthost2': 'test_value_17',
        'ip6-trusthost3': 'test_value_18',
        'ip6-trusthost4': 'test_value_19',
        'ip6-trusthost5': 'test_value_20',
        'ip6-trusthost6': 'test_value_21',
        'ip6-trusthost7': 'test_value_22',
        'ip6-trusthost8': 'test_value_23',
        'ip6-trusthost9': 'test_value_24',
        'name': 'default_name_25',
                'password': 'test_value_26',
                'password-expire': 'test_value_27',
                'peer-auth': 'enable',
                'peer-group': 'test_value_29',
                'radius-vdom-override': 'enable',
                'remote-auth': 'enable',
                'remote-group': 'test_value_32',
                'schedule': 'test_value_33',
                'sms-custom-server': 'test_value_34',
                'sms-phone': 'test_value_35',
                'sms-server': 'fortiguard',
                'ssh-certificate': 'test_value_37',
                'ssh-public-key1': 'test_value_38',
                'ssh-public-key2': 'test_value_39',
                'ssh-public-key3': 'test_value_40',
                'trusthost1': 'test_value_41',
                'trusthost10': 'test_value_42',
                'trusthost2': 'test_value_43',
                'trusthost3': 'test_value_44',
                'trusthost4': 'test_value_45',
                'trusthost5': 'test_value_46',
                'trusthost6': 'test_value_47',
                'trusthost7': 'test_value_48',
                'trusthost8': 'test_value_49',
                'trusthost9': 'test_value_50',
                'two-factor': 'disable',
                'wildcard': 'enable'
    }

    set_method_mock.assert_called_with('system', 'admin', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_admin_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_admin': {
            'accprofile': 'test_value_3',
            'accprofile_override': 'enable',
            'allow_remove_admin_session': 'enable',
            'comments': 'test_value_6',
            'email_to': 'test_value_7',
            'force_password_change': 'enable',
            'fortitoken': 'test_value_9',
            'guest_auth': 'disable',
            'guest_lang': 'test_value_11',
            'hidden': '12',
            'history0': 'test_value_13',
            'history1': 'test_value_14',
            'ip6_trusthost1': 'test_value_15',
            'ip6_trusthost10': 'test_value_16',
            'ip6_trusthost2': 'test_value_17',
            'ip6_trusthost3': 'test_value_18',
            'ip6_trusthost4': 'test_value_19',
            'ip6_trusthost5': 'test_value_20',
            'ip6_trusthost6': 'test_value_21',
            'ip6_trusthost7': 'test_value_22',
            'ip6_trusthost8': 'test_value_23',
            'ip6_trusthost9': 'test_value_24',
            'name': 'default_name_25',
            'password': 'test_value_26',
            'password_expire': 'test_value_27',
            'peer_auth': 'enable',
            'peer_group': 'test_value_29',
            'radius_vdom_override': 'enable',
            'remote_auth': 'enable',
            'remote_group': 'test_value_32',
            'schedule': 'test_value_33',
            'sms_custom_server': 'test_value_34',
            'sms_phone': 'test_value_35',
            'sms_server': 'fortiguard',
            'ssh_certificate': 'test_value_37',
            'ssh_public_key1': 'test_value_38',
            'ssh_public_key2': 'test_value_39',
            'ssh_public_key3': 'test_value_40',
            'trusthost1': 'test_value_41',
            'trusthost10': 'test_value_42',
            'trusthost2': 'test_value_43',
            'trusthost3': 'test_value_44',
            'trusthost4': 'test_value_45',
            'trusthost5': 'test_value_46',
            'trusthost6': 'test_value_47',
            'trusthost7': 'test_value_48',
            'trusthost8': 'test_value_49',
            'trusthost9': 'test_value_50',
            'two_factor': 'disable',
            'wildcard': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_admin.fortios_system(input_data, fos_instance)

    expected_data = {
        'accprofile': 'test_value_3',
        'accprofile-override': 'enable',
        'allow-remove-admin-session': 'enable',
        'comments': 'test_value_6',
        'email-to': 'test_value_7',
        'force-password-change': 'enable',
        'fortitoken': 'test_value_9',
        'guest-auth': 'disable',
        'guest-lang': 'test_value_11',
        'hidden': '12',
        'history0': 'test_value_13',
        'history1': 'test_value_14',
        'ip6-trusthost1': 'test_value_15',
        'ip6-trusthost10': 'test_value_16',
        'ip6-trusthost2': 'test_value_17',
        'ip6-trusthost3': 'test_value_18',
        'ip6-trusthost4': 'test_value_19',
        'ip6-trusthost5': 'test_value_20',
        'ip6-trusthost6': 'test_value_21',
        'ip6-trusthost7': 'test_value_22',
        'ip6-trusthost8': 'test_value_23',
        'ip6-trusthost9': 'test_value_24',
        'name': 'default_name_25',
                'password': 'test_value_26',
                'password-expire': 'test_value_27',
                'peer-auth': 'enable',
                'peer-group': 'test_value_29',
                'radius-vdom-override': 'enable',
                'remote-auth': 'enable',
                'remote-group': 'test_value_32',
                'schedule': 'test_value_33',
                'sms-custom-server': 'test_value_34',
                'sms-phone': 'test_value_35',
                'sms-server': 'fortiguard',
                'ssh-certificate': 'test_value_37',
                'ssh-public-key1': 'test_value_38',
                'ssh-public-key2': 'test_value_39',
                'ssh-public-key3': 'test_value_40',
                'trusthost1': 'test_value_41',
                'trusthost10': 'test_value_42',
                'trusthost2': 'test_value_43',
                'trusthost3': 'test_value_44',
                'trusthost4': 'test_value_45',
                'trusthost5': 'test_value_46',
                'trusthost6': 'test_value_47',
                'trusthost7': 'test_value_48',
                'trusthost8': 'test_value_49',
                'trusthost9': 'test_value_50',
                'two-factor': 'disable',
                'wildcard': 'enable'
    }

    set_method_mock.assert_called_with('system', 'admin', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_admin_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'system_admin': {
            'accprofile': 'test_value_3',
            'accprofile_override': 'enable',
            'allow_remove_admin_session': 'enable',
            'comments': 'test_value_6',
            'email_to': 'test_value_7',
            'force_password_change': 'enable',
            'fortitoken': 'test_value_9',
            'guest_auth': 'disable',
            'guest_lang': 'test_value_11',
            'hidden': '12',
            'history0': 'test_value_13',
            'history1': 'test_value_14',
            'ip6_trusthost1': 'test_value_15',
            'ip6_trusthost10': 'test_value_16',
            'ip6_trusthost2': 'test_value_17',
            'ip6_trusthost3': 'test_value_18',
            'ip6_trusthost4': 'test_value_19',
            'ip6_trusthost5': 'test_value_20',
            'ip6_trusthost6': 'test_value_21',
            'ip6_trusthost7': 'test_value_22',
            'ip6_trusthost8': 'test_value_23',
            'ip6_trusthost9': 'test_value_24',
            'name': 'default_name_25',
            'password': 'test_value_26',
            'password_expire': 'test_value_27',
            'peer_auth': 'enable',
            'peer_group': 'test_value_29',
            'radius_vdom_override': 'enable',
            'remote_auth': 'enable',
            'remote_group': 'test_value_32',
            'schedule': 'test_value_33',
            'sms_custom_server': 'test_value_34',
            'sms_phone': 'test_value_35',
            'sms_server': 'fortiguard',
            'ssh_certificate': 'test_value_37',
            'ssh_public_key1': 'test_value_38',
            'ssh_public_key2': 'test_value_39',
            'ssh_public_key3': 'test_value_40',
            'trusthost1': 'test_value_41',
            'trusthost10': 'test_value_42',
            'trusthost2': 'test_value_43',
            'trusthost3': 'test_value_44',
            'trusthost4': 'test_value_45',
            'trusthost5': 'test_value_46',
            'trusthost6': 'test_value_47',
            'trusthost7': 'test_value_48',
            'trusthost8': 'test_value_49',
            'trusthost9': 'test_value_50',
            'two_factor': 'disable',
            'wildcard': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_admin.fortios_system(input_data, fos_instance)

    delete_method_mock.assert_called_with('system', 'admin', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_system_admin_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'system_admin': {
            'accprofile': 'test_value_3',
            'accprofile_override': 'enable',
            'allow_remove_admin_session': 'enable',
            'comments': 'test_value_6',
            'email_to': 'test_value_7',
            'force_password_change': 'enable',
            'fortitoken': 'test_value_9',
            'guest_auth': 'disable',
            'guest_lang': 'test_value_11',
            'hidden': '12',
            'history0': 'test_value_13',
            'history1': 'test_value_14',
            'ip6_trusthost1': 'test_value_15',
            'ip6_trusthost10': 'test_value_16',
            'ip6_trusthost2': 'test_value_17',
            'ip6_trusthost3': 'test_value_18',
            'ip6_trusthost4': 'test_value_19',
            'ip6_trusthost5': 'test_value_20',
            'ip6_trusthost6': 'test_value_21',
            'ip6_trusthost7': 'test_value_22',
            'ip6_trusthost8': 'test_value_23',
            'ip6_trusthost9': 'test_value_24',
            'name': 'default_name_25',
            'password': 'test_value_26',
            'password_expire': 'test_value_27',
            'peer_auth': 'enable',
            'peer_group': 'test_value_29',
            'radius_vdom_override': 'enable',
            'remote_auth': 'enable',
            'remote_group': 'test_value_32',
            'schedule': 'test_value_33',
            'sms_custom_server': 'test_value_34',
            'sms_phone': 'test_value_35',
            'sms_server': 'fortiguard',
            'ssh_certificate': 'test_value_37',
            'ssh_public_key1': 'test_value_38',
            'ssh_public_key2': 'test_value_39',
            'ssh_public_key3': 'test_value_40',
            'trusthost1': 'test_value_41',
            'trusthost10': 'test_value_42',
            'trusthost2': 'test_value_43',
            'trusthost3': 'test_value_44',
            'trusthost4': 'test_value_45',
            'trusthost5': 'test_value_46',
            'trusthost6': 'test_value_47',
            'trusthost7': 'test_value_48',
            'trusthost8': 'test_value_49',
            'trusthost9': 'test_value_50',
            'two_factor': 'disable',
            'wildcard': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_admin.fortios_system(input_data, fos_instance)

    delete_method_mock.assert_called_with('system', 'admin', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_system_admin_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_admin': {
            'accprofile': 'test_value_3',
            'accprofile_override': 'enable',
            'allow_remove_admin_session': 'enable',
            'comments': 'test_value_6',
            'email_to': 'test_value_7',
            'force_password_change': 'enable',
            'fortitoken': 'test_value_9',
            'guest_auth': 'disable',
            'guest_lang': 'test_value_11',
            'hidden': '12',
            'history0': 'test_value_13',
            'history1': 'test_value_14',
            'ip6_trusthost1': 'test_value_15',
            'ip6_trusthost10': 'test_value_16',
            'ip6_trusthost2': 'test_value_17',
            'ip6_trusthost3': 'test_value_18',
            'ip6_trusthost4': 'test_value_19',
            'ip6_trusthost5': 'test_value_20',
            'ip6_trusthost6': 'test_value_21',
            'ip6_trusthost7': 'test_value_22',
            'ip6_trusthost8': 'test_value_23',
            'ip6_trusthost9': 'test_value_24',
            'name': 'default_name_25',
            'password': 'test_value_26',
            'password_expire': 'test_value_27',
            'peer_auth': 'enable',
            'peer_group': 'test_value_29',
            'radius_vdom_override': 'enable',
            'remote_auth': 'enable',
            'remote_group': 'test_value_32',
            'schedule': 'test_value_33',
            'sms_custom_server': 'test_value_34',
            'sms_phone': 'test_value_35',
            'sms_server': 'fortiguard',
            'ssh_certificate': 'test_value_37',
            'ssh_public_key1': 'test_value_38',
            'ssh_public_key2': 'test_value_39',
            'ssh_public_key3': 'test_value_40',
            'trusthost1': 'test_value_41',
            'trusthost10': 'test_value_42',
            'trusthost2': 'test_value_43',
            'trusthost3': 'test_value_44',
            'trusthost4': 'test_value_45',
            'trusthost5': 'test_value_46',
            'trusthost6': 'test_value_47',
            'trusthost7': 'test_value_48',
            'trusthost8': 'test_value_49',
            'trusthost9': 'test_value_50',
            'two_factor': 'disable',
            'wildcard': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_admin.fortios_system(input_data, fos_instance)

    expected_data = {
        'accprofile': 'test_value_3',
        'accprofile-override': 'enable',
        'allow-remove-admin-session': 'enable',
        'comments': 'test_value_6',
        'email-to': 'test_value_7',
        'force-password-change': 'enable',
        'fortitoken': 'test_value_9',
        'guest-auth': 'disable',
        'guest-lang': 'test_value_11',
        'hidden': '12',
        'history0': 'test_value_13',
        'history1': 'test_value_14',
        'ip6-trusthost1': 'test_value_15',
        'ip6-trusthost10': 'test_value_16',
        'ip6-trusthost2': 'test_value_17',
        'ip6-trusthost3': 'test_value_18',
        'ip6-trusthost4': 'test_value_19',
        'ip6-trusthost5': 'test_value_20',
        'ip6-trusthost6': 'test_value_21',
        'ip6-trusthost7': 'test_value_22',
        'ip6-trusthost8': 'test_value_23',
        'ip6-trusthost9': 'test_value_24',
        'name': 'default_name_25',
                'password': 'test_value_26',
                'password-expire': 'test_value_27',
                'peer-auth': 'enable',
                'peer-group': 'test_value_29',
                'radius-vdom-override': 'enable',
                'remote-auth': 'enable',
                'remote-group': 'test_value_32',
                'schedule': 'test_value_33',
                'sms-custom-server': 'test_value_34',
                'sms-phone': 'test_value_35',
                'sms-server': 'fortiguard',
                'ssh-certificate': 'test_value_37',
                'ssh-public-key1': 'test_value_38',
                'ssh-public-key2': 'test_value_39',
                'ssh-public-key3': 'test_value_40',
                'trusthost1': 'test_value_41',
                'trusthost10': 'test_value_42',
                'trusthost2': 'test_value_43',
                'trusthost3': 'test_value_44',
                'trusthost4': 'test_value_45',
                'trusthost5': 'test_value_46',
                'trusthost6': 'test_value_47',
                'trusthost7': 'test_value_48',
                'trusthost8': 'test_value_49',
                'trusthost9': 'test_value_50',
                'two-factor': 'disable',
                'wildcard': 'enable'
    }

    set_method_mock.assert_called_with('system', 'admin', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_system_admin_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'system_admin': {
            'random_attribute_not_valid': 'tag',
            'accprofile': 'test_value_3',
            'accprofile_override': 'enable',
            'allow_remove_admin_session': 'enable',
            'comments': 'test_value_6',
            'email_to': 'test_value_7',
            'force_password_change': 'enable',
            'fortitoken': 'test_value_9',
            'guest_auth': 'disable',
            'guest_lang': 'test_value_11',
            'hidden': '12',
            'history0': 'test_value_13',
            'history1': 'test_value_14',
            'ip6_trusthost1': 'test_value_15',
            'ip6_trusthost10': 'test_value_16',
            'ip6_trusthost2': 'test_value_17',
            'ip6_trusthost3': 'test_value_18',
            'ip6_trusthost4': 'test_value_19',
            'ip6_trusthost5': 'test_value_20',
            'ip6_trusthost6': 'test_value_21',
            'ip6_trusthost7': 'test_value_22',
            'ip6_trusthost8': 'test_value_23',
            'ip6_trusthost9': 'test_value_24',
            'name': 'default_name_25',
            'password': 'test_value_26',
            'password_expire': 'test_value_27',
            'peer_auth': 'enable',
            'peer_group': 'test_value_29',
            'radius_vdom_override': 'enable',
            'remote_auth': 'enable',
            'remote_group': 'test_value_32',
            'schedule': 'test_value_33',
            'sms_custom_server': 'test_value_34',
            'sms_phone': 'test_value_35',
            'sms_server': 'fortiguard',
            'ssh_certificate': 'test_value_37',
            'ssh_public_key1': 'test_value_38',
            'ssh_public_key2': 'test_value_39',
            'ssh_public_key3': 'test_value_40',
            'trusthost1': 'test_value_41',
            'trusthost10': 'test_value_42',
            'trusthost2': 'test_value_43',
            'trusthost3': 'test_value_44',
            'trusthost4': 'test_value_45',
            'trusthost5': 'test_value_46',
            'trusthost6': 'test_value_47',
            'trusthost7': 'test_value_48',
            'trusthost8': 'test_value_49',
            'trusthost9': 'test_value_50',
            'two_factor': 'disable',
            'wildcard': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_admin.fortios_system(input_data, fos_instance)

    expected_data = {
        'accprofile': 'test_value_3',
        'accprofile-override': 'enable',
        'allow-remove-admin-session': 'enable',
        'comments': 'test_value_6',
        'email-to': 'test_value_7',
        'force-password-change': 'enable',
        'fortitoken': 'test_value_9',
        'guest-auth': 'disable',
        'guest-lang': 'test_value_11',
        'hidden': '12',
        'history0': 'test_value_13',
        'history1': 'test_value_14',
        'ip6-trusthost1': 'test_value_15',
        'ip6-trusthost10': 'test_value_16',
        'ip6-trusthost2': 'test_value_17',
        'ip6-trusthost3': 'test_value_18',
        'ip6-trusthost4': 'test_value_19',
        'ip6-trusthost5': 'test_value_20',
        'ip6-trusthost6': 'test_value_21',
        'ip6-trusthost7': 'test_value_22',
        'ip6-trusthost8': 'test_value_23',
        'ip6-trusthost9': 'test_value_24',
        'name': 'default_name_25',
                'password': 'test_value_26',
                'password-expire': 'test_value_27',
                'peer-auth': 'enable',
                'peer-group': 'test_value_29',
                'radius-vdom-override': 'enable',
                'remote-auth': 'enable',
                'remote-group': 'test_value_32',
                'schedule': 'test_value_33',
                'sms-custom-server': 'test_value_34',
                'sms-phone': 'test_value_35',
                'sms-server': 'fortiguard',
                'ssh-certificate': 'test_value_37',
                'ssh-public-key1': 'test_value_38',
                'ssh-public-key2': 'test_value_39',
                'ssh-public-key3': 'test_value_40',
                'trusthost1': 'test_value_41',
                'trusthost10': 'test_value_42',
                'trusthost2': 'test_value_43',
                'trusthost3': 'test_value_44',
                'trusthost4': 'test_value_45',
                'trusthost5': 'test_value_46',
                'trusthost6': 'test_value_47',
                'trusthost7': 'test_value_48',
                'trusthost8': 'test_value_49',
                'trusthost9': 'test_value_50',
                'two-factor': 'disable',
                'wildcard': 'enable'
    }

    set_method_mock.assert_called_with('system', 'admin', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
