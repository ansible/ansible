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
from ansible.modules.network.ios import ios_static_route
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosStaticRouteModule(TestIosModule):

    module = ios_static_route

    def setUp(self):
        super(TestIosStaticRouteModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ios.ios_static_route.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_static_route.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosStaticRouteModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('ios_static_route_config.cfg').strip()
        self.load_config.return_value = dict(diff=None, session='session')

    def test_ios_static_route_idempotent(self):
        set_module_args(dict(
            prefix='10.1.1.1',
            mask='255.255.255.255',
            next_hop='192.168.1.2',
            tag=100,
            vrf='INTERNET',
            state='present'
        ))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_ios_static_route_config(self):
        set_module_args(dict(
            prefix='12.11.0.0',
            mask='255.255.0.0',
            next_hop='10.1.1.1',
            tag=100,
            vrf='DATA_VRF',
            admin_distance=150,
            interface='GigabitEthernet0/1',
            name='Web Server Static',
            state='present'
        ))
        commands = [
            'ip route vrf DATA_VRF 12.11.0.0 255.255.0.0 GigabitEthernet0/1 10.1.1.1 150 tag 100 name "Web Server Static"'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_ios_static_route_not_remove(self):
        set_module_args(dict(
            prefix='192.168.1.128',
            mask='255.255.255.128',
            next_hop='10.1.1.1',
            tag=100,
            vrf='DATA',
            track=1,
            interface='GigabitEthernet0/0',
            name='Some Remote Server',
            state='absent'
        ))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_ios_static_route_remove(self):
        set_module_args(dict(
            prefix='192.168.1.128',
            mask='255.255.255.128',
            next_hop='10.1.1.1',
            tag=200,
            vrf='DATA',
            track=1,
            admin_distance=200,
            interface='GigabitEthernet0/0',
            name='Some Remote Server',
            state='absent'
        ))
        commands = ['no ip route vrf DATA 192.168.1.128 255.255.255.128 GigabitEthernet0/0 10.1.1.1 200 tag 200 name "Some Remote Server" track 1']
        self.execute_module(changed=True, commands=commands)
