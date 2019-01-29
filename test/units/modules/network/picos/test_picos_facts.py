# -*- coding: utf-8 -*-
#
# (c) 2019, Pica8, Inc. <simon.yang@pica8.com>
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
import re

from units.compat.mock import patch
from ansible.modules.network.picos import picos_facts
from units.modules.utils import set_module_args
from .picos_module import TestPicosModule, load_fixture


class TestPicosFactsModule(TestPicosModule):

    module = picos_facts

    def setUp(self):
        super(TestPicosFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.picos.picos_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestPicosFactsModule, self).tearDown()
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
                filename = re.sub(r'\W+', '_', str(command))
                output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_picos_facts_default(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        facts = result.get('ansible_facts')
        self.assertEqual(len(facts), 5)
        self.assertEqual(facts['ansible_net_hostname'].strip(), 'XorPlus')
        self.assertEqual(facts['ansible_net_serialnum'].strip(), 'QTFCXI3170013')
        self.assertEqual(facts['ansible_net_model'].strip(), 'P3295')
        self.assertEqual(facts['ansible_net_version'].strip(), '2.10.2/d9ce4ec')

    def test_picos_facts_not_all(self):
        set_module_args(dict(gather_subset='-all'))
        result = self.execute_module()
        facts = result.get('ansible_facts')
        self.assertEqual(len(facts), 5)
        self.assertEqual(facts['ansible_net_hostname'].strip(), 'XorPlus')
        self.assertEqual(facts['ansible_net_serialnum'].strip(), 'QTFCXI3170013')
        self.assertEqual(facts['ansible_net_model'].strip(), 'P3295')
        self.assertEqual(facts['ansible_net_version'].strip(), '2.10.2/d9ce4ec')

    def test_picos_facts_exclude_most(self):
        set_module_args(dict(gather_subset=['-hardware', '-config']))
        result = self.execute_module()
        facts = result.get('ansible_facts')
        self.assertEqual(len(facts), 6)
        self.assertEqual(facts['ansible_net_hostname'].strip(), 'XorPlus')
        self.assertEqual(facts['ansible_net_serialnum'].strip(), 'QTFCXI3170013')
        self.assertEqual(facts['ansible_net_model'].strip(), 'P3295')
        self.assertEqual(facts['ansible_net_license']['hardwareid'].strip(), '036A-FAE5-DAE6-1A34')
        self.assertEqual(facts['ansible_net_license']['type'].strip(), '1GE')
        self.assertEqual(facts['ansible_net_license']['installed'], False)

    def test_picos_facts_invalid_subset(self):
        set_module_args(dict(gather_subset='cereal'))
        result = self.execute_module(failed=True)
