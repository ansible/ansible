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
    from ansible.modules.network.fortios import fortios_report_style
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_report_style.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_report_style_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'report_style': {
            'align': 'left',
            'bg_color': 'test_value_4',
            'border_bottom': 'test_value_5',
            'border_left': 'test_value_6',
            'border_right': 'test_value_7',
            'border_top': 'test_value_8',
            'column_gap': 'test_value_9',
            'column_span': 'none',
            'fg_color': 'test_value_11',
            'font_family': 'Verdana',
            'font_size': 'test_value_13',
            'font_style': 'normal',
            'font_weight': 'normal',
            'height': 'test_value_16',
            'line_height': 'test_value_17',
            'margin_bottom': 'test_value_18',
            'margin_left': 'test_value_19',
            'margin_right': 'test_value_20',
            'margin_top': 'test_value_21',
            'name': 'default_name_22',
            'options': 'font',
            'padding_bottom': 'test_value_24',
            'padding_left': 'test_value_25',
            'padding_right': 'test_value_26',
            'padding_top': 'test_value_27',
            'width': 'test_value_28'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_style.fortios_report(input_data, fos_instance)

    expected_data = {
        'align': 'left',
        'bg-color': 'test_value_4',
        'border-bottom': 'test_value_5',
        'border-left': 'test_value_6',
        'border-right': 'test_value_7',
        'border-top': 'test_value_8',
        'column-gap': 'test_value_9',
        'column-span': 'none',
        'fg-color': 'test_value_11',
        'font-family': 'Verdana',
        'font-size': 'test_value_13',
        'font-style': 'normal',
        'font-weight': 'normal',
        'height': 'test_value_16',
        'line-height': 'test_value_17',
        'margin-bottom': 'test_value_18',
        'margin-left': 'test_value_19',
        'margin-right': 'test_value_20',
        'margin-top': 'test_value_21',
        'name': 'default_name_22',
                'options': 'font',
                'padding-bottom': 'test_value_24',
                'padding-left': 'test_value_25',
                'padding-right': 'test_value_26',
                'padding-top': 'test_value_27',
                'width': 'test_value_28'
    }

    set_method_mock.assert_called_with('report', 'style', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_report_style_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'report_style': {
            'align': 'left',
            'bg_color': 'test_value_4',
            'border_bottom': 'test_value_5',
            'border_left': 'test_value_6',
            'border_right': 'test_value_7',
            'border_top': 'test_value_8',
            'column_gap': 'test_value_9',
            'column_span': 'none',
            'fg_color': 'test_value_11',
            'font_family': 'Verdana',
            'font_size': 'test_value_13',
            'font_style': 'normal',
            'font_weight': 'normal',
            'height': 'test_value_16',
            'line_height': 'test_value_17',
            'margin_bottom': 'test_value_18',
            'margin_left': 'test_value_19',
            'margin_right': 'test_value_20',
            'margin_top': 'test_value_21',
            'name': 'default_name_22',
            'options': 'font',
            'padding_bottom': 'test_value_24',
            'padding_left': 'test_value_25',
            'padding_right': 'test_value_26',
            'padding_top': 'test_value_27',
            'width': 'test_value_28'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_style.fortios_report(input_data, fos_instance)

    expected_data = {
        'align': 'left',
        'bg-color': 'test_value_4',
        'border-bottom': 'test_value_5',
        'border-left': 'test_value_6',
        'border-right': 'test_value_7',
        'border-top': 'test_value_8',
        'column-gap': 'test_value_9',
        'column-span': 'none',
        'fg-color': 'test_value_11',
        'font-family': 'Verdana',
        'font-size': 'test_value_13',
        'font-style': 'normal',
        'font-weight': 'normal',
        'height': 'test_value_16',
        'line-height': 'test_value_17',
        'margin-bottom': 'test_value_18',
        'margin-left': 'test_value_19',
        'margin-right': 'test_value_20',
        'margin-top': 'test_value_21',
        'name': 'default_name_22',
                'options': 'font',
                'padding-bottom': 'test_value_24',
                'padding-left': 'test_value_25',
                'padding-right': 'test_value_26',
                'padding-top': 'test_value_27',
                'width': 'test_value_28'
    }

    set_method_mock.assert_called_with('report', 'style', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_report_style_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'report_style': {
            'align': 'left',
            'bg_color': 'test_value_4',
            'border_bottom': 'test_value_5',
            'border_left': 'test_value_6',
            'border_right': 'test_value_7',
            'border_top': 'test_value_8',
            'column_gap': 'test_value_9',
            'column_span': 'none',
            'fg_color': 'test_value_11',
            'font_family': 'Verdana',
            'font_size': 'test_value_13',
            'font_style': 'normal',
            'font_weight': 'normal',
            'height': 'test_value_16',
            'line_height': 'test_value_17',
            'margin_bottom': 'test_value_18',
            'margin_left': 'test_value_19',
            'margin_right': 'test_value_20',
            'margin_top': 'test_value_21',
            'name': 'default_name_22',
            'options': 'font',
            'padding_bottom': 'test_value_24',
            'padding_left': 'test_value_25',
            'padding_right': 'test_value_26',
            'padding_top': 'test_value_27',
            'width': 'test_value_28'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_style.fortios_report(input_data, fos_instance)

    delete_method_mock.assert_called_with('report', 'style', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_report_style_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'report_style': {
            'align': 'left',
            'bg_color': 'test_value_4',
            'border_bottom': 'test_value_5',
            'border_left': 'test_value_6',
            'border_right': 'test_value_7',
            'border_top': 'test_value_8',
            'column_gap': 'test_value_9',
            'column_span': 'none',
            'fg_color': 'test_value_11',
            'font_family': 'Verdana',
            'font_size': 'test_value_13',
            'font_style': 'normal',
            'font_weight': 'normal',
            'height': 'test_value_16',
            'line_height': 'test_value_17',
            'margin_bottom': 'test_value_18',
            'margin_left': 'test_value_19',
            'margin_right': 'test_value_20',
            'margin_top': 'test_value_21',
            'name': 'default_name_22',
            'options': 'font',
            'padding_bottom': 'test_value_24',
            'padding_left': 'test_value_25',
            'padding_right': 'test_value_26',
            'padding_top': 'test_value_27',
            'width': 'test_value_28'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_style.fortios_report(input_data, fos_instance)

    delete_method_mock.assert_called_with('report', 'style', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_report_style_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'report_style': {
            'align': 'left',
            'bg_color': 'test_value_4',
            'border_bottom': 'test_value_5',
            'border_left': 'test_value_6',
            'border_right': 'test_value_7',
            'border_top': 'test_value_8',
            'column_gap': 'test_value_9',
            'column_span': 'none',
            'fg_color': 'test_value_11',
            'font_family': 'Verdana',
            'font_size': 'test_value_13',
            'font_style': 'normal',
            'font_weight': 'normal',
            'height': 'test_value_16',
            'line_height': 'test_value_17',
            'margin_bottom': 'test_value_18',
            'margin_left': 'test_value_19',
            'margin_right': 'test_value_20',
            'margin_top': 'test_value_21',
            'name': 'default_name_22',
            'options': 'font',
            'padding_bottom': 'test_value_24',
            'padding_left': 'test_value_25',
            'padding_right': 'test_value_26',
            'padding_top': 'test_value_27',
            'width': 'test_value_28'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_style.fortios_report(input_data, fos_instance)

    expected_data = {
        'align': 'left',
        'bg-color': 'test_value_4',
        'border-bottom': 'test_value_5',
        'border-left': 'test_value_6',
        'border-right': 'test_value_7',
        'border-top': 'test_value_8',
        'column-gap': 'test_value_9',
        'column-span': 'none',
        'fg-color': 'test_value_11',
        'font-family': 'Verdana',
        'font-size': 'test_value_13',
        'font-style': 'normal',
        'font-weight': 'normal',
        'height': 'test_value_16',
        'line-height': 'test_value_17',
        'margin-bottom': 'test_value_18',
        'margin-left': 'test_value_19',
        'margin-right': 'test_value_20',
        'margin-top': 'test_value_21',
        'name': 'default_name_22',
                'options': 'font',
                'padding-bottom': 'test_value_24',
                'padding-left': 'test_value_25',
                'padding-right': 'test_value_26',
                'padding-top': 'test_value_27',
                'width': 'test_value_28'
    }

    set_method_mock.assert_called_with('report', 'style', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_report_style_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'report_style': {
            'random_attribute_not_valid': 'tag',
            'align': 'left',
            'bg_color': 'test_value_4',
            'border_bottom': 'test_value_5',
            'border_left': 'test_value_6',
            'border_right': 'test_value_7',
            'border_top': 'test_value_8',
            'column_gap': 'test_value_9',
            'column_span': 'none',
            'fg_color': 'test_value_11',
            'font_family': 'Verdana',
            'font_size': 'test_value_13',
            'font_style': 'normal',
            'font_weight': 'normal',
            'height': 'test_value_16',
            'line_height': 'test_value_17',
            'margin_bottom': 'test_value_18',
            'margin_left': 'test_value_19',
            'margin_right': 'test_value_20',
            'margin_top': 'test_value_21',
            'name': 'default_name_22',
            'options': 'font',
            'padding_bottom': 'test_value_24',
            'padding_left': 'test_value_25',
            'padding_right': 'test_value_26',
            'padding_top': 'test_value_27',
            'width': 'test_value_28'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_style.fortios_report(input_data, fos_instance)

    expected_data = {
        'align': 'left',
        'bg-color': 'test_value_4',
        'border-bottom': 'test_value_5',
        'border-left': 'test_value_6',
        'border-right': 'test_value_7',
        'border-top': 'test_value_8',
        'column-gap': 'test_value_9',
        'column-span': 'none',
        'fg-color': 'test_value_11',
        'font-family': 'Verdana',
        'font-size': 'test_value_13',
        'font-style': 'normal',
        'font-weight': 'normal',
        'height': 'test_value_16',
        'line-height': 'test_value_17',
        'margin-bottom': 'test_value_18',
        'margin-left': 'test_value_19',
        'margin-right': 'test_value_20',
        'margin-top': 'test_value_21',
        'name': 'default_name_22',
                'options': 'font',
                'padding-bottom': 'test_value_24',
                'padding-left': 'test_value_25',
                'padding-right': 'test_value_26',
                'padding-top': 'test_value_27',
                'width': 'test_value_28'
    }

    set_method_mock.assert_called_with('report', 'style', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
