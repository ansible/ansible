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

from units.compat.mock import patch
from units.modules.utils import set_module_args
from ansible.modules.network.nos import nos_facts
from .nos_module import TestNosModule, load_fixture


class TestNosFactsModule(TestNosModule):

    module = nos_facts

    def setUp(self):
        super(TestNosFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.nos.nos_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestNosFactsModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            commands = args[1]
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('nos_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_nos_facts(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_model'], 'BR-VDX6740'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_serialnum'], 'CPL2541K01E'
        )
