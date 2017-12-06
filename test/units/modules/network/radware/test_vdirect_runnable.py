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
from ansible.compat.tests.mock import patch, MagicMock

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

BASE_PARAMS = {'vdirect_ip': None, 'vdirect_user': None, 'vdirect_password': None,
               'vdirect_wait': None, 'vdirect_secondary_ip': None,
               'vdirect_https_port': None, 'vdirect_http_port': None,
               'vdirect_timeout': None, 'vdirect_use_ssl': None, 'vdirect_validate_certs': None}

RUNNABLE_PARAMS = {'runnable_type': 'ConfigurationTemplate', 'runnable_name': 'runnable',
                   'action_name': None, 'parameters': None}

RUNNABLE_OBJECTS_RESULT = [200, '', '', {'names': ['runnable']}]
AVAILABLE_ACTIONS_RESULT = [200, '', '', {'names': ['a', 'b']}]
ACTIONS_PARAMS_RESULT = [200, '', '', {'parameters': [{'name': 'pin', 'type': 'in', 'direction': 'in'},
                                                      {'name': 'pout', 'type': 'out', 'direction': 'out'},
                                                      {'name': 'alteon', 'type': 'alteon'}]}]

RUN_RESULT = [200, '', '', {
    "uri": "https://10.11.12.13:2189/api/status?token=Workflow%5Ca%5Capply%5Cc4b533a8-8764-4cbf-a19c-63b11b9ccc09",
    "targetUri": "https://10.11.12.13:2189/api/workflow/a",
    "complete": True, "status": 200, "success": True, "messages": [], "action": "apply", "parameters": {},
}]

MODULE_RESULT = {"msg": "Configuration template run completed.", "parameters": {}}


@patch('vdirect_client.rest_client.RestClient')
class RestClient ():
    def __init__(self, vdirect_ip=None, vdirect_user=None, vdirect_password=None, wait=None,
                 secondary_vdirect_ip=None, https_port=None, http_port=None,
                 timeout=None, https=None, strict_http_results=None,
                 verify=None):
        pass


@patch('vdirect_client.rest_client.Runnable')
class Runnable ():
    available_actions_result = None
    action_info_result = None
    runnable_objects_result = None
    run_result = None

    def __init__(self, client):
        self.client = client

    @classmethod
    def set_action_info_result(cls, result):
        Runnable.action_info_result = result

    @classmethod
    def set_available_actions_result(cls, result):
        Runnable.available_actions_result = result

    @classmethod
    def set_run_result(cls, result):
        Runnable.run_result = result

    @classmethod
    def set_runnable_objects_result(cls, result):
        Runnable.runnable_objects_result = result

    def get_available_actions(self, type=None, name=None):
        return Runnable.available_actions_result

    def get_action_info(self, type, name, action_name):
        return Runnable.action_info_result

    def run(self, data, type, name, action_name):
        return Runnable.run_result

    def get_runnable_objects(self, type):
        return Runnable.runnable_objects_result


