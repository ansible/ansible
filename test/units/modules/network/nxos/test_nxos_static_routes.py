#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.nxos import nxos_static_routes
from ansible.module_utils.network.nxos.config.static_routes.static_routes import add_commands
from units.modules.utils import set_module_args
from .nxos_module import TestNxosModule, load_fixture, set_module_args
import itertools


class TestNxosStaticRoutesModule(TestNxosModule):

    module = nxos_static_routes

    def setUp(self):
        super(TestNxosStaticRoutesModule, self).setUp()

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
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start(
        )

        self.mock_edit_config = patch(
            'ansible.module_utils.network.nxos.providers.providers.CliProvider.edit_config'
        )
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.nxos.facts.static_routes.static_routes.Static_routesFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestNxosStaticRoutesModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, transport='cli', filename=None):
        if filename is None:
            filename = 'nxos_static_routes_config.cfg'

        def load_from_file(*args, **kwargs):
            output = load_fixture(filename)
            return output

        self.execute_show_command.side_effect = load_from_file

    def test_nxos_static_routes_merged(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="120.10.10.0/24",
                                       next_hops=[
                                           dict(forward_router_address="12.12.12.12",
                                                interface="Ethernet1",
                                                admin_distance=5)
                                       ])
                         ])
                ])
            ], state="merged"))
        commands = ['ip route 120.10.10.0/24 Ethernet1 12.12.12.12 5']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="120.10.10.0/24",
                                       next_hops=[
                                           dict(forward_router_address="12.12.12.12",
                                                interface="Ethernet1",
                                                admin_distance=5)
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
                             dict(dest="99.9.9.0/24",
                                  next_hops=[
                                      dict(forward_router_address="191.123.14.1",
                                           tag=12,
                                           route_name="replaced_route")
                                  ])
                         ])
                ])
            ], state="replaced"))
        commands = ['no ip route 120.10.10.0/24 Ethernet1 12.12.12.12 5',
                    'ip route 99.9.9.0/24 191.123.14.1 tag 12 name replaced_route'
                    ]
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="99.9.9.0/24",
                                  next_hops=[
                                      dict(forward_router_address="191.123.14.1",
                                           tag=12,
                                           route_name="replaced_route")
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
                             dict(dest="120.10.10.0/24",
                                       next_hops=[
                                           dict(forward_router_address="12.12.12.12",
                                                interface="Ethernet1",
                                                admin_distance=5)
                                       ])
                         ])
                ])
            ], state="overridden"))
        commands = [
            'vrf context default',
            'no ip route 10.10.30.0/24 1.2.4.8'
            'ip route 120.10.10.0/24 Ethernet1 12.12.12.12 5'
            'vrf context test'
            'no ip route 10.8.0.0/14 15.16.17.18'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv4",
                         routes=[
                             dict(dest="120.10.10.0/24",
                                       next_hops=[
                                           dict(forward_router_address="12.12.12.12",
                                                interface="Ethernet1",
                                                admin_distance=5)
                                       ])
                         ])
                ])
            ], state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_static_routes_deletedvrf(self):
        set_module_args(dict(config=[dict(vrf="test", )], state="deleted"))
        commands = ['vrf context default',
                    'no ip route 10.8.0.0/14 15.16.17.18']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_deletedroute(self):
        set_module_args(
            dict(config=[
                dict(vrf="test",
                     address_families=[
                         dict(afi="ipv4", routes=[dict(dest="10.8.0.0/24")])
                     ])
            ], state="deleted"))
        commands = ['vrf context test',
                    'no ip route 10.8.0.0/14 15.16.17.18']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_static_routes_deletedafi(self):
        set_module_args(
            dict(config=[
                dict(address_families=[dict(afi="ipv4")])
            ], state="deleted"))
        commands = ['no ip route 10.10.30.0/24 1.2.4.8']
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
                    'ipv6 route 1200:10::/64 2048:ae12::/64 Ethernet1 5']
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), sorted(
            commands), result['rendered'])

