# (c) 2016 Red Hat Inc.
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
from ansible.modules.network.vyos import vyos_user
from units.modules.utils import set_module_args
from .vyos_module import TestVyosModule, load_fixture


class TestVyosUserModule(TestVyosModule):

    module = vyos_user

    def setUp(self):
        super(TestVyosUserModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.vyos.vyos_user.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.vyos.vyos_user.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestVyosUserModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('vyos_user_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

    def test_vyos_user_password(self):
        set_module_args(dict(name='ansible', configured_password='test'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['set system login user ansible authentication plaintext-password test'])

    def test_vyos_user_delete(self):
        set_module_args(dict(name='ansible', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['delete system login user ansible'])

    def test_vyos_user_level(self):
        set_module_args(dict(name='ansible', level='operator'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['set system login user ansible level operator'])

    def test_vyos_user_level_invalid(self):
        set_module_args(dict(name='ansible', level='sysadmin'))
        self.execute_module(failed=True)

    def test_vyos_user_purge(self):
        set_module_args(dict(purge=True))
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['commands']), sorted(['delete system login user ansible',
                                                             'delete system login user admin']))

    def test_vyos_user_update_password_changed(self):
        set_module_args(dict(name='test', configured_password='test', update_password='on_create'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['set system login user test authentication plaintext-password test'])

    def test_vyos_user_update_password_on_create_ok(self):
        set_module_args(dict(name='ansible', configured_password='test', update_password='on_create'))
        self.execute_module()

    def test_vyos_user_update_password_always(self):
        set_module_args(dict(name='ansible', configured_password='test', update_password='always'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['set system login user ansible authentication plaintext-password test'])
