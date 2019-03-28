# -*- coding: utf-8 -*-
#
# Copyright 2017 Radware LTD.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
from mock import patch, MagicMock

from units.compat import unittest
from units.compat.mock import patch

RESP_STATUS = 0
RESP_REASON = 1
RESP_STR = 2
RESP_DATA = 3

NONE_PARAMS = {'vdirect_ip': None, 'vdirect_user': None, 'vdirect_password': None,
               'vdirect_wait': None, 'vdirect_secondary_ip': None,
               'vdirect_https_port': None, 'vdirect_http_port': None,
               'vdirect_timeout': None, 'vdirect_use_ssl': None, 'validate_certs': None}


@patch('vdirect_client.rest_client.RestClient')
class RestClient:
    def __init__(self, vdirect_ip=None, vdirect_user=None, vdirect_password=None, wait=None,
                 secondary_vdirect_ip=None, https_port=None, http_port=None,
                 timeout=None, https=None, strict_http_results=None,
                 verify=None):
        pass


@patch('vdirect_client.rest_client.Template')
class Template:
    create_from_source_result = None
    upload_source_result = None

    def __init__(self, client):
        self.client = client

    @classmethod
    def set_create_from_source_result(cls, result):
        Template.create_from_source_result = result

    @classmethod
    def set_upload_source_result(cls, result):
        Template.upload_source_result = result

    def create_from_source(self, data, name=None, tenant=None, fail_if_invalid=False):
        return Template.create_from_source_result

    def upload_source(self, data, name=None, tenant=None, fail_if_invalid=False):
        return Template.upload_source_result


@patch('vdirect_client.rest_client.WorkflowTemplate')
class WorkflowTemplate:
    create_template_from_archive_result = None
    update_archive_result = None

    def __init__(self, client):
        self.client = client

    @classmethod
    def set_create_template_from_archive_result(cls, result):
        WorkflowTemplate.create_template_from_archive_result = result

    @classmethod
    def set_update_archive_result(cls, result):
        WorkflowTemplate.update_archive_result = result

    def create_template_from_archive(self, data, validate=False, fail_if_invalid=False, tenant=None):
        return WorkflowTemplate.create_template_from_archive_result

    def update_archive(self, data, workflow_template_name):
        return WorkflowTemplate.update_archive_result


