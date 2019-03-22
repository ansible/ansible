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
import copy
from functools import partial

from ansible.module_utils.network.ftd.common import HTTPMethod, equal_objects, FtdConfigurationError, \
    FtdServerError, ResponseParams, copy_identity_properties, FtdUnexpectedResponse
from ansible.module_utils.network.ftd.fdm_swagger_client import OperationField, ValidationError
from ansible.module_utils.six import iteritems

DEFAULT_PAGE_SIZE = 10
DEFAULT_OFFSET = 0

UNPROCESSABLE_ENTITY_STATUS = 422
INVALID_UUID_ERROR_MESSAGE = "Validation failed due to an invalid UUID"
DUPLICATE_NAME_ERROR_MESSAGE = "Validation failed due to a duplicate name"

MULTIPLE_DUPLICATES_FOUND_ERROR = (
    "Cannot add a new object. An object(s) with the same attributes exists."
    "Multiple objects returned according to filters being specified. "
    "Please specify more specific filters which can find exact object that caused duplication error")


class OperationNamePrefix:
    ADD = 'add'
    EDIT = 'edit'
    GET = 'get'
    DELETE = 'delete'
    UPSERT = 'upsert'


class QueryParams:
    FILTER = 'filter'


class ParamName:
    QUERY_PARAMS = 'query_params'
    PATH_PARAMS = 'path_params'
    DATA = 'data'
    FILTERS = 'filters'


class CheckModeException(Exception):
    pass


class FtdInvalidOperationNameError(Exception):
    def __init__(self, operation_name):
        super(FtdInvalidOperationNameError, self).__init__(operation_name)
        self.operation_name = operation_name


