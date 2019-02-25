#
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

import json

from units.compat.mock import patch
from ansible.modules.network.nso import nso_action
from . import nso_module
from .nso_module import MockResponse

from units.modules.utils import set_module_args


class TestNsoAction(nso_module.TestNsoModule):
    module = nso_action

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_action_missing(self, open_url_mock):
        action_input = {}
        path = '/ncs:devices/device{ce0}/missing'
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5.0"}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_schema', {'path': path}, 200, '{"error": {"data": {"param": "path"}, "type": "rpc.method.invalid_params"}}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc',
            'path': path,
            'input': action_input,
            'validate_certs': False
        })
        self.execute_module(failed=True, msg='NSO get_schema invalid params. path = /ncs:devices/device{ce0}/missing')

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_action_not_action(self, open_url_mock):
        action_input = {}
        path = '/ncs:devices/device{ce0}/description'
        schema = nso_module.load_fixture('description_schema.json')
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5.0"}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_schema', {'path': path}, 200, '{"result": %s}' % (json.dumps(schema, ))),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc',
            'path': path,
            'input': action_input,
            'validate_certs': False
        })
        self.execute_module(failed=True, msg='/ncs:devices/device{ce0}/description is not an action')

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_action_ok(self, open_url_mock):
        action_input = {}
        path = '/ncs:devices/device{ce0}/sync-from'
        output = {"result": True}
        schema = nso_module.load_fixture('sync_from_schema.json')
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5.0"}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_schema', {'path': path}, 200, '{"result": %s}' % (json.dumps(schema, ))),
            MockResponse('run_action', {'path': path, 'params': action_input}, 200, '{"result": {"result": true}}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc',
            'path': path,
            'input': action_input,
            'validate_certs': False
        })
        self.execute_module(changed=True, output=output)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_action_validate_ok(self, open_url_mock):
        action_input = {}
        path = '/test:action'
        output = {'version': [{'name': 'v1'}, {'name': 'v2'}]}
        schema = nso_module.load_fixture('complex_schema.json')
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5.0"}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_schema', {'path': path}, 200, '{"result": %s}' % (json.dumps(schema, ))),
            MockResponse('run_action', {'path': path, 'params': action_input}, 200,
                         '{"result": {"version": [{"name": "v1"}, {"name": "v2"}]}}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc',
            'path': path,
            'input': action_input,
            'output_required': output,
            'validate_certs': False
        })
        self.execute_module(changed=True, output=output)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_action_validate_failed(self, open_url_mock):
        action_input = {}
        path = '/test:action'
        output_mismatch = {'version': [{'name': 'v1'}, {'name': 'v3'}]}
        schema = nso_module.load_fixture('complex_schema.json')
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5.0"}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_schema', {'path': path}, 200, '{"result": %s}' % (json.dumps(schema, ))),
            MockResponse('run_action', {'path': path, 'params': action_input}, 200,
                         '{"result": {"version": [{"name": "v1"}, {"name": "v2"}]}}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc',
            'path': path,
            'input': action_input,
            'output_required': output_mismatch,
            'validate_certs': False
        })
        self.execute_module(failed=True, msg="version value mismatch. expected [{'name': 'v1'}, {'name': 'v3'}] got [{'name': 'v1'}, {'name': 'v2'}]")

        self.assertEqual(0, len(calls))
