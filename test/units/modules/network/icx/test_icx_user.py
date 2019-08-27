# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.icx import icx_user
from units.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXSCPModule(TestICXModule):

    module = icx_user

    def setUp(self):
        super(TestICXSCPModule, self).setUp()
        self.mock_get_config = patch('ansible.modules.network.icx.icx_user.get_config')
        self.get_config = self.mock_get_config.start()
        self.mock_load_config = patch('ansible.modules.network.icx.icx_user.load_config')
        self.load_config = self.mock_load_config.start()
        self.mock_exec_command = patch('ansible.modules.network.icx.icx_user.exec_command')
        self.exec_command = self.mock_exec_command.start()
        self.set_running_config()

    def tearDown(self):
        super(TestICXSCPModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_exec_command.stop()

    def load_fixtures(self, commands=None):
        compares = None

        def load_file(*args, **kwargs):
            module = args
            for arg in args:
                if arg.params['check_running_config'] is True:
                    return load_fixture('show_running-config_include_username.txt').strip()
                else:
                    return ''
        self.get_config.side_effect = load_file
        self.load_config.return_value = None

    def test_icx_user_create_new_with_password(self):
        set_module_args(dict(name='ale6', configured_password='alethea123'))
        if not self.ENV_ICX_USE_DIFF:
            commands = ['username ale6 password alethea123']
            self.execute_module(commands=commands, changed=True)
        else:
            commands = ['username ale6 password alethea123']
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_create_new_with_password_and_privilege(self):
        set_module_args(dict(name='ale6', privilege="5", configured_password='alethea123'))
        if not self.ENV_ICX_USE_DIFF:
            commands = ['username ale6 privilege 5 password alethea123']
            self.execute_module(commands=commands, changed=True)
        else:
            commands = ['username ale6 privilege 5 password alethea123']
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_update_privilege(self):
        set_module_args(dict(name='ale1', privilege="0", configured_password='alethea123'))
        if not self.ENV_ICX_USE_DIFF:
            commands = ['username ale1 privilege 0 password alethea123']
            self.execute_module(commands=commands, changed=True)
        else:
            commands = ['username ale1 privilege 0 password alethea123']
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_update_password(self):
        set_module_args(dict(name='ale1', configured_password='alethea123'))
        if not self.ENV_ICX_USE_DIFF:
            commands = ['username ale1 password alethea123']  # previous privilage will be added
            self.execute_module(commands=commands, changed=True)
        else:
            commands = ['username ale1 privilege 5 password alethea123']  # previous privilage will be added
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_update_password_compare(self):
        set_module_args(dict(name='ale1', configured_password='alethea123', check_running_config=True))
        if not self.ENV_ICX_USE_DIFF:
            commands = ['username ale1 privilege 5 password alethea123']  # previous privilage will be added
            self.execute_module(commands=commands, changed=True)
        else:
            commands = ['username ale1 privilege 5 password alethea123']  # previous privilage will be added
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_delete_user(self):
        set_module_args(dict(name='ale1', state="absent"))
        if not self.ENV_ICX_USE_DIFF:
            commands = ['no username ale1']
            self.execute_module(commands=commands, changed=True)
        else:
            commands = ['no username ale1']
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_agregate(self):
        set_module_args(dict(aggregate=[
            {
                "name": 'ale6',
                "configured_password": 'alethea123'
            },
            {
                "name": 'ale7',
                "configured_password": 'alethea123'
            }
        ]))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'username ale6 password alethea123',
                'username ale7 password alethea123'
            ]
            self.execute_module(commands=commands, changed=True)
        else:
            commands = [
                'username ale6 password alethea123',
                'username ale7 password alethea123'
            ]
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_not_update_old_user_password(self):
        set_module_args(dict(aggregate=[
            {
                "name": 'ale6',
                "configured_password": 'alethea123'
            },
            {
                "name": 'ale1',
                "configured_password": 'alethea123',
            },
        ],
            update_password='on_create'
        ))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'username ale1 password alethea123',
                'username ale6 password alethea123',
            ]
            self.execute_module(commands=commands, changed=True)
        else:
            commands = [
                'username ale6 password alethea123',
            ]
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_only_update_changed_settings(self):
        set_module_args(dict(aggregate=[
            {
                "name": 'ale1'
            },
            {
                "name": 'ale2',
                "privilege": 5,
                "configured_password": "ale123"
            },
            {
                "name": 'ale3',
                "privilege": 4,
                "configured_password": "ale123"
            }
        ],
            update_password="on_create"
        ))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'username ale2 privilege 5 password ale123',
                'username ale3 privilege 4 password ale123'
            ]
            self.execute_module(commands=commands, changed=True)
        else:
            commands = [
                'username ale3 privilege 4 password ale123'
            ]
            self.execute_module(commands=commands, changed=True)

    def test_icx_user_purge(self):
        set_module_args(dict(aggregate=[
            {
                "name": 'ale1'
            }
        ],
            purge=True
        ))
        if not self.ENV_ICX_USE_DIFF:
            commands = [

            ]
            self.execute_module(commands=commands, changed=False)
        else:
            commands = [
                'no username ale2',
                'no username ale3',
                'no username ale4'
            ]
            self.execute_module(commands=commands, changed=True)
