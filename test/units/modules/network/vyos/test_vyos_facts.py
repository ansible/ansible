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
from ansible.modules.network.vyos import vyos_facts
from units.modules.utils import set_module_args
from .vyos_module import TestVyosModule, load_fixture


class TestVyosFactsModule(TestVyosModule):

    module = vyos_facts

    def setUp(self):
        super(TestVyosFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.vyos.vyos_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestVyosFactsModule, self).tearDown()
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
                filename = str(command).replace(' ', '_')
                output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_vyos_facts_default(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        facts = result.get('ansible_facts')
        self.assertEqual(len(facts), 5)
        self.assertEqual(facts['ansible_net_hostname'].strip(), 'vyos01')
        self.assertEqual(facts['ansible_net_version'], 'VyOS')

    def test_vyos_facts_not_all(self):
        set_module_args(dict(gather_subset='!all'))
        result = self.execute_module()
        facts = result.get('ansible_facts')
        self.assertEqual(len(facts), 5)
        self.assertEqual(facts['ansible_net_hostname'].strip(), 'vyos01')
        self.assertEqual(facts['ansible_net_version'], 'VyOS')

    def test_vyos_facts_exclude_most(self):
        set_module_args(dict(gather_subset=['!neighbors', '!config']))
        result = self.execute_module()
        facts = result.get('ansible_facts')
        self.assertEqual(len(facts), 5)
        self.assertEqual(facts['ansible_net_hostname'].strip(), 'vyos01')
        self.assertEqual(facts['ansible_net_version'], 'VyOS')

    def test_vyos_facts_invalid_subset(self):
        set_module_args(dict(gather_subset='cereal'))
        result = self.execute_module(failed=True)
