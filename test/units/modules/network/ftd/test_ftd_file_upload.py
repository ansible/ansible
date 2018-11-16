# Copyright (c) 2018 Cisco and/or its affiliates.
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
#

from __future__ import absolute_import

import pytest

from ansible.module_utils import basic
from ansible.module_utils.network.ftd.common import HTTPMethod
from ansible.module_utils.network.ftd.fdm_swagger_client import OperationField
from ansible.modules.network.ftd import ftd_file_upload
from units.modules.utils import set_module_args, exit_json, fail_json, AnsibleFailJson, AnsibleExitJson


class TestFtdFileUpload(object):
    module = ftd_file_upload

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_file_upload.Connection')
        return connection_class_mock.return_value

    @pytest.mark.parametrize("missing_arg", ['operation', 'file_to_upload'])
    def test_module_should_fail_without_required_args(self, missing_arg):
        module_args = {'operation': 'uploadFile', 'file_to_upload': '/tmp/test.txt'}
        del module_args[missing_arg]
        set_module_args(module_args)

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        assert 'missing required arguments: %s' % missing_arg in str(ex)

    def test_module_should_fail_when_no_operation_spec_found(self, connection_mock):
        connection_mock.get_operation_spec.return_value = None
        set_module_args({'operation': 'nonExistingUploadOperation', 'file_to_upload': '/tmp/test.txt'})

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['failed']
        assert result['msg'] == 'Operation with specified name is not found: nonExistingUploadOperation'

    def test_module_should_fail_when_not_upload_operation_specified(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.URL: '/object/network',
            OperationField.MODEL_NAME: 'NetworkObject'
        }
        set_module_args({'operation': 'nonUploadOperation', 'file_to_upload': '/tmp/test.txt'})

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['failed']
        assert result['msg'] == 'Invalid upload operation: nonUploadOperation. ' \
                                'The operation must make POST request and return UploadStatus model.'

    def test_module_should_call_upload_and_return_response(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {
            OperationField.METHOD: HTTPMethod.POST,
            OperationField.URL: '/uploadFile',
            OperationField.MODEL_NAME: 'FileUploadStatus'
        }
        connection_mock.upload_file.return_value = {'id': '123'}

        set_module_args({
            'operation': 'uploadFile',
            'file_to_upload': '/tmp/test.txt'
        })
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['changed']
        assert {'id': '123'} == result['response']
        connection_mock.upload_file.assert_called_once_with('/tmp/test.txt', '/uploadFile')
