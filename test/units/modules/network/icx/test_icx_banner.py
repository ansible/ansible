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
from ansible.compat.tests.mock import patch
from ansible.modules.network.icx import icx_banner
from units.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXBannerModule(TestICXModule):

    module = icx_banner

    def setUp(self):
        super(TestICXBannerModule, self).setUp()
        self.mock_exec_command = patch('ansible.modules.network.icx.icx_banner.exec_command')
        self.exec_command = self.mock_exec_command.start()

        self.mock_load_config = patch('ansible.modules.network.icx.icx_banner.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.icx.icx_banner.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_get_env_diff = patch('ansible.modules.network.icx.icx_banner.get_env_diff')
        self.get_env_diff = self.mock_get_env_diff.start()
        self.set_running_config()

    def tearDown(self):
        super(TestICXBannerModule, self).tearDown()
        self.mock_exec_command.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()
        self.mock_get_env_diff.stop()

    def load_fixtures(self, commands=None):
        compares = None

        def load_file(*args, **kwargs):
            module = args
            for arg in args:
                if arg.params['check_running_config'] is not None:
                    compares = arg.params['check_running_config']
                    break
                else:
                    compares = None
            env = self.get_running_config(compares)
            self.get_env_diff.return_value = self.get_running_config(compare=compares)
            if env is True:
                return load_fixture('icx_banner_show_banner.txt').strip()
            else:
                return ''

        self.exec_command.return_value = (0, '', None)
        self.get_config.side_effect = load_file
        self.load_config.return_value = dict(diff=None, session='session')

    def test_icx_banner_create(self):
        if not self.ENV_ICX_USE_DIFF:
            set_module_args(dict(banner='motd', text='welcome\nnew user'))
            commands = ['banner motd $\nwelcome\nnew user\n$']
            self.execute_module(changed=True, commands=commands)
        else:
            for banner_type in ('motd', 'exec', 'incoming'):
                set_module_args(dict(banner=banner_type, text='test\nbanner\nstring'))
                commands = ['banner {0} $\ntest\nbanner\nstring\n$'.format(banner_type)]
                self.execute_module(changed=True, commands=commands)

    def test_icx_banner_remove(self):
        set_module_args(dict(banner='motd', state='absent'))
        if not self.ENV_ICX_USE_DIFF:
            commands = ['no banner motd']
            self.execute_module(changed=True, commands=commands)
        else:
            commands = ['no banner motd']
            self.execute_module(changed=True, commands=commands)

    def test_icx_banner_motd_enter_set(self):
        set_module_args(dict(banner='motd', enterkey=True))

        if not self.ENV_ICX_USE_DIFF:
            commands = ['banner motd require-enter-key']
            self.execute_module(changed=True, commands=commands)
        else:
            self.execute_module(changed=False)

    def test_icx_banner_motd_enter_remove(self):
        set_module_args(dict(banner='motd', state='absent', enterkey=False))
        if not self.ENV_ICX_USE_DIFF:
            commands = ['no banner motd', 'no banner motd require-enter-key']
            self.execute_module(changed=True, commands=commands)

        else:
            commands = ['no banner motd', 'no banner motd require-enter-key']
            self.execute_module(changed=True, commands=commands)

    def test_icx_banner_remove_compare(self):
        set_module_args(dict(banner='incoming', state='absent', check_running_config='True'))
        if self.get_running_config(compare=True):
            if not self.ENV_ICX_USE_DIFF:
                commands = []
                self.execute_module(changed=False, commands=commands)
            else:
                commands = []
                self.execute_module()
