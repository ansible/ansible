#
# (c) 2018 Extreme Networks Inc.
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json

from units.compat.mock import patch
from units.modules.utils import set_module_args
from ansible.module_utils.common._collections_compat import Mapping
from ansible.modules.network.exos import exos_facts
from .exos_module import TestExosModule


class TestExosFactsModule(TestExosModule):

    module = exos_facts

    def setUp(self):
        super(TestExosFactsModule, self).setUp()

        self.mock_run_commands = patch('ansible.module_utils.network.exos.facts.legacy.base.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_resource_connection = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection = self.mock_get_resource_connection.start()

    def tearDown(self):
        super(TestExosFactsModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):

        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()
            fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')

            for command in commands:
                if isinstance(command, Mapping):
                    command = command['command']
                filename = str(command).replace(' ', '_')
                filename = os.path.join(fixture_path, filename)
                with open(filename) as f:
                    data = f.read()

                try:
                    data = json.loads(data)
                except Exception:
                    pass

                output.append(data)
            return output

        self.run_commands.side_effect = load_from_file

    def test_exos_facts_default(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_model'], 'X870-32c'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_serialnum'], '1604G-00175'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_version'], '22.5.1.7'
        )

    def test_exos_facts_hardware(self):
        set_module_args(dict(gather_subset='hardware'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_memfree_mb'], 7298
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_memtotal_mb'], 8192
        )

    def test_exos_facts_interfaces(self):
        set_module_args(dict(gather_subset='interfaces'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['1']['bandwidth_configured'], '25000'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['3']['description'], 'Database Server'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['3']['type'], 'Ethernet'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['vlan1']['ipv4'][0]['address'], '10.0.1.1'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['vlan3']['ipv6'][0]['address'], 'fe80::202:b3ff:fe1e:8329'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_all_ipv4_addresses'], ['10.0.1.1', '192.168.1.1']
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_all_ipv6_addresses'], ['fe80::202:b3ff:fe1e:8329']
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['vlan3']['type'], 'VLAN'
        )
