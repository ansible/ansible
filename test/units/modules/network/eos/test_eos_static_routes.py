#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.eos import eos_static_routes
from ansible.module_utils.network.eos.config.static_routes.static_routes import add_commands
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture
import itertools


class TestEosStaticRoutesModule(TestEosModule):
    module = eos_static_routes

    def setUp(self):
        super(TestEosStaticRoutesModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.common.network.Config.load_config')
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
            'ansible.module_utils.network.eos.providers.providers.CliProvider.edit_config'
        )
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.eos.facts.static_routes.static_routes.Static_routesFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestEosStaticRoutesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli', filename=None):
        if filename is None:
            filename = 'eos_static_routes_config.cfg'

        def load_from_file(*args, **kwargs):
            output = load_fixture(filename)
            return output

        self.execute_show_command.side_effect = load_from_file

    def test_eos_static_routes_merged(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv6",
                              routes=[
                                  dict(dest="1200:10::/64",
                                       next_hops=[
                                           dict(interface="Ethernet1",
                                                admin_distance=55)
                                       ])
                              ])
                     ])
            ], state="merged"))
        commands = ['ipv6 route vrf testvrf 1200:10::/64 Ethernet1 55']
        self.execute_module(changed=True, commands=commands)

    def test_eos_static_routes_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv4",
                              routes=[
                                  dict(dest="120.1.1.0/24",
                                       next_hops=[
                                           dict(interface="Ethernet1",
                                                admin_distance=23)
                                       ])
                              ])
                     ])
            ], state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_eos_static_routes_default(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv6",
                              routes=[
                                  dict(dest="1200:10::/64",
                                       next_hops=[
                                           dict(interface="Ethernet1",
                                                admin_distance=55)
                                       ])
                              ])
                     ])
            ]))
        commands = ['ipv6 route vrf testvrf 1200:10::/64 Ethernet1 55']
        self.execute_module(changed=True, commands=commands)

    def test_eos_static_routes_default_idempotent(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv4",
                              routes=[
                                  dict(dest="120.1.1.0/24",
                                       next_hops=[
                                           dict(interface="Ethernet1",
                                                admin_distance=23)
                                       ])
                              ])
                     ])
            ]))
        self.execute_module(changed=False, commands=[])

    def test_eos_static_routes_replaced(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi="ipv6",
                         routes=[
                             dict(dest="1000:10::/64",
                                  next_hops=[
                                      dict(interface="Ethernet1",
                                           admin_distance=55)
                                  ])
                         ])
                ])
            ], state="replaced"))
        commands = [
            'ipv6 route 1000:10::/64 Ethernet1 55',
            'no ipv6 route 1000:10::/64 Ethernet1 67 tag 98'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_eos_static_routes_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv4",
                              routes=[
                                  dict(dest="120.1.1.0/24",
                                       next_hops=[
                                           dict(interface="Ethernet1",
                                                admin_distance=23)
                                       ])
                              ])
                     ])
            ], state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_eos_static_routes_overridden(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv6",
                              routes=[
                                  dict(dest="1200:10::/64",
                                       next_hops=[
                                           dict(interface="Ethernet1",
                                                admin_distance=55)
                                       ])
                              ])
                     ])
            ], state="overridden"))
        commands = [
            'ipv6 route vrf testvrf 1200:10::/64 Ethernet1 55',
            'no ip route vrf testvrf 120.1.1.0/24 Ethernet1 23',
            'no ip route 10.1.1.0/24 Management1',
            'no ipv6 route 1000:10::/64 Ethernet1 67 tag 98'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_eos_static_routes_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv4",
                              routes=[
                                  dict(dest="120.1.1.0/24",
                                       next_hops=[
                                           dict(interface="Ethernet1",
                                                admin_distance=23)
                                       ])
                              ])
                     ]),
                dict(address_families=[
                     dict(afi="ipv4",
                          routes=[
                              dict(dest="10.1.1.0/24",
                                   next_hops=[
                                       dict(interface="Management1")
                                   ])
                          ])
                     ]),
                dict(address_families=[
                     dict(afi="ipv6",
                          routes=[
                              dict(dest="1000:10::/64",
                                   next_hops=[
                                       dict(interface="Ethernet1",
                                            admin_distance=67,
                                            tag=98)
                                   ])
                          ])
                     ])
            ], state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_eos_static_routes_deletedvrf(self):
        set_module_args(dict(config=[dict(vrf="testvrf", )], state="deleted"))
        commands = ['no ip route vrf testvrf 120.1.1.0/24 Ethernet1 23']
        self.execute_module(changed=True, commands=commands)

    def test_eos_static_routes_deletedroute(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv4", routes=[dict(dest="120.1.1.0/24")])
                     ])
            ], state="deleted"))
        commands = ['no ip route vrf testvrf 120.1.1.0/24 Ethernet1 23']

        self.execute_module(changed=True, commands=commands)

    def test_eos_static_routes_deletedafi(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf", address_families=[dict(afi="ipv4")])
            ], state="deleted"))
        commands = ['no ip route vrf testvrf 120.1.1.0/24 Ethernet1 23']
        self.execute_module(changed=True, commands=commands)

    def test_eos_static_routes_gathered(self):
        set_module_args(
            dict(config=[],
                 state="gathered"))
        result = self.execute_module(changed=False, filename='eos_static_routes_config.cfg')
        commands = []
        for gathered_cmds in result['gathered']:
            cfg = add_commands(gathered_cmds)
            commands.append(cfg)
        commands = list(itertools.chain(*commands))
        config_commands = ['ip route 10.1.1.0/24 Management1', 'ipv6 route 1000:10::/64 Ethernet1 67 tag 98',
                           'ip route vrf testvrf 120.1.1.0/24 Ethernet1 23']
        self.assertEqual(sorted(config_commands), sorted(commands), result['gathered'])

    def test_eos_static_routes_rendered(self):
        set_module_args(
            dict(config=[
                dict(vrf="testvrf",
                     address_families=[
                         dict(afi="ipv6",
                              routes=[
                                  dict(dest="1200:10::/64",
                                       next_hops=[
                                           dict(interface="Ethernet1",
                                                admin_distance=55)
                                       ])
                              ])
                     ])
            ], state="rendered"))
        commands = ['ipv6 route vrf testvrf 1200:10::/64 Ethernet1 55']
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), sorted(commands), result['rendered'])

    def test_eos_static_routes_parsed(self):
        set_module_args(
            dict(running_config="ipv6 route vrf testvrf 1200:10::/64 Ethernet1 55",
                 state="parsed"))
        commands = ['ipv6 route vrf testvrf 1200:10::/64 Ethernet1 55']
        result = self.execute_module(changed=False)
        parsed_commands = []
        for cmds in result['parsed']:
            cfg = add_commands(cmds)
            parsed_commands.append(cfg)
        parsed_commands = list(itertools.chain(*parsed_commands))
        self.assertEqual(sorted(parsed_commands), sorted(commands), result['parsed'])
