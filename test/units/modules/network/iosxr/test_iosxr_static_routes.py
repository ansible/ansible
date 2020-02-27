#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.iosxr import iosxr_static_routes
from units.modules.utils import set_module_args
from .iosxr_module import TestIosxrModule, load_fixture


class TestIosxrStaticRoutesModule(TestIosxrModule):
    module = iosxr_static_routes

    def setUp(self):
        super(TestIosxrStaticRoutesModule, self).setUp()

        self.mock_get_config = patch(
            "ansible.module_utils.network.common.network.Config.get_config"
        )
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            "ansible.module_utils.network.common.network.Config.load_config"
        )
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch(
            "ansible.module_utils.network.common.cfg.base.get_resource_connection"
        )
        self.get_resource_connection_config = (
            self.mock_get_resource_connection_config.start()
        )

        self.mock_get_resource_connection_facts = patch(
            "ansible.module_utils.network.common.facts.facts.get_resource_connection"
        )
        self.get_resource_connection_facts = (
            self.mock_get_resource_connection_facts.start()
        )

        self.mock_execute_show_command = patch(
            "ansible.module_utils.network.iosxr.facts.static_routes.static_routes.Static_routesFacts.get_device_data"
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestIosxrStaticRoutesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            return load_fixture("iosxr_static_routes_config.cfg")

        self.execute_show_command.side_effect = load_from_file

    def test_iosxr_static_routes_merged(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        vrf="dev_site",
                        address_families=[
                            dict(
                                afi="ipv6",
                                safi="unicast",
                                routes=[
                                    dict(
                                        dest="1200:10::/64",
                                        next_hops=[
                                            dict(
                                                interface="GigabitEthernet0/0/0/1",
                                                admin_distance=55,
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
                state="merged",
            )
        )
        commands = [
            "router static",
            "vrf dev_site",
            "address-family ipv6 unicast",
            "1200:10::/64 GigabitEthernet0/0/0/1 55",
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_static_routes_merged_idempotent(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        vrf="DEV_SITE",
                        address_families=[
                            dict(
                                afi="ipv4",
                                safi="unicast",
                                routes=[
                                    dict(
                                        dest="192.0.2.48/28",
                                        next_hops=[
                                            dict(
                                                interface="192.0.2.12",
                                                description="DEV",
                                                dest_vrf="test_1",
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
                state="merged",
            )
        )
        self.execute_module(changed=False, commands=[])

    def test_iosxr_static_routes_default(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        address_families=[
                            dict(
                                afi="ipv4",
                                safi="unicast",
                                routes=[
                                    dict(
                                        dest="192.168.1.0/24",
                                        next_hops=[
                                            dict(
                                                interface="GigabitEthernet0/0/0/2",
                                                track="ip_sla_2",
                                                vrflabel=1200,
                                            )
                                        ],
                                    )
                                ],
                            )
                        ]
                    )
                ]
            )
        )
        commands = [
            "router static",
            "address-family ipv4 unicast",
            "192.168.1.0/24 GigabitEthernet0/0/0/2 track ip_sla_2 vrflabel 1200",
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_static_routes_default_idempotent(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        address_families=[
                            dict(
                                afi="ipv4",
                                safi="unicast",
                                routes=[
                                    dict(
                                        dest="192.0.2.32/28",
                                        next_hops=[
                                            dict(
                                                forward_router_address="192.0.2.11",
                                                admin_distance=100,
                                            )
                                        ],
                                    )
                                ],
                            )
                        ]
                    )
                ]
            )
        )
        self.execute_module(changed=False, commands=[])

    def test_iosxr_static_routes_replaced(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        address_families=[
                            dict(
                                afi="ipv4",
                                safi="unicast",
                                routes=[
                                    dict(
                                        dest="192.0.2.16/28",
                                        next_hops=[
                                            dict(
                                                forward_router_address="192.0.2.11",
                                                admin_distance=100,
                                            )
                                        ],
                                    )
                                ],
                            )
                        ]
                    )
                ],
                state="replaced",
            )
        )
        commands = [
            "router static",
            "address-family ipv4 unicast",
            "no 192.0.2.16/28 192.0.2.10 FastEthernet0/0/0/1",
            "no 192.0.2.16/28 FastEthernet0/0/0/5",
            "192.0.2.16/28 192.0.2.11 100",
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_static_routes_replaced_idempotent(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        address_families=[
                            dict(
                                afi="ipv4",
                                safi="unicast",
                                routes=[
                                    dict(
                                        dest="192.0.2.16/28",
                                        next_hops=[
                                            dict(
                                                interface="FastEthernet0/0/0/5",
                                                track="ip_sla_1",
                                            ),
                                            dict(
                                                interface="FastEthernet0/0/0/1",
                                                forward_router_address="192.0.2.10",
                                                tag=10,
                                                description="LAB",
                                                metric=120,
                                            ),
                                        ],
                                    )
                                ],
                            )
                        ]
                    )
                ],
                state="replaced",
            )
        )
        self.execute_module(changed=False, commands=[])

    def test_iosxr_static_routes_overridden(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        vrf="DEV_SITE_NEW",
                        address_families=[
                            dict(
                                afi="ipv4",
                                safi="unicast",
                                routes=[
                                    dict(
                                        dest="192.0.4.16/28",
                                        next_hops=[
                                            dict(
                                                interface="FastEthernet0/0/0/5",
                                                track="ip_sla_1",
                                            ),
                                            dict(
                                                interface="FastEthernet0/0/0/1",
                                                forward_router_address="192.0.2.10",
                                                tag=10,
                                                description="LAB",
                                                metric=120,
                                            ),
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
                state="overridden",
            )
        )
        commands = [
            "router static",
            "no address-family ipv4 unicast",
            "no address-family ipv6 unicast",
            "no vrf DEV_SITE",
            "vrf DEV_SITE_NEW",
            "address-family ipv4 unicast",
            "192.0.4.16/28 192.0.2.10 FastEthernet0/0/0/1 description LAB metric 120 tag 10",
            "192.0.4.16/28 FastEthernet0/0/0/5 track ip_sla_1",
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_static_routes_deleted_next_hop(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        address_families=[
                            dict(
                                afi="ipv4",
                                safi="unicast",
                                routes=[
                                    dict(
                                        dest="192.0.2.16/28",
                                        next_hops=[
                                            dict(interface="FastEthernet0/0/0/5")
                                        ],
                                    )
                                ],
                            )
                        ]
                    )
                ],
                state="deleted",
            )
        )

        commands = [
            "router static",
            "address-family ipv4 unicast",
            "no 192.0.2.16/28 FastEthernet0/0/0/5",
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_static_routes_deleted_dest(self):
        set_module_args(
            dict(
                config=[
                    dict(
                        address_families=[
                            dict(
                                afi="ipv4",
                                safi="unicast",
                                routes=[dict(dest="192.0.2.16/28")],
                            )
                        ]
                    )
                ],
                state="deleted",
            )
        )

        commands = ["router static", "address-family ipv4 unicast", "no 192.0.2.16/28"]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_static_routes_deleted_afi(self):
        set_module_args(
            dict(
                config=[dict(address_families=[dict(afi="ipv4", safi="unicast")])],
                state="deleted",
            )
        )

        commands = [
            "router static",
            "no address-family ipv4 unicast",
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_static_routes_deleted_vrf(self):
        set_module_args(dict(config=[dict(vrf="DEV_SITE")], state="deleted"))

        commands = [
            "router static",
            "no vrf DEV_SITE",
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_static_routes_deleted_all(self):
        set_module_args(dict(state="deleted"))

        commands = [
            "no router static",
        ]
        self.execute_module(changed=True, commands=commands)