class OperationChecker(object):

    @classmethod
    def is_add_operation(cls, operation_name, operation_spec):
        """
        Check if operation defined with 'operation_name' is add object operation according to 'operation_spec'.

        :param operation_name: name of the operation being called by the user
        :type operation_name: str
        :param operation_spec: specification of the operation being called by the user
        :type operation_spec: dict
        :return: True if the called operation is add object operation, otherwise False
        :rtype: bool
        """
        # Some endpoints have non-CRUD operations, so checking operation name is required in addition to the HTTP method
        return operation_name.startswith(OperationNamePrefix.ADD) and is_post_request(operation_spec)

    @classmethod
    def is_edit_operation(cls, operation_name, operation_spec):
        """
        Check if operation defined with 'operation_name' is edit object operation according to 'operation_spec'.

        :param operation_name: name of the operation being called by the user
        :type operation_name: str
        :param operation_spec: specification of the operation being called by the user
        :type operation_spec: dict
        :return: True if the called operation is edit object operation, otherwise False
        :rtype: bool
        """
        # Some endpoints have non-CRUD operations, so checking operation name is required in addition to the HTTP method
        return operation_name.startswith(OperationNamePrefix.EDIT) and is_put_request(operation_spec)

    @classmethod
    def is_delete_operation(cls, operation_name, operation_spec):
        """
        Check if operation defined with 'operation_name' is delete object operation according to 'operation_spec'.

        :param operation_name: name of the operation being called by the user
        :type operation_name: str
        :param operation_spec: specification of the operation being called by the user
        :type operation_spec: dict
        :return: True if the called operation is delete object operation, otherwise False
        :rtype: bool
        """
        # Some endpoints have non-CRUD operations, so checking operation name is required in addition to the HTTP method
        return operation_name.startswith(OperationNamePrefix.DELETE) \
            and operation_spec[OperationField.METHOD] == HTTPMethod.DELETE

    @classmethod
    def is_get_list_operation(cls, operation_name, operation_spec):
        """
        Check if operation defined with 'operation_name' is get list of objects operation according to 'operation_spec'.

        :param operation_name: name of the operation being called by the user
        :type operation_name: str
        :param operation_spec: specification of the operation being called by the user
        :type operation_spec: dict
        :return: True if the called operation is get a list of objects operation, otherwise False
        :rtype: bool
        """
        return operation_spec[OperationField.METHOD] == HTTPMethod.GET \
            and operation_spec[OperationField.RETURN_MULTIPLE_ITEMS]

    @classmethod
    def is_get_operation(cls, operation_name, operation_spec):
        """
        Check if operation defined with 'operation_name' is get objects operation according to 'operation_spec'.

        :param operation_name: name of the operation being called by the user
        :type operation_name: str
        :param operation_spec: specification of the operation being called by the user
        :type operation_spec: dict
        :return: True if the called operation is get object operation, otherwise False
        :rtype: bool
        """
        return operation_spec[OperationField.METHOD] == HTTPMethod.GET \
            and not operation_spec[OperationField.RETURN_MULTIPLE_ITEMS]

    @classmethod
    def is_upsert_operation(cls, operation_name):
        """
        Check if operation defined with 'operation_name' is upsert objects operation according to 'operation_name'.

        :param operation_name: name of the operation being called by the user
        :type operation_name: str
        :return: True if the called operation is upsert object operation, otherwise False
        :rtype: bool
        """
        return operation_name.startswith(OperationNamePrefix.UPSERT)

    @classmethod
    def is_find_by_filter_operation(cls, operation_name, params, operation_spec):
        """
        Checks whether the called operation is 'find by filter'. This operation fetches all objects and finds
        the matching ones by the given filter. As filtering is done on the client side, this operation should be used
        only when selected filters are not implemented on the server side.

        :param operation_name: name of the operation being called by the user
        :type operation_name: str
        :param operation_spec: specification of the operation being called by the user
        :type operation_spec: dict
        :param params: params - params should contain 'filters'
        :return: True if the called operation is find by filter, otherwise False
        :rtype: bool
        """
        is_get_list = cls.is_get_list_operation(operation_name, operation_spec)
        return is_get_list and ParamName.FILTERS in params and params[ParamName.FILTERS]

    @classmethod
    def is_upsert_operation_supported(cls, operations):
        """
        Checks if all operations required for upsert object operation are defined in 'operations'.

        :param operations: specification of the operations supported by model
        :type operations: dict
        :return: True if all criteria required to provide requested called operation are satisfied, otherwise False
        :rtype: bool
        """
        amount_operations_need_for_upsert_operation = 3
        amount_supported_operations = 0
        for operation_name, operation_spec in operations.items():
            if cls.is_add_operation(operation_name, operation_spec) \
                    or cls.is_edit_operation(operation_name, operation_spec) \
                    or cls.is_get_list_operation(operation_name, operation_spec):
                amount_supported_operations += 1

        return amount_supported_operations == amount_operations_need_for_upsert_operation


