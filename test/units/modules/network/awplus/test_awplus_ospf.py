# (c) 2020 Allied Telesis
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
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.awplus import awplus_ospf
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusOspfModule(TestAwplusModule):

    module = awplus_ospf

    def setUp(self):
        super(TestAwplusOspfModule, self).setUp()

        self.mock_load_config = patch(
            "ansible.modules.network.awplus.awplus_ospf.load_config"
        )
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch(
            "ansible.modules.network.awplus.awplus_ospf.get_config"
        )
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestAwplusOspfModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=""):
        self.get_config.return_value = load_fixture("awplus_ospf_config.cfg")
        self.load_config.return_value = []

    def test_awplus_router_ospf(self):
        set_module_args({"router": {"process_id": 12}})
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["router ospf 12"])

    def test_awplus_router_ospf_change_nothing(self):
        set_module_args({"router": {"process_id": 100}})
        self.execute_module(changed=False)

    def test_awplus_router_ospf_no(self):
        set_module_args({"router": {"state": "absent"}})
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["no router ospf"])

    def test_awplus_router_ospf_no_process_id(self):
        set_module_args({"router": {"state": "absent", "process_id": 100}})
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["no router ospf 100"])

    def test_awplus_router_ospf_vrf(self):
        set_module_args({"router": {"vrf_instance": "red"}})
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["router ospf red"])

    def test_awplus_router_ospf_process_id_vrf(self):
        set_module_args({"router": {"process_id": 12, "vrf_instance": "red"}})
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["router ospf 12 red"])

    def test_awplus_ospf_area(self):
        set_module_args(
            {
                "router": {"process_id": 100}, "area": {"area_id": 1}
            }
        )
        self.execute_module(failed=True)

    def test_awplus_ospf_area_default_cost(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "default_cost": {"cost_value": 123}},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "area 1 default-cost 123"]
        )

    def test_awplus_ospf_area_default_cost_no_val(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "default_cost": {}},
            }
        )
        self.execute_module(failed=True)

    def test_awplus_ospf_area_default_cost_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "default_cost": {"state": "absent"}},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "no area 1 default-cost"]
        )

    def test_awplus_ospf_area_authentication(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "authentication": {"message_digest": True},
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "area 1 authentication message-digest"],
        )

    def test_awplus_ospf_area_authentication_change_nothing(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "authentication": {"state": "present"}},
            }
        )
        self.execute_module(changed=False)

    def test_awplus_ospf_area_authentication_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "authentication": {
                        "message_digest": True,
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "no area 1 authentication"]
        )

    def test_awplus_ospf_area_filter_list_in(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "filter_list": {
                        "prefix_list": "list1",
                        "direction": "in"
                    },
                },
            }
        )
        self.execute_module(changed=False)

    def test_awplus_ospf_area_filter_list_out(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "filter_list": {
                        "prefix_list": "list1",
                        "direction": "out"
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "area 1 filter-list prefix list1 out"],
        )

    def test_awplus_ospf_area_filter_list_in_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "filter_list": {
                        "prefix_list": "list1",
                        "direction": "in",
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no area 1 filter-list prefix list1 in"],
        )

    def test_awplus_ospf_area_filter_list_out_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "filter_list": {
                        "prefix_list": "list1",
                        "direction": "out",
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no area 1 filter-list prefix list1 out"],
        )

    def test_awplus_ospf_area_nssa_default_info(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "nssa": {
                        "default_information_originate": True,
                        "default_information_originate_metric_type": 2,
                        "default_information_originate_metric": 34,
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "area 1 nssa default-information-originate metric 34 "
                "metric-type 2",
            ],
        )

    def test_awplus_ospf_area_nssa_default_info_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "nssa": {
                        "state": "absent",
                        "default_information_originate": True,
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no area 1 nssa default-information-originate",
            ],
        )

    def test_awplus_ospf_area_nssa_no_redestribution(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "nssa": {"no_redistribution": True}},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "area 1 nssa no-redistribution"],
        )

    def test_awplus_ospf_area_nssa_no_redistribution_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "nssa": {"no_redistribution": True, "state": "absent"},
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no area 1 nssa no-redistribution"],
        )

    def test_awplus_ospf_area_nssa_no_summary(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "nssa": {"no_summary": True}},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "area 1 nssa no-summary"]
        )

    def test_awplus_ospf_area_nssa_no_summary_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "nssa": {"no_summary": True, "state": "absent"},
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no area 1 nssa no-summary"],
        )

    def test_awplus_ospf_area_nssa_translator_role(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "nssa": {
                        "translator_role": True,
                        "translator_role_type": "always",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "area 1 nssa translator-role always"],
        )

    def test_awplus_ospf_area_nssa_translator_role_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "nssa": {
                        "translator_role": True,
                        "translator_role_type": "always",
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no area 1 nssa translator-role"],
        )

    def test_awplus_ospf_area_range(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "range": {"ip_addr": "192.168.0.0/16"}},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "area 1 range 192.168.0.0/16"],
        )

    def test_awplus_ospf_area_range_advertise(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "range": {"ip_addr": "192.168.0.0/16", "advertise": True},
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "area 1 range 192.168.0.0/16 advertise"],
        )

    def test_awplus_ospf_area_range_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "range": {"ip_addr": "192.168.0.0/16", "state": "absent"},
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no area 1 range 192.168.0.0/16"],
        )

    def test_awplus_ospf_area_stub(self):
        set_module_args(
            {"router": {"process_id": 100}, "area": {"area_id": 1, "stub": {}}}
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "area 1 stub"]
        )

    def test_awplus_ospf_area_stub_no_summary(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "stub": {"no_summary": True}},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "area 1 stub no-summary"]
        )

    def test_awplus_ospf_area_stub_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {"area_id": 1, "stub": {"state": "absent"}},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "no area 1 stub"]
        )

    def test_awplus_ospf_area_stub_no_summary_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "stub": {"no_summary": True, "state": "absent"},
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no area 1 stub no-summary"],
        )

    def test_awplus_ospf_area_virtual_link(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {"ip_addr": "10.10.11.50"},
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "area 1 virtual-link 10.10.11.50"],
        )

    def test_awplus_ospf_area_virtual_link_auth(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "auth_key": "password1",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "area 1 virtual-link 10.10.11.50 authentication-key password1",
            ],
        )

    def test_awplus_ospf_area_virtual_link_msg(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "msg_key_id": 1,
                        "msg_key_password": "password12345678",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "area 1 virtual-link 10.10.11.50 message-digest-key 1 md5 "
                "password12345678",
            ],
        )

    def test_awplus_ospf_area_virtual_link_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no area 1 virtual-link 10.10.11.50"],
        )

    def test_awplus_ospf_area_virtual_link_auth_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "auth_key": "password1",
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no area 1 virtual-link 10.10.11.50 authentication-key",
            ],
        )

    def test_awplus_ospf_area_virtual_link_msg_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "msg_key_id": 1,
                        "msg_key_password": "password12345678",
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no area 1 virtual-link 10.10.11.50 message-digest-key 1"
            ],
        )

    def test_awplus_ospf_area_virtual_link_authentication(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "area 1 virtual-link 10.10.11.50 authentication",
            ],
        )

    def test_awplus_ospf_area_virtual_link_authentication_message_digest(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                        "authentication_type": "message-digest",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "area 1 virtual-link 10.10.11.50 authentication "
                "message-digest",
            ],
        )

    def test_awplus_ospf_area_virtual_link_authentication_auth(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                        "auth_key": "password1",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "area 1 virtual-link 10.10.11.50 authentication "
                "authentication-key password1",
            ],
        )

    def test_awplus_ospf_area_virtual_link_authentication_msg(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                        "authentication_type": "null",
                        "msg_key_id": 1,
                        "msg_key_password": "password12345678",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "area 1 virtual-link 10.10.11.50 authentication null "
                "message-digest-key 1 md5 password12345678",
            ],
        )

    def test_awplus_ospf_area_virtual_link_authentication_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no area 1 virtual-link 10.10.11.50 authentication",
            ],
        )

    def test_awplus_ospf_area_virtual_link_authentication_auth_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                        "auth_key": "password1",
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no area 1 virtual-link 10.10.11.50 authentication "
                "authentication-key",
            ],
        )

    def test_awplus_ospf_area_virtual_link_authentication_msg_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                        "msg_key_id": 1,
                        "msg_key_password": "password12345678",
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no area 1 virtual-link 10.10.11.50 authentication "
                "message-digest-key 1",
            ],
        )

    def test_awplus_ospf_area_virtual_link_all(self,):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                        "authentication_type": "null",
                        "msg_key_id": 1,
                        "msg_key_password": "password12345678",
                        "dead_interval": True,
                        "dead_interval_value": 123,
                        "hello_interval": True,
                        "hello_interval_value": 456,
                        "retransmit_interval": True,
                        "retransmit_interval_value": 789,
                        "transmit_delay": True,
                        "transmit_delay_value": 963,
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "area 1 virtual-link 10.10.11.50 authentication dead-interval "
                "123 hello-interval 456 retransmit-interval 789 "
                "transmit-delay 963",
            ],
        )

    def test_awplus_ospf_area_virtual_link_all_no(self,):
        set_module_args(
            {
                "router": {"process_id": 100},
                "area": {
                    "area_id": 1,
                    "virtual_link": {
                        "ip_addr": "10.10.11.50",
                        "authentication": True,
                        "authentication_type": "null",
                        "msg_key_id": 1,
                        "msg_key_password": "password12345678",
                        "dead_interval": True,
                        "dead_interval_value": 123,
                        "hello_interval": True,
                        "hello_interval_value": 456,
                        "retransmit_interval": True,
                        "retransmit_interval_value": 789,
                        "transmit_delay": True,
                        "transmit_delay_value": 963,
                        "state": "absent",
                    },
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no area 1 virtual-link 10.10.11.50 authentication "
                "dead-interval hello-interval retransmit-interval "
                "transmit-delay",
            ],
        )

    def test_awplus_ospf_network_area(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "network_area": {
                    "network_address": "10.0.0.0/8",
                    "area_id": "1.1.1.1",
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "network 10.0.0.0/8 area 1.1.1.1"],
        )

    def test_awplus_ospf_network_area_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "network_area": {
                    "network_address": "10.0.0.0/8",
                    "area_id": "1.1.1.1",
                    "state": "absent",
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no network 10.0.0.0/8 area 1.1.1.1"],
        )

    def test_awplus_ospf_router_id(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "ospf_router_id": {"ip_addr": "2.3.4.5"},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "ospf router-id 2.3.4.5"]
        )

    def test_awplus_ospf_router_id_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "ospf_router_id": {"state": "absent"},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "no ospf router-id"]
        )

    def test_awplus_ospf_passive_interface_all(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "passive_interface": {"ip_addr": "10.0.0.1", "name": "vlan1"},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "passive-interface vlan1 10.0.0.1"],
        )

    def test_awplus_ospf_passive_interface_interface(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "passive_interface": {"name": "vlan1"},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"], ["router ospf 100", "passive-interface vlan1"]
        )

    def test_awplus_ospf_passive_interface_ip_addr(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "passive_interface": {"ip_addr": "10.0.0.1"},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "passive-interface 10.0.0.1"],
        )

    def test_awplus_ospf_passive_interface_all_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "passive_interface": {
                    "ip_addr": "10.0.0.1",
                    "name": "vlan1",
                    "state": "absent",
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no passive-interface vlan1 10.0.0.1"],
        )

    def test_awplus_ospf_passive_interface_interface_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "passive_interface": {"name": "vlan1", "state": "absent"},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no passive-interface vlan1"],
        )

    def test_awplus_ospf_passive_interface_ip_addr_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "passive_interface": {
                    "ip_addr": "10.0.0.1",
                    "state": "absent",
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no passive-interface 10.0.0.1"],
        )

    def test_awplus_ospf_redistribute_fail(self):
        set_module_args({"router": {"process_id": 100}, "redistribute": {}})
        self.execute_module(failed=True)

    def test_awplus_ospf_redistribute_all_metric_type_1(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "redistribute": {
                    "static": True,
                    "metric": 12,
                    "metric_type": "1",
                    "route_map_name": "rmap2",
                    "tag": 456456,
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "redistribute static metric 12 metric-type 1 "
                "route-map rmap2 tag 456456",
            ],
        )

    def test_awplus_ospf_redistribute_all_metric_type_1_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "redistribute": {
                    "connected": True,
                    "metric": 12,
                    "metric_type": "1",
                    "route_map_name": "rmap2",
                    "tag": 456456,
                    "state": "absent",
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no redistribute connected metric metric-type route-map tag",
            ],
        )

    def test_awplus_ospf_redistribute_metric_type_2_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "redistribute": {
                    "static": True,
                    "metric_type": "2",
                    "state": "absent",
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no redistribute static metric-type"],
        )

    def test_awplus_ospf_summary_address(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "summary_address": {"ip_addr": "172.16.0.0/16"},
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "summary-address 172.16.0.0/16"],
        )

    def test_awplus_ospf_summary_address_advertise(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "summary_address": {
                    "ip_addr": "172.16.0.0/16",
                    "not_advertise": True,
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "summary-address 172.16.0.0/16 not-advertise",
            ],
        )

    def test_awplus_ospf_summary_address_tag(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "summary_address": {
                    "ip_addr": "172.16.0.0/16",
                    "tag": 123456789,
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "summary-address 172.16.0.0/16 tag 123456789",
            ],
        )

    def test_awplus_ospf_summary_address_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "summary_address": {
                    "ip_addr": "172.16.0.0/16",
                    "state": "absent",
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["router ospf 100", "no summary-address 172.16.0.0/16"],
        )

    def test_awplus_ospf_summary_address_advertise_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "summary_address": {
                    "ip_addr": "172.16.0.0/16",
                    "not_advertise": True,
                    "state": "absent"
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no summary-address 172.16.0.0/16 not-advertise",
            ],
        )

    def test_awplus_ospf_summary_address_tag_no(self):
        set_module_args(
            {
                "router": {"process_id": 100},
                "summary_address": {
                    "ip_addr": "172.16.0.0/16",
                    "tag": 123456789,
                    "state": "absent"
                },
            }
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "router ospf 100",
                "no summary-address 172.16.0.0/16 tag 123456789",
            ],
        )
