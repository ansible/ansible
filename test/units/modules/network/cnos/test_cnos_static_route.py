# (c) 2016 Red Hat Inc.
# Copyright (C) 2017 Lenovo.
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
from ansible.modules.network.cnos import cnos_static_route
from .cnos_module import TestCnosModule, load_fixture
from units.modules.utils import set_module_args


class TestCnosStaticRouteModule(TestCnosModule):

    module = cnos_static_route

    def setUp(self):
        super(TestCnosStaticRouteModule, self).setUp()

        self.mock_exec_command = patch('ansible.modules.network.cnos.cnos_banner.exec_command')
        self.exec_command = self.mock_exec_command.start()

        self.mock_load_config = patch('ansible.modules.network.cnos.cnos_static_route.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.cnos.cnos_static_route.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestCnosStaticRouteModule, self).tearDown()
        self.mock_exec_command.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None):
        self.exec_command.return_value = (0, load_fixture('cnos_static_route.cfg').strip(), None)
        self.load_config.return_value = dict(diff=None, session='session')

    def test_cnos_static_route_present(self):
        set_module_args(dict(prefix='10.241.107.20', mask='255.255.255.0', next_hop='10.241.106.1'))
        self.execute_module(changed=True, commands=['ip route 10.241.107.20 255.255.255.0 10.241.106.1 1'])

    def test_cnos_static_route_present_no_defaults(self):
        set_module_args(dict(prefix='10.241.106.4', mask='255.255.255.0', next_hop='1.2.3.5',
                             description='testing', admin_distance=100))
        self.execute_module(changed=True,
                            commands=['ip route 10.241.106.4 255.255.255.0 1.2.3.5 100 description testing'])

    def test_cnos_static_route_change(self):
        set_module_args(dict(prefix='10.10.30.64', mask='255.255.255.0', next_hop='1.2.4.8'))
        self.execute_module(changed=True,
                            commands=['ip route 10.10.30.64 255.255.255.0 1.2.4.8 1'])

    def test_cnos_static_route_absent(self):
        set_module_args(dict(prefix='10.10.30.12',
                             mask='255.255.255.0', next_hop='1.2.4.8', state='absent'))
        self.execute_module(changed=True,
                            commands=['no ip route 10.10.30.12 255.255.255.0 1.2.4.8 1'])
