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
    from ansible.modules.network.fortios import fortios_alertemail_setting
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_alertemail_setting.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_alertemail_setting_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'alertemail_setting': {
            'admin_login_logs': 'enable',
            'alert_interval': '4',
            'amc_interface_bypass_mode': 'enable',
            'antivirus_logs': 'enable',
            'configuration_changes_logs': 'enable',
            'critical_interval': '8',
            'debug_interval': '9',
            'email_interval': '10',
            'emergency_interval': '11',
            'error_interval': '12',
            'FDS_license_expiring_days': '13',
            'FDS_license_expiring_warning': 'enable',
            'FDS_update_logs': 'enable',
            'filter_mode': 'category',
            'FIPS_CC_errors': 'enable',
            'firewall_authentication_failure_logs': 'enable',
            'fortiguard_log_quota_warning': 'enable',
            'FSSO_disconnect_logs': 'enable',
            'HA_logs': 'enable',
            'information_interval': '22',
            'IPS_logs': 'enable',
            'IPsec_errors_logs': 'enable',
            'local_disk_usage': '25',
            'log_disk_usage_warning': 'enable',
            'mailto1': 'test_value_27',
            'mailto2': 'test_value_28',
            'mailto3': 'test_value_29',
            'notification_interval': '30',
            'PPP_errors_logs': 'enable',
            'severity': 'emergency',
            'ssh_logs': 'enable',
            'sslvpn_authentication_errors_logs': 'enable',
            'username': 'test_value_35',
            'violation_traffic_logs': 'enable',
            'warning_interval': '37',
            'webfilter_logs': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_alertemail_setting.fortios_alertemail(input_data, fos_instance)

    expected_data = {
        'admin-login-logs': 'enable',
        'alert-interval': '4',
        'amc-interface-bypass-mode': 'enable',
        'antivirus-logs': 'enable',
        'configuration-changes-logs': 'enable',
        'critical-interval': '8',
        'debug-interval': '9',
        'email-interval': '10',
        'emergency-interval': '11',
        'error-interval': '12',
        'FDS-license-expiring-days': '13',
        'FDS-license-expiring-warning': 'enable',
        'FDS-update-logs': 'enable',
        'filter-mode': 'category',
        'FIPS-CC-errors': 'enable',
        'firewall-authentication-failure-logs': 'enable',
        'fortiguard-log-quota-warning': 'enable',
        'FSSO-disconnect-logs': 'enable',
        'HA-logs': 'enable',
        'information-interval': '22',
        'IPS-logs': 'enable',
        'IPsec-errors-logs': 'enable',
        'local-disk-usage': '25',
        'log-disk-usage-warning': 'enable',
        'mailto1': 'test_value_27',
        'mailto2': 'test_value_28',
        'mailto3': 'test_value_29',
        'notification-interval': '30',
        'PPP-errors-logs': 'enable',
        'severity': 'emergency',
        'ssh-logs': 'enable',
        'sslvpn-authentication-errors-logs': 'enable',
        'username': 'test_value_35',
        'violation-traffic-logs': 'enable',
        'warning-interval': '37',
        'webfilter-logs': 'enable'
    }

    set_method_mock.assert_called_with('alertemail', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_alertemail_setting_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'alertemail_setting': {
            'admin_login_logs': 'enable',
            'alert_interval': '4',
            'amc_interface_bypass_mode': 'enable',
            'antivirus_logs': 'enable',
            'configuration_changes_logs': 'enable',
            'critical_interval': '8',
            'debug_interval': '9',
            'email_interval': '10',
            'emergency_interval': '11',
            'error_interval': '12',
            'FDS_license_expiring_days': '13',
            'FDS_license_expiring_warning': 'enable',
            'FDS_update_logs': 'enable',
            'filter_mode': 'category',
            'FIPS_CC_errors': 'enable',
            'firewall_authentication_failure_logs': 'enable',
            'fortiguard_log_quota_warning': 'enable',
            'FSSO_disconnect_logs': 'enable',
            'HA_logs': 'enable',
            'information_interval': '22',
            'IPS_logs': 'enable',
            'IPsec_errors_logs': 'enable',
            'local_disk_usage': '25',
            'log_disk_usage_warning': 'enable',
            'mailto1': 'test_value_27',
            'mailto2': 'test_value_28',
            'mailto3': 'test_value_29',
            'notification_interval': '30',
            'PPP_errors_logs': 'enable',
            'severity': 'emergency',
            'ssh_logs': 'enable',
            'sslvpn_authentication_errors_logs': 'enable',
            'username': 'test_value_35',
            'violation_traffic_logs': 'enable',
            'warning_interval': '37',
            'webfilter_logs': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_alertemail_setting.fortios_alertemail(input_data, fos_instance)

    expected_data = {
        'admin-login-logs': 'enable',
        'alert-interval': '4',
        'amc-interface-bypass-mode': 'enable',
        'antivirus-logs': 'enable',
        'configuration-changes-logs': 'enable',
        'critical-interval': '8',
        'debug-interval': '9',
        'email-interval': '10',
        'emergency-interval': '11',
        'error-interval': '12',
        'FDS-license-expiring-days': '13',
        'FDS-license-expiring-warning': 'enable',
        'FDS-update-logs': 'enable',
        'filter-mode': 'category',
        'FIPS-CC-errors': 'enable',
        'firewall-authentication-failure-logs': 'enable',
        'fortiguard-log-quota-warning': 'enable',
        'FSSO-disconnect-logs': 'enable',
        'HA-logs': 'enable',
        'information-interval': '22',
        'IPS-logs': 'enable',
        'IPsec-errors-logs': 'enable',
        'local-disk-usage': '25',
        'log-disk-usage-warning': 'enable',
        'mailto1': 'test_value_27',
        'mailto2': 'test_value_28',
        'mailto3': 'test_value_29',
        'notification-interval': '30',
        'PPP-errors-logs': 'enable',
        'severity': 'emergency',
        'ssh-logs': 'enable',
        'sslvpn-authentication-errors-logs': 'enable',
        'username': 'test_value_35',
        'violation-traffic-logs': 'enable',
        'warning-interval': '37',
        'webfilter-logs': 'enable'
    }

    set_method_mock.assert_called_with('alertemail', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_alertemail_setting_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'alertemail_setting': {
            'admin_login_logs': 'enable',
            'alert_interval': '4',
            'amc_interface_bypass_mode': 'enable',
            'antivirus_logs': 'enable',
            'configuration_changes_logs': 'enable',
            'critical_interval': '8',
            'debug_interval': '9',
            'email_interval': '10',
            'emergency_interval': '11',
            'error_interval': '12',
            'FDS_license_expiring_days': '13',
            'FDS_license_expiring_warning': 'enable',
            'FDS_update_logs': 'enable',
            'filter_mode': 'category',
            'FIPS_CC_errors': 'enable',
            'firewall_authentication_failure_logs': 'enable',
            'fortiguard_log_quota_warning': 'enable',
            'FSSO_disconnect_logs': 'enable',
            'HA_logs': 'enable',
            'information_interval': '22',
            'IPS_logs': 'enable',
            'IPsec_errors_logs': 'enable',
            'local_disk_usage': '25',
            'log_disk_usage_warning': 'enable',
            'mailto1': 'test_value_27',
            'mailto2': 'test_value_28',
            'mailto3': 'test_value_29',
            'notification_interval': '30',
            'PPP_errors_logs': 'enable',
            'severity': 'emergency',
            'ssh_logs': 'enable',
            'sslvpn_authentication_errors_logs': 'enable',
            'username': 'test_value_35',
            'violation_traffic_logs': 'enable',
            'warning_interval': '37',
            'webfilter_logs': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_alertemail_setting.fortios_alertemail(input_data, fos_instance)

    expected_data = {
        'admin-login-logs': 'enable',
        'alert-interval': '4',
        'amc-interface-bypass-mode': 'enable',
        'antivirus-logs': 'enable',
        'configuration-changes-logs': 'enable',
        'critical-interval': '8',
        'debug-interval': '9',
        'email-interval': '10',
        'emergency-interval': '11',
        'error-interval': '12',
        'FDS-license-expiring-days': '13',
        'FDS-license-expiring-warning': 'enable',
        'FDS-update-logs': 'enable',
        'filter-mode': 'category',
        'FIPS-CC-errors': 'enable',
        'firewall-authentication-failure-logs': 'enable',
        'fortiguard-log-quota-warning': 'enable',
        'FSSO-disconnect-logs': 'enable',
        'HA-logs': 'enable',
        'information-interval': '22',
        'IPS-logs': 'enable',
        'IPsec-errors-logs': 'enable',
        'local-disk-usage': '25',
        'log-disk-usage-warning': 'enable',
        'mailto1': 'test_value_27',
        'mailto2': 'test_value_28',
        'mailto3': 'test_value_29',
        'notification-interval': '30',
        'PPP-errors-logs': 'enable',
        'severity': 'emergency',
        'ssh-logs': 'enable',
        'sslvpn-authentication-errors-logs': 'enable',
        'username': 'test_value_35',
        'violation-traffic-logs': 'enable',
        'warning-interval': '37',
        'webfilter-logs': 'enable'
    }

    set_method_mock.assert_called_with('alertemail', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_alertemail_setting_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'alertemail_setting': {
            'random_attribute_not_valid': 'tag',
            'admin_login_logs': 'enable',
            'alert_interval': '4',
            'amc_interface_bypass_mode': 'enable',
            'antivirus_logs': 'enable',
            'configuration_changes_logs': 'enable',
            'critical_interval': '8',
            'debug_interval': '9',
            'email_interval': '10',
            'emergency_interval': '11',
            'error_interval': '12',
            'FDS_license_expiring_days': '13',
            'FDS_license_expiring_warning': 'enable',
            'FDS_update_logs': 'enable',
            'filter_mode': 'category',
            'FIPS_CC_errors': 'enable',
            'firewall_authentication_failure_logs': 'enable',
            'fortiguard_log_quota_warning': 'enable',
            'FSSO_disconnect_logs': 'enable',
            'HA_logs': 'enable',
            'information_interval': '22',
            'IPS_logs': 'enable',
            'IPsec_errors_logs': 'enable',
            'local_disk_usage': '25',
            'log_disk_usage_warning': 'enable',
            'mailto1': 'test_value_27',
            'mailto2': 'test_value_28',
            'mailto3': 'test_value_29',
            'notification_interval': '30',
            'PPP_errors_logs': 'enable',
            'severity': 'emergency',
            'ssh_logs': 'enable',
            'sslvpn_authentication_errors_logs': 'enable',
            'username': 'test_value_35',
            'violation_traffic_logs': 'enable',
            'warning_interval': '37',
            'webfilter_logs': 'enable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_alertemail_setting.fortios_alertemail(input_data, fos_instance)

    expected_data = {
        'admin-login-logs': 'enable',
        'alert-interval': '4',
        'amc-interface-bypass-mode': 'enable',
        'antivirus-logs': 'enable',
        'configuration-changes-logs': 'enable',
        'critical-interval': '8',
        'debug-interval': '9',
        'email-interval': '10',
        'emergency-interval': '11',
        'error-interval': '12',
        'FDS-license-expiring-days': '13',
        'FDS-license-expiring-warning': 'enable',
        'FDS-update-logs': 'enable',
        'filter-mode': 'category',
        'FIPS-CC-errors': 'enable',
        'firewall-authentication-failure-logs': 'enable',
        'fortiguard-log-quota-warning': 'enable',
        'FSSO-disconnect-logs': 'enable',
        'HA-logs': 'enable',
        'information-interval': '22',
        'IPS-logs': 'enable',
        'IPsec-errors-logs': 'enable',
        'local-disk-usage': '25',
        'log-disk-usage-warning': 'enable',
        'mailto1': 'test_value_27',
        'mailto2': 'test_value_28',
        'mailto3': 'test_value_29',
        'notification-interval': '30',
        'PPP-errors-logs': 'enable',
        'severity': 'emergency',
        'ssh-logs': 'enable',
        'sslvpn-authentication-errors-logs': 'enable',
        'username': 'test_value_35',
        'violation-traffic-logs': 'enable',
        'warning-interval': '37',
        'webfilter-logs': 'enable'
    }

    set_method_mock.assert_called_with('alertemail', 'setting', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
