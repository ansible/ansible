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

from ansible.compat.tests.mock import patch
from ansible.modules.network.nso import nso_query
from . import nso_module
from .nso_module import MockResponse

from units.modules.utils import set_module_args


class TestNsoQuery(nso_module.TestNsoModule):
    module = nso_query

    @patch('ansible.module_utils.network.nso.nso.open_url')
    def test_nso_query(self, open_url_mock):
        xpath = '/packages/package'
        fields = ['name', 'package-version']
        calls = [
            MockResponse('login', {}, 200, '{}', {'set-cookie': 'id'}),
            MockResponse('get_system_setting', {'operation': 'version'}, 200, '{"result": "4.5"}'),
            MockResponse('new_trans', {'mode': 'read'}, 200, '{"result": {"th": 1}}'),
            MockResponse('query',
                         {'xpath_expr': xpath, 'selection': fields}, 200,
                         '{"result": {"results": [["test", "1.0"]]}}'),
            MockResponse('logout', {}, 200, '{"result": {}}'),
        ]
        open_url_mock.side_effect = lambda *args, **kwargs: nso_module.mock_call(calls, *args, **kwargs)

        set_module_args({
            'username': 'user', 'password': 'password',
            'url': 'http://localhost:8080/jsonrpc',
            'xpath': xpath,
            'fields': fields
        })
        self.execute_module(changed=False, output=[["test", "1.0"]])

        self.assertEqual(0, len(calls))
