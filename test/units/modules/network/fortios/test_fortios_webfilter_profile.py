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
    from ansible.modules.network.fortios import fortios_webfilter_profile
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_webfilter_profile.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_webfilter_profile_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'webfilter_profile': {
            'comment': 'Optional comments.',
            'extended_log': 'enable',
            'https_replacemsg': 'enable',
            'inspection_mode': 'proxy',
            'log_all_url': 'enable',
            'name': 'default_name_8',
            'options': 'activexfilter',
            'ovrd_perm': 'bannedword-override',
            'post_action': 'normal',
            'replacemsg_group': 'test_value_12',
            'web_content_log': 'enable',
            'web_extended_all_action_log': 'enable',
            'web_filter_activex_log': 'enable',
            'web_filter_applet_log': 'enable',
            'web_filter_command_block_log': 'enable',
            'web_filter_cookie_log': 'enable',
            'web_filter_cookie_removal_log': 'enable',
            'web_filter_js_log': 'enable',
            'web_filter_jscript_log': 'enable',
            'web_filter_referer_log': 'enable',
            'web_filter_unknown_log': 'enable',
            'web_filter_vbs_log': 'enable',
            'web_ftgd_err_log': 'enable',
            'web_ftgd_quota_usage': 'enable',
            'web_invalid_domain_log': 'enable',
            'web_url_log': 'enable',
            'wisp': 'enable',
            'wisp_algorithm': 'primary-secondary',
            'youtube_channel_status': 'disable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_webfilter_profile.fortios_webfilter(input_data, fos_instance)

    expected_data = {
        'comment': 'Optional comments.',
        'extended-log': 'enable',
        'https-replacemsg': 'enable',
        'inspection-mode': 'proxy',
        'log-all-url': 'enable',
        'name': 'default_name_8',
                'options': 'activexfilter',
                'ovrd-perm': 'bannedword-override',
                'post-action': 'normal',
                'replacemsg-group': 'test_value_12',
                'web-content-log': 'enable',
                'web-extended-all-action-log': 'enable',
                'web-filter-activex-log': 'enable',
                'web-filter-applet-log': 'enable',
                'web-filter-command-block-log': 'enable',
                'web-filter-cookie-log': 'enable',
                'web-filter-cookie-removal-log': 'enable',
                'web-filter-js-log': 'enable',
                'web-filter-jscript-log': 'enable',
                'web-filter-referer-log': 'enable',
                'web-filter-unknown-log': 'enable',
                'web-filter-vbs-log': 'enable',
                'web-ftgd-err-log': 'enable',
                'web-ftgd-quota-usage': 'enable',
                'web-invalid-domain-log': 'enable',
                'web-url-log': 'enable',
                'wisp': 'enable',
                'wisp-algorithm': 'primary-secondary',
                'youtube-channel-status': 'disable'
    }

    set_method_mock.assert_called_with('webfilter', 'profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_webfilter_profile_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'webfilter_profile': {
            'comment': 'Optional comments.',
            'extended_log': 'enable',
            'https_replacemsg': 'enable',
            'inspection_mode': 'proxy',
            'log_all_url': 'enable',
            'name': 'default_name_8',
            'options': 'activexfilter',
            'ovrd_perm': 'bannedword-override',
            'post_action': 'normal',
            'replacemsg_group': 'test_value_12',
            'web_content_log': 'enable',
            'web_extended_all_action_log': 'enable',
            'web_filter_activex_log': 'enable',
            'web_filter_applet_log': 'enable',
            'web_filter_command_block_log': 'enable',
            'web_filter_cookie_log': 'enable',
            'web_filter_cookie_removal_log': 'enable',
            'web_filter_js_log': 'enable',
            'web_filter_jscript_log': 'enable',
            'web_filter_referer_log': 'enable',
            'web_filter_unknown_log': 'enable',
            'web_filter_vbs_log': 'enable',
            'web_ftgd_err_log': 'enable',
            'web_ftgd_quota_usage': 'enable',
            'web_invalid_domain_log': 'enable',
            'web_url_log': 'enable',
            'wisp': 'enable',
            'wisp_algorithm': 'primary-secondary',
            'youtube_channel_status': 'disable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_webfilter_profile.fortios_webfilter(input_data, fos_instance)

    expected_data = {
        'comment': 'Optional comments.',
        'extended-log': 'enable',
        'https-replacemsg': 'enable',
        'inspection-mode': 'proxy',
        'log-all-url': 'enable',
        'name': 'default_name_8',
                'options': 'activexfilter',
                'ovrd-perm': 'bannedword-override',
                'post-action': 'normal',
                'replacemsg-group': 'test_value_12',
                'web-content-log': 'enable',
                'web-extended-all-action-log': 'enable',
                'web-filter-activex-log': 'enable',
                'web-filter-applet-log': 'enable',
                'web-filter-command-block-log': 'enable',
                'web-filter-cookie-log': 'enable',
                'web-filter-cookie-removal-log': 'enable',
                'web-filter-js-log': 'enable',
                'web-filter-jscript-log': 'enable',
                'web-filter-referer-log': 'enable',
                'web-filter-unknown-log': 'enable',
                'web-filter-vbs-log': 'enable',
                'web-ftgd-err-log': 'enable',
                'web-ftgd-quota-usage': 'enable',
                'web-invalid-domain-log': 'enable',
                'web-url-log': 'enable',
                'wisp': 'enable',
                'wisp-algorithm': 'primary-secondary',
                'youtube-channel-status': 'disable'
    }

    set_method_mock.assert_called_with('webfilter', 'profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_webfilter_profile_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'webfilter_profile': {
            'comment': 'Optional comments.',
            'extended_log': 'enable',
            'https_replacemsg': 'enable',
            'inspection_mode': 'proxy',
            'log_all_url': 'enable',
            'name': 'default_name_8',
            'options': 'activexfilter',
            'ovrd_perm': 'bannedword-override',
            'post_action': 'normal',
            'replacemsg_group': 'test_value_12',
            'web_content_log': 'enable',
            'web_extended_all_action_log': 'enable',
            'web_filter_activex_log': 'enable',
            'web_filter_applet_log': 'enable',
            'web_filter_command_block_log': 'enable',
            'web_filter_cookie_log': 'enable',
            'web_filter_cookie_removal_log': 'enable',
            'web_filter_js_log': 'enable',
            'web_filter_jscript_log': 'enable',
            'web_filter_referer_log': 'enable',
            'web_filter_unknown_log': 'enable',
            'web_filter_vbs_log': 'enable',
            'web_ftgd_err_log': 'enable',
            'web_ftgd_quota_usage': 'enable',
            'web_invalid_domain_log': 'enable',
            'web_url_log': 'enable',
            'wisp': 'enable',
            'wisp_algorithm': 'primary-secondary',
            'youtube_channel_status': 'disable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_webfilter_profile.fortios_webfilter(input_data, fos_instance)

    delete_method_mock.assert_called_with('webfilter', 'profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_webfilter_profile_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'webfilter_profile': {
            'comment': 'Optional comments.',
            'extended_log': 'enable',
            'https_replacemsg': 'enable',
            'inspection_mode': 'proxy',
            'log_all_url': 'enable',
            'name': 'default_name_8',
            'options': 'activexfilter',
            'ovrd_perm': 'bannedword-override',
            'post_action': 'normal',
            'replacemsg_group': 'test_value_12',
            'web_content_log': 'enable',
            'web_extended_all_action_log': 'enable',
            'web_filter_activex_log': 'enable',
            'web_filter_applet_log': 'enable',
            'web_filter_command_block_log': 'enable',
            'web_filter_cookie_log': 'enable',
            'web_filter_cookie_removal_log': 'enable',
            'web_filter_js_log': 'enable',
            'web_filter_jscript_log': 'enable',
            'web_filter_referer_log': 'enable',
            'web_filter_unknown_log': 'enable',
            'web_filter_vbs_log': 'enable',
            'web_ftgd_err_log': 'enable',
            'web_ftgd_quota_usage': 'enable',
            'web_invalid_domain_log': 'enable',
            'web_url_log': 'enable',
            'wisp': 'enable',
            'wisp_algorithm': 'primary-secondary',
            'youtube_channel_status': 'disable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_webfilter_profile.fortios_webfilter(input_data, fos_instance)

    delete_method_mock.assert_called_with('webfilter', 'profile', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_webfilter_profile_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'webfilter_profile': {
            'comment': 'Optional comments.',
            'extended_log': 'enable',
            'https_replacemsg': 'enable',
            'inspection_mode': 'proxy',
            'log_all_url': 'enable',
            'name': 'default_name_8',
            'options': 'activexfilter',
            'ovrd_perm': 'bannedword-override',
            'post_action': 'normal',
            'replacemsg_group': 'test_value_12',
            'web_content_log': 'enable',
            'web_extended_all_action_log': 'enable',
            'web_filter_activex_log': 'enable',
            'web_filter_applet_log': 'enable',
            'web_filter_command_block_log': 'enable',
            'web_filter_cookie_log': 'enable',
            'web_filter_cookie_removal_log': 'enable',
            'web_filter_js_log': 'enable',
            'web_filter_jscript_log': 'enable',
            'web_filter_referer_log': 'enable',
            'web_filter_unknown_log': 'enable',
            'web_filter_vbs_log': 'enable',
            'web_ftgd_err_log': 'enable',
            'web_ftgd_quota_usage': 'enable',
            'web_invalid_domain_log': 'enable',
            'web_url_log': 'enable',
            'wisp': 'enable',
            'wisp_algorithm': 'primary-secondary',
            'youtube_channel_status': 'disable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_webfilter_profile.fortios_webfilter(input_data, fos_instance)

    expected_data = {
        'comment': 'Optional comments.',
        'extended-log': 'enable',
        'https-replacemsg': 'enable',
        'inspection-mode': 'proxy',
        'log-all-url': 'enable',
        'name': 'default_name_8',
                'options': 'activexfilter',
                'ovrd-perm': 'bannedword-override',
                'post-action': 'normal',
                'replacemsg-group': 'test_value_12',
                'web-content-log': 'enable',
                'web-extended-all-action-log': 'enable',
                'web-filter-activex-log': 'enable',
                'web-filter-applet-log': 'enable',
                'web-filter-command-block-log': 'enable',
                'web-filter-cookie-log': 'enable',
                'web-filter-cookie-removal-log': 'enable',
                'web-filter-js-log': 'enable',
                'web-filter-jscript-log': 'enable',
                'web-filter-referer-log': 'enable',
                'web-filter-unknown-log': 'enable',
                'web-filter-vbs-log': 'enable',
                'web-ftgd-err-log': 'enable',
                'web-ftgd-quota-usage': 'enable',
                'web-invalid-domain-log': 'enable',
                'web-url-log': 'enable',
                'wisp': 'enable',
                'wisp-algorithm': 'primary-secondary',
                'youtube-channel-status': 'disable'
    }

    set_method_mock.assert_called_with('webfilter', 'profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_webfilter_profile_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'webfilter_profile': {
            'random_attribute_not_valid': 'tag',
            'comment': 'Optional comments.',
            'extended_log': 'enable',
            'https_replacemsg': 'enable',
            'inspection_mode': 'proxy',
            'log_all_url': 'enable',
            'name': 'default_name_8',
            'options': 'activexfilter',
            'ovrd_perm': 'bannedword-override',
            'post_action': 'normal',
            'replacemsg_group': 'test_value_12',
            'web_content_log': 'enable',
            'web_extended_all_action_log': 'enable',
            'web_filter_activex_log': 'enable',
            'web_filter_applet_log': 'enable',
            'web_filter_command_block_log': 'enable',
            'web_filter_cookie_log': 'enable',
            'web_filter_cookie_removal_log': 'enable',
            'web_filter_js_log': 'enable',
            'web_filter_jscript_log': 'enable',
            'web_filter_referer_log': 'enable',
            'web_filter_unknown_log': 'enable',
            'web_filter_vbs_log': 'enable',
            'web_ftgd_err_log': 'enable',
            'web_ftgd_quota_usage': 'enable',
            'web_invalid_domain_log': 'enable',
            'web_url_log': 'enable',
            'wisp': 'enable',
            'wisp_algorithm': 'primary-secondary',
            'youtube_channel_status': 'disable'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_webfilter_profile.fortios_webfilter(input_data, fos_instance)

    expected_data = {
        'comment': 'Optional comments.',
        'extended-log': 'enable',
        'https-replacemsg': 'enable',
        'inspection-mode': 'proxy',
        'log-all-url': 'enable',
        'name': 'default_name_8',
                'options': 'activexfilter',
                'ovrd-perm': 'bannedword-override',
                'post-action': 'normal',
                'replacemsg-group': 'test_value_12',
                'web-content-log': 'enable',
                'web-extended-all-action-log': 'enable',
                'web-filter-activex-log': 'enable',
                'web-filter-applet-log': 'enable',
                'web-filter-command-block-log': 'enable',
                'web-filter-cookie-log': 'enable',
                'web-filter-cookie-removal-log': 'enable',
                'web-filter-js-log': 'enable',
                'web-filter-jscript-log': 'enable',
                'web-filter-referer-log': 'enable',
                'web-filter-unknown-log': 'enable',
                'web-filter-vbs-log': 'enable',
                'web-ftgd-err-log': 'enable',
                'web-ftgd-quota-usage': 'enable',
                'web-invalid-domain-log': 'enable',
                'web-url-log': 'enable',
                'wisp': 'enable',
                'wisp-algorithm': 'primary-secondary',
                'youtube-channel-status': 'disable'
    }

    set_method_mock.assert_called_with('webfilter', 'profile', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
