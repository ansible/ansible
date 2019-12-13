#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.modules.network.nxos import nxos_static_routes
from units.compat.mock import patch, MagicMock
from units.modules.utils import set_module_args
from .nxos_module import TestNxosModule, load_fixture


class TestNxosStaticRoutesModule(TestNxosModule):

    module = nxos_static_routes

    def setUp(self):
        super(TestNxosStaticRoutesModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.modules.network.nxos.nxos_static_route.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch(
            'ansible.module_utils.network.common.cfg.base.get_resource_connection'
        )
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start(
        )

        self.mock_get_resource_connection_facts = patch(
            'ansible.module_utils.network.common.facts.facts.get_resource_connection'
        )
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch(
            'ansible.module_utils.network.nxos.config.static_routes.static_routes.Static_routes.edit_config'
        )
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.nxos.facts.static_routes.static_routes.Static_routesFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestNxosStaticRoutesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            non_vrf_data = [
                'ip route 192.0.2.16/28 192.0.2.24 name initial_route']
            vrf_data = [
                'vrf context test\n  ip route 192.0.2.96/28 192.0.2.122 vrf dest_vrf']

            output = non_vrf_data + vrf_data
            return output

        self.execute_show_command.side_effect = load_from_file

    def test_nxos_static_routes_merged(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="192.0.2.32/28",
                                       next_hops=[
                                           dict(forward_router_address="192.0.2.40",
                                                interface="Ethernet1/2",
                                                admin_distance=5)
                                       ])
                         ])
                ])
            ], state="merged"))
        commands = ['vrf context default',
                    'ip route 192.0.2.32/28 Ethernet1/2 192.0.2.40 5']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="192.0.2.16/28",
                                       next_hops=[
                                           dict(forward_router_address="192.0.2.24",
                                                route_name='initial_route')
                                       ])
                         ])
                ])
            ], state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_static_routes_replaced(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="192.0.2.48/28",
                                  next_hops=[
                                      dict(forward_router_address="192.0.2.50",
                                           tag=12,
                                           route_name="replaced_route")
                                  ])
                         ])
                ])
            ], state="replaced"))
        commands = ['vrf context default',
                    'no ip route 192.0.2.16/28 192.0.2.24 name initial_route',
                    'ip route 192.0.2.48/28 192.0.2.50 name replaced_route tag 12'
                    ]
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="192.0.2.16/28",
                                       next_hops=[
                                           dict(forward_router_address="192.0.2.24",
                                                route_name='initial_route')
                                       ])
                         ])
                ])
            ], state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_static_routes_overridden(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="192.0.2.112/28",
                                  next_hops=[
                                      dict(forward_router_address="192.0.2.68",
                                           route_name="overridden_route",
                                           dest_vrf="end_vrf")
                                  ])
                         ])
                ])
            ], state="overridden"))
        commands = [
            'vrf context default',
            'no ip route 192.0.2.16/28 192.0.2.24 name initial_route',
            'ip route 192.0.2.112/28 192.0.2.68 vrf end_vrf name overridden_route',
            'vrf context test',
            'no ip route 192.0.2.96/28 192.0.2.122 vrf dest_vrf'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(vrf='test',
                     address_families=[
                         dict(afi="ipv4",
                              routes=[
                                  dict(dest="192.0.2.96/28",
                                       next_hops=[
                                           dict(forward_router_address="192.0.2.122",
                                                dest_vrf='dest_vrf')
                                       ])
                              ])
                     ]),
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="192.0.2.16/28",
                                  next_hops=[
                                      dict(forward_router_address="192.0.2.24",
                                           route_name='initial_route')
                                  ])
                         ])
                ]),
            ], state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_static_routes_deletedvrf(self):
        set_module_args(dict(config=[dict(vrf="test", )], state="deleted"))
        commands = ['vrf context test',
                    'no ip route 192.0.2.96/28 192.0.2.122 vrf dest_vrf']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_deletedroute(self):
        set_module_args(
            dict(config=[
                dict(vrf="test",
                     address_families=[
                         dict(afi="ipv4", routes=[dict(dest="192.0.2.96/28")])
                     ])
            ], state="deleted"))
        commands = ['vrf context test',
                    'no ip route 192.0.2.96/28 192.0.2.122 vrf dest_vrf']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_deletedafi(self):
        set_module_args(
            dict(config=[
                dict(address_families=[dict(afi="ipv4")])
            ], state="deleted"))
        commands = ['vrf context default',
                    'no ip route 192.0.2.16/28 192.0.2.24 name initial_route']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_rendered(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv6",
                              routes=[
                                  dict(dest="1200:10::/64",
                                       next_hops=[
                                           dict(forward_router_address="2048:ae12::/64",
                                                interface="Ethernet1",
                                                admin_distance=5)
                                       ])
                              ])
                     ])
            ], state="rendered"))
        commands = ['vrf context testvrf',
                    'ipv6 route 1200:10::/64 Ethernet1 2048:ae12::/64 5']
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), sorted(
            commands), result['rendered'])

    def test_nxos_static_routes_parsed(self):
        set_module_args(dict(running_config='''ip route 192.0.2.16/28 192.0.2.24 name initial_route
        vrf context test
          ip route 192.0.2.96/28 192.0.2.122 vrf dest_vrf''',
                             state="parsed"))
        result = self.execute_module(changed=False)
        compare_list = [{'vrf': 'test', 'address_families': [{'routes': [{'dest': '192.0.2.96/28', 'next_hops': [{'dest_vrf': 'dest_vrf', 'forward_router_address': '192.0.2.122'}]}], 'afi': 'ipv4'}]},
                        {'address_families': [{'routes': [{'dest': '192.0.2.16/28', 'next_hops': [{'route_name': 'initial_route', 'forward_router_address': '192.0.2.24'}]}], 'afi': 'ipv4'}]}]
        self.assertEqual(result['parsed'],
                         compare_list, result['parsed'])

    def test_nxos_static_routes_gathered(self):
        set_module_args(dict(config=[], state="gathered"))
        result = self.execute_module(changed=False)
        compare_list = [{'vrf': 'test', 'address_families': [{'routes': [{'dest': '192.0.2.96/28', 'next_hops': [{'dest_vrf': 'dest_vrf', 'forward_router_address': '192.0.2.122'}]}], 'afi': 'ipv4'}]},
                        {'address_families': [{'routes': [{'dest': '192.0.2.16/28', 'next_hops': [{'route_name': 'initial_route', 'forward_router_address': '192.0.2.24'}]}], 'afi': 'ipv4'}]}]
        self.assertEqual(result['gathered'],
                         compare_list, result['gathered'])
