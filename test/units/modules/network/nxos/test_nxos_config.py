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
from ansible.modules.network.nxos import nxos_config
from ansible.plugins.cliconf.nxos import Cliconf
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosConfigModule(TestNxosModule):

    module = nxos_config

    def setUp(self):
        super(TestNxosConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_save_config = patch('ansible.modules.network.nxos.nxos_config.save_config')
        self.save_config = self.mock_save_config.start()

        self.mock_get_connection = patch('ansible.modules.network.nxos.nxos_config.get_connection')
        self.get_connection = self.mock_get_connection.start()

        self.conn = self.get_connection()
        self.conn.edit_config = MagicMock()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.cliconf_obj = Cliconf(MagicMock())
        self.running_config = load_fixture('nxos_config', 'config.cfg')

    def tearDown(self):
        super(TestNxosConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()
        self.mock_get_connection.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('nxos_config', 'config.cfg')
        self.load_config.return_value = None

    def test_nxos_config_no_change(self):
        lines = ['hostname localhost']
        args = dict(lines=lines)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        set_module_args(args)
        result = self.execute_module()

    def test_nxos_config_src(self):
        src = load_fixture('nxos_config', 'candidate.cfg')
        args = dict(src=src)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, self.running_config))
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['hostname switch01', 'interface Ethernet1',
                  'description test interface', 'no shutdown', 'ip routing']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])

    def test_nxos_config_replace_src(self):
        set_module_args(dict(replace_src='bootflash:config', replace='config'))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(self.running_config, self.running_config, diff_replace='config'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['config replace bootflash:config'])

    def test_nxos_config_lines(self):
        lines = ['hostname switch01', 'ip domain-name eng.ansible.com']
        args = dict(lines=lines)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])

    def test_nxos_config_before(self):
        lines = ['hostname switch01', 'ip domain-name eng.ansible.com']
        args = dict(lines=lines,
                    before=['before command'])
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['before command', 'hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])
        self.assertEqual('before command', result['commands'][0])

    def test_nxos_config_after(self):
        lines = ['hostname switch01', 'ip domain-name eng.ansible.com']
        args = dict(lines=lines,
                    after=['after command'])

        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['after command', 'hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])
        self.assertEqual('after command', result['commands'][-1])

    def test_nxos_config_parents(self):
        lines = ['ip address 1.2.3.4/5', 'no shutdown']
        parents = ['interface Ethernet10']
        args = dict(lines=lines, parents=parents)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(parents + lines), self.running_config, path=parents))
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['interface Ethernet10', 'ip address 1.2.3.4/5', 'no shutdown']

        self.assertEqual(config, result['commands'], result['commands'])

    def test_nxos_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_nxos_config_src_and_parents_fails(self):
        args = dict(src='foo', parents='foo')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_nxos_config_match_exact_requires_lines(self):
        args = dict(match='exact')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_nxos_config_match_strict_requires_lines(self):
        args = dict(match='strict')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_nxos_config_replace_block_requires_lines(self):
        args = dict(replace='block')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_nxos_config_replace_config_requires_src(self):
        args = dict(replace='config')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_nxos_config_backup_returns__backup__(self):
        args = dict(backup=True)
        set_module_args(args)
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_nxos_config_save_always(self):
        args = dict(save_when='always')
        set_module_args(args)
        self.execute_module()
        self.assertEqual(self.save_config.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)

    def test_nxos_config_save_changed_true(self):
        args = dict(save_when='changed', lines=['hostname foo', 'interface GigabitEthernet0/0', 'no ip address'])
        set_module_args(args)
        self.execute_module(changed=True)
        self.assertEqual(self.save_config.call_count, 1)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 1)

    def test_nxos_config_save_changed_false(self):
        args = dict(save_when='changed')
        set_module_args(args)
        self.execute_module()
        self.assertEqual(self.save_config.call_count, 0)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)

    def test_nxos_config_defaults_false(self):
        set_module_args(dict(lines=['hostname localhost'], defaults=False))
        result = self.execute_module(changed=True)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.get_config.call_args[1], dict(flags=[]))

    def test_nxos_config_defaults_true(self):
        set_module_args(dict(lines=['hostname localhost'], defaults=True))
        result = self.execute_module(changed=True)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.get_config.call_args[1], dict(flags=['all']))

    def test_nxos_config_defaults_false_backup_true(self):
        set_module_args(dict(lines=['hostname localhost'], defaults=False, backup=True))
        result = self.execute_module(changed=True)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.get_config.call_args[1], dict(flags=[]))

    def test_nxos_config_defaults_true_backup_true(self):
        set_module_args(dict(lines=['hostname localhost'], defaults=True, backup=True))
        result = self.execute_module(changed=True)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.get_config.call_args[1], dict(flags=['all']))
