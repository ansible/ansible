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
from ansible.modules.network.iosxr import iosxr_user
from units.modules.utils import set_module_args
from .iosxr_module import TestIosxrModule, load_fixture


class TestIosxrUserModule(TestIosxrModule):

    module = iosxr_user

    def setUp(self):
        super(TestIosxrUserModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.iosxr.iosxr_user.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.iosxr.iosxr_user.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_is_cliconf = patch('ansible.modules.network.iosxr.iosxr_user.is_cliconf')
        self.is_cliconf = self.mock_is_cliconf.start()

    def tearDown(self):
        super(TestIosxrUserModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_is_cliconf.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('iosxr_user_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')
        self.is_cliconf.return_value = True

    def test_iosxr_user_delete(self):
        set_module_args(dict(name='ansible', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no username ansible'])

    def test_iosxr_user_password(self):
        set_module_args(dict(name='ansible', configured_password='test'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['username ansible secret test'])

    def test_iosxr_user_purge(self):
        set_module_args(dict(purge=True))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no username ansible'])

    def test_iosxr_user_group(self):
        set_module_args(dict(name='ansible', group='sysadmin'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['username ansible group sysadmin'])

    def test_iosxr_user_update_password_changed(self):
        set_module_args(dict(name='test', configured_password='test', update_password='on_create'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'],
                         ['username test', 'username test secret test'])

    def test_iosxr_user_update_password_on_create_ok(self):
        set_module_args(dict(name='ansible', configured_password='test', update_password='on_create'))
        self.execute_module()

    def test_iosxr_user_update_password_always(self):
        set_module_args(dict(name='ansible', configured_password='test', update_password='always'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['username ansible secret test'])

    def test_iosxr_user_admin_mode(self):
        set_module_args(dict(name='ansible-2', configured_password='test-2', admin=True))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['username ansible-2', 'username ansible-2 secret test-2'])
