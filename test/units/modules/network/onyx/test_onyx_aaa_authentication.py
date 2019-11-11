#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_aaa_authentication
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxAaaAuthenticationModule(TestOnyxModule):

    module = onyx_aaa_authentication

    def setUp(self):
        self.enabled = False
        super(TestOnyxAaaAuthenticationModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_aaa_authentication.OnyxAaaAuthenticationModule, "_show_aaa_auth_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxAaaAuthenticationModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_aaa_authentication.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_aaa_auth_login_no_change(self):
        set_module_args(dict(auth_login_method1='local',
                             auth_login_method2='ldap',
                             auth_login_method3='tacacs+',
                             auth_login_method4='radius'))
        self.execute_module(changed=False)

    def test_aaa_auth_login_with_change(self):
        set_module_args(dict(auth_login_method1='local',
                             auth_login_method2='ldap',
                             auth_login_method3='local',
                             auth_login_method4='ldap'))
        commands = ['aaa authentication login default local ldap local ldap']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_fail_delay_no_change(self):
        set_module_args(dict(auth_fail_delay_time=55))
        self.execute_module(changed=False)

    def test_aaa_fail_delay_with_change(self):
        set_module_args(dict(auth_fail_delay_time=50))
        commands = ['aaa authentication attempts fail-delay 50']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_auth_track_no_change(self):
        set_module_args(dict(auth_track_enabled=True))
        self.execute_module(changed=False)

    def test_aaa_auth_track_with_change(self):
        set_module_args(dict(auth_track_enabled=False))
        commands = ['no aaa authentication attempts track enable']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_auth_track_downcase_no_change(self):
        set_module_args(dict(track_downcase_enabled=False))
        self.execute_module(changed=False)

    def test_aaa_auth_track_downcase_with_change(self):
        set_module_args(dict(track_downcase_enabled=True))
        commands = ['aaa authentication attempts track downcase']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_auth_track_reset_all_with_change(self):
        set_module_args(dict(reset_for='all',
                             reset_type='no-unlock'))
        commands = ['aaa authentication attempts reset all no-unlock']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_auth_track_reset_user_with_change(self):
        set_module_args(dict(reset_for='user',
                             user_name='sara',
                             reset_type='no-unlock'))
        commands = ['aaa authentication attempts reset user sara no-unlock']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_auth_admin_lockout_no_change(self):
        set_module_args(dict(admin_no_lockout_enabled=True))
        self.execute_module(changed=False)

    def test_aaa_auth_admin_lockout_with_change(self):
        set_module_args(dict(admin_no_lockout_enabled=False))
        commands = ['no aaa authentication attempts class-override admin no-lockout']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_unknown_account_hash_username_no_change(self):
        set_module_args(dict(unknown_account_hash_username_enabled=False))
        self.execute_module(changed=False)

    def test_aaa_unknown_account_hash_username_with_change(self):
        set_module_args(dict(unknown_account_hash_username_enabled=True))
        commands = ['aaa authentication attempts class-override unknown hash-username']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_unknown_account_track_no_change(self):
        set_module_args(dict(unknown_account_no_track_enabled=True))
        self.execute_module(changed=False)

    def test_aaa_unknown_account_track_with_change(self):
        set_module_args(dict(unknown_account_no_track_enabled=False))
        commands = ['no aaa authentication attempts class-override unknown no-track']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_lock_state_no_change(self):
        set_module_args(dict(lockout_enabled=True))
        self.execute_module(changed=False)

    def test_aaa_lock_state_with_change(self):
        set_module_args(dict(lockout_enabled=False))
        commands = ['no aaa authentication attempts lockout enable']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_lock_time_no_change(self):
        set_module_args(dict(lock_time=66))
        self.execute_module(changed=False)

    def test_aaa_lock_time_with_change(self):
        set_module_args(dict(lock_time=60))
        commands = ['aaa authentication attempts lockout lock-time 60']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_unlock_time_no_change(self):
        set_module_args(dict(unlock_time=66))
        self.execute_module(changed=False)

    def test_aaa_unlock_time_with_change(self):
        set_module_args(dict(unlock_time=50))
        commands = ['aaa authentication attempts lockout unlock-time 50']
        self.execute_module(changed=True, commands=commands)

    def test_aaa_max_failure_account_no_change(self):
        set_module_args(dict(max_failure_account=55))
        self.execute_module(changed=False)

    def test_aaa_max_failure_account_with_change(self):
        set_module_args(dict(max_failure_account=59))
        commands = ['aaa authentication attempts lockout max-fail 59']
        self.execute_module(changed=True, commands=commands)
