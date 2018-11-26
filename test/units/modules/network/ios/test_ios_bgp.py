#
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
from ansible.modules.network.ios import ios_bgp
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosBgpModule(TestIosModule):
    module = ios_bgp

    def setUp(self):
        super(TestIosBgpModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ios.ios_bgp.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_bgp.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosBgpModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('ios_bgp_config.cfg')
        self.load_config.return_value = []

    def test_ios_bgp(self):
        set_module_args(dict(bgp_as='65535', router_id='192.0.2.11'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['router bgp 65535', 'bgp router-id 192.0.2.11'])

    def test_ios_bgp_unchanged(self):
        set_module_args(dict(bgp_as='65535', router_id='192.0.2.1'))
        self.execute_module()

    def test_ios_bgp_networks(self):
        set_module_args(dict(bgp_as='65535', networks=[dict(network='10.0.0.0', route_map='RMAP_1'),
                                                       dict(network='192.168.2.0', mask='255.255.254.0',
                                                            route_map='RMAP_2')]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['router bgp 65535', 'network 10.0.0.0 route-map RMAP_1',
                                              'network 192.168.2.0 mask 255.255.254.0 route-map RMAP_2'])

    def test_ios_bgp_networks_unchanged(self):
        set_module_args(dict(bgp_as='65535', networks=[dict(network='11.0.0.0', mask='255.255.0.0',
                                                            route_map='RMAP')]))
        self.execute_module()

    def test_ios_bgp_neighbors(self):
        set_module_args(dict(bgp_as='65535', neighbors=[dict(neighbor='192.168.0.100', remote_as='65535',
                                                             ebgp_multihop='5'), dict(neighbor='192.168.0.101',
                                                                                      remote_as=65535,
                                                                                      description='Neighbor1')]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['router bgp 65535', 'neighbor 192.168.0.100 remote-as 65535',
                                              'neighbor 192.168.0.100 ebgp-multihop 5',
                                              'neighbor 192.168.0.101 remote-as 65535',
                                              'neighbor 192.168.0.101 description Neighbor1'])
    def test_ios_bgp_neighbors_unchanged(self):
        set_module_args(dict(bgp_as='65535', neighbors=[dict(neighbor='2.2.2.2', remote_as='500',
                                                             timers=dict(keepalive=300, holdtime=350,
                                                                         min_neighbor_holdtime=330))]))
        self.execute_module()

    def test_ios_bgp_address_families(self):
        set_module_args(dict(bgp_as='65535', address_families=[dict(name='ipv4', cast='unicast',
                                                                    networks=[dict(network='12.0.0.0', route_map='RMAP2')],
                                                                    redistribute=[dict(protocol='eigrp', id='65', metric='100')]
                                                                    )]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['router bgp 65535', 'address-family ipv4', 'redistribute eigrp 65 metric 100',
                                              'network 12.0.0.0 route-map RMAP2',
                                              'exit-address-family'])

    def test_ios_bgp_address_families_unchanged(self):
        set_module_args(dict(bgp_as='65535', address_families=[dict(name='ipv4', cast='unicast',
                                                                    networks=[dict(network='192.168.3.0', mask='255.255.254.0')],
                                                                    redistribute=[dict(protocol='ospf', id='145', metric='120',
                                                                                       route_map='RMAP2')])]))
        self.execute_module()
