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

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.cnos import cnos_config

from .cnos_module import TestCnosModule, load_fixture
from units.modules.utils import set_module_args


class TestCnosConfigModule(TestCnosModule):

    module = cnos_config

    def setUp(self):
        self.patcher_get_config = patch('ansible.modules.network.cnos.cnos_config.get_config')
        self.mock_get_config = self.patcher_get_config.start()
        self.patcher_exec_command = patch('ansible.modules.network.cnos.cnos_config.load_config')
        self.mock_exec_command = self.patcher_exec_command.start()

    def tearDown(self):
        self.patcher_get_config.stop()
        self.patcher_exec_command.stop()

    def load_fixtures(self, commands=None):
        config_file = 'cnos_config_config.cfg'
        self.mock_get_config.return_value = load_fixture(config_file)
        self.mock_exec_command.return_value = 'dummy diff'

    def test_cnos_config_unchanged(self):
        src = load_fixture('cnos_config_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_cnos_config_src(self):
        src = load_fixture('cnos_config_src.cfg')
        set_module_args(dict(src=src))
        commands = ['hostname foo', 'interface ethernet 1/13',
                    'speed 10000']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_cnos_config_lines_wo_parents(self):
        set_module_args(dict(lines=['hostname foo']))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_config_lines_w_parents(self):
        set_module_args(dict(lines=['shutdown'], parents=['interface ethernet 1/13']))
        commands = ['interface ethernet 1/13', 'shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_config_before(self):
        set_module_args(dict(lines=['hostname foo'], before=['test1', 'test2']))
        commands = ['test1', 'test2', 'hostname foo']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_cnos_config_after(self):
        set_module_args(dict(lines=['hostname foo'], after=['test1', 'test2']))
        commands = ['hostname foo', 'test1', 'test2']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_cnos_config_before_after_no_change(self):
        set_module_args(dict(lines=['hostname ip10-241-107-39'],
                             before=['test1', 'test2'],
                             after=['test2', 'test3']))
        self.execute_module()

    def test_cnos_config_config(self):
        config = 'hostname localhost'
        set_module_args(dict(lines=['hostname ip10-241-107-39'], config=config))
        commands = ['hostname ip10-241-107-39']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_config_replace_block(self):
        lines = ['description test string', 'test string']
        parents = ['interface ethernet 1/13']
        set_module_args(dict(lines=lines, replace='block', parents=parents))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands)

    def test_cnos_config_match_none(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string']
        parents = ['interface ethernet 1/13']
        set_module_args(dict(lines=lines, parents=parents, match='none'))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_cnos_config_match_strict(self):
        lines = ['ip address 100.10.10.10/24', 'no switchport']
        parents = ['interface Ethernet1/12']
        set_module_args(dict(lines=lines, parents=parents, match='strict'))
        commands = parents + ['no switchport']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_cnos_config_match_exact(self):
        lines = ['ip address 1.2.3.4 255.255.255.0', 'description test string',
                 'no shutdown']
        parents = ['interface ethernet 1/13']
        set_module_args(dict(lines=lines, parents=parents, match='exact'))
        commands = parents + lines
        self.execute_module(changed=True, commands=commands, sort=False)
