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
from ansible.modules.network.awplus import awplus_static_route
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusStaticRouteModule(TestAwplusModule):

    module = awplus_static_route

    def setUp(self):
        super(TestAwplusStaticRouteModule, self).setUp()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_static_route.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_static_route.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestAwplusStaticRouteModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('awplus_static_route.cfg')
        self.load_config.return_value = None

    def test_awplus_static_route_present(self):
        set_module_args(dict(prefix='192.168.20.64',
                             mask=25, next_hop='192.0.2.3'))
        self.execute_module(changed=True, commands=[
                            'ip route 192.168.20.64/25 192.0.2.3'])

    def test_awplus_static_route_present_no_defaults(self):
        set_module_args(dict(prefix='192.168.20.64', mask=24, next_hop='192.0.2.3',
                             interface="vlan2", admin_distance=100))
        self.execute_module(changed=True, commands=[
                            'ip route 192.168.20.64/24 192.0.2.3 vlan2 100'])

    def test_awplus_static_route_present_vrf(self):
        set_module_args(dict(prefix='192.168.20.64', mask=24,
                             next_hop='192.0.2.3', vrf='test'))
        self.execute_module(changed=True, sort=False, commands=[
                            'ip route vrf test 192.168.20.64/24 192.0.2.3'])

    def test_awplus_static_route_no_change(self):
        set_module_args(dict(prefix='10.0.0.0', mask=8, next_hop='10.37.7.1'))
        self.execute_module(changed=False, commands=[])

    def test_awplus_static_route_absent(self):
        set_module_args(dict(prefix='10.0.0.0', mask=8,
                             next_hop='10.37.7.1', state='absent'))
        self.execute_module(changed=True, commands=[
                            'no ip route 10.0.0.0/8 10.37.7.1'])

    def test_awplus_static_route_absent_no_change(self):
        set_module_args(dict(prefix='192.168.20.6', mask=24,
                             next_hop='192.0.2.3', state='absent'))
        self.execute_module(changed=False, commands=[])
