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
from ansible.modules.network.nxos import nxos_config
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosConfigModule(TestNxosModule):

    module = nxos_config

    def setUp(self):
        super(TestNxosConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_capabilities = patch('ansible.modules.network.nxos.nxos_config.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'device_info': {'network_os_platform': 'N9K-NXOSV'}}

    def tearDown(self):
        super(TestNxosConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('nxos_config', 'config.cfg')
        self.load_config.return_value = None

    def test_nxos_config_no_change(self):
        args = dict(lines=['hostname localhost'])
        set_module_args(args)
        result = self.execute_module()

    def test_nxos_config_src(self):
        args = dict(src=load_fixture('nxos_config', 'candidate.cfg'))
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['hostname switch01', 'interface Ethernet1',
                  'description test interface', 'no shutdown', 'ip routing']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])

    def test_nxos_config_replace_src(self):
        set_module_args(dict(replace_src='config.txt', replace='config'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['config replace config.txt'])

    def test_nxos_config_lines(self):
        args = dict(lines=['hostname switch01', 'ip domain-name eng.ansible.com'])
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])

    def test_nxos_config_before(self):
        args = dict(lines=['hostname switch01', 'ip domain-name eng.ansible.com'],
                    before=['before command'])

        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['before command', 'hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])
        self.assertEqual('before command', result['commands'][0])

    def test_nxos_config_after(self):
        args = dict(lines=['hostname switch01', 'ip domain-name eng.ansible.com'],
                    after=['after command'])

        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['after command', 'hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])
        self.assertEqual('after command', result['commands'][-1])

    def test_nxos_config_parents(self):
        args = dict(lines=['ip address 1.2.3.4/5', 'no shutdown'], parents=['interface Ethernet10'])
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
