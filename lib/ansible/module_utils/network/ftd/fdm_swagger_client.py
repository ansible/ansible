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

from ansible.module_utils.network.ftd.common import HTTPMethod
from ansible.module_utils.six import integer_types, string_types, iteritems

FILE_MODEL_NAME = '_File'
SUCCESS_RESPONSE_CODE = '200'
DELETE_PREFIX = 'delete'


class OperationField:
    URL = 'url'
    METHOD = 'method'
    PARAMETERS = 'parameters'
    MODEL_NAME = 'modelName'
    DESCRIPTION = 'description'
    RETURN_MULTIPLE_ITEMS = 'returnMultipleItems'
    TAGS = "tags"


class SpecProp:
    DEFINITIONS = 'definitions'
    OPERATIONS = 'operations'
    MODELS = 'models'
    MODEL_OPERATIONS = 'model_operations'


class PropName:
    ENUM = 'enum'
    TYPE = 'type'
    REQUIRED = 'required'
    INVALID_TYPE = 'invalid_type'
    REF = '$ref'
    ALL_OF = 'allOf'
    BASE_PATH = 'basePath'
    PATHS = 'paths'
    OPERATION_ID = 'operationId'
    SCHEMA = 'schema'
    ITEMS = 'items'
    PROPERTIES = 'properties'
    RESPONSES = 'responses'
    NAME = 'name'
    DESCRIPTION = 'description'


class PropType:
    STRING = 'string'
    BOOLEAN = 'boolean'
    INTEGER = 'integer'
    NUMBER = 'number'
    OBJECT = 'object'
    ARRAY = 'array'
    FILE = 'file'


class OperationParams:
    PATH = 'path'
    QUERY = 'query'


class QueryParams:
    FILTER = 'filter'


def _get_model_name_from_url(schema_ref):
    path = schema_ref.split('/')
    return path[len(path) - 1]


class IllegalArgumentException(ValueError):
    """
    Exception raised when the function parameters:
        - not all passed
        - empty string
        - wrong type
    """
    pass


class ValidationError(ValueError):
    pass


