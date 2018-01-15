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
from ansible.modules.network.eos import eos_banner
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosBannerModule(TestEosModule):

    module = eos_banner

    def setUp(self):
        super(TestEosBannerModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.eos.eos_banner.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_banner.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestEosBannerModule, self).tearDown()

        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        if transport == 'cli':
            self.run_commands.return_value = [load_fixture('eos_banner_show_banner.txt').strip()]
        else:
            self.run_commands.return_value = [{'loginBanner': load_fixture('eos_banner_show_banner.txt').strip()}]

        self.load_config.return_value = dict(diff=None, session='session')

    def test_eos_banner_create_with_cli_transport(self):
        set_module_args(dict(banner='login', text='test\nbanner\nstring',
                             transport='cli'))
        commands = ['banner login', 'test', 'banner', 'string', 'EOF']
        self.execute_module(changed=True, commands=commands)

    def test_eos_banner_remove_with_cli_transport(self):
        set_module_args(dict(banner='login', state='absent', transport='cli'))
        commands = ['no banner login']
        self.execute_module(changed=True, commands=commands)

    def test_eos_banner_create_with_eapi_transport(self):
        set_module_args(dict(banner='login', text='test\nbanner\nstring',
                             transport='eapi'))
        commands = ['banner login']
        inputs = ['test\nbanner\nstring']
        self.execute_module(changed=True, commands=commands, inputs=inputs, transport='eapi')

    def test_eos_banner_remove_with_eapi_transport(self):
        set_module_args(dict(banner='login', state='absent', transport='eapi'))
        commands = ['no banner login']
        self.execute_module(changed=True, commands=commands, transport='eapi')

    def test_eos_banner_nochange_with_cli_transport(self):
        banner_text = load_fixture('eos_banner_show_banner.txt').strip()
        set_module_args(dict(banner='login', text=banner_text, transport='cli'))
        self.execute_module()

    def test_eos_banner_nochange_with_eapi_transport(self):
        banner_text = load_fixture('eos_banner_show_banner.txt').strip()
        set_module_args(dict(banner='login', text=banner_text, transport='eapi'))
        self.execute_module(transport='eapi')
