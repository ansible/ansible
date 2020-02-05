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

from __future__ import (absolute_import, division, print_function)

import os
import json

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)
    if path not in fixture_data:
        with open(path) as f:
            data = json.load(f)
        fixture_data[path] = data
    return fixture_data[path]


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


def mock_call(calls, url, timeout, validate_certs, data=None, headers=None, method=None):
    if len(calls) == 0:
        raise ValueError('no call mock for method {0}({1})'.format(
            url, data))

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


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


class TestNsoModule(unittest.TestCase):

    def execute_module(self, failed=False, changed=False, **kwargs):
        if failed:
            result = self.failed()
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed)
            self.assertEqual(result['changed'], changed, result)

        for key, value in kwargs.items():
            if key not in result:
                self.fail("{0} not in result {1}".format(key, result))
            self.assertEqual(value, result[key])

        return result

    def failed(self):
        def fail_json(*args, **kwargs):
            kwargs['failed'] = True
            raise AnsibleFailJson(kwargs)

        with patch.object(basic.AnsibleModule, 'fail_json', fail_json):
            with self.assertRaises(AnsibleFailJson) as exc:
                self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def changed(self, changed=False):
        def exit_json(*args, **kwargs):
            if 'changed' not in kwargs:
                kwargs['changed'] = False
            raise AnsibleExitJson(kwargs)

        with patch.object(basic.AnsibleModule, 'exit_json', exit_json):
            with self.assertRaises(AnsibleExitJson) as exc:
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], changed, result)
        return result