class FdmSwaggerParser:
    _definitions = None
    _base_path = None

    def parse_spec(self, spec, docs=None):
        """
        This method simplifies a swagger format, resolves a model name for each operation, and adds documentation for
        each operation and model if it is provided.

        :param spec: An API specification in the swagger format, see
            <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md>
        :type spec: dict
        :param spec: A documentation map containing descriptions for models, operations and operation parameters.
        :type docs: dict
        :rtype: dict
        :return:
        Ex.
            The models field contains model definition from swagger see
            <#https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#definitions>
            {
                'models':{
                    'model_name':{...},
                    ...
                },
                'operations':{
                    'operation_name':{
                        'method': 'get', #post, put, delete
                        'url': '/api/fdm/v2/object/networks', #url already contains a value from `basePath`
                        'modelName': 'NetworkObject', # it is a link to the model from 'models'
                                                      # None - for a delete operation or we don't have information
                                                      # '_File' - if an endpoint works with files
                        'returnMultipleItems': False, # shows if the operation returns a single item or an item list
                        'parameters': {
                            'path':{
                                'param_name':{
                                    'type': 'string'#integer, boolean, number
                                    'required' True #False
                                }
                                ...
                                },
                            'query':{
                                'param_name':{
                                    'type': 'string'#integer, boolean, number
                                    'required' True #False
                                }
                                ...
                            }
                        }
                    },
                    ...
                },
                'model_operations':{
                    'model_name':{ # a list of operations available for the current model
                        'operation_name':{
                            ... # the same as in the operations section
                        },
                        ...
                    },
                    ...
                }
            }
        """
        self._definitions = spec[SpecProp.DEFINITIONS]
        self._base_path = spec[PropName.BASE_PATH]
        operations = self._get_operations(spec)

        if docs:
            operations = self._enrich_operations_with_docs(operations, docs)
            self._definitions = self._enrich_definitions_with_docs(self._definitions, docs)

        return {
            SpecProp.MODELS: self._definitions,
            SpecProp.OPERATIONS: operations,
            SpecProp.MODEL_OPERATIONS: self._get_model_operations(operations)
        }

    @property
    def base_path(self):
        return self._base_path

    def _get_model_operations(self, operations):
        model_operations = {}
        for operations_name, params in iteritems(operations):
            model_name = params[OperationField.MODEL_NAME]
            model_operations.setdefault(model_name, {})[operations_name] = params
        return model_operations

    def _get_operations(self, spec):
        paths_dict = spec[PropName.PATHS]
        operations_dict = {}
        for url, operation_params in iteritems(paths_dict):
            for method, params in iteritems(operation_params):
                operation = {
                    OperationField.METHOD: method,
                    OperationField.URL: self._base_path + url,
                    OperationField.MODEL_NAME: self._get_model_name(method, params),
                    OperationField.RETURN_MULTIPLE_ITEMS: self._return_multiple_items(params),
                    OperationField.TAGS: params.get(OperationField.TAGS, [])
                }
                if OperationField.PARAMETERS in params:
                    operation[OperationField.PARAMETERS] = self._get_rest_params(params[OperationField.PARAMETERS])

                operation_id = params[PropName.OPERATION_ID]
                operations_dict[operation_id] = operation
        return operations_dict

    def _enrich_operations_with_docs(self, operations, docs):
        def get_operation_docs(op):
            op_url = op[OperationField.URL][len(self._base_path):]
            return docs[PropName.PATHS].get(op_url, {}).get(op[OperationField.METHOD], {})

        for operation in operations.values():
            operation_docs = get_operation_docs(operation)
            operation[OperationField.DESCRIPTION] = operation_docs.get(PropName.DESCRIPTION, '')

            if OperationField.PARAMETERS in operation:
                param_descriptions = dict((
                    (p[PropName.NAME], p[PropName.DESCRIPTION])
                    for p in operation_docs.get(OperationField.PARAMETERS, {})
                ))

                for param_name, params_spec in operation[OperationField.PARAMETERS][OperationParams.PATH].items():
                    params_spec[OperationField.DESCRIPTION] = param_descriptions.get(param_name, '')

                for param_name, params_spec in operation[OperationField.PARAMETERS][OperationParams.QUERY].items():
                    params_spec[OperationField.DESCRIPTION] = param_descriptions.get(param_name, '')

        return operations

    def _enrich_definitions_with_docs(self, definitions, docs):
        for model_name, model_def in definitions.items():
            model_docs = docs[SpecProp.DEFINITIONS].get(model_name, {})
            model_def[PropName.DESCRIPTION] = model_docs.get(PropName.DESCRIPTION, '')
            for prop_name, prop_spec in model_def.get(PropName.PROPERTIES, {}).items():
                prop_spec[PropName.DESCRIPTION] = model_docs.get(PropName.PROPERTIES, {}).get(prop_name, '')
                prop_spec[PropName.REQUIRED] = prop_name in model_def.get(PropName.REQUIRED, [])
        return definitions

    def _get_model_name(self, method, params):
        if method == HTTPMethod.GET:
            return self._get_model_name_from_responses(params)
        elif method == HTTPMethod.POST or method == HTTPMethod.PUT:
            return self._get_model_name_for_post_put_requests(params)
        elif method == HTTPMethod.DELETE:
            return self._get_model_name_from_delete_operation(params)
        else:
            return None

    @staticmethod
    def _return_multiple_items(op_params):
        """
        Defines if the operation returns one item or a list of items.

        :param op_params: operation specification
        :return: True if the operation returns a list of items, otherwise False
        """
        try:
            schema = op_params[PropName.RESPONSES][SUCCESS_RESPONSE_CODE][PropName.SCHEMA]
            return PropName.ITEMS in schema[PropName.PROPERTIES]
        except KeyError:
            return False

    def _get_model_name_from_delete_operation(self, params):
        operation_id = params[PropName.OPERATION_ID]
        if operation_id.startswith(DELETE_PREFIX):
            model_name = operation_id[len(DELETE_PREFIX):]
            if model_name in self._definitions:
                return model_name
        return None

    def _get_model_name_for_post_put_requests(self, params):
        model_name = None
        if OperationField.PARAMETERS in params:
            body_param_dict = self._get_body_param_from_parameters(params[OperationField.PARAMETERS])
            if body_param_dict:
                schema_ref = body_param_dict[PropName.SCHEMA][PropName.REF]
                model_name = self._get_model_name_byschema_ref(schema_ref)
        if model_name is None:
            model_name = self._get_model_name_from_responses(params)
        return model_name

    @staticmethod
    def _get_body_param_from_parameters(params):
        return next((param for param in params if param['in'] == 'body'), None)

    def _get_model_name_from_responses(self, params):
        responses = params[PropName.RESPONSES]
        if SUCCESS_RESPONSE_CODE in responses:
            response = responses[SUCCESS_RESPONSE_CODE][PropName.SCHEMA]
            if PropName.REF in response:
                return self._get_model_name_byschema_ref(response[PropName.REF])
            elif PropName.PROPERTIES in response:
                ref = response[PropName.PROPERTIES][PropName.ITEMS][PropName.ITEMS][PropName.REF]
                return self._get_model_name_byschema_ref(ref)
            elif (PropName.TYPE in response) and response[PropName.TYPE] == PropType.FILE:
                return FILE_MODEL_NAME
        else:
            return None

    def _get_rest_params(self, params):
        path = {}
        query = {}
        operation_param = {
            OperationParams.PATH: path,
            OperationParams.QUERY: query
        }
        for param in params:
            in_param = param['in']
            if in_param == OperationParams.QUERY:
                query[param[PropName.NAME]] = self._simplify_param_def(param)
            elif in_param == OperationParams.PATH:
                path[param[PropName.NAME]] = self._simplify_param_def(param)
        return operation_param

    @staticmethod
    def _simplify_param_def(param):
        return {
            PropName.TYPE: param[PropName.TYPE],
            PropName.REQUIRED: param[PropName.REQUIRED]
        }

    def _get_model_name_byschema_ref(self, schema_ref):
        model_name = _get_model_name_from_url(schema_ref)
        model_def = self._definitions[model_name]
        if PropName.ALL_OF in model_def:
            return self._get_model_name_byschema_ref(model_def[PropName.ALL_OF][0][PropName.REF])
        else:
            return model_name


