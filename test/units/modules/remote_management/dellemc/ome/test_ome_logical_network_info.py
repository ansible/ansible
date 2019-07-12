# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.0
# Copyright (C) 2019 Dell Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# All rights reserved. Dell, EMC, and other trademarks are trademarks of Dell Inc. or its subsidiaries.
# Other trademarks may be trademarks of their respective owners.
#

from __future__ import absolute_import

import pytest
from units.modules.utils import set_module_args, exit_json, \
    fail_json, AnsibleFailJson, AnsibleExitJson
from ansible.module_utils import basic
from ansible.modules.remote_management.dellemc.ome import ome_logical_network_info
from ansible.module_utils.six.moves.urllib.error import HTTPError

default_args = {'hostname': '192.168.0.1', 'username': 'username', 'password': 'password'}
resource_logical_network_id = {"logical_network_id": "NetworkConfigurationService/Networks(1234)"}


class TestOmeLogicalNetworkInfo(object):
    module = ome_logical_network_info

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.remote_management.'
                                             'dellemc.ome.ome_logical_network_info.RestOME')
        return connection_class_mock.return_value

    @pytest.fixture
    def response_mock(self, mocker):
        response_class_mock = mocker.patch('ansible.module_utils.remote_management.dellemc.ome.OpenURLResponse')
        return response_class_mock

    def test_main_all_logical_network_info_success_case(self, module_mock,
                                                        connection_mock, response_mock):
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.json_data = {"value": [{"attribute1": "details", "attribute2": "details"},
                                             {"attribute1": "details", "attribute2": "details"}]}
        response_mock.status_code = 200
        result = self._run_module(default_args)
        assert result['changed'] is False
        assert 'logical_network_info' in result

    def test_main_logical_network_failure_case_1(self, module_mock, connection_mock, response_mock):
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.status_code = 500
        result = self._run_module_with_fail_json(default_args)
        assert result['msg'] == 'Failed to fetch the device logical network information'

    def test_main_logical_network_failure_case_2(self, mocker, module_mock, connection_mock, response_mock):
        default_args.update({"logical_network_name": "logical network"})
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_requefst.return_value = response_mock
        get_logical_network_id_from_logical_network_name = \
            mocker.patch('ansible.modules.remote_management.dellemc.ome.'
                         'ome_logical_network_info.'
                         '_get_logical_network_id_from_logical_network_name')
        get_logical_network_id_from_logical_network_name.return_value = False
        response_mock.json_data = None
        response_mock.status_code = 400
        result = self._run_module_with_fail_json(default_args)
        assert result['failed'] is True
        assert result['msg'] == "Provided logical network name - '{0}' does not exist in the device".\
            format(default_args['logical_network_name'])

    def test_main_specific_logical_network_id_success_case(self, module_mock, connection_mock, response_mock):
        default_args.update({"logical_network_id": "1234"})
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.json_data = {"value": [{"1234": "details"}]}
        response_mock.status_code = 200
        result = self._run_module(default_args)
        assert result['changed'] is False
        assert 'logical_network_info' in result

    def test_main_http_error_error_case(self, module_mock, connection_mock,
                                        response_mock):
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.side_effect = HTTPError('http://testhost.com', 400, '', {}, None)
        response_mock.json_data = {"value": [{"Id": "details", "Name": "details"}]}
        response_mock.status_code = 400
        result = self._run_module_with_fail_json(default_args)
        assert 'logical_network_info' not in result
        assert result['failed'] is True

    def test_get_logical_network_id_from_logical_network_name_success_case(self, connection_mock, response_mock):
        default_args.update({"logical_network_name": "logical network"})
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.json_data = {"value": [{"Name": "logical network", "Id": 1234}]}
        response_mock.status_code = 200
        result = self.module._get_logical_network_id_from_logical_network_name("logical network", connection_mock)
        assert 1234 == result
        assert isinstance(result, int)

    def test_get_logical_network_id_from_logical_network_name_fail_case(self, connection_mock, response_mock):
        default_args.update({"logical_network_name": "logical network"})
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.json_data = {"value": [{"Name": "logical", "Id": 1234}]}
        response_mock.status_code = 200
        result = self.module._get_logical_network_id_from_logical_network_name("logical network", connection_mock)
        assert result is False
        assert isinstance(result, bool)

    def test_get_logical_network_id_from_logical_network_name_error_case_1(self, connection_mock, response_mock):
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.side_effect = HTTPError('http://testhost.com', 400, '', {}, None)
        response_mock.json_data = {"value": [{"Name": "logical network", "Id": 1234}]}
        response_mock.status_code = 400
        with pytest.raises(HTTPError):
            self.module._get_logical_network_id_from_logical_network_name("INVALID", connection_mock)

    def test_get_logical_network_id_from_logical_network_name_error_case_2(self, connection_mock, response_mock):
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.success = False
        with pytest.raises(ValueError):
            self.module._get_logical_network_id_from_logical_network_name(1234, connection_mock)

    def test_main_logical_network_name_success_case(self, mocker, connection_mock, response_mock):
        default_args.update({"logical_network_name": "logical network"})
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        get_logical_network_id_from_logical_network_name = \
            mocker.patch('ansible.modules.remote_management.dellemc.ome.'
                         'ome_logical_network_info.'
                         '_get_logical_network_id_from_logical_network_name')
        get_logical_network_id_from_logical_network_name.return_value = 1234
        response_mock.json_data = {"value": [{1234: "details"}]}
        response_mock.status_code = 200
        result = self._run_module(default_args)
        assert result['changed'] is False
        assert 'logical_network_info' in result

    def _run_module(self, module_args):
        set_module_args(module_args)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()
        return ex.value.args[0]

    def _run_module_with_fail_json(self, module_args):
        set_module_args(module_args)
        with pytest.raises(AnsibleFailJson) as exc:
            self.module.main()
        result = exc.value.args[0]
        return result
