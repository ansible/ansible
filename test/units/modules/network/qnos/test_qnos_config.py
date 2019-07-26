#
# (c) 2019 Red Hat Inc.
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
from ansible.modules.network.qnos import qnos_config
from ansible.plugins.cliconf.qnos import Cliconf
from units.modules.utils import set_module_args
from .qnos_module import TestQnosModule, load_fixture
from ansible.module_utils.network.common.config import dumps


class TestQnosConfigModule(TestQnosModule):

    module = qnos_config

    def setUp(self):
        super(TestQnosConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.qnos.qnos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_get_connection = patch('ansible.modules.network.qnos.qnos_config.get_connection')
        self.get_connection = self.mock_get_connection.start()

        self.conn = self.get_connection()
        self.conn.edit_config = MagicMock()

        self.mock_run_commands = patch('ansible.modules.network.qnos.qnos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.cliconf_obj = Cliconf(MagicMock())
        self.running_config = load_fixture('qnos_config_config.cfg')

    def tearDown(self):
        super(TestQnosConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_run_commands.stop()
        self.mock_get_connection.stop()

    def load_fixtures(self, commands=None):
        config_file = 'qnos_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.get_connection.edit_config.return_value = None

    def test_qnos_config_unchanged(self):
        src = load_fixture('qnos_config_config.cfg')
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, src))
        set_module_args(dict(src=src))
        self.execute_module()

    def test_qnos_config_src(self):
        src = load_fixture('qnos_config_src.cfg')
        set_module_args(dict(src=src))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, self.running_config))
        commands = ['hostname foo', 'interface 0/1',
                    'no ip address','exit','interface 0/2','exit']
        self.execute_module(changed=True, commands=commands)

    def test_qnos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_qnos_config_save_always(self):
        self.run_commands.return_value = "Hostname foo"
        set_module_args(dict(save_when='always'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.conn.edit_config.call_count, 0)
        args = self.run_commands.call_args[0][1]
        self.assertIn('copy running-config startup-config\r', args)

    def test_qnos_config_save_changed_true(self):
        src = load_fixture('qnos_config_src.cfg')
        set_module_args(dict(src=src, save_when='changed'))
        commands = ['hostname foo', 'interface 0/1', 'no ip address','exit','interface 0/2','exit']
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, self.running_config))
        self.execute_module(changed=True, commands=commands)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.conn.edit_config.call_count, 1)
        args = self.run_commands.call_args[0][1]
        self.assertIn('copy running-config startup-config\r', args)

    def test_qnos_config_save_changed_false(self):
        set_module_args(dict(save_when='changed'))
        self.execute_module(changed=False)
        self.assertEqual(self.run_commands.call_count, 0)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.conn.edit_config.call_count, 0)

    def test_qnos_config_save_always(self):
        self.run_commands.return_value = "hostname foo"
        set_module_args(dict(save_when='always'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.conn.edit_config.call_count, 0)
        args = self.run_commands.call_args[0][1]
        self.assertIn('copy running-config startup-config\r', args)

    def test_qnos_config_lines_wo_parents(self):
        lines = ['hostname foo']
        set_module_args(dict(lines=lines))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_qnos_config_lines_w_parents(self):
        lines = ['shutdown']
        parents = ['interface 0/1']
        set_module_args(dict(lines=lines, parents=parents))
        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = qnos_config.get_candidate_config(module)

        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config))

        commands = ['interface 0/1', 'shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_qnos_config_before(self):
        lines = ['hostname foo']
        set_module_args(dict(lines=lines, before=['test1', 'test2']))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        commands = ['test1', 'test2', 'hostname foo']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_qnos_config_after(self):
        lines = ['hostname foo']
        set_module_args(dict(lines=lines, after=['test1', 'test2']))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        commands = ['hostname foo', 'test1', 'test2']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_qnos_config_before_after_no_change(self):
        lines = ['hostname router']
        set_module_args(dict(lines=lines,
                             before=['test1', 'test2'],
                             after=['test3', 'test4']))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        self.execute_module()

    def test_qnos_config_config(self):
        config = 'hostname localhost'
        lines = ['hostname router']
        set_module_args(dict(lines=lines, config=config))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), config))
        commands = ['hostname router']
        self.execute_module(changed=True, commands=commands)

    def test_qnos_config_replace_block(self):
        lines = ['description defg','exit']
        parents = ['interface 0/1']
        set_module_args(dict(lines=lines, replace='block', parents=parents))

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = qnos_config.get_candidate_config(module)

        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_replace='block', path=parents))
        lines.remove('exit')
        commands = parents + lines
        self.execute_module(changed=True, commands=commands)

    def test_qnos_config_match_none(self):
        lines = ['hostname router']
        set_module_args(dict(lines=lines, match='none'))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config, diff_match='none'))
        self.execute_module(changed=True, commands=lines)

    def test_qnos_config_match_none(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string']
        parents = ['interface 0/1']
        set_module_args(dict(lines=lines, parents=parents, match='none'))

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = qnos_config.get_candidate_config(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='none', path=parents))

        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_qnos_config_match_strict(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string',
                 'shutdown']
        parents = ['interface 0/1']
        set_module_args(dict(lines=lines, parents=parents, match='strict'))

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = qnos_config.get_candidate_config(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='strict', path=parents))

        commands = parents + ['shutdown']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_qnos_config_match_exact(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string',
                 'shutdown']
        parents = ['interface 0/1']
        set_module_args(dict(lines=lines, parents=parents, match='exact'))

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = qnos_config.get_candidate_config(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='exact', path=parents))

        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_qnos_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_qnos_config_src_and_parents_fails(self):
        args = dict(src='foo', parents='foo')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_qnos_config_match_exact_requires_lines(self):
        args = dict(match='exact')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_qnos_config_match_strict_requires_lines(self):
        args = dict(match='strict')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_qnos_config_replace_block_requires_lines(self):
        args = dict(replace='block')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_qnos_config_replace_config_requires_src(self):
        args = dict(replace='config')
        set_module_args(args)
        result = self.execute_module(failed=True)
