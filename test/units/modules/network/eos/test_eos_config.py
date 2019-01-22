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
from ansible.modules.network.eos import eos_config
from ansible.plugins.cliconf.eos import Cliconf
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosConfigModule(TestEosModule):

    module = eos_config

    def setUp(self):
        super(TestEosConfigModule, self).setUp()
        self.mock_get_config = patch('ansible.modules.network.eos.eos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_get_connection = patch('ansible.modules.network.eos.eos_config.get_connection')
        self.get_connection = self.mock_get_connection.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_config.load_config')
        self.load_config = self.mock_load_config.start()
        self.mock_run_commands = patch('ansible.modules.network.eos.eos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_supports_sessions = patch('ansible.plugins.cliconf.eos.Cliconf.supports_sessions')
        self.supports_sessions = self.mock_supports_sessions.start()
        self.mock_supports_sessions.return_value = True

        self.conn = self.get_connection()
        self.conn.edit_config = MagicMock()

        self.cliconf_obj = Cliconf(MagicMock())
        self.running_config = load_fixture('eos_config_config.cfg')

    def tearDown(self):
        super(TestEosConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_get_connection.stop()
        self.mock_supports_sessions.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('eos_config_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

    def test_eos_config_no_change(self):
        lines = ['hostname localhost']
        config = '\n'.join(lines)
        args = dict(lines=lines)
        set_module_args(args)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(config, config))
        result = self.execute_module()

    def test_eos_config_src(self):
        src = load_fixture('eos_config_candidate.cfg')
        args = dict(src=src)
        set_module_args(args)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, self.running_config))
        result = self.execute_module(changed=True)
        config = ['hostname switch01', 'interface Ethernet1',
                  'description test interface', 'no shutdown', 'ip routing']
        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])

    def test_eos_config_lines(self):
        lines = ['hostname switch01', 'ip domain-name eng.ansible.com']
        args = dict(lines=lines)
        set_module_args(args)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        result = self.execute_module(changed=True)
        config = ['hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])

    def test_eos_config_before(self):
        lines = ['hostname switch01', 'ip domain-name eng.ansible.com']
        before = ['before command']
        args = dict(lines=lines,
                    before=before)
        set_module_args(args)

        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        result = self.execute_module(changed=True)
        config = ['before command', 'hostname switch01']
        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])
        self.assertEqual('before command', result['commands'][0])

    def test_eos_config_after(self):
        lines = ['hostname switch01', 'ip domain-name eng.ansible.com']
        args = dict(lines=lines,
                    after=['after command'])

        set_module_args(args)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        result = self.execute_module(changed=True)
        config = ['after command', 'hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])
        self.assertEqual('after command', result['commands'][-1])

    def test_eos_config_parents(self):
        lines = ['ip address 1.2.3.4/5', 'no shutdown']
        parents = ['interface Ethernet10']
        args = dict(lines=lines, parents=parents)
        candidate = parents + lines
        set_module_args(args)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(candidate), self.running_config))

        result = self.execute_module(changed=True)
        config = ['interface Ethernet10', 'ip address 1.2.3.4/5', 'no shutdown']

        self.assertEqual(config, result['commands'], result['commands'])

    def test_eos_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_match_exact_requires_lines(self):
        args = dict(match='exact')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_match_strict_requires_lines(self):
        args = dict(match='strict')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_replace_block_requires_lines(self):
        args = dict(replace='block')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_replace_config_requires_src(self):
        args = dict(replace='config')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_backup_returns__backup__(self):
        args = dict(backup=True)
        set_module_args(args)
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_eos_config_save_when(self):
        mock_run_commands = patch('ansible.modules.network.eos.eos_config.run_commands')
        run_commands = mock_run_commands.start()

        run_commands.return_value = [load_fixture('eos_config_config.cfg'),
                                     load_fixture('eos_config_config.cfg')]

        args = dict(save_when='modified')
        set_module_args(args)
        result = self.execute_module()

        run_commands.return_value = [load_fixture('eos_config_config.cfg'),
                                     load_fixture('eos_config_config_updated.cfg')]

        args = dict(save_when='modified')
        set_module_args(args)
        result = self.execute_module(changed=True)

        mock_run_commands.stop()

    def test_eos_config_save_changed_true(self):
        commands = ['hostname foo', 'interface GigabitEthernet0/0', 'no ip address']
        set_module_args(dict(save_when='changed', lines=commands))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 1)
        args = self.run_commands.call_args[0][1][0]['command']
        self.assertIn('copy running-config startup-config', args)

    def test_eos_config_save_changed_false(self):
        set_module_args(dict(save_when='changed'))
        self.execute_module(changed=False)
        self.assertEqual(self.run_commands.call_count, 0)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)

    def test_eos_config_save_always(self):
        self.run_commands.return_value = "hostname foo"
        set_module_args(dict(save_when='always'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)
        args = self.run_commands.call_args[0][1][0]['command']
        self.assertIn('copy running-config startup-config', args)
