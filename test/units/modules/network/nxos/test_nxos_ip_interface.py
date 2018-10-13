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

from units.compat.mock import patch
from ansible.modules.network.nxos import _nxos_ip_interface
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosIPInterfaceModule(TestNxosModule):

    module = _nxos_ip_interface

    def setUp(self):
        super(TestNxosIPInterfaceModule, self).setUp()

        self.mock_get_interface_mode = patch(
            'ansible.modules.network.nxos._nxos_ip_interface.get_interface_mode')
        self.get_interface_mode = self.mock_get_interface_mode.start()

        self.mock_send_show_command = patch(
            'ansible.modules.network.nxos._nxos_ip_interface.send_show_command')
        self.send_show_command = self.mock_send_show_command.start()

        self.mock_load_config = patch('ansible.modules.network.nxos._nxos_ip_interface.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_capabilities = patch('ansible.modules.network.nxos._nxos_ip_interface.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'network_api': 'cliconf'}

    def tearDown(self):
        super(TestNxosIPInterfaceModule, self).tearDown()
        self.mock_get_interface_mode.stop()
        self.mock_send_show_command.stop()
        self.mock_load_config.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_interface_mode.return_value = 'layer3'
        self.send_show_command.return_value = [load_fixture('', '_nxos_ip_interface.cfg')]
        self.load_config.return_value = None

    def test_nxos_ip_interface_ip_present(self):
        set_module_args(dict(interface='eth2/1', addr='1.1.1.2', mask=8))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'],
                         ['interface eth2/1',
                          'no ip address 192.0.2.1/8',
                          'ip address 1.1.1.2/8'])

    def test_nxos_ip_interface_ip_idempotent(self):
        set_module_args(dict(interface='eth2/1', addr='192.0.2.1', mask=8))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_ip_interface_ip_absent(self):
        set_module_args(dict(interface='eth2/1', state='absent',
                             addr='192.0.2.1', mask=8))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'],
                         ['interface eth2/1', 'no ip address 192.0.2.1/8'])
