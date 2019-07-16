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

from units.compat.mock import patch, MagicMock
from units.modules.utils import set_module_args
from ansible.plugins.cliconf.exos import Cliconf
from ansible.modules.network.exos import exos_config
from .exos_module import TestExosModule, load_fixture


class TestExosConfigModule(TestExosModule):

    module = exos_config

    def setUp(self):
        super(TestExosConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.exos.exos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.exos.exos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.exos.exos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_startup_config = patch('ansible.modules.network.exos.exos_config.get_startup_config')
        self.get_startup_config = self.mock_get_startup_config.start()

        self.cliconf_obj = Cliconf(MagicMock())

        self.mock_get_diff = patch('ansible.modules.network.exos.exos_config.get_diff')
        self.get_diff = self.mock_get_diff.start()

        self.running_config = load_fixture('exos_config_config.cfg')

    def tearDown(self):
        super(TestExosConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()
        self.mock_get_startup_config.stop()

    def load_fixtures(self, commands=None):
        config_file = 'exos_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_exos_config_unchanged(self):
        src = load_fixture('exos_config_config.cfg')
        set_module_args(dict(src=src))
        self.get_diff.return_value = self.cliconf_obj.get_diff(src, src)
        self.execute_module()

    def test_exos_config_src(self):
        src = load_fixture('exos_config_src.cfg')
        set_module_args(dict(src=src))
        commands = ['configure ports 1 description-string "IDS"',
                    'configure snmp sysName "marble"']
        self.get_diff.return_value = self.cliconf_obj.get_diff(src, self.running_config)
        self.execute_module(changed=True, commands=commands)

    def test_exos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_exos_config_save_always(self):
        self.run_commands.return_value = 'configure snmp sysName "marble"'
        set_module_args(dict(save_when='always'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)
        args = self.run_commands.call_args[0][1]
        self.assertIn('save configuration', args['command'])

    def test_exos_config_save_changed_true(self):
        src = load_fixture('exos_config_src.cfg')
        set_module_args(dict(src=src, save_when='changed'))
        commands = ['configure ports 1 description-string "IDS"',
                    'configure snmp sysName "marble"']
        self.get_diff.return_value = self.cliconf_obj.get_diff(src, self.running_config)
        self.execute_module(changed=True, commands=commands)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 1)
        args = self.run_commands.call_args[0][1]
        self.assertIn('save configuration', args['command'])

    def test_exos_config_save_changed_true_check_mode(self):
        src = load_fixture('exos_config_src.cfg')
        set_module_args(dict(src=src, save_when='changed', _ansible_check_mode=True))
        commands = ['configure ports 1 description-string "IDS"',
                    'configure snmp sysName "marble"']
        self.get_diff.return_value = self.cliconf_obj.get_diff(src, self.running_config)
        self.execute_module(changed=True, commands=commands)
        self.assertEqual(self.run_commands.call_count, 0)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 0)

    def test_exos_config_save_changed_false(self):
        set_module_args(dict(save_when='changed'))
        self.execute_module(changed=False)
        self.assertEqual(self.run_commands.call_count, 0)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)

    def test_exos_config_save_modified_false(self):
        self.get_startup_config.return_value = load_fixture('exos_config_config.cfg')
        set_module_args(dict(save_when='modified'))
        self.execute_module(changed=False)
        self.assertEqual(self.run_commands.call_count, 0)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.get_startup_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 0)

    def test_exos_config_save_modified_true(self):
        self.get_startup_config.return_value = load_fixture('exos_config_modified.cfg')
        set_module_args(dict(save_when='modified'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertTrue(self.get_config.call_count > 0)
        self.assertEqual(self.get_startup_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 0)

    def test_exos_config_lines(self):
        lines = ['configure snmp sysName "marble"']
        set_module_args(dict(lines=lines))
        commands = ['configure snmp sysName "marble"']
        self.get_diff.return_value = self.cliconf_obj.get_diff('\n'.join(lines), self.running_config)
        self.execute_module(changed=True, commands=commands)

    def test_exos_config_before(self):
        lines = ['configure snmp sysName "marble"']
        set_module_args(dict(lines=lines, before=['test1', 'test2']))
        commands = ['test1', 'test2', 'configure snmp sysName "marble"']
        self.get_diff.return_value = self.cliconf_obj.get_diff('\n'.join(lines), self.running_config)
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_exos_config_after(self):
        lines = ['configure snmp sysName "marble"']
        set_module_args(dict(lines=lines, after=['test1', 'test2']))
        commands = ['configure snmp sysName "marble"', 'test1', 'test2']
        self.get_diff.return_value = self.cliconf_obj.get_diff('\n'.join(lines), self.running_config)
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_exos_config_before_after_no_change(self):
        lines = ['configure snmp sysName "x870"']
        set_module_args(dict(lines=lines,
                             before=['test1', 'test2'],
                             after=['test3', 'test4']))
        self.get_diff.return_value = self.cliconf_obj.get_diff('\n'.join(lines), self.running_config)
        self.execute_module()

    def test_exos_config_config(self):
        config = 'hostname localhost'
        lines = ['configure snmp sysName "x870"']
        set_module_args(dict(lines=lines, config=config))
        commands = ['configure snmp sysName "x870"']
        self.get_diff.return_value = self.cliconf_obj.get_diff('\n'.join(lines), config)
        self.execute_module(changed=True, commands=commands)

    def test_exos_config_match_none(self):
        lines = ['configure snmp sysName "x870"']
        set_module_args(dict(lines=lines, match='none'))
        self.get_diff.return_value = self.cliconf_obj.get_diff('\n'.join(lines), self.running_config, diff_match='none')
        self.execute_module(changed=True, commands=lines)

    def test_exos_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_exos_config_match_exact_requires_lines(self):
        args = dict(match='exact')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_exos_config_match_strict_requires_lines(self):
        args = dict(match='strict')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_exos_config_replace_block_requires_lines(self):
        args = dict(replace='block')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_exos_config_replace_config_requires_src(self):
        args = dict(replace='config')
        set_module_args(args)
        self.execute_module(failed=True)

    def test_exos_diff_running_unchanged(self):
        args = dict(diff_against='running', _ansible_diff=True)
        set_module_args(args)
        self.execute_module(changed=False)

    def test_exos_diff_running_unchanged_check(self):
        args = dict(diff_against='running',
                    _ansible_diff=True,
                    _ansible_check_mode=True)
        set_module_args(args)
        self.execute_module(changed=False)

    def test_exos_diff_startup_unchanged(self):
        mock_get_startup_config = patch('ansible.modules.network.exos.exos_config.get_startup_config')
        get_startup_config = mock_get_startup_config.start()
        get_startup_config.return_value = load_fixture('exos_config_config.cfg')

        args = dict(diff_against='startup', _ansible_diff=True)
        set_module_args(args)
        self.execute_module(changed=False)
        self.assertEqual(get_startup_config.call_count, 1)

        mock_get_startup_config.stop()

    def test_exos_diff_startup_changed(self):
        mock_get_startup_config = patch('ansible.modules.network.exos.exos_config.get_startup_config')
        get_startup_config = mock_get_startup_config.start()
        get_startup_config.return_value = load_fixture('exos_config_modified.cfg')

        args = dict(diff_against='startup', _ansible_diff=True)
        set_module_args(args)
        self.execute_module(changed=True)
        self.assertEqual(get_startup_config.call_count, 1)

        mock_get_startup_config.stop()

    def test_exos_diff_intended_unchanged(self):
        intended_config = load_fixture('exos_config_config.cfg')
        args = dict(diff_against='intended',
                    intended_config=intended_config,
                    _ansible_diff=True)
        set_module_args(args)
        self.get_diff = self.cliconf_obj.get_diff(intended_config, self.running_config)
        self.execute_module(changed=False)

    def test_exos_diff_intended_modified(self):
        intended_config = load_fixture('exos_config_modified.cfg')
        args = dict(diff_against='intended',
                    intended_config=intended_config,
                    _ansible_diff=True)
        set_module_args(args)
        self.get_diff = self.cliconf_obj.get_diff(intended_config, self.running_config)
        self.execute_module(changed=True)
