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
from ansible.modules.network.dellos6 import dellos6_config
from units.modules.utils import set_module_args
from .dellos6_module import TestDellos6Module, load_fixture


class TestDellos6ConfigModule(TestDellos6Module):

    module = dellos6_config

    def setUp(self):
        super(TestDellos6ConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.dellos6.dellos6_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.dellos6.dellos6_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.dellos6.dellos6_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestDellos6ConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        config_file = 'dellos6_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_dellos6_config_unchanged(self):
        src = load_fixture('dellos6_config_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_dellos6_config_src(self):
        src = load_fixture('dellos6_config_src.cfg')
        set_module_args(dict(src=src))
        commands = ['hostname foo', 'exit', 'interface Te1/0/2',
                    'shutdown', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_dellos6_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_dellos6_config_save(self):
        set_module_args(dict(save=True))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)
        args = self.run_commands.call_args[0][1]
        self.assertDictContainsSubset({'command': 'copy running-config startup-config'}, args[0])
#        self.assertIn('copy running-config startup-config\r', args)

    def test_dellos6_config_lines_wo_parents(self):
        set_module_args(dict(lines=['hostname foo']))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_dellos6_config_lines_w_parents(self):
        set_module_args(dict(lines=['description "teest"', 'exit'], parents=['interface Te1/0/2']))
        commands = ['interface Te1/0/2', 'description "teest"', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_dellos6_config_before(self):
        set_module_args(dict(lines=['hostname foo'], before=['snmp-server contact bar']))
        commands = ['snmp-server contact bar', 'hostname foo']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_dellos6_config_after(self):
        set_module_args(dict(lines=['hostname foo'], after=['snmp-server contact bar']))
        commands = ['hostname foo', 'snmp-server contact bar']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_dellos6_config_before_after_no_change(self):
        set_module_args(dict(lines=['hostname router'],
                             before=['snmp-server contact bar'],
                             after=['snmp-server location chennai']))
        self.execute_module()

    def test_dellos6_config_config(self):
        config = 'hostname localhost'
        set_module_args(dict(lines=['hostname router'], config=config))
        commands = ['hostname router']
        self.execute_module(changed=True, commands=commands)

    def test_dellos6_config_replace_block(self):
        lines = ['description test string', 'shutdown']
        parents = ['interface Te1/0/2']
        set_module_args(dict(lines=lines, replace='block', parents=parents))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands)

    def test_dellos6_config_match_none(self):
        lines = ['hostname router']
        set_module_args(dict(lines=lines, match='none'))
        self.execute_module(changed=True, commands=lines)

    def test_dellos6_config_match_none(self):
        lines = ['description test string', 'shutdown']
        parents = ['interface Te1/0/2']
        set_module_args(dict(lines=lines, parents=parents, match='none'))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_dellos6_config_match_strict(self):
        lines = ['description "test_string"',
                 'shutdown']
        parents = ['interface Te1/0/1']
        set_module_args(dict(lines=lines, parents=parents, match='strict'))
        commands = parents + ['shutdown']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_dellos6_config_match_exact(self):
        lines = ['description test_string', 'shutdown']
        parents = ['interface Te1/0/1']
        set_module_args(dict(lines=lines, parents=parents, match='exact'))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)