class BaseConfigurationResource(object):

    def __init__(self, conn, check_mode=False):
        self._conn = conn
        self.config_changed = False
        self._operation_spec_cache = {}
        self._models_operations_specs_cache = {}
        self._check_mode = check_mode
        self._operation_checker = OperationChecker

    def execute_operation(self, op_name, params):
        """
        Allow user request execution of simple operations(natively supported by API provider) as well as complex
        operations(operations that are implemented as a set of simple operations).

        :param op_name: name of the operation being called by the user
        :type op_name: str
        :param params: definition of the params that operation should be executed with
        :type params: dict
        :return: Result of the operation being executed
        :rtype: dict
        """
        if self._operation_checker.is_upsert_operation(op_name):
            return self.upsert_object(op_name, params)
        else:
            return self.crud_operation(op_name, params)

    def crud_operation(self, op_name, params):
        """
        Allow user request execution of simple operations(natively supported by API provider) only.

        :param op_name: name of the operation being called by the user
        :type op_name: str
        :param params: definition of the params that operation should be executed with
        :type params: dict
        :return: Result of the operation being executed
        :rtype: dict
        """
        op_spec = self.get_operation_spec(op_name)
        if op_spec is None:
            raise FtdInvalidOperationNameError(op_name)

        if self._operation_checker.is_add_operation(op_name, op_spec):
            resp = self.add_object(op_name, params)
        elif self._operation_checker.is_edit_operation(op_name, op_spec):
            resp = self.edit_object(op_name, params)
        elif self._operation_checker.is_delete_operation(op_name, op_spec):
            resp = self.delete_object(op_name, params)
        elif self._operation_checker.is_find_by_filter_operation(op_name, params, op_spec):
            resp = list(self.get_objects_by_filter(op_name, params))
        else:
            resp = self.send_general_request(op_name, params)
        return resp

    def get_operation_spec(self, operation_name):
        if operation_name not in self._operation_spec_cache:
            self._operation_spec_cache[operation_name] = self._conn.get_operation_spec(operation_name)
        return self._operation_spec_cache[operation_name]

    def get_operation_specs_by_model_name(self, model_name):
        if model_name not in self._models_operations_specs_cache:
            model_op_specs = self._conn.get_operation_specs_by_model_name(model_name)
            self._models_operations_specs_cache[model_name] = model_op_specs
            for op_name, op_spec in iteritems(model_op_specs):
                self._operation_spec_cache.setdefault(op_name, op_spec)
        return self._models_operations_specs_cache[model_name]

    def get_objects_by_filter(self, operation_name, params):
        def transform_filters_to_query_param(filter_params):
            return ';'.join(['%s:%s' % (key, val) for key, val in sorted(iteritems(filter_params))])

        def match_filters(filter_params, obj):
            for k, v in iteritems(filter_params):
                if k not in obj or obj[k] != v:
                    return False
            return True

        dummy, query_params, path_params = _get_user_params(params)
        # copy required params to avoid mutation of passed `params` dict
        get_list_params = {ParamName.QUERY_PARAMS: dict(query_params), ParamName.PATH_PARAMS: dict(path_params)}

        filters = params.get(ParamName.FILTERS) or {}
        if filters:
            get_list_params[ParamName.QUERY_PARAMS][QueryParams.FILTER] = transform_filters_to_query_param(filters)

        item_generator = iterate_over_pageable_resource(
            partial(self.send_general_request, operation_name=operation_name), get_list_params
        )
        return (i for i in item_generator if match_filters(filters, i))

    def add_object(self, operation_name, params):
        def is_duplicate_name_error(err):
            return err.code == UNPROCESSABLE_ENTITY_STATUS and DUPLICATE_NAME_ERROR_MESSAGE in str(err)

        try:
            return self.send_general_request(operation_name, params)
        except FtdServerError as e:
            if is_duplicate_name_error(e):
                return self._check_if_the_same_object(operation_name, params, e)
            else:
                raise e

    def _check_if_the_same_object(self, operation_name, params, e):
        """
        Special check used in the scope of 'add_object' operation, which can be requested as a standalone operation or
        in the scope of 'upsert_object' operation. This method executed in case 'add_object' failed and should try to
        find the object that caused "object duplicate" error. In case single object found and it's equal to one we are
        trying to create - the existing object will be returned (attempt to have kind of idempotency for add action).
        In the case when we got more than one object returned as a result of the request to API - it will be hard to
        find exact duplicate so the exception will be raised.
        """
        model_name = self.get_operation_spec(operation_name)[OperationField.MODEL_NAME]
        get_list_operation = self._find_get_list_operation(model_name)
        if get_list_operation:
            data = params[ParamName.DATA]
            if not params.get(ParamName.FILTERS):
                params[ParamName.FILTERS] = {'name': data['name']}

            existing_obj = None
            existing_objs = self.get_objects_by_filter(get_list_operation, params)

            for i, obj in enumerate(existing_objs):
                if i > 0:
                    raise FtdConfigurationError(MULTIPLE_DUPLICATES_FOUND_ERROR)
                existing_obj = obj

            if existing_obj is not None:
                if equal_objects(existing_obj, data):
                    return existing_obj
                else:
                    raise FtdConfigurationError(
                        'Cannot add new object. '
                        'An object with the same name but different parameters already exists.',
                        existing_obj)

        raise e

    def _find_get_list_operation(self, model_name):
        operations = self.get_operation_specs_by_model_name(model_name) or {}
        return next((
            op for op, op_spec in operations.items()
            if self._operation_checker.is_get_list_operation(op, op_spec)), None)

    def _find_get_operation(self, model_name):
        operations = self.get_operation_specs_by_model_name(model_name) or {}
        return next((
            op for op, op_spec in operations.items()
            if self._operation_checker.is_get_operation(op, op_spec)), None)

    def delete_object(self, operation_name, params):
        def is_invalid_uuid_error(err):
            return err.code == UNPROCESSABLE_ENTITY_STATUS and INVALID_UUID_ERROR_MESSAGE in str(err)

        try:
            return self.send_general_request(operation_name, params)
        except FtdServerError as e:
            if is_invalid_uuid_error(e):
                return {'status': 'Referenced object does not exist'}
            else:
                raise e

    def edit_object(self, operation_name, params):
        data, dummy, path_params = _get_user_params(params)

        model_name = self.get_operation_spec(operation_name)[OperationField.MODEL_NAME]
        get_operation = self._find_get_operation(model_name)

        if get_operation:
            existing_object = self.send_general_request(get_operation, {ParamName.PATH_PARAMS: path_params})
            if not existing_object:
                raise FtdConfigurationError('Referenced object does not exist')
            elif equal_objects(existing_object, data):
                return existing_object

        return self.send_general_request(operation_name, params)

    def send_general_request(self, operation_name, params):
        self.validate_params(operation_name, params)
        if self._check_mode:
            raise CheckModeException()

        data, query_params, path_params = _get_user_params(params)
        op_spec = self.get_operation_spec(operation_name)
        url, method = op_spec[OperationField.URL], op_spec[OperationField.METHOD]

        return self._send_request(url, method, data, path_params, query_params)

    def _send_request(self, url_path, http_method, body_params=None, path_params=None, query_params=None):
        def raise_for_failure(resp):
            if not resp[ResponseParams.SUCCESS]:
                raise FtdServerError(resp[ResponseParams.RESPONSE], resp[ResponseParams.STATUS_CODE])

        response = self._conn.send_request(url_path=url_path, http_method=http_method, body_params=body_params,
                                           path_params=path_params, query_params=query_params)
        raise_for_failure(response)
        if http_method != HTTPMethod.GET:
            self.config_changed = True
        return response[ResponseParams.RESPONSE]

    def validate_params(self, operation_name, params):
        report = {}
        op_spec = self.get_operation_spec(operation_name)
        data, query_params, path_params = _get_user_params(params)

        def validate(validation_method, field_name, user_params):
            key = 'Invalid %s provided' % field_name
            try:
                is_valid, validation_report = validation_method(operation_name, user_params)
                if not is_valid:
                    report[key] = validation_report
            except Exception as e:
                report[key] = str(e)
            return report

        validate(self._conn.validate_query_params, ParamName.QUERY_PARAMS, query_params)
        validate(self._conn.validate_path_params, ParamName.PATH_PARAMS, path_params)
        if is_post_request(op_spec) or is_put_request(op_spec):
            validate(self._conn.validate_data, ParamName.DATA, data)

        if report:
            raise ValidationError(report)

    def is_upsert_operation_supported(self, op_name):
        """
        Checks if all operations required for upsert object operation are defined in 'operations'.

        :param op_name: upsert operation name
        :type op_name: str
        :return: True if all criteria required to provide requested called operation are satisfied, otherwise False
        :rtype: bool
        """
        model_name = _extract_model_from_upsert_operation(op_name)
        operations = self.get_operation_specs_by_model_name(model_name)
        return self._operation_checker.is_upsert_operation_supported(operations)

    @staticmethod
    def _get_operation_name(checker, operations):
        for operation_name, op_spec in operations.items():
            if checker(operation_name, op_spec):
                return operation_name
        raise FtdConfigurationError("Operation is not supported")

    def _add_upserted_object(self, model_operations, params):
        add_op_name = self._get_operation_name(self._operation_checker.is_add_operation, model_operations)
        return self.add_object(add_op_name, params)

    def _edit_upserted_object(self, model_operations, existing_object, params):
        edit_op_name = self._get_operation_name(self._operation_checker.is_edit_operation, model_operations)
        _set_default(params, 'path_params', {})
        _set_default(params, 'data', {})

        params['path_params']['objId'] = existing_object['id']
        copy_identity_properties(existing_object, params['data'])
        return self.edit_object(edit_op_name, params)

    def upsert_object(self, op_name, params):
        """
        The wrapper on top of add object operation, get a list of objects and edit object operations that implement
        upsert object operation. As a result, the object will be created if the object does not exist, if a single
        object exists with requested 'params' this object will be updated otherwise, Exception will be raised.

        :param op_name: upsert operation name
        :type op_name: str
        :param params: params that upsert operation should be executed with
        :type params: dict
        :return: upserted object representation
        :rtype: dict
        """
        if not self.is_upsert_operation_supported(op_name):
            raise FtdInvalidOperationNameError(op_name)

        model_name = _extract_model_from_upsert_operation(op_name)
        model_operations = self.get_operation_specs_by_model_name(model_name)

        try:
            return self._add_upserted_object(model_operations, params)
        except FtdConfigurationError as e:
            if e.obj:
                return self._edit_upserted_object(model_operations, e.obj, params)
            raise e


