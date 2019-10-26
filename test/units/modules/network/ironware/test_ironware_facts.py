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
from ansible.modules.network.ironware import ironware_facts
from .ironware_module import TestIronwareModule, load_fixture


class TestIronwareFacts(TestIronwareModule):

    module = ironware_facts

    def setUp(self):
        super(TestIronwareFacts, self).setUp()
        self.mock_run_commands = patch(
            'ansible.modules.network.ironware.ironware_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestIronwareFacts, self).tearDown()
        self.mock_run_commands.stop()

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
                filename = str(command).split(' | ')[0].replace(' ', '_').replace('/', '7')
                output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_ironware_facts_gather_subset_default(self):
        set_module_args(dict())
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('hardware', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('interfaces', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals(['/flash/'], ansible_facts['ansible_net_filesystems'])
        self.assertIn('1/1', ansible_facts['ansible_net_interfaces'].keys())
        self.assertIn('10.69.1.6', ansible_facts['ansible_net_all_ipv4_addresses'])
        self.assertIn('2001:db8::1', ansible_facts['ansible_net_all_ipv6_addresses'])
        self.assertIn('ansible_net_neighbors', ansible_facts)
        self.assertIn('1/2', ansible_facts['ansible_net_neighbors'].keys())
        self.assertEquals(4096, ansible_facts['ansible_net_memtotal_mb'])
        self.assertEquals(3630, ansible_facts['ansible_net_memfree_mb'])
        self.assertEquals('5.8.0fT163', ansible_facts['ansible_net_version'])
        self.assertEquals('MLXe 4-slot Chassis', ansible_facts['ansible_net_model'])
        self.assertEquals('BGD2503J01F', ansible_facts['ansible_net_serialnum'])

    def test_ironware_facts_gather_subset_config(self):
        set_module_args({'gather_subset': 'config'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('config', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('ansible_net_config', ansible_facts)

    def test_ironware_facts_gather_subset_mpls(self):
        set_module_args({'gather_subset': 'mpls'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('mpls', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('ansible_net_mpls_lsps', ansible_facts)
        self.assertIn('ansible_net_mpls_vll', ansible_facts)
        self.assertIn('ansible_net_mpls_vll_local', ansible_facts)
        self.assertIn('ansible_net_mpls_vpls', ansible_facts)
        self.assertIn('LSP1', ansible_facts['ansible_net_mpls_lsps'].keys())
        self.assertIn('TEST-VLL', ansible_facts['ansible_net_mpls_vll'].keys())
        self.assertIn('TEST-LOCAL', ansible_facts['ansible_net_mpls_vll_local'].keys())
        self.assertIn('TEST-VPLS', ansible_facts['ansible_net_mpls_vpls'].keys())
