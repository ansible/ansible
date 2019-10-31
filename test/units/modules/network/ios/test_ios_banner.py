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
from ansible.modules.network.ios import ios_banner
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosBannerModule(TestIosModule):

    module = ios_banner

    def setUp(self):
        super(TestIosBannerModule, self).setUp()

        self.mock_exec_command = patch('ansible.modules.network.ios.ios_banner.exec_command')
        self.exec_command = self.mock_exec_command.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_banner.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosBannerModule, self).tearDown()
        self.mock_exec_command.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.exec_command.return_value = (0, load_fixture('ios_banner_show_banner.txt').strip(), None)
        self.load_config.return_value = dict(diff=None, session='session')

    def test_ios_banner_create(self):
        for banner_type in ('login', 'motd', 'exec', 'incoming', 'slip-ppp'):
            set_module_args(dict(banner=banner_type, text='test\nbanner\nstring'))
            commands = ['banner {0} @\ntest\nbanner\nstring\n@'.format(banner_type)]
            self.execute_module(changed=True, commands=commands)

    def test_ios_banner_remove(self):
        set_module_args(dict(banner='login', state='absent'))
        commands = ['no banner login']
        self.execute_module(changed=True, commands=commands)

    def test_ios_banner_nochange(self):
        banner_text = load_fixture('ios_banner_show_banner.txt').strip()
        set_module_args(dict(banner='login', text=banner_text))
        self.execute_module()


class TestIosBannerIos12Module(TestIosBannerModule):

    def load_fixtures(self, commands):
        show_banner_return_value = (1, '', None)
        show_running_config_return_value = \
            (0, load_fixture('ios_banner_show_running_config_ios12.txt').strip(), None)
        self.exec_command.side_effect = [show_banner_return_value,
                                         show_running_config_return_value]

    def test_ios_banner_nochange(self):
        banner_text = load_fixture('ios_banner_show_banner.txt').strip()
        set_module_args(dict(banner='exec', text=banner_text))
        self.execute_module()
