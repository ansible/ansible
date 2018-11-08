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
from ansible.modules.network.iosxr import iosxr_config
from ansible.plugins.cliconf.iosxr import Cliconf
from units.modules.utils import set_module_args
from .iosxr_module import TestIosxrModule, load_fixture


class TestIosxrConfigModule(TestIosxrModule):

    module = iosxr_config

    def setUp(self):
        super(TestIosxrConfigModule, self).setUp()

        self.patcher_get_config = patch('ansible.modules.network.iosxr.iosxr_config.get_config')
        self.mock_get_config = self.patcher_get_config.start()

        self.patcher_exec_command = patch('ansible.modules.network.iosxr.iosxr_config.load_config')
        self.mock_exec_command = self.patcher_exec_command.start()

        self.mock_get_connection = patch('ansible.modules.network.iosxr.iosxr_config.get_connection')
        self.get_connection = self.mock_get_connection.start()

        self.conn = self.get_connection()
        self.conn.edit_config = MagicMock()

        self.cliconf_obj = Cliconf(MagicMock())
        self.running_config = load_fixture('iosxr_config_config.cfg')

    def tearDown(self):
        super(TestIosxrConfigModule, self).tearDown()

        self.patcher_get_config.stop()
        self.patcher_exec_command.stop()
        self.mock_get_connection.stop()

    def load_fixtures(self, commands=None):
        config_file = 'iosxr_config_config.cfg'
        self.mock_get_config.return_value = load_fixture(config_file)
        self.mock_exec_command.return_value = 'dummy diff'

    def test_iosxr_config_unchanged(self):
        src = load_fixture('iosxr_config_config.cfg')
        set_module_args(dict(src=src))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, src))
        self.execute_module()

    def test_iosxr_config_src(self):
        src = load_fixture('iosxr_config_src.cfg')
        set_module_args(dict(src=src))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(src, self.running_config))
        commands = ['hostname foo', 'interface GigabitEthernet0/0',
                    'no ip address']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_iosxr_config_lines_wo_parents(self):
        lines = ['hostname foo']
        set_module_args(dict(lines=lines))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_config_lines_w_parents(self):
        lines = ['shutdown']
        parents = ['interface GigabitEthernet0/0']
        candidate = parents + lines
        set_module_args(dict(lines=lines, parents=parents))
        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = iosxr_config.get_candidate(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config))
        commands = ['interface GigabitEthernet0/0', 'shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_config_before(self):
        lines = ['hostname foo']
        set_module_args(dict(lines=lines, before=['test1', 'test2']))
        commands = ['test1', 'test2', 'hostname foo']
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_iosxr_config_after(self):
        lines = ['hostname foo']
        set_module_args(dict(lines=lines, after=['test1', 'test2']))
        commands = ['hostname foo', 'test1', 'test2']
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_iosxr_config_before_after_no_change(self):
        lines = ['hostname router']
        set_module_args(dict(lines=lines,
                             before=['test1', 'test2'],
                             after=['test3', 'test4']))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        self.execute_module()

    def test_iosxr_config_config(self):
        config = 'hostname localhost'
        lines = ['hostname router']
        set_module_args(dict(lines=['hostname router'], config=config))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), config))
        commands = ['hostname router']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_config_replace_block(self):
        lines = ['description test string', 'test string']
        parents = ['interface GigabitEthernet0/0']
        set_module_args(dict(lines=lines, replace='block', parents=parents))
        commands = parents + lines

        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = iosxr_config.get_candidate(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_replace='block', path=parents))
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_config_force(self):
        lines = ['hostname router']
        set_module_args(dict(lines=lines, force=True))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config, diff_match='none'))
        self.execute_module(changed=True, commands=lines)

    def test_iosxr_config_admin(self):
        lines = ['username admin', 'group root-system', 'secret P@ssw0rd']
        set_module_args(dict(lines=lines, admin=True))
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff('\n'.join(lines), self.running_config))
        self.execute_module(changed=True, commands=lines)

    def test_iosxr_config_match_none(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string']
        parents = ['interface GigabitEthernet0/0']
        set_module_args(dict(lines=lines, parents=parents, match='none'))
        commands = parents + lines
        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = iosxr_config.get_candidate(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='none', path=parents))

        self.execute_module(changed=True, commands=commands, sort=False)

    def test_iosxr_config_match_strict(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string',
                 'shutdown']
        parents = ['interface GigabitEthernet0/0']
        set_module_args(dict(lines=lines, parents=parents, match='strict'))
        commands = parents + ['shutdown']
        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = iosxr_config.get_candidate(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='strict', path=parents))

        self.execute_module(changed=True, commands=commands, sort=False)

    def test_iosxr_config_match_exact(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string',
                 'shutdown']
        parents = ['interface GigabitEthernet0/0']
        set_module_args(dict(lines=lines, parents=parents, match='exact'))
        commands = parents + lines
        module = MagicMock()
        module.params = {'lines': lines, 'parents': parents, 'src': None}
        candidate_config = iosxr_config.get_candidate(module)
        self.conn.get_diff = MagicMock(return_value=self.cliconf_obj.get_diff(candidate_config, self.running_config, diff_match='exact', path=parents))

        self.execute_module(changed=True, commands=commands, sort=False)

    def test_iosxr_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_iosxr_config_src_and_parents_fails(self):
        args = dict(src='foo', parents='foo')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_iosxr_config_match_exact_requires_lines(self):
        args = dict(match='exact')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_iosxr_config_match_strict_requires_lines(self):
        args = dict(match='strict')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_iosxr_config_replace_block_requires_lines(self):
        args = dict(replace='block')
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_iosxr_config_replace_config_requires_src(self):
        args = dict(replace='config')
        set_module_args(args)
        result = self.execute_module(failed=True)
