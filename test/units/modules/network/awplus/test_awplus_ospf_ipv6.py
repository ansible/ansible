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
from ansible.modules.network.awplus import awplus_ospf_ipv6
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusOspfIPv6Module(TestAwplusModule):

    module = awplus_ospf_ipv6

    def setUp(self):
        super(TestAwplusOspfIPv6Module, self).setUp()

        self.mock_load_config = patch(
            "ansible.modules.network.awplus.awplus_ospf_ipv6.load_config"
        )
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch(
            "ansible.modules.network.awplus.awplus_ospf_ipv6.get_config"
        )
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestAwplusOspfIPv6Module, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=""):
        self.get_config.return_value = load_fixture(
            "awplus_ospf_ipv6_config.cfg")
        self.load_config.return_value = []

    def test_awplus_router_ospf(self):
        set_module_args({"router": {"process_id": 12}})
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["router ipv6 ospf 12"])

    def test_awplus_router_ospf_change_nothing(self):
        set_module_args({"router": {"process_id": 100}})
        self.execute_module(changed=False)

    def test_awplus_router_ospf_no(self):
        set_module_args({"router": {"state": "absent"}})
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["no router ipv6 ospf"])

    def test_awplus_router_ospf_no_process_id(self):
        set_module_args({"router": {"state": "absent", "process_id": 100}})
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["no router ipv6 ospf 100"])
