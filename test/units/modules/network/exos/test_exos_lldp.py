#
# (c) 2019 Extreme Networks Inc.
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
#
from __future__ import (absolute_import, division, print_function)
import json
import re
from units.compat.mock import patch
from ansible.modules.network.exos import exos_lldp
from units.modules.utils import set_module_args
from ansible.module_utils.six import assertCountEqual
from .exos_module import TestExosModule, load_fixture
__metaclass__ = type


class TestExosLldpModule(TestExosModule):
    module = exos_lldp

    def setUp(self):
        super(TestExosLldpModule, self).setUp()
        self.mock_send_requests = patch(
            'ansible.modules.network.exos.exos_lldp.send_requests'
        )
        self.send_requests = self.mock_send_requests.start()

    def tearDown(self):
        super(TestExosLldpModule, self).tearDown()
        self.mock_send_requests.stop()

    def load_fixtures(self, commands=None):
        def get_fixture(*args, **kwargs):
            # if kwargs['requests'][0]["path"] != '/rest/restconf/data/openconfig-interfaces:interfaces?depth=4':
            #     raise ConnectionError(kwargs)
            # print(kwargs)
            interface_file = 'get_all_interfaces'
            requests = kwargs["requests"]
            resp = []
            for req in requests:
                if req["path"] == "/rest/restconf/data/openconfig-interfaces:interfaces?depth=4":
                    return [load_fixture(interface_file)]
                else:
                    path = req["path"]

                    interface = (re.search('=(.*)/config', path)).group(1)
                    resp.append({
                        "openconfig-lldp:config": {
                            "enabled": False,
                            "name": interface
                        }
                    })

                    return resp

        self.send_requests.side_effect = get_fixture

    def make_lldp_request(self, interface):
        lldp_request = {
            "data": {
                "openconfig-lldp:config": {
                    "enabled": True,
                    "name": interface
                }
            },
            "method": "PATCH",
            "path": "/rest/restconf/data/openconfig-lldp:lldp/interfaces/interface=" + interface + "/config"
        }
        return lldp_request

    def test_enable_single_interface(self, *args, **kwargs):
        set_module_args(dict(
            interfaces="1:1",
            state="present"
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["requests"], [{
                "data": {
                    "openconfig-lldp:config": {
                        "enabled": True,
                        "name": "1:1"
                    }
                },
                "method": "PATCH",
                "path": "/rest/restconf/data/openconfig-lldp:lldp/interfaces/interface=1:1/config"
            }])

    def test_invalid_interface(self, *args, **kwargs):
        set_module_args(dict(
            interfaces="1:35",
            state="present"
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], "Invalid interface")

    def test_idempotent_absent(self, *args, **kwargs):
        set_module_args(dict(
            interfaces="1:1",
            state="absent"
        ))
        result = self.execute_module()
        self.assertEqual(result['changed'], False)
        self.assertEqual(result["requests"], [])

    def test_interface_range(self, *args, **kwargs):
        set_module_args(dict(
            interfaces="1:1-1:3",
            state="present"
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(len(result["requests"]), 3)
        self.assertEqual(
            result["requests"][0], self.make_lldp_request("1:1"))
        self.assertEqual(
            result["requests"][1], self.make_lldp_request("1:2"))
        self.assertEqual(
            result["requests"][2], self.make_lldp_request("1:3"))

    def test_interface_range2(self, *args, **kwargs):
        set_module_args(dict(
            interfaces="1:33-2:2",
            state="present"
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(len(result["requests"]), 4)
        self.assertEqual(
            result["requests"][0], self.make_lldp_request("1:33"))
        self.assertEqual(
            result["requests"][1], self.make_lldp_request("1:34"))
        self.assertEqual(
            result["requests"][2], self.make_lldp_request("2:1"))
        self.assertEqual(
            result["requests"][3], self.make_lldp_request("2:2"))

    def test_interface_range3(self, *args, **kwargs):
        set_module_args(dict(
            interfaces="1:5-1:7,2:7",
            state="present"
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(len(result["requests"]), 4)
        self.assertEqual(
            result["requests"][0], self.make_lldp_request("1:5"))
        self.assertEqual(
            result["requests"][1], self.make_lldp_request("1:6"))
        self.assertEqual(
            result["requests"][2], self.make_lldp_request("1:7"))
        self.assertEqual(
            result["requests"][3], self.make_lldp_request("2:7"))
