# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from units.compat.mock import patch
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

        self.set_running_config()

    def tearDown(self):
        super(TestICXBannerModule, self).tearDown()
        self.mock_exec_command.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None):
        compares = None

        def load_file(*args, **kwargs):
            module = args
            for arg in args:
                if arg.params['check_running_config'] is True:
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
