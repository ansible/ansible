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

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_bgp
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosBgpModule(TestNxosModule):

    module = nxos_bgp

    def setUp(self):
        super(TestNxosBgpModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_bgp.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_bgp.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosBgpModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('nxos_bgp', 'config.cfg')
        self.load_config.return_value = []

    def test_nxos_bgp(self):
        set_module_args(dict(asn=65535, router_id='1.1.1.1'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['router bgp 65535', 'router-id 1.1.1.1'])

    def test_nxos_bgp_change_nothing(self):
        set_module_args(dict(asn=65535, router_id='192.168.1.1'))
        self.execute_module(changed=False)

    def test_nxos_bgp_wrong_asn(self):
        set_module_args(dict(asn=10, router_id='192.168.1.1'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Another BGP ASN already exists.')

    def test_nxos_bgp_remove(self):
        set_module_args(dict(asn=65535, state='absent'))
        self.execute_module(changed=True, commands=['no router bgp 65535'])

    def test_nxos_bgp_remove_vrf(self):
        set_module_args(dict(asn=65535, vrf='test2', state='absent'))
        self.execute_module(changed=True, commands=['router bgp 65535', 'no vrf test2'])

    def test_nxos_bgp_remove_nonexistant_vrf(self):
        set_module_args(dict(asn=65535, vrf='foo', state='absent'))
        self.execute_module(changed=False)

    def test_nxos_bgp_remove_wrong_asn(self):
        set_module_args(dict(asn=10, state='absent'))
        self.execute_module(changed=False)

    def test_nxos_bgp_vrf(self):
        set_module_args(dict(asn=65535, vrf='test', router_id='1.1.1.1'))
        result = self.execute_module(changed=True, commands=['router bgp 65535', 'vrf test', 'router-id 1.1.1.1'])
        self.assertEqual(result['warnings'], ["VRF test doesn't exist."])

    def test_nxos_bgp_global_param(self):
        set_module_args(dict(asn=65535, shutdown=True))
        self.execute_module(changed=True, commands=['router bgp 65535', 'shutdown'])

    def test_nxos_bgp_global_param_outside_default(self):
        set_module_args(dict(asn=65535, vrf='test', shutdown=True))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Global params can be modified only under "default" VRF.')

    def test_nxos_bgp_default_value(self):
        set_module_args(dict(asn=65535, graceful_restart_timers_restart='default'))
        self.execute_module(
            changed=True,
            commands=['router bgp 65535', 'graceful-restart restart-time 120']
        )


class TestNxosBgp32BitsAS(TestNxosModule):

    module = nxos_bgp

    def setUp(self):
        super(TestNxosBgp32BitsAS, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_bgp.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_bgp.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosBgp32BitsAS, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('nxos_bgp', 'config_32_bits_as.cfg')
        self.load_config.return_value = []

    def test_nxos_bgp_change_nothing(self):
        set_module_args(dict(asn='65535.65535', router_id='192.168.1.1'))
        self.execute_module(changed=False)

    def test_nxos_bgp_wrong_asn(self):
        set_module_args(dict(asn='65535.10', router_id='192.168.1.1'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Another BGP ASN already exists.')

    def test_nxos_bgp_remove(self):
        set_module_args(dict(asn='65535.65535', state='absent'))
        self.execute_module(changed=True, commands=['no router bgp 65535.65535'])
