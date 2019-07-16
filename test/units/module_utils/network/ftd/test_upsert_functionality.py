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

import copy
import json
import unittest

import pytest
from units.compat import mock

from ansible.module_utils.network.ftd.common import FtdServerError, HTTPMethod, ResponseParams, FtdConfigurationError
from ansible.module_utils.network.ftd.configuration import DUPLICATE_NAME_ERROR_MESSAGE, UNPROCESSABLE_ENTITY_STATUS, \
    MULTIPLE_DUPLICATES_FOUND_ERROR, BaseConfigurationResource, FtdInvalidOperationNameError, QueryParams, \
    ADD_OPERATION_NOT_SUPPORTED_ERROR, ParamName
from ansible.module_utils.network.ftd.fdm_swagger_client import ValidationError

ADD_RESPONSE = {'status': 'Object added'}
EDIT_RESPONSE = {'status': 'Object edited'}
DELETE_RESPONSE = {'status': 'Object deleted'}
GET_BY_FILTER_RESPONSE = [{'name': 'foo', 'description': 'bar'}]
ARBITRARY_RESPONSE = {'status': 'Arbitrary request sent'}


class TestUpsertOperationUnitTests(unittest.TestCase):
    def setUp(self):
        self._conn = mock.MagicMock()
        self._resource = BaseConfigurationResource(self._conn)

    def test_get_operation_name(self):
        operation_a = mock.MagicMock()
        operation_b = mock.MagicMock()

        def checker_wrapper(expected_object):
            def checker(obj, *args, **kwargs):
                return obj == expected_object

            return checker

        operations = {
            operation_a: "spec",
            operation_b: "spec"
        }

        assert operation_a == self._resource._get_operation_name(checker_wrapper(operation_a), operations)
        assert operation_b == self._resource._get_operation_name(checker_wrapper(operation_b), operations)
        assert self._resource._get_operation_name(checker_wrapper(None), operations) is None

    @mock.patch.object(BaseConfigurationResource, "_get_operation_name")
    @mock.patch.object(BaseConfigurationResource, "add_object")
    def test_add_upserted_object(self, add_object_mock, get_operation_mock):
        model_operations = mock.MagicMock()
        params = mock.MagicMock()
        add_op_name = get_operation_mock.return_value

        assert add_object_mock.return_value == self._resource._add_upserted_object(model_operations, params)

        get_operation_mock.assert_called_once_with(
            self._resource._operation_checker.is_add_operation,
            model_operations)
        add_object_mock.assert_called_once_with(add_op_name, params)

    @mock.patch.object(BaseConfigurationResource, "_get_operation_name")
    @mock.patch.object(BaseConfigurationResource, "add_object")
    def test_add_upserted_object_with_no_add_operation(self, add_object_mock, get_operation_mock):
        model_operations = mock.MagicMock()
        get_operation_mock.return_value = None

        with pytest.raises(FtdConfigurationError) as exc_info:
            self._resource._add_upserted_object(model_operations, mock.MagicMock())
        assert ADD_OPERATION_NOT_SUPPORTED_ERROR in str(exc_info.value)

        get_operation_mock.assert_called_once_with(self._resource._operation_checker.is_add_operation, model_operations)
        add_object_mock.assert_not_called()

    @mock.patch.object(BaseConfigurationResource, "_get_operation_name")
    @mock.patch.object(BaseConfigurationResource, "edit_object")
    @mock.patch("ansible.module_utils.network.ftd.configuration.copy_identity_properties")
    @mock.patch("ansible.module_utils.network.ftd.configuration._set_default")
    def test_edit_upserted_object(self, _set_default_mock, copy_properties_mock, edit_object_mock, get_operation_mock):
        model_operations = mock.MagicMock()
        existing_object = mock.MagicMock()
        params = {
            'path_params': {},
            'data': {}
        }

        result = self._resource._edit_upserted_object(model_operations, existing_object, params)

        assert result == edit_object_mock.return_value

        _set_default_mock.assert_has_calls([
            mock.call(params, 'path_params', {}),
            mock.call(params, 'data', {})
        ])
        get_operation_mock.assert_called_once_with(
            self._resource._operation_checker.is_edit_operation,
            model_operations
        )
        copy_properties_mock.assert_called_once_with(
            existing_object,
            params['data']
        )
        edit_object_mock.assert_called_once_with(
            get_operation_mock.return_value,
            params
        )

    @mock.patch("ansible.module_utils.network.ftd.configuration.OperationChecker.is_upsert_operation_supported")
    @mock.patch.object(BaseConfigurationResource, "get_operation_specs_by_model_name")
    @mock.patch.object(BaseConfigurationResource, "_find_object_matching_params")
    @mock.patch.object(BaseConfigurationResource, "_add_upserted_object")
    @mock.patch.object(BaseConfigurationResource, "_edit_upserted_object")
    def test_upsert_object_successfully_added(self, edit_mock, add_mock, find_object, get_operation_mock,
                                              is_upsert_supported_mock):
        params = mock.MagicMock()

        is_upsert_supported_mock.return_value = True
        find_object.return_value = None

        result = self._resource.upsert_object('upsertFoo', params)

        assert result == add_mock.return_value
        self._conn.get_model_spec.assert_called_once_with('Foo')
        is_upsert_supported_mock.assert_called_once_with(get_operation_mock.return_value)
        get_operation_mock.assert_called_once_with('Foo')
        find_object.assert_called_once_with('Foo', params)
        add_mock.assert_called_once_with(get_operation_mock.return_value, params)
        edit_mock.assert_not_called()

    @mock.patch("ansible.module_utils.network.ftd.configuration.equal_objects")
    @mock.patch("ansible.module_utils.network.ftd.configuration.OperationChecker.is_upsert_operation_supported")
    @mock.patch.object(BaseConfigurationResource, "get_operation_specs_by_model_name")
    @mock.patch.object(BaseConfigurationResource, "_find_object_matching_params")
    @mock.patch.object(BaseConfigurationResource, "_add_upserted_object")
    @mock.patch.object(BaseConfigurationResource, "_edit_upserted_object")
    def test_upsert_object_successfully_edited(self, edit_mock, add_mock, find_object, get_operation_mock,
                                               is_upsert_supported_mock, equal_objects_mock):
        params = mock.MagicMock()
        existing_obj = mock.MagicMock()

        is_upsert_supported_mock.return_value = True
        find_object.return_value = existing_obj
        equal_objects_mock.return_value = False

        result = self._resource.upsert_object('upsertFoo', params)

        assert result == edit_mock.return_value
        self._conn.get_model_spec.assert_called_once_with('Foo')
        get_operation_mock.assert_called_once_with('Foo')
        is_upsert_supported_mock.assert_called_once_with(get_operation_mock.return_value)
        add_mock.assert_not_called()
        equal_objects_mock.assert_called_once_with(existing_obj, params[ParamName.DATA])
        edit_mock.assert_called_once_with(get_operation_mock.return_value, existing_obj, params)

    @mock.patch("ansible.module_utils.network.ftd.configuration.equal_objects")
    @mock.patch("ansible.module_utils.network.ftd.configuration.OperationChecker.is_upsert_operation_supported")
    @mock.patch.object(BaseConfigurationResource, "get_operation_specs_by_model_name")
    @mock.patch.object(BaseConfigurationResource, "_find_object_matching_params")
    @mock.patch.object(BaseConfigurationResource, "_add_upserted_object")
    @mock.patch.object(BaseConfigurationResource, "_edit_upserted_object")
    def test_upsert_object_returned_without_modifications(self, edit_mock, add_mock, find_object, get_operation_mock,
                                                          is_upsert_supported_mock, equal_objects_mock):
        params = mock.MagicMock()
        existing_obj = mock.MagicMock()

        is_upsert_supported_mock.return_value = True
        find_object.return_value = existing_obj
        equal_objects_mock.return_value = True

        result = self._resource.upsert_object('upsertFoo', params)

        assert result == existing_obj
        self._conn.get_model_spec.assert_called_once_with('Foo')
        get_operation_mock.assert_called_once_with('Foo')
        is_upsert_supported_mock.assert_called_once_with(get_operation_mock.return_value)
        add_mock.assert_not_called()
        equal_objects_mock.assert_called_once_with(existing_obj, params[ParamName.DATA])
        edit_mock.assert_not_called()

    @mock.patch("ansible.module_utils.network.ftd.configuration.OperationChecker.is_upsert_operation_supported")
    @mock.patch.object(BaseConfigurationResource, "get_operation_specs_by_model_name")
    @mock.patch.object(BaseConfigurationResource, "_find_object_matching_params")
    @mock.patch.object(BaseConfigurationResource, "_add_upserted_object")
    @mock.patch.object(BaseConfigurationResource, "_edit_upserted_object")
    def test_upsert_object_not_supported(self, edit_mock, add_mock, find_object, get_operation_mock,
                                         is_upsert_supported_mock):
        params = mock.MagicMock()

        is_upsert_supported_mock.return_value = False

        self.assertRaises(
            FtdInvalidOperationNameError,
            self._resource.upsert_object, 'upsertFoo', params
        )

        self._conn.get_model_spec.assert_called_once_with('Foo')
        get_operation_mock.assert_called_once_with('Foo')
        is_upsert_supported_mock.assert_called_once_with(get_operation_mock.return_value)
        find_object.assert_not_called()
        add_mock.assert_not_called()
        edit_mock.assert_not_called()

    @mock.patch("ansible.module_utils.network.ftd.configuration.OperationChecker.is_upsert_operation_supported")
    @mock.patch.object(BaseConfigurationResource, "get_operation_specs_by_model_name")
    @mock.patch.object(BaseConfigurationResource, "_find_object_matching_params")
    @mock.patch.object(BaseConfigurationResource, "_add_upserted_object")
    @mock.patch.object(BaseConfigurationResource, "_edit_upserted_object")
    def test_upsert_object_when_model_not_supported(self, edit_mock, add_mock, find_object, get_operation_mock,
                                                    is_upsert_supported_mock):
        params = mock.MagicMock()
        self._conn.get_model_spec.return_value = None

        self.assertRaises(
            FtdInvalidOperationNameError,
            self._resource.upsert_object, 'upsertNonExisting', params
        )

        self._conn.get_model_spec.assert_called_once_with('NonExisting')
        get_operation_mock.assert_not_called()
        is_upsert_supported_mock.assert_not_called()
        find_object.assert_not_called()
        add_mock.assert_not_called()
        edit_mock.assert_not_called()

    @mock.patch("ansible.module_utils.network.ftd.configuration.equal_objects")
    @mock.patch("ansible.module_utils.network.ftd.configuration.OperationChecker.is_upsert_operation_supported")
    @mock.patch.object(BaseConfigurationResource, "get_operation_specs_by_model_name")
    @mock.patch.object(BaseConfigurationResource, "_find_object_matching_params")
    @mock.patch.object(BaseConfigurationResource, "_add_upserted_object")
    @mock.patch.object(BaseConfigurationResource, "_edit_upserted_object")
    def test_upsert_object_with_fatal_error_during_edit(self, edit_mock, add_mock, find_object, get_operation_mock,
                                                        is_upsert_supported_mock, equal_objects_mock):
        params = mock.MagicMock()
        existing_obj = mock.MagicMock()

        is_upsert_supported_mock.return_value = True
        find_object.return_value = existing_obj
        equal_objects_mock.return_value = False
        edit_mock.side_effect = FtdConfigurationError("Some object edit error")

        self.assertRaises(
            FtdConfigurationError,
            self._resource.upsert_object, 'upsertFoo', params
        )

        is_upsert_supported_mock.assert_called_once_with(get_operation_mock.return_value)
        self._conn.get_model_spec.assert_called_once_with('Foo')
        get_operation_mock.assert_called_once_with('Foo')
        find_object.assert_called_once_with('Foo', params)
        add_mock.assert_not_called()
        edit_mock.assert_called_once_with(get_operation_mock.return_value, existing_obj, params)

    @mock.patch("ansible.module_utils.network.ftd.configuration.OperationChecker.is_upsert_operation_supported")
    @mock.patch.object(BaseConfigurationResource, "get_operation_specs_by_model_name")
    @mock.patch.object(BaseConfigurationResource, "_find_object_matching_params")
    @mock.patch.object(BaseConfigurationResource, "_add_upserted_object")
    @mock.patch.object(BaseConfigurationResource, "_edit_upserted_object")
    def test_upsert_object_with_fatal_error_during_add(self, edit_mock, add_mock, find_object, get_operation_mock,
                                                       is_upsert_supported_mock):
        params = mock.MagicMock()

        is_upsert_supported_mock.return_value = True
        find_object.return_value = None

        error = FtdConfigurationError("Obj duplication error")
        add_mock.side_effect = error

        self.assertRaises(
            FtdConfigurationError,
            self._resource.upsert_object, 'upsertFoo', params
        )

        is_upsert_supported_mock.assert_called_once_with(get_operation_mock.return_value)
        self._conn.get_model_spec.assert_called_once_with('Foo')
        get_operation_mock.assert_called_once_with('Foo')
        find_object.assert_called_once_with('Foo', params)
        add_mock.assert_called_once_with(get_operation_mock.return_value, params)
        edit_mock.assert_not_called()


