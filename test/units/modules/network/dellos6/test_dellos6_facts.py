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

from units.compat.mock import patch
from units.modules.utils import set_module_args
from .dellos6_module import TestDellos6Module, load_fixture
from ansible.modules.network.dellos6 import dellos6_facts


class TestDellos6Facts(TestDellos6Module):

    module = dellos6_facts

    def setUp(self):
        super(TestDellos6Facts, self).setUp()

        self.mock_run_command = patch(
            'ansible.modules.network.dellos6.dellos6_facts.run_commands')
        self.run_command = self.mock_run_command.start()

    def tearDown(self):
        super(TestDellos6Facts, self).tearDown()

        self.mock_run_command.stop()

    def load_fixtures(self, commands=None):

        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item)
                    command = obj['command']
                except ValueError:
                    command = item
                if '|' in command:
                    command = str(command).replace('|', '')
                filename = str(command).replace(' ', '_')
                filename = filename.replace('/', '7')
                output.append(load_fixture(filename))
            return output

        self.run_command.side_effect = load_from_file

    def test_dellos6_facts_gather_subset_default(self):
        set_module_args(dict())
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('hardware', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('interfaces', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals('"dellos6_sw1"', ansible_facts['ansible_net_hostname'])
        self.assertIn('Te1/0/1', ansible_facts['ansible_net_interfaces'].keys())
        self.assertEquals(1682, ansible_facts['ansible_net_memtotal_mb'])
        self.assertEquals(623, ansible_facts['ansible_net_memfree_mb'])

    def test_dellos6_facts_gather_subset_config(self):
        set_module_args({'gather_subset': 'config'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('config', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals('"dellos6_sw1"', ansible_facts['ansible_net_hostname'])
        self.assertIn('ansible_net_config', ansible_facts)

    def test_dellos6_facts_gather_subset_hardware(self):
        set_module_args({'gather_subset': 'hardware'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('hardware', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals(1682, ansible_facts['ansible_net_memtotal_mb'])
        self.assertEquals(623, ansible_facts['ansible_net_memfree_mb'])

    def test_dellos6_facts_gather_subset_interfaces(self):
        set_module_args({'gather_subset': 'interfaces'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('interfaces', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('Te1/0/1', ansible_facts['ansible_net_interfaces'].keys())
        self.assertEquals(['Te1/0/5'], list(ansible_facts['ansible_net_neighbors'].keys()))
        self.assertIn('ansible_net_interfaces', ansible_facts)
