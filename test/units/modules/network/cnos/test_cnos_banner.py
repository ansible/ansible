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
from ansible.modules.network.cnos import cnos_banner
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosBannerModule(TestCnosModule):

    module = cnos_banner

    def setUp(self):
        super(TestCnosBannerModule, self).setUp()

        self.mock_exec_command = patch('ansible.modules.network.cnos.cnos_banner.exec_command')
        self.exec_command = self.mock_exec_command.start()

        self.mock_load_config = patch('ansible.modules.network.cnos.cnos_banner.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestCnosBannerModule, self).tearDown()
        self.mock_exec_command.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.exec_command.return_value = (0, load_fixture('cnos_banner_show_banner.txt').strip(), None)
        self.load_config.return_value = dict(diff=None, session='session')

    def test_cnos_banner_create(self):
        for banner_type in ('login', 'motd'):
            set_module_args(dict(banner=banner_type, text='test\nbanner\nstring'))
            commands = ['banner {0} test'.format(banner_type), 'banner {0} banner'.format(banner_type), 'banner {0} string'.format(banner_type)]
            self.execute_module(changed=True, commands=commands)

    def test_cnos_banner_remove(self):
        set_module_args(dict(banner='login', state='absent'))
        commands = ['no banner login']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_banner_nochange(self):
        banner_text = load_fixture('cnos_banner_show_banner.txt').strip()
        set_module_args(dict(banner='login', text=banner_text))
        self.execute_module()
