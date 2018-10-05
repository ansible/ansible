#
# (c) 2016 Red Hat Inc.
#
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

from ansible.compat.tests.mock import patch, MagicMock
from ansible.modules.network.vyos import vyos_config
from ansible.plugins.cliconf.vyos import Cliconf
from units.modules.utils import set_module_args
from .vyos_module import TestVyosModule, load_fixture


class TestVyosConfigModule(TestVyosModule):

    module = vyos_config

    def setUp(self):
        super(TestVyosConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.vyos.vyos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.vyos.vyos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.vyos.vyos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_connection = patch('ansible.modules.network.vyos.vyos_config.get_connection')
        self.get_connection = self.mock_get_connection.start()

        self.cliconf_obj = Cliconf(MagicMock())
        self.running_config = load_fixture('vyos_config_config.cfg')

        self.conn = self.get_connection()
        self.conn.edit_config = MagicMock()
        self.running_config = load_fixture('vyos_config_config.cfg')

    def tearDown(self):
        super(TestVyosConfigModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()
        self.mock_get_connection.stop()

    def load_fixtures(self, commands=None):
        config_file = 'vyos_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_vyos_config_unchanged(self):
        src = load_fixture('vyos_config_config.cfg')
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, src))
        set_module_args(dict(src=src))
        self.execute_module()

    def test_vyos_config_src(self):
        src = load_fixture('vyos_config_src.cfg')
        set_module_args(dict(src=src))
        candidate = '\n'.join(self.module.format_commands(src.splitlines()))
        commands = ['set system host-name foo', 'delete interfaces ethernet eth0 address']
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate, self.running_config))
        self.execute_module(changed=True, commands=commands)

    def test_vyos_config_src_brackets(self):
        src = load_fixture('vyos_config_src_brackets.cfg')
        set_module_args(dict(src=src))
        candidate = '\n'.join(self.module.format_commands(src.splitlines()))
        commands = ['set interfaces ethernet eth0 address 10.10.10.10/24', 'set system host-name foo']
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate, self.running_config))
        self.execute_module(changed=True, commands=commands)

    def test_vyos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_vyos_config_lines(self):
        commands = ['set system host-name foo']
        set_module_args(dict(lines=commands))
        candidate = '\n'.join(commands)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate, self.running_config))
        self.execute_module(changed=True, commands=commands)

    def test_vyos_config_config(self):
        config = 'set system host-name localhost'
        new_config = ['set system host-name router']
        set_module_args(dict(lines=new_config, config=config))
        candidate = '\n'.join(new_config)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate, config))
        self.execute_module(changed=True, commands=new_config)

    def test_vyos_config_match_none(self):
        lines = ['set system interfaces ethernet eth0 address 1.2.3.4/24',
                 'set system interfaces ethernet eth0 description test string']
        set_module_args(dict(lines=lines, match='none'))
        candidate = '\n'.join(lines)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate, None, diff_match='none'))
        self.execute_module(changed=True, commands=lines, sort=False)
