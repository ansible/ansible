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
from ansible.modules.network.nso import nso_config
from units.modules.utils import set_module_args
from . import nso_module
from .nso_module import MockResponse


class TestNsoConfig(nso_module.TestNsoModule):
    module = nso_config

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_config_invalid_version_short(self, open_url_mock):
        self._test_invalid_version(open_url_mock, '3.3')

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_config_invalid_version_long(self, open_url_mock):
        self._test_invalid_version(open_url_mock, '3.3.2')

    def _test_invalid_version(self, open_url_mock, version):
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "%s"}' % (version, )),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        data = nso_module.load_fixture('config_config.json')
        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc', 'data': data,
            'validate_certs': False
        })
        self.execute_module(failed=True)

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_config_valid_version_short(self, open_url_mock):
        self._test_valid_version(open_url_mock, '4.5')

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_config_valid_version_long(self, open_url_mock):
        self._test_valid_version(open_url_mock, '4.4.3')

    def _test_valid_version(self, open_url_mock, version):
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "%s"}' % (version, )),
            MockResponse('new_trans', {}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_trans_changes', {}, 200, '{"result": {"changes": []}}'),
            MockResponse('delete_trans', {}, 200, '{"result": {}}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        data = nso_module.load_fixture('config_empty_data.json')
        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc', 'data': data,
            'validate_certs': False
        })
        self.execute_module(changed=False, changes=[], diffs=[])

        self.assertEqual(0, len(calls))

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_config_changed(self, open_url_mock):
        vpn_schema = nso_module.load_fixture('l3vpn_schema.json')
        l3vpn_schema = nso_module.load_fixture('l3vpn_l3vpn_schema.json')
        endpoint_schema = nso_module.load_fixture('l3vpn_l3vpn_endpoint_schema.json')
        changes = nso_module.load_fixture('config_config_changes.json')

        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5.1"}'),
            MockResponse('get_module_prefix_map', {}, 200, '{"result": {"l3vpn": "l3vpn"}}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('get_schema', {'path': '/l3vpn:vpn'}, 200, '{"result": %s}' % (json.dumps(vpn_schema, ))),
            MockResponse('get_schema', {'path': '/l3vpn:vpn/l3vpn'}, 200, '{"result": %s}' % (json.dumps(l3vpn_schema, ))),
            MockResponse('exists', {'path': '/l3vpn:vpn/l3vpn{company}'}, 200, '{"result": {"exists": true}}'),
            MockResponse('get_schema', {'path': '/l3vpn:vpn/l3vpn/endpoint'}, 200, '{"result": %s}' % (json.dumps(endpoint_schema, ))),
            MockResponse('exists', {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}'}, 200, '{"result": {"exists": false}}'),
            MockResponse('new_trans', {'mode': 'read_write'}, 200, '{"result": {"th": 2}}'),
            MockResponse('create', {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}'}, 200, '{"result": {}}'),
            MockResponse('set_value', {'path': '/l3vpn:vpn/l3vpn{company}/route-distinguisher', 'value': 999}, 200, '{"result": {}}'),
            MockResponse('set_value', {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/as-number', 'value': 65101}, 200, '{"result": {}}'),
            MockResponse('set_value', {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/bandwidth', 'value': 12000000}, 200, '{"result": {}}'),
            MockResponse('set_value', {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/ce-device', 'value': 'ce6'}, 200, '{"result": {}}'),
            MockResponse('set_value', {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/ce-interface',
                                       'value': 'GigabitEthernet0/12'}, 200, '{"result": {}}'),
            MockResponse('set_value', {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/ip-network',
                                       'value': '10.10.1.0/24'}, 200, '{"result": {}}'),
            MockResponse('get_trans_changes', {}, 200, '{"result": %s}' % (json.dumps(changes), )),
            MockResponse('validate_commit', {}, 200, '{"result": {}}'),
            MockResponse('commit', {}, 200, '{"result": {}}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        data = nso_module.load_fixture('config_config.json')
        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc', 'data': data,
            'validate_certs': False
        })
        self.execute_module(changed=True, changes=[
            {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/ce-device', 'type': 'set', 'from': None, 'to': 'ce6'},
            {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/ip-network', 'type': 'set', 'from': None, 'to': '10.10.1.0/24'},
            {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/as-number', 'type': 'set', 'from': None, 'to': '65101'},
            {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/ce-interface', 'type': 'set', 'from': None, 'to': 'GigabitEthernet0/12'},
            {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}/bandwidth', 'type': 'set', 'from': None, 'to': '12000000'},
            {'path': '/l3vpn:vpn/l3vpn{company}/endpoint{branch-office1}', 'type': 'create'},
        ], diffs=[])

        self.assertEqual(0, len(calls))
