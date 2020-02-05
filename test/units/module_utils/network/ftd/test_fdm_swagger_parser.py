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

from ansible.module_utils.network.ftd.common import HTTPMethod
from ansible.module_utils.network.ftd.fdm_swagger_client import FdmSwaggerParser

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_FOLDER = os.path.join(DIR_PATH, 'test_data')

base = {
    'basePath': "/api/fdm/v2",
    'definitions': {"NetworkObject": {"type": "object",
                                      "properties": {"version": {"type": "string"}, "name": {"type": "string"},
                                                     "description": {"type": "string"},
                                                     "subType": {"type": "object",
                                                                 "$ref": "#/definitions/NetworkObjectType"},
                                                     "value": {"type": "string"},
                                                     "isSystemDefined": {"type": "boolean"},
                                                     "dnsResolution": {"type": "object",
                                                                       "$ref": "#/definitions/FQDNDNSResolution"},
                                                     "id": {"type": "string"},
                                                     "type": {"type": "string", "default": "networkobject"}},
                                      "required": ["subType", "type", "value", "name"]},
                    "NetworkObjectWrapper": {
                        "allOf": [{"$ref": "#/definitions/NetworkObject"}, {"$ref": "#/definitions/LinksWrapper"}]}
                    },
    'paths': {
        "/object/networks": {
            "get": {"tags": ["NetworkObject"],
                    "operationId": "getNetworkObjectList",
                    "responses": {
                        "200": {
                            "description": "",
                            "schema": {"type": "object",
                                       "title": "NetworkObjectList",
                                       "properties": {
                                           "items": {
                                               "type": "array",
                                               "items": {"$ref": "#/definitions/NetworkObjectWrapper"}},
                                           "paging": {
                                               "$ref": "#/definitions/Paging"}},
                                       "required": ["items", "paging"]}}},
                    "parameters": [
                        {"name": "offset", "in": "query", "required": False, "type": "integer"},
                        {"name": "limit", "in": "query", "required": False, "type": "integer"},
                        {"name": "sort", "in": "query", "required": False, "type": "string"},
                        {"name": "filter", "in": "query", "required": False, "type": "string"}]},
            "post": {"tags": ["NetworkObject"], "operationId": "addNetworkObject",
                     "responses": {
                         "200": {"description": "",
                                 "schema": {"type": "object",
                                            "$ref": "#/definitions/NetworkObjectWrapper"}},
                         "422": {"description": "",
                                 "schema": {"type": "object", "$ref": "#/definitions/ErrorWrapper"}}},
                     "parameters": [{"in": "body", "name": "body",
                                     "required": True,
                                     "schema": {"$ref": "#/definitions/NetworkObject"}}]}
        },
        "/object/networks/{objId}": {
            "get": {"tags": ["NetworkObject"], "operationId": "getNetworkObject",
                    "responses": {"200": {"description": "",
                                          "schema": {"type": "object",
                                                     "$ref": "#/definitions/NetworkObjectWrapper"}},
                                  "404": {"description": "",
                                          "schema": {"type": "object",
                                                     "$ref": "#/definitions/ErrorWrapper"}}},
                    "parameters": [{"name": "objId", "in": "path", "required": True,
                                    "type": "string"}]},

            "put": {"tags": ["NetworkObject"], "operationId": "editNetworkObject",
                    "responses": {"200": {"description": "",
                                          "schema": {"type": "object",
                                                     "$ref": "#/definitions/NetworkObjectWrapper"}},
                                  "422": {"description": "",
                                          "schema": {"type": "object",
                                                     "$ref": "#/definitions/ErrorWrapper"}}},
                    "parameters": [{"name": "objId", "in": "path", "required": True,
                                    "type": "string"},
                                   {"in": "body", "name": "body", "required": True,
                                    "schema": {"$ref": "#/definitions/NetworkObject"}}]},
            "delete": {"tags": ["NetworkObject"], "operationId": "deleteNetworkObject",
                       "responses": {"204": {"description": ""},
                                     "422": {"description": "",
                                             "schema": {"type": "object",
                                                        "$ref": "#/definitions/ErrorWrapper"}}},
                       "parameters": [{"name": "objId", "in": "path", "required": True,
                                       "type": "string"}]}}}
}


