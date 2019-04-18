#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.frr.providers.cli.config.bgp.process import Provider
from ansible.modules.network.frr import frr_bgp
from .frr_module import TestFrrModule, load_fixture


class TestFrrBgpModule(TestFrrModule):
    module = frr_bgp

    def setUp(self):
        super(TestFrrBgpModule, self).setUp()
        self._bgp_config = load_fixture('frr_bgp_config')

    def test_frr_bgp(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, router_id='192.0.2.2', networks=None,
                                               address_family=None), operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['router bgp 64496', 'bgp router-id 192.0.2.2', 'exit'])

    def test_frr_bgp_idempotent(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, router_id='192.0.2.1', networks=None,
                                               address_family=None), operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_frr_bgp_remove(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, networks=None,
                                               address_family=None), operation='delete'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['no router bgp 64496'])

    def test_frr_bgp_neighbor(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, neighbors=[dict(neighbor='192.51.100.2', remote_as=64496)],
                                               networks=None, address_family=None),
                                   operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['router bgp 64496', 'neighbor 192.51.100.2 remote-as 64496', 'exit'])

    def test_frr_bgp_neighbor_idempotent(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, neighbors=[dict(neighbor='192.51.100.1', remote_as=64496,
                                                                             timers=dict(keepalive=120, holdtime=360))],
                                               networks=None, address_family=None),
                                   operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_frr_bgp_network(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, networks=[dict(prefix='192.0.2.0', masklen=24, route_map='RMAP_1')],
                                               address_family=None),
                                   operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(sorted(commands), sorted(['router bgp 64496', 'network 192.0.2.0/24 route-map RMAP_1', 'exit']))

    def test_frr_bgp_network_idempotent(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, networks=[dict(prefix='192.0.1.0', masklen=24, route_map='RMAP_1'),
                                                                       dict(prefix='198.51.100.0', masklen=24, route_map='RMAP_2')],
                                               address_family=None),
                                   operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_frr_bgp_address_family_redistribute(self):
        rd_1 = dict(protocol='ospf', id='233', metric=90, route_map=None)

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', safi='unicast', redistribute=[rd_1])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        cmd = ['router bgp 64496', 'address-family ipv4 unicast', 'redistribute ospf 233 metric 90',
               'exit-address-family', 'exit']
        self.assertEqual(sorted(commands), sorted(cmd))

    def test_frr_bgp_address_family_redistribute_idempotent(self):
        rd_1 = dict(protocol='eigrp', metric=10, route_map='RMAP_3', id=None)
        rd_2 = dict(protocol='static', metric=100, id=None, route_map=None)

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', safi='unicast', redistribute=[rd_1, rd_2])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_frr_bgp_address_family_neighbors(self):
        af_nbr_1 = dict(neighbor='192.51.100.1', maximum_prefix=35, activate=True)
        af_nbr_2 = dict(neighbor='192.51.100.3', route_reflector_client=True, activate=True)

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', safi='multicast', neighbors=[af_nbr_1, af_nbr_2])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        cmd = ['router bgp 64496', 'address-family ipv4 multicast', 'neighbor 192.51.100.1 activate',
               'neighbor 192.51.100.1 maximum-prefix 35', 'neighbor 192.51.100.3 activate',
               'neighbor 192.51.100.3 route-reflector-client', 'exit-address-family', 'exit']
        self.assertEqual(sorted(commands), sorted(cmd))

    def test_frr_bgp_address_family_neighbors_idempotent(self):
        af_nbr_1 = dict(neighbor='2.2.2.2', remove_private_as=True, maximum_prefix=100)

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', safi='unicast', neighbors=[af_nbr_1])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_frr_bgp_address_family_networks(self):
        net = dict(prefix='1.0.0.0', masklen=8, route_map='RMAP_1')
        net2 = dict(prefix='192.168.1.0', masklen=24, route_map='RMAP_2')

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', safi='multicast', networks=[net, net2])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        cmd = ['router bgp 64496', 'address-family ipv4 multicast', 'network 1.0.0.0/8 route-map RMAP_1',
               'network 192.168.1.0/24 route-map RMAP_2', 'exit-address-family', 'exit']
        self.assertEqual(sorted(commands), sorted(cmd))

    def test_frr_bgp_address_family_networks_idempotent(self):
        net = dict(prefix='10.0.0.0', masklen=8, route_map='RMAP_1')
        net2 = dict(prefix='20.0.0.0', masklen=8, route_map='RMAP_2')

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', safi='multicast', networks=[net, net2])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_frr_bgp_operation_override(self):
        net_1 = dict(prefix='1.0.0.0', masklen=8, route_map='RMAP_1')
        net_2 = dict(prefix='192.168.1.0', masklen=24, route_map='RMAP_2')
        nbr_1 = dict(neighbor='192.51.100.1', remote_as=64496, advertisement_interval=120)
        nbr_2 = dict(neighbor='192.51.100.3', remote_as=64496, timers=dict(keepalive=300, holdtime=360))
        af_nbr_1 = dict(neighbor='192.51.100.1', maximum_prefix=35)
        af_nbr_2 = dict(neighbor='192.51.100.3', route_reflector_client=True)

        af_1 = dict(afi='ipv4', safi='unicast', neighbors=[af_nbr_1, af_nbr_2])
        af_2 = dict(afi='ipv4', safi='multicast', networks=[net_1, net_2])
        config = dict(bgp_as=64496, neighbors=[nbr_1, nbr_2], address_family=[af_1, af_2], networks=None)

        obj = Provider(params=dict(config=config, operation='override'))
        commands = obj.render(self._bgp_config)

        cmd = ['no router bgp 64496', 'router bgp 64496', 'neighbor 192.51.100.1 remote-as 64496',
               'neighbor 192.51.100.1 advertisement-interval 120', 'neighbor 192.51.100.3 remote-as 64496',
               'neighbor 192.51.100.3 timers 300 360', 'address-family ipv4 unicast',
               'neighbor 192.51.100.1 maximum-prefix 35', 'neighbor 192.51.100.3 route-reflector-client', 'exit-address-family',
               'address-family ipv4 multicast', 'network 1.0.0.0/8 route-map RMAP_1', 'network 192.168.1.0/24 route-map RMAP_2',
               'exit-address-family', 'exit']

        self.assertEqual(sorted(commands), sorted(cmd))

    def test_frr_bgp_operation_replace(self):
        rd = dict(protocol='ospf', id=223, metric=110, route_map=None)
        net = dict(prefix='10.0.0.0', masklen=8, route_map='RMAP_1')
        net2 = dict(prefix='20.0.0.0', masklen=8, route_map='RMAP_2')

        af_1 = dict(afi='ipv4', safi='unicast', redistribute=[rd])
        af_2 = dict(afi='ipv4', safi='multicast', networks=[net, net2])

        config = dict(bgp_as=64496, address_family=[af_1, af_2], networks=None)
        obj = Provider(params=dict(config=config, operation='replace'))
        commands = obj.render(self._bgp_config)

        cmd = ['router bgp 64496', 'address-family ipv4 unicast', 'redistribute ospf 223 metric 110', 'no redistribute eigrp',
               'no redistribute static', 'exit-address-family', 'exit']

        self.assertEqual(sorted(commands), sorted(cmd))

    def test_frr_bgp_operation_replace_with_new_as(self):
        rd = dict(protocol='ospf', id=223, metric=110, route_map=None)

        af_1 = dict(afi='ipv4', safi='unicast', redistribute=[rd])

        config = dict(bgp_as=64497, address_family=[af_1], networks=None)
        obj = Provider(params=dict(config=config, operation='replace'))
        commands = obj.render(self._bgp_config)

        cmd = ['no router bgp 64496', 'router bgp 64497', 'address-family ipv4 unicast', 'redistribute ospf 223 metric 110',
               'exit-address-family', 'exit']

        self.assertEqual(sorted(commands), sorted(cmd))