# functional tests below
class TestUpsertOperationFunctionalTests(object):

    @pytest.fixture(autouse=True)
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_configuration.Connection')
        connection_instance = connection_class_mock.return_value
        connection_instance.validate_data.return_value = True, None
        connection_instance.validate_query_params.return_value = True, None
        connection_instance.validate_path_params.return_value = True, None
        return connection_instance

    def test_module_should_create_object_when_upsert_operation_and_object_does_not_exist(self, connection_mock):
        url = '/test'

        operations = {
            'getObjectList': {
                'method': HTTPMethod.GET,
                'url': url,
                'modelName': 'Object',
                'returnMultipleItems': True},
            'addObject': {
                'method': HTTPMethod.POST,
                'modelName': 'Object',
                'url': url},
            'editObject': {
                'method': HTTPMethod.PUT,
                'modelName': 'Object',
                'url': '/test/{objId}'},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': '/test/{objId}',
                'returnMultipleItems': False
            }
        }

        def get_operation_spec(name):
            return operations[name]

        def request_handler(url_path=None, http_method=None, body_params=None, path_params=None, query_params=None):
            if http_method == HTTPMethod.POST:
                assert url_path == url
                assert body_params == params['data']
                assert query_params == {}
                assert path_params == params['path_params']
                return {
                    ResponseParams.SUCCESS: True,
                    ResponseParams.RESPONSE: ADD_RESPONSE
                }
            elif http_method == HTTPMethod.GET:
                return {
                    ResponseParams.SUCCESS: True,
                    ResponseParams.RESPONSE: {'items': []}
                }
            else:
                assert False

        connection_mock.get_operation_spec = get_operation_spec

        connection_mock.get_operation_specs_by_model_name.return_value = operations
        connection_mock.send_request = request_handler
        params = {
            'operation': 'upsertObject',
            'data': {'id': '123', 'name': 'testObject', 'type': 'object'},
            'path_params': {'objId': '123'},
            'register_as': 'test_var'
        }

        result = self._resource_execute_operation(params, connection=connection_mock)

        assert ADD_RESPONSE == result

    def test_module_should_fail_when_no_model(self, connection_mock):
        connection_mock.get_model_spec.return_value = None
        params = {
            'operation': 'upsertObject',
            'data': {'id': '123', 'name': 'testObject', 'type': 'object'},
            'path_params': {'objId': '123'},
            'register_as': 'test_var'
        }

        with pytest.raises(FtdInvalidOperationNameError) as exc_info:
            self._resource_execute_operation(params, connection=connection_mock)
        assert 'upsertObject' == exc_info.value.operation_name

    def test_module_should_fail_when_no_add_operation_and_no_object(self, connection_mock):
        url = '/test'

        operations = {
            'getObjectList': {
                'method': HTTPMethod.GET,
                'url': url,
                'modelName': 'Object',
                'returnMultipleItems': True},
            'editObject': {
                'method': HTTPMethod.PUT,
                'modelName': 'Object',
                'url': '/test/{objId}'},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': '/test/{objId}',
                'returnMultipleItems': False
            }}

        def get_operation_spec(name):
            return operations[name]

        connection_mock.get_operation_spec = get_operation_spec

        connection_mock.get_operation_specs_by_model_name.return_value = operations
        connection_mock.send_request.return_value = {
            ResponseParams.SUCCESS: True,
            ResponseParams.RESPONSE: {'items': []}
        }
        params = {
            'operation': 'upsertObject',
            'data': {'id': '123', 'name': 'testObject', 'type': 'object'},
            'path_params': {'objId': '123'},
            'register_as': 'test_var'
        }

        with pytest.raises(FtdConfigurationError) as exc_info:
            self._resource_execute_operation(params, connection=connection_mock)
        assert ADD_OPERATION_NOT_SUPPORTED_ERROR in str(exc_info.value)

    # test when object exists but with different fields(except id)
    def test_module_should_update_object_when_upsert_operation_and_object_exists(self, connection_mock):
        url = '/test'
        obj_id = '456'
        version = 'test_version'
        url_with_id_templ = '{0}/{1}'.format(url, '{objId}')

        new_value = '0000'
        old_value = '1111'
        params = {
            'operation': 'upsertObject',
            'data': {'name': 'testObject', 'value': new_value, 'type': 'object'},
            'register_as': 'test_var'
        }

        def request_handler(url_path=None, http_method=None, body_params=None, path_params=None, query_params=None):
            if http_method == HTTPMethod.POST:
                assert url_path == url
                assert body_params == params['data']
                assert query_params == {}
                assert path_params == {}
                return {
                    ResponseParams.SUCCESS: False,
                    ResponseParams.RESPONSE: DUPLICATE_NAME_ERROR_MESSAGE,
                    ResponseParams.STATUS_CODE: UNPROCESSABLE_ENTITY_STATUS
                }
            elif http_method == HTTPMethod.GET:
                is_get_list_req = url_path == url
                is_get_req = url_path == url_with_id_templ
                assert is_get_req or is_get_list_req

                if is_get_list_req:
                    assert body_params == {}
                    assert query_params == {QueryParams.FILTER: 'name:testObject', 'limit': 10, 'offset': 0}
                    assert path_params == {}
                elif is_get_req:
                    assert body_params == {}
                    assert query_params == {}
                    assert path_params == {'objId': obj_id}

                return {
                    ResponseParams.SUCCESS: True,
                    ResponseParams.RESPONSE: {
                        'items': [
                            {'name': 'testObject', 'value': old_value, 'type': 'object', 'id': obj_id,
                             'version': version}
                        ]
                    }
                }
            elif http_method == HTTPMethod.PUT:
                assert url_path == url_with_id_templ
                return {
                    ResponseParams.SUCCESS: True,
                    ResponseParams.RESPONSE: body_params
                }
            else:
                assert False

        operations = {
            'getObjectList': {'method': HTTPMethod.GET, 'url': url, 'modelName': 'Object', 'returnMultipleItems': True},
            'addObject': {'method': HTTPMethod.POST, 'modelName': 'Object', 'url': url},
            'editObject': {'method': HTTPMethod.PUT, 'modelName': 'Object', 'url': url_with_id_templ},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': url_with_id_templ,
                'returnMultipleItems': False}
        }

        def get_operation_spec(name):
            return operations[name]

        connection_mock.get_operation_spec = get_operation_spec
        connection_mock.get_operation_specs_by_model_name.return_value = operations

        connection_mock.send_request = request_handler
        expected_val = {'name': 'testObject', 'value': new_value, 'type': 'object', 'id': obj_id, 'version': version}

        result = self._resource_execute_operation(params, connection=connection_mock)

        assert expected_val == result

    # test when object exists and all fields have the same value
    def test_module_should_not_update_object_when_upsert_operation_and_object_exists_with_the_same_fields(
            self, connection_mock):
        url = '/test'
        url_with_id_templ = '{0}/{1}'.format(url, '{objId}')

        params = {
            'operation': 'upsertObject',
            'data': {'name': 'testObject', 'value': '3333', 'type': 'object'},
            'register_as': 'test_var'
        }

        expected_val = copy.deepcopy(params['data'])
        expected_val['version'] = 'test_version'
        expected_val['id'] = 'test_id'

        def request_handler(url_path=None, http_method=None, body_params=None, path_params=None, query_params=None):
            if http_method == HTTPMethod.POST:
                assert url_path == url
                assert body_params == params['data']
                assert query_params == {}
                assert path_params == {}
                return {
                    ResponseParams.SUCCESS: False,
                    ResponseParams.RESPONSE: DUPLICATE_NAME_ERROR_MESSAGE,
                    ResponseParams.STATUS_CODE: UNPROCESSABLE_ENTITY_STATUS
                }
            elif http_method == HTTPMethod.GET:
                assert url_path == url
                assert body_params == {}
                assert query_params == {QueryParams.FILTER: 'name:testObject', 'limit': 10, 'offset': 0}
                assert path_params == {}

                return {
                    ResponseParams.SUCCESS: True,
                    ResponseParams.RESPONSE: {
                        'items': [expected_val]
                    }
                }
            else:
                assert False

        operations = {
            'getObjectList': {'method': HTTPMethod.GET, 'modelName': 'Object', 'url': url, 'returnMultipleItems': True},
            'addObject': {'method': HTTPMethod.POST, 'modelName': 'Object', 'url': url},
            'editObject': {'method': HTTPMethod.PUT, 'modelName': 'Object', 'url': url_with_id_templ},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': url_with_id_templ,
                'returnMultipleItems': False}
        }

        def get_operation_spec(name):
            return operations[name]

        connection_mock.get_operation_spec = get_operation_spec
        connection_mock.get_operation_specs_by_model_name.return_value = operations
        connection_mock.send_request = request_handler

        result = self._resource_execute_operation(params, connection=connection_mock)

        assert expected_val == result

    def test_module_should_fail_when_upsert_operation_is_not_supported(self, connection_mock):
        connection_mock.get_operation_specs_by_model_name.return_value = {
            'addObject': {'method': HTTPMethod.POST, 'modelName': 'Object', 'url': '/test'},
            'editObject': {'method': HTTPMethod.PUT, 'modelName': 'Object', 'url': '/test/{objId}'},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': '/test/{objId}',
                'returnMultipleItems': False}
        }
        operation_name = 'upsertObject'
        params = {
            'operation': operation_name,
            'data': {'id': '123', 'name': 'testObject', 'type': 'object'},
            'path_params': {'objId': '123'},
            'register_as': 'test_var'
        }

        result = self._resource_execute_operation_with_expected_failure(
            expected_exception_class=FtdInvalidOperationNameError,
            params=params, connection=connection_mock)

        connection_mock.send_request.assert_not_called()
        assert operation_name == result.operation_name

    # when create operation raised FtdConfigurationError exception without id and version
    def test_module_should_fail_when_upsert_operation_and_failed_create_without_id_and_version(self, connection_mock):
        url = '/test'
        url_with_id_templ = '{0}/{1}'.format(url, '{objId}')

        params = {
            'operation': 'upsertObject',
            'data': {'name': 'testObject', 'value': '3333', 'type': 'object'},
            'register_as': 'test_var'
        }

        def request_handler(url_path=None, http_method=None, body_params=None, path_params=None, query_params=None):
            if http_method == HTTPMethod.POST:
                assert url_path == url
                assert body_params == params['data']
                assert query_params == {}
                assert path_params == {}
                return {
                    ResponseParams.SUCCESS: False,
                    ResponseParams.RESPONSE: DUPLICATE_NAME_ERROR_MESSAGE,
                    ResponseParams.STATUS_CODE: UNPROCESSABLE_ENTITY_STATUS
                }
            elif http_method == HTTPMethod.GET:
                assert url_path == url
                assert body_params == {}
                assert query_params == {QueryParams.FILTER: 'name:testObject', 'limit': 10, 'offset': 0}
                assert path_params == {}

                return {
                    ResponseParams.SUCCESS: True,
                    ResponseParams.RESPONSE: {
                        'items': []
                    }
                }
            else:
                assert False

        operations = {
            'getObjectList': {'method': HTTPMethod.GET, 'modelName': 'Object', 'url': url, 'returnMultipleItems': True},
            'addObject': {'method': HTTPMethod.POST, 'modelName': 'Object', 'url': url},
            'editObject': {'method': HTTPMethod.PUT, 'modelName': 'Object', 'url': url_with_id_templ},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': url_with_id_templ,
                'returnMultipleItems': False}
        }

        def get_operation_spec(name):
            return operations[name]

        connection_mock.get_operation_spec = get_operation_spec
        connection_mock.get_operation_specs_by_model_name.return_value = operations
        connection_mock.send_request = request_handler

        result = self._resource_execute_operation_with_expected_failure(
            expected_exception_class=FtdServerError,
            params=params, connection=connection_mock)

        assert result.code == 422
        assert result.response == 'Validation failed due to a duplicate name'

    def test_module_should_fail_when_upsert_operation_and_failed_update_operation(self, connection_mock):
        url = '/test'
        obj_id = '456'
        version = 'test_version'
        url_with_id_templ = '{0}/{1}'.format(url, '{objId}')

        error_code = 404

        new_value = '0000'
        old_value = '1111'
        params = {
            'operation': 'upsertObject',
            'data': {'name': 'testObject', 'value': new_value, 'type': 'object'},
            'register_as': 'test_var'
        }

        error_msg = 'test error'

        def request_handler(url_path=None, http_method=None, body_params=None, path_params=None, query_params=None):
            if http_method == HTTPMethod.POST:
                assert url_path == url
                assert body_params == params['data']
                assert query_params == {}
                assert path_params == {}
                return {
                    ResponseParams.SUCCESS: False,
                    ResponseParams.RESPONSE: DUPLICATE_NAME_ERROR_MESSAGE,
                    ResponseParams.STATUS_CODE: UNPROCESSABLE_ENTITY_STATUS
                }
            elif http_method == HTTPMethod.GET:
                is_get_list_req = url_path == url
                is_get_req = url_path == url_with_id_templ
                assert is_get_req or is_get_list_req

                if is_get_list_req:
                    assert body_params == {}
                    assert query_params == {QueryParams.FILTER: 'name:testObject', 'limit': 10, 'offset': 0}
                elif is_get_req:
                    assert body_params == {}
                    assert query_params == {}
                    assert path_params == {'objId': obj_id}

                return {
                    ResponseParams.SUCCESS: True,
                    ResponseParams.RESPONSE: {
                        'items': [
                            {'name': 'testObject', 'value': old_value, 'type': 'object', 'id': obj_id,
                             'version': version}
                        ]
                    }
                }
            elif http_method == HTTPMethod.PUT:
                assert url_path == url_with_id_templ
                raise FtdServerError(error_msg, error_code)
            else:
                assert False

        operations = {
            'getObjectList': {'method': HTTPMethod.GET, 'modelName': 'Object', 'url': url, 'returnMultipleItems': True},
            'addObject': {'method': HTTPMethod.POST, 'modelName': 'Object', 'url': url},
            'editObject': {'method': HTTPMethod.PUT, 'modelName': 'Object', 'url': url_with_id_templ},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': url_with_id_templ,
                'returnMultipleItems': False}
        }

        def get_operation_spec(name):
            return operations[name]

        connection_mock.get_operation_spec = get_operation_spec
        connection_mock.get_operation_specs_by_model_name.return_value = operations
        connection_mock.send_request = request_handler

        result = self._resource_execute_operation_with_expected_failure(
            expected_exception_class=FtdServerError,
            params=params, connection=connection_mock)

        assert result.code == error_code
        assert result.response == error_msg

    def test_module_should_fail_when_upsert_operation_and_invalid_data_for_create_operation(self, connection_mock):
        new_value = '0000'
        params = {
            'operation': 'upsertObject',
            'data': {'name': 'testObject', 'value': new_value, 'type': 'object'},
            'register_as': 'test_var'
        }

        connection_mock.send_request.assert_not_called()

        operations = {
            'getObjectList': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': 'sd',
                'returnMultipleItems': True},
            'addObject': {'method': HTTPMethod.POST, 'modelName': 'Object', 'url': 'sdf'},
            'editObject': {'method': HTTPMethod.PUT, 'modelName': 'Object', 'url': 'sadf'},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': 'sdfs',
                'returnMultipleItems': False}
        }

        def get_operation_spec(name):
            return operations[name]

        connection_mock.get_operation_spec = get_operation_spec
        connection_mock.get_operation_specs_by_model_name.return_value = operations

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
        key = 'Invalid data provided'

        result = self._resource_execute_operation_with_expected_failure(
            expected_exception_class=ValidationError,
            params=params, connection=connection_mock)

        assert len(result.args) == 1
        assert key in result.args[0]
        assert json.loads(result.args[0][key]) == {
            'invalid_type': [{'actually_value': 1, 'expected_type': 'string', 'path': 'objects[3].id'}],
            'required': ['objects[0].type']
        }

    def test_module_should_fail_when_upsert_operation_and_few_objects_found_by_filter(self, connection_mock):
        url = '/test'
        url_with_id_templ = '{0}/{1}'.format(url, '{objId}')

        sample_obj = {'name': 'testObject', 'value': '3333', 'type': 'object'}
        params = {
            'operation': 'upsertObject',
            'data': sample_obj,
            'register_as': 'test_var'
        }

        def request_handler(url_path=None, http_method=None, body_params=None, path_params=None, query_params=None):
            if http_method == HTTPMethod.POST:
                assert url_path == url
                assert body_params == params['data']
                assert query_params == {}
                assert path_params == {}
                return {
                    ResponseParams.SUCCESS: False,
                    ResponseParams.RESPONSE: DUPLICATE_NAME_ERROR_MESSAGE,
                    ResponseParams.STATUS_CODE: UNPROCESSABLE_ENTITY_STATUS
                }
            elif http_method == HTTPMethod.GET:
                assert url_path == url
                assert body_params == {}
                assert query_params == {QueryParams.FILTER: 'name:testObject', 'limit': 10, 'offset': 0}
                assert path_params == {}

                return {
                    ResponseParams.SUCCESS: True,
                    ResponseParams.RESPONSE: {
                        'items': [sample_obj, sample_obj]
                    }
                }
            else:
                assert False

        operations = {
            'getObjectList': {'method': HTTPMethod.GET, 'modelName': 'Object', 'url': url, 'returnMultipleItems': True},
            'addObject': {'method': HTTPMethod.POST, 'modelName': 'Object', 'url': url},
            'editObject': {'method': HTTPMethod.PUT, 'modelName': 'Object', 'url': url_with_id_templ},
            'otherObjectOperation': {
                'method': HTTPMethod.GET,
                'modelName': 'Object',
                'url': url_with_id_templ,
                'returnMultipleItems': False}
        }

        def get_operation_spec(name):
            return operations[name]

        connection_mock.get_operation_spec = get_operation_spec
        connection_mock.get_operation_specs_by_model_name.return_value = operations
        connection_mock.send_request = request_handler

        result = self._resource_execute_operation_with_expected_failure(
            expected_exception_class=FtdConfigurationError,
            params=params, connection=connection_mock)

        assert result.msg is MULTIPLE_DUPLICATES_FOUND_ERROR
        assert result.obj is None

    @staticmethod
    def _resource_execute_operation(params, connection):
        resource = BaseConfigurationResource(connection)
        op_name = params['operation']

        resp = resource.execute_operation(op_name, params)

        return resp

    def _resource_execute_operation_with_expected_failure(self, expected_exception_class, params, connection):
        with pytest.raises(expected_exception_class) as ex:
            self._resource_execute_operation(params, connection)
        # 'ex' here is the instance of '_pytest._code.code.ExceptionInfo' but not <expected_exception_class>
        # actual instance of <expected_exception_class> is in the value attribute of 'ex'. That's why we should return
        # 'ex.value' here, so it can be checked in a test later.
        return ex.value
