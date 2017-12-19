# Copyright (c) 2017 Cisco and/or its affiliates.
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

from __future__ import (absolute_import, division, print_function)

import json

from ansible.compat.tests.mock import patch
from ansible.compat.tests import unittest
from ansible.module_utils.network.nso import nso


MODULE_PREFIX_MAP = '''
{
  "ansible-nso": "an",
  "test": "test",
  "tailf-ncs": "ncs"
}
'''


SCHEMA_DATA = {
    '/an:id-name-leaf': '''
{
  "meta": {
    "prefix": "an",
    "namespace": "http://github.com/ansible/nso",
    "types": {
      "http://github.com/ansible/nso:id-name-t": [
        {
          "name": "http://github.com/ansible/nso:id-name-t",
          "enumeration": [
            {
              "label": "id-one"
            },
            {
              "label": "id-two"
            }
          ]
        },
        {
          "name": "identityref"
        }
      ]
    },
    "keypath": "/an:id-name-leaf"
  },
  "data": {
    "kind": "leaf",
    "type": {
      "namespace": "http://github.com/ansible/nso",
      "name": "id-name-t"
    },
    "name": "id-name-leaf",
    "qname": "an:id-name-leaf"
  }
}''',
    '/an:id-name-values': '''
{
  "meta": {
    "prefix": "an",
    "namespace": "http://github.com/ansible/nso",
    "types": {},
    "keypath": "/an:id-name-values"
  },
  "data": {
    "kind": "container",
    "name": "id-name-values",
    "qname": "an:id-name-values",
    "children": [
      {
        "kind": "list",
        "name": "id-name-value",
        "qname": "an:id-name-value",
        "key": [
          "name"
        ]
      }
    ]
  }
}
''',
    '/an:id-name-values/id-name-value': '''
{
  "meta": {
    "prefix": "an",
    "namespace": "http://github.com/ansible/nso",
    "types": {
      "http://github.com/ansible/nso:id-name-t": [
        {
          "name": "http://github.com/ansible/nso:id-name-t",
          "enumeration": [
            {
              "label": "id-one"
            },
            {
              "label": "id-two"
            }
          ]
        },
        {
          "name": "identityref"
        }
      ]
    },
    "keypath": "/an:id-name-values/id-name-value"
  },
  "data": {
    "kind": "list",
    "name": "id-name-value",
    "qname": "an:id-name-value",
    "key": [
      "name"
    ],
    "children": [
      {
        "kind": "key",
        "name": "name",
        "qname": "an:name",
        "type": {
          "namespace": "http://github.com/ansible/nso",
          "name": "id-name-t"
        }
      },
      {
        "kind": "leaf",
        "type": {
          "primitive": true,
          "name": "string"
        },
        "name": "value",
        "qname": "an:value"
      }
    ]
  }
}
''',
    '/test:test': '''
{
    "meta": {},
    "data": {
        "kind": "list",
        "name":"test",
        "qname":"test:test",
        "key":["name"],
        "children": [
            {
                "kind": "key",
                "name": "name",
                "qname": "test:name",
                "type": {"name":"string","primitive":true}
            },
            {
                "kind": "choice",
                "name": "test-choice",
                "qname": "test:test-choice",
                "cases": [
                    {
                        "kind": "case",
                        "name": "direct-child-case",
                        "qname":"test:direct-child-case",
                        "children":[
                            {
                                "kind": "leaf",
                                "name": "direct-child",
                                "qname": "test:direct-child",
                                "type": {"name":"string","primitive":true}
                            }
                        ]
                    },
                    {
                        "kind":"case","name":"nested-child-case","qname":"test:nested-child-case",
                        "children": [
                            {
                                "kind": "choice",
                                "name": "nested-choice",
                                "qname": "test:nested-choice",
                                "cases": [
                                    {
                                        "kind":"case","name":"nested-child","qname":"test:nested-child",
                                        "children": [
                                            {
                                               "kind": "leaf",
                                               "name":"nested-child",
                                                "qname":"test:nested-child",
                                               "type":{"name":"string","primitive":true}}
                                         ]
                                    }
                             ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
}
'''
}


