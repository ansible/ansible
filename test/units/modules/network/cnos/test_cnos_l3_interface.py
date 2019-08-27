#
# (c) 2018 Lenovo.
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
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.cnos import cnos_l3_interface
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosL3InterfaceModule(TestCnosModule):
    module = cnos_l3_interface

    def setUp(self):
        super(TestCnosL3InterfaceModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.cnos.cnos_l3_interface.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.cnos.cnos_l3_interface.load_config'
        )
        self._patch_is_switchport = patch(
            'ansible.modules.network.cnos.cnos_l3_interface.is_switchport'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()
        self._is_switchport = self._patch_is_switchport.start()

    def tearDown(self):
        super(TestCnosL3InterfaceModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()

    def load_fixtures(self, commands=None):
        config_file = 'l3_interface_config.cfg'
        self._get_config.return_value = load_fixture(config_file)
        self._load_config.return_value = None
        self._is_switchport.return_value = False

    def test_cnos_l3_interface_ipv4_address(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 1/35',
            ipv4='192.168.4.1/24'
        ))
        commands = [
            'interface Ethernet 1/35',
            'ip address 192.168.4.1 255.255.255.0'
        ]
        result = self.execute_module(changed=True, commands=commands)

    def test_cnos_l3_interface_absent(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet1/9',
            state='absent'
        ))
        commands = [
            'interface Ethernet1/9',
            'no ip address',
            'no ipv6 address'
        ]
        result = self.execute_module(changed=True, commands=commands)
