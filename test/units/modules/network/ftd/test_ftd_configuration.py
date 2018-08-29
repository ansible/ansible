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

import json

import pytest

from ansible.module_utils import basic
from ansible.module_utils.network.ftd.common import HTTPMethod, FtdConfigurationError, FtdServerError
from ansible.modules.network.ftd import ftd_configuration
from units.modules.utils import set_module_args, exit_json, fail_json, AnsibleFailJson, AnsibleExitJson

ADD_RESPONSE = {'status': 'Object added'}
EDIT_RESPONSE = {'status': 'Object edited'}
DELETE_RESPONSE = {'status': 'Object deleted'}
GET_BY_FILTER_RESPONSE = [{'name': 'foo', 'description': 'bar'}]
ARBITRARY_RESPONSE = {'status': 'Arbitrary request sent'}


class TestFtdConfiguration(object):
    module = ftd_configuration

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_configuration.Connection')
        connection_instance = connection_class_mock.return_value
        connection_instance.validate_data.return_value = True, None
        connection_instance.validate_query_params.return_value = True, None
        connection_instance.validate_path_params.return_value = True, None

        return connection_instance

    @pytest.fixture
    def resource_mock(self, mocker):
        resource_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_configuration.BaseConfigurationResource')
        resource_instance = resource_class_mock.return_value
        resource_instance.add_object.return_value = ADD_RESPONSE
        resource_instance.edit_object.return_value = EDIT_RESPONSE
        resource_instance.delete_object.return_value = DELETE_RESPONSE
        resource_instance.send_request.return_value = ARBITRARY_RESPONSE
        resource_instance.get_objects_by_filter.return_value = GET_BY_FILTER_RESPONSE
        return resource_instance

    def test_module_should_fail_without_operation_arg(self):
        set_module_args({})

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        assert 'missing required arguments: operation' in str(ex)

    def test_module_should_fail_when_no_operation_spec_found(self, connection_mock):
        connection_mock.get_operation_spec.return_value = None
        set_module_args({'operation': 'nonExistingOperation'})

        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        assert 'Invalid operation name provided: nonExistingOperation' in str(ex)

    def test_module_should_add_object_when_add_operation(self, connection_mock, resource_mock):
        connection_mock.get_operation_spec.return_value = {
            'method': HTTPMethod.POST,
            'url': '/object'
        }

        params = {
            'operation': 'addObject',
            'data': {'name': 'testObject', 'type': 'object'}
        }
        result = self._run_module(params)

        assert ADD_RESPONSE == result['response']
        resource_mock.add_object.assert_called_with(connection_mock.get_operation_spec.return_value['url'],
                                                    params['data'], None, None)

    def test_module_should_edit_object_when_edit_operation(self, connection_mock, resource_mock):
        connection_mock.get_operation_spec.return_value = {
            'method': HTTPMethod.PUT,
            'url': '/object/{objId}'
        }

        params = {
            'operation': 'editObject',
            'data': {'id': '123', 'name': 'testObject', 'type': 'object'},
            'path_params': {'objId': '123'}
        }
        result = self._run_module(params)

        assert EDIT_RESPONSE == result['response']
        resource_mock.edit_object.assert_called_with(connection_mock.get_operation_spec.return_value['url'],
                                                     params['data'],
                                                     params['path_params'], None)

    def test_module_should_delete_object_when_delete_operation(self, connection_mock, resource_mock):
        connection_mock.get_operation_spec.return_value = {
            'method': HTTPMethod.DELETE,
            'url': '/object/{objId}'
        }

        params = {
            'operation': 'deleteObject',
            'path_params': {'objId': '123'}
        }
        result = self._run_module(params)

        assert DELETE_RESPONSE == result['response']
        resource_mock.delete_object.assert_called_with(connection_mock.get_operation_spec.return_value['url'],
                                                       params['path_params'])

    def test_module_should_get_objects_by_filter_when_find_by_filter_operation(self, connection_mock, resource_mock):
        connection_mock.get_operation_spec.return_value = {
            'method': HTTPMethod.GET,
            'url': '/objects'
        }

        params = {
            'operation': 'getObjectList',
            'filters': {'name': 'foo'}
        }
        result = self._run_module(params)

        assert GET_BY_FILTER_RESPONSE == result['response']
        resource_mock.get_objects_by_filter.assert_called_with(connection_mock.get_operation_spec.return_value['url'],
                                                               params['filters'],
                                                               None, None)

    def test_module_should_send_request_when_arbitrary_operation(self, connection_mock, resource_mock):
        connection_mock.get_operation_spec.return_value = {
            'method': HTTPMethod.GET,
            'url': '/object/status/{objId}'
        }

        params = {
            'operation': 'checkStatus',
            'path_params': {'objId': '123'}
        }
        result = self._run_module(params)

        assert ARBITRARY_RESPONSE == result['response']
        resource_mock.send_request.assert_called_with(connection_mock.get_operation_spec.return_value['url'],
                                                      HTTPMethod.GET, None,
                                                      params['path_params'], None)

    def test_module_should_fail_when_operation_raises_configuration_error(self, connection_mock, resource_mock):
        connection_mock.get_operation_spec.return_value = {'method': HTTPMethod.GET, 'url': '/test'}
        resource_mock.send_request.side_effect = FtdConfigurationError('Foo error.')

        result = self._run_module_with_fail_json({'operation': 'failure'})
        assert result['failed']
        assert 'Failed to execute failure operation because of the configuration error: Foo error.' == result['msg']

    def test_module_should_fail_when_operation_raises_server_error(self, connection_mock, resource_mock):
        connection_mock.get_operation_spec.return_value = {'method': HTTPMethod.GET, 'url': '/test'}
        resource_mock.send_request.side_effect = FtdServerError({'error': 'foo'}, 500)

        result = self._run_module_with_fail_json({'operation': 'failure'})
        assert result['failed']
        assert 'Server returned an error trying to execute failure operation. Status code: 500. ' \
               'Server response: {\'error\': \'foo\'}' == result['msg']

    def test_module_should_fail_if_validation_error_in_data(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {'method': HTTPMethod.POST, 'url': '/test'}
        report = {
            'required': ['objects[0].type'],
            'invalid_type': [
                {
                    'path': 'objects[3].id',
                    'expected_type': 'string',
                    'actually_value': 1
                }
            ]
        }
        connection_mock.validate_data.return_value = (False, json.dumps(report, sort_keys=True, indent=4))

        result = self._run_module_with_fail_json({
            'operation': 'test',
            'data': {}
        })
        key = 'Invalid data provided'
        assert result['msg'][key]
        result['msg'][key] = json.loads(result['msg'][key])
        assert result == {
            'msg':
                {key: {
                    'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
                    'required': ['objects[0].type']
                }},
            'failed': True}

    def test_module_should_fail_if_validation_error_in_query_params(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {'method': HTTPMethod.GET, 'url': '/test'}
        report = {
            'required': ['objects[0].type'],
            'invalid_type': [
                {
                    'path': 'objects[3].id',
                    'expected_type': 'string',
                    'actually_value': 1
                }
            ]
        }
        connection_mock.validate_query_params.return_value = (False, json.dumps(report, sort_keys=True, indent=4))

        result = self._run_module_with_fail_json({
            'operation': 'test',
            'data': {}
        })
        key = 'Invalid query_params provided'
        assert result['msg'][key]
        result['msg'][key] = json.loads(result['msg'][key])

        assert result == {'msg': {key: {
            'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
            'required': ['objects[0].type']}}, 'failed': True}

    def test_module_should_fail_if_validation_error_in_path_params(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {'method': HTTPMethod.GET, 'url': '/test'}
        report = {
            'path_params': {
                'required': ['objects[0].type'],
                'invalid_type': [
                    {
                        'path': 'objects[3].id',
                        'expected_type': 'string',
                        'actually_value': 1
                    }
                ]
            }
        }
        connection_mock.validate_path_params.return_value = (False, json.dumps(report, sort_keys=True, indent=4))

        result = self._run_module_with_fail_json({
            'operation': 'test',
            'data': {}
        })
        key = 'Invalid path_params provided'
        assert result['msg'][key]
        result['msg'][key] = json.loads(result['msg'][key])

        assert result == {'msg': {key: {
            'path_params': {
                'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
                'required': ['objects[0].type']}}}, 'failed': True}

    def test_module_should_fail_if_validation_error_in_all_params(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {'method': HTTPMethod.POST, 'url': '/test'}
        report = {
            'data': {
                'required': ['objects[0].type'],
                'invalid_type': [
                    {
                        'path': 'objects[3].id',
                        'expected_type': 'string',
                        'actually_value': 1
                    }
                ]
            },
            'path_params': {
                'required': ['some_param'],
                'invalid_type': [
                    {
                        'path': 'name',
                        'expected_type': 'string',
                        'actually_value': True
                    }
                ]
            },
            'query_params': {
                'required': ['other_param'],
                'invalid_type': [
                    {
                        'path': 'f_integer',
                        'expected_type': 'integer',
                        'actually_value': "test"
                    }
                ]
            }
        }
        connection_mock.validate_data.return_value = (False, json.dumps(report['data'], sort_keys=True, indent=4))
        connection_mock.validate_query_params.return_value = (False,
                                                              json.dumps(report['query_params'], sort_keys=True,
                                                                         indent=4))
        connection_mock.validate_path_params.return_value = (False,
                                                             json.dumps(report['path_params'], sort_keys=True,
                                                                        indent=4))

        result = self._run_module_with_fail_json({
            'operation': 'test',
            'data': {}
        })
        key_data = 'Invalid data provided'
        assert result['msg'][key_data]
        result['msg'][key_data] = json.loads(result['msg'][key_data])

        key_path_params = 'Invalid path_params provided'
        assert result['msg'][key_path_params]
        result['msg'][key_path_params] = json.loads(result['msg'][key_path_params])

        key_query_params = 'Invalid query_params provided'
        assert result['msg'][key_query_params]
        result['msg'][key_query_params] = json.loads(result['msg'][key_query_params])

        assert result == {'msg': {
            key_data: {'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
                       'required': ['objects[0].type']},
            key_path_params: {'invalid_type': [{'actually_value': True, 'expected_type': 'string', 'path': 'name'}],
                              'required': ['some_param']},
            key_query_params: {
                'invalid_type': [{'actually_value': 'test', 'expected_type': 'integer', 'path': 'f_integer'}],
                'required': ['other_param']}}, 'failed': True}

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
