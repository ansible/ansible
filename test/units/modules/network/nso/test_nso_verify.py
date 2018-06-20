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

from ansible.compat.tests.mock import patch
from ansible.modules.network.nso import nso_verify
from . import nso_module
from .nso_module import MockResponse

from units.modules.utils import set_module_args


class TestNsoVerify(nso_module.TestNsoModule):
    module = nso_verify

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_verify_empty_data(self, open_url_mock):
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.4.3"}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        data = {}
        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc', 'data': data
        })
        self.execute_module(changed=False)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_verify_violation(self, open_url_mock):
        devices_schema = nso_module.load_fixture('devices_schema.json')
        device_schema = nso_module.load_fixture('device_schema.json')
        description_schema = nso_module.load_fixture('description_schema.json')

        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5.0"}'),
            MockResponse('get_module_prefix_map', {}, 200, '{"result": {"tailf-ncs": "ncs"}}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_schema', {'path': '/ncs:devices'}, 200, '{"result": %s}' % (json.dumps(devices_schema, ))),
            MockResponse('get_schema', {'path': '/ncs:devices/device'}, 200, '{"result": %s}' % (json.dumps(device_schema, ))),
            MockResponse('exists', {'path': '/ncs:devices/device{ce0}'}, 200, '{"result": {"exists": true}}'),
            MockResponse('get_value', {'path': '/ncs:devices/device{ce0}/description'}, 200, '{"result": {"value": "In Violation"}}'),
            MockResponse('get_schema', {'path': '/ncs:devices/device/description'}, 200, '{"result": %s}' % (json.dumps(description_schema, ))),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        data = nso_module.load_fixture('verify_violation_data.json')
        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc', 'data': data
        })
        self.execute_module(failed=True, violations=[
            {'path': '/ncs:devices/device{ce0}/description', 'expected-value': 'Example Device', 'value': 'In Violation'},
        ])

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_verify_ok(self, open_url_mock):
        devices_schema = nso_module.load_fixture('devices_schema.json')
        device_schema = nso_module.load_fixture('device_schema.json')

        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5.0"}'),
            MockResponse('get_module_prefix_map', {}, 200, '{"result": {"tailf-ncs": "ncs"}}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_schema', {'path': '/ncs:devices'}, 200, '{"result": %s}' % (json.dumps(devices_schema, ))),
            MockResponse('get_schema', {'path': '/ncs:devices/device'}, 200, '{"result": %s}' % (json.dumps(device_schema, ))),
            MockResponse('exists', {'path': '/ncs:devices/device{ce0}'}, 200, '{"result": {"exists": true}}'),
            MockResponse('get_value', {'path': '/ncs:devices/device{ce0}/description'}, 200, '{"result": {"value": "Example Device"}}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        data = nso_module.load_fixture('verify_violation_data.json')
        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc', 'data': data
        })
        self.execute_module(changed=False)

        self.assertEqual(0, len(calls))