class FdmSwaggerValidator:
    def __init__(self, spec):
        """
        :param spec: dict
                    data from FdmSwaggerParser().parse_spec()
        """
        self._operations = spec[SpecProp.OPERATIONS]
        self._models = spec[SpecProp.MODELS]

    def validate_data(self, operation_name, data=None):
        """
        Validate data for the post|put requests
        :param operation_name: string
                            The value must be non empty string.
                            The operation name is used to get a model specification
        :param data: dict
                    The value must be in the format that the model(from operation) expects
        :rtype: (bool, string|dict)
        :return:
            (True, None) - if data valid
            Invalid:
            (False, {
                'required': [ #list of the fields that are required but were not present in the data
                    'field_name',
                    'patent.field_name',# when the nested field is omitted
                    'patent.list[2].field_name' # if data is array and one of the field is omitted
                ],
                'invalid_type':[ #list of the fields with invalid data
                        {
                           'path': 'objId', #field name or path to the field. Ex. objects[3].id, parent.name
                           'expected_type': 'string',# expected type. Ex. 'object', 'array', 'string', 'integer',
                                                     # 'boolean', 'number'
                           'actually_value': 1 # the value that user passed
                       }
                ]
            })
        :raises IllegalArgumentException
            'The operation_name parameter must be a non-empty string' if operation_name is not valid
            'The data parameter must be a dict' if data neither dict or None
            '{operation_name} operation does not support' if the spec does not contain the operation
        """
        if data is None:
            data = {}

        self._check_validate_data_params(data, operation_name)

        operation = self._operations[operation_name]
        model = self._models[operation[OperationField.MODEL_NAME]]
        status = self._init_report()

        self._validate_object(status, model, data, '')

        if len(status[PropName.REQUIRED]) > 0 or len(status[PropName.INVALID_TYPE]) > 0:
            return False, self._delete_empty_field_from_report(status)
        return True, None

    def _check_validate_data_params(self, data, operation_name):
        if not operation_name or not isinstance(operation_name, string_types):
            raise IllegalArgumentException("The operation_name parameter must be a non-empty string")
        if not isinstance(data, dict):
            raise IllegalArgumentException("The data parameter must be a dict")
        if operation_name not in self._operations:
            raise IllegalArgumentException("{0} operation does not support".format(operation_name))

    def validate_query_params(self, operation_name, params):
        """
           Validate params for the get requests. Use this method for validating the query part of the url.
           :param operation_name: string
                               The value must be non empty string.
                               The operation name is used to get a params specification
           :param params: dict
                        should be in the format that the specification(from operation) expects
                    Ex.
                    {
                        'objId': "string_value",
                        'p_integer': 1,
                        'p_boolean': True,
                        'p_number': 2.3
                    }
           :rtype:(Boolean, msg)
           :return:
               (True, None) - if params valid
               Invalid:
               (False, {
                   'required': [ #list of the fields that are required but are not present in the params
                       'field_name'
                   ],
                   'invalid_type':[ #list of the fields with invalid data and expected type of the params
                            {
                              'path': 'objId', #field name
                              'expected_type': 'string',#expected type. Ex. 'string', 'integer', 'boolean', 'number'
                              'actually_value': 1 # the value that user passed
                            }
                   ]
               })
            :raises IllegalArgumentException
               'The operation_name parameter must be a non-empty string' if operation_name is not valid
               'The params parameter must be a dict' if params neither dict or None
               '{operation_name} operation does not support' if the spec does not contain the operation
           """
        return self._validate_url_params(operation_name, params, resource=OperationParams.QUERY)

    def validate_path_params(self, operation_name, params):
        """
        Validate params for the get requests. Use this method for validating the path part of the url.
           :param operation_name: string
                               The value must be non empty string.
                               The operation name is used to get a params specification
           :param params: dict
                        should be in the format that the specification(from operation) expects

                 Ex.
                 {
                     'objId': "string_value",
                     'p_integer': 1,
                     'p_boolean': True,
                     'p_number': 2.3
                 }
        :rtype:(Boolean, msg)
        :return:
            (True, None) - if params valid
            Invalid:
            (False, {
                'required': [ #list of the fields that are required but are not present in the params
                    'field_name'
                ],
                'invalid_type':[ #list of the fields with invalid data and expected type of the params
                         {
                           'path': 'objId', #field name
                           'expected_type': 'string',#expected type. Ex. 'string', 'integer', 'boolean', 'number'
                           'actually_value': 1 # the value that user passed
                         }
                ]
            })
        :raises IllegalArgumentException
            'The operation_name parameter must be a non-empty string' if operation_name is not valid
            'The params parameter must be a dict' if params neither dict or None
            '{operation_name} operation does not support' if the spec does not contain the operation
        """
        return self._validate_url_params(operation_name, params, resource=OperationParams.PATH)

    def _validate_url_params(self, operation, params, resource):
        if params is None:
            params = {}

        self._check_validate_url_params(operation, params)

        operation = self._operations[operation]
        if OperationField.PARAMETERS in operation and resource in operation[OperationField.PARAMETERS]:
            spec = operation[OperationField.PARAMETERS][resource]
            status = self._init_report()
            self._check_url_params(status, spec, params)

            if len(status[PropName.REQUIRED]) > 0 or len(status[PropName.INVALID_TYPE]) > 0:
                return False, self._delete_empty_field_from_report(status)
            return True, None
        else:
            return True, None

    def _check_validate_url_params(self, operation, params):
        if not operation or not isinstance(operation, string_types):
            raise IllegalArgumentException("The operation_name parameter must be a non-empty string")
        if not isinstance(params, dict):
            raise IllegalArgumentException("The params parameter must be a dict")
        if operation not in self._operations:
            raise IllegalArgumentException("{0} operation does not support".format(operation))

    def _check_url_params(self, status, spec, params):
        for prop_name in spec.keys():
            prop = spec[prop_name]
            if prop[PropName.REQUIRED] and prop_name not in params:
                status[PropName.REQUIRED].append(prop_name)
                continue
            if prop_name in params:
                expected_type = prop[PropName.TYPE]
                value = params[prop_name]
                if prop_name in params and not self._is_correct_simple_types(expected_type, value, allow_null=False):
                    self._add_invalid_type_report(status, '', prop_name, expected_type, value)

    def _validate_object(self, status, model, data, path):
        if self._is_enum(model):
            self._check_enum(status, model, data, path)
        elif self._is_object(model):
            self._check_object(status, model, data, path)

    def _is_enum(self, model):
        return self._is_string_type(model) and PropName.ENUM in model

    def _check_enum(self, status, model, data, path):
        if data is not None and data not in model[PropName.ENUM]:
            self._add_invalid_type_report(status, path, '', PropName.ENUM, data)

    def _add_invalid_type_report(self, status, path, prop_name, expected_type, actually_value):
        status[PropName.INVALID_TYPE].append({
            'path': self._create_path_to_field(path, prop_name),
            'expected_type': expected_type,
            'actually_value': actually_value
        })

    def _check_object(self, status, model, data, path):
        if data is None:
            return

        if not isinstance(data, dict):
            self._add_invalid_type_report(status, path, '', PropType.OBJECT, data)
            return None

        if PropName.REQUIRED in model:
            self._check_required_fields(status, model[PropName.REQUIRED], data, path)

        model_properties = model[PropName.PROPERTIES]
        for prop in model_properties.keys():
            if prop in data:
                model_prop_val = model_properties[prop]
                expected_type = model_prop_val[PropName.TYPE]
                actually_value = data[prop]
                self._check_types(status, actually_value, expected_type, model_prop_val, path, prop)

    def _check_types(self, status, actually_value, expected_type, model, path, prop_name):
        if expected_type == PropType.OBJECT:
            ref_model = self._get_model_by_ref(model)

            self._validate_object(status, ref_model, actually_value,
                                  path=self._create_path_to_field(path, prop_name))
        elif expected_type == PropType.ARRAY:
            self._check_array(status, model, actually_value,
                              path=self._create_path_to_field(path, prop_name))
        elif not self._is_correct_simple_types(expected_type, actually_value):
            self._add_invalid_type_report(status, path, prop_name, expected_type, actually_value)

    def _get_model_by_ref(self, model_prop_val):
        model = _get_model_name_from_url(model_prop_val[PropName.REF])
        return self._models[model]

    def _check_required_fields(self, status, required_fields, data, path):
        missed_required_fields = [self._create_path_to_field(path, field) for field in
                                  required_fields if field not in data.keys() or data[field] is None]
        if len(missed_required_fields) > 0:
            status[PropName.REQUIRED] += missed_required_fields

    def _check_array(self, status, model, data, path):
        if data is None:
            return
        elif not isinstance(data, list):
            self._add_invalid_type_report(status, path, '', PropType.ARRAY, data)
        else:
            item_model = model[PropName.ITEMS]
            for i, item_data in enumerate(data):
                self._check_types(status, item_data, item_model[PropName.TYPE], item_model, "{0}[{1}]".format(path, i),
                                  '')

    @staticmethod
    def _is_correct_simple_types(expected_type, value, allow_null=True):
        def is_numeric_string(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        if value is None and allow_null:
            return True
        elif expected_type == PropType.STRING:
            return isinstance(value, string_types)
        elif expected_type == PropType.BOOLEAN:
            return isinstance(value, bool)
        elif expected_type == PropType.INTEGER:
            is_integer = isinstance(value, integer_types) and not isinstance(value, bool)
            is_digit_string = isinstance(value, string_types) and value.isdigit()
            return is_integer or is_digit_string
        elif expected_type == PropType.NUMBER:
            is_number = isinstance(value, (integer_types, float)) and not isinstance(value, bool)
            is_numeric_string = isinstance(value, string_types) and is_numeric_string(value)
            return is_number or is_numeric_string
        return False

    @staticmethod
    def _is_string_type(model):
        return PropName.TYPE in model and model[PropName.TYPE] == PropType.STRING

    @staticmethod
    def _init_report():
        return {
            PropName.REQUIRED: [],
            PropName.INVALID_TYPE: []
        }

    @staticmethod
    def _delete_empty_field_from_report(status):
        if not status[PropName.REQUIRED]:
            del status[PropName.REQUIRED]
        if not status[PropName.INVALID_TYPE]:
            del status[PropName.INVALID_TYPE]
        return status

    @staticmethod
    def _create_path_to_field(path='', field=''):
        separator = ''
        if path and field:
            separator = '.'
        return "{0}{1}{2}".format(path, separator, field)

    @staticmethod
    def _is_object(model):
        return PropName.TYPE in model and model[PropName.TYPE] == PropType.OBJECT
