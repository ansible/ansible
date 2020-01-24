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
from ansible.module_utils.network.ftd.fdm_swagger_client import FILE_MODEL_NAME, OperationField
from ansible.modules.network.ftd import ftd_file_download
from units.modules.utils import set_module_args, exit_json, fail_json, AnsibleFailJson, AnsibleExitJson


class TestFtdFileDownload(object):
    module = ftd_file_download

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_file_download.Connection')
        return connection_class_mock.return_value

    @pytest.mark.parametrize("missing_arg", ['operation', 'destination'])
    def test_module_should_fail_without_required_args(self, missing_arg):
        module_args = {'operation': 'downloadFile', 'destination': '/tmp'}
        del module_args[missing_arg]
        set_module_args(module_args)

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        assert 'missing required arguments: %s' % missing_arg in str(ex.value)

    def test_module_should_fail_when_no_operation_spec_found(self, connection_mock):
        connection_mock.get_operation_spec.return_value = None
        set_module_args({'operation': 'nonExistingDownloadOperation', 'destination': '/tmp'})

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['failed']
        assert result['msg'] == 'Operation with specified name is not found: nonExistingDownloadOperation'

    def test_module_should_fail_when_not_download_operation_specified(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.URL: '/object',
            OperationField.MODEL_NAME: 'NetworkObject'
        }
        set_module_args({'operation': 'nonDownloadOperation', 'destination': '/tmp'})

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['failed']
        assert result['msg'] == 'Invalid download operation: nonDownloadOperation. ' \
                                'The operation must make GET request and return a file.'

    def test_module_should_call_download_and_return(self, connection_mock):
        connection_mock.validate_path_params.return_value = (True, None)
        connection_mock.get_operation_spec.return_value = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.URL: '/file/{objId}',
            OperationField.MODEL_NAME: FILE_MODEL_NAME
        }

        set_module_args({
            'operation': 'downloadFile',
            'path_params': {'objId': '12'},
            'destination': '/tmp'
        })
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert not result['changed']
        connection_mock.download_file.assert_called_once_with('/file/{objId}', '/tmp', {'objId': '12'})
