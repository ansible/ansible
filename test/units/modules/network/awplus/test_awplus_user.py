# (c) 2020 Allied Telesis
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.awplus import awplus_user
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusUserModule(TestAwplusModule):

    module = awplus_user

    def setUp(self):
        super(TestAwplusUserModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_user.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_user.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestAwplusUserModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('awplus_user_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

    def test_awplus_user_create(self):
        set_module_args(dict(name='test', configured_password='test'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['username test password test'])

    def test_awplus_user_delete(self):
        set_module_args(dict(name='ansible', state='absent'))
        result = self.execute_module(changed=True)
        cmds = [
            {
                "command": "no username ansible", "answer": "y", "newline": False,
                "prompt": "This operation will remove all username related configurations with same name",
            }
        ]

        result_cmd = []
        for i in result['commands']:
            result_cmd.append(i)

        self.assertEqual(result_cmd, cmds)

    def test_awplus_user_password(self):
        set_module_args(dict(name='ansible', configured_password='test'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
                         'username ansible password test'])

    def test_awplus_user_privilege(self):
        set_module_args(dict(name='test', privilege=15))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['username test privilege 15'])

    def test_awplus_user_privilege_invalid(self):
        set_module_args(dict(name='ansible', privilege=25))
        self.execute_module(failed=True)

    def test_awplus_user_purge(self):
        set_module_args(dict(purge=True, name='manager'))
        result = self.execute_module(changed=True)
        cmd = {
            "command": "no username ansible", "answer": "y", "newline": False,
            "prompt": "This operation will remove all username related configurations with same name",
        }

        result_cmd = []
        for i in result['commands']:
            result_cmd.append(i)

        self.assertEqual(result_cmd, [cmd])
