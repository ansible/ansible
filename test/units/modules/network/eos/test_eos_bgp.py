#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.eos.providers.cli.config.bgp.process import Provider
from ansible.modules.network.eos import eos_bgp
from .eos_module import TestEosModule, load_fixture


class TestFrrBgpModule(TestEosModule):
    module = eos_bgp

    def setUp(self):
        super(TestFrrBgpModule, self).setUp()
        self._bgp_config = load_fixture('eos_bgp_config.cfg')

    def test_eos_bgp(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, router_id='192.0.2.2', networks=None,
                                               address_family=None), operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['router bgp 64496', 'router-id 192.0.2.2', 'exit'])

    def test_eos_bgp_idempotent(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, router_id='192.0.2.1',
                                               networks=None, address_family=None), operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_eos_bgp_remove(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, networks=None, address_family=None), operation='delete'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['no router bgp 64496'])

    def test_eos_bgp_neighbor(self):
        obj = Provider(params=dict(config=dict(bgp_as=64496, neighbors=[dict(neighbor='198.51.100.12', remote_as=64498)],
                                               networks=None, address_family=None),
                                   operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, ['router bgp 64496', 'neighbor 198.51.100.12 remote-as 64498', 'exit'])

    def test_eos_bgp_neighbor_idempotent(self):
        neighbors = [dict(neighbor='198.51.100.102', remote_as=64498, timers=dict(keepalive=300, holdtime=360)),
                     dict(neighbor='203.0.113.5', remote_as=64511, maximum_prefix=500)]
        obj = Provider(params=dict(config=dict(bgp_as=64496, neighbors=neighbors, networks=None, address_family=None),
                                   operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_eos_bgp_network(self):
        obj = Provider(
            params=dict(config=dict(bgp_as=64496, networks=[dict(prefix='203.0.113.0', masklen=24, route_map='RMAP_1')],
                                    address_family=None),
                        operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(sorted(commands), sorted(['router bgp 64496', 'network 203.0.113.0/24 route-map RMAP_1', 'exit']))

    def test_eos_bgp_network_idempotent(self):
        obj = Provider(
            params=dict(config=dict(bgp_as=64496, networks=[dict(prefix='192.0.2.0', masklen=27, route_map='RMAP_1'),
                                                            dict(prefix='198.51.100.0', masklen=24, route_map='RMAP_2')],
                                    address_family=None),
                        operation='merge'))
        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_eos_bgp_redistribute(self):
        rd_1 = dict(protocol='rip', route_map='RMAP_1')

        config = dict(bgp_as=64496, redistribute=[rd_1], networks=None, address_family=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        cmd = ['router bgp 64496', 'redistribute rip route-map RMAP_1', 'exit']
        self.assertEqual(sorted(commands), sorted(cmd))

    def test_eos_bgp_redistribute_idempotent(self):
        rd_1 = dict(protocol='ospf', route_map='RMAP_1')
        config = dict(bgp_as=64496, redistribute=[rd_1], networks=None, address_family=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_eos_bgp_address_family_neighbors(self):
        af_nbr_1 = dict(neighbor='198.51.100.104', default_originate=True, activate=True)
        af_nbr_2 = dict(neighbor='198.51.100.105', activate=True, weight=30, graceful_restart=True)

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', neighbors=[af_nbr_1, af_nbr_2])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        cmd = ['router bgp 64496', 'address-family ipv4', 'neighbor 198.51.100.104 activate',
               'neighbor 198.51.100.104 default-originate', 'neighbor 198.51.100.105 weight 30',
               'neighbor 198.51.100.105 activate', 'neighbor 198.51.100.105 graceful-restart', 'exit', 'exit']
        self.assertEqual(sorted(commands), sorted(cmd))

    def test_eos_bgp_address_family_neighbors_idempotent(self):
        af_nbr_1 = dict(neighbor='198.51.100.102', activate=True, graceful_restart=True, default_originate=True, weight=25)
        af_nbr_2 = dict(neighbor='192.0.2.111', activate=True, default_originate=True)
        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', neighbors=[af_nbr_1, af_nbr_2])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_eos_bgp_address_family_networks(self):
        net = dict(prefix='203.0.113.128', masklen=26, route_map='RMAP_1')
        net2 = dict(prefix='203.0.113.192', masklen=26, route_map='RMAP_2')

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv4', networks=[net, net2])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        cmd = ['router bgp 64496', 'address-family ipv4', 'network 203.0.113.128/26 route-map RMAP_1',
               'network 203.0.113.192/26 route-map RMAP_2', 'exit', 'exit']
        self.assertEqual(sorted(commands), sorted(cmd))

    def test_eos_bgp_address_family_networks_idempotent(self):
        net = dict(prefix='2001:db8:8000::', masklen=34, route_map=None)
        net2 = dict(prefix='2001:db8:c000::', masklen=34, route_map=None)

        config = dict(bgp_as=64496, address_family=[dict(afi='ipv6', networks=[net, net2])],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='merge'))

        commands = obj.render(self._bgp_config)
        self.assertEqual(commands, [])

    def test_eos_bgp_operation_override(self):
        net_1 = dict(prefix='2001:0db8:0800::', masklen=38, route_map='RMAP_1')
        net_2 = dict(prefix='2001:0db8:1c00::', masklen=38, route_map='RMAP_2')
        nbr_1 = dict(neighbor='203.0.113.111', remote_as=64511, update_source='Ethernet2')
        nbr_2 = dict(neighbor='203.0.113.120', remote_as=64511, timers=dict(keepalive=300, holdtime=360))
        af_nbr_1 = dict(neighbor='203.0.113.111', activate=True)
        af_nbr_2 = dict(neighbor='203.0.113.120', activate=True, default_originate=True)

        af_1 = dict(afi='ipv4', neighbors=[af_nbr_1, af_nbr_2])
        af_2 = dict(afi='ipv6', networks=[net_1, net_2])
        config = dict(bgp_as=64496, neighbors=[nbr_1, nbr_2], address_family=[af_1, af_2],
                      networks=None)

        obj = Provider(params=dict(config=config, operation='override'))
        commands = obj.render(self._bgp_config)

        cmd = ['no router bgp 64496', 'router bgp 64496', 'neighbor 203.0.113.111 remote-as 64511',
               'neighbor 203.0.113.111 update-source Ethernet2', 'neighbor 203.0.113.120 remote-as 64511',
               'neighbor 203.0.113.120 timers 300 360', 'address-family ipv4',
               'neighbor 203.0.113.111 activate', 'neighbor 203.0.113.120 default-originate', 'neighbor 203.0.113.120 activate',
               'exit', 'address-family ipv6', 'network 2001:0db8:0800::/38 route-map RMAP_1',
               'network 2001:0db8:1c00::/38 route-map RMAP_2',
               'exit', 'exit']

        self.assertEqual(sorted(commands), sorted(cmd))

    def test_eos_bgp_operation_replace(self):
        net = dict(prefix='203.0.113.0', masklen=27, route_map='RMAP_1')
        net2 = dict(prefix='192.0.2.32', masklen=29, route_map='RMAP_2')
        net_3 = dict(prefix='2001:db8:8000::', masklen=34, route_map=None)
        net_4 = dict(prefix='2001:db8:c000::', masklen=34, route_map=None)

        af_1 = dict(afi='ipv4', networks=[net, net2])
        af_2 = dict(afi='ipv6', networks=[net_3, net_4])

        config = dict(bgp_as=64496, address_family=[af_1, af_2], networks=None)
        obj = Provider(params=dict(config=config, operation='replace'))
        commands = obj.render(self._bgp_config)

        cmd = ['router bgp 64496', 'address-family ipv4', 'network 203.0.113.0/27 route-map RMAP_1',
               'network 192.0.2.32/29 route-map RMAP_2', 'no network 192.0.2.0/27', 'no network 198.51.100.0/24',
               'exit', 'exit']

        self.assertEqual(sorted(commands), sorted(cmd))

    def test_eos_bgp_operation_replace_with_new_as(self):
        nbr = dict(neighbor='203.0.113.124', remote_as=64496, update_source='Ethernet3')

        config = dict(bgp_as=64497, neighbors=[nbr], networks=None, address_family=None)
        obj = Provider(params=dict(config=config, operation='replace'))
        commands = obj.render(self._bgp_config)

        cmd = ['no router bgp 64496', 'router bgp 64497', 'neighbor 203.0.113.124 remote-as 64496',
               'neighbor 203.0.113.124 update-source Ethernet3', 'exit']

        self.assertEqual(sorted(commands), sorted(cmd))
