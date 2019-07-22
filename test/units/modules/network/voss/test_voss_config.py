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

from units.compat.mock import patch, MagicMock
from units.modules.utils import set_module_args
from ansible.modules.network.voss import voss_config
from ansible.plugins.cliconf.voss import Cliconf
from .voss_module import TestVossModule, load_fixture


class TestVossConfigModule(TestVossModule):

    module = voss_config

    def setUp(self):
        super(TestVossConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.voss.voss_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_get_connection = patch('ansible.modules.network.voss.voss_config.get_connection')
        self.get_connection = self.mock_get_connection.start()

        self.conn = self.get_connection()
        self.conn.edit_config = MagicMock()

        self.mock_run_commands = patch('ansible.modules.network.voss.voss_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.cliconf_obj = Cliconf(MagicMock())
        self.running_config = load_fixture('voss_config_config.cfg')

    def tearDown(self):
        super(TestVossConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_run_commands.stop()
        self.mock_get_connection.stop()

    def load_fixtures(self, commands=None):
        config_file = 'voss_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.get_connection.edit_config.return_value = None

    def test_voss_config_unchanged(self):
        src = load_fixture('voss_config_config.cfg')
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, src))
        set_module_args(dict(src=src))
        self.execute_module()

    def test_voss_config_src(self):
        src = load_fixture('voss_config_src.cfg')
        set_module_args(dict(src=src))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, self.running_config))
        commands = ['prompt "VSP8K"', 'interface GigabitEthernet 1/1',
                    'name "UNUSED"', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_voss_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_voss_config_save_always(self):
        self.run_commands.return_value = "Hostname foo"
        set_module_args(dict(save_when='always'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.conn.edit_config.call_count, 0)
        args = self.run_commands.call_args[0][1]
        self.assertIn('save config\r', args)

    def test_voss_config_save_changed_true(self):
        src = load_fixture('voss_config_src.cfg')
        set_module_args(dict(src=src, save_when='changed'))
        commands = ['prompt "VSP8K"', 'interface GigabitEthernet 1/1',
                    'name "UNUSED"', 'exit']
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, self.running_config))
        self.execute_module(changed=True, commands=commands)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.conn.edit_config.call_count, 1)
        args = self.run_commands.call_args[0][1]
        self.assertIn('save config\r', args)

    def test_voss_config_save_changed_false(self):
        set_module_args(dict(save_when='changed'))
        self.execute_module(changed=False)
        self.assertEqual(self.run_commands.call_count, 0)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.conn.edit_config.call_count, 0)

    def test_voss_config_lines_wo_parents(self):
        lines = ['prompt "VSP8K"']
        set_module_args(dict(lines=lines))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        commands = ['prompt "VSP8K"']
        self.execute_module(changed=True, commands=commands)

    def test_voss_config_lines_w_parents(self):
        lines = ['no shutdown']
        parents = ['interface GigabitEthernet 1/1']
        set_module_args(dict(lines=lines, parents=parents))
        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = voss_config.get_candidate_config(module)

        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config))

        commands = ['interface GigabitEthernet 1/1', 'no shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_voss_config_before(self):
        lines = ['prompt "VSP8K"']
        set_module_args(dict(lines=lines, before=['test1', 'test2']))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines),
                                                                              self.running_config))
        commands = ['test1', 'test2', 'prompt "VSP8K"']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_voss_config_after(self):
        lines = ['prompt "VSP8K"']
        set_module_args(dict(lines=lines, after=['test1', 'test2']))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines),
                                                                              self.running_config))
        commands = ['prompt "VSP8K"', 'test1', 'test2']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_voss_config_before_after_no_change(self):
        lines = ['prompt "VSP300"']
        set_module_args(dict(lines=lines,
                             before=['test1', 'test2'],
                             after=['test3', 'test4']))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        self.execute_module()

    def test_voss_config_config(self):
        config = 'prompt "VSP300"'
        lines = ['prompt router']
        set_module_args(dict(lines=lines, config=config))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), config))
        commands = ['prompt router']
        self.execute_module(changed=True, commands=commands)

    def test_voss_config_replace_block(self):
        lines = ['name "ServerB"', 'test string']
        parents = ['interface GigabitEthernet 1/2']
        set_module_args(dict(lines=lines, replace='block', parents=parents))

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = voss_config.get_candidate_config(module)

        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_replace='block', path=parents))

        commands = parents + lines
        self.execute_module(changed=True, commands=commands)

    def test_voss_config_match_none(self):
        lines = ['prompt router']
        set_module_args(dict(lines=lines, match='none'))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config, diff_match='none'))
        self.execute_module(changed=True, commands=lines)

    def test_voss_config_match_none_parents(self):
        lines = ['name ServerA', 'vlacp enable']
        parents = ['interface GigabitEthernet 1/1']
        set_module_args(dict(lines=lines, parents=parents, match='none'))

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = voss_config.get_candidate_config(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='none', path=parents))

        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_voss_config_match_strict(self):
        lines = ['name "ServerA"', 'vlacp enable',
                 'no shutdown']
        parents = ['interface GigabitEthernet 1/1']
        set_module_args(dict(lines=lines, parents=parents, match='strict'))

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = voss_config.get_candidate_config(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='strict', path=parents))

        commands = parents + ['no shutdown']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_voss_config_match_exact(self):
        lines = ['name "ServerA"', 'vlacp enable', 'no shutdown']
        parents = ['interface GigabitEthernet 1/1']
        set_module_args(dict(lines=lines, parents=parents, match='exact'))

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = voss_config.get_candidate_config(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='exact', path=parents))

        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_voss_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_voss_config_src_and_parents_fails(self):
        args = dict(src='foo', parents='foo')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_voss_config_match_exact_requires_lines(self):
        args = dict(match='exact')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_voss_config_match_strict_requires_lines(self):
        args = dict(match='strict')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_voss_config_replace_block_requires_lines(self):
        args = dict(replace='block')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_voss_config_replace_config_requires_src(self):
        args = dict(replace='config')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_voss_config_ipv6(self):
        lines = ['ip address 1 1.1.1.1/255.255.255.255',
                 'ipv6 interface address 2011:0:0:0:0:0:0:1/128']
        parents = ['interface loopback 1']
        set_module_args(dict(lines=lines, parents=parents))
        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = voss_config.get_candidate_config(module)

        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config))
        self.execute_module(changed=False)

    def test_voss_config_src_ipv6(self):
        src = load_fixture('voss_config_ipv6.cfg')
        set_module_args(dict(src=src))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, self.running_config))
        commands = ['interface loopback 1', 'ip address 1 2.2.2.2/255.255.255.255',
                    'ipv6 interface address 2011:0:0:0:0:0:0:2/128', 'exit']
        self.execute_module(changed=True, commands=commands)
