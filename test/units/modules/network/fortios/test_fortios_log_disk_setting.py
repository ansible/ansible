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
    from ansible.modules.network.fortios import fortios_log_disk_setting
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_log_disk_setting.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_log_disk_setting_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'log_disk_setting': {
            'diskfull': 'overwrite',
            'dlp_archive_quota': '4',
            'full_final_warning_threshold': '5',
            'full_first_warning_threshold': '6',
            'full_second_warning_threshold': '7',
            'ips_archive': 'enable',
            'log_quota': '9',
            'max_log_file_size': '10',
            'max_policy_packet_capture_size': '11',
            'maximum_log_age': '12',
            'report_quota': '13',
            'roll_day': 'sunday',
            'roll_schedule': 'daily',
            'roll_time': 'test_value_16',
            'source_ip': '84.230.14.17',
            'status': 'enable',
            'upload': 'enable',
            'upload_delete_files': 'enable',
            'upload_destination': 'ftp-server',
            'upload_ssl_conn': 'default',
            'uploaddir': 'test_value_23',
            'uploadip': 'test_value_24',
            'uploadpass': 'test_value_25',
            'uploadport': '26',
            'uploadsched': 'disable',
            'uploadtime': 'test_value_28',
            'uploadtype': 'traffic',
            'uploaduser': 'test_value_30'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_log_disk_setting.fortios_log_disk(input_data, fos_instance)

    expected_data = {
        'diskfull': 'overwrite',
        'dlp-archive-quota': '4',
        'full-final-warning-threshold': '5',
        'full-first-warning-threshold': '6',
        'full-second-warning-threshold': '7',
        'ips-archive': 'enable',
        'log-quota': '9',
        'max-log-file-size': '10',
        'max-policy-packet-capture-size': '11',
        'maximum-log-age': '12',
        'report-quota': '13',
        'roll-day': 'sunday',
        'roll-schedule': 'daily',
        'roll-time': 'test_value_16',
        'source-ip': '84.230.14.17',
        'status': 'enable',
        'upload': 'enable',
        'upload-delete-files': 'enable',
        'upload-destination': 'ftp-server',
        'upload-ssl-conn': 'default',
        'uploaddir': 'test_value_23',
        'uploadip': 'test_value_24',
        'uploadpass': 'test_value_25',
        'uploadport': '26',
        'uploadsched': 'disable',
        'uploadtime': 'test_value_28',
        'uploadtype': 'traffic',
        'uploaduser': 'test_value_30'
    }

    set_method_mock.assert_called_with('log.disk', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_log_disk_setting_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'log_disk_setting': {
            'diskfull': 'overwrite',
            'dlp_archive_quota': '4',
            'full_final_warning_threshold': '5',
            'full_first_warning_threshold': '6',
            'full_second_warning_threshold': '7',
            'ips_archive': 'enable',
            'log_quota': '9',
            'max_log_file_size': '10',
            'max_policy_packet_capture_size': '11',
            'maximum_log_age': '12',
            'report_quota': '13',
            'roll_day': 'sunday',
            'roll_schedule': 'daily',
            'roll_time': 'test_value_16',
            'source_ip': '84.230.14.17',
            'status': 'enable',
            'upload': 'enable',
            'upload_delete_files': 'enable',
            'upload_destination': 'ftp-server',
            'upload_ssl_conn': 'default',
            'uploaddir': 'test_value_23',
            'uploadip': 'test_value_24',
            'uploadpass': 'test_value_25',
            'uploadport': '26',
            'uploadsched': 'disable',
            'uploadtime': 'test_value_28',
            'uploadtype': 'traffic',
            'uploaduser': 'test_value_30'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_log_disk_setting.fortios_log_disk(input_data, fos_instance)

    expected_data = {
        'diskfull': 'overwrite',
        'dlp-archive-quota': '4',
        'full-final-warning-threshold': '5',
        'full-first-warning-threshold': '6',
        'full-second-warning-threshold': '7',
        'ips-archive': 'enable',
        'log-quota': '9',
        'max-log-file-size': '10',
        'max-policy-packet-capture-size': '11',
        'maximum-log-age': '12',
        'report-quota': '13',
        'roll-day': 'sunday',
        'roll-schedule': 'daily',
        'roll-time': 'test_value_16',
        'source-ip': '84.230.14.17',
        'status': 'enable',
        'upload': 'enable',
        'upload-delete-files': 'enable',
        'upload-destination': 'ftp-server',
        'upload-ssl-conn': 'default',
        'uploaddir': 'test_value_23',
        'uploadip': 'test_value_24',
        'uploadpass': 'test_value_25',
        'uploadport': '26',
        'uploadsched': 'disable',
        'uploadtime': 'test_value_28',
        'uploadtype': 'traffic',
        'uploaduser': 'test_value_30'
    }

    set_method_mock.assert_called_with('log.disk', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_log_disk_setting_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'log_disk_setting': {
            'diskfull': 'overwrite',
            'dlp_archive_quota': '4',
            'full_final_warning_threshold': '5',
            'full_first_warning_threshold': '6',
            'full_second_warning_threshold': '7',
            'ips_archive': 'enable',
            'log_quota': '9',
            'max_log_file_size': '10',
            'max_policy_packet_capture_size': '11',
            'maximum_log_age': '12',
            'report_quota': '13',
            'roll_day': 'sunday',
            'roll_schedule': 'daily',
            'roll_time': 'test_value_16',
            'source_ip': '84.230.14.17',
            'status': 'enable',
            'upload': 'enable',
            'upload_delete_files': 'enable',
            'upload_destination': 'ftp-server',
            'upload_ssl_conn': 'default',
            'uploaddir': 'test_value_23',
            'uploadip': 'test_value_24',
            'uploadpass': 'test_value_25',
            'uploadport': '26',
            'uploadsched': 'disable',
            'uploadtime': 'test_value_28',
            'uploadtype': 'traffic',
            'uploaduser': 'test_value_30'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_log_disk_setting.fortios_log_disk(input_data, fos_instance)

    expected_data = {
        'diskfull': 'overwrite',
        'dlp-archive-quota': '4',
        'full-final-warning-threshold': '5',
        'full-first-warning-threshold': '6',
        'full-second-warning-threshold': '7',
        'ips-archive': 'enable',
        'log-quota': '9',
        'max-log-file-size': '10',
        'max-policy-packet-capture-size': '11',
        'maximum-log-age': '12',
        'report-quota': '13',
        'roll-day': 'sunday',
        'roll-schedule': 'daily',
        'roll-time': 'test_value_16',
        'source-ip': '84.230.14.17',
        'status': 'enable',
        'upload': 'enable',
        'upload-delete-files': 'enable',
        'upload-destination': 'ftp-server',
        'upload-ssl-conn': 'default',
        'uploaddir': 'test_value_23',
        'uploadip': 'test_value_24',
        'uploadpass': 'test_value_25',
        'uploadport': '26',
        'uploadsched': 'disable',
        'uploadtime': 'test_value_28',
        'uploadtype': 'traffic',
        'uploaduser': 'test_value_30'
    }

    set_method_mock.assert_called_with('log.disk', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_log_disk_setting_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'log_disk_setting': {
            'random_attribute_not_valid': 'tag',
            'diskfull': 'overwrite',
            'dlp_archive_quota': '4',
            'full_final_warning_threshold': '5',
            'full_first_warning_threshold': '6',
            'full_second_warning_threshold': '7',
            'ips_archive': 'enable',
            'log_quota': '9',
            'max_log_file_size': '10',
            'max_policy_packet_capture_size': '11',
            'maximum_log_age': '12',
            'report_quota': '13',
            'roll_day': 'sunday',
            'roll_schedule': 'daily',
            'roll_time': 'test_value_16',
            'source_ip': '84.230.14.17',
            'status': 'enable',
            'upload': 'enable',
            'upload_delete_files': 'enable',
            'upload_destination': 'ftp-server',
            'upload_ssl_conn': 'default',
            'uploaddir': 'test_value_23',
            'uploadip': 'test_value_24',
            'uploadpass': 'test_value_25',
            'uploadport': '26',
            'uploadsched': 'disable',
            'uploadtime': 'test_value_28',
            'uploadtype': 'traffic',
            'uploaduser': 'test_value_30'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_log_disk_setting.fortios_log_disk(input_data, fos_instance)

    expected_data = {
        'diskfull': 'overwrite',
        'dlp-archive-quota': '4',
        'full-final-warning-threshold': '5',
        'full-first-warning-threshold': '6',
        'full-second-warning-threshold': '7',
        'ips-archive': 'enable',
        'log-quota': '9',
        'max-log-file-size': '10',
        'max-policy-packet-capture-size': '11',
        'maximum-log-age': '12',
        'report-quota': '13',
        'roll-day': 'sunday',
        'roll-schedule': 'daily',
        'roll-time': 'test_value_16',
        'source-ip': '84.230.14.17',
        'status': 'enable',
        'upload': 'enable',
        'upload-delete-files': 'enable',
        'upload-destination': 'ftp-server',
        'upload-ssl-conn': 'default',
        'uploaddir': 'test_value_23',
        'uploadip': 'test_value_24',
        'uploadpass': 'test_value_25',
        'uploadport': '26',
        'uploadsched': 'disable',
        'uploadtime': 'test_value_28',
        'uploadtype': 'traffic',
        'uploaduser': 'test_value_30'
    }

    set_method_mock.assert_called_with('log.disk', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
