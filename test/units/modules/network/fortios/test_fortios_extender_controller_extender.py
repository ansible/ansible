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
    from ansible.modules.network.fortios import fortios_extender_controller_extender
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_extender_controller_extender.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_extender_controller_extender_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'extender_controller_extender': {
            'aaa_shared_secret': 'test_value_3',
            'access_point_name': 'test_value_4',
            'admin': 'disable',
            'at_dial_script': 'test_value_6',
            'billing_start_day': '7',
            'cdma_aaa_spi': 'test_value_8',
            'cdma_ha_spi': 'test_value_9',
            'cdma_nai': 'test_value_10',
            'conn_status': '11',
            'description': 'test_value_12',
            'dial_mode': 'dial-on-demand',
            'dial_status': '14',
            'ext_name': 'test_value_15',
            'ha_shared_secret': 'test_value_16',
            'id': '17',
            'ifname': 'test_value_18',
            'initiated_update': 'enable',
            'mode': 'standalone',
            'modem_passwd': 'test_value_21',
            'modem_type': 'cdma',
            'multi_mode': 'auto',
            'ppp_auth_protocol': 'auto',
            'ppp_echo_request': 'enable',
            'ppp_password': 'test_value_26',
            'ppp_username': 'test_value_27',
            'primary_ha': 'test_value_28',
            'quota_limit_mb': '29',
            'redial': 'none',
            'redundant_intf': 'test_value_31',
            'roaming': 'enable',
            'role': 'none',
            'secondary_ha': 'test_value_34',
            'sim_pin': 'test_value_35',
            'vdom': '36',
            'wimax_auth_protocol': 'tls',
            'wimax_carrier': 'test_value_38',
            'wimax_realm': 'test_value_39'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_extender_controller_extender.fortios_extender_controller(input_data, fos_instance)

    expected_data = {
        'aaa-shared-secret': 'test_value_3',
        'access-point-name': 'test_value_4',
        'admin': 'disable',
        'at-dial-script': 'test_value_6',
        'billing-start-day': '7',
        'cdma-aaa-spi': 'test_value_8',
        'cdma-ha-spi': 'test_value_9',
        'cdma-nai': 'test_value_10',
        'conn-status': '11',
        'description': 'test_value_12',
        'dial-mode': 'dial-on-demand',
        'dial-status': '14',
        'ext-name': 'test_value_15',
        'ha-shared-secret': 'test_value_16',
        'id': '17',
        'ifname': 'test_value_18',
        'initiated-update': 'enable',
        'mode': 'standalone',
                'modem-passwd': 'test_value_21',
                'modem-type': 'cdma',
                'multi-mode': 'auto',
                'ppp-auth-protocol': 'auto',
                'ppp-echo-request': 'enable',
                'ppp-password': 'test_value_26',
                'ppp-username': 'test_value_27',
                'primary-ha': 'test_value_28',
                'quota-limit-mb': '29',
                'redial': 'none',
                'redundant-intf': 'test_value_31',
                'roaming': 'enable',
                'role': 'none',
                'secondary-ha': 'test_value_34',
                'sim-pin': 'test_value_35',
                'vdom': '36',
                'wimax-auth-protocol': 'tls',
                'wimax-carrier': 'test_value_38',
                'wimax-realm': 'test_value_39'
    }

    set_method_mock.assert_called_with('extender-controller', 'extender', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_extender_controller_extender_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'extender_controller_extender': {
            'aaa_shared_secret': 'test_value_3',
            'access_point_name': 'test_value_4',
            'admin': 'disable',
            'at_dial_script': 'test_value_6',
            'billing_start_day': '7',
            'cdma_aaa_spi': 'test_value_8',
            'cdma_ha_spi': 'test_value_9',
            'cdma_nai': 'test_value_10',
            'conn_status': '11',
            'description': 'test_value_12',
            'dial_mode': 'dial-on-demand',
            'dial_status': '14',
            'ext_name': 'test_value_15',
            'ha_shared_secret': 'test_value_16',
            'id': '17',
            'ifname': 'test_value_18',
            'initiated_update': 'enable',
            'mode': 'standalone',
            'modem_passwd': 'test_value_21',
            'modem_type': 'cdma',
            'multi_mode': 'auto',
            'ppp_auth_protocol': 'auto',
            'ppp_echo_request': 'enable',
            'ppp_password': 'test_value_26',
            'ppp_username': 'test_value_27',
            'primary_ha': 'test_value_28',
            'quota_limit_mb': '29',
            'redial': 'none',
            'redundant_intf': 'test_value_31',
            'roaming': 'enable',
            'role': 'none',
            'secondary_ha': 'test_value_34',
            'sim_pin': 'test_value_35',
            'vdom': '36',
            'wimax_auth_protocol': 'tls',
            'wimax_carrier': 'test_value_38',
            'wimax_realm': 'test_value_39'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_extender_controller_extender.fortios_extender_controller(input_data, fos_instance)

    expected_data = {
        'aaa-shared-secret': 'test_value_3',
        'access-point-name': 'test_value_4',
        'admin': 'disable',
        'at-dial-script': 'test_value_6',
        'billing-start-day': '7',
        'cdma-aaa-spi': 'test_value_8',
        'cdma-ha-spi': 'test_value_9',
        'cdma-nai': 'test_value_10',
        'conn-status': '11',
        'description': 'test_value_12',
        'dial-mode': 'dial-on-demand',
        'dial-status': '14',
        'ext-name': 'test_value_15',
        'ha-shared-secret': 'test_value_16',
        'id': '17',
        'ifname': 'test_value_18',
        'initiated-update': 'enable',
        'mode': 'standalone',
                'modem-passwd': 'test_value_21',
                'modem-type': 'cdma',
                'multi-mode': 'auto',
                'ppp-auth-protocol': 'auto',
                'ppp-echo-request': 'enable',
                'ppp-password': 'test_value_26',
                'ppp-username': 'test_value_27',
                'primary-ha': 'test_value_28',
                'quota-limit-mb': '29',
                'redial': 'none',
                'redundant-intf': 'test_value_31',
                'roaming': 'enable',
                'role': 'none',
                'secondary-ha': 'test_value_34',
                'sim-pin': 'test_value_35',
                'vdom': '36',
                'wimax-auth-protocol': 'tls',
                'wimax-carrier': 'test_value_38',
                'wimax-realm': 'test_value_39'
    }

    set_method_mock.assert_called_with('extender-controller', 'extender', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_extender_controller_extender_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'extender_controller_extender': {
            'aaa_shared_secret': 'test_value_3',
            'access_point_name': 'test_value_4',
            'admin': 'disable',
            'at_dial_script': 'test_value_6',
            'billing_start_day': '7',
            'cdma_aaa_spi': 'test_value_8',
            'cdma_ha_spi': 'test_value_9',
            'cdma_nai': 'test_value_10',
            'conn_status': '11',
            'description': 'test_value_12',
            'dial_mode': 'dial-on-demand',
            'dial_status': '14',
            'ext_name': 'test_value_15',
            'ha_shared_secret': 'test_value_16',
            'id': '17',
            'ifname': 'test_value_18',
            'initiated_update': 'enable',
            'mode': 'standalone',
            'modem_passwd': 'test_value_21',
            'modem_type': 'cdma',
            'multi_mode': 'auto',
            'ppp_auth_protocol': 'auto',
            'ppp_echo_request': 'enable',
            'ppp_password': 'test_value_26',
            'ppp_username': 'test_value_27',
            'primary_ha': 'test_value_28',
            'quota_limit_mb': '29',
            'redial': 'none',
            'redundant_intf': 'test_value_31',
            'roaming': 'enable',
            'role': 'none',
            'secondary_ha': 'test_value_34',
            'sim_pin': 'test_value_35',
            'vdom': '36',
            'wimax_auth_protocol': 'tls',
            'wimax_carrier': 'test_value_38',
            'wimax_realm': 'test_value_39'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_extender_controller_extender.fortios_extender_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('extender-controller', 'extender', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_extender_controller_extender_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'extender_controller_extender': {
            'aaa_shared_secret': 'test_value_3',
            'access_point_name': 'test_value_4',
            'admin': 'disable',
            'at_dial_script': 'test_value_6',
            'billing_start_day': '7',
            'cdma_aaa_spi': 'test_value_8',
            'cdma_ha_spi': 'test_value_9',
            'cdma_nai': 'test_value_10',
            'conn_status': '11',
            'description': 'test_value_12',
            'dial_mode': 'dial-on-demand',
            'dial_status': '14',
            'ext_name': 'test_value_15',
            'ha_shared_secret': 'test_value_16',
            'id': '17',
            'ifname': 'test_value_18',
            'initiated_update': 'enable',
            'mode': 'standalone',
            'modem_passwd': 'test_value_21',
            'modem_type': 'cdma',
            'multi_mode': 'auto',
            'ppp_auth_protocol': 'auto',
            'ppp_echo_request': 'enable',
            'ppp_password': 'test_value_26',
            'ppp_username': 'test_value_27',
            'primary_ha': 'test_value_28',
            'quota_limit_mb': '29',
            'redial': 'none',
            'redundant_intf': 'test_value_31',
            'roaming': 'enable',
            'role': 'none',
            'secondary_ha': 'test_value_34',
            'sim_pin': 'test_value_35',
            'vdom': '36',
            'wimax_auth_protocol': 'tls',
            'wimax_carrier': 'test_value_38',
            'wimax_realm': 'test_value_39'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_extender_controller_extender.fortios_extender_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('extender-controller', 'extender', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_extender_controller_extender_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'extender_controller_extender': {
            'aaa_shared_secret': 'test_value_3',
            'access_point_name': 'test_value_4',
            'admin': 'disable',
            'at_dial_script': 'test_value_6',
            'billing_start_day': '7',
            'cdma_aaa_spi': 'test_value_8',
            'cdma_ha_spi': 'test_value_9',
            'cdma_nai': 'test_value_10',
            'conn_status': '11',
            'description': 'test_value_12',
            'dial_mode': 'dial-on-demand',
            'dial_status': '14',
            'ext_name': 'test_value_15',
            'ha_shared_secret': 'test_value_16',
            'id': '17',
            'ifname': 'test_value_18',
            'initiated_update': 'enable',
            'mode': 'standalone',
            'modem_passwd': 'test_value_21',
            'modem_type': 'cdma',
            'multi_mode': 'auto',
            'ppp_auth_protocol': 'auto',
            'ppp_echo_request': 'enable',
            'ppp_password': 'test_value_26',
            'ppp_username': 'test_value_27',
            'primary_ha': 'test_value_28',
            'quota_limit_mb': '29',
            'redial': 'none',
            'redundant_intf': 'test_value_31',
            'roaming': 'enable',
            'role': 'none',
            'secondary_ha': 'test_value_34',
            'sim_pin': 'test_value_35',
            'vdom': '36',
            'wimax_auth_protocol': 'tls',
            'wimax_carrier': 'test_value_38',
            'wimax_realm': 'test_value_39'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_extender_controller_extender.fortios_extender_controller(input_data, fos_instance)

    expected_data = {
        'aaa-shared-secret': 'test_value_3',
        'access-point-name': 'test_value_4',
        'admin': 'disable',
        'at-dial-script': 'test_value_6',
        'billing-start-day': '7',
        'cdma-aaa-spi': 'test_value_8',
        'cdma-ha-spi': 'test_value_9',
        'cdma-nai': 'test_value_10',
        'conn-status': '11',
        'description': 'test_value_12',
        'dial-mode': 'dial-on-demand',
        'dial-status': '14',
        'ext-name': 'test_value_15',
        'ha-shared-secret': 'test_value_16',
        'id': '17',
        'ifname': 'test_value_18',
        'initiated-update': 'enable',
        'mode': 'standalone',
                'modem-passwd': 'test_value_21',
                'modem-type': 'cdma',
                'multi-mode': 'auto',
                'ppp-auth-protocol': 'auto',
                'ppp-echo-request': 'enable',
                'ppp-password': 'test_value_26',
                'ppp-username': 'test_value_27',
                'primary-ha': 'test_value_28',
                'quota-limit-mb': '29',
                'redial': 'none',
                'redundant-intf': 'test_value_31',
                'roaming': 'enable',
                'role': 'none',
                'secondary-ha': 'test_value_34',
                'sim-pin': 'test_value_35',
                'vdom': '36',
                'wimax-auth-protocol': 'tls',
                'wimax-carrier': 'test_value_38',
                'wimax-realm': 'test_value_39'
    }

    set_method_mock.assert_called_with('extender-controller', 'extender', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_extender_controller_extender_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'extender_controller_extender': {
            'random_attribute_not_valid': 'tag',
            'aaa_shared_secret': 'test_value_3',
            'access_point_name': 'test_value_4',
            'admin': 'disable',
            'at_dial_script': 'test_value_6',
            'billing_start_day': '7',
            'cdma_aaa_spi': 'test_value_8',
            'cdma_ha_spi': 'test_value_9',
            'cdma_nai': 'test_value_10',
            'conn_status': '11',
            'description': 'test_value_12',
            'dial_mode': 'dial-on-demand',
            'dial_status': '14',
            'ext_name': 'test_value_15',
            'ha_shared_secret': 'test_value_16',
            'id': '17',
            'ifname': 'test_value_18',
            'initiated_update': 'enable',
            'mode': 'standalone',
            'modem_passwd': 'test_value_21',
            'modem_type': 'cdma',
            'multi_mode': 'auto',
            'ppp_auth_protocol': 'auto',
            'ppp_echo_request': 'enable',
            'ppp_password': 'test_value_26',
            'ppp_username': 'test_value_27',
            'primary_ha': 'test_value_28',
            'quota_limit_mb': '29',
            'redial': 'none',
            'redundant_intf': 'test_value_31',
            'roaming': 'enable',
            'role': 'none',
            'secondary_ha': 'test_value_34',
            'sim_pin': 'test_value_35',
            'vdom': '36',
            'wimax_auth_protocol': 'tls',
            'wimax_carrier': 'test_value_38',
            'wimax_realm': 'test_value_39'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_extender_controller_extender.fortios_extender_controller(input_data, fos_instance)

    expected_data = {
        'aaa-shared-secret': 'test_value_3',
        'access-point-name': 'test_value_4',
        'admin': 'disable',
        'at-dial-script': 'test_value_6',
        'billing-start-day': '7',
        'cdma-aaa-spi': 'test_value_8',
        'cdma-ha-spi': 'test_value_9',
        'cdma-nai': 'test_value_10',
        'conn-status': '11',
        'description': 'test_value_12',
        'dial-mode': 'dial-on-demand',
        'dial-status': '14',
        'ext-name': 'test_value_15',
        'ha-shared-secret': 'test_value_16',
        'id': '17',
        'ifname': 'test_value_18',
        'initiated-update': 'enable',
        'mode': 'standalone',
                'modem-passwd': 'test_value_21',
                'modem-type': 'cdma',
                'multi-mode': 'auto',
                'ppp-auth-protocol': 'auto',
                'ppp-echo-request': 'enable',
                'ppp-password': 'test_value_26',
                'ppp-username': 'test_value_27',
                'primary-ha': 'test_value_28',
                'quota-limit-mb': '29',
                'redial': 'none',
                'redundant-intf': 'test_value_31',
                'roaming': 'enable',
                'role': 'none',
                'secondary-ha': 'test_value_34',
                'sim-pin': 'test_value_35',
                'vdom': '36',
                'wimax-auth-protocol': 'tls',
                'wimax-carrier': 'test_value_38',
                'wimax-realm': 'test_value_39'
    }

    set_method_mock.assert_called_with('extender-controller', 'extender', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
