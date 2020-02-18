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
from ansible.modules.network.vyos import vyos_static_routes
from units.modules.utils import set_module_args
from .vyos_module import TestVyosModule, load_fixture


class TestVyosStaticRoutesModule(TestVyosModule):

    module = vyos_static_routes

    def setUp(self):
        super(TestVyosStaticRoutesModule, self).setUp()
        self.mock_get_config = patch('ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.vyos.facts.static_routes.static_routes.Static_routesFacts.get_device_data')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestVyosStaticRoutesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            return load_fixture('vyos_static_routes_config.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_vyos_static_routes_merged(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(
                        afi='ipv4',
                        routes=[
                            dict(
                                dest='192.0.2.48/28',
                                next_hops=[
                                    dict(
                                        forward_router_address='192.0.2.9'),
                                    dict(forward_router_address='192.0.2.10')
                                ])
                        ])
                ])
            ],
                state="merged"))
        commands = ['set protocols static route 192.0.2.48/28',
                    "set protocols static route 192.0.2.48/28 next-hop '192.0.2.9'",
                    "set protocols static route 192.0.2.48/28 next-hop '192.0.2.10'"]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_static_routes_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(
                        afi='ipv4',
                        routes=[
                            dict(
                                dest='192.0.2.32/28',
                                next_hops=[
                                    dict(
                                        forward_router_address='192.0.2.9'),
                                    dict(forward_router_address='192.0.2.10')
                                ])
                        ])
                ])
            ],
                state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_vyos_static_routes_replaced(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(
                        afi='ipv4',
                        routes=[
                            dict(
                                dest='192.0.2.48/28',
                                next_hops=[
                                    dict(
                                        forward_router_address='192.0.2.9'),
                                    dict(forward_router_address='192.0.2.10')
                                ])
                        ])
                ])
            ],
                state="replaced"))
        commands = ["set protocols static route 192.0.2.48/28",
                    "set protocols static route 192.0.2.48/28 next-hop '192.0.2.9'",
                    "set protocols static route 192.0.2.48/28 next-hop '192.0.2.10'"]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_static_routes_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(
                        afi='ipv4',
                        routes=[
                            dict(
                                dest='192.0.2.32/28',
                                next_hops=[
                                    dict(
                                        forward_router_address='192.0.2.9'),
                                    dict(forward_router_address='192.0.2.10')
                                ])
                        ])
                ])
            ],
                state="replaced"))

        self.execute_module(changed=False, commands=[])

    def test_vyos_static_routes_overridden(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(
                        afi='ipv4',
                        routes=[
                            dict(
                                dest='192.0.2.48/28',
                                next_hops=[
                                    dict(
                                        forward_router_address='192.0.2.9'),
                                    dict(forward_router_address='192.0.2.10')
                                ])
                        ])
                ])
            ],
                state="overridden"))
        commands = ['delete protocols static route 192.0.2.32/28',
                    'set protocols static route 192.0.2.48/28',
                    "set protocols static route 192.0.2.48/28 next-hop '192.0.2.9'",
                    "set protocols static route 192.0.2.48/28 next-hop '192.0.2.10'"]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_static_routes_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(
                        afi='ipv4',
                        routes=[
                            dict(
                                dest='192.0.2.32/28',
                                next_hops=[
                                    dict(
                                        forward_router_address='192.0.2.9'),
                                    dict(forward_router_address='192.0.2.10')
                                ])
                        ])
                ])
            ],
                state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_vyos_static_routes_deleted(self):
        set_module_args(
            dict(config=[
                dict(address_families=[
                    dict(afi='ipv4', routes=[dict(dest='192.0.2.32/28')])
                ])
            ],
                state="deleted"))
        commands = ['delete protocols static route 192.0.2.32/28']
        self.execute_module(changed=True, commands=commands)
