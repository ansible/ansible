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
from units.modules.utils import set_module_args
from ansible.modules.network.ironware import ironware_config
from .ironware_module import TestIronwareModule, load_fixture


class TestIronwareConfigModule(TestIronwareModule):

    module = ironware_config

    def setUp(self):
        super(TestIronwareConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ironware.ironware_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ironware.ironware_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.ironware.ironware_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestIronwareConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        config_file = 'ironware_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def execute_module(self, failed=False, changed=False, updates=None, sort=True, defaults=False):

        self.load_fixtures(updates)

        if failed:
            result = self.failed()
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed)
            self.assertEqual(result['changed'], changed, result)

        if updates is not None:
            if sort:
                self.assertEqual(sorted(updates), sorted(result['updates']), result['updates'])
            else:
                self.assertEqual(updates, result['updates'], result['updates'])

        return result

    def test_ironware_config_unchanged(self):
        src = load_fixture('ironware_config_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_ironware_config_src(self):
        src = load_fixture('ironware_config_src.cfg')
        set_module_args(dict(src=src))
        updates = ['hostname foo', 'interface ethernet 1/1',
                   'no ip address']
        self.execute_module(changed=True, updates=updates)

    def test_ironware_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_ironware_config_save_always(self):
        self.run_commands.return_value = "hostname foobar"
        set_module_args(dict(save_when='always'))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 1)
        self.assertEqual(self.load_config.call_count, 0)

    def test_ironware_config_lines_wo_parents(self):
        set_module_args(dict(lines=['hostname foobar']))
        updates = ['hostname foobar']
        self.execute_module(changed=True, updates=updates)

    def test_ironware_config_lines_w_parents(self):
        set_module_args(dict(lines=['disable'], parents=['interface ethernet 1/1']))
        updates = ['interface ethernet 1/1', 'disable']
        self.execute_module(changed=True, updates=updates)

    def test_ironware_config_before(self):
        set_module_args(dict(lines=['hostname foo'], before=['test1', 'test2']))
        updates = ['test1', 'test2', 'hostname foo']
        self.execute_module(changed=True, updates=updates, sort=False)

    def test_ironware_config_after(self):
        set_module_args(dict(lines=['hostname foo'], after=['test1', 'test2']))
        updates = ['hostname foo', 'test1', 'test2']
        self.execute_module(changed=True, updates=updates, sort=False)

    def test_ironware_config_before_after_no_change(self):
        set_module_args(dict(lines=['hostname router'],
                             before=['test1', 'test2'],
                             after=['test3', 'test4']))
        self.execute_module()

    def test_ironware_config_config(self):
        config = 'hostname localhost'
        set_module_args(dict(lines=['hostname router'], config=config))
        updates = ['hostname router']
        self.execute_module(changed=True, updates=updates)

    def test_ironware_config_replace_block(self):
        lines = ['port-name test string', 'test string']
        parents = ['interface ethernet 1/1']
        set_module_args(dict(lines=lines, replace='block', parents=parents))
        updates = parents + lines
        self.execute_module(changed=True, updates=updates)

    def test_ironware_config_match_none(self):
        lines = ['hostname router']
        set_module_args(dict(lines=lines, match='none'))
        self.execute_module(changed=True, updates=lines)

    def test_ironware_config_match_none_parents(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'port-name test string']
        parents = ['interface ethernet 1/1']
        set_module_args(dict(lines=lines, parents=parents, match='none'))
        updates = parents + lines
        self.execute_module(changed=True, updates=updates, sort=False)

    def test_ironware_config_match_strict(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'port-name test string',
                 'disable']
        parents = ['interface ethernet 1/1']
        set_module_args(dict(lines=lines, parents=parents, match='strict'))
        updates = parents + ['disable']
        self.execute_module(changed=True, updates=updates, sort=False)

    def test_ironware_config_match_exact(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'port-name test string',
                 'disable']
        parents = ['interface ethernet 1/1']
        set_module_args(dict(lines=lines, parents=parents, match='exact'))
        updates = parents + lines
        self.execute_module(changed=True, updates=updates, sort=False)
