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

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_pim_rp_address
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosPimRpAddressModule(TestNxosModule):

    module = nxos_pim_rp_address

    def setUp(self):
        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_pim_rp_address.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_pim_rp_address.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('nxos_pim_rp_address', 'config.cfg')
        self.load_config.return_value = None

    def test_nxos_pim_rp_address(self):
        set_module_args(dict(rp_address='5.6.7.8'))
        self.execute_module(changed=True, commands=['ip pim rp-address 5.6.7.8'])

    def test_nxos_pim_rp_address_no_change(self):
        set_module_args(dict(rp_address='1.2.3.4'))
        self.execute_module(changed=False, commands=[])

    def test_nxos_pim_rp_address_absent(self):
        set_module_args(dict(rp_address='1.2.3.4', state='absent'))
        self.execute_module(changed=True, commands=['no ip pim rp-address 1.2.3.4'])

    def test_nxos_pim_rp_address_absent_no_change(self):
        set_module_args(dict(rp_address='5.6.7.8', state='absent'))
        self.execute_module(changed=False, commands=[])
