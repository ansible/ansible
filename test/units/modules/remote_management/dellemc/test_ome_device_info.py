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
from ansible.modules.remote_management.dellemc import ome_device_info
from ansible.module_utils.six.moves.urllib.error import HTTPError

default_args = {'hostname': '192.168.0.1', 'username': 'username', 'password': 'password'}
resource_basic_inventory = {"basic_inventory": "DeviceService/Devices"}
resource_detailed_inventory = {"detailed_inventory:": {"device_id": {1234: None},
                                                       "device_service_tag": {1345: "MXL1234"}}}


class TestOmeDeviceInfo(object):
    module = ome_device_info

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.remote_management.dellemc.ome_device_info.RestOME')
        return connection_class_mock.return_value

    @pytest.fixture
    def response_mock(self, mocker):
        response_class_mock = mocker.patch('ansible.module_utils.remote_management.dellemc.ome.OpenURLResponse')
        return response_class_mock

    @pytest.fixture
    def validate_inputs_mock(self, mocker):
        response_class_mock = mocker.patch('ansible.modules.remote_management.dellemc.ome_device_info._validate_inputs')
        response_class_mock.return_value = None

    @pytest.fixture
    def get_device_identifier_map_mock(self, mocker):
        response_class_mock = mocker.patch('ansible.modules.remote_management.dellemc.ome_device_info._get_device_identifier_map')
        response_class_mock.return_value = resource_detailed_inventory
        return response_class_mock.return_value

    @pytest.fixture
    def get_resource_parameters_mock(self, mocker):
        response_class_mock = mocker.patch('ansible.modules.remote_management.dellemc.ome_device_info._get_resource_parameters')
        return response_class_mock

    def test_main_basic_inventory_success_case(self, module_mock, validate_inputs_mock, connection_mock, get_resource_parameters_mock, response_mock):
        get_resource_parameters_mock.return_value = resource_basic_inventory
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.json_data = {"value": [{"device_id1": "details", "device_id2": "details"}]}
        response_mock.status_code = 200
        result = self._run_module(default_args)
        assert result['changed'] is False
        assert 'device_info' in result

    def test_main_basic_inventory_failure_case(self, module_mock, validate_inputs_mock, connection_mock, get_resource_parameters_mock, response_mock):
        get_resource_parameters_mock.return_value = resource_basic_inventory
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.status_code = 500
        result = self._run_module_with_fail_json(default_args)
        assert result['msg'] == 'Failed to fetch the device information'

    def test_main_detailed_inventory_success_case(self, module_mock, validate_inputs_mock, connection_mock, get_resource_parameters_mock, response_mock):
        default_args.update({"fact_subset": "detailed_inventory", "system_query_options": {"device_id": [1234], "device_service_tag": ["MXL1234"]}})
        detailed_inventory = {"detailed_inventory:": {"device_id": {1234: "DeviceService/Devices(1234)/InventoryDetails"},
                                                      "device_service_tag": {"MXL1234": "DeviceService/Devices(4321)/InventoryDetails"}}}
        get_resource_parameters_mock.return_value = detailed_inventory
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.json_data = {"value": [{"device_id": {"1234": "details"}}, {"device_service_tag": {"MXL1234": "details"}}]}
        response_mock.status_code = 200
        result = self._run_module(default_args)
        assert result['changed'] is False
        assert 'device_info' in result

    def test_main_HTTPError_error_case(self, module_mock, validate_inputs_mock, connection_mock, get_resource_parameters_mock, response_mock):
        get_resource_parameters_mock.return_value = resource_basic_inventory
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.side_effect = HTTPError('http://testhost.com', 400, '', {}, None)
        response_mock.json_data = {"value": [{"device_id1": "details", "device_id2": "details"}]}
        response_mock.status_code = 400
        result = self._run_module_with_fail_json(default_args)
        assert 'device_info' not in result
        assert result['failed'] is True

    @pytest.mark.parametrize("fact_subset, mutually_exclusive_call", [("basic_inventory", False), ("detailed_inventory", True)])
    def test_validate_inputs(self, fact_subset, mutually_exclusive_call, mocker):
        module_params = {"fact_subset": fact_subset}
        check_mutually_inclusive_arguments_mock = mocker.patch(
            'ansible.modules.remote_management.dellemc.ome_device_info._check_mutually_inclusive_arguments')
        check_mutually_inclusive_arguments_mock.return_value = None
        self.module._validate_inputs(module_params)
        if mutually_exclusive_call:
            check_mutually_inclusive_arguments_mock.assert_called()
        else:
            check_mutually_inclusive_arguments_mock.assert_not_called()
        check_mutually_inclusive_arguments_mock.reset_mock()

    system_query_options_params = [{"system_query_options": None}, {"system_query_options": {"device_id": None}},
                                   {"system_query_options": {"device_service_tag": None}}]

    @pytest.mark.parametrize("system_query_options_params", system_query_options_params)
    def test_check_mutually_inclusive_arguments(self, system_query_options_params):
        module_params = {"fact_subset": "subsystem_health"}
        required_args = ["device_id", "device_service_tag"]
        module_params.update(system_query_options_params)
        with pytest.raises(ValueError) as ex:
            self.module._check_mutually_inclusive_arguments(module_params["fact_subset"], module_params, ["device_id", "device_service_tag"])
        assert "One of the following {0} is required for {1}".format(required_args, module_params["fact_subset"]) == str(ex.value)

    params = [{"fact_subset": "basic_inventory", "system_query_options": {"device_id": [1234]}},
              {"fact_subset": "subsystem_health", "system_query_options": {"device_service_tag": ["MXL1234"]}},
              {"fact_subset": "detailed_inventory", "system_query_options": {"device_id": [1234], "inventory_type": "serverDeviceCards"}}]

    @pytest.mark.parametrize("module_params", params)
    def test_get_resource_parameters(self, module_params, connection_mock):
        self.module._get_resource_parameters(module_params, connection_mock)

    @pytest.mark.parametrize("module_params,data", [({"system_query_options": None}, None), ({"system_query_options": {"fileter": None}}, None),
                                                    ({"system_query_options": {"filter": "abc"}}, "$filter")])
    def test_get_query_parameters(self, module_params, data):
        res = self.module._get_query_parameters(module_params)
        if data is not None:
            assert data in res
        else:
            assert res is None

    @pytest.mark.parametrize("module_params", params)
    def test_get_device_identifier_map(self, module_params, connection_mock, mocker):
        get_device_id_from_service_tags_mock = mocker.patch('ansible.modules.remote_management.dellemc.ome_device_info._get_device_id_from_service_tags')
        get_device_id_from_service_tags_mock.return_value = None
        res = self.module._get_device_identifier_map(module_params, connection_mock)
        assert isinstance(res, dict)

    def test_check_duplicate_device_id(self):
        self.module._check_duplicate_device_id([1234], {1234: "MX1234"})
        assert self.module.device_fact_error_report["MX1234"] == "Duplicate report of device_id: 1234"

    @pytest.mark.parametrize("val,expected_res", [(123, True), ("abc", False)])
    def test_is_int(self, val, expected_res):
        actual_res = self.module.is_int(val)
        assert actual_res == expected_res

    def test_get_device_id_from_service_tags(self, connection_mock, response_mock):
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.return_value = response_mock
        response_mock.json_data = {"value": [{"DeviceServiceTag": "MX1234", "Id": 1234}]}
        response_mock.status_code = 200
        response_mock.success = True
        self.module._get_device_id_from_service_tags(["MX1234", "INVALID"], connection_mock)

    def test_get_device_id_from_service_tags_error_case(self, connection_mock, response_mock):
        connection_mock.__enter__.return_value = connection_mock
        connection_mock.invoke_request.side_effect = HTTPError('http://testhost.com',
                                                               400, '', {}, None)
        response_mock.json_data = {"value": [{"DeviceServiceTag": "MX1234", "Id": 1234}]}
        response_mock.status_code = 200
        response_mock.success = True
        with pytest.raises(HTTPError) as ex:
            self.module._get_device_id_from_service_tags(["INVALID"], connection_mock)

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
