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

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_hsrp
from .nxos_module import TestNxosModule, set_module_args


class TestNxosHsrpModule(TestNxosModule):

    module = nxos_hsrp

    def setUp(self):
        super(TestNxosHsrpModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_hsrp.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_hsrp.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_capabilities = patch('ansible.modules.network.nxos.nxos_hsrp.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'network_api': 'cliconf'}

    def tearDown(self):
        super(TestNxosHsrpModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_nxos_hsrp(self):
        set_module_args(dict(group='10',
                             vip='192.0.2.2/8',
                             priority='150',
                             interface='Ethernet1/2',
                             preempt='enabled',
                             host='192.0.2.1'))
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['commands']), sorted(['config t',
                                                             'interface ethernet1/2',
                                                             'hsrp version 2',
                                                             'hsrp 10',
                                                             'priority 150',
                                                             'ip 192.0.2.2/8',
                                                             'preempt']))
