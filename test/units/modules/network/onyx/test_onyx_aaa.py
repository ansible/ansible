#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_aaa
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxAAAModule(TestOnyxModule):

    module = onyx_aaa

    def setUp(self):
        self.enabled = False
        super(TestOnyxAAAModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_aaa.OnyxAAAModule, "_show_aaa_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxAAAModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_aaa.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_aaa_accounting_no_change(self):
        set_module_args(dict(tacacs_accounting_enabled=False))
        self.execute_module(changed=False)

    def test_aaa_accounting_with_change(self):
        set_module_args(dict(tacacs_accounting_enabled=True))
        commands = ['aaa accounting changes default stop-only tacacs+']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_auth_default_user_no_change(self):
        set_module_args(dict(auth_default_user='admin'))
        self.execute_module(changed=False)

    def test_aaa_auth_default_user_with_change(self):
        set_module_args(dict(auth_default_user='monitor'))
        commands = ['aaa authorization map default-user monitor']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_auth_order_no_change(self):
        set_module_args(dict(auth_order='remote-first'))
        self.execute_module(changed=False)

    def test_aaa_auth_order_with_change(self):
        set_module_args(dict(auth_order='local-only'))
        commands = ['aaa authorization map order local-only']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_fallback_no_change(self):
        set_module_args(dict(auth_fallback_enabled=True))
        self.execute_module(changed=False)

    def test_aaa_fallback_with_change(self):
        set_module_args(dict(auth_fallback_enabled=False))
        commands = ['no aaa authorization map fallback server-err']
        self.execute_module(changed=True, commands=commands)
