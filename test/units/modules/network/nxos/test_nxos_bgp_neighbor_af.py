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
from ansible.modules.network.nxos import nxos_bgp_neighbor_af
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosBgpNeighborAfModule(TestNxosModule):

    module = nxos_bgp_neighbor_af

    def setUp(self):
        super(TestNxosBgpNeighborAfModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_bgp_neighbor_af.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_bgp_neighbor_af.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosBgpNeighborAfModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('nxos_bgp', 'config.cfg')
        self.load_config.return_value = []

    def test_nxos_bgp_neighbor_af(self):
        set_module_args(dict(asn=65535, neighbor='192.0.2.3', afi='ipv4',
                             safi='unicast', route_reflector_client=True))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
            'router bgp 65535', 'neighbor 192.0.2.3', 'address-family ipv4 unicast',
            'route-reflector-client'
        ])

    def test_nxos_bgp_neighbor_af_exists(self):
        set_module_args(dict(asn=65535, neighbor='3.3.3.5', afi='ipv4', safi='unicast'))
        self.execute_module(changed=False, commands=[])

    def test_nxos_bgp_neighbor_af_absent(self):
        set_module_args(dict(asn=65535, neighbor='3.3.3.5', afi='ipv4', safi='unicast', state='absent'))
        self.execute_module(
            changed=True, sort=False,
            commands=['router bgp 65535', 'neighbor 3.3.3.5', 'no address-family ipv4 unicast']
        )

    def test_nxos_bgp_neighbor_af_advertise_map(self):
        set_module_args(dict(asn=65535, neighbor='3.3.3.5', afi='ipv4', safi='unicast',
                             advertise_map_exist=['my_advertise_map', 'my_exist_map']))
        self.execute_module(
            changed=True, sort=False,
            commands=['router bgp 65535', 'neighbor 3.3.3.5', 'address-family ipv4 unicast', 'advertise-map my_advertise_map exist-map my_exist_map']
        )

    def test_nxos_bgp_neighbor_af_advertise_map_non_exist(self):
        set_module_args(dict(asn=65535, neighbor='3.3.3.5', afi='ipv4', safi='unicast',
                             advertise_map_non_exist=['my_advertise_map', 'my_non_exist_map']))
        self.execute_module(
            changed=True, sort=False,
            commands=['router bgp 65535', 'neighbor 3.3.3.5', 'address-family ipv4 unicast', 'advertise-map my_advertise_map non-exist-map my_non_exist_map']
        )

    def test_nxos_bgp_neighbor_af_max_prefix_limit_default(self):
        set_module_args(dict(asn=65535, neighbor='3.3.3.5', afi='ipv4',
                             safi='unicast', max_prefix_limit='default'))
        self.execute_module(
            changed=True, sort=False,
            commands=['router bgp 65535', 'neighbor 3.3.3.5', 'address-family ipv4 unicast', 'no maximum-prefix']
        )

    def test_nxos_bgp_neighbor_af_max_prefix(self):
        set_module_args(dict(asn=65535, neighbor='3.3.3.5', afi='ipv4',
                             safi='unicast', max_prefix_threshold=20,
                             max_prefix_limit=20))
        self.execute_module(
            changed=True, sort=False,
            commands=['router bgp 65535', 'neighbor 3.3.3.5', 'address-family ipv4 unicast', 'maximum-prefix 20 20']
        )

    def test_nxos_bgp_neighbor_af_disable_peer_as_check(self):
        set_module_args(dict(asn=65535, neighbor='3.3.3.5', afi='ipv4',
                             safi='unicast', disable_peer_as_check=True))
        self.execute_module(
            changed=True,
            commands=['router bgp 65535', 'neighbor 3.3.3.5', 'address-family ipv4 unicast', 'disable-peer-as-check']
        )