class MockResponse(object):
    def __init__(self, method, params, code, body, headers=None):
        if headers is None:
            headers = {}

        self.method = method
        self.params = params

        self.code = code
        self.body = body
        self.headers = dict(headers)

    def read(self):
        return self.body


def mock_call(calls, url, data=None, headers=None, method=None):
    result = calls[0]
    del calls[0]

    request = json.loads(data)
    if result.method != request['method']:
        raise ValueError('expected method {0}({1}), got {2}({3})'.format(
            result.method, result.params,
            request['method'], request['params']))

    for key, value in result.params.items():
        if key not in request['params']:
            raise ValueError('{0} not in parameters'.format(key))
        if value != request['params'][key]:
            raise ValueError('expected {0} to be {1}, got {2}'.format(
                key, value, request['params'][key]))

    return result


def get_schema_response(path):
    return MockResponse(
        'get_schema', {'path': path}, 200, '{{"result": {0}}}'.format(
            SCHEMA_DATA[path]))


class TestValueBuilder(unittest.TestCase):
    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_identityref_leaf(self, open_url_mock):
        calls = [
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            get_schema_response('/an:id-name-leaf'),
            MockResponse('get_module_prefix_map', {}, 200, '{{"result": {0}}}'.format(MODULE_PREFIX_MAP))
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)

        parent = "/an:id-name-leaf"
        schema_data = json.loads(
            SCHEMA_DATA['/an:id-name-leaf'])
        schema = schema_data['data']

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc'))
        vb.build(parent, None, 'ansible-nso:id-two', schema)
        self.assertEquals(1, len(vb.values))
        value = vb.values[0]
        self.assertEquals(parent, value.path)
        self.assertEquals('set', value.state)
        self.assertEquals('an:id-two', value.value)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_identityref_key(self, open_url_mock):
        calls = [
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            get_schema_response('/an:id-name-values/id-name-value'),
            MockResponse('get_module_prefix_map', {}, 200, '{{"result": {0}}}'.format(MODULE_PREFIX_MAP)),
            MockResponse('exists', {'path': '/an:id-name-values/id-name-value{an:id-one}'}, 200, '{"result": {"exists": true}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)

        parent = "/an:id-name-values"
        schema_data = json.loads(
            SCHEMA_DATA['/an:id-name-values/id-name-value'])
        schema = schema_data['data']

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc'))
        vb.build(parent, 'id-name-value', [{'name': 'ansible-nso:id-one', 'value': '1'}], schema)
        self.assertEquals(1, len(vb.values))
        value = vb.values[0]
        self.assertEquals('{0}/id-name-value{{an:id-one}}/value'.format(parent), value.path)
        self.assertEquals('set', value.state)
        self.assertEquals('1', value.value)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nested_choice(self, open_url_mock):
        calls = [
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            get_schema_response('/test:test'),
            MockResponse('exists', {'path': '/test:test{direct}'}, 200, '{"result": {"exists": true}}'),
            MockResponse('exists', {'path': '/test:test{nested}'}, 200, '{"result": {"exists": true}}')
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)

        parent = "/test:test"
        schema_data = json.loads(
            SCHEMA_DATA['/test:test'])
        schema = schema_data['data']

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc'))
        vb.build(parent, None, [{'name': 'direct', 'direct-child': 'direct-value'},
                                {'name': 'nested', 'nested-child': 'nested-value'}], schema)
        self.assertEquals(2, len(vb.values))
        value = vb.values[0]
        self.assertEquals('{0}{{direct}}/direct-child'.format(parent), value.path)
        self.assertEquals('set', value.state)
        self.assertEquals('direct-value', value.value)

        value = vb.values[1]
        self.assertEquals('{0}{{nested}}/nested-child'.format(parent), value.path)
        self.assertEquals('set', value.state)
        self.assertEquals('nested-value', value.value)

        self.assertEqual(0, len(calls))
