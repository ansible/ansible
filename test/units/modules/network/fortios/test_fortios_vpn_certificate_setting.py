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
    from ansible.modules.network.fortios import fortios_vpn_certificate_setting
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_vpn_certificate_setting.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_vpn_certificate_setting_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_certificate_setting': {
            'certname_dsa1024': 'test_value_3',
            'certname_dsa2048': 'test_value_4',
            'certname_ecdsa256': 'test_value_5',
            'certname_ecdsa384': 'test_value_6',
            'certname_rsa1024': 'test_value_7',
            'certname_rsa2048': 'test_value_8',
            'check_ca_cert': 'enable',
            'check_ca_chain': 'enable',
            'cmp_save_extra_certs': 'enable',
            'cn_match': 'substring',
            'ocsp_default_server': 'test_value_13',
            'ocsp_status': 'enable',
            'ssl_min_proto_version': 'default',
            'ssl_ocsp_option': 'certificate',
            'ssl_ocsp_status': 'enable',
            'strict_crl_check': 'enable',
            'strict_ocsp_check': 'enable',
            'subject_match': 'substring'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_certificate_setting.fortios_vpn_certificate(input_data, fos_instance)

    expected_data = {
        'certname-dsa1024': 'test_value_3',
        'certname-dsa2048': 'test_value_4',
        'certname-ecdsa256': 'test_value_5',
        'certname-ecdsa384': 'test_value_6',
        'certname-rsa1024': 'test_value_7',
        'certname-rsa2048': 'test_value_8',
        'check-ca-cert': 'enable',
        'check-ca-chain': 'enable',
        'cmp-save-extra-certs': 'enable',
        'cn-match': 'substring',
        'ocsp-default-server': 'test_value_13',
        'ocsp-status': 'enable',
        'ssl-min-proto-version': 'default',
        'ssl-ocsp-option': 'certificate',
        'ssl-ocsp-status': 'enable',
        'strict-crl-check': 'enable',
        'strict-ocsp-check': 'enable',
        'subject-match': 'substring'
    }

    set_method_mock.assert_called_with('vpn.certificate', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_vpn_certificate_setting_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_certificate_setting': {
            'certname_dsa1024': 'test_value_3',
            'certname_dsa2048': 'test_value_4',
            'certname_ecdsa256': 'test_value_5',
            'certname_ecdsa384': 'test_value_6',
            'certname_rsa1024': 'test_value_7',
            'certname_rsa2048': 'test_value_8',
            'check_ca_cert': 'enable',
            'check_ca_chain': 'enable',
            'cmp_save_extra_certs': 'enable',
            'cn_match': 'substring',
            'ocsp_default_server': 'test_value_13',
            'ocsp_status': 'enable',
            'ssl_min_proto_version': 'default',
            'ssl_ocsp_option': 'certificate',
            'ssl_ocsp_status': 'enable',
            'strict_crl_check': 'enable',
            'strict_ocsp_check': 'enable',
            'subject_match': 'substring'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_certificate_setting.fortios_vpn_certificate(input_data, fos_instance)

    expected_data = {
        'certname-dsa1024': 'test_value_3',
        'certname-dsa2048': 'test_value_4',
        'certname-ecdsa256': 'test_value_5',
        'certname-ecdsa384': 'test_value_6',
        'certname-rsa1024': 'test_value_7',
        'certname-rsa2048': 'test_value_8',
        'check-ca-cert': 'enable',
        'check-ca-chain': 'enable',
        'cmp-save-extra-certs': 'enable',
        'cn-match': 'substring',
        'ocsp-default-server': 'test_value_13',
        'ocsp-status': 'enable',
        'ssl-min-proto-version': 'default',
        'ssl-ocsp-option': 'certificate',
        'ssl-ocsp-status': 'enable',
        'strict-crl-check': 'enable',
        'strict-ocsp-check': 'enable',
        'subject-match': 'substring'
    }

    set_method_mock.assert_called_with('vpn.certificate', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_vpn_certificate_setting_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_certificate_setting': {
            'certname_dsa1024': 'test_value_3',
            'certname_dsa2048': 'test_value_4',
            'certname_ecdsa256': 'test_value_5',
            'certname_ecdsa384': 'test_value_6',
            'certname_rsa1024': 'test_value_7',
            'certname_rsa2048': 'test_value_8',
            'check_ca_cert': 'enable',
            'check_ca_chain': 'enable',
            'cmp_save_extra_certs': 'enable',
            'cn_match': 'substring',
            'ocsp_default_server': 'test_value_13',
            'ocsp_status': 'enable',
            'ssl_min_proto_version': 'default',
            'ssl_ocsp_option': 'certificate',
            'ssl_ocsp_status': 'enable',
            'strict_crl_check': 'enable',
            'strict_ocsp_check': 'enable',
            'subject_match': 'substring'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_certificate_setting.fortios_vpn_certificate(input_data, fos_instance)

    expected_data = {
        'certname-dsa1024': 'test_value_3',
        'certname-dsa2048': 'test_value_4',
        'certname-ecdsa256': 'test_value_5',
        'certname-ecdsa384': 'test_value_6',
        'certname-rsa1024': 'test_value_7',
        'certname-rsa2048': 'test_value_8',
        'check-ca-cert': 'enable',
        'check-ca-chain': 'enable',
        'cmp-save-extra-certs': 'enable',
        'cn-match': 'substring',
        'ocsp-default-server': 'test_value_13',
        'ocsp-status': 'enable',
        'ssl-min-proto-version': 'default',
        'ssl-ocsp-option': 'certificate',
        'ssl-ocsp-status': 'enable',
        'strict-crl-check': 'enable',
        'strict-ocsp-check': 'enable',
        'subject-match': 'substring'
    }

    set_method_mock.assert_called_with('vpn.certificate', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_vpn_certificate_setting_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_certificate_setting': {
            'random_attribute_not_valid': 'tag',
            'certname_dsa1024': 'test_value_3',
            'certname_dsa2048': 'test_value_4',
            'certname_ecdsa256': 'test_value_5',
            'certname_ecdsa384': 'test_value_6',
            'certname_rsa1024': 'test_value_7',
            'certname_rsa2048': 'test_value_8',
            'check_ca_cert': 'enable',
            'check_ca_chain': 'enable',
            'cmp_save_extra_certs': 'enable',
            'cn_match': 'substring',
            'ocsp_default_server': 'test_value_13',
            'ocsp_status': 'enable',
            'ssl_min_proto_version': 'default',
            'ssl_ocsp_option': 'certificate',
            'ssl_ocsp_status': 'enable',
            'strict_crl_check': 'enable',
            'strict_ocsp_check': 'enable',
            'subject_match': 'substring'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_certificate_setting.fortios_vpn_certificate(input_data, fos_instance)

    expected_data = {
        'certname-dsa1024': 'test_value_3',
        'certname-dsa2048': 'test_value_4',
        'certname-ecdsa256': 'test_value_5',
        'certname-ecdsa384': 'test_value_6',
        'certname-rsa1024': 'test_value_7',
        'certname-rsa2048': 'test_value_8',
        'check-ca-cert': 'enable',
        'check-ca-chain': 'enable',
        'cmp-save-extra-certs': 'enable',
        'cn-match': 'substring',
        'ocsp-default-server': 'test_value_13',
        'ocsp-status': 'enable',
        'ssl-min-proto-version': 'default',
        'ssl-ocsp-option': 'certificate',
        'ssl-ocsp-status': 'enable',
        'strict-crl-check': 'enable',
        'strict-ocsp-check': 'enable',
        'subject-match': 'substring'
    }

    set_method_mock.assert_called_with('vpn.certificate', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
