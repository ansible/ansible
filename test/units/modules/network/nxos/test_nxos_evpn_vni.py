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
from ansible.modules.network.nxos import nxos_evpn_vni
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosEvpnVniModule(TestNxosModule):

    module = nxos_evpn_vni

    def setUp(self):
        super(TestNxosEvpnVniModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_evpn_vni.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_evpn_vni.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_evpn_vni.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosEvpnVniModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('', 'nxos_evpn_vni_config.cfg')
        self.load_config.return_value = None

    def test_nxos_evpn_vni_present(self):
        set_module_args(dict(vni='6000',
                             route_target_import='5000:10',
                             state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['evpn',
                                              'vni 6000 l2',
                                              'route-target import 5000:10',
                                              'no route-target import auto'])

    def test_nxos_evpn_vni_absent_not_existing(self):
        set_module_args(dict(vni='12000', state='absent'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_evpn_vni_absent_existing(self):
        set_module_args(dict(vni='6000', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['evpn', 'no vni 6000 l2'])
