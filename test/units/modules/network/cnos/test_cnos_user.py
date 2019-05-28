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
from ansible.modules.network.cnos import cnos_user
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosUserModule(TestCnosModule):

    module = cnos_user

    def setUp(self):
        super(TestCnosUserModule, self).setUp()
        self.mock_get_config = patch('ansible.modules.network.cnos.cnos_user.get_config')
        self.get_config = self.mock_get_config.start()
        self.mock_load_config = patch('ansible.modules.network.cnos.cnos_user.load_config')
        self.load_config = self.mock_load_config.start()
        self.mock_run_commands = patch('ansible.modules.network.cnos.cnos_user.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestCnosUserModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('cnos_user_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')
        self.run_commands.return_value = [load_fixture('cnos_user_config.cfg')]

    def test_cnos_user_create(self):
        set_module_args(dict(name='test', configured_password='Anil'))
        commands = ['username test', 'username test password Anil']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_user_delete(self):
        set_module_args(dict(name='ansible', state='absent'))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_cnos_user_password(self):
        set_module_args(dict(name='ansible', configured_password='test'))
        commands = ['username ansible', 'username ansible password test']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_user_purge(self):
        set_module_args(dict(purge=True))
        commands = ['no username admin\n', 'no username ansible\n']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_user_role(self):
        set_module_args(dict(name='ansible', role='network-admin', configured_password='test'))
        result = self.execute_module(changed=True)
        self.assertIn('username ansible role network-admin', result['commands'])

    def test_cnos_user_sshkey(self):
        set_module_args(dict(name='ansible', sshkey='test'))
        commands = ['username ansible', 'username ansible sshkey test']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_user_update_password_changed(self):
        set_module_args(dict(name='test', configured_password='test', update_password='on_create'))
        commands = ['username test', 'username test password test']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_user_update_password_always(self):
        set_module_args(dict(name='ansible', configured_password='test', update_password='always'))
        commands = ['username ansible', 'username ansible password test']
        self.execute_module(changed=True, commands=commands)
