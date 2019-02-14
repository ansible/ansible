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
from ansible.modules.network.nxos import nxos_pim
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosPimModule(TestNxosModule):

    module = nxos_pim

    def setUp(self):
        super(TestNxosPimModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_pim.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_pim.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestNxosPimModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('nxos_pim', 'config.cfg')
        self.load_config.return_value = None

    def test_nxos_pim(self):
        set_module_args(dict(ssm_range='232.0.0.0/8'))
        self.execute_module(changed=True, commands=['ip pim ssm range 232.0.0.0/8'])

    def test_nxos_pim_none(self):
        set_module_args(dict(ssm_range='none'))
        self.execute_module(changed=True, commands=['ip pim ssm range none'])

    def test_nxos_pim_no_change(self):
        set_module_args(dict(ssm_range='127.0.0.0/31'))
        self.execute_module(changed=False, commands=[])
