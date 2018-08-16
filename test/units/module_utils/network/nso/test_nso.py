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
    "meta": {
        "types": {
            "http://example.com/test:t15": [
               {
                  "leaf_type":[
                     {
                        "name":"string"
                     }
                  ],
                  "list_type":[
                     {
                        "name":"http://example.com/test:t15",
                        "leaf-list":true
                     }
                  ]
               }
            ]
        }
    },
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
            },
            {
               "kind":"leaf-list",
               "name":"device-list",
               "qname":"test:device-list",
               "type": {
                  "namespace":"http://example.com/test",
                  "name":"t15"
               }
            }
        ]
    }
}
''',
    '/test:test/device-list': '''
{
    "meta": {
        "types": {
            "http://example.com/test:t15": [
               {
                  "leaf_type":[
                     {
                        "name":"string"
                     }
                  ],
                  "list_type":[
                     {
                        "name":"http://example.com/test:t15",
                        "leaf-list":true
                     }
                  ]
               }
            ]
        }
    },
    "data": {
        "kind":"leaf-list",
        "name":"device-list",
        "qname":"test:device-list",
        "type": {
           "namespace":"http://example.com/test",
           "name":"t15"
        }
    }
}
''',
    '/test:deps': '''
{
    "meta": {
    },
    "data": {
        "kind":"container",
        "name":"deps",
        "qname":"test:deps",
        "children": [
            {
                "kind": "leaf",
                "type": {
                  "primitive": true,
                  "name": "string"
                },
                "name": "a",
                "qname": "test:a",
                "deps": ["/test:deps/c"]
            },
            {
                "kind": "leaf",
                "type": {
                  "primitive": true,
                  "name": "string"
                },
                "name": "b",
                "qname": "test:b",
                "deps": ["/test:deps/a"]
            },
            {
                "kind": "leaf",
                "type": {
                  "primitive": true,
                  "name": "string"
                },
                "name": "c",
                "qname": "test:c"
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


def mock_call(calls, url, timeout, data=None, headers=None, method=None):
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


class TestJsonRpc(unittest.TestCase):
    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_exists(self, open_url_mock):
        calls = [
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            MockResponse('exists', {'path': '/exists'}, 200, '{"result": {"exists": true}}'),
            MockResponse('exists', {'path': '/not-exists'}, 200, '{"result": {"exists": false}}')
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)
        client = nso.JsonRpc('http://localhost:8080/jsonrpc', 10)
        self.assertEquals(True, client.exists('/exists'))
        self.assertEquals(False, client.exists('/not-exists'))

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_exists_data_not_found(self, open_url_mock):
        calls = [
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            MockResponse('exists', {'path': '/list{missing-parent}/list{child}'}, 200, '{"error":{"type":"data.not_found"}}')
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)
        client = nso.JsonRpc('http://localhost:8080/jsonrpc', 10)
        self.assertEquals(False, client.exists('/list{missing-parent}/list{child}'))

        self.assertEqual(0, len(calls))


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

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc', 10))
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
            MockResponse('exists', {'path': '/an:id-name-values/id-name-value{an:id-one}'}, 200, '{"result": {"exists": true}}')
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)

        parent = "/an:id-name-values"
        schema_data = json.loads(
            SCHEMA_DATA['/an:id-name-values/id-name-value'])
        schema = schema_data['data']

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc', 10))
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

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc', 10))
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

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_leaf_list_type(self, open_url_mock):
        calls = [
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.4"}'),
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            get_schema_response('/test:test')
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)

        parent = "/test:test"
        schema_data = json.loads(
            SCHEMA_DATA['/test:test'])
        schema = schema_data['data']

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc', 10))
        vb.build(parent, None, {'device-list': ['one', 'two']}, schema)
        self.assertEquals(1, len(vb.values))
        value = vb.values[0]
        self.assertEquals('{0}/device-list'.format(parent), value.path)
        self.assertEquals(['one', 'two'], value.value)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_leaf_list_type_45(self, open_url_mock):
        calls = [
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5"}'),
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            get_schema_response('/test:test/device-list')
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)

        parent = "/test:test"
        schema_data = json.loads(
            SCHEMA_DATA['/test:test'])
        schema = schema_data['data']

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc', 10))
        vb.build(parent, None, {'device-list': ['one', 'two']}, schema)
        self.assertEquals(3, len(vb.values))
        value = vb.values[0]
        self.assertEquals('{0}/device-list'.format(parent), value.path)
        self.assertEquals(nso.State.ABSENT, value.state)
        value = vb.values[1]
        self.assertEquals('{0}/device-list{{one}}'.format(parent), value.path)
        self.assertEquals(nso.State.PRESENT, value.state)
        value = vb.values[2]
        self.assertEquals('{0}/device-list{{two}}'.format(parent), value.path)
        self.assertEquals(nso.State.PRESENT, value.state)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_sort_by_deps(self, open_url_mock):
        calls = [
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            get_schema_response('/test:deps')
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)

        parent = "/test:deps"
        schema_data = json.loads(
            SCHEMA_DATA['/test:deps'])
        schema = schema_data['data']

        values = {
            'a': '1',
            'b': '2',
            'c': '3',
        }

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc', 10))
        vb.build(parent, None, values, schema)
        self.assertEquals(3, len(vb.values))
        value = vb.values[0]
        self.assertEquals('{0}/c'.format(parent), value.path)
        self.assertEquals('3', value.value)
        value = vb.values[1]
        self.assertEquals('{0}/a'.format(parent), value.path)
        self.assertEquals('1', value.value)
        value = vb.values[2]
        self.assertEquals('{0}/b'.format(parent), value.path)
        self.assertEquals('2', value.value)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_sort_by_deps_not_included(self, open_url_mock):
        calls = [
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            get_schema_response('/test:deps')
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: mock_call(calls, *args, **kwargs)

        parent = "/test:deps"
        schema_data = json.loads(
            SCHEMA_DATA['/test:deps'])
        schema = schema_data['data']

        values = {
            'a': '1',
            'b': '2'
        }

        vb = nso.ValueBuilder(nso.JsonRpc('http://localhost:8080/jsonrpc', 10))
        vb.build(parent, None, values, schema)
        self.assertEquals(2, len(vb.values))
        value = vb.values[0]
        self.assertEquals('{0}/a'.format(parent), value.path)
        self.assertEquals('1', value.value)
        value = vb.values[1]
        self.assertEquals('{0}/b'.format(parent), value.path)
        self.assertEquals('2', value.value)

        self.assertEqual(0, len(calls))


class TestVerifyVersion(unittest.TestCase):
    def test_valid_versions(self):
        self.assertTrue(nso.verify_version_str('5.0', [(4, 6), (4, 5, 1)]))
        self.assertTrue(nso.verify_version_str('5.1.1', [(4, 6), (4, 5, 1)]))
        self.assertTrue(nso.verify_version_str('5.1.1.2', [(4, 6), (4, 5, 1)]))
        self.assertTrue(nso.verify_version_str('4.6', [(4, 6), (4, 5, 1)]))
        self.assertTrue(nso.verify_version_str('4.6.2', [(4, 6), (4, 5, 1)]))
        self.assertTrue(nso.verify_version_str('4.6.2.1', [(4, 6), (4, 5, 1)]))
        self.assertTrue(nso.verify_version_str('4.5.1', [(4, 6), (4, 5, 1)]))
        self.assertTrue(nso.verify_version_str('4.5.2', [(4, 6), (4, 5, 1)]))
        self.assertTrue(nso.verify_version_str('4.5.1.2', [(4, 6), (4, 5, 1)]))

    def test_invalid_versions(self):
        self.assertFalse(nso.verify_version_str('4.4', [(4, 6), (4, 5, 1)]))
        self.assertFalse(nso.verify_version_str('4.4.1', [(4, 6), (4, 5, 1)]))
        self.assertFalse(nso.verify_version_str('4.4.1.2', [(4, 6), (4, 5, 1)]))
        self.assertFalse(nso.verify_version_str('4.5.0', [(4, 6), (4, 5, 1)]))


class TestValueSort(unittest.TestCase):
    def test_sort_parent_depend(self):
        values = [
            nso.ValueBuilder.Value('/test/list{entry}', '/test/list', 'CREATE', ['']),
            nso.ValueBuilder.Value('/test/list{entry}/description', '/test/list/description', 'TEST', ['']),
            nso.ValueBuilder.Value('/test/entry', '/test/entry', 'VALUE', ['/test/list', '/test/list/name'])
        ]

        result = [v.path for v in nso.ValueBuilder.sort_values(values)]

        self.assertEquals(['/test/list{entry}', '/test/entry', '/test/list{entry}/description'], result)

    def test_sort_break_direct_cycle(self):
        values = [
            nso.ValueBuilder.Value('/test/a', '/test/a', 'VALUE', ['/test/c']),
            nso.ValueBuilder.Value('/test/b', '/test/b', 'VALUE', ['/test/a']),
            nso.ValueBuilder.Value('/test/c', '/test/c', 'VALUE', ['/test/a'])
        ]

        result = [v.path for v in nso.ValueBuilder.sort_values(values)]

        self.assertEquals(['/test/a', '/test/b', '/test/c'], result)

    def test_sort_break_indirect_cycle(self):
        values = [
            nso.ValueBuilder.Value('/test/c', '/test/c', 'VALUE', ['/test/a']),
            nso.ValueBuilder.Value('/test/a', '/test/a', 'VALUE', ['/test/b']),
            nso.ValueBuilder.Value('/test/b', '/test/b', 'VALUE', ['/test/c'])
        ]

        result = [v.path for v in nso.ValueBuilder.sort_values(values)]

        self.assertEquals(['/test/a', '/test/c', '/test/b'], result)

    def test_sort_depend_on_self(self):
        values = [
            nso.ValueBuilder.Value('/test/a', '/test/a', 'VALUE', ['/test/a']),
            nso.ValueBuilder.Value('/test/b', '/test/b', 'VALUE', [])
        ]

        result = [v.path for v in nso.ValueBuilder.sort_values(values)]

        self.assertEqual(['/test/a', '/test/b'], result)