def _set_default(params, field_name, value):
    if field_name not in params or params[field_name] is None:
        params[field_name] = value


def is_post_request(operation_spec):
    return operation_spec[OperationField.METHOD] == HTTPMethod.POST


def is_put_request(operation_spec):
    return operation_spec[OperationField.METHOD] == HTTPMethod.PUT


def _extract_model_from_upsert_operation(op_name):
    return op_name[len(OperationNamePrefix.UPSERT):]


def _get_user_params(params):
    return params.get(ParamName.DATA) or {}, params.get(ParamName.QUERY_PARAMS) or {}, params.get(
        ParamName.PATH_PARAMS) or {}


def iterate_over_pageable_resource(resource_func, params):
    """
    A generator function that iterates over a resource that supports pagination and lazily returns present items
    one by one.

    :param resource_func: function that receives `params` argument and returns a page of objects
    :type resource_func: callable
    :param params: initial dictionary of parameters that will be passed to the resource_func.
                   Should contain `query_params` inside.
    :type params: dict
    :return: an iterator containing returned items
    :rtype: iterator of dict
    """
    # creating a copy not to mutate passed dict
    params = copy.deepcopy(params)
    params[ParamName.QUERY_PARAMS].setdefault('limit', DEFAULT_PAGE_SIZE)
    params[ParamName.QUERY_PARAMS].setdefault('offset', DEFAULT_OFFSET)
    limit = int(params[ParamName.QUERY_PARAMS]['limit'])

    def received_less_items_than_requested(items_in_response, items_expected):
        if items_in_response == items_expected:
            return False
        elif items_in_response < items_expected:
            return True

        raise FtdUnexpectedResponse(
            "Get List of Objects Response from the server contains more objects than requested. "
            "There are {0} item(s) in the response while {1} was(ere) requested".format(items_in_response,
                                                                                        items_expected)
        )

    while True:
        result = resource_func(params=params)

        for item in result['items']:
            yield item

        if received_less_items_than_requested(len(result['items']), limit):
            break

        # creating a copy not to mutate existing dict
        params = copy.deepcopy(params)
        query_params = params[ParamName.QUERY_PARAMS]
        query_params['offset'] = int(query_params['offset']) + limit
