# (c) 2018 Red Hat Inc.
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from units.compat.mock import patch
from ansible.modules.network.edgeswitch import edgeswitch_facts
from units.modules.utils import set_module_args
from .edgeswitch_module import TestEdgeswitchModule, load_fixture


class TestEdgeswitchFactsModule(TestEdgeswitchModule):

    module = edgeswitch_facts

    def setUp(self):
        super(TestEdgeswitchFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.edgeswitch.edgeswitch_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestEdgeswitchFactsModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module = args
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('edgeswitch_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_edgeswitch_facts_default(self):
        set_module_args(dict(gather_subset=['all', '!interfaces', '!config']))
        result = self.execute_module()
        facts = result.get('ansible_facts')
        self.assertEqual(len(facts), 5)
        self.assertEqual(facts['ansible_net_hostname'], 'sw_test_1')
        self.assertEqual(facts['ansible_net_serialnum'], 'F09FC2EFD310')
        self.assertEqual(facts['ansible_net_version'], '1.7.4.5075842')

    def test_edgeswitch_facts_interfaces(self):
        set_module_args(dict(gather_subset='interfaces'))
        result = self.execute_module()
        facts = result.get('ansible_facts')
        self.assertEqual(len(facts), 6)
        self.assertEqual(facts['ansible_net_interfaces']['0/1']['operstatus'], 'Enable')
        self.assertEqual(facts['ansible_net_interfaces']['0/2']['mediatype'], '2.5G-BaseFX')
        self.assertEqual(facts['ansible_net_interfaces']['0/3']['physicalstatus'], '10G Full')
        self.assertEqual(facts['ansible_net_interfaces']['0/4']['lineprotocol'], 'Up')
        self.assertEqual(facts['ansible_net_interfaces']['0/15']['description'], 'UPLINK VIDEO WITH A VERY LONG DESCRIPTION THAT HELPS NO ONE')
