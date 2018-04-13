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
from ansible.modules.network.nxos import nxos_interface_ospf
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosInterfaceOspfModule(TestNxosModule):

    module = nxos_interface_ospf

    def setUp(self):
        super(TestNxosInterfaceOspfModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_interface_ospf.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_interface_ospf.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestNxosInterfaceOspfModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        module_name = self.module.__name__.rsplit('.', 1)[1]
        self.get_config.return_value = load_fixture(module_name, 'config.cfg')
        self.load_config.return_value = None

    def test_nxos_interface_ospf(self):
        set_module_args(dict(interface='ethernet1/32', ospf=1, area=1))
        self.execute_module(changed=True, commands=['interface Ethernet1/32', 'ip router ospf 1 area 0.0.0.1'])

    def test_loopback_interface_failed(self):
        set_module_args(dict(interface='loopback0', ospf=1, area=0, passive_interface=True))
        self.execute_module(failed=True, changed=False)
