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
    from ansible.modules.network.fortios import fortios_report_theme
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_report_theme.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_report_theme_creation(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'report_theme': {
            'bullet_list_style': 'test_value_3',
            'column_count': '1',
            'default_html_style': 'test_value_5',
            'default_pdf_style': 'test_value_6',
            'graph_chart_style': 'test_value_7',
            'heading1_style': 'test_value_8',
            'heading2_style': 'test_value_9',
            'heading3_style': 'test_value_10',
            'heading4_style': 'test_value_11',
            'hline_style': 'test_value_12',
            'image_style': 'test_value_13',
            'name': 'default_name_14',
            'normal_text_style': 'test_value_15',
            'numbered_list_style': 'test_value_16',
            'page_footer_style': 'test_value_17',
            'page_header_style': 'test_value_18',
            'page_orient': 'portrait',
            'page_style': 'test_value_20',
            'report_subtitle_style': 'test_value_21',
            'report_title_style': 'test_value_22',
            'table_chart_caption_style': 'test_value_23',
            'table_chart_even_row_style': 'test_value_24',
            'table_chart_head_style': 'test_value_25',
            'table_chart_odd_row_style': 'test_value_26',
            'table_chart_style': 'test_value_27',
            'toc_heading1_style': 'test_value_28',
            'toc_heading2_style': 'test_value_29',
            'toc_heading3_style': 'test_value_30',
            'toc_heading4_style': 'test_value_31',
            'toc_title_style': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_theme.fortios_report(input_data, fos_instance)

    expected_data = {
        'bullet-list-style': 'test_value_3',
        'column-count': '1',
        'default-html-style': 'test_value_5',
        'default-pdf-style': 'test_value_6',
        'graph-chart-style': 'test_value_7',
        'heading1-style': 'test_value_8',
        'heading2-style': 'test_value_9',
        'heading3-style': 'test_value_10',
        'heading4-style': 'test_value_11',
        'hline-style': 'test_value_12',
        'image-style': 'test_value_13',
        'name': 'default_name_14',
                'normal-text-style': 'test_value_15',
                'numbered-list-style': 'test_value_16',
                'page-footer-style': 'test_value_17',
                'page-header-style': 'test_value_18',
                'page-orient': 'portrait',
                'page-style': 'test_value_20',
                'report-subtitle-style': 'test_value_21',
                'report-title-style': 'test_value_22',
                'table-chart-caption-style': 'test_value_23',
                'table-chart-even-row-style': 'test_value_24',
                'table-chart-head-style': 'test_value_25',
                'table-chart-odd-row-style': 'test_value_26',
                'table-chart-style': 'test_value_27',
                'toc-heading1-style': 'test_value_28',
                'toc-heading2-style': 'test_value_29',
                'toc-heading3-style': 'test_value_30',
                'toc-heading4-style': 'test_value_31',
                'toc-title-style': 'test_value_32'
    }

    set_method_mock.assert_called_with('report', 'theme', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_report_theme_creation_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'report_theme': {
            'bullet_list_style': 'test_value_3',
            'column_count': '1',
            'default_html_style': 'test_value_5',
            'default_pdf_style': 'test_value_6',
            'graph_chart_style': 'test_value_7',
            'heading1_style': 'test_value_8',
            'heading2_style': 'test_value_9',
            'heading3_style': 'test_value_10',
            'heading4_style': 'test_value_11',
            'hline_style': 'test_value_12',
            'image_style': 'test_value_13',
            'name': 'default_name_14',
            'normal_text_style': 'test_value_15',
            'numbered_list_style': 'test_value_16',
            'page_footer_style': 'test_value_17',
            'page_header_style': 'test_value_18',
            'page_orient': 'portrait',
            'page_style': 'test_value_20',
            'report_subtitle_style': 'test_value_21',
            'report_title_style': 'test_value_22',
            'table_chart_caption_style': 'test_value_23',
            'table_chart_even_row_style': 'test_value_24',
            'table_chart_head_style': 'test_value_25',
            'table_chart_odd_row_style': 'test_value_26',
            'table_chart_style': 'test_value_27',
            'toc_heading1_style': 'test_value_28',
            'toc_heading2_style': 'test_value_29',
            'toc_heading3_style': 'test_value_30',
            'toc_heading4_style': 'test_value_31',
            'toc_title_style': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_theme.fortios_report(input_data, fos_instance)

    expected_data = {
        'bullet-list-style': 'test_value_3',
        'column-count': '1',
        'default-html-style': 'test_value_5',
        'default-pdf-style': 'test_value_6',
        'graph-chart-style': 'test_value_7',
        'heading1-style': 'test_value_8',
        'heading2-style': 'test_value_9',
        'heading3-style': 'test_value_10',
        'heading4-style': 'test_value_11',
        'hline-style': 'test_value_12',
        'image-style': 'test_value_13',
        'name': 'default_name_14',
                'normal-text-style': 'test_value_15',
                'numbered-list-style': 'test_value_16',
                'page-footer-style': 'test_value_17',
                'page-header-style': 'test_value_18',
                'page-orient': 'portrait',
                'page-style': 'test_value_20',
                'report-subtitle-style': 'test_value_21',
                'report-title-style': 'test_value_22',
                'table-chart-caption-style': 'test_value_23',
                'table-chart-even-row-style': 'test_value_24',
                'table-chart-head-style': 'test_value_25',
                'table-chart-odd-row-style': 'test_value_26',
                'table-chart-style': 'test_value_27',
                'toc-heading1-style': 'test_value_28',
                'toc-heading2-style': 'test_value_29',
                'toc-heading3-style': 'test_value_30',
                'toc-heading4-style': 'test_value_31',
                'toc-title-style': 'test_value_32'
    }

    set_method_mock.assert_called_with('report', 'theme', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_report_theme_removal(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'report_theme': {
            'bullet_list_style': 'test_value_3',
            'column_count': '1',
            'default_html_style': 'test_value_5',
            'default_pdf_style': 'test_value_6',
            'graph_chart_style': 'test_value_7',
            'heading1_style': 'test_value_8',
            'heading2_style': 'test_value_9',
            'heading3_style': 'test_value_10',
            'heading4_style': 'test_value_11',
            'hline_style': 'test_value_12',
            'image_style': 'test_value_13',
            'name': 'default_name_14',
            'normal_text_style': 'test_value_15',
            'numbered_list_style': 'test_value_16',
            'page_footer_style': 'test_value_17',
            'page_header_style': 'test_value_18',
            'page_orient': 'portrait',
            'page_style': 'test_value_20',
            'report_subtitle_style': 'test_value_21',
            'report_title_style': 'test_value_22',
            'table_chart_caption_style': 'test_value_23',
            'table_chart_even_row_style': 'test_value_24',
            'table_chart_head_style': 'test_value_25',
            'table_chart_odd_row_style': 'test_value_26',
            'table_chart_style': 'test_value_27',
            'toc_heading1_style': 'test_value_28',
            'toc_heading2_style': 'test_value_29',
            'toc_heading3_style': 'test_value_30',
            'toc_heading4_style': 'test_value_31',
            'toc_title_style': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_theme.fortios_report(input_data, fos_instance)

    delete_method_mock.assert_called_with('report', 'theme', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200


def test_report_theme_deletion_fails(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    delete_method_result = {'status': 'error', 'http_method': 'POST', 'http_status': 500}
    delete_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.delete', return_value=delete_method_result)

    input_data = {
        'username': 'admin',
        'state': 'absent',
        'report_theme': {
            'bullet_list_style': 'test_value_3',
            'column_count': '1',
            'default_html_style': 'test_value_5',
            'default_pdf_style': 'test_value_6',
            'graph_chart_style': 'test_value_7',
            'heading1_style': 'test_value_8',
            'heading2_style': 'test_value_9',
            'heading3_style': 'test_value_10',
            'heading4_style': 'test_value_11',
            'hline_style': 'test_value_12',
            'image_style': 'test_value_13',
            'name': 'default_name_14',
            'normal_text_style': 'test_value_15',
            'numbered_list_style': 'test_value_16',
            'page_footer_style': 'test_value_17',
            'page_header_style': 'test_value_18',
            'page_orient': 'portrait',
            'page_style': 'test_value_20',
            'report_subtitle_style': 'test_value_21',
            'report_title_style': 'test_value_22',
            'table_chart_caption_style': 'test_value_23',
            'table_chart_even_row_style': 'test_value_24',
            'table_chart_head_style': 'test_value_25',
            'table_chart_odd_row_style': 'test_value_26',
            'table_chart_style': 'test_value_27',
            'toc_heading1_style': 'test_value_28',
            'toc_heading2_style': 'test_value_29',
            'toc_heading3_style': 'test_value_30',
            'toc_heading4_style': 'test_value_31',
            'toc_title_style': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_theme.fortios_report(input_data, fos_instance)

    delete_method_mock.assert_called_with('report', 'theme', mkey=ANY, vdom='root')
    schema_method_mock.assert_not_called()
    assert is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 500


def test_report_theme_idempotent(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'error', 'http_method': 'DELETE', 'http_status': 404}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'report_theme': {
            'bullet_list_style': 'test_value_3',
            'column_count': '1',
            'default_html_style': 'test_value_5',
            'default_pdf_style': 'test_value_6',
            'graph_chart_style': 'test_value_7',
            'heading1_style': 'test_value_8',
            'heading2_style': 'test_value_9',
            'heading3_style': 'test_value_10',
            'heading4_style': 'test_value_11',
            'hline_style': 'test_value_12',
            'image_style': 'test_value_13',
            'name': 'default_name_14',
            'normal_text_style': 'test_value_15',
            'numbered_list_style': 'test_value_16',
            'page_footer_style': 'test_value_17',
            'page_header_style': 'test_value_18',
            'page_orient': 'portrait',
            'page_style': 'test_value_20',
            'report_subtitle_style': 'test_value_21',
            'report_title_style': 'test_value_22',
            'table_chart_caption_style': 'test_value_23',
            'table_chart_even_row_style': 'test_value_24',
            'table_chart_head_style': 'test_value_25',
            'table_chart_odd_row_style': 'test_value_26',
            'table_chart_style': 'test_value_27',
            'toc_heading1_style': 'test_value_28',
            'toc_heading2_style': 'test_value_29',
            'toc_heading3_style': 'test_value_30',
            'toc_heading4_style': 'test_value_31',
            'toc_title_style': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_theme.fortios_report(input_data, fos_instance)

    expected_data = {
        'bullet-list-style': 'test_value_3',
        'column-count': '1',
        'default-html-style': 'test_value_5',
        'default-pdf-style': 'test_value_6',
        'graph-chart-style': 'test_value_7',
        'heading1-style': 'test_value_8',
        'heading2-style': 'test_value_9',
        'heading3-style': 'test_value_10',
        'heading4-style': 'test_value_11',
        'hline-style': 'test_value_12',
        'image-style': 'test_value_13',
        'name': 'default_name_14',
                'normal-text-style': 'test_value_15',
                'numbered-list-style': 'test_value_16',
                'page-footer-style': 'test_value_17',
                'page-header-style': 'test_value_18',
                'page-orient': 'portrait',
                'page-style': 'test_value_20',
                'report-subtitle-style': 'test_value_21',
                'report-title-style': 'test_value_22',
                'table-chart-caption-style': 'test_value_23',
                'table-chart-even-row-style': 'test_value_24',
                'table-chart-head-style': 'test_value_25',
                'table-chart-odd-row-style': 'test_value_26',
                'table-chart-style': 'test_value_27',
                'toc-heading1-style': 'test_value_28',
                'toc-heading2-style': 'test_value_29',
                'toc-heading3-style': 'test_value_30',
                'toc-heading4-style': 'test_value_31',
                'toc-title-style': 'test_value_32'
    }

    set_method_mock.assert_called_with('report', 'theme', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert not changed
    assert response['status'] == 'error'
    assert response['http_status'] == 404


def test_report_theme_filter_foreign_attributes(mocker):
    schema_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.schema')

    set_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    set_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.set', return_value=set_method_result)

    input_data = {
        'username': 'admin',
        'state': 'present',
        'report_theme': {
            'random_attribute_not_valid': 'tag',
            'bullet_list_style': 'test_value_3',
            'column_count': '1',
            'default_html_style': 'test_value_5',
            'default_pdf_style': 'test_value_6',
            'graph_chart_style': 'test_value_7',
            'heading1_style': 'test_value_8',
            'heading2_style': 'test_value_9',
            'heading3_style': 'test_value_10',
            'heading4_style': 'test_value_11',
            'hline_style': 'test_value_12',
            'image_style': 'test_value_13',
            'name': 'default_name_14',
            'normal_text_style': 'test_value_15',
            'numbered_list_style': 'test_value_16',
            'page_footer_style': 'test_value_17',
            'page_header_style': 'test_value_18',
            'page_orient': 'portrait',
            'page_style': 'test_value_20',
            'report_subtitle_style': 'test_value_21',
            'report_title_style': 'test_value_22',
            'table_chart_caption_style': 'test_value_23',
            'table_chart_even_row_style': 'test_value_24',
            'table_chart_head_style': 'test_value_25',
            'table_chart_odd_row_style': 'test_value_26',
            'table_chart_style': 'test_value_27',
            'toc_heading1_style': 'test_value_28',
            'toc_heading2_style': 'test_value_29',
            'toc_heading3_style': 'test_value_30',
            'toc_heading4_style': 'test_value_31',
            'toc_title_style': 'test_value_32'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_report_theme.fortios_report(input_data, fos_instance)

    expected_data = {
        'bullet-list-style': 'test_value_3',
        'column-count': '1',
        'default-html-style': 'test_value_5',
        'default-pdf-style': 'test_value_6',
        'graph-chart-style': 'test_value_7',
        'heading1-style': 'test_value_8',
        'heading2-style': 'test_value_9',
        'heading3-style': 'test_value_10',
        'heading4-style': 'test_value_11',
        'hline-style': 'test_value_12',
        'image-style': 'test_value_13',
        'name': 'default_name_14',
                'normal-text-style': 'test_value_15',
                'numbered-list-style': 'test_value_16',
                'page-footer-style': 'test_value_17',
                'page-header-style': 'test_value_18',
                'page-orient': 'portrait',
                'page-style': 'test_value_20',
                'report-subtitle-style': 'test_value_21',
                'report-title-style': 'test_value_22',
                'table-chart-caption-style': 'test_value_23',
                'table-chart-even-row-style': 'test_value_24',
                'table-chart-head-style': 'test_value_25',
                'table-chart-odd-row-style': 'test_value_26',
                'table-chart-style': 'test_value_27',
                'toc-heading1-style': 'test_value_28',
                'toc-heading2-style': 'test_value_29',
                'toc-heading3-style': 'test_value_30',
                'toc-heading4-style': 'test_value_31',
                'toc-title-style': 'test_value_32'
    }

    set_method_mock.assert_called_with('report', 'theme', data=expected_data, vdom='root')
    schema_method_mock.assert_not_called()
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
