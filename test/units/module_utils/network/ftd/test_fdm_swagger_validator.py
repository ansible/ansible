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
import os
import unittest

import pytest
from ansible.module_utils.network.ftd.fdm_swagger_client import FdmSwaggerValidator, IllegalArgumentException

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_FOLDER = os.path.join(DIR_PATH, 'test_data')

mock_data = {
    'models': {
        'ReferenceModel': {'type': 'object', 'required': ['id', 'type'],
                           'properties': {'id': {'type': 'string'}, 'type': {'type': 'string'},
                                          'version': {'type': 'string'}, 'name': {'type': 'string'}}},
        'FQDNDNSResolution': {'type': 'string', 'enum': ['IPV4_ONLY', 'IPV6_ONLY', 'IPV4_AND_IPV6']},
        'NetworkObjectType': {'type': 'string', 'enum': ['HOST', 'NETWORK', 'IPRANGE', 'FQDN']},
        'NetworkObject': {'type': 'object',
                          'properties': {'version': {'type': 'string'},
                                         'name': {'type': 'string'},
                                         'description': {'type': 'string'},
                                         'subType': {'type': 'object',
                                                     '$ref': '#/definitions/NetworkObjectType'},
                                         'value': {'type': 'string'},
                                         'isSystemDefined': {'type': 'boolean'},
                                         'dnsResolution': {'type': 'object',
                                                           '$ref': '#/definitions/FQDNDNSResolution'},
                                         'objects': {'type': 'array',
                                                     'items': {'type': 'object',
                                                               '$ref': '#/definitions/ReferenceModel'}},
                                         'id': {'type': 'string'},
                                         'type': {'type': 'string',
                                                  'default': 'networkobject'}},
                          'required': ['subType', 'type', 'value']}
    },
    'operations': {
        'getNetworkObjectList': {
            'method': 'get',
            'url': '/api/fdm/v2/object/networks',
            'modelName': 'NetworkObject',
            'parameters': {
                'path': {
                    'objId': {
                        'required': True,
                        'type': "string"
                    }
                },
                'query': {
                    'offset': {
                        'required': False,
                        'type': 'integer'
                    },
                    'limit': {
                        'required': True,
                        'type': 'integer'
                    },
                    'sort': {
                        'required': False,
                        'type': 'string'
                    },
                    'filter': {
                        'required': False,
                        'type': 'string'
                    }
                }
            }
        }
    }
}

nested_mock_data1 = {
    'models': {
        'model1': {
            'type': 'object',
            'properties': {
                'f_string': {'type': 'string'},
                'f_number': {'type': 'number'},
                'f_boolean': {'type': 'boolean'},
                'f_integer': {'type': 'integer'}
            },
            'required': ['f_string']
        },
        'TestModel': {
            'type': 'object',
            'properties': {
                'nested_model': {'type': 'object',
                                 '$ref': '#/definitions/model1'},
                'f_integer': {'type': 'integer'}
            },
            'required': ['nested_model']
        }
    },
    'operations': {
        'getdata': {
            'modelName': 'TestModel'
        }
    }
}


def sort_validator_rez(data):
    if 'required' in data:
        data['required'] = sorted(data['required'])
    if 'invalid_type' in data:
        data['invalid_type'] = sorted(data['invalid_type'],
                                      key=lambda k: '{0}{1}{2}'.format(k['path'], ['expected_type'],
                                                                       ['actually_value']))

    return data


