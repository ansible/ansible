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
from ansible.modules.network.nxos import nxos_static_route
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosStaticRouteModule(TestNxosModule):

    module = nxos_static_route

    def setUp(self):
        super(TestNxosStaticRouteModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_static_route.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_static_route.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosStaticRouteModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('', 'nxos_static_route.cfg')
        self.load_config.return_value = None

    def test_nxos_static_route_present(self):
        set_module_args(dict(prefix='192.168.20.64/24', next_hop='192.0.2.3'))
        self.execute_module(changed=True, commands=['ip route 192.168.20.0/24 192.0.2.3'])

    def test_nxos_static_route_present_no_defaults(self):
        set_module_args(dict(prefix='192.168.20.64/24', next_hop='192.0.2.3',
                             route_name='testing', pref=100))
        self.execute_module(changed=True, commands=['ip route 192.168.20.0/24 192.0.2.3 name testing 100'])

    def test_nxos_static_route_present_vrf(self):
        set_module_args(dict(prefix='192.168.20.64/24', next_hop='192.0.2.3', vrf='test'))
        self.execute_module(changed=True, sort=False, commands=['vrf context test', 'ip route 192.168.20.0/24 192.0.2.3'])

    def test_nxos_static_route_no_change(self):
        set_module_args(dict(prefix='10.10.30.64/24', next_hop='1.2.4.8'))
        self.execute_module(changed=False, commands=[])

    def test_nxos_static_route_absent(self):
        set_module_args(dict(prefix='10.10.30.12/24', next_hop='1.2.4.8', state='absent'))
        self.execute_module(changed=True, commands=['no ip route 10.10.30.0/24 1.2.4.8'])

    def test_nxos_static_route_absent_no_change(self):
        set_module_args(dict(prefix='192.168.20.6/24', next_hop='192.0.2.3', state='absent'))
        self.execute_module(changed=False, commands=[])

    def test_nxos_static_route_absent_vrf(self):
        set_module_args(dict(prefix='10.11.12.13/14', next_hop='15.16.17.18', vrf='test', state='absent'))
        self.execute_module(
            changed=True, sort=False,
            commands=['vrf context test', 'no ip route 10.8.0.0/14 15.16.17.18']
        )
