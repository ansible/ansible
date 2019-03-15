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
from ansible.modules.network.voss import voss_facts
from .voss_module import TestVossModule, load_fixture


class TestVossFactsModule(TestVossModule):

    module = voss_facts

    def setUp(self):
        super(TestVossFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.voss.voss_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestVossFactsModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module = args
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('voss_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_voss_facts_default(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_model'], '4450GSX-PWR+'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_serialnum'], '14JP512E0001'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_version'], '7.0.0.0_B015'
        )

    def test_voss_facts_interfaces(self):
        set_module_args(dict(gather_subset='interfaces'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['1/1']['description'], 'serverA'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['Clip1']['ipv4'][0]['address'], '1.1.1.1'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_neighbors']['1/1'][0]['host'], 'X690-48t-2q-4c'
        )

    def test_voss_facts_hardware(self):
        set_module_args(dict(gather_subset='hardware'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_memfree_mb'], 625
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_memtotal_mb'], 1002
        )
