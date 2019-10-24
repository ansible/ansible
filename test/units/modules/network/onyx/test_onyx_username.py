#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_username
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxUsernameModule(TestOnyxModule):

    module = onyx_username

    def setUp(self):
        self.enabled = False
        super(TestOnyxUsernameModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_username.OnyxUsernameModule, "_get_username_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxUsernameModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_username_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_new_username(self):
        set_module_args(dict(username='test'))
        commands = ['username test']
        self.execute_module(changed=True, commands=commands)

    def test_change_full_username(self):
        set_module_args(dict(username='anass', full_name="anasshami"))
        commands = ['username anass full-name anasshami']
        self.execute_module(changed=True, commands=commands)

    def test_change_username_password(self):
        set_module_args(dict(username='anass', password="12345"))
        commands = ['username anass password 12345']
        self.execute_module(changed=True, commands=commands)

    def test_change_username_password_encrypted(self):
        set_module_args(dict(username='anass', password="12345", encrypted_password=True))
        commands = ['username anass password 7 12345']
        self.execute_module(changed=True, commands=commands)

    def test_disable_username(self):
        set_module_args(dict(username='anass', disabled="all"))
        commands = ['username anass disable']
        self.execute_module(changed=True, commands=commands)

    def test_disable_username_login(self):
        set_module_args(dict(username='anass', disabled="login"))
        commands = ['username anass disable login']
        self.execute_module(changed=True, commands=commands)

    def test_disable_username_password(self):
        set_module_args(dict(username='anass', disabled="password"))
        commands = ['username anass disable password']
        self.execute_module(changed=True, commands=commands)

    def test_change_username_capability(self):
        set_module_args(dict(username='anass', capability="monitor"))
        commands = ['username anass capability monitor']
        self.execute_module(changed=True, commands=commands)

    def test_disconnect_username(self):
        set_module_args(dict(username='anass', disconnected=True))
        commands = ['username anass disconnect']
        self.execute_module(changed=True, commands=commands)

    def test_no_change_username_capability(self):
        set_module_args(dict(username='anass', capability="admin"))
        self.execute_module(changed=False)

    def test_no_change_username_disabled(self):
        set_module_args(dict(username='anassh', disabled="all"))
        self.execute_module(changed=False)

    def test_no_change_username_nopass(self):
        set_module_args(dict(username='admin', nopassword=True))
        self.execute_module(changed=False)

    def test_no_change_full_username(self):
        set_module_args(dict(username='admin', full_name="System Administrator"))
        self.execute_module(changed=False)