class TestManager(unittest.TestCase):

    def setUp(self):
        self.module_mock = MagicMock()
        self.module_mock.rest_client.RESP_STATUS = 0
        self.module_mock.rest_client.RESP_REASON = 1
        self.module_mock.rest_client.RESP_STR = 2
        self.module_mock.rest_client.RESP_DATA = 3

    def test_missing_parameter(self, *args):
        with patch.dict('sys.modules', **{
            'vdirect_client': self.module_mock,
            'vdirect_client.rest_client': self.module_mock,
        }):
            from ansible.modules.network.radware import vdirect_runnable

            try:
                params = BASE_PARAMS.copy()
                vdirect_runnable.VdirectRunnable(params)
                self.fail("KeyError was not thrown for missing parameter")
            except KeyError:
                assert True

    def test_validate_runnable_exists(self, *args):
        with patch.dict('sys.modules', **{
            'vdirect_client': self.module_mock,
            'vdirect_client.rest_client': self.module_mock,
        }):
            from ansible.modules.network.radware import vdirect_runnable

            Runnable.set_runnable_objects_result(RUNNABLE_OBJECTS_RESULT)
            BASE_PARAMS.update(RUNNABLE_PARAMS)
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable.client.runnable = Runnable(vdirectRunnable.client)
            vdirectRunnable._validate_runnable_exists()
            assert True

            BASE_PARAMS.update(RUNNABLE_PARAMS)
            BASE_PARAMS['runnable_name'] = "missing"
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable.client.runnable = Runnable(vdirectRunnable.client)
            try:
                vdirectRunnable._validate_runnable_exists()
                self.fail("MissingRunnableException was not thrown for missing runnable name")
            except vdirect_runnable.MissingRunnableException:
                assert True

    def test_validate_action_name(self, *args):
        with patch.dict('sys.modules', **{
            'vdirect_client': self.module_mock,
            'vdirect_client.rest_client': self.module_mock,
        }):
            from ansible.modules.network.radware import vdirect_runnable

            Runnable.set_runnable_objects_result(RUNNABLE_OBJECTS_RESULT)
            BASE_PARAMS.update(RUNNABLE_PARAMS)
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable._validate_action_name()
            assert vdirectRunnable.action_name == vdirect_runnable.VdirectRunnable.RUN_ACTION

            BASE_PARAMS['runnable_type'] = vdirect_runnable.WORKFLOW_TEMPLATE_RUNNABLE_TYPE
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable._validate_action_name()
            assert vdirectRunnable.action_name == vdirect_runnable.VdirectRunnable.CREATE_WORKFLOW_ACTION

            BASE_PARAMS['runnable_type'] = vdirect_runnable.WORKFLOW_RUNNABLE_TYPE
            BASE_PARAMS['action_name'] = 'a'
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable.client.runnable = Runnable(vdirectRunnable.client)
            Runnable.set_available_actions_result(AVAILABLE_ACTIONS_RESULT)
            vdirectRunnable._validate_action_name()
            assert vdirectRunnable.action_name == 'a'

            BASE_PARAMS['action_name'] = 'c'
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable.client.runnable = Runnable(vdirectRunnable.client)
            Runnable.set_available_actions_result(AVAILABLE_ACTIONS_RESULT)
            try:
                vdirectRunnable._validate_action_name()
                self.fail("WrongActionNameException was not thrown for wrong action name")
            except vdirect_runnable.WrongActionNameException:
                assert True

    def test_validate_required_action_params(self, *args):
        with patch.dict('sys.modules', **{
            'vdirect_client': self.module_mock,
            'vdirect_client.rest_client': self.module_mock,
        }):
            from ansible.modules.network.radware import vdirect_runnable

            Runnable.set_runnable_objects_result(RUNNABLE_OBJECTS_RESULT)
            BASE_PARAMS.update(RUNNABLE_PARAMS)
            BASE_PARAMS['runnable_type'] = vdirect_runnable.WORKFLOW_RUNNABLE_TYPE
            BASE_PARAMS['action_name'] = 'a'
            BASE_PARAMS['parameters'] = {"alteon": "x"}

            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable.client.runnable = Runnable(vdirectRunnable.client)
            Runnable.set_available_actions_result(AVAILABLE_ACTIONS_RESULT)
            Runnable.set_action_info_result(ACTIONS_PARAMS_RESULT)

            vdirectRunnable._validate_action_name()
            try:
                vdirectRunnable._validate_required_action_params()
                self.fail("MissingActionParametersException was not thrown for missing parameters")
            except vdirect_runnable.MissingActionParametersException:
                assert True

            BASE_PARAMS['parameters'] = {"alteon": "x"}
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable._validate_action_name()
            try:
                vdirectRunnable._validate_required_action_params()
                self.fail("MissingActionParametersException was not thrown for missing parameters")
            except vdirect_runnable.MissingActionParametersException:
                assert True

            BASE_PARAMS['parameters'] = {"pin": "x", "alteon": "x"}
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable._validate_action_name()
            vdirectRunnable._validate_required_action_params()
            assert True

    def test_run(self, *args):
        with patch.dict('sys.modules', **{
            'vdirect_client': self.module_mock,
            'vdirect_client.rest_client': self.module_mock,
        }):
            from ansible.modules.network.radware import vdirect_runnable

            Runnable.set_runnable_objects_result(RUNNABLE_OBJECTS_RESULT)

            BASE_PARAMS.update(RUNNABLE_PARAMS)

            BASE_PARAMS['runnable_type'] = vdirect_runnable.CONFIGURATION_TEMPLATE_RUNNABLE_TYPE
            BASE_PARAMS['parameters'] = {"pin": "x", "alteon": "x"}
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable.client.runnable = Runnable(vdirectRunnable.client)
            Runnable.set_available_actions_result(AVAILABLE_ACTIONS_RESULT)
            Runnable.set_action_info_result(ACTIONS_PARAMS_RESULT)
            Runnable.set_run_result(RUN_RESULT)
            res = vdirectRunnable.run()
            assert res == MODULE_RESULT

            BASE_PARAMS['runnable_type'] = vdirect_runnable.WORKFLOW_TEMPLATE_RUNNABLE_TYPE
            MODULE_RESULT['msg'] = "Workflow created."
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable.client.runnable = Runnable(vdirectRunnable.client)
            res = vdirectRunnable.run()
            assert res == MODULE_RESULT

            BASE_PARAMS['runnable_type'] = vdirect_runnable.WORKFLOW_RUNNABLE_TYPE
            BASE_PARAMS['action_name'] = 'a'
            MODULE_RESULT['msg'] = "Workflow action run completed."
            vdirectRunnable = vdirect_runnable.VdirectRunnable(BASE_PARAMS)
            vdirectRunnable.client.runnable = Runnable(vdirectRunnable.client)
            Runnable.set_available_actions_result(AVAILABLE_ACTIONS_RESULT)
            Runnable.set_action_info_result(ACTIONS_PARAMS_RESULT)
            res = vdirectRunnable.run()
            assert res == MODULE_RESULT

            result_parameters = {"param1": "value1", "param2": "value2"}
            RUN_RESULT[self.module_mock.rest_client.RESP_DATA]['parameters'] = result_parameters
            MODULE_RESULT['parameters'] = result_parameters
            res = vdirectRunnable.run()
            assert res == MODULE_RESULT

            RUN_RESULT[self.module_mock.rest_client.RESP_DATA]['status'] = 404
            vdirectRunnable.run()
            assert res == MODULE_RESULT

            RUN_RESULT[self.module_mock.rest_client.RESP_STATUS] = 400
            RUN_RESULT[self.module_mock.rest_client.RESP_REASON] = "Reason"
            RUN_RESULT[self.module_mock.rest_client.RESP_STR] = "Details"
            try:
                vdirectRunnable.run()
                self.fail("RunnableException was not thrown for failed run.")
            except vdirect_runnable.RunnableException as e:
                assert str(e) == "Reason: Reason. Details:Details."

            RUN_RESULT[self.module_mock.rest_client.RESP_STATUS] = 200
            RUN_RESULT[self.module_mock.rest_client.RESP_DATA]["status"] = 400
            RUN_RESULT[self.module_mock.rest_client.RESP_DATA]["success"] = False
            RUN_RESULT[self.module_mock.rest_client.RESP_DATA]["exception"] = {"message": "exception message"}
            try:
                vdirectRunnable.run()
                self.fail("RunnableException was not thrown for failed run.")
            except vdirect_runnable.RunnableException as e:
                assert str(e) == "Reason: exception message. Details:Details."
