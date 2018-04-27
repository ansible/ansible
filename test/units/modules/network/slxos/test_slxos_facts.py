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

from ansible.compat.tests.mock import patch
from ansible.modules.network.slxos import slxos_facts
from units.modules.utils import set_module_args
from .slxos_module import TestSlxosModule, load_fixture


class TestSlxosFactsModule(TestSlxosModule):

    module = slxos_facts

    def setUp(self):
        super(TestSlxosFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.slxos.slxos_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestSlxosFactsModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            commands = args[1]
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('slxos_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_slxos_facts(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_model'], 'BR-SLX9140'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_serialnum'], 'EXH3349M005'
        )
