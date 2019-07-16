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

import json
import unittest

import pytest
from units.compat import mock
from units.compat.mock import call, patch

from ansible.module_utils.network.ftd.common import HTTPMethod, FtdUnexpectedResponse
from ansible.module_utils.network.ftd.configuration import iterate_over_pageable_resource, BaseConfigurationResource, \
    OperationChecker, OperationNamePrefix, ParamName, QueryParams
from ansible.module_utils.network.ftd.fdm_swagger_client import ValidationError, OperationField


class TestBaseConfigurationResource(object):
    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_configuration.Connection')
        connection_instance = connection_class_mock.return_value
        connection_instance.validate_data.return_value = True, None
        connection_instance.validate_query_params.return_value = True, None
        connection_instance.validate_path_params.return_value = True, None

        return connection_instance

    @patch.object(BaseConfigurationResource, '_send_request')
    def test_get_objects_by_filter_with_multiple_filters(self, send_request_mock, connection_mock):
        objects = [
            {'name': 'obj1', 'type': 1, 'foo': {'bar': 'buzz'}},
            {'name': 'obj2', 'type': 1, 'foo': {'bar': 'buz'}},
            {'name': 'obj3', 'type': 2, 'foo': {'bar': 'buzz'}}
        ]
        connection_mock.get_operation_spec.return_value = {
            'method': HTTPMethod.GET,
            'url': '/object/'
        }
        resource = BaseConfigurationResource(connection_mock, False)

        send_request_mock.side_effect = [{'items': objects}, {'items': []}]
        # resource.get_objects_by_filter returns generator so to be able compare generated list with expected list
        # we need evaluate it.
        assert objects == list(resource.get_objects_by_filter('test', {}))
        send_request_mock.assert_has_calls(
            [
                mock.call('/object/', 'get', {}, {}, {'limit': 10, 'offset': 0})
            ]
        )

        send_request_mock.reset_mock()
        send_request_mock.side_effect = [{'items': objects}, {'items': []}]
        # resource.get_objects_by_filter returns generator so to be able compare generated list with expected list
        # we need evaluate it.
        assert [objects[0]] == list(resource.get_objects_by_filter('test', {ParamName.FILTERS: {'name': 'obj1'}}))
        send_request_mock.assert_has_calls(
            [
                mock.call('/object/', 'get', {}, {}, {QueryParams.FILTER: 'name:obj1', 'limit': 10, 'offset': 0})
            ]
        )

        send_request_mock.reset_mock()
        send_request_mock.side_effect = [{'items': objects}, {'items': []}]
        # resource.get_objects_by_filter returns generator so to be able compare generated list with expected list
        # we need evaluate it.
        assert [objects[1]] == list(resource.get_objects_by_filter(
            'test',
            {ParamName.FILTERS: {'name': 'obj2', 'type': 1, 'foo': {'bar': 'buz'}}}))

        send_request_mock.assert_has_calls(
            [
                mock.call('/object/', 'get', {}, {}, {QueryParams.FILTER: 'name:obj2', 'limit': 10, 'offset': 0})
            ]
        )

    @patch.object(BaseConfigurationResource, '_send_request')
    def test_get_objects_by_filter_with_multiple_responses(self, send_request_mock, connection_mock):
        send_request_mock.side_effect = [
            {'items': [
                {'name': 'obj1', 'type': 'foo'},
                {'name': 'obj2', 'type': 'bar'}
            ]},
            {'items': [
                {'name': 'obj3', 'type': 'foo'}
            ]},
            {'items': []}
        ]
        connection_mock.get_operation_spec.return_value = {
            'method': HTTPMethod.GET,
            'url': '/object/'
        }
        resource = BaseConfigurationResource(connection_mock, False)
        assert [{'name': 'obj1', 'type': 'foo'}] == list(resource.get_objects_by_filter(
            'test',
            {ParamName.FILTERS: {'type': 'foo'}}))
        send_request_mock.assert_has_calls(
            [
                mock.call('/object/', 'get', {}, {}, {'limit': 10, 'offset': 0})
            ]
        )

        send_request_mock.reset_mock()
        send_request_mock.side_effect = [
            {'items': [
                {'name': 'obj1', 'type': 'foo'},
                {'name': 'obj2', 'type': 'bar'}
            ]},
            {'items': [
                {'name': 'obj3', 'type': 'foo'}
            ]},
            {'items': []}
        ]
        resp = list(resource.get_objects_by_filter(
            'test',
            {
                ParamName.FILTERS: {'type': 'foo'},
                ParamName.QUERY_PARAMS: {'limit': 2}
            }))
        assert [{'name': 'obj1', 'type': 'foo'}, {'name': 'obj3', 'type': 'foo'}] == resp
        send_request_mock.assert_has_calls(
            [
                mock.call('/object/', 'get', {}, {}, {'limit': 2, 'offset': 0}),
                mock.call('/object/', 'get', {}, {}, {'limit': 2, 'offset': 2})
            ]
        )

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

        with pytest.raises(ValidationError) as e_info:
            resource = BaseConfigurationResource(connection_mock, False)
            resource.crud_operation('addTest', {'data': {}})

        result = e_info.value.args[0]
        key = 'Invalid data provided'
        assert result[key]
        result[key] = json.loads(result[key])
        assert result == {key: {
            'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
            'required': ['objects[0].type']
        }}

    def test_module_should_fail_if_validation_error_in_query_params(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {'method': HTTPMethod.GET, 'url': '/test',
                                                           'returnMultipleItems': False}
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

        with pytest.raises(ValidationError) as e_info:
            resource = BaseConfigurationResource(connection_mock, False)
            resource.crud_operation('getTestList', {'data': {}})

        result = e_info.value.args[0]

        key = 'Invalid query_params provided'
        assert result[key]
        result[key] = json.loads(result[key])

        assert result == {key: {
            'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
            'required': ['objects[0].type']}}

    def test_module_should_fail_if_validation_error_in_path_params(self, connection_mock):
        connection_mock.get_operation_spec.return_value = {'method': HTTPMethod.GET, 'url': '/test',
                                                           'returnMultipleItems': False}
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

        with pytest.raises(ValidationError) as e_info:
            resource = BaseConfigurationResource(connection_mock, False)
            resource.crud_operation('putTest', {'data': {}})

        result = e_info.value.args[0]

        key = 'Invalid path_params provided'
        assert result[key]
        result[key] = json.loads(result[key])

        assert result == {key: {
            'path_params': {
                'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
                'required': ['objects[0].type']}}}

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

        with pytest.raises(ValidationError) as e_info:
            resource = BaseConfigurationResource(connection_mock, False)
            resource.crud_operation('putTest', {'data': {}})

        result = e_info.value.args[0]

        key_data = 'Invalid data provided'
        assert result[key_data]
        result[key_data] = json.loads(result[key_data])

        key_path_params = 'Invalid path_params provided'
        assert result[key_path_params]
        result[key_path_params] = json.loads(result[key_path_params])

        key_query_params = 'Invalid query_params provided'
        assert result[key_query_params]
        result[key_query_params] = json.loads(result[key_query_params])

        assert result == {
            key_data: {'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
                       'required': ['objects[0].type']},
            key_path_params: {'invalid_type': [{'actually_value': True, 'expected_type': 'string', 'path': 'name'}],
                              'required': ['some_param']},
            key_query_params: {
                'invalid_type': [{'actually_value': 'test', 'expected_type': 'integer', 'path': 'f_integer'}],
                'required': ['other_param']}}


class TestIterateOverPageableResource(object):

    def test_iterate_over_pageable_resource_with_no_items(self):
        resource_func = mock.Mock(return_value={'items': []})

        items = iterate_over_pageable_resource(resource_func, {'query_params': {}})

        assert [] == list(items)

    def test_iterate_over_pageable_resource_with_one_page(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo', 'bar']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func, {'query_params': {}})

        assert ['foo', 'bar'] == list(items)
        resource_func.assert_has_calls([
            call(params={'query_params': {'offset': 0, 'limit': 10}})
        ])

    def test_iterate_over_pageable_resource_with_multiple_pages(self):
        objects = [
            {'items': ['foo']},
            {'items': ['bar']},
            {'items': ['buzz']},
            {'items': []},
        ]
        resource_func = mock.Mock(side_effect=objects)

        items = iterate_over_pageable_resource(resource_func, {'query_params': {}})
        assert ['foo'] == list(items)

        resource_func.reset_mock()
        resource_func = mock.Mock(side_effect=objects)
        items = iterate_over_pageable_resource(resource_func, {'query_params': {'limit': 1}})
        assert ['foo', 'bar', 'buzz'] == list(items)

    def test_iterate_over_pageable_resource_should_preserve_query_params(self):
        resource_func = mock.Mock(return_value={'items': []})

        items = iterate_over_pageable_resource(resource_func, {'query_params': {'filter': 'name:123'}})

        assert [] == list(items)
        resource_func.assert_called_once_with(params={'query_params': {'filter': 'name:123', 'offset': 0, 'limit': 10}})

    def test_iterate_over_pageable_resource_should_preserve_limit(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func, {'query_params': {'limit': 1}})

        assert ['foo'] == list(items)
        resource_func.assert_has_calls([
            call(params={'query_params': {'offset': 0, 'limit': 1}})
        ])

    def test_iterate_over_pageable_resource_should_preserve_offset(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func, {'query_params': {'offset': 3}})

        assert ['foo'] == list(items)
        resource_func.assert_has_calls([
            call(params={'query_params': {'offset': 3, 'limit': 10}}),
        ])

    def test_iterate_over_pageable_resource_should_pass_with_string_offset_and_limit(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo']},
            {'items': []},
        ])

        items = iterate_over_pageable_resource(resource_func, {'query_params': {'offset': '1', 'limit': '1'}})

        assert ['foo'] == list(items)
        resource_func.assert_has_calls([
            call(params={'query_params': {'offset': '1', 'limit': '1'}}),
            call(params={'query_params': {'offset': 2, 'limit': '1'}})
        ])

    def test_iterate_over_pageable_resource_raises_exception_when_server_returned_more_items_than_requested(self):
        resource_func = mock.Mock(side_effect=[
            {'items': ['foo', 'redundant_bar']},
            {'items': []},
        ])

        with pytest.raises(FtdUnexpectedResponse):
            list(iterate_over_pageable_resource(resource_func, {'query_params': {'offset': '1', 'limit': '1'}}))

        resource_func.assert_has_calls([
            call(params={'query_params': {'offset': '1', 'limit': '1'}})
        ])


class TestOperationCheckerClass(unittest.TestCase):
    def setUp(self):
        self._checker = OperationChecker

    def test_is_add_operation_positive(self):
        operation_name = OperationNamePrefix.ADD + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.POST}
        assert self._checker.is_add_operation(operation_name, operation_spec)

    def test_is_add_operation_wrong_method_in_spec(self):
        operation_name = OperationNamePrefix.ADD + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.GET}
        assert not self._checker.is_add_operation(operation_name, operation_spec)

    def test_is_add_operation_negative_wrong_operation_name(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.POST}
        assert not self._checker.is_add_operation(operation_name, operation_spec)

    def test_is_edit_operation_positive(self):
        operation_name = OperationNamePrefix.EDIT + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.PUT}
        assert self._checker.is_edit_operation(operation_name, operation_spec)

    def test_is_edit_operation_wrong_method_in_spec(self):
        operation_name = OperationNamePrefix.EDIT + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.GET}
        assert not self._checker.is_edit_operation(operation_name, operation_spec)

    def test_is_edit_operation_negative_wrong_operation_name(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.PUT}
        assert not self._checker.is_edit_operation(operation_name, operation_spec)

    def test_is_delete_operation_positive(self):
        operation_name = OperationNamePrefix.DELETE + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.DELETE}
        self.assertTrue(
            self._checker.is_delete_operation(operation_name, operation_spec)
        )

    def test_is_delete_operation_wrong_method_in_spec(self):
        operation_name = OperationNamePrefix.DELETE + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.GET}
        assert not self._checker.is_delete_operation(operation_name, operation_spec)

    def test_is_delete_operation_negative_wrong_operation_name(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {OperationField.METHOD: HTTPMethod.DELETE}
        assert not self._checker.is_delete_operation(operation_name, operation_spec)

    def test_is_get_list_operation_positive(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.RETURN_MULTIPLE_ITEMS: True
        }
        assert self._checker.is_get_list_operation(operation_name, operation_spec)

    def test_is_get_list_operation_wrong_method_in_spec(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {
            OperationField.METHOD: HTTPMethod.POST,
            OperationField.RETURN_MULTIPLE_ITEMS: True
        }
        assert not self._checker.is_get_list_operation(operation_name, operation_spec)

    def test_is_get_list_operation_does_not_return_list(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.RETURN_MULTIPLE_ITEMS: False
        }
        assert not self._checker.is_get_list_operation(operation_name, operation_spec)

    def test_is_get_operation_positive(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.RETURN_MULTIPLE_ITEMS: False
        }
        self.assertTrue(
            self._checker.is_get_operation(operation_name, operation_spec)
        )

    def test_is_get_operation_wrong_method_in_spec(self):
        operation_name = OperationNamePrefix.ADD + "Object"
        operation_spec = {
            OperationField.METHOD: HTTPMethod.POST,
            OperationField.RETURN_MULTIPLE_ITEMS: False
        }
        assert not self._checker.is_get_operation(operation_name, operation_spec)

    def test_is_get_operation_negative_when_returns_multiple(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.RETURN_MULTIPLE_ITEMS: True
        }
        assert not self._checker.is_get_operation(operation_name, operation_spec)

    def test_is_upsert_operation_positive(self):
        operation_name = OperationNamePrefix.UPSERT + "Object"
        assert self._checker.is_upsert_operation(operation_name)

    def test_is_upsert_operation_with_wrong_operation_name(self):
        for op_type in [OperationNamePrefix.ADD, OperationNamePrefix.GET, OperationNamePrefix.EDIT,
                        OperationNamePrefix.DELETE]:
            operation_name = op_type + "Object"
            assert not self._checker.is_upsert_operation(operation_name)

    def test_is_find_by_filter_operation(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.RETURN_MULTIPLE_ITEMS: True
        }
        params = {ParamName.FILTERS: 1}
        self.assertTrue(
            self._checker.is_find_by_filter_operation(
                operation_name, params, operation_spec
            )
        )

    def test_is_find_by_filter_operation_negative_when_filters_empty(self):
        operation_name = OperationNamePrefix.GET + "Object"
        operation_spec = {
            OperationField.METHOD: HTTPMethod.GET,
            OperationField.RETURN_MULTIPLE_ITEMS: True
        }
        params = {ParamName.FILTERS: None}
        assert not self._checker.is_find_by_filter_operation(
            operation_name, params, operation_spec
        )

        params = {}
        assert not self._checker.is_find_by_filter_operation(
            operation_name, params, operation_spec
        )

    def test_is_upsert_operation_supported_operation(self):
        get_list_op_spec = {OperationField.METHOD: HTTPMethod.GET, OperationField.RETURN_MULTIPLE_ITEMS: True}
        add_op_spec = {OperationField.METHOD: HTTPMethod.POST}
        edit_op_spec = {OperationField.METHOD: HTTPMethod.PUT}

        assert self._checker.is_upsert_operation_supported({'getList': get_list_op_spec, 'edit': edit_op_spec})
        assert self._checker.is_upsert_operation_supported(
            {'add': add_op_spec, 'getList': get_list_op_spec, 'edit': edit_op_spec})
        assert not self._checker.is_upsert_operation_supported({'getList': get_list_op_spec})
        assert not self._checker.is_upsert_operation_supported({'edit': edit_op_spec})
        assert not self._checker.is_upsert_operation_supported({'getList': get_list_op_spec, 'add': add_op_spec})
