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
    from ansible.modules.network.fortios import fortios_vpn_ssl_web_portal
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_vpn_ssl_web_portal.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_vpn_ssl_web_portal_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ssl_web_portal': {
            'allow_user_access': 'web',
            'auto_connect': 'enable',
            'custom_lang': 'test_value_5',
            'customize_forticlient_download_url': 'enable',
            'display_bookmark': 'enable',
            'display_connection_tools': 'enable',
            'display_history': 'enable',
            'display_status': 'enable',
            'dns_server1': 'test_value_11',
            'dns_server2': 'test_value_12',
            'dns_suffix': 'test_value_13',
            'exclusive_routing': 'enable',
            'forticlient_download': 'enable',
            'forticlient_download_method': 'direct',
            'heading': 'test_value_17',
            'hide_sso_credential': 'enable',
            'host_check': 'none',
            'host_check_interval': '20',
            'ip_mode': 'range',
            'ipv6_dns_server1': 'test_value_22',
            'ipv6_dns_server2': 'test_value_23',
            'ipv6_exclusive_routing': 'enable',
            'ipv6_service_restriction': 'enable',
            'ipv6_split_tunneling': 'enable',
            'ipv6_tunnel_mode': 'enable',
            'ipv6_wins_server1': 'test_value_28',
            'ipv6_wins_server2': 'test_value_29',
            'keep_alive': 'enable',
            'limit_user_logins': 'enable',
            'mac_addr_action': 'allow',
            'mac_addr_check': 'enable',
            'macos_forticlient_download_url': 'test_value_34',
            'name': 'default_name_35',
            'os_check': 'enable',
            'redir_url': 'test_value_37',
            'save_password': 'enable',
            'service_restriction': 'enable',
            'skip_check_for_unsupported_browser': 'enable',
            'skip_check_for_unsupported_os': 'enable',
            'smb_ntlmv1_auth': 'enable',
            'smbv1': 'enable',
            'split_tunneling': 'enable',
            'theme': 'blue',
            'tunnel_mode': 'enable',
            'user_bookmark': 'enable',
            'user_group_bookmark': 'enable',
            'web_mode': 'enable',
            'windows_forticlient_download_url': 'test_value_50',
            'wins_server1': 'test_value_51',
            'wins_server2': 'test_value_52'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ssl_web_portal.fortios_vpn_ssl_web(input_data, fos_instance)

    expected_data = {
        'allow-user-access': 'web',
        'auto-connect': 'enable',
        'custom-lang': 'test_value_5',
        'customize-forticlient-download-url': 'enable',
        'display-bookmark': 'enable',
        'display-connection-tools': 'enable',
        'display-history': 'enable',
        'display-status': 'enable',
        'dns-server1': 'test_value_11',
        'dns-server2': 'test_value_12',
        'dns-suffix': 'test_value_13',
        'exclusive-routing': 'enable',
        'forticlient-download': 'enable',
        'forticlient-download-method': 'direct',
        'heading': 'test_value_17',
        'hide-sso-credential': 'enable',
        'host-check': 'none',
        'host-check-interval': '20',
        'ip-mode': 'range',
        'ipv6-dns-server1': 'test_value_22',
        'ipv6-dns-server2': 'test_value_23',
        'ipv6-exclusive-routing': 'enable',
        'ipv6-service-restriction': 'enable',
        'ipv6-split-tunneling': 'enable',
        'ipv6-tunnel-mode': 'enable',
        'ipv6-wins-server1': 'test_value_28',
        'ipv6-wins-server2': 'test_value_29',
        'keep-alive': 'enable',
        'limit-user-logins': 'enable',
        'mac-addr-action': 'allow',
        'mac-addr-check': 'enable',
        'macos-forticlient-download-url': 'test_value_34',
        'name': 'default_name_35',
                'os-check': 'enable',
                'redir-url': 'test_value_37',
                'save-password': 'enable',
                'service-restriction': 'enable',
                'skip-check-for-unsupported-browser': 'enable',
                'skip-check-for-unsupported-os': 'enable',
                'smb-ntlmv1-auth': 'enable',
                'smbv1': 'enable',
                'split-tunneling': 'enable',
                'theme': 'blue',
                'tunnel-mode': 'enable',
                'user-bookmark': 'enable',
                'user-group-bookmark': 'enable',
                'web-mode': 'enable',
                'windows-forticlient-download-url': 'test_value_50',
                'wins-server1': 'test_value_51',
                'wins-server2': 'test_value_52'
    }

    set_method_mock.assert_called_with('vpn.ssl.web', 'portal', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_vpn_ssl_web_portal_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ssl_web_portal': {
            'allow_user_access': 'web',
            'auto_connect': 'enable',
            'custom_lang': 'test_value_5',
            'customize_forticlient_download_url': 'enable',
            'display_bookmark': 'enable',
            'display_connection_tools': 'enable',
            'display_history': 'enable',
            'display_status': 'enable',
            'dns_server1': 'test_value_11',
            'dns_server2': 'test_value_12',
            'dns_suffix': 'test_value_13',
            'exclusive_routing': 'enable',
            'forticlient_download': 'enable',
            'forticlient_download_method': 'direct',
            'heading': 'test_value_17',
            'hide_sso_credential': 'enable',
            'host_check': 'none',
            'host_check_interval': '20',
            'ip_mode': 'range',
            'ipv6_dns_server1': 'test_value_22',
            'ipv6_dns_server2': 'test_value_23',
            'ipv6_exclusive_routing': 'enable',
            'ipv6_service_restriction': 'enable',
            'ipv6_split_tunneling': 'enable',
            'ipv6_tunnel_mode': 'enable',
            'ipv6_wins_server1': 'test_value_28',
            'ipv6_wins_server2': 'test_value_29',
            'keep_alive': 'enable',
            'limit_user_logins': 'enable',
            'mac_addr_action': 'allow',
            'mac_addr_check': 'enable',
            'macos_forticlient_download_url': 'test_value_34',
            'name': 'default_name_35',
            'os_check': 'enable',
            'redir_url': 'test_value_37',
            'save_password': 'enable',
            'service_restriction': 'enable',
            'skip_check_for_unsupported_browser': 'enable',
            'skip_check_for_unsupported_os': 'enable',
            'smb_ntlmv1_auth': 'enable',
            'smbv1': 'enable',
            'split_tunneling': 'enable',
            'theme': 'blue',
            'tunnel_mode': 'enable',
            'user_bookmark': 'enable',
            'user_group_bookmark': 'enable',
            'web_mode': 'enable',
            'windows_forticlient_download_url': 'test_value_50',
            'wins_server1': 'test_value_51',
            'wins_server2': 'test_value_52'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ssl_web_portal.fortios_vpn_ssl_web(input_data, fos_instance)

    expected_data = {
        'allow-user-access': 'web',
        'auto-connect': 'enable',
        'custom-lang': 'test_value_5',
        'customize-forticlient-download-url': 'enable',
        'display-bookmark': 'enable',
        'display-connection-tools': 'enable',
        'display-history': 'enable',
        'display-status': 'enable',
        'dns-server1': 'test_value_11',
        'dns-server2': 'test_value_12',
        'dns-suffix': 'test_value_13',
        'exclusive-routing': 'enable',
        'forticlient-download': 'enable',
        'forticlient-download-method': 'direct',
        'heading': 'test_value_17',
        'hide-sso-credential': 'enable',
        'host-check': 'none',
        'host-check-interval': '20',
        'ip-mode': 'range',
        'ipv6-dns-server1': 'test_value_22',
        'ipv6-dns-server2': 'test_value_23',
        'ipv6-exclusive-routing': 'enable',
        'ipv6-service-restriction': 'enable',
        'ipv6-split-tunneling': 'enable',
        'ipv6-tunnel-mode': 'enable',
        'ipv6-wins-server1': 'test_value_28',
        'ipv6-wins-server2': 'test_value_29',
        'keep-alive': 'enable',
        'limit-user-logins': 'enable',
        'mac-addr-action': 'allow',
        'mac-addr-check': 'enable',
        'macos-forticlient-download-url': 'test_value_34',
        'name': 'default_name_35',
                'os-check': 'enable',
                'redir-url': 'test_value_37',
                'save-password': 'enable',
                'service-restriction': 'enable',
                'skip-check-for-unsupported-browser': 'enable',
                'skip-check-for-unsupported-os': 'enable',
                'smb-ntlmv1-auth': 'enable',
                'smbv1': 'enable',
                'split-tunneling': 'enable',
                'theme': 'blue',
                'tunnel-mode': 'enable',
                'user-bookmark': 'enable',
                'user-group-bookmark': 'enable',
                'web-mode': 'enable',
                'windows-forticlient-download-url': 'test_value_50',
                'wins-server1': 'test_value_51',
                'wins-server2': 'test_value_52'
    }

    set_method_mock.assert_called_with('vpn.ssl.web', 'portal', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_vpn_ssl_web_portal_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'vpn_ssl_web_portal': {
            'allow_user_access': 'web',
            'auto_connect': 'enable',
            'custom_lang': 'test_value_5',
            'customize_forticlient_download_url': 'enable',
            'display_bookmark': 'enable',
            'display_connection_tools': 'enable',
            'display_history': 'enable',
            'display_status': 'enable',
            'dns_server1': 'test_value_11',
            'dns_server2': 'test_value_12',
            'dns_suffix': 'test_value_13',
            'exclusive_routing': 'enable',
            'forticlient_download': 'enable',
            'forticlient_download_method': 'direct',
            'heading': 'test_value_17',
            'hide_sso_credential': 'enable',
            'host_check': 'none',
            'host_check_interval': '20',
            'ip_mode': 'range',
            'ipv6_dns_server1': 'test_value_22',
            'ipv6_dns_server2': 'test_value_23',
            'ipv6_exclusive_routing': 'enable',
            'ipv6_service_restriction': 'enable',
            'ipv6_split_tunneling': 'enable',
            'ipv6_tunnel_mode': 'enable',
            'ipv6_wins_server1': 'test_value_28',
            'ipv6_wins_server2': 'test_value_29',
            'keep_alive': 'enable',
            'limit_user_logins': 'enable',
            'mac_addr_action': 'allow',
            'mac_addr_check': 'enable',
            'macos_forticlient_download_url': 'test_value_34',
            'name': 'default_name_35',
            'os_check': 'enable',
            'redir_url': 'test_value_37',
            'save_password': 'enable',
            'service_restriction': 'enable',
            'skip_check_for_unsupported_browser': 'enable',
            'skip_check_for_unsupported_os': 'enable',
            'smb_ntlmv1_auth': 'enable',
            'smbv1': 'enable',
            'split_tunneling': 'enable',
            'theme': 'blue',
            'tunnel_mode': 'enable',
            'user_bookmark': 'enable',
            'user_group_bookmark': 'enable',
            'web_mode': 'enable',
            'windows_forticlient_download_url': 'test_value_50',
            'wins_server1': 'test_value_51',
            'wins_server2': 'test_value_52'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ssl_web_portal.fortios_vpn_ssl_web(input_data, fos_instance)

    delete_method_mock.assert_called_with('vpn.ssl.web', 'portal', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_vpn_ssl_web_portal_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'vpn_ssl_web_portal': {
            'allow_user_access': 'web',
            'auto_connect': 'enable',
            'custom_lang': 'test_value_5',
            'customize_forticlient_download_url': 'enable',
            'display_bookmark': 'enable',
            'display_connection_tools': 'enable',
            'display_history': 'enable',
            'display_status': 'enable',
            'dns_server1': 'test_value_11',
            'dns_server2': 'test_value_12',
            'dns_suffix': 'test_value_13',
            'exclusive_routing': 'enable',
            'forticlient_download': 'enable',
            'forticlient_download_method': 'direct',
            'heading': 'test_value_17',
            'hide_sso_credential': 'enable',
            'host_check': 'none',
            'host_check_interval': '20',
            'ip_mode': 'range',
            'ipv6_dns_server1': 'test_value_22',
            'ipv6_dns_server2': 'test_value_23',
            'ipv6_exclusive_routing': 'enable',
            'ipv6_service_restriction': 'enable',
            'ipv6_split_tunneling': 'enable',
            'ipv6_tunnel_mode': 'enable',
            'ipv6_wins_server1': 'test_value_28',
            'ipv6_wins_server2': 'test_value_29',
            'keep_alive': 'enable',
            'limit_user_logins': 'enable',
            'mac_addr_action': 'allow',
            'mac_addr_check': 'enable',
            'macos_forticlient_download_url': 'test_value_34',
            'name': 'default_name_35',
            'os_check': 'enable',
            'redir_url': 'test_value_37',
            'save_password': 'enable',
            'service_restriction': 'enable',
            'skip_check_for_unsupported_browser': 'enable',
            'skip_check_for_unsupported_os': 'enable',
            'smb_ntlmv1_auth': 'enable',
            'smbv1': 'enable',
            'split_tunneling': 'enable',
            'theme': 'blue',
            'tunnel_mode': 'enable',
            'user_bookmark': 'enable',
            'user_group_bookmark': 'enable',
            'web_mode': 'enable',
            'windows_forticlient_download_url': 'test_value_50',
            'wins_server1': 'test_value_51',
            'wins_server2': 'test_value_52'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ssl_web_portal.fortios_vpn_ssl_web(input_data, fos_instance)

    delete_method_mock.assert_called_with('vpn.ssl.web', 'portal', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_vpn_ssl_web_portal_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ssl_web_portal': {
            'allow_user_access': 'web',
            'auto_connect': 'enable',
            'custom_lang': 'test_value_5',
            'customize_forticlient_download_url': 'enable',
            'display_bookmark': 'enable',
            'display_connection_tools': 'enable',
            'display_history': 'enable',
            'display_status': 'enable',
            'dns_server1': 'test_value_11',
            'dns_server2': 'test_value_12',
            'dns_suffix': 'test_value_13',
            'exclusive_routing': 'enable',
            'forticlient_download': 'enable',
            'forticlient_download_method': 'direct',
            'heading': 'test_value_17',
            'hide_sso_credential': 'enable',
            'host_check': 'none',
            'host_check_interval': '20',
            'ip_mode': 'range',
            'ipv6_dns_server1': 'test_value_22',
            'ipv6_dns_server2': 'test_value_23',
            'ipv6_exclusive_routing': 'enable',
            'ipv6_service_restriction': 'enable',
            'ipv6_split_tunneling': 'enable',
            'ipv6_tunnel_mode': 'enable',
            'ipv6_wins_server1': 'test_value_28',
            'ipv6_wins_server2': 'test_value_29',
            'keep_alive': 'enable',
            'limit_user_logins': 'enable',
            'mac_addr_action': 'allow',
            'mac_addr_check': 'enable',
            'macos_forticlient_download_url': 'test_value_34',
            'name': 'default_name_35',
            'os_check': 'enable',
            'redir_url': 'test_value_37',
            'save_password': 'enable',
            'service_restriction': 'enable',
            'skip_check_for_unsupported_browser': 'enable',
            'skip_check_for_unsupported_os': 'enable',
            'smb_ntlmv1_auth': 'enable',
            'smbv1': 'enable',
            'split_tunneling': 'enable',
            'theme': 'blue',
            'tunnel_mode': 'enable',
            'user_bookmark': 'enable',
            'user_group_bookmark': 'enable',
            'web_mode': 'enable',
            'windows_forticlient_download_url': 'test_value_50',
            'wins_server1': 'test_value_51',
            'wins_server2': 'test_value_52'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ssl_web_portal.fortios_vpn_ssl_web(input_data, fos_instance)

    expected_data = {
        'allow-user-access': 'web',
        'auto-connect': 'enable',
        'custom-lang': 'test_value_5',
        'customize-forticlient-download-url': 'enable',
        'display-bookmark': 'enable',
        'display-connection-tools': 'enable',
        'display-history': 'enable',
        'display-status': 'enable',
        'dns-server1': 'test_value_11',
        'dns-server2': 'test_value_12',
        'dns-suffix': 'test_value_13',
        'exclusive-routing': 'enable',
        'forticlient-download': 'enable',
        'forticlient-download-method': 'direct',
        'heading': 'test_value_17',
        'hide-sso-credential': 'enable',
        'host-check': 'none',
        'host-check-interval': '20',
        'ip-mode': 'range',
        'ipv6-dns-server1': 'test_value_22',
        'ipv6-dns-server2': 'test_value_23',
        'ipv6-exclusive-routing': 'enable',
        'ipv6-service-restriction': 'enable',
        'ipv6-split-tunneling': 'enable',
        'ipv6-tunnel-mode': 'enable',
        'ipv6-wins-server1': 'test_value_28',
        'ipv6-wins-server2': 'test_value_29',
        'keep-alive': 'enable',
        'limit-user-logins': 'enable',
        'mac-addr-action': 'allow',
        'mac-addr-check': 'enable',
        'macos-forticlient-download-url': 'test_value_34',
        'name': 'default_name_35',
                'os-check': 'enable',
                'redir-url': 'test_value_37',
                'save-password': 'enable',
                'service-restriction': 'enable',
                'skip-check-for-unsupported-browser': 'enable',
                'skip-check-for-unsupported-os': 'enable',
                'smb-ntlmv1-auth': 'enable',
                'smbv1': 'enable',
                'split-tunneling': 'enable',
                'theme': 'blue',
                'tunnel-mode': 'enable',
                'user-bookmark': 'enable',
                'user-group-bookmark': 'enable',
                'web-mode': 'enable',
                'windows-forticlient-download-url': 'test_value_50',
                'wins-server1': 'test_value_51',
                'wins-server2': 'test_value_52'
    }

    set_method_mock.assert_called_with('vpn.ssl.web', 'portal', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_vpn_ssl_web_portal_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'vpn_ssl_web_portal': {
            'random_attribute_not_valid': 'tag',
            'allow_user_access': 'web',
            'auto_connect': 'enable',
            'custom_lang': 'test_value_5',
            'customize_forticlient_download_url': 'enable',
            'display_bookmark': 'enable',
            'display_connection_tools': 'enable',
            'display_history': 'enable',
            'display_status': 'enable',
            'dns_server1': 'test_value_11',
            'dns_server2': 'test_value_12',
            'dns_suffix': 'test_value_13',
            'exclusive_routing': 'enable',
            'forticlient_download': 'enable',
            'forticlient_download_method': 'direct',
            'heading': 'test_value_17',
            'hide_sso_credential': 'enable',
            'host_check': 'none',
            'host_check_interval': '20',
            'ip_mode': 'range',
            'ipv6_dns_server1': 'test_value_22',
            'ipv6_dns_server2': 'test_value_23',
            'ipv6_exclusive_routing': 'enable',
            'ipv6_service_restriction': 'enable',
            'ipv6_split_tunneling': 'enable',
            'ipv6_tunnel_mode': 'enable',
            'ipv6_wins_server1': 'test_value_28',
            'ipv6_wins_server2': 'test_value_29',
            'keep_alive': 'enable',
            'limit_user_logins': 'enable',
            'mac_addr_action': 'allow',
            'mac_addr_check': 'enable',
            'macos_forticlient_download_url': 'test_value_34',
            'name': 'default_name_35',
            'os_check': 'enable',
            'redir_url': 'test_value_37',
            'save_password': 'enable',
            'service_restriction': 'enable',
            'skip_check_for_unsupported_browser': 'enable',
            'skip_check_for_unsupported_os': 'enable',
            'smb_ntlmv1_auth': 'enable',
            'smbv1': 'enable',
            'split_tunneling': 'enable',
            'theme': 'blue',
            'tunnel_mode': 'enable',
            'user_bookmark': 'enable',
            'user_group_bookmark': 'enable',
            'web_mode': 'enable',
            'windows_forticlient_download_url': 'test_value_50',
            'wins_server1': 'test_value_51',
            'wins_server2': 'test_value_52'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_vpn_ssl_web_portal.fortios_vpn_ssl_web(input_data, fos_instance)

    expected_data = {
        'allow-user-access': 'web',
        'auto-connect': 'enable',
        'custom-lang': 'test_value_5',
        'customize-forticlient-download-url': 'enable',
        'display-bookmark': 'enable',
        'display-connection-tools': 'enable',
        'display-history': 'enable',
        'display-status': 'enable',
        'dns-server1': 'test_value_11',
        'dns-server2': 'test_value_12',
        'dns-suffix': 'test_value_13',
        'exclusive-routing': 'enable',
        'forticlient-download': 'enable',
        'forticlient-download-method': 'direct',
        'heading': 'test_value_17',
        'hide-sso-credential': 'enable',
        'host-check': 'none',
        'host-check-interval': '20',
        'ip-mode': 'range',
        'ipv6-dns-server1': 'test_value_22',
        'ipv6-dns-server2': 'test_value_23',
        'ipv6-exclusive-routing': 'enable',
        'ipv6-service-restriction': 'enable',
        'ipv6-split-tunneling': 'enable',
        'ipv6-tunnel-mode': 'enable',
        'ipv6-wins-server1': 'test_value_28',
        'ipv6-wins-server2': 'test_value_29',
        'keep-alive': 'enable',
        'limit-user-logins': 'enable',
        'mac-addr-action': 'allow',
        'mac-addr-check': 'enable',
        'macos-forticlient-download-url': 'test_value_34',
        'name': 'default_name_35',
                'os-check': 'enable',
                'redir-url': 'test_value_37',
                'save-password': 'enable',
                'service-restriction': 'enable',
                'skip-check-for-unsupported-browser': 'enable',
                'skip-check-for-unsupported-os': 'enable',
                'smb-ntlmv1-auth': 'enable',
                'smbv1': 'enable',
                'split-tunneling': 'enable',
                'theme': 'blue',
                'tunnel-mode': 'enable',
                'user-bookmark': 'enable',
                'user-group-bookmark': 'enable',
                'web-mode': 'enable',
                'windows-forticlient-download-url': 'test_value_50',
                'wins-server1': 'test_value_51',
                'wins-server2': 'test_value_52'
    }

    set_method_mock.assert_called_with('vpn.ssl.web', 'portal', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
