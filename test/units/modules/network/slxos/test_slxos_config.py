#
# (c) 2018 Extreme Networks Inc.
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests.mock import patch
from ansible.modules.network.slxos import slxos_config
from units.modules.utils import set_module_args
from .slxos_module import TestSlxosModule, load_fixture


class TestSlxosConfigModule(TestSlxosModule):

    module = slxos_config

    def setUp(self):
        super(TestSlxosConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.slxos.slxos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.slxos.slxos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.slxos.slxos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestSlxosConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        config_file = 'slxos_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_slxos_config_unchanged(self):
        src = load_fixture('slxos_config_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_slxos_config_src(self):
        src = load_fixture('slxos_config_src.cfg')
        set_module_args(dict(src=src))
        commands = ['hostname foo', 'interface Ethernet 0/0',
                    'no ip address']
        self.execute_module(changed=True, commands=commands)

    def test_slxos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_slxos_config_save_always(self):
        self.run_commands.return_value = "Hostname foo"
        set_module_args(dict(save_when='always'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)
        args = self.run_commands.call_args[0][1]
        self.assertIn('copy running-config startup-config', args['command'])

    def test_slxos_config_save_changed_true(self):
        src = load_fixture('slxos_config_src.cfg')
        set_module_args(dict(src=src, save_when='changed'))
        commands = ['hostname foo', 'interface Ethernet 0/0', 'no ip address']
        self.execute_module(changed=True, commands=commands)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 1)
        args = self.run_commands.call_args[0][1]
        self.assertIn('copy running-config startup-config', args['command'])

    def test_slxos_config_save_changed_false(self):
        set_module_args(dict(save_when='changed'))
        self.execute_module(changed=False)
        self.assertEqual(self.run_commands.call_count, 0)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)

    def test_slxos_config_lines_wo_parents(self):
        set_module_args(dict(lines=['hostname foo']))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_slxos_config_lines_w_parents(self):
        set_module_args(dict(lines=['shutdown'], parents=['interface Ethernet 0/0']))
        commands = ['interface Ethernet 0/0', 'shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_slxos_config_before(self):
        set_module_args(dict(lines=['hostname foo'], before=['test1', 'test2']))
        commands = ['test1', 'test2', 'hostname foo']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_slxos_config_after(self):
        set_module_args(dict(lines=['hostname foo'], after=['test1', 'test2']))
        commands = ['hostname foo', 'test1', 'test2']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_slxos_config_before_after_no_change(self):
        set_module_args(dict(lines=['hostname router'],
                             before=['test1', 'test2'],
                             after=['test3', 'test4']))
        self.execute_module()

    def test_slxos_config_config(self):
        config = 'hostname localhost'
        set_module_args(dict(lines=['hostname router'], config=config))
        commands = ['hostname router']
        self.execute_module(changed=True, commands=commands)

    def test_slxos_config_replace_block(self):
        lines = ['description test string', 'test string']
        parents = ['interface Ethernet 0/0']
        set_module_args(dict(lines=lines, replace='block', parents=parents))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands)

    def test_slxos_config_match_none(self):
        lines = ['hostname router']
        set_module_args(dict(lines=lines, match='none'))
        self.execute_module(changed=True, commands=lines)

    def test_slxos_config_match_none(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string']
        parents = ['interface Ethernet 0/0']
        set_module_args(dict(lines=lines, parents=parents, match='none'))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_slxos_config_match_strict(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string',
                 'shutdown']
        parents = ['interface Ethernet 0/0']
        set_module_args(dict(lines=lines, parents=parents, match='strict'))
        commands = parents + ['shutdown']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_slxos_config_match_exact(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string',
                 'shutdown']
        parents = ['interface Ethernet 0/0']
        set_module_args(dict(lines=lines, parents=parents, match='exact'))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_slxos_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_slxos_config_src_and_parents_fails(self):
        args = dict(src='foo', parents='foo')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_slxos_config_match_exact_requires_lines(self):
        args = dict(match='exact')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_slxos_config_match_strict_requires_lines(self):
        args = dict(match='strict')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_slxos_config_replace_block_requires_lines(self):
        args = dict(replace='block')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_slxos_config_replace_config_requires_src(self):
        args = dict(replace='config')
        set_module_args(args)
        self.execute_module(failed=True)
