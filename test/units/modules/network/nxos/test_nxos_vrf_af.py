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
from ansible.modules.network.nxos import nxos_vrf_af
from .nxos_module import TestNxosModule, set_module_args


class TestNxosVrfafModule(TestNxosModule):

    module = nxos_vrf_af

    def setUp(self):
        super(TestNxosVrfafModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_vrf_af.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_vrf_af.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosVrfafModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_nxos_vrf_af_present(self):
        set_module_args(dict(vrf='ntc', afi='ipv4', safi='unicast', state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['commands']), sorted(['vrf context ntc',
                                                             'address-family ipv4 unicast']))

    def test_nxos_vrf_af_absent(self):
        set_module_args(dict(vrf='ntc', afi='ipv4', safi='unicast', state='absent'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_route_target(self):
        set_module_args(dict(vrf='ntc', afi='ipv4', safi='unicast', route_target_both_auto_evpn=True))
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['commands']), sorted(['vrf context ntc',
                                                             'address-family ipv4 unicast',
                                                             'route-target both auto evpn']))