class TestManager(unittest.TestCase):

    def setUp(self):
        pass

    def test_missing_parameter(self, *args):
        module_mock = MagicMock()
        with patch.dict('sys.modules', **{
            'vdirect_client': module_mock,
            'vdirect_client.rest_client': module_mock,
        }):
            from ansible.modules.network.radware import vdirect_file

            try:
                params = NONE_PARAMS.copy()
                del params['vdirect_ip']
                vdirect_file.VdirectFile(params)
                self.fail("KeyError was not thrown for missing parameter")
            except KeyError:
                assert True

    def test_wrong_file_extension(self, *args):
        module_mock = MagicMock()
        with patch.dict('sys.modules', **{
            'vdirect_client': module_mock,
            'vdirect_client.rest_client': module_mock,
        }):
            from ansible.modules.network.radware import vdirect_file

            module_mock.RESP_STATUS = 0
            file = vdirect_file.VdirectFile(NONE_PARAMS)
            result = file.upload("file.??")
            assert result == vdirect_file.WRONG_EXTENSION_ERROR

    def test_missing_file(self, *args):
        module_mock = MagicMock()
        with patch.dict('sys.modules', **{
            'vdirect_client': module_mock,
            'vdirect_client.rest_client': module_mock,
        }):
            from ansible.modules.network.radware import vdirect_file

            file = vdirect_file.VdirectFile(NONE_PARAMS)
            try:
                file.upload("missing_file.vm")
                self.fail("IOException was not thrown for missing file")
            except IOError:
                assert True

    def test_template_upload_create(self, *args):
        module_mock = MagicMock()
        with patch.dict('sys.modules', **{
            'vdirect_client': module_mock,
            'vdirect_client.rest_client': module_mock,
        }):
            from ansible.modules.network.radware import vdirect_file
            vdirect_file.rest_client.RESP_STATUS = 0
            vdirect_file.rest_client.Template = Template

            file = vdirect_file.VdirectFile(NONE_PARAMS)
            path = os.path.dirname(os.path.abspath(__file__))

            Template.set_create_from_source_result([201])
            result = file.upload(os.path.join(path, "ct.vm"))
            self.assertEqual(result, vdirect_file.CONFIGURATION_TEMPLATE_CREATED_SUCCESS,
                             'Unexpected result received:' + repr(result))

            Template.set_create_from_source_result([400, "", "Parsing error", ""])
            try:
                result = file.upload(os.path.join(path, "ct.vm"))
                self.fail("InvalidSourceException was not thrown")
            except vdirect_file.InvalidSourceException:
                assert True

    def test_template_upload_update(self, *args):
        module_mock = MagicMock()
        with patch.dict('sys.modules', **{
            'vdirect_client': module_mock,
            'vdirect_client.rest_client': module_mock,
        }):
            from ansible.modules.network.radware import vdirect_file
            vdirect_file.rest_client.RESP_STATUS = 0
            vdirect_file.rest_client.Template = Template

            file = vdirect_file.VdirectFile(NONE_PARAMS)
            path = os.path.dirname(os.path.abspath(__file__))

            Template.set_create_from_source_result([409])
            Template.set_upload_source_result([201])
            result = file.upload(os.path.join(path, "ct.vm"))
            self.assertEqual(result, vdirect_file.CONFIGURATION_TEMPLATE_UPDATED_SUCCESS,
                             'Unexpected result received:' + repr(result))

            Template.set_upload_source_result([400, "", "Parsing error", ""])
            try:
                result = file.upload(os.path.join(path, "ct.vm"))
                self.fail("InvalidSourceException was not thrown")
            except vdirect_file.InvalidSourceException:
                assert True

    def test_workflow_upload_create(self, *args):
        module_mock = MagicMock()
        with patch.dict('sys.modules', **{
            'vdirect_client': module_mock,
            'vdirect_client.rest_client': module_mock,
        }):
            from ansible.modules.network.radware import vdirect_file
            vdirect_file.rest_client.RESP_STATUS = 0
            vdirect_file.rest_client.WorkflowTemplate = WorkflowTemplate

            file = vdirect_file.VdirectFile(NONE_PARAMS)
            path = os.path.dirname(os.path.abspath(__file__))

            WorkflowTemplate.set_create_template_from_archive_result([201])
            result = file.upload(os.path.join(path, "wt.zip"))
            self.assertEqual(result, vdirect_file.WORKFLOW_TEMPLATE_CREATED_SUCCESS,
                             'Unexpected result received:' + repr(result))

            WorkflowTemplate.set_create_template_from_archive_result([400, "", "Parsing error", ""])
            try:
                result = file.upload(os.path.join(path, "wt.zip"))
                self.fail("InvalidSourceException was not thrown")
            except vdirect_file.InvalidSourceException:
                assert True

    def test_workflow_upload_update(self, *args):
        module_mock = MagicMock()
        with patch.dict('sys.modules', **{
            'vdirect_client': module_mock,
            'vdirect_client.rest_client': module_mock,
        }):
            from ansible.modules.network.radware import vdirect_file
            vdirect_file.rest_client.RESP_STATUS = 0
            vdirect_file.rest_client.WorkflowTemplate = WorkflowTemplate

            file = vdirect_file.VdirectFile(NONE_PARAMS)
            path = os.path.dirname(os.path.abspath(__file__))

            WorkflowTemplate.set_create_template_from_archive_result([409])
            WorkflowTemplate.set_update_archive_result([201])
            result = file.upload(os.path.join(path, "wt.zip"))
            self.assertEqual(result, vdirect_file.WORKFLOW_TEMPLATE_UPDATED_SUCCESS,
                             'Unexpected result received:' + repr(result))

            WorkflowTemplate.set_update_archive_result([400, "", "Parsing error", ""])
            try:
                result = file.upload(os.path.join(path, "wt.zip"))
                self.fail("InvalidSourceException was not thrown")
            except vdirect_file.InvalidSourceException:
                assert True
