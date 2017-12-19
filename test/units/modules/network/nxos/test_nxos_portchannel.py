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
from ansible.modules.network.nxos import nxos_portchannel
from .nxos_module import TestNxosModule, set_module_args


class TestNxosPortchannelModule(TestNxosModule):

    module = nxos_portchannel

    def setUp(self):
        super(TestNxosPortchannelModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_portchannel.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_portchannel.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_portchannel.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_get_capabilities = patch('ansible.modules.network.nxos.nxos_portchannel.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'network_api': 'cliconf'}

    def tearDown(self):
        super(TestNxosPortchannelModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_nxos_portchannel(self):
        set_module_args(dict(group='99',
                             members=['Ethernet2/1', 'Ethernet2/2'],
                             mode='active',
                             state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface port-channel99',
                                              'interface Ethernet2/1',
                                              'channel-group 99 mode active',
                                              'interface Ethernet2/2',
                                              'channel-group 99 mode active'])
