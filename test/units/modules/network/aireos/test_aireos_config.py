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

from ansible.compat.tests.mock import patch
from ansible.modules.network.aireos import aireos_config
from units.modules.utils import set_module_args
from .aireos_module import TestCiscoWlcModule, load_fixture


class TestCiscoWlcConfigModule(TestCiscoWlcModule):

    module = aireos_config

    def setUp(self):
        super(TestCiscoWlcConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.aireos.aireos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.aireos.aireos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.aireos.aireos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestCiscoWlcConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        config_file = 'aireos_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_aireos_config_unchanged(self):
        src = load_fixture('aireos_config_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_aireos_config_src(self):
        src = load_fixture('aireos_config_src.cfg')
        set_module_args(dict(src=src))
        commands = ['sysname foo', 'interface address dynamic-interface mtc-1 10.33.20.4 255.255.255.0 10.33.20.2']
        self.execute_module(changed=True, commands=commands)

    def test_aireos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_aireos_config_save(self):
        self.run_commands.return_value = "sysname foo"
        set_module_args(dict(save=True))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)

    def test_aireos_config_before(self):
        set_module_args(dict(lines=['sysname foo'], before=['test1', 'test2']))
        commands = ['test1', 'test2', 'sysname foo']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_aireos_config_after(self):
        set_module_args(dict(lines=['sysname foo'], after=['test1', 'test2']))
        commands = ['sysname foo', 'test1', 'test2']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_aireos_config_before_after_no_change(self):
        set_module_args(dict(lines=['sysname router'],
                             before=['test1', 'test2'],
                             after=['test3', 'test4']))
        self.execute_module()

    def test_aireos_config_config(self):
        config = 'sysname localhost'
        set_module_args(dict(lines=['sysname router'], config=config))
        commands = ['sysname router']
        self.execute_module(changed=True, commands=commands)

    def test_aireos_config_match_none(self):
        lines = ['sysname router', 'interface create mtc-1 1']
        set_module_args(dict(lines=lines, match='none'))
        self.execute_module(changed=True, commands=lines, sort=False)