def _get_objects(base_object, key_names):
    return dict((_key, base_object[_key]) for _key in key_names)


class TestFdmSwaggerParser(unittest.TestCase):

    def test_simple_object(self):
        self._data = copy.deepcopy(base)

        self.fdm_data = FdmSwaggerParser().parse_spec(self._data)

        expected_operations = {
            'getNetworkObjectList': {
                'method': HTTPMethod.GET,
                'url': '/api/fdm/v2/object/networks',
                'modelName': 'NetworkObject',
                'parameters': {
                    'path': {},
                    'query': {
                        'offset': {
                            'required': False,
                            'type': 'integer'
                        },
                        'limit': {
                            'required': False,
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
                },
                'returnMultipleItems': True,
                "tags": ["NetworkObject"]
            },
            'addNetworkObject': {
                'method': HTTPMethod.POST,
                'url': '/api/fdm/v2/object/networks',
                'modelName': 'NetworkObject',
                'parameters': {'path': {},
                               'query': {}},
                'returnMultipleItems': False,
                "tags": ["NetworkObject"]
            },
            'getNetworkObject': {
                'method': HTTPMethod.GET,
                'url': '/api/fdm/v2/object/networks/{objId}',
                'modelName': 'NetworkObject',
                'parameters': {
                    'path': {
                        'objId': {
                            'required': True,
                            'type': "string"
                        }
                    },
                    'query': {}
                },
                'returnMultipleItems': False,
                "tags": ["NetworkObject"]
            },
            'editNetworkObject': {
                'method': HTTPMethod.PUT,
                'url': '/api/fdm/v2/object/networks/{objId}',
                'modelName': 'NetworkObject',
                'parameters': {
                    'path': {
                        'objId': {
                            'required': True,
                            'type': "string"
                        }
                    },
                    'query': {}
                },
                'returnMultipleItems': False,
                "tags": ["NetworkObject"]
            },
            'deleteNetworkObject': {
                'method': HTTPMethod.DELETE,
                'url': '/api/fdm/v2/object/networks/{objId}',
                'modelName': 'NetworkObject',
                'parameters': {
                    'path': {
                        'objId': {
                            'required': True,
                            'type': "string"
                        }
                    },
                    'query': {}
                },
                'returnMultipleItems': False,
                "tags": ["NetworkObject"]
            }
        }
        assert sorted(['NetworkObject', 'NetworkObjectWrapper']) == sorted(self.fdm_data['models'].keys())
        assert expected_operations == self.fdm_data['operations']
        assert {'NetworkObject': expected_operations} == self.fdm_data['model_operations']

    def test_simple_object_with_documentation(self):
        api_spec = copy.deepcopy(base)
        docs = {
            'definitions': {
                'NetworkObject': {
                    'description': 'Description for Network Object',
                    'properties': {'name': 'Description for name field'}
                }
            },
            'paths': {
                '/object/networks': {
                    'get': {
                        'description': 'Description for getNetworkObjectList operation',
                        'parameters': [{'name': 'offset', 'description': 'Description for offset field'}]
                    },
                    'post': {'description': 'Description for addNetworkObject operation'}
                }
            }
        }

        self.fdm_data = FdmSwaggerParser().parse_spec(api_spec, docs)

        assert 'Description for Network Object' == self.fdm_data['models']['NetworkObject']['description']
        assert '' == self.fdm_data['models']['NetworkObjectWrapper']['description']
        network_properties = self.fdm_data['models']['NetworkObject']['properties']
        assert '' == network_properties['id']['description']
        assert not network_properties['id']['required']
        assert 'Description for name field' == network_properties['name']['description']
        assert network_properties['name']['required']

        ops = self.fdm_data['operations']
        assert 'Description for getNetworkObjectList operation' == ops['getNetworkObjectList']['description']
        assert 'Description for addNetworkObject operation' == ops['addNetworkObject']['description']
        assert '' == ops['deleteNetworkObject']['description']

        get_op_params = ops['getNetworkObjectList']['parameters']
        assert 'Description for offset field' == get_op_params['query']['offset']['description']
        assert '' == get_op_params['query']['limit']['description']

    def test_model_operations_should_contain_all_operations(self):
        data = {
            'basePath': '/v2/',
            'definitions': {
                'Model1': {"type": "object"},
                'Model2': {"type": "object"},
                'Model3': {"type": "object"}
            },
            'paths': {
                'path1': {
                    'get': {
                        'operationId': 'getSomeModelList',
                        "responses": {
                            "200": {"description": "",
                                    "schema": {"type": "object",
                                               "title": "NetworkObjectList",
                                               "properties": {
                                                   "items": {
                                                       "type": "array",
                                                       "items": {
                                                           "$ref": "#/definitions/Model1"
                                                       }
                                                   }
                                               }}
                                    }
                        }
                    },
                    "post": {
                        "operationId": "addSomeModel",
                        "parameters": [{"in": "body",
                                        "name": "body",
                                        "schema": {"$ref": "#/definitions/Model2"}
                                        }]}
                },
                'path2/{id}': {
                    "get": {"operationId": "getSomeModel",
                            "responses": {"200": {"description": "",
                                                  "schema": {"type": "object",
                                                             "$ref": "#/definitions/Model3"}},
                                          }
                            },
                    "put": {"operationId": "editSomeModel",
                            "parameters": [{"in": "body",
                                            "name": "body",
                                            "schema": {"$ref": "#/definitions/Model1"}}
                                           ]},
                    "delete": {
                        "operationId": "deleteModel3",
                    }},
                'path3': {
                    "delete": {
                        "operationId": "deleteNoneModel",
                    }
                }
            }
        }

        expected_operations = {
            'getSomeModelList': {
                'method': HTTPMethod.GET,
                'url': '/v2/path1',
                'modelName': 'Model1',
                'returnMultipleItems': True,
                'tags': []
            },
            'addSomeModel': {
                'method': HTTPMethod.POST,
                'url': '/v2/path1',
                'modelName': 'Model2',
                'parameters': {
                    'path': {},
                    'query': {}
                },
                'returnMultipleItems': False,
                'tags': []
            },
            'getSomeModel': {
                'method': HTTPMethod.GET,
                'url': '/v2/path2/{id}',
                'modelName': 'Model3',
                'returnMultipleItems': False,
                'tags': []
            },
            'editSomeModel': {
                'method': HTTPMethod.PUT,
                'url': '/v2/path2/{id}',
                'modelName': 'Model1',
                'parameters': {
                    'path': {},
                    'query': {}
                },
                'returnMultipleItems': False,
                'tags': []
            },
            'deleteModel3': {
                'method': HTTPMethod.DELETE,
                'url': '/v2/path2/{id}',
                'modelName': 'Model3',
                'returnMultipleItems': False,
                'tags': []
            },
            'deleteNoneModel': {
                'method': HTTPMethod.DELETE,
                'url': '/v2/path3',
                'modelName': None,
                'returnMultipleItems': False,
                'tags': []
            }
        }

        fdm_data = FdmSwaggerParser().parse_spec(data)
        assert sorted(['Model1', 'Model2', 'Model3']) == sorted(fdm_data['models'].keys())
        assert expected_operations == fdm_data['operations']
        assert {
            'Model1': {
                'getSomeModelList': expected_operations['getSomeModelList'],
                'editSomeModel': expected_operations['editSomeModel'],
            },
            'Model2': {
                'addSomeModel': expected_operations['addSomeModel']
            },
            'Model3': {
                'getSomeModel': expected_operations['getSomeModel'],
                'deleteModel3': expected_operations['deleteModel3']
            },
            None: {
                'deleteNoneModel': expected_operations['deleteNoneModel']
            }
        } == fdm_data['model_operations']
