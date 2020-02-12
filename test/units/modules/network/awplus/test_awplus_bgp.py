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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.awplus import awplus_bgp
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusBgpModule(TestAwplusModule):

    module = awplus_bgp

    def setUp(self):
        super(TestAwplusBgpModule, self).setUp()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_bgp.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_bgp.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestAwplusBgpModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('awplus_bgp_config.cfg')
        self.load_config.return_value = []

    def test_awplus_bgp(self):
        set_module_args(dict(asn=100, router_id='192.0.2.2'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
                         'router bgp 100', 'bgp router-id 192.0.2.2'])

    def test_awplus_bgp_change_nothing(self):
        set_module_args(dict(asn=100, router_id='192.0.2.1', state='present'))
        self.execute_module(changed=False)

    def test_awplus_bgp_wrong_asn(self):
        set_module_args(dict(asn=10, router_id='192.168.1.1'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Another BGP ASN already exists.')

    def test_awplus_bgp_remove(self):
        set_module_args(dict(asn=100, state='absent'))
        self.execute_module(changed=True, commands=['no router bgp 100'])

    def test_awplus_bgp_remove_vrf(self):
        set_module_args(dict(asn=100, vrf='red', state='absent'))
        self.execute_module(changed=True, commands=[
                            'router bgp 100', 'no address-family ipv4 vrf red'])

    def test_awplus_bgp_remove_nonexistant_vrf(self):
        set_module_args(dict(asn=100, vrf='foo', state='absent'))
        self.execute_module(changed=False)

    def test_awplus_bgp_remove_wrong_asn(self):
        set_module_args(dict(asn=10, state='absent'))
        self.execute_module(changed=False)

    def test_awplus_bgp_vrf(self):
        set_module_args(dict(asn=100, vrf='test', router_id='192.0.2.1'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], "VRF test doesn't exist.")

    def test_awplus_bgp_global_param(self):
        set_module_args(dict(asn=100, confederation_id=16))
        self.execute_module(changed=True, commands=[
                            'router bgp 100', 'bgp confederation identifier 16'])

    def test_awplus_bgp_global_param_outside_default(self):
        set_module_args(dict(asn=100, vrf='run', enforce_first_as=True))
        result = self.execute_module(failed=True)
        self.assertEqual(
            result['msg'], 'Global params can be modified only under "default" VRF.')

    def test_awplus_bgp_default_value(self):
        set_module_args(
            dict(asn=100, graceful_restart_timers_restart='default'))
        self.execute_module(
            changed=True,
            commands=['router bgp 100',
                      'bgp graceful-restart restart-time 120']
        )