class TestFdmSwaggerValidator(unittest.TestCase):

    @staticmethod
    def check_illegal_argument_exception(cb, msg):
        with pytest.raises(IllegalArgumentException) as ctx:
            cb()
        assert msg == str(ctx.value)

    def test_path_params_valid(self):
        self.url_data_valid(method='validate_path_params', parameters_type='path')

    def test_query_params_valid(self):
        self.url_data_valid(method='validate_query_params', parameters_type='query')

    @staticmethod
    def url_data_valid(method, parameters_type):
        local_mock_spec = {
            'models': {},
            'operations': {
                'getNetwork': {
                    'method': 'get',
                    'parameters': {
                        parameters_type: {
                            'objId': {
                                'required': True,
                                'type': "string"
                            },
                            'p_integer': {
                                'required': False,
                                'type': "integer"
                            },
                            'p_boolean': {
                                'required': False,
                                'type': "boolean"
                            },
                            'p_number': {
                                'required': False,
                                'type': "number"
                            }
                        }
                    }
                }
            }
        }
        data = {
            'objId': "value1",
            'p_integer': 1,
            'p_boolean': True,
            'p_number': 2.3
        }
        validator = FdmSwaggerValidator(local_mock_spec)
        valid, rez = getattr(validator, method)('getNetwork', data)
        assert valid
        assert rez is None

    def test_path_params_required_fields(self):
        self.url_data_required_fields(method='validate_path_params', parameters_type='path')

    def test_query_params_required_fields(self):
        self.url_data_required_fields(method='validate_query_params', parameters_type='query')

    @staticmethod
    def url_data_required_fields(method, parameters_type):
        local_mock_spec = {
            'models': {},
            'operations': {
                'getNetwork': {
                    'method': 'get',
                    'parameters': {
                        parameters_type: {
                            'objId': {
                                'required': True,
                                'type': "string"
                            },
                            'parentId': {
                                'required': True,
                                'type': "string"
                            },
                            'someParam': {
                                'required': False,
                                'type': "string"
                            },
                            'p_integer': {
                                'required': False,
                                'type': "integer"
                            },
                            'p_boolean': {
                                'required': False,
                                'type': "boolean"
                            },
                            'p_number': {
                                'required': False,
                                'type': "number"
                            }
                        }
                    }
                }
            }
        }
        validator = FdmSwaggerValidator(local_mock_spec)
        valid, rez = getattr(validator, method)('getNetwork', None)
        assert not valid
        assert sort_validator_rez({
            'required': ['objId', 'parentId']
        }) == sort_validator_rez(rez)
        valid, rez = getattr(validator, method)('getNetwork', {})
        assert not valid
        assert sort_validator_rez({
            'required': ['objId', 'parentId']
        }) == sort_validator_rez(rez)
        data = {
            'someParam': "test"
        }
        valid, rez = getattr(validator, method)('getNetwork', data)
        assert not valid
        assert sort_validator_rez({
            'required': ['objId', 'parentId']
        }) == sort_validator_rez(rez)

    def test_path_params_invalid_params(self):
        self.url_params_invalid_params(method='validate_path_params', parameters_type='path')

    def test_query_params_invalid_params(self):
        self.url_params_invalid_params(method='validate_query_params', parameters_type='query')

    @staticmethod
    def url_params_invalid_params(method, parameters_type):
        local_mock_spec = {
            'models': {},
            'operations': {
                'getNetwork': {
                    'method': 'get',
                    'parameters': {
                        parameters_type: {
                            'objId': {
                                'required': True,
                                'type': "string"
                            },
                            'parentId': {
                                'required': True,
                                'type': "string"
                            },
                            'someParam': {
                                'required': False,
                                'type': "string"
                            },
                            'p_integer': {
                                'required': False,
                                'type': "integer"
                            },
                            'p_boolean': {
                                'required': False,
                                'type': "boolean"
                            },
                            'p_number': {
                                'required': False,
                                'type': "number"
                            }
                        }
                    }
                }
            }
        }
        validator = FdmSwaggerValidator(local_mock_spec)
        data = {
            'objId': 1,
            'parentId': True,
            'someParam': [],
            'p_integer': 1.2,
            'p_boolean': 0,
            'p_number': False
        }
        valid, rez = getattr(validator, method)('getNetwork', data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'objId',
                    'expected_type': 'string',
                    'actually_value': 1
                },
                {
                    'path': 'parentId',
                    'expected_type': 'string',
                    'actually_value': True
                },
                {
                    'path': 'someParam',
                    'expected_type': 'string',
                    'actually_value': []
                },
                {
                    'path': 'p_integer',
                    'expected_type': 'integer',
                    'actually_value': 1.2
                },
                {
                    'path': 'p_boolean',
                    'expected_type': 'boolean',
                    'actually_value': 0
                },
                {
                    'path': 'p_number',
                    'expected_type': 'number',
                    'actually_value': False
                }
            ]
        }) == sort_validator_rez(rez)
        data = {
            'objId': {},
            'parentId': 0,
            'someParam': 1.2,
            'p_integer': True,
            'p_boolean': 1,
            'p_number': True
        }
        valid, rez = getattr(validator, method)('getNetwork', data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'objId',
                    'expected_type': 'string',
                    'actually_value': {}
                },
                {
                    'path': 'parentId',
                    'expected_type': 'string',
                    'actually_value': 0
                },
                {
                    'path': 'someParam',
                    'expected_type': 'string',
                    'actually_value': 1.2
                },
                {
                    'path': 'p_integer',
                    'expected_type': 'integer',
                    'actually_value': True
                },
                {
                    'path': 'p_boolean',
                    'expected_type': 'boolean',
                    'actually_value': 1
                },
                {
                    'path': 'p_number',
                    'expected_type': 'number',
                    'actually_value': True
                }
            ]
        }) == sort_validator_rez(rez)
        data = {
            'objId': {},
            'parentId': 0,
            'someParam': 1.2,
            'p_integer': "1",
            'p_boolean': "",
            'p_number': "2.1"
        }
        valid, rez = getattr(validator, method)('getNetwork', data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'objId',
                    'expected_type': 'string',
                    'actually_value': {}
                },
                {
                    'path': 'parentId',
                    'expected_type': 'string',
                    'actually_value': 0
                },
                {
                    'path': 'someParam',
                    'expected_type': 'string',
                    'actually_value': 1.2
                },
                {
                    'path': 'p_boolean',
                    'expected_type': 'boolean',
                    'actually_value': ""
                }
            ]
        }) == sort_validator_rez(rez)

        data = {
            'objId': "123",
            'parentId': "1",
            'someParam': None,
            'p_integer': None
        }
        valid, rez = getattr(validator, method)('getNetwork', data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'someParam',
                    'expected_type': 'string',
                    'actually_value': None
                },
                {
                    'path': 'p_integer',
                    'expected_type': 'integer',
                    'actually_value': None
                }
            ]
        }) == sort_validator_rez(rez)

    def test_validate_path_params_method_with_empty_data(self):
        self.validate_url_data_with_empty_data(method='validate_path_params', parameters_type='path')

    def test_validate_query_params_method_with_empty_data(self):
        self.validate_url_data_with_empty_data(method='validate_query_params', parameters_type='query')

    def validate_url_data_with_empty_data(self, method, parameters_type):
        local_mock_spec = {
            'models': {},
            'operations': {
                'getNetwork': {
                    'method': 'get',
                    'parameters': {
                        parameters_type: {
                            'objId': {
                                'required': True,
                                'type': "string"
                            }
                        }
                    }
                }
            }
        }
        validator = FdmSwaggerValidator(local_mock_spec)
        valid, rez = getattr(validator, method)('getNetwork', None)
        assert not valid
        assert {'required': ['objId']} == rez

        self.check_illegal_argument_exception(lambda: getattr(validator, method)('getNetwork', ''),
                                              "The params parameter must be a dict")

        self.check_illegal_argument_exception(lambda: getattr(validator, method)('getNetwork', []),
                                              "The params parameter must be a dict")

        valid, rez = getattr(validator, method)('getNetwork', {})
        assert not valid
        assert {'required': ['objId']} == rez

        self.check_illegal_argument_exception(lambda: getattr(validator, method)(None, {'name': 'test'}),
                                              "The operation_name parameter must be a non-empty string")

        self.check_illegal_argument_exception(lambda: getattr(validator, method)('', {'name': 'test'}),
                                              "The operation_name parameter must be a non-empty string")

        self.check_illegal_argument_exception(lambda: getattr(validator, method)([], {'name': 'test'}),
                                              "The operation_name parameter must be a non-empty string")

        self.check_illegal_argument_exception(lambda: getattr(validator, method)({}, {'name': 'test'}),
                                              "The operation_name parameter must be a non-empty string")

        self.check_illegal_argument_exception(
            lambda: getattr(validator, method)('operation_does_not_exist', {'name': 'test'}),
            "operation_does_not_exist operation does not support")

    def test_validate_data_method_with_empty_data(self):
        validator = FdmSwaggerValidator(mock_data)
        valid, rez = validator.validate_data('getNetworkObjectList', None)
        assert not valid
        assert sort_validator_rez({
            'required': ['subType', 'type', 'value']
        }) == sort_validator_rez(rez)

        self.check_illegal_argument_exception(lambda: validator.validate_data('getNetworkObjectList', ''),
                                              "The data parameter must be a dict")

        self.check_illegal_argument_exception(lambda: validator.validate_data('getNetworkObjectList', []),
                                              "The data parameter must be a dict")
        valid, rez = validator.validate_data('getNetworkObjectList', {})
        assert not valid
        assert sort_validator_rez({
            'required': ['subType', 'type', 'value']
        }) == sort_validator_rez(rez)

        self.check_illegal_argument_exception(lambda: validator.validate_data(None, {'name': 'test'}),
                                              "The operation_name parameter must be a non-empty string")

        self.check_illegal_argument_exception(lambda: validator.validate_data('', {'name': 'test'}),
                                              "The operation_name parameter must be a non-empty string")

        self.check_illegal_argument_exception(lambda: validator.validate_data([], {'name': 'test'}),
                                              "The operation_name parameter must be a non-empty string")

        self.check_illegal_argument_exception(lambda: validator.validate_data({}, {'name': 'test'}),
                                              "The operation_name parameter must be a non-empty string")

        self.check_illegal_argument_exception(
            lambda: validator.validate_data('operation_does_not_exist', {'name': 'test'}),
            "operation_does_not_exist operation does not support")

    def test_errors_for_required_fields(self):
        data = {
            'name': 'test'
        }
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert not valid
        assert sort_validator_rez({
            'required': ['subType', 'type', 'value']
        }) == sort_validator_rez(rez)

    def test_errors_if_no_data_was_passed(self):
        data = {}
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert not valid
        assert sort_validator_rez({
            'required': ['subType', 'type', 'value']
        }) == sort_validator_rez(rez)

    def test_errors_if_one_required_field_is_empty(self):
        data = {
            'subType': 'NETWORK',
            'value': '1.1.1.1'
        }
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert not valid
        assert {'required': ['type']} == rez

    def test_types_of_required_fields_are_incorrect(self):
        data = {
            'subType': True,
            'type': 1,
            'value': False
        }
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'subType',
                    'expected_type': 'enum',
                    'actually_value': True
                },
                {
                    'path': 'value',
                    'expected_type': 'string',
                    'actually_value': False
                },
                {
                    'path': 'type',
                    'expected_type': 'string',
                    'actually_value': 1
                }
            ]
        }) == sort_validator_rez(rez)
        data = {
            'subType': {},
            'type': [],
            'value': {}
        }
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'subType',
                    'expected_type': 'enum',
                    'actually_value': {}
                },
                {
                    'path': 'value',
                    'expected_type': 'string',
                    'actually_value': {}
                },
                {
                    'path': 'type',
                    'expected_type': 'string',
                    'actually_value': []
                }
            ]
        }) == sort_validator_rez(rez)

    def test_pass_only_required_fields(self):
        data = {
            'subType': 'NETWORK',
            'type': 'networkobject',
            'value': '1.1.1.1'
        }
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert valid
        assert rez is None

    def test_pass_only_required_fields_with_none_values(self):
        data = {
            'subType': 'NETWORK',
            'type': 'networkobject',
            'value': None
        }
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert not valid
        assert {'required': ['value']} == rez

    def test_pass_no_data_with_no_required_fields(self):
        spec = copy.deepcopy(mock_data)
        del spec['models']['NetworkObject']['required']

        valid, rez = FdmSwaggerValidator(spec).validate_data('getNetworkObjectList', {})

        assert valid
        assert rez is None

    def test_pass_all_fields_with_correct_data(self):
        data = {
            'id': 'id-di',
            'version': 'v',
            'name': 'test_name',
            'subType': 'NETWORK',
            'type': 'networkobject',
            'value': '1.1.1.1',
            'description': 'des',
            'isSystemDefined': False,
            'dnsResolution': 'IPV4_ONLY',
            'objects': [{
                'type': 'port',
                'id': 'fs-sf'
            }]
        }
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert valid
        assert rez is None

    def test_array_data_is_not_correct(self):
        data = {
            'name': 'test_name',
            'subType': 'NETWORK',
            'type': 'networkobject',
            'value': '1.1.1.1',
            'objects': [
                {
                    'id': 'fs-sf'
                },
                {
                    'type': 'type'
                },
                {},
                {
                    'id': 1,
                    'type': True
                },
                [],
                'test'
            ]
        }
        valid, rez = FdmSwaggerValidator(mock_data).validate_data('getNetworkObjectList', data)
        assert not valid
        assert sort_validator_rez({
            'required': ['objects[0].type', 'objects[1].id', 'objects[2].id', 'objects[2].type'],
            'invalid_type': [
                {
                    'path': 'objects[3].id',
                    'expected_type': 'string',
                    'actually_value': 1
                },
                {
                    'path': 'objects[3].type',
                    'expected_type': 'string',
                    'actually_value': True
                },
                {
                    'path': 'objects[4]',
                    'expected_type': 'object',
                    'actually_value': []
                },
                {
                    'path': 'objects[5]',
                    'expected_type': 'object',
                    'actually_value': 'test'
                }
            ]
        }) == sort_validator_rez(rez)

    def test_simple_types(self):
        local_mock_data = {
            'models': {
                'TestModel': {
                    'type': 'object',
                    'properties': {
                        'f_string': {'type': 'string'},
                        'f_number': {'type': 'number'},
                        'f_boolean': {'type': 'boolean'},
                        'f_integer': {'type': 'integer'}
                    },
                    'required': []
                }
            },
            'operations': {
                'getdata': {
                    'modelName': 'TestModel'
                }
            }
        }
        valid_data = {
            "f_string": "test",
            "f_number": 2.2,
            "f_boolean": False,
            "f_integer": 1
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', valid_data)
        assert valid
        assert rez is None

        valid_data = {
            "f_string": "",
            "f_number": 0,
            "f_boolean": True,
            "f_integer": 0
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', valid_data)
        assert valid
        assert rez is None

        valid_data = {
            "f_string": "0",
            "f_number": 100,
            "f_boolean": True,
            "f_integer": 2
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', valid_data)
        assert valid
        assert rez is None

        valid_data = {
            "f_string": None,
            "f_number": None,
            "f_boolean": None,
            "f_integer": None
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', valid_data)
        assert valid
        assert rez is None

    def test_invalid_simple_types(self):
        local_mock_data = {
            'models': {
                'TestModel': {
                    'type': 'object',
                    'properties': {
                        'f_string': {'type': 'string'},
                        'f_number': {'type': 'number'},
                        'f_boolean': {'type': 'boolean'},
                        'f_integer': {'type': 'integer'}
                    },
                    'required': []
                }
            },
            'operations': {
                'getdata': {
                    'modelName': 'TestModel'
                }
            }
        }
        invalid_data = {
            "f_string": True,
            "f_number": True,
            "f_boolean": 1,
            "f_integer": True
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', invalid_data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'f_string',
                    'expected_type': 'string',
                    'actually_value': True
                },
                {
                    'path': 'f_number',
                    'expected_type': 'number',
                    'actually_value': True
                },
                {
                    'path': 'f_boolean',
                    'expected_type': 'boolean',
                    'actually_value': 1
                },
                {
                    'path': 'f_integer',
                    'expected_type': 'integer',
                    'actually_value': True
                }
            ]
        }) == sort_validator_rez(rez)

        invalid_data = {
            "f_string": 1,
            "f_number": False,
            "f_boolean": 0,
            "f_integer": "test"
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', invalid_data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'f_string',
                    'expected_type': 'string',
                    'actually_value': 1
                },
                {
                    'path': 'f_number',
                    'expected_type': 'number',
                    'actually_value': False
                },
                {
                    'path': 'f_boolean',
                    'expected_type': 'boolean',
                    'actually_value': 0
                },
                {
                    'path': 'f_integer',
                    'expected_type': 'integer',
                    'actually_value': "test"
                }
            ]
        }) == sort_validator_rez(rez)

        invalid_data = {
            "f_string": False,
            "f_number": "1",
            "f_boolean": "",
            "f_integer": "1.2"
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', invalid_data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'f_string',
                    'expected_type': 'string',
                    'actually_value': False
                },
                {
                    'path': 'f_boolean',
                    'expected_type': 'boolean',
                    'actually_value': ""
                },
                {
                    'path': 'f_integer',
                    'expected_type': 'integer',
                    'actually_value': '1.2'
                }
            ]
        }) == sort_validator_rez(rez)

    def test_nested_required_fields(self):
        valid_data = {
            'nested_model': {
                'f_string': "test"
            }
        }

        valid, rez = FdmSwaggerValidator(nested_mock_data1).validate_data('getdata', valid_data)
        assert valid
        assert rez is None

    def test_invalid_nested_required_fields(self):
        invalid_data = {
            'f_integer': 2
        }

        valid, rez = FdmSwaggerValidator(nested_mock_data1).validate_data('getdata', invalid_data)
        assert not valid
        assert {'required': ['nested_model']} == rez

        invalid_data = {
            'nested_model': {
                'f_number': 1.2
            }
        }

        valid, rez = FdmSwaggerValidator(nested_mock_data1).validate_data('getdata', invalid_data)
        assert not valid
        assert {'required': ['nested_model.f_string']} == rez

    def test_invalid_type_in_nested_fields(self):
        invalid_data = {
            'nested_model': {
                "f_string": 1,
                "f_number": "ds",
                "f_boolean": 1.3,
                "f_integer": True
            }
        }

        valid, rez = FdmSwaggerValidator(nested_mock_data1).validate_data('getdata', invalid_data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'nested_model.f_string',
                    'expected_type': 'string',
                    'actually_value': 1
                },
                {
                    'path': 'nested_model.f_number',
                    'expected_type': 'number',
                    'actually_value': "ds"
                },
                {
                    'path': 'nested_model.f_boolean',
                    'expected_type': 'boolean',
                    'actually_value': 1.3
                },
                {
                    'path': 'nested_model.f_integer',
                    'expected_type': 'integer',
                    'actually_value': True
                }
            ]

        }) == sort_validator_rez(rez)

    def test_few_levels_nested_fields(self):
        local_mock_data = {
            'models': {
                'Model2': {
                    'type': 'object',
                    'required': ['ms', 'ts'],
                    'properties': {
                        'ms': {'type': 'array',
                               'items': {
                                   'type': 'object',
                                   '$ref': '#/definitions/ReferenceModel'}},
                        'ts': {'type': 'array',
                               'items': {
                                   'type': 'object',
                                   '$ref': '#/definitions/ReferenceModel'}}
                    }
                },
                'NetworkObjectType': {'type': 'string', 'enum': ['HOST', 'NETWORK', 'IPRANGE', 'FQDN']},
                'Fragment': {'type': 'object',
                             'required': ['type', 'objects', 'subType', 'object'],
                             'properties': {
                                 'objects': {'type': 'array',
                                             'items': {
                                                 'type': 'object',
                                                 '$ref': '#/definitions/ReferenceModel'}},
                                 'object': {'type': 'object',
                                            '$ref': '#/definitions/Model2'},
                                 'subType': {'type': 'object',
                                             '$ref': '#/definitions/NetworkObjectType'},
                                 'type': {'type': 'string'},
                                 'value': {'type': 'number'},
                                 'name': {'type': 'string'}}},
                'ReferenceModel': {'type': 'object', 'required': ['id', 'type'],
                                   'properties': {
                                       'id': {'type': 'string'},
                                       'type': {'type': 'string'},
                                       'version': {'type': 'string'},
                                       'name': {'type': 'string'}}},
                'model1': {
                    'type': 'object',
                    'properties': {
                        'f_string': {'type': 'string'},
                        'f_number': {'type': 'number'},
                        'f_boolean': {'type': 'boolean'},
                        'f_integer': {'type': 'integer'},
                        'objects': {'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        '$ref': '#/definitions/ReferenceModel'}},
                        'fragments': {'type': 'array',
                                      'items': {
                                          'type': 'object',
                                          '$ref': '#/definitions/Fragment'}}
                    },
                    'required': ['f_string', 'objects', 'fragments']
                },
                'TestModel': {
                    'type': 'object',
                    'properties': {
                        'nested_model': {'type': 'object',
                                         '$ref': '#/definitions/model1'},
                        'f_integer': {'type': 'integer'}
                    },
                    'required': ['nested_model']
                }
            },
            'operations': {
                'getdata': {
                    'modelName': 'TestModel'
                }
            }
        }

        valid_data = {
            "nested_model": {
                'objects': [{
                    'type': 't1',
                    'id': 'id1'
                }],
                'fragments': [{
                    'type': "test",
                    'subType': 'NETWORK',
                    'object': {
                        'ts': [],
                        'ms': [{
                            'type': "tt",
                            'id': 'id'
                        }]
                    },
                    'objects': [{
                        'type': 't',
                        'id': 'id'
                    }]
                }],
                'f_string': '1'
            }
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', valid_data)
        assert valid
        assert rez is None

        valid_data = {
            "nested_model": {
                'objects': [{
                    'type': 't1',
                    'id': 'id1'
                }],
                'fragments': [{
                    'type': "test",
                    'subType': 'NETWORK',
                    'object': {
                        'ms': {}
                    },
                    'objects': [{
                        'type': 't',
                        'id': 'id'
                    }]
                }],
                'f_string': '1'
            }
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', valid_data)
        assert not valid
        assert sort_validator_rez({
            'required': ['nested_model.fragments[0].object.ts'],
            'invalid_type': [{
                'path': 'nested_model.fragments[0].object.ms',
                'expected_type': 'array',
                'actually_value': {}
            }]
        }) == sort_validator_rez(rez)

        valid_data = {
            "nested_model": {
                'objects': [{
                    'type': 't1',
                    'id': 'id1'
                }],
                'fragments': [{
                    'type': "test",
                    'subType': 'NETWORK',
                    'object': [],
                    'objects': {}
                }],
                'f_string': '1'
            }
        }

        valid, rez = FdmSwaggerValidator(local_mock_data).validate_data('getdata', valid_data)
        assert not valid
        assert sort_validator_rez({
            'invalid_type': [
                {
                    'path': 'nested_model.fragments[0].objects',
                    'expected_type': 'array',
                    'actually_value': {}
                },
                {
                    'path': 'nested_model.fragments[0].object',
                    'expected_type': 'object',
                    'actually_value': []}
            ]}) == sort_validator_rez(rez)
