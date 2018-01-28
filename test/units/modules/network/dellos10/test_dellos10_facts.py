# (c) 2016 Red Hat Inc.
#
# (c) 2017 Dell EMC.
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
from units.modules.utils import set_module_args
from .dellos10_module import TestDellos10Module, load_fixture
from ansible.modules.network.dellos10 import dellos10_facts


class TestDellos10Facts(TestDellos10Module):

    module = dellos10_facts

    def setUp(self):
        super(TestDellos10Facts, self).setUp()

        self.mock_run_command = patch(
            'ansible.modules.network.dellos10.dellos10_facts.run_commands')
        self.run_command = self.mock_run_command.start()

    def tearDown(self):
        super(TestDellos10Facts, self).tearDown()

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
                filename = filename.replace(':', '_colon_')
                output.append(load_fixture(filename))
            return output

        self.run_command.side_effect = load_from_file

    def test_dellos10_facts_gather_subset_default(self):
        set_module_args(dict())
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('hardware', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('interfaces', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals('os10', ansible_facts['ansible_net_hostname'])
        self.assertIn('ethernet1/1/8', ansible_facts['ansible_net_interfaces'].keys())
        self.assertEquals(7936, ansible_facts['ansible_net_memtotal_mb'])
        self.assertEquals(5693, ansible_facts['ansible_net_memfree_mb'])

    def test_dellos10_facts_gather_subset_config(self):
        set_module_args({'gather_subset': 'config'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('config', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals('os10', ansible_facts['ansible_net_hostname'])
        self.assertIn('ansible_net_config', ansible_facts)

    def test_dellos10_facts_gather_subset_hardware(self):
        set_module_args({'gather_subset': 'hardware'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('hardware', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals('x86_64', ansible_facts['ansible_net_cpu_arch'])
        self.assertEquals(7936, ansible_facts['ansible_net_memtotal_mb'])
        self.assertEquals(5693, ansible_facts['ansible_net_memfree_mb'])

    def test_dellos10_facts_gather_subset_interfaces(self):
        set_module_args({'gather_subset': 'interfaces'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('interfaces', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('ethernet1/1/8', ansible_facts['ansible_net_interfaces'].keys())
        self.assertEquals(sorted(['mgmt1/1/1', 'ethernet1/1/4', 'ethernet1/1/2', 'ethernet1/1/3', 'ethernet1/1/1']),
                          sorted(list(ansible_facts['ansible_net_neighbors'].keys())))
        self.assertIn('ansible_net_interfaces', ansible_facts)
