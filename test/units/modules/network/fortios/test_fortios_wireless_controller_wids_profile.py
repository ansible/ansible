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
    from ansible.modules.network.fortios import fortios_wireless_controller_wids_profile
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_wireless_controller_wids_profile.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_wireless_controller_wids_profile_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wids_profile': {
            'ap_auto_suppress': 'enable',
            'ap_bgscan_disable_day': 'sunday',
            'ap_bgscan_disable_end': 'test_value_5',
            'ap_bgscan_disable_start': 'test_value_6',
            'ap_bgscan_duration': '7',
            'ap_bgscan_idle': '8',
            'ap_bgscan_intv': '9',
            'ap_bgscan_period': '10',
            'ap_bgscan_report_intv': '11',
            'ap_fgscan_report_intv': '12',
            'ap_scan': 'disable',
            'ap_scan_passive': 'enable',
            'asleap_attack': 'enable',
            'assoc_flood_thresh': '16',
            'assoc_flood_time': '17',
            'assoc_frame_flood': 'enable',
            'auth_flood_thresh': '19',
            'auth_flood_time': '20',
            'auth_frame_flood': 'enable',
            'comment': 'Comment.',
            'deauth_broadcast': 'enable',
            'deauth_unknown_src_thresh': '24',
            'eapol_fail_flood': 'enable',
            'eapol_fail_intv': '26',
            'eapol_fail_thresh': '27',
            'eapol_logoff_flood': 'enable',
            'eapol_logoff_intv': '29',
            'eapol_logoff_thresh': '30',
            'eapol_pre_fail_flood': 'enable',
            'eapol_pre_fail_intv': '32',
            'eapol_pre_fail_thresh': '33',
            'eapol_pre_succ_flood': 'enable',
            'eapol_pre_succ_intv': '35',
            'eapol_pre_succ_thresh': '36',
            'eapol_start_flood': 'enable',
            'eapol_start_intv': '38',
            'eapol_start_thresh': '39',
            'eapol_succ_flood': 'enable',
            'eapol_succ_intv': '41',
            'eapol_succ_thresh': '42',
            'invalid_mac_oui': 'enable',
            'long_duration_attack': 'enable',
            'long_duration_thresh': '45',
            'name': 'default_name_46',
            'null_ssid_probe_resp': 'enable',
            'sensor_mode': 'disable',
            'spoofed_deauth': 'enable',
            'weak_wep_iv': 'enable',
            'wireless_bridge': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wids_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ap-auto-suppress': 'enable',
        'ap-bgscan-disable-day': 'sunday',
        'ap-bgscan-disable-end': 'test_value_5',
        'ap-bgscan-disable-start': 'test_value_6',
        'ap-bgscan-duration': '7',
        'ap-bgscan-idle': '8',
        'ap-bgscan-intv': '9',
        'ap-bgscan-period': '10',
        'ap-bgscan-report-intv': '11',
        'ap-fgscan-report-intv': '12',
        'ap-scan': 'disable',
        'ap-scan-passive': 'enable',
        'asleap-attack': 'enable',
        'assoc-flood-thresh': '16',
        'assoc-flood-time': '17',
        'assoc-frame-flood': 'enable',
        'auth-flood-thresh': '19',
        'auth-flood-time': '20',
        'auth-frame-flood': 'enable',
        'comment': 'Comment.',
        'deauth-broadcast': 'enable',
        'deauth-unknown-src-thresh': '24',
        'eapol-fail-flood': 'enable',
        'eapol-fail-intv': '26',
        'eapol-fail-thresh': '27',
        'eapol-logoff-flood': 'enable',
        'eapol-logoff-intv': '29',
        'eapol-logoff-thresh': '30',
        'eapol-pre-fail-flood': 'enable',
        'eapol-pre-fail-intv': '32',
        'eapol-pre-fail-thresh': '33',
        'eapol-pre-succ-flood': 'enable',
        'eapol-pre-succ-intv': '35',
        'eapol-pre-succ-thresh': '36',
        'eapol-start-flood': 'enable',
        'eapol-start-intv': '38',
        'eapol-start-thresh': '39',
        'eapol-succ-flood': 'enable',
        'eapol-succ-intv': '41',
        'eapol-succ-thresh': '42',
        'invalid-mac-oui': 'enable',
        'long-duration-attack': 'enable',
        'long-duration-thresh': '45',
        'name': 'default_name_46',
                'null-ssid-probe-resp': 'enable',
                'sensor-mode': 'disable',
                'spoofed-deauth': 'enable',
                'weak-wep-iv': 'enable',
                'wireless-bridge': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wids-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_wids_profile_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wids_profile': {
            'ap_auto_suppress': 'enable',
            'ap_bgscan_disable_day': 'sunday',
            'ap_bgscan_disable_end': 'test_value_5',
            'ap_bgscan_disable_start': 'test_value_6',
            'ap_bgscan_duration': '7',
            'ap_bgscan_idle': '8',
            'ap_bgscan_intv': '9',
            'ap_bgscan_period': '10',
            'ap_bgscan_report_intv': '11',
            'ap_fgscan_report_intv': '12',
            'ap_scan': 'disable',
            'ap_scan_passive': 'enable',
            'asleap_attack': 'enable',
            'assoc_flood_thresh': '16',
            'assoc_flood_time': '17',
            'assoc_frame_flood': 'enable',
            'auth_flood_thresh': '19',
            'auth_flood_time': '20',
            'auth_frame_flood': 'enable',
            'comment': 'Comment.',
            'deauth_broadcast': 'enable',
            'deauth_unknown_src_thresh': '24',
            'eapol_fail_flood': 'enable',
            'eapol_fail_intv': '26',
            'eapol_fail_thresh': '27',
            'eapol_logoff_flood': 'enable',
            'eapol_logoff_intv': '29',
            'eapol_logoff_thresh': '30',
            'eapol_pre_fail_flood': 'enable',
            'eapol_pre_fail_intv': '32',
            'eapol_pre_fail_thresh': '33',
            'eapol_pre_succ_flood': 'enable',
            'eapol_pre_succ_intv': '35',
            'eapol_pre_succ_thresh': '36',
            'eapol_start_flood': 'enable',
            'eapol_start_intv': '38',
            'eapol_start_thresh': '39',
            'eapol_succ_flood': 'enable',
            'eapol_succ_intv': '41',
            'eapol_succ_thresh': '42',
            'invalid_mac_oui': 'enable',
            'long_duration_attack': 'enable',
            'long_duration_thresh': '45',
            'name': 'default_name_46',
            'null_ssid_probe_resp': 'enable',
            'sensor_mode': 'disable',
            'spoofed_deauth': 'enable',
            'weak_wep_iv': 'enable',
            'wireless_bridge': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wids_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ap-auto-suppress': 'enable',
        'ap-bgscan-disable-day': 'sunday',
        'ap-bgscan-disable-end': 'test_value_5',
        'ap-bgscan-disable-start': 'test_value_6',
        'ap-bgscan-duration': '7',
        'ap-bgscan-idle': '8',
        'ap-bgscan-intv': '9',
        'ap-bgscan-period': '10',
        'ap-bgscan-report-intv': '11',
        'ap-fgscan-report-intv': '12',
        'ap-scan': 'disable',
        'ap-scan-passive': 'enable',
        'asleap-attack': 'enable',
        'assoc-flood-thresh': '16',
        'assoc-flood-time': '17',
        'assoc-frame-flood': 'enable',
        'auth-flood-thresh': '19',
        'auth-flood-time': '20',
        'auth-frame-flood': 'enable',
        'comment': 'Comment.',
        'deauth-broadcast': 'enable',
        'deauth-unknown-src-thresh': '24',
        'eapol-fail-flood': 'enable',
        'eapol-fail-intv': '26',
        'eapol-fail-thresh': '27',
        'eapol-logoff-flood': 'enable',
        'eapol-logoff-intv': '29',
        'eapol-logoff-thresh': '30',
        'eapol-pre-fail-flood': 'enable',
        'eapol-pre-fail-intv': '32',
        'eapol-pre-fail-thresh': '33',
        'eapol-pre-succ-flood': 'enable',
        'eapol-pre-succ-intv': '35',
        'eapol-pre-succ-thresh': '36',
        'eapol-start-flood': 'enable',
        'eapol-start-intv': '38',
        'eapol-start-thresh': '39',
        'eapol-succ-flood': 'enable',
        'eapol-succ-intv': '41',
        'eapol-succ-thresh': '42',
        'invalid-mac-oui': 'enable',
        'long-duration-attack': 'enable',
        'long-duration-thresh': '45',
        'name': 'default_name_46',
                'null-ssid-probe-resp': 'enable',
                'sensor-mode': 'disable',
                'spoofed-deauth': 'enable',
                'weak-wep-iv': 'enable',
                'wireless-bridge': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wids-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_wids_profile_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_wids_profile': {
            'ap_auto_suppress': 'enable',
            'ap_bgscan_disable_day': 'sunday',
            'ap_bgscan_disable_end': 'test_value_5',
            'ap_bgscan_disable_start': 'test_value_6',
            'ap_bgscan_duration': '7',
            'ap_bgscan_idle': '8',
            'ap_bgscan_intv': '9',
            'ap_bgscan_period': '10',
            'ap_bgscan_report_intv': '11',
            'ap_fgscan_report_intv': '12',
            'ap_scan': 'disable',
            'ap_scan_passive': 'enable',
            'asleap_attack': 'enable',
            'assoc_flood_thresh': '16',
            'assoc_flood_time': '17',
            'assoc_frame_flood': 'enable',
            'auth_flood_thresh': '19',
            'auth_flood_time': '20',
            'auth_frame_flood': 'enable',
            'comment': 'Comment.',
            'deauth_broadcast': 'enable',
            'deauth_unknown_src_thresh': '24',
            'eapol_fail_flood': 'enable',
            'eapol_fail_intv': '26',
            'eapol_fail_thresh': '27',
            'eapol_logoff_flood': 'enable',
            'eapol_logoff_intv': '29',
            'eapol_logoff_thresh': '30',
            'eapol_pre_fail_flood': 'enable',
            'eapol_pre_fail_intv': '32',
            'eapol_pre_fail_thresh': '33',
            'eapol_pre_succ_flood': 'enable',
            'eapol_pre_succ_intv': '35',
            'eapol_pre_succ_thresh': '36',
            'eapol_start_flood': 'enable',
            'eapol_start_intv': '38',
            'eapol_start_thresh': '39',
            'eapol_succ_flood': 'enable',
            'eapol_succ_intv': '41',
            'eapol_succ_thresh': '42',
            'invalid_mac_oui': 'enable',
            'long_duration_attack': 'enable',
            'long_duration_thresh': '45',
            'name': 'default_name_46',
            'null_ssid_probe_resp': 'enable',
            'sensor_mode': 'disable',
            'spoofed_deauth': 'enable',
            'weak_wep_iv': 'enable',
            'wireless_bridge': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wids_profile.fortios_wireless_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller', 'wids-profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_wireless_controller_wids_profile_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'wireless_controller_wids_profile': {
            'ap_auto_suppress': 'enable',
            'ap_bgscan_disable_day': 'sunday',
            'ap_bgscan_disable_end': 'test_value_5',
            'ap_bgscan_disable_start': 'test_value_6',
            'ap_bgscan_duration': '7',
            'ap_bgscan_idle': '8',
            'ap_bgscan_intv': '9',
            'ap_bgscan_period': '10',
            'ap_bgscan_report_intv': '11',
            'ap_fgscan_report_intv': '12',
            'ap_scan': 'disable',
            'ap_scan_passive': 'enable',
            'asleap_attack': 'enable',
            'assoc_flood_thresh': '16',
            'assoc_flood_time': '17',
            'assoc_frame_flood': 'enable',
            'auth_flood_thresh': '19',
            'auth_flood_time': '20',
            'auth_frame_flood': 'enable',
            'comment': 'Comment.',
            'deauth_broadcast': 'enable',
            'deauth_unknown_src_thresh': '24',
            'eapol_fail_flood': 'enable',
            'eapol_fail_intv': '26',
            'eapol_fail_thresh': '27',
            'eapol_logoff_flood': 'enable',
            'eapol_logoff_intv': '29',
            'eapol_logoff_thresh': '30',
            'eapol_pre_fail_flood': 'enable',
            'eapol_pre_fail_intv': '32',
            'eapol_pre_fail_thresh': '33',
            'eapol_pre_succ_flood': 'enable',
            'eapol_pre_succ_intv': '35',
            'eapol_pre_succ_thresh': '36',
            'eapol_start_flood': 'enable',
            'eapol_start_intv': '38',
            'eapol_start_thresh': '39',
            'eapol_succ_flood': 'enable',
            'eapol_succ_intv': '41',
            'eapol_succ_thresh': '42',
            'invalid_mac_oui': 'enable',
            'long_duration_attack': 'enable',
            'long_duration_thresh': '45',
            'name': 'default_name_46',
            'null_ssid_probe_resp': 'enable',
            'sensor_mode': 'disable',
            'spoofed_deauth': 'enable',
            'weak_wep_iv': 'enable',
            'wireless_bridge': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wids_profile.fortios_wireless_controller(input_data, fos_instance)

    delete_method_mock.assert_called_with('wireless-controller', 'wids-profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_wireless_controller_wids_profile_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wids_profile': {
            'ap_auto_suppress': 'enable',
            'ap_bgscan_disable_day': 'sunday',
            'ap_bgscan_disable_end': 'test_value_5',
            'ap_bgscan_disable_start': 'test_value_6',
            'ap_bgscan_duration': '7',
            'ap_bgscan_idle': '8',
            'ap_bgscan_intv': '9',
            'ap_bgscan_period': '10',
            'ap_bgscan_report_intv': '11',
            'ap_fgscan_report_intv': '12',
            'ap_scan': 'disable',
            'ap_scan_passive': 'enable',
            'asleap_attack': 'enable',
            'assoc_flood_thresh': '16',
            'assoc_flood_time': '17',
            'assoc_frame_flood': 'enable',
            'auth_flood_thresh': '19',
            'auth_flood_time': '20',
            'auth_frame_flood': 'enable',
            'comment': 'Comment.',
            'deauth_broadcast': 'enable',
            'deauth_unknown_src_thresh': '24',
            'eapol_fail_flood': 'enable',
            'eapol_fail_intv': '26',
            'eapol_fail_thresh': '27',
            'eapol_logoff_flood': 'enable',
            'eapol_logoff_intv': '29',
            'eapol_logoff_thresh': '30',
            'eapol_pre_fail_flood': 'enable',
            'eapol_pre_fail_intv': '32',
            'eapol_pre_fail_thresh': '33',
            'eapol_pre_succ_flood': 'enable',
            'eapol_pre_succ_intv': '35',
            'eapol_pre_succ_thresh': '36',
            'eapol_start_flood': 'enable',
            'eapol_start_intv': '38',
            'eapol_start_thresh': '39',
            'eapol_succ_flood': 'enable',
            'eapol_succ_intv': '41',
            'eapol_succ_thresh': '42',
            'invalid_mac_oui': 'enable',
            'long_duration_attack': 'enable',
            'long_duration_thresh': '45',
            'name': 'default_name_46',
            'null_ssid_probe_resp': 'enable',
            'sensor_mode': 'disable',
            'spoofed_deauth': 'enable',
            'weak_wep_iv': 'enable',
            'wireless_bridge': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wids_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ap-auto-suppress': 'enable',
        'ap-bgscan-disable-day': 'sunday',
        'ap-bgscan-disable-end': 'test_value_5',
        'ap-bgscan-disable-start': 'test_value_6',
        'ap-bgscan-duration': '7',
        'ap-bgscan-idle': '8',
        'ap-bgscan-intv': '9',
        'ap-bgscan-period': '10',
        'ap-bgscan-report-intv': '11',
        'ap-fgscan-report-intv': '12',
        'ap-scan': 'disable',
        'ap-scan-passive': 'enable',
        'asleap-attack': 'enable',
        'assoc-flood-thresh': '16',
        'assoc-flood-time': '17',
        'assoc-frame-flood': 'enable',
        'auth-flood-thresh': '19',
        'auth-flood-time': '20',
        'auth-frame-flood': 'enable',
        'comment': 'Comment.',
        'deauth-broadcast': 'enable',
        'deauth-unknown-src-thresh': '24',
        'eapol-fail-flood': 'enable',
        'eapol-fail-intv': '26',
        'eapol-fail-thresh': '27',
        'eapol-logoff-flood': 'enable',
        'eapol-logoff-intv': '29',
        'eapol-logoff-thresh': '30',
        'eapol-pre-fail-flood': 'enable',
        'eapol-pre-fail-intv': '32',
        'eapol-pre-fail-thresh': '33',
        'eapol-pre-succ-flood': 'enable',
        'eapol-pre-succ-intv': '35',
        'eapol-pre-succ-thresh': '36',
        'eapol-start-flood': 'enable',
        'eapol-start-intv': '38',
        'eapol-start-thresh': '39',
        'eapol-succ-flood': 'enable',
        'eapol-succ-intv': '41',
        'eapol-succ-thresh': '42',
        'invalid-mac-oui': 'enable',
        'long-duration-attack': 'enable',
        'long-duration-thresh': '45',
        'name': 'default_name_46',
                'null-ssid-probe-resp': 'enable',
                'sensor-mode': 'disable',
                'spoofed-deauth': 'enable',
                'weak-wep-iv': 'enable',
                'wireless-bridge': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wids-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_wireless_controller_wids_profile_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'wireless_controller_wids_profile': {
            'random_attribute_not_valid': 'tag',
            'ap_auto_suppress': 'enable',
            'ap_bgscan_disable_day': 'sunday',
            'ap_bgscan_disable_end': 'test_value_5',
            'ap_bgscan_disable_start': 'test_value_6',
            'ap_bgscan_duration': '7',
            'ap_bgscan_idle': '8',
            'ap_bgscan_intv': '9',
            'ap_bgscan_period': '10',
            'ap_bgscan_report_intv': '11',
            'ap_fgscan_report_intv': '12',
            'ap_scan': 'disable',
            'ap_scan_passive': 'enable',
            'asleap_attack': 'enable',
            'assoc_flood_thresh': '16',
            'assoc_flood_time': '17',
            'assoc_frame_flood': 'enable',
            'auth_flood_thresh': '19',
            'auth_flood_time': '20',
            'auth_frame_flood': 'enable',
            'comment': 'Comment.',
            'deauth_broadcast': 'enable',
            'deauth_unknown_src_thresh': '24',
            'eapol_fail_flood': 'enable',
            'eapol_fail_intv': '26',
            'eapol_fail_thresh': '27',
            'eapol_logoff_flood': 'enable',
            'eapol_logoff_intv': '29',
            'eapol_logoff_thresh': '30',
            'eapol_pre_fail_flood': 'enable',
            'eapol_pre_fail_intv': '32',
            'eapol_pre_fail_thresh': '33',
            'eapol_pre_succ_flood': 'enable',
            'eapol_pre_succ_intv': '35',
            'eapol_pre_succ_thresh': '36',
            'eapol_start_flood': 'enable',
            'eapol_start_intv': '38',
            'eapol_start_thresh': '39',
            'eapol_succ_flood': 'enable',
            'eapol_succ_intv': '41',
            'eapol_succ_thresh': '42',
            'invalid_mac_oui': 'enable',
            'long_duration_attack': 'enable',
            'long_duration_thresh': '45',
            'name': 'default_name_46',
            'null_ssid_probe_resp': 'enable',
            'sensor_mode': 'disable',
            'spoofed_deauth': 'enable',
            'weak_wep_iv': 'enable',
            'wireless_bridge': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_wireless_controller_wids_profile.fortios_wireless_controller(input_data, fos_instance)

    expected_data = {
        'ap-auto-suppress': 'enable',
        'ap-bgscan-disable-day': 'sunday',
        'ap-bgscan-disable-end': 'test_value_5',
        'ap-bgscan-disable-start': 'test_value_6',
        'ap-bgscan-duration': '7',
        'ap-bgscan-idle': '8',
        'ap-bgscan-intv': '9',
        'ap-bgscan-period': '10',
        'ap-bgscan-report-intv': '11',
        'ap-fgscan-report-intv': '12',
        'ap-scan': 'disable',
        'ap-scan-passive': 'enable',
        'asleap-attack': 'enable',
        'assoc-flood-thresh': '16',
        'assoc-flood-time': '17',
        'assoc-frame-flood': 'enable',
        'auth-flood-thresh': '19',
        'auth-flood-time': '20',
        'auth-frame-flood': 'enable',
        'comment': 'Comment.',
        'deauth-broadcast': 'enable',
        'deauth-unknown-src-thresh': '24',
        'eapol-fail-flood': 'enable',
        'eapol-fail-intv': '26',
        'eapol-fail-thresh': '27',
        'eapol-logoff-flood': 'enable',
        'eapol-logoff-intv': '29',
        'eapol-logoff-thresh': '30',
        'eapol-pre-fail-flood': 'enable',
        'eapol-pre-fail-intv': '32',
        'eapol-pre-fail-thresh': '33',
        'eapol-pre-succ-flood': 'enable',
        'eapol-pre-succ-intv': '35',
        'eapol-pre-succ-thresh': '36',
        'eapol-start-flood': 'enable',
        'eapol-start-intv': '38',
        'eapol-start-thresh': '39',
        'eapol-succ-flood': 'enable',
        'eapol-succ-intv': '41',
        'eapol-succ-thresh': '42',
        'invalid-mac-oui': 'enable',
        'long-duration-attack': 'enable',
        'long-duration-thresh': '45',
        'name': 'default_name_46',
                'null-ssid-probe-resp': 'enable',
                'sensor-mode': 'disable',
                'spoofed-deauth': 'enable',
                'weak-wep-iv': 'enable',
                'wireless-bridge': 'enable'
    }

    set_method_mock.assert_called_with('wireless-controller', 'wids-profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
