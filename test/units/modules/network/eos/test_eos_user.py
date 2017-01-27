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

import os
import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.errors import AnsibleModuleExit
from ansible.modules.network.eos import eos_user
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}

def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except:
        pass

    fixture_data[path] = data
    return data


class TestEosUserModule(unittest.TestCase):

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.eos.eos_user.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_user.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def execute_module(self, failed=False, changed=False, commands=None, sort=True):

        self.get_config.return_value = load_fixture('eos_user_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

        with self.assertRaises(AnsibleModuleExit) as exc:
            eos_user.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result['failed'], result)
        else:
            self.assertEqual(result['changed'], changed, result)

        if commands:
            if sort:
                self.assertEqual(sorted(commands), sorted(result['commands']), result['commands'])
            else:
                self.assertEqual(commands, result['commands'])

        return result

    def test_eos_user_create(self):
        set_module_args(dict(username='test', nopassword=True))
        commands = ['username test nopassword']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_delete(self):
        set_module_args(dict(username='ansible', state='absent'))
        commands = ['no username ansible']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_password(self):
        set_module_args(dict(username='ansible', password='test'))
        commands = ['username ansible secret ********']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_privilege(self):
        set_module_args(dict(username='ansible', privilege=15))
        commands = ['username ansible privilege 15']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_privilege_invalid(self):
        set_module_args(dict(username='ansible', privilege=25))
        self.execute_module(failed=True)

    def test_eos_user_purge(self):
        set_module_args(dict(purge=True))
        commands = ['no username ansible']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_role(self):
        set_module_args(dict(username='ansible', role='test'))
        commands = ['username ansible role test']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_sshkey(self):
        set_module_args(dict(username='ansible', sshkey='test'))
        commands = ['username ansible sshkey test']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_update_password_changed(self):
        set_module_args(dict(username='test', password='test', update_password='on_create'))
        commands = ['username ******** secret ********']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_update_password_on_create_ok(self):
        set_module_args(dict(username='ansible', password='test', update_password='on_create'))
        commands = []
        self.execute_module(commands=commands)

    def test_eos_user_update_password_always(self):
        set_module_args(dict(username='ansible', password='test', update_password='always'))
        commands = ['username ansible secret ********']
        self.execute_module(changed=True, commands=commands)


