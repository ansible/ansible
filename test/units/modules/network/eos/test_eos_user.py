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

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.eos import eos_user
from .eos_module import TestEosModule, load_fixture, set_module_args


class TestEosUserModule(TestEosModule):

    module = eos_user

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.eos.eos_user.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_user.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('eos_user_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

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
        commands = ['username ansible secret test']
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
        commands = ['username test secret test']
        self.execute_module(changed=True, commands=commands)

    def test_eos_user_update_password_on_create_ok(self):
        set_module_args(dict(username='ansible', password='test', update_password='on_create'))
        self.execute_module()

    def test_eos_user_update_password_always(self):
        set_module_args(dict(username='ansible', password='test', update_password='always'))
        commands = ['username ansible secret test']
        self.execute_module(changed=True, commands=commands)


