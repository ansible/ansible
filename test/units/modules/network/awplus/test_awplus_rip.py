#
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
from ansible.modules.network.awplus import awplus_rip
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusRipModule(TestAwplusModule):

    module = awplus_rip

    def setUp(self):
        super(TestAwplusRipModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_rip.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_rip.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestAwplusRipModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('awplus_rip_config.cfg')
        self.load_config.return_value = None

    def test_awplus_rip_network(self):
        set_module_args(dict(network='195.46.3.4'))
        commands = ['router rip',
                    'no network 1.3.3.4',
                    'network 195.46.3.4',
                    'address-family ipv4 vrf yellow',
                    'no passive-interface vlan10']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_rip_no_network(self):
        set_module_args(dict(network='1.3.3.4', state='absent'))
        commands = ['router rip',
                    'no network 1.3.3.4']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_rip_passive_interface(self):
        set_module_args(dict(passive_int='blue vlan20'))
        commands = ['router rip',
                    'no network 1.3.3.4',
                    'address-family ipv4 vrf blue',
                    'passive-interface vlan20',
                    'address-family ipv4 vrf yellow',
                    'no passive-interface vlan10']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_rip_no_passive_interface(self):
        set_module_args(dict(passive_int='yellow vlan10', state='absent'))
        commands = ['router rip',
                    'address-family ipv4 vrf yellow',
                    'no passive-interface vlan10']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_rip_no_change(self):
        set_module_args(dict(passive_int='yellow vlan10', network='1.3.3.4'))
        commands = ['router rip']
        self.execute_module(changed=True, commands=commands)
