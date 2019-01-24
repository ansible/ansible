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

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_config
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxConfigModule(TestOnyxModule):

    module = onyx_config

    def setUp(self):
        super(TestOnyxConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.onyx.onyx_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.onyx.onyx_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.onyx.onyx_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestOnyxConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_onyx_config_unchanged(self):
        src = load_fixture('onyx_config_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_onyx_config_src(self):
        src = load_fixture('onyx_config_src.cfg')
        set_module_args(dict(src=src))
        commands = [
            'interface mlag-port-channel 2']
        self.execute_module(changed=True, commands=commands, is_updates=True)

    def test_onyx_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_onyx_config_save(self):
        set_module_args(dict(lines=['hostname foo'], save='yes'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 0)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 1)
        args = self.load_config.call_args[0][1]
        self.assertIn('configuration write', args)

    def test_onyx_config_lines_wo_parents(self):
        set_module_args(dict(lines=['hostname foo']))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands, is_updates=True)

    def test_onyx_config_before(self):
        set_module_args(dict(lines=['hostname foo'], before=['test1', 'test2']))
        commands = ['test1', 'test2', 'hostname foo']
        self.execute_module(changed=True, commands=commands, sort=False, is_updates=True)

    def test_onyx_config_after(self):
        set_module_args(dict(lines=['hostname foo'], after=['test1', 'test2']))
        commands = ['hostname foo', 'test1', 'test2']
        self.execute_module(changed=True, commands=commands, sort=False, is_updates=True)

    def test_onyx_config_before_after(self):
        set_module_args(dict(lines=['hostname foo'],
                             before=['test1', 'test2'],
                             after=['test3', 'test4']))
        commands = ['test1', 'test2', 'hostname foo', 'test3', 'test4']
        self.execute_module(changed=True, commands=commands, sort=False, is_updates=True)

    def test_onyx_config_config(self):
        config = 'hostname localhost'
        set_module_args(dict(lines=['hostname router'], config=config))
        commands = ['hostname router']
        self.execute_module(changed=True, commands=commands, is_updates=True)

    def test_onyx_config_match_none(self):
        lines = ['hostname router']
        set_module_args(dict(lines=lines, match='none'))
        self.execute_module(changed=True, commands=lines, is_updates=True)
