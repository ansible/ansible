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
from ansible.modules.network.nxos import nxos_vrf_af
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosVrfafModule(TestNxosModule):

    module = nxos_vrf_af

    def setUp(self):
        super(TestNxosVrfafModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_vrf_af.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_vrf_af.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosVrfafModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('nxos_vrf_af', 'config.cfg')
        self.load_config.return_value = None

    def test_nxos_vrf_af_present_current_non_existing(self):
        set_module_args(dict(vrf='vrf0', afi='ipv4', state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf0',
                                              'address-family ipv4 unicast'])

    def test_nxos_vrf_af_present_current_existing(self):
        set_module_args(dict(vrf='vrf1', afi='ipv4', state='present'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_absent_current_non_existing(self):
        set_module_args(dict(vrf='vrf0', afi='ipv4', state='absent'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_absent_current_existing(self):
        set_module_args(dict(vrf='vrf1', afi='ipv4', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf1',
                                              'no address-family ipv4 unicast'])

    def test_nxos_vrf_af_auto_evpn_route_target_present_current_existing(self):
        set_module_args(dict(vrf='vrf11', afi='ipv4', route_target_both_auto_evpn=True))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_auto_evpn_route_target_present_current_non_existing(self):
        set_module_args(dict(vrf='vrf10', afi='ipv4', route_target_both_auto_evpn=True))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf10',
                                              'address-family ipv4 unicast',
                                              'route-target both auto evpn'])

    def test_nxos_vrf_af_auto_evpn_route_target_absent_current_existing(self):
        set_module_args(dict(vrf='vrf11', afi='ipv4', route_target_both_auto_evpn=False))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf11',
                                              'address-family ipv4 unicast',
                                              'no route-target both auto evpn'])

    def test_nxos_vrf_af_auto_evpn_route_target_absent_current_non_existing(self):
        set_module_args(dict(vrf='vrf1', afi='ipv4', route_target_both_auto_evpn=False))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_route_target_import_present_current_non_existing(self):
        set_module_args(dict(vrf='vrf1',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "present"
                               }
                             ]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf1',
                                              'address-family ipv4 unicast',
                                              'route-target import 65000:1000'])

    def test_nxos_vrf_af_route_target_import_present_current_existing(self):
        set_module_args(dict(vrf='vrf21',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "present"
                               }
                             ]))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_route_target_multi_import_present_current_non_existing(self):
        set_module_args(dict(vrf='vrf1',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "present"
                               },
                               {
                                 "rt": "65001:1000",
                                 "state": "present"
                               },
                               {
                                 "rt": "65002:1000",
                                 "state": "present"
                               }
                             ]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf1',
                                              'address-family ipv4 unicast',
                                              'route-target import 65000:1000',
                                              'route-target import 65001:1000',
                                              'route-target import 65002:1000'])

    def test_nxos_vrf_af_route_target_multi_import_present_current_existing(self):
        set_module_args(dict(vrf='vrf21',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "present"
                               },
                               {
                                 "rt": "65001:1000",
                                 "state": "present"
                               },
                               {
                                 "rt": "65002:1000",
                                 "state": "present"
                               }
                             ]))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_route_target_import_absent_current_non_existing(self):
        set_module_args(dict(vrf='vrf1',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "absent"
                               }
                             ]))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_route_target_import_absent_current_existing(self):
        set_module_args(dict(vrf='vrf21',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "absent"
                               }
                             ]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf21',
                                              'address-family ipv4 unicast',
                                              'no route-target import 65000:1000'])

    def test_nxos_vrf_af_route_target_multi_import_absent_current_non_existing(self):
        set_module_args(dict(vrf='vrf1',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "absent"
                               },
                               {
                                 "rt": "65001:1000",
                                 "state": "absent"
                               },
                               {
                                 "rt": "65002:1000",
                                 "state": "absent"
                               }
                             ]))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_nxos_vrf_af_route_target_multi_import_absent_current_existing(self):
        set_module_args(dict(vrf='vrf21',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "absent"
                               },
                               {
                                 "rt": "65001:1000",
                                 "state": "absent"
                               },
                               {
                                 "rt": "65002:1000",
                                 "state": "absent"
                               }
                             ]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf21',
                                              'address-family ipv4 unicast',
                                              'no route-target import 65000:1000',
                                              'no route-target import 65001:1000',
                                              'no route-target import 65002:1000'])

    def test_nxos_vrf_af_route_target_multi_import_absent_current_mix(self):
        set_module_args(dict(vrf='vrf21',
                             afi='ipv4',
                             route_target_import=[
                               {
                                 "rt": "65000:1000",
                                 "state": "present"
                               },
                               {
                                 "rt": "65001:1000",
                                 "state": "present"
                               },
                               {
                                 "rt": "65002:1000",
                                 "state": "absent"
                               },
                               {
                                 "rt": "65003:1000",
                                 "state": "present"
                               },
                               {
                                 "rt": "65004:1000",
                                 "state": "absent"
                               }
                             ]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vrf context vrf21',
                                              'address-family ipv4 unicast',
                                              'no route-target import 65002:1000',
                                              'route-target import 65003:1000'])