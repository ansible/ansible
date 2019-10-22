#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_snmp_users
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxSNMPUsersModule(TestOnyxModule):

    module = onyx_snmp_users

    def setUp(self):
        self.enabled = False
        super(TestOnyxSNMPUsersModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_snmp_users.OnyxSNMPUsersModule, "_show_users")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxSNMPUsersModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_snmp_users.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_snmp_user_state_no_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         enabled='true')]))
        self.execute_module(changed=False)

    def test_snmp_user_state_with_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         enabled='false')]))
        commands = ['no snmp-server user sara v3 enable']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_user_set_access_state_no_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         set_access_enabled='true')]))
        self.execute_module(changed=False)

    def test_snmp_user_set_access_state_with_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         set_access_enabled='false')]))
        commands = ['no snmp-server user sara v3 enable sets']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_user_require_privacy_state_no_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         require_privacy='false')]))
        self.execute_module(changed=False)

    def test_snmp_user_require_privacy_state_with_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         require_privacy='yes')]))
        commands = ['snmp-server user sara v3 require-privacy']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_user_auth_type_no_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         auth_type='sha',
                                         auth_password='12sara123456')]))
        self.execute_module(changed=False)

    def test_snmp_user_auth_type_with_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         auth_type='md5',
                                         auth_password='12sara123456')]))
        commands = ['snmp-server user sara v3 auth md5 12sara123456']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_user_capability_level_no_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         capability_level='admin')]))
        self.execute_module(changed=False)

    def test_snmp_user_capability_level_with_change(self):
        set_module_args(dict(users=[dict(name='sara',
                                         capability_level='monitor')]))
        commands = ['snmp-server user sara v3 capability monitor']
        self.execute_module(changed=True, commands=commands)
